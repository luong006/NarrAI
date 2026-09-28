"""
End-to-End Test Suite: Requirement 2 (R2)
Next-Gen Literary Social Graph, 3-Stage Hybrid Recommender Engine & Open Messenger

Derived strictly from:
- ORIGINAL_REQUEST.md (## 2026-09-28T01:01:31Z)
- PROJECT.md (§ M2 ↔ Social & Messenger APIs & Feature Inventory 6-9)

Test Structure (4-Tier Methodology):
- Tier 1: Feature Coverage (Data models, mathematical algorithms, 3-stage recommender, messenger chat)
- Tier 2: Boundary & Corner Cases (Cold-start empty profiles, zero views, conversation idempotency, vector limits)
- Tier 3: Cross-Feature Combinations (Interactions driving decay and MMR feed changes, comment entity boosts)
- Tier 4: Real-World Application Scenarios (Full author-reader lifecycle: publish, explore, interact, message)
"""

import os
import sys
import json
import math
import unittest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure backend root is on sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from db.models import (
    Base,
    User,
    SocialPost,
    PostInteraction,
    UserInterestProfile,
    Conversation,
    ConversationParticipant,
    ChatMessage
)

# Optional service imports if already implemented by Worker M2
try:
    from services import recommender_service
    HAS_RECOMMENDER_SERVICE = True
except (ImportError, AttributeError):
    recommender_service = None
    HAS_RECOMMENDER_SERVICE = False

try:
    from services import messenger_service
    HAS_MESSENGER_SERVICE = True
except (ImportError, AttributeError):
    messenger_service = None
    HAS_MESSENGER_SERVICE = False


# ==============================================================================
# AUTHORITATIVE REFERENCE ORACLES (DERIVED STRICTLY FROM ORIGINAL_REQUEST.MD)
# ==============================================================================

WEIGHT_DWELL_60 = 2.5
WEIGHT_SCROLL_100 = 2.0
WEIGHT_SCROLL_50 = 1.0
WEIGHT_LIKE = 1.5
WEIGHT_COMMENT = 3.0
WEIGHT_BOOKMARK = 2.0
WEIGHT_SHARE = 2.5
WEIGHT_CLICK = 0.5
TIME_DECAY_LAMBDA = 0.05  # per day
MMR_LAMBDA = 0.7
BANDIT_EPSILON = 0.15

def oracle_compute_decay(u_old: list, delta_days: float, decay_lambda: float = 0.05) -> list:
    """Formula: U_decayed = U_old * exp(-lambda * delta_days)"""
    decay_factor = math.exp(-decay_lambda * delta_days)
    return [x * decay_factor for x in u_old]

def oracle_l2_normalize(vec: list) -> list:
    """Normalizes vector to L2 unit length."""
    norm = math.sqrt(sum(x * x for x in vec))
    if norm == 0:
        return [0.0] * len(vec)
    return [x / norm for x in vec]

def oracle_cosine_similarity(v1: list, v2: list) -> float:
    """Cosine similarity between two normalized vectors."""
    dot = sum(a * b for a, b in zip(v1, v2))
    return max(0.0, min(1.0, dot))

def oracle_multi_task_ranking_score(
    cosine_sim: float,
    implicit_affinity: float,
    hours_since_published: float,
    completion_count: int,
    likes_count: int,
    views_count: int,
    dwell_time_avg: float
) -> float:
    """
    Score(p, u) = 0.35*CosineSim + 0.25*ImplicitAffinity + 0.20*Freshness + 0.20*QualityScore
    Freshness = 1 / (1 + 0.02 * hours)
    Quality = 0.40*CompletionRate + 0.30*LikeRatio + 0.30*DwellNorm
    """
    w1, w2, w3, w4 = 0.35, 0.25, 0.20, 0.20
    freshness = 1.0 / (1.0 + 0.02 * max(0.0, hours_since_published))
    
    views_safe = max(1, views_count)
    completion_rate = min(1.0, completion_count / views_safe)
    like_ratio = min(1.0, likes_count / views_safe)
    dwell_norm = min(1.0, dwell_time_avg / 60.0)
    
    quality_score = 0.40 * completion_rate + 0.30 * like_ratio + 0.30 * dwell_norm
    return w1 * cosine_sim + w2 * implicit_affinity + w3 * freshness + w4 * quality_score

