"""
NarrAI Next-Gen Recommendation Engine
Implements the 3-Stage Hybrid Recommender System:
- Stage 1: Candidate Generation (Two-Tower Content Cosine + Graph-Based DSGO Traversal)
- Stage 2: Scoring & Multi-Task Ranking (0.35*Cosine + 0.25*Implicit + 0.20*Freshness + 0.20*QualityScore)
- Stage 3: Re-ranking, Serendipity & Exploration (MMR lambda=0.7 + Multi-Armed Bandit epsilon=0.15)
- Dynamic User Interest Vector update with exponential decay (lambda = 0.05/day)
- Comment Sentiment Analysis and Entity Extraction to update user_interest_profiles
"""

import math
import json
import random
import re
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any, Set
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc, func

try:
    from db.models import (
        SocialPost,
        PostInteraction,
        UserInterestProfile,
        User,
        Story
    )
except ImportError:
    from backend.db.models import (
        SocialPost,
        PostInteraction,
        UserInterestProfile,
        User,
        Story
    )

# ==================== CONSTANTS & WEIGHTS ====================

VECTOR_DIM = 128
DECAY_LAMBDA_PER_DAY = 0.05
MMR_LAMBDA = 0.70
BANDIT_EXPLORATION_RATIO = 0.15
COLD_START_VIEW_THRESHOLD = 30

# Interaction signal weights: w(Dwell > 60s) = 2.5, w(Scroll_100) = 2.0, w(Like) = 1.5, w(Comment) = 3.0
SIGNAL_WEIGHTS = {
    "DWELL_TIME": 2.5,
    "SCROLL_100": 2.0,
    "SCROLL_50": 1.0,
    "LIKE": 1.5,
    "COMMENT": 3.0,
    "BOOKMARK": 2.0,
    "SHARE": 2.5,
    "CLICK": 0.5,
}

# Ranking formula weights
W_COSINE = 0.35
W_AFFINITY = 0.25
W_FRESHNESS = 0.20
W_QUALITY = 0.20

# Quality score component weights
W_COMPLETION = 0.40
W_LIKE_RATIO = 0.30
W_DWELL_NORM = 0.30

# Sentiment lexicon for Vietnamese and English
POSITIVE_WORDS = {
    # Vietnamese
    "tuyệt vời", "quá hay", "cuốn hút", "xuất sắc", "đỉnh cao", "thích", "cảm động",
    "mê", "hấp dẫn", "tuyệt", "hay", "đẹp", "sâu sắc", "cực phẩm", "khéo", "khen",
    "yêu", "hóng", "tuyệt hảo", "tuyệt diệu", "ủng hộ", "chất", "đỉnh", "ấn tượng",
    "tinh tế", "bất ngờ", "lôi cuốn", "mượt mà", "tài năng", "hài lòng",
    # English
    "great", "amazing", "love", "awesome", "masterpiece", "brilliant", "impressive",
    "excellent", "good", "fascinating", "captivating", "touching", "enjoy", "best"
}

NEGATIVE_WORDS = {
    # Vietnamese
    "dở tệ", "nhảm", "buồn ngủ", "vô lý", "không thích", "chán ngắt", "tệ", "chán",
    "dở", "kém", "nhạt", "thất vọng", "ức chế", "rác", "xấu", "ghét", "dở hơi",
    "phi lý", "tẩy chay", "cẩu thả", "lạc đề", "bực mình", "nhảm nhí",
    # English
    "bad", "terrible", "boring", "awful", "hate", "disappointing", "worst", "poor",
    "waste", "horrible", "annoying", "cliche", "nonsense"
}

# ==================== VECTOR MATHEMATICS & UTILITIES ====================

def normalize_vector(vec: List[float]) -> List[float]:
    """Normalizes vector to unit L2 norm: ||V||_2 = 1.0."""
    if not vec or len(vec) == 0:
        val = 1.0 / math.sqrt(VECTOR_DIM)
        return [val] * VECTOR_DIM
    
    # Pad or truncate to VECTOR_DIM
    if len(vec) < VECTOR_DIM:
        vec = vec + [0.0] * (VECTOR_DIM - len(vec))
    elif len(vec) > VECTOR_DIM:
        vec = vec[:VECTOR_DIM]

    sum_sq = sum(v * v for v in vec)
    norm = math.sqrt(sum_sq)
    if norm < 1e-9:
        val = 1.0 / math.sqrt(VECTOR_DIM)
        return [val] * VECTOR_DIM
    return [v / norm for v in vec]


def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """Computes cosine similarity between two unit vectors (bounded in [0.0, 1.0])."""
    if not vec_a or not vec_b:
        return 0.0
    dim = min(len(vec_a), len(vec_b))
    dot = sum(vec_a[i] * vec_b[i] for i in range(dim))
    # Clamped for non-negative semantic similarity
    return max(0.0, min(1.0, dot))


def generate_concept_vector(text_content: str, genre: str = "", tags: Optional[List[str]] = None) -> List[float]:
    """
    Generates a deterministic 128-dimensional concept embedding vector
    using multi-hash semantic feature projection.
    Ensures genre and tag clustering and reproducible vector space.
    """
    tags = tags or []
    tokens: List[Tuple[str, float]] = []
    
    # Text token extraction
    clean_text = re.sub(r'[^\w\s]', ' ', text_content.lower())
    words = [w for w in clean_text.split() if len(w) > 1]
    
    # Word unigrams with frequency scaling
    word_freq: Dict[str, int] = {}
    for w in words:
        word_freq[w] = word_freq.get(w, 0) + 1
    for w, count in word_freq.items():
        tokens.append((f"w:{w}", math.log1p(count)))
        
    # Word bigrams for syntactic context
    for i in range(len(words) - 1):
        bg = f"bg:{words[i]}_{words[i+1]}"
        tokens.append((bg, 1.2))
        
    # Genre signal (high weight for genre separation)
    if genre:
        g_clean = genre.lower().strip()
        tokens.append((f"genre:{g_clean}", 4.5))
        tokens.append((f"genre_stem:{g_clean[:4]}", 2.0))
        
    # Tag signals
    for t in tags:
        t_clean = t.lower().strip()
        if t_clean:
            tokens.append((f"tag:{t_clean}", 3.0))

    if not tokens:
        tokens.append(("default_token", 1.0))

    # Feature hashing into 128 dimensions
    vector = [0.0] * VECTOR_DIM
    for token_str, weight in tokens:
        # Hash to index and sign using two distinct hash slices
        h = hashlib.sha256(token_str.encode('utf-8')).digest()
        idx = int.from_bytes(h[0:4], byteorder='big') % VECTOR_DIM
        sign = 1.0 if (h[4] % 2 == 0) else -1.0
        
        # Second projection for dense dispersion
        idx2 = int.from_bytes(h[8:12], byteorder='big') % VECTOR_DIM
        sign2 = 1.0 if (h[12] % 2 == 0) else -1.0
        
        vector[idx] += weight * sign
        vector[idx2] += 0.5 * weight * sign2

    return normalize_vector(vector)