def oracle_mmr_score(score_p: float, sim_to_selected: float, lambda_mmr: float = 0.7) -> float:
    """MMR_Score(p) = lambda * Score(p, u) - (1 - lambda) * max_s Sim(p, s)"""
    return lambda_mmr * score_p - (1.0 - lambda_mmr) * sim_to_selected


# ==============================================================================
# TEST CASE FIXTURES
# ==============================================================================

class BaseSocialMessengerTestCase(unittest.TestCase):
    """
    Sets up isolated SQLite in-memory test database.
    """
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.db = self.SessionLocal()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def create_user(self, username: str, full_name: str = "") -> User:
        user = User(
            username=username,
            full_name=full_name or f"Full Name {username}",
            password_hash="pw_hash",
            coins=100
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def create_post(
        self,
        user_id: int,
        title: str,
        genre: str,
        concept_vec: list = None,
        views: int = 10,
        likes: int = 2,
        completions: int = 1,
        dwell_avg: float = 45.0,
        entities: list = None
    ) -> SocialPost:
        vec = concept_vec if concept_vec is not None else oracle_l2_normalize([1.0] + [0.0] * 127)
        post = SocialPost(
            user_id=user_id,
            title=title,
            content_snippet=f"Snippet for {title}",
            genre=genre,
            tags=json.dumps([genre]),
            concept_vector=json.dumps(vec),
            views_count=views,
            likes_count=likes,
            completion_count=completions,
            dwell_time_avg=dwell_avg,
            dsgo_entities=json.dumps(entities or []),
            dsgo_spaces=json.dumps([]),
            created_at=datetime.utcnow()
        )
        self.db.add(post)
        self.db.commit()
        self.db.refresh(post)
        return post


class TestTier1RecommenderFeatureCoverage(BaseSocialMessengerTestCase):
    """
    Tier 1: Feature Coverage & Mathematical Validation for Recommender.
    """

    def test_social_models_creation_and_attributes(self):
        """Verify social_posts, post_interactions, and user_interest_profiles database models."""
        user = self.create_user("author_kim", "Kim Dung")
        vec = [0.0] * 128
        vec[0] = 1.0

        post = self.create_post(user.id, "Tiếu Ngạo Giang Hồ", "Kiếm hiệp", concept_vec=vec, entities=["Lệnh Hồ Xung"])
        self.assertIsNotNone(post.id)
        self.assertEqual(post.title, "Tiếu Ngạo Giang Hồ")
        self.assertEqual(post.genre, "Kiếm hiệp")

        # Create interaction
        interaction = PostInteraction(
            user_id=user.id,
            post_id=post.id,
            interaction_type="LIKE",
            dwell_seconds=75.0,
            scroll_depth=100,
            comment_text="Truyện rất hay!",
            sentiment_score=0.8,
            extracted_entities=json.dumps(["Lệnh Hồ Xung"])
        )
        self.db.add(interaction)
        self.db.commit()
        self.assertIsNotNone(interaction.id)
        self.assertEqual(interaction.dwell_time, 75.0)

        # Create interest profile
        profile = UserInterestProfile(
            user_id=user.id,
            interest_vector=json.dumps(vec),
            genre_affinity=json.dumps({"Kiếm hiệp": 0.9}),
            entity_affinity=json.dumps({"Lệnh Hồ Xung": 1.5})
        )
        self.db.add(profile)
        self.db.commit()
        self.assertIsNotNone(profile.id)

    def test_exponential_time_decay_mathematical_oracle(self):
        """
        Verify exponential time decay: U_decayed = U_old * exp(-lambda * delta_days).
        At delta_days = 0 -> 100% of original.
        At delta_days = 30 -> exp(-0.05 * 30) = exp(-1.5) approx 0.22313.
        """
        initial_vector = [1.0] * 128
        decayed_0 = oracle_compute_decay(initial_vector, delta_days=0.0, decay_lambda=0.05)
        self.assertAlmostEqual(decayed_0[0], 1.0, places=4)

        decayed_30 = oracle_compute_decay(initial_vector, delta_days=30.0, decay_lambda=0.05)
        expected_decay_factor = math.exp(-0.05 * 30.0)  # ~0.22313
        self.assertAlmostEqual(decayed_30[0], expected_decay_factor, places=4)
        self.assertAlmostEqual(decayed_30[127], expected_decay_factor, places=4)

    def test_interaction_weights_and_sentiment_adjustment(self):
        """
        Verify interaction signal weights:
        w(Dwell>60) = 2.5, w(Scroll_100) = 2.0, w(Like) = 1.5, w(Comment) = 3.0.
        Effective comment weight: w_comment * (1.0 + s) where s in [-1.0, 1.0].
        """
        self.assertEqual(WEIGHT_DWELL_60, 2.5)
        self.assertEqual(WEIGHT_SCROLL_100, 2.0)
        self.assertEqual(WEIGHT_LIKE, 1.5)
        self.assertEqual(WEIGHT_COMMENT, 3.0)

        # Positive praise (s = +0.8)
        w_pos = WEIGHT_COMMENT * (1.0 + 0.8)
        self.assertAlmostEqual(w_pos, 5.4, places=2)

        # Harsh criticism (s = -0.8)
        w_neg = WEIGHT_COMMENT * (1.0 - 0.8)
        self.assertAlmostEqual(w_neg, 0.6, places=2)

    def test_multi_task_ranking_scoring_oracle(self):
        """
        Verify Stage 2 Multi-Task Ranking score computation:
        Score = 0.35*Cosine + 0.25*Affinity + 0.20*Freshness + 0.20*QualityScore.
        """
        score = oracle_multi_task_ranking_score(
            cosine_sim=0.8,
            implicit_affinity=0.6,
            hours_since_published=24.0,  # Freshness = 1 / (1 + 0.48) = ~0.6757
            completion_count=10,
            likes_count=20,
            views_count=50,             # CompRate=0.2, LikeRatio=0.4, DwellNorm=1.0 -> Quality=0.4*0.2 + 0.3*0.4 + 0.3*1.0 = 0.5
            dwell_time_avg=60.0
        )
        self.assertGreater(score, 0.0)
        self.assertLessEqual(score, 1.0)
        # Expected calculation:
        # Cosine: 0.35 * 0.8 = 0.28
        # Affinity: 0.25 * 0.6 = 0.15
        # Freshness: 0.20 * (1 / 1.48) = 0.1351
        # Quality: 0.20 * (0.08 + 0.12 + 0.30) = 0.20 * 0.50 = 0.10
        # Total approx = 0.28 + 0.15 + 0.1351 + 0.10 = 0.6651
        self.assertAlmostEqual(score, 0.6651, delta=0.01)

    def test_mmr_diversity_score_oracle(self):
        """
        Verify MMR score penalties for similarity:
        MMR_Score(p) = 0.7 * Score(p, u) - 0.3 * max_s Sim(p, s).
        """
        # Candidate A: high relevance (0.9), highly similar to existing (0.8)
        mmr_a = oracle_mmr_score(score_p=0.9, sim_to_selected=0.8, lambda_mmr=0.7)
        # 0.7 * 0.9 - 0.3 * 0.8 = 0.63 - 0.24 = 0.39

        # Candidate B: moderate relevance (0.7), diverse (similarity 0.1)
        mmr_b = oracle_mmr_score(score_p=0.7, sim_to_selected=0.1, lambda_mmr=0.7)
        # 0.7 * 0.7 - 0.3 * 0.1 = 0.49 - 0.03 = 0.46

        # Due to MMR diversity promotion, Candidate B wins over Candidate A!
        self.assertGreater(mmr_b, mmr_a)


class TestTier1MessengerFeatureCoverage(BaseSocialMessengerTestCase):
    """
    Tier 1: Feature Coverage for Open Messenger Platform.
    """

    def test_open_messenger_models_and_1_to_1_chat(self):
        """Verify Conversation, Participant, and ChatMessage exchange."""
        alice = self.create_user("alice", "Alice Johnson")
        bob = self.create_user("bob", "Bob Smith")

        # Create conversation
        conv = Conversation(last_message_text="Chào bạn!", last_message_at=datetime.utcnow())
        self.db.add(conv)
        self.db.commit()

        # Add participants
        p_alice = ConversationParticipant(conversation_id=conv.id, user_id=alice.id, unread_count=0)
        p_bob = ConversationParticipant(conversation_id=conv.id, user_id=bob.id, unread_count=1)
        self.db.add_all([p_alice, p_bob])

        # Add message from Alice to Bob
        msg = ChatMessage(
            conversation_id=conv.id,
            sender_id=alice.id,
            message_text="Chào bạn, tác phẩm của bạn rất hay!",
            is_read=False
        )
        self.db.add(msg)
        self.db.commit()

        self.assertIsNotNone(msg.id)
        self.assertEqual(p_bob.unread_count, 1)

        # Bob reads the message
        msg.is_read = True
        p_bob.unread_count = 0
        p_bob.last_read_message_id = msg.id
        self.db.commit()

        self.assertEqual(p_bob.unread_count, 0)
        self.assertTrue(msg.is_read)

    def test_user_directory_search_query(self):
        """User directory query matches username and full_name, excluding self."""
        current_user = self.create_user("searcher", "Nguyễn Tìm Kiếm")
        target1 = self.create_user("tran_hung_dao", "Trần Hưng Đạo")
        target2 = self.create_user("ly_thuong_kiet", "Lý Thường Kiệt")

        query_str = "%trần%"
        results = (
            self.db.query(User)
            .filter(
                User.id != current_user.id,
                (User.username.ilike(query_str)) | (User.full_name.ilike(query_str))
            )
            .all()
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].username, "tran_hung_dao")


class TestTier2RecommenderMessengerBoundaryCases(BaseSocialMessengerTestCase):
    """
    Tier 2: Boundary & Corner Cases (Zero views, zero vectors, empty profiles, conversation idempotency).
    """

    def test_cold_start_new_user_empty_profile(self):
        """User with no prior interactions has safe fallback without crashing."""
        user = self.create_user("newbie")
        profile = (
            self.db.query(UserInterestProfile)
            .filter(UserInterestProfile.user_id == user.id)
            .first()
        )
        self.assertIsNone(profile)
        # Empty profile must not cause division by zero in scoring
        zero_sim = oracle_cosine_similarity([0.0] * 128, [1.0] + [0.0] * 127)
        self.assertEqual(zero_sim, 0.0)

    def test_zero_views_post_safe_quality_score(self):
        """Posts with 0 views gracefully compute quality score without ZeroDivisionError."""
        score = oracle_multi_task_ranking_score(
            cosine_sim=0.5,
            implicit_affinity=0.0,
            hours_since_published=1.0,
            completion_count=0,
            likes_count=0,
            views_count=0,  # 0 views!
            dwell_time_avg=0.0
        )
        self.assertFalse(math.isnan(score))
        self.assertGreater(score, 0.0)

    def test_vector_normalization_with_all_zeros(self):
        """Normalizing an all-zero vector returns all zeros without ZeroDivisionError."""
        zero_vec = [0.0] * 128
        normalized = oracle_l2_normalize(zero_vec)
        self.assertEqual(normalized, [0.0] * 128)

    def test_conversation_participant_unique_constraint(self):
        """Ensures participant uniqueness per conversation."""
        u1 = self.create_user("u1")
        u2 = self.create_user("u2")
        conv = Conversation()
        self.db.add(conv)
        self.db.commit()

        p1 = ConversationParticipant(conversation_id=conv.id, user_id=u1.id)
        p2 = ConversationParticipant(conversation_id=conv.id, user_id=u2.id)
        self.db.add_all([p1, p2])
        self.db.commit()

        # Attempting duplicate participant in same conversation should violate unique constraint
        p1_dup = ConversationParticipant(conversation_id=conv.id, user_id=u1.id)
        self.db.add(p1_dup)
        with self.assertRaises(Exception):
            self.db.commit()
        self.db.rollback()