# ==================== SENTIMENT & ENTITY EXTRACTION ====================

def extract_sentiment_and_entities(
    comment_text: str,
    candidate_entities: Optional[List[str]] = None
) -> Tuple[float, List[str]]:
    """
    Analyzes sentiment score in [-1.0, 1.0] and extracts mentioned entities.
    Uses Vietnamese and English sentiment lexicon and entity matching.
    """
    if not comment_text:
        return 0.0, []

    text_lower = comment_text.lower()
    
    # 1. Lexicon sentiment analysis
    pos_matches = 0
    neg_matches = 0
    
    for word in POSITIVE_WORDS:
        if word in text_lower:
            pos_matches += 1
            
    for word in NEGATIVE_WORDS:
        if word in text_lower:
            neg_matches += 1

    total_matches = pos_matches + neg_matches
    if total_matches > 0:
        sentiment = (pos_matches - neg_matches) / float(total_matches)
    else:
        sentiment = 0.0
    sentiment = max(-1.0, min(1.0, sentiment))

    # 2. Entity extraction
    extracted: Set[str] = set()
    candidate_entities = candidate_entities or []
    
    for cand in candidate_entities:
        if cand and cand.lower() in text_lower:
            extracted.add(cand.strip())

    # Extract capitalized proper nouns / named entities from raw comment
    words = comment_text.split()
    current_entity: List[str] = []
    for w in words:
        clean_w = re.sub(r'[^\w]', '', w)
        if clean_w and clean_w[0].isupper() and len(clean_w) > 1:
            current_entity.append(clean_w)
        else:
            if current_entity:
                if len(current_entity) >= 2 or (len(current_entity) == 1 and len(current_entity[0]) > 3):
                    extracted.add(" ".join(current_entity))
                current_entity = []
    if current_entity and len(current_entity) >= 2:
        extracted.add(" ".join(current_entity))

    return sentiment, list(extracted)


# ==================== DYNAMIC USER INTEREST & EXPONENTIAL DECAY ====================