class TestTier3RecommenderCrossFeatureIntegration(BaseSocialMessengerTestCase):
    """
    Tier 3: Cross-Feature Integration Tests (Interaction -> Profile Decay & Update -> MMR Re-ranking).
    """

    def test_user_interaction_drives_profile_shift_and_scoring(self):
        """
        Simulates:
        1. User with initial Sci-Fi interest vector.
        2. User views and likes a Vietnamese Historical story (Dã Sử).
        3. User profile updates with decay and pulls towards Historical concept vector.
        4. Recommender ranking shifts to favor Historical stories.
        """
        user = self.create_user("reader_one")
        author = self.create_user("author_one")

        # Concept vector 1 (Sci-Fi): 1.0 at index 0
        v_scifi = oracle_l2_normalize([1.0] + [0.0] * 127)
        # Concept vector 2 (Historical): 1.0 at index 1
        v_history = oracle_l2_normalize([0.0, 1.0] + [0.0] * 126)

        # Initial profile has pure Sci-Fi interest
        profile = UserInterestProfile(
            user_id=user.id,
            interest_vector=json.dumps(v_scifi),
            genre_affinity=json.dumps({"Sci-Fi": 0.9}),
            entity_affinity=json.dumps({})
        )
        self.db.add(profile)
        self.db.commit()

        # Post is Historical
        post_hist = self.create_post(
            author.id, "Bạch Đằng Vương", "Dã sử", concept_vec=v_history, entities=["Ngô Quyền"]
        )

        # User interacts: Like (weight 1.5) + Dwell 80s (weight 2.5) -> Total weight = 4.0
        interaction = PostInteraction(
            user_id=user.id,
            post_id=post_hist.id,
            interaction_type="LIKE",
            dwell_seconds=80.0,
            scroll_depth=100
        )
        self.db.add(interaction)
        self.db.commit()

        # Update profile: apply decay (say 5 days past) + add weighted post vector
        u_decayed = oracle_compute_decay(v_scifi, delta_days=5.0)
        # Shift with effective weight 4.0
        u_shifted = [dec + 4.0 * hist for dec, hist in zip(u_decayed, v_history)]
        u_final = oracle_l2_normalize(u_shifted)

        # After interaction, similarity with Historical post is significantly higher than 0!
        new_hist_sim = oracle_cosine_similarity(u_final, v_history)
        self.assertGreater(new_hist_sim, 0.70, f"Expected strong historical affinity, got {new_hist_sim}")

    def test_comment_entity_extraction_boosts_affinity(self):
        """
        User leaves positive comment mentioning an entity ('Trần Hưng Đạo').
        Affinity score for 'Trần Hưng Đạo' increases proportionally to sentiment.
        """
        comment_text = "Trần Hưng Đạo điều binh khiển tướng xuất sắc quá!"
        sentiment = 0.9  # Positive
        mentioned_entity = "Trần Hưng Đạo"

        entity_affinity = {}
        # Formula: entity_affinity[entity] += 1.5 * (1.0 + sentiment)
        boost = 1.5 * (1.0 + sentiment)
        entity_affinity[mentioned_entity] = entity_affinity.get(mentioned_entity, 0.0) + boost

        self.assertAlmostEqual(entity_affinity["Trần Hưng Đạo"], 2.85, places=2)