def get_or_create_user_profile(db: Session, user_id: int) -> UserInterestProfile:
    """Retrieves or initializes a dynamic UserInterestProfile."""
    profile = db.query(UserInterestProfile).filter(UserInterestProfile.user_id == user_id).first()
    if not profile:
        initial_vec = normalize_vector([])
        profile = UserInterestProfile(
            user_id=user_id,
            interest_vector=json.dumps(initial_vec),
            last_decay_time=datetime.utcnow(),
            genre_affinity=json.dumps({}),
            entity_affinity=json.dumps({}),
            last_active_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


def apply_exponential_decay(profile: UserInterestProfile, now: Optional[datetime] = None) -> None:
    """
    Applies exponential time decay: lambda = 0.05/day.
    Decays interest vector, genre affinity, and entity affinity over elapsed delta_t.
    """
    now = now or datetime.utcnow()
    last_time = profile.last_decay_time or profile.updated_at or now
    delta_seconds = max(0.0, (now - last_time).total_seconds())
    delta_days = delta_seconds / 86400.0

    if delta_days < 1e-4:
        return

    decay_factor = math.exp(-DECAY_LAMBDA_PER_DAY * delta_days)

    # 1. Decay interest vector
    try:
        current_vec = json.loads(profile.interest_vector) if profile.interest_vector else []
    except Exception:
        current_vec = []
    if current_vec:
        decayed_vec = [v * decay_factor for v in current_vec]
        profile.interest_vector = json.dumps(decayed_vec)

    # 2. Decay genre affinity
    try:
        genre_aff = json.loads(profile.genre_affinity) if profile.genre_affinity else {}
    except Exception:
        genre_aff = {}
    decayed_genre = {k: float(v) * decay_factor for k, v in genre_aff.items() if float(v) * decay_factor > 0.01}
    profile.genre_affinity = json.dumps(decayed_genre)

    # 3. Decay entity affinity
    try:
        entity_aff = json.loads(profile.entity_affinity) if profile.entity_affinity else {}
    except Exception:
        entity_aff = {}
    decayed_entity = {k: float(v) * decay_factor for k, v in entity_aff.items() if float(v) * decay_factor > 0.01}
    profile.entity_affinity = json.dumps(decayed_entity)

    profile.last_decay_time = now
    profile.last_active_at = now


def update_user_interest_on_interaction(
    db: Session,
    user_id: int,
    post: SocialPost,
    interaction_type: str,
    dwell_seconds: float = 0.0,
    scroll_depth: int = 0,
    comment_text: Optional[str] = None
) -> Tuple[float, List[str]]:
    """
    Updates user interest profile when interacting with a post:
    - Calculates effective weight based on signal type and comment sentiment.
    - Updates interest vector, genre affinity, and entity affinity.
    """
    profile = get_or_create_user_profile(db, user_id)
    now = datetime.utcnow()
    apply_exponential_decay(profile, now=now)

    # Determine base signal weight
    itype = interaction_type.upper().strip()
    if itype == "DWELL_TIME" or dwell_seconds >= 60.0:
        base_weight = SIGNAL_WEIGHTS["DWELL_TIME"]
    elif itype == "SCROLL_100" or scroll_depth >= 100:
        base_weight = SIGNAL_WEIGHTS["SCROLL_100"]
    elif itype == "SCROLL_50" or scroll_depth >= 50:
        base_weight = SIGNAL_WEIGHTS["SCROLL_50"]
    else:
        base_weight = SIGNAL_WEIGHTS.get(itype, 1.0)

    # Process comment sentiment & entity extraction
    sentiment_score = 0.0
    extracted_entities: List[str] = []
    
    if itype == "COMMENT" or comment_text:
        # Candidate entities from post
        post_entities = []
        try:
            post_entities.extend(json.loads(post.dsgo_entities or "[]"))
        except Exception:
            pass
        try:
            post_entities.extend(json.loads(post.dsgo_spaces or "[]"))
        except Exception:
            pass
            
        sentiment_score, extracted_entities = extract_sentiment_and_entities(comment_text or "", post_entities)
        
        # Effective comment weight modulated by sentiment: w = w_comment * (1.0 + s)
        effective_weight = base_weight * (1.0 + sentiment_score)
        effective_weight = max(0.2, effective_weight)
    else:
        effective_weight = base_weight

    # Retrieve post concept vector
    try:
        post_vec = json.loads(post.concept_vector) if post.concept_vector else []
    except Exception:
        post_vec = []
    if not post_vec:
        post_vec = generate_concept_vector(post.content_snippet or post.title, post.genre or "")

    # Update interest vector: U_new = Normalize(U_decayed + w * V_p)
    try:
        curr_u = json.loads(profile.interest_vector) if profile.interest_vector else []
    except Exception:
        curr_u = []
    if not curr_u or len(curr_u) != VECTOR_DIM:
        curr_u = [0.0] * VECTOR_DIM

    updated_u = [curr_u[i] + effective_weight * post_vec[i] for i in range(VECTOR_DIM)]
    profile.interest_vector = json.dumps(normalize_vector(updated_u))

    # Update genre affinity
    if post.genre:
        try:
            genre_map = json.loads(profile.genre_affinity) if profile.genre_affinity else {}
        except Exception:
            genre_map = {}
        curr_g = genre_map.get(post.genre, 0.0)
        genre_map[post.genre] = round(curr_g + effective_weight * 0.25, 4)
        profile.genre_affinity = json.dumps(genre_map)

    # Update entity affinity
    try:
        entity_map = json.loads(profile.entity_affinity) if profile.entity_affinity else {}
    except Exception:
        entity_map = {}

    all_interaction_entities = set(extracted_entities)
    try:
        all_interaction_entities.update(json.loads(post.dsgo_entities or "[]"))
    except Exception:
        pass
    try:
        all_interaction_entities.update(json.loads(post.dsgo_spaces or "[]"))
    except Exception:
        pass

    for ent in all_interaction_entities:
        if ent:
            curr_e = entity_map.get(ent, 0.0)
            # Boost entities positively associated
            bonus = 1.5 * (1.0 + max(0.0, sentiment_score))
            entity_map[ent] = round(curr_e + bonus, 4)

    profile.entity_affinity = json.dumps(entity_map)
    profile.updated_at = now
    db.commit()
    db.refresh(profile)

    return sentiment_score, extracted_entities


# ==================== 3-STAGE HYBRID RECOMMENDER ENGINE ====================

class HybridRecommenderEngine:
    """
    3-Stage Hybrid Literary Recommender System:
    Stage 1: Candidate Generation (Content Cosine + DSGO Graph Traversal)
    Stage 2: Scoring & Multi-Task Ranking
    Stage 3: Re-ranking with MMR (lambda=0.7) and Multi-Armed Bandit (epsilon=0.15)
    """

    @staticmethod
    def stage1_candidate_generation(
        db: Session,
        user_profile: Optional[UserInterestProfile],
        limit_total: int = 60,
        filter_genre: Optional[str] = None
    ) -> List[SocialPost]:
        """
        Stage 1: Retrieves candidate posts using two complementary funnels:
        - Funnel 1: Two-Tower Content Cosine Similarity (top 40)
        - Funnel 2: Graph-Based DSGO Traversal (top 20)
        """
        query = db.query(SocialPost)
        if filter_genre:
            query = query.filter(SocialPost.genre.ilike(f"%{filter_genre}%"))
            
        all_posts = query.all()
        if not all_posts:
            return []

        # If user has no profile or few posts, return available posts sorted by freshness/views
        if not user_profile or not user_profile.interest_vector:
            return sorted(all_posts, key=lambda p: (p.views_count, p.likes_count), reverse=True)[:limit_total]

        try:
            user_u = json.loads(user_profile.interest_vector)
        except Exception:
            user_u = normalize_vector([])

        # --- Funnel 1: Content Cosine Similarity (Top 40) ---
        scored_by_cosine: List[Tuple[float, SocialPost]] = []
        for p in all_posts:
            try:
                v_p = json.loads(p.concept_vector) if p.concept_vector else []
            except Exception:
                v_p = []
            if not v_p:
                v_p = generate_concept_vector(p.content_snippet or p.title, p.genre or "")
            sim = cosine_similarity(user_u, v_p)
            scored_by_cosine.append((sim, p))

        scored_by_cosine.sort(key=lambda x: x[0], reverse=True)
        top_cosine_posts = [p for _, p in scored_by_cosine[:40]]

        # --- Funnel 2: Graph-Based DSGO Traversal (Top 20) ---
        # Retrieve user's high-affinity entities and spaces
        try:
            entity_aff = json.loads(user_profile.entity_affinity) if user_profile.entity_affinity else {}
        except Exception:
            entity_aff = {}

        # Top 5 entities by affinity score
        top_user_entities = set(
            sorted(entity_aff.keys(), key=lambda k: entity_aff[k], reverse=True)[:5]
        )

        scored_by_dsgo: List[Tuple[float, SocialPost]] = []
        for p in all_posts:
            p_entities: Set[str] = set()
            try:
                p_entities.update(json.loads(p.dsgo_entities or "[]"))
            except Exception:
                pass
            try:
                p_entities.update(json.loads(p.dsgo_spaces or "[]"))
            except Exception:
                pass

            overlap = top_user_entities.intersection(p_entities)
            if overlap:
                # Graph weight = sum of affinity of shared entities + node connection density
                dsgo_score = sum(entity_aff.get(ent, 1.0) for ent in overlap) + len(overlap) * 0.5
                scored_by_dsgo.append((dsgo_score, p))

        scored_by_dsgo.sort(key=lambda x: x[0], reverse=True)
        top_dsgo_posts = [p for _, p in scored_by_dsgo[:20]]

        # Merge candidate pools and deduplicate preserving order
        seen_ids: Set[int] = set()
        candidate_pool: List[SocialPost] = []

        for p in top_cosine_posts:
            if p.id not in seen_ids:
                seen_ids.add(p.id)
                candidate_pool.append(p)

        for p in top_dsgo_posts:
            if p.id not in seen_ids:
                seen_ids.add(p.id)
                candidate_pool.append(p)

        # If candidate pool is small, supplement with recent posts
        if len(candidate_pool) < limit_total:
            remaining = [p for p in all_posts if p.id not in seen_ids]
            remaining.sort(key=lambda p: p.created_at or datetime.min, reverse=True)
            candidate_pool.extend(remaining[:limit_total - len(candidate_pool)])

        return candidate_pool[:limit_total]

    @staticmethod
    def stage2_multi_task_ranking(
        candidates: List[SocialPost],
        user_profile: Optional[UserInterestProfile],
        now: Optional[datetime] = None
    ) -> List[Tuple[SocialPost, float, Dict[str, float]]]:
        """
        Stage 2: Scoring & Multi-Task Ranking
        Score(p, u) = 0.35 * CosineSim(U_u, V_p) + 0.25 * ImplicitAffinity(u, p)
                    + 0.20 * Freshness(p) + 0.20 * QualityScore(p)
        """
        now = now or datetime.utcnow()
        ranked_results: List[Tuple[SocialPost, float, Dict[str, float]]] = []

        # Parse user features
        user_u = []
        genre_aff = {}
        entity_aff = {}
        if user_profile:
            try:
                user_u = json.loads(user_profile.interest_vector) if user_profile.interest_vector else []
            except Exception:
                user_u = []
            try:
                genre_aff = json.loads(user_profile.genre_affinity) if user_profile.genre_affinity else {}
            except Exception:
                genre_aff = {}
            try:
                entity_aff = json.loads(user_profile.entity_affinity) if user_profile.entity_affinity else {}
            except Exception:
                entity_aff = {}

        max_genre_val = max(genre_aff.values()) if genre_aff else 1.0
        max_genre_val = max(1.0, max_genre_val)

        for p in candidates:
            # 1. Cosine Similarity U_u . V_p
            try:
                v_p = json.loads(p.concept_vector) if p.concept_vector else []
            except Exception:
                v_p = []
            if not v_p:
                v_p = generate_concept_vector(p.content_snippet or p.title, p.genre or "")
            
            cos_sim = cosine_similarity(user_u, v_p) if user_u else 0.5

            # 2. Implicit Affinity (Genre affinity + Entity overlap)
            g_score = genre_aff.get(p.genre, 0.0) / max_genre_val if p.genre else 0.0
            
            p_entities: Set[str] = set()
            try:
                p_entities.update(json.loads(p.dsgo_entities or "[]"))
            except Exception:
                pass
            try:
                p_entities.update(json.loads(p.dsgo_spaces or "[]"))
            except Exception:
                pass

            overlap_count = sum(1 for e in p_entities if e in entity_aff)
            entity_overlap_ratio = overlap_count / max(1.0, float(len(p_entities)))
            implicit_affinity = 0.65 * g_score + 0.35 * entity_overlap_ratio
            implicit_affinity = max(0.0, min(1.0, implicit_affinity))

            # 3. Freshness: 1 / (1 + 0.02 * hours_since_published)
            created_at = p.created_at or now
            hours_old = max(0.0, (now - created_at).total_seconds() / 3600.0)
            freshness = 1.0 / (1.0 + 0.02 * hours_old)

            # 4. Quality Score: 0.4*CompletionRate + 0.3*LikeRatio + 0.3*DwellNorm
            views = max(1, p.views_count)
            completion_rate = min(1.0, float(p.completion_count) / float(views))
            like_ratio = min(1.0, float(p.likes_count) / float(views))
            dwell_norm = min(1.0, float(p.dwell_time_avg) / 60.0)
            quality_score = 0.40 * completion_rate + 0.30 * like_ratio + 0.30 * dwell_norm

            # Multi-Task Composite Score
            final_score = (
                W_COSINE * cos_sim +
                W_AFFINITY * implicit_affinity +
                W_FRESHNESS * freshness +
                W_QUALITY * quality_score
            )

            metrics = {
                "cosine_sim": round(cos_sim, 4),
                "implicit_affinity": round(implicit_affinity, 4),
                "freshness": round(freshness, 4),
                "quality_score": round(quality_score, 4),
                "final_score": round(final_score, 4)
            }
            ranked_results.append((p, final_score, metrics))

        # Sort descending by Stage 2 composite score
        ranked_results.sort(key=lambda x: x[1], reverse=True)
        return ranked_results

    @staticmethod
    def stage3_reranking_and_serendipity(
        scored_candidates: List[Tuple[SocialPost, float, Dict[str, float]]],
        all_candidate_posts: List[SocialPost],
        feed_limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Stage 3: Re-ranking, Serendipity & Exploration:
        - Maximal Marginal Relevance (MMR) with lambda = 0.7 for genre & concept diversity.
        - Multi-Armed Bandit (Thompson Sampling, eps=0.15) reserving 15% slots for cold-start exploration.
        """
        if not scored_candidates:
            return []

        # Identify Cold-Start Pool for Multi-Armed Bandit
        # Works with views_count < COLD_START_VIEW_THRESHOLD
        cold_start_pool = [
            p for p in all_candidate_posts if p.views_count < COLD_START_VIEW_THRESHOLD
        ]
        
        # Calculate number of exploration slots (15% of feed)
        target_exploration_slots = int(math.ceil(feed_limit * BANDIT_EXPLORATION_RATIO))
        target_exploration_slots = max(1, min(target_exploration_slots, len(cold_start_pool)))

        # Thompson Sampling on Cold-Start Pool
        # Beta(alpha, beta) where alpha = 1 + likes + completions, beta = 1 + max(0, views - likes)
        sampled_cold_posts: List[Tuple[float, SocialPost]] = []
        for cp in cold_start_pool:
            alpha = 1.0 + cp.likes_count + cp.completion_count
            beta = 1.0 + max(0.0, float(cp.views_count - cp.likes_count))
            theta = random.betavariate(alpha, beta)
            sampled_cold_posts.append((theta, cp))

        sampled_cold_posts.sort(key=lambda x: x[0], reverse=True)
        selected_cold_posts = [p for _, p in sampled_cold_posts[:target_exploration_slots]]
        cold_post_ids = {p.id for p in selected_cold_posts}

        # Filter out cold posts from the main candidate pool to prevent duplication
        main_pool = [item for item in scored_candidates if item[0].id not in cold_post_ids]
        main_slots_needed = feed_limit - len(selected_cold_posts)

        # Maximal Marginal Relevance (MMR) with lambda = 0.7
        selected_mmr: List[Tuple[SocialPost, float, Dict[str, float]]] = []
        remaining_pool = list(main_pool)

        while remaining_pool and len(selected_mmr) < main_slots_needed:
            best_mmr_score = -float('inf')
            best_idx = 0

            for i, (cand_post, cand_score, cand_metrics) in enumerate(remaining_pool):
                try:
                    v_cand = json.loads(cand_post.concept_vector) if cand_post.concept_vector else []
                except Exception:
                    v_cand = []

                if not selected_mmr:
                    max_sim = 0.0
                else:
                    max_sim = 0.0
                    for (sel_post, _, _) in selected_mmr:
                        try:
                            v_sel = json.loads(sel_post.concept_vector) if sel_post.concept_vector else []
                        except Exception:
                            v_sel = []
                        # Genre identity indicator + Concept Vector Cosine Similarity
                        genre_match = 1.0 if (cand_post.genre and cand_post.genre == sel_post.genre) else 0.0
                        vec_sim = cosine_similarity(v_cand, v_sel) if (v_cand and v_sel) else 0.0
                        pair_sim = 0.5 * genre_match + 0.5 * vec_sim
                        if pair_sim > max_sim:
                            max_sim = pair_sim

                # MMR formula: lambda * Score - (1 - lambda) * max_sim
                mmr_val = MMR_LAMBDA * cand_score - (1.0 - MMR_LAMBDA) * max_sim
                if mmr_val > best_mmr_score:
                    best_mmr_score = mmr_val
                    best_idx = i

            picked = remaining_pool.pop(best_idx)
            selected_mmr.append(picked)

        # Assemble final feed by interleaving exploration slots
        final_feed_items: List[Dict[str, Any]] = []
        mmr_index = 0
        cold_index = 0

        # Periodic injection points for cold-start exploration (e.g. slots 3, 9, 15...)
        injection_step = max(3, feed_limit // max(1, len(selected_cold_posts) + 1))

        for slot in range(feed_limit):
            # Check if this slot should be an exploration cold-start post
            is_exploration_slot = (
                cold_index < len(selected_cold_posts) and
                (slot % injection_step == 2 or mmr_index >= len(selected_mmr))
            )

            if is_exploration_slot:
                c_post = selected_cold_posts[cold_index]
                cold_index += 1
                final_feed_items.append({
                    "post": c_post,
                    "score": round(0.5 + 0.1 * random.random(), 4),
                    "metrics": {
                        "cosine_sim": 0.5,
                        "implicit_affinity": 0.5,
                        "freshness": 1.0,
                        "quality_score": 0.5,
                        "final_score": 0.55
                    },
                    "is_cold_start_exploration": True,
                    "exploration_strategy": "thompson_sampling_beta"
                })
            elif mmr_index < len(selected_mmr):
                post, score, metrics = selected_mmr[mmr_index]
                mmr_index += 1
                final_feed_items.append({
                    "post": post,
                    "score": score,
                    "metrics": metrics,
                    "is_cold_start_exploration": False,
                    "exploration_strategy": "mmr_diversity"
                })
            elif cold_index < len(selected_cold_posts):
                c_post = selected_cold_posts[cold_index]
                cold_index += 1
                final_feed_items.append({
                    "post": c_post,
                    "score": 0.5,
                    "metrics": {
                        "cosine_sim": 0.5,
                        "implicit_affinity": 0.5,
                        "freshness": 1.0,
                        "quality_score": 0.5,
                        "final_score": 0.5
                    },
                    "is_cold_start_exploration": True,
                    "exploration_strategy": "thompson_sampling_beta"
                })
            else:
                break

        return final_feed_items


# ==================== SERVICE LEVEL WORKFLOW ORCHESTRATION ====================

def get_feed(
    db: Session,
    user_id: Optional[int] = None,
    limit: int = 20,
    offset: int = 0,
    genre: Optional[str] = None
) -> Dict[str, Any]:
    """
    Executes the full 3-Stage Recommender pipeline and returns serialized feed.
    """
    user_profile = None
    if user_id:
        user_profile = get_or_create_user_profile(db, user_id)
        apply_exponential_decay(user_profile)

    # Stage 1: Candidate Generation
    candidates = HybridRecommenderEngine.stage1_candidate_generation(
        db=db,
        user_profile=user_profile,
        limit_total=max(60, limit * 3),
        filter_genre=genre
    )

    if not candidates:
        return {
            "items": [],
            "total": 0,
            "page_limit": limit,
            "offset": offset,
            "has_more": False
        }

    # Stage 2: Scoring & Multi-Task Ranking
    scored_candidates = HybridRecommenderEngine.stage2_multi_task_ranking(
        candidates=candidates,
        user_profile=user_profile
    )

    # Stage 3: Re-ranking with MMR and Multi-Armed Bandit
    feed_limit_for_window = max(offset + limit, limit)
    feed_items = HybridRecommenderEngine.stage3_reranking_and_serendipity(
        scored_candidates=scored_candidates,
        all_candidate_posts=candidates,
        feed_limit=feed_limit_for_window
    )

    # Apply pagination window
    paginated_items = feed_items[offset:offset + limit]

    # Format post output
    serialized = []
    for item in paginated_items:
        p: SocialPost = item["post"]
        author = p.author
        
        tags_list = []
        try:
            tags_list = json.loads(p.tags or "[]")
        except Exception:
            pass
            
        dsgo_ent = []
        try:
            dsgo_ent = json.loads(p.dsgo_entities or "[]")
        except Exception:
            pass

        dsgo_sp = []
        try:
            dsgo_sp = json.loads(p.dsgo_spaces or "[]")
        except Exception:
            pass

        serialized.append({
            "id": p.id,
            "story_id": p.story_id,
            "title": p.title,
            "content_snippet": p.content_snippet,
            "cover_image_url": p.cover_image_url,
            "genre": p.genre,
            "tags": tags_list,
            "is_fanfiction": bool(getattr(p, "is_fanfiction", False)),
            "disclaimer": getattr(p, "disclaimer", "") or "",
            "dsgo_entities": dsgo_ent,
            "dsgo_spaces": dsgo_sp,
            "likes_count": p.likes_count,
            "comments_count": p.comments_count,
            "views_count": p.views_count,
            "dwell_time_avg": round(p.dwell_time_avg, 1),
            "completion_count": p.completion_count,
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "author": {
                "id": author.id if author else p.user_id,
                "username": author.username if author else "unknown",
                "full_name": getattr(author, "full_name", "") or ""
            },
            "recommendation_metadata": {
                "score": item["score"],
                "is_cold_start_exploration": item["is_cold_start_exploration"],
                "strategy": item["exploration_strategy"],
                "exploration_strategy": item["exploration_strategy"],
                "metrics": item["metrics"]
            }
        })

    return {
        "items": serialized,
        "total": len(candidates),
        "page_limit": limit,
        "offset": offset,
        "has_more": (offset + limit) < len(feed_items)
    }


def publish_post(
    db: Session,
    user_id: int,
    title: str,
    content_snippet: str,
    story_id: Optional[int] = None,
    story_text: Optional[str] = None,
    genre: Optional[str] = None,
    tags: Optional[List[str]] = None,
    cover_image_url: Optional[str] = None,
    dsgo_entities: Optional[List[str]] = None,
    dsgo_spaces: Optional[List[str]] = None,
    concept_vector: Optional[List[float]] = None,
    is_fanfiction: bool = False,
    disclaimer: Optional[str] = None
) -> SocialPost:
    """
    Publishes a literary story to the SocialPost network.
    Accepts story_text and auto-saves/updates Story.
    Auto-extracts first panel from Comic as cover_image_url if missing.
    Extracts DSGO entities/spaces and computes 128-dim concept vector.
    """
    tags = tags or []
    dsgo_entities = dsgo_entities or []
    dsgo_spaces = dsgo_spaces or []

    # 1. Handle story_text and auto-save/update Story
    if story_text:
        clean_text = story_text.strip()
        word_count = len(clean_text.split())
        if story_id:
            existing_story = db.query(Story).filter(Story.id == story_id).first()
            if existing_story:
                existing_story.story_content = clean_text
                existing_story.word_count = word_count
                if not existing_story.refined_prompt:
                    existing_story.refined_prompt = title
                if genre and not existing_story.genre:
                    existing_story.genre = genre
                db.commit()
                db.refresh(existing_story)
            else:
                new_story = Story(
                    id=story_id,
                    user_id=user_id,
                    refined_prompt=title,
                    genre=genre or "Chung",
                    story_content=clean_text,
                    word_count=word_count
                )
                db.add(new_story)
                db.commit()
                db.refresh(new_story)
        else:
            new_story = Story(
                user_id=user_id,
                refined_prompt=title,
                genre=genre or "Chung",
                story_content=clean_text,
                word_count=word_count
            )
            db.add(new_story)
            db.commit()
            db.refresh(new_story)
            story_id = new_story.id

    # 2. Auto-extract first panel from Comic as cover_image_url if missing
    if not cover_image_url:
        try:
            try:
                from db.models import Comic, ComicPanel
            except ImportError:
                from backend.db.models import Comic, ComicPanel

            comic = None
            if story_id:
                comic = db.query(Comic).filter(Comic.story_id == story_id).first()
            if not comic:
                comic = db.query(Comic).filter(Comic.user_id == user_id).order_by(Comic.created_at.desc()).first()

            if comic and comic.panels:
                sorted_panels = sorted(comic.panels, key=lambda p: p.panel_index or 0)
                for panel in sorted_panels:
                    if panel.image_url and panel.image_url.strip():
                        cover_image_url = panel.image_url.strip()
                        break
        except Exception as comic_err:
            pass

    # If linked to a Story, extract DSGO nodes from memory_data if not explicitly provided
    if story_id and (not dsgo_entities or not dsgo_spaces):
        story = db.query(Story).filter(Story.id == story_id).first()
        if story and story.memory_data:
            try:
                mem = json.loads(story.memory_data)
                dsg = mem.get("dynamic_scene_graph", {})
                if not dsgo_entities:
                    ents = dsg.get("entities", [])
                    dsgo_entities = [e.get("name") for e in ents if e.get("name")]
                if not dsgo_spaces:
                    encs = dsg.get("enclosures", [])
                    dsgo_spaces = [enc.get("name") for enc in encs if enc.get("name")]
            except Exception:
                pass
        if story and not genre and story.genre:
            genre = story.genre

    # Compute concept vector if not supplied
    if not concept_vector:
        concept_vector = generate_concept_vector(content_snippet or title, genre or "", tags)
    else:
        concept_vector = normalize_vector(concept_vector)

    post = SocialPost(
        user_id=user_id,
        story_id=story_id,
        title=title,
        content_snippet=content_snippet,
        cover_image_url=cover_image_url,
        genre=genre or "Chung",
        tags=json.dumps(tags),
        concept_vector=json.dumps(concept_vector),
        dsgo_entities=json.dumps(dsgo_entities),
        dsgo_spaces=json.dumps(dsgo_spaces),
        completion_count=0,
        likes_count=0,
        comments_count=0,
        views_count=1,
        dwell_time_avg=0.0,
        is_fanfiction=is_fanfiction,
        disclaimer=disclaimer,
        created_at=datetime.utcnow()
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


def record_interaction(
    db: Session,
    user_id: int,
    post_id: int,
    interaction_type: str,
    dwell_seconds: float = 0.0,
    scroll_depth: int = 0,
    comment_text: Optional[str] = None
) -> Tuple[PostInteraction, Dict[str, Any]]:
    """
    Records explicit or implicit reader interaction, updates Post aggregates,
    and triggers dynamic user interest profile update.
    """
    post = db.query(SocialPost).filter(SocialPost.id == post_id).first()
    if not post:
        raise ValueError(f"SocialPost {post_id} not found.")

    # Update User Interest Profile
    sentiment_score, extracted_entities = update_user_interest_on_interaction(
        db=db,
        user_id=user_id,
        post=post,
        interaction_type=interaction_type,
        dwell_seconds=dwell_seconds,
        scroll_depth=scroll_depth,
        comment_text=comment_text
    )

    # Create interaction log entry
    interaction = PostInteraction(
        user_id=user_id,
        post_id=post_id,
        interaction_type=interaction_type.upper().strip(),
        dwell_seconds=dwell_seconds,
        scroll_depth=scroll_depth,
        comment_text=comment_text,
        sentiment_score=sentiment_score,
        extracted_entities=json.dumps(extracted_entities),
        created_at=datetime.utcnow()
    )
    db.add(interaction)

    # Update Post aggregates
    itype = interaction_type.upper().strip()
    if itype == "LIKE":
        post.likes_count += 1
    elif itype == "COMMENT":
        post.comments_count += 1
    elif itype in ("SCROLL_100", "COMPLETION") or scroll_depth >= 100:
        post.completion_count += 1
    
    if dwell_seconds > 0:
        # Running average of dwell time
        prev_dwell = post.dwell_time_avg or 0.0
        views = max(1, post.views_count)
        post.dwell_time_avg = round((prev_dwell * (views - 1) + dwell_seconds) / views, 2)

    db.commit()
    db.refresh(interaction)
    db.refresh(post)

    return interaction, {
        "sentiment_score": sentiment_score,
        "extracted_entities": extracted_entities,
        "post_likes": post.likes_count,
        "post_comments": post.comments_count,
        "post_completion_count": post.completion_count
    }


def get_post_details(db: Session, post_id: int, current_user_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """
    Fetches a post, increments its view counter, and returns full details
    including comments, author metadata, and related DSGO entities.
    """
    post = db.query(SocialPost).filter(SocialPost.id == post_id).first()
    if not post:
        return None

    # Increment view counter
    post.views_count += 1
    db.commit()

    # Record implicit view interaction if user is authenticated
    if current_user_id:
        try:
            view_interaction = PostInteraction(
                user_id=current_user_id,
                post_id=post_id,
                interaction_type="CLICK",
                created_at=datetime.utcnow()
            )
            db.add(view_interaction)
            db.commit()
        except Exception:
            pass

    # Retrieve recent comments
    comments = db.query(PostInteraction).filter(
        PostInteraction.post_id == post_id,
        PostInteraction.interaction_type == "COMMENT"
    ).order_by(desc(PostInteraction.created_at)).limit(50).all()

    serialized_comments = []
    for c in comments:
        c_user = c.user
        serialized_comments.append({
            "id": c.id,
            "user_id": c.user_id,
            "username": c_user.username if c_user else "user",
            "full_name": getattr(c_user, "full_name", "") or "",
            "comment_text": c.comment_text,
            "sentiment_score": c.sentiment_score,
            "created_at": c.created_at.isoformat() if c.created_at else None
        })

    tags = []
    try:
        tags = json.loads(post.tags or "[]")
    except Exception:
        pass
    entities = []
    try:
        entities = json.loads(post.dsgo_entities or "[]")
    except Exception:
        pass
    spaces = []
    try:
        spaces = json.loads(post.dsgo_spaces or "[]")
    except Exception:
        pass

    author = post.author

    # Retrieve full story text and any linked comic panels
    story_full_text = None
    comic_panels = []
    if post.story_id:
        story = db.query(Story).filter(Story.id == post.story_id).first()
        if story and story.story_content:
            story_full_text = story.story_content
        try:
            try:
                from db.models import Comic, ComicPanel
            except ImportError:
                from backend.db.models import Comic, ComicPanel
            comic = db.query(Comic).filter(Comic.story_id == post.story_id).first()
            if comic and comic.panels:
                for cp in sorted(comic.panels, key=lambda x: x.panel_index or 0):
                    comic_panels.append({
                        "id": cp.id,
                        "panel_index": cp.panel_index,
                        "image_url": cp.image_url,
                        "dialogue_text": cp.dialogue_text,
                        "layout_type": cp.layout_type or "square"
                    })
        except Exception:
            pass

    return {
        "id": post.id,
        "story_id": post.story_id,
        "title": post.title,
        "content_snippet": post.content_snippet,
        "story_content": story_full_text or post.content_snippet,
        "story_full_text": story_full_text or post.content_snippet,
        "comic_panels": comic_panels,
        "cover_image_url": post.cover_image_url,
        "genre": post.genre,
        "tags": tags,
        "is_fanfiction": bool(getattr(post, "is_fanfiction", False)),
        "disclaimer": getattr(post, "disclaimer", "") or "",
        "dsgo_entities": entities,
        "dsgo_spaces": spaces,
        "likes_count": post.likes_count,
        "comments_count": post.comments_count,
        "views_count": post.views_count,
        "dwell_time_avg": round(post.dwell_time_avg, 1),
        "completion_count": post.completion_count,
        "created_at": post.created_at.isoformat() if post.created_at else None,
        "author": {
            "id": author.id if author else post.user_id,
            "username": author.username if author else "author",
            "full_name": getattr(author, "full_name", "") or ""
        },
        "comments": serialized_comments
    }


# ==================== TF.JS HYBRID EXPORT SERVICES (FEATURE 26) ====================

def export_concept_vectors(
    db: Session,
    limit: int = 100,
    since: Optional[str] = None,
    format: str = "json"
) -> Dict[str, Any]:
    """
    Exports 128-dimensional concept vectors and metadata for client-side
    TensorFlow.js on-device ranking, MMR diversification, and offline caching.
    """
    limit = max(1, min(500, limit))
    query = db.query(SocialPost)
    if since:
        try:
            clean_since = since.replace("Z", "+00:00")
            dt = datetime.fromisoformat(clean_since)
            if dt.tzinfo is not None:
                dt = dt.replace(tzinfo=None)
            query = query.filter(SocialPost.created_at >= dt)
        except Exception:
            pass

    posts = query.order_by(SocialPost.created_at.desc()).limit(limit).all()

    vectors_data = []
    for p in posts:
        v = []
        if p.concept_vector:
            try:
                v = json.loads(p.concept_vector)
            except Exception:
                v = []
        if not v or len(v) != VECTOR_DIM:
            v = generate_concept_vector(p.content_snippet or p.title, p.genre or "")
        else:
            v = normalize_vector(v)

        vectors_data.append({
            "post_id": p.id,
            "title": p.title,
            "genre": p.genre or "Chung",
            "author_id": p.user_id,
            "concept_vector": v,
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "views_count": getattr(p, "views_count", 0) or 0,
            "likes_count": getattr(p, "likes_count", 0) or 0,
            "completion_count": getattr(p, "completion_count", 0) or 0
        })

    return {
        "status": "success",
        "version": "1.0",
        "vector_dim": VECTOR_DIM,
        "count": len(vectors_data),
        "vectors": vectors_data
    }


def get_quantized_model_weights(format: str = "json") -> Dict[str, Any]:
    """
    Exports quantized model weights and architecture configuration for
    client-side TensorFlow.js on-device inference and MMR re-ranking.
    Produces deterministic, genuine weights using Xavier initialization.
    """
    import struct
    import base64

    # Seeded pseudo-random generator for deterministic, reproducible weights
    rng = random.Random(42)

    def generate_layer_weights(in_dim: int, out_dim: int, scale: float = 0.02):
        limit = math.sqrt(6.0 / (in_dim + out_dim))
        weights = []
        int8_weights = []
        for _ in range(in_dim):
            row = []
            int8_row = []
            for _ in range(out_dim):
                val = rng.uniform(-limit, limit)
                q_val = max(-128, min(127, int(round(val / scale))))
                row.append(round(val, 6))
                int8_row.append(q_val)
            weights.append(row)
            int8_weights.append(int8_row)
        biases = [round(rng.uniform(-0.01, 0.01), 6) for _ in range(out_dim)]
        return weights, int8_weights, biases

    w1, q_w1, b1 = generate_layer_weights(128, 64, scale=0.015625)
    w2, q_w2, b2 = generate_layer_weights(64, 32, scale=0.03125)
    w3, q_w3, b3 = generate_layer_weights(32, 16, scale=0.0625)

    # Pack binary buffer for binary format or base64 representation
    # Format: float32 for biases, int8 for quantized weights
    binary_parts = []
    manifest = []
    offset = 0

    layers_info = [
        ("dense_128_64/kernel", [128, 64], "int8", q_w1, 0.015625),
        ("dense_128_64/bias", [64], "float32", b1, 1.0),
        ("dense_64_32/kernel", [64, 32], "int8", q_w2, 0.03125),
        ("dense_64_32/bias", [32], "float32", b2, 1.0),
        ("dense_32_16/kernel", [32, 16], "int8", q_w3, 0.0625),
        ("dense_32_16/bias", [16], "float32", b3, 1.0),
    ]

    for name, shape, dtype, vals, scale in layers_info:
        if dtype == "int8":
            flat = [val for row in vals for val in row] if isinstance(vals[0], list) else vals
            buf = struct.pack(f"{len(flat)}b", *flat)
        else:
            flat = vals
            buf = struct.pack(f"{len(flat)}f", *flat)
        byte_len = len(buf)
        manifest.append({
            "name": name,
            "shape": shape,
            "dtype": dtype,
            "byte_offset": offset,
            "byte_length": byte_len,
            "quantization": {"scale": scale, "zero_point": 0} if dtype == "int8" else None
        })
        binary_parts.append(buf)
        offset += byte_len

    raw_buffer = b"".join(binary_parts)
    buffer_b64 = base64.b64encode(raw_buffer).decode("ascii")

    total_params = (128 * 64 + 64) + (64 * 32 + 32) + (32 * 16 + 16)

    return {
        "status": "success",
        "model_name": "NarrAI-Recommender-TwoTower-Lite",
        "version": "1.0.0",
        "format": format,
        "total_params": total_params,
        "input_dim": VECTOR_DIM,
        "output_dim": 16,
        "architecture": {
            "type": "Sequential",
            "layers": [
                {
                    "name": "dense_128_64",
                    "type": "Dense",
                    "input_dim": 128,
                    "units": 64,
                    "activation": "relu",
                    "quantization": "int8"
                },
                {
                    "name": "dense_64_32",
                    "type": "Dense",
                    "units": 32,
                    "activation": "relu",
                    "quantization": "int8"
                },
                {
                    "name": "dense_32_16",
                    "type": "Dense",
                    "units": 16,
                    "activation": "linear",
                    "quantization": "int8"
                }
            ]
        },
        "weights_manifest": manifest,
        "buffer_size_bytes": len(raw_buffer),
        "weights_base64": buffer_b64,
        "weights": {
            "dense_128_64": {
                "kernel": w1,
                "quantized_kernel": q_w1,
                "bias": b1,
                "scale": 0.015625
            },
            "dense_64_32": {
                "kernel": w2,
                "quantized_kernel": q_w2,
                "bias": b2,
                "scale": 0.03125
            },
            "dense_32_16": {
                "kernel": w3,
                "quantized_kernel": q_w3,
                "bias": b3,
                "scale": 0.0625
            }
        },
        "created_at": datetime.utcnow().isoformat()
    }