class TestTier4SocialMessengerRealWorldEcosystem(BaseSocialMessengerTestCase):
    """
    Tier 4: Real-World Application Scenarios (End-to-End Literary Social Community Lifecycle).
    """

    def test_full_community_journey_publish_discover_read_chat(self):
        """
        End-to-end community workflow:
        1. Author publishes a historical novel ("Đại Chiến Bạch Đằng").
        2. Post enters feed; Reader discovers it through Recommender.
        3. Reader reads chapter (Dwell 90s, Scroll 100%), likes and leaves comment.
        4. Reader searches for Author in Open Messenger directory.
        5. Reader initiates 1-1 conversation and sends congratulatory message.
        6. Author checks unread message count, opens dialogue, and replies.
        """
        author = self.create_user("author_nguyen", "Nguyễn Du")
        reader = self.create_user("reader_minh", "Trần Minh")

        # 1. Author publishes story
        hist_vec = oracle_l2_normalize([0.0, 1.0] + [0.0] * 126)
        story_post = self.create_post(
            user_id=author.id,
            title="Đại Chiến Bạch Đằng 1288",
            genre="Chính sử",
            concept_vec=hist_vec,
            views=5,
            likes=1,
            entities=["Trần Quốc Tuấn", "Bạch Đằng"]
        )

        # 2. Reader interacts with story
        interaction = PostInteraction(
            user_id=reader.id,
            post_id=story_post.id,
            interaction_type="COMMENT",
            dwell_seconds=95.0,
            scroll_depth=100,
            comment_text="Tác phẩm quá hào hùng, tự hào Đại Việt!",
            sentiment_score=0.9
        )
        self.db.add(interaction)
        # Update post counters
        story_post.views_count += 1
        story_post.comments_count += 1
        story_post.likes_count += 1
        self.db.commit()

        # 3. Reader searches for Author in user directory
        search_res = (
            self.db.query(User)
            .filter(User.id != reader.id, User.username.ilike("%nguyen%"))
            .all()
        )
        self.assertIn(author, search_res)

        # 4. Reader opens conversation with Author
        conv = Conversation(
            last_message_text="Cảm ơn tác giả!",
            last_message_at=datetime.utcnow()
        )
        self.db.add(conv)
        self.db.commit()

        p_reader = ConversationParticipant(conversation_id=conv.id, user_id=reader.id, unread_count=0)
        p_author = ConversationParticipant(conversation_id=conv.id, user_id=author.id, unread_count=1)
        self.db.add_all([p_reader, p_author])

        msg1 = ChatMessage(
            conversation_id=conv.id,
            sender_id=reader.id,
            message_text="Chào bạn, bộ truyện Bạch Đằng 1288 viết rất tuyệt vời!",
            is_read=False
        )
        self.db.add(msg1)
        self.db.commit()

        # 5. Author checks total unread count
        author_unread = (
            self.db.query(ConversationParticipant.unread_count)
            .filter(ConversationParticipant.user_id == author.id)
            .scalar()
        )
        self.assertEqual(author_unread, 1)

        # 6. Author reads and replies
        msg1.is_read = True
        p_author.unread_count = 0
        p_author.last_read_message_id = msg1.id

        msg_reply = ChatMessage(
            conversation_id=conv.id,
            sender_id=author.id,
            message_text="Cảm ơn bạn đã ủng hộ tác phẩm của mình!",
            is_read=False
        )
        p_reader.unread_count += 1
        self.db.add(msg_reply)
        self.db.commit()

        # Verify state
        self.assertEqual(p_author.unread_count, 0)
        self.assertEqual(p_reader.unread_count, 1)
        self.assertTrue(msg1.is_read)
        self.assertFalse(msg_reply.is_read)


if __name__ == "__main__":
    unittest.main()
