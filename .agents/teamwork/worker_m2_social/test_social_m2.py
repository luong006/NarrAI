"""
Comprehensive Verification Suite for Milestone 2:
- Next-Gen Recommendation Engine (3-Stage Hybrid, MMR, Multi-Armed Bandit, Dynamic Decay, Sentiment)
- Open Messenger (Directory Search, Idempotent 1-1 Conversations, Real-Time Persistence, Unread Tracking)
- Social & Messenger Routers
"""

import unittest
import math
import json
import os
import sys
from datetime import datetime, timedelta

# Ensure backend directory is in sys.path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "backend"))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

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

from services.recommender_service import (
    VECTOR_DIM,
    DECAY_LAMBDA_PER_DAY,
    MMR_LAMBDA,
    BANDIT_EXPLORATION_RATIO,
    SIGNAL_WEIGHTS,
    W_COSINE,
    W_AFFINITY,
    W_FRESHNESS,
    W_QUALITY,
    normalize_vector,
    cosine_similarity,
    generate_concept_vector,
    extract_sentiment_and_entities,
    get_or_create_user_profile,
    apply_exponential_decay,
    update_user_interest_on_interaction,
    HybridRecommenderEngine,
    get_feed,
    publish_post,
    record_interaction,
    get_post_details
)

from services.messenger_service import (
    sanitize_message_text,
    search_users,
    get_or_create_conversation,
    send_message,
    get_conversation_messages,
    list_conversations,
    get_total_unread_count
)

from routers.social_router import router as social_router
from routers.messenger_router import router as messenger_router


class TestMilestone2SocialAndMessenger(unittest.TestCase):
    def setUp(self):
        """Creates an in-memory SQLite database for test isolation."""
        self.engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.db = self.Session()

        # Seed test users
        self.user1 = User(id=1, username="writer_viet", full_name="Nguyen Van A", coins=100)
        self.user2 = User(id=2, username="reader_minh", full_name="Tran Thi B", coins=50)
        self.user3 = User(id=3, username="scifi_lover", full_name="Le Van C", coins=30)
        self.db.add_all([self.user1, self.user2, self.user3])
        self.db.commit()

    def tearDown(self):
        self.db.close()

    # ==================== 1. VECTOR UTILITIES & MATH ====================

    def test_normalize_vector_and_dimension(self):
        """Test vector normalization produces 128 dimensions and unit L2 norm."""
        raw = [1.0] * 50
        normed = normalize_vector(raw)
        self.assertEqual(len(normed), VECTOR_DIM)
        l2 = math.sqrt(sum(x * x for x in normed))
        self.assertAlmostEqual(l2, 1.0, places=5)

    def test_cosine_similarity(self):
        """Test cosine similarity bounded between 0.0 and 1.0."""
        v1 = normalize_vector([1.0, 0.0, 0.0])
        v2 = normalize_vector([1.0, 0.0, 0.0])
        v3 = normalize_vector([0.0, 1.0, 0.0])

        sim_identical = cosine_similarity(v1, v2)
        sim_orthogonal = cosine_similarity(v1, v3)

        self.assertAlmostEqual(sim_identical, 1.0, places=5)
        self.assertAlmostEqual(sim_orthogonal, 0.0, places=5)

    def test_generate_concept_vector_deterministic(self):
        """Test concept vector generator is deterministic and produces unit vectors."""
        vec1 = generate_concept_vector("Tran Hung Dao danh tran Bach Dang", "Lich Su", ["Hao Khi", "Chien Tran"])
        vec2 = generate_concept_vector("Tran Hung Dao danh tran Bach Dang", "Lich Su", ["Hao Khi", "Chien Tran"])
        self.assertEqual(vec1, vec2)
        self.assertEqual(len(vec1), VECTOR_DIM)
        l2 = math.sqrt(sum(x * x for x in vec1))
        self.assertAlmostEqual(l2, 1.0, places=5)

        # Different genre should produce distinct vector with lower cosine similarity
        vec_scifi = generate_concept_vector("Cyberpunk robot phieu luu", "Cyberpunk", ["AI", "Tuong Lai"])
        sim = cosine_similarity(vec1, vec_scifi)
        self.assertLess(sim, 0.8)

    # ==================== 2. SENTIMENT & ENTITY EXTRACTION ====================

    def test_sentiment_extraction(self):
        """Test sentiment score extraction for positive and negative Vietnamese comments."""
        pos_text = "Tác phẩm quá tuyệt vời, đỉnh cao và rất cuốn hút!"
        neg_text = "Truyện dở tệ, nhảm nhí và quá buồn ngủ."

        pos_score, _ = extract_sentiment_and_entities(pos_text)
        neg_score, _ = extract_sentiment_and_entities(neg_text)

        self.assertGreater(pos_score, 0.5)
        self.assertLess(neg_score, -0.5)

    def test_entity_extraction_from_comment(self):
        """Test extraction of candidate DSGO entities mentioned in comment."""
        comment = "Cảnh Trần Hưng Đạo hội quân ở Sông Bạch Đằng thực sự quá xúc động!"
        candidates = ["Trần Hưng Đạo", "Sông Bạch Đằng", "Nguyễn Huệ"]
        sentiment, entities = extract_sentiment_and_entities(comment, candidates)

        self.assertIn("Trần Hưng Đạo", entities)
        self.assertIn("Sông Bạch Đằng", entities)
        self.assertNotIn("Nguyễn Huệ", entities)

    # ==================== 3. EXPONENTIAL DECAY & DYNAMIC INTEREST ====================

    def test_exponential_decay(self):
        """Test that user interest decays with lambda = 0.05/day."""
        profile = get_or_create_user_profile(self.db, user_id=1)
        initial_vec = normalize_vector([1.0] * 128)
        profile.interest_vector = json.dumps(initial_vec)
        profile.genre_affinity = json.dumps({"Lich Su": 10.0})
        profile.last_decay_time = datetime.utcnow() - timedelta(days=10)
        self.db.commit()

        apply_exponential_decay(profile)
        expected_decay = math.exp(-0.05 * 10)  # ~0.6065

        decayed_genre = json.loads(profile.genre_affinity)
        self.assertAlmostEqual(decayed_genre["Lich Su"], 10.0 * expected_decay, places=2)

    def test_interaction_signals_and_weights(self):
        """Test that signal weights match specifications: Dwell>60s=2.5, Scroll_100=2.0, Like=1.5, Comment=3.0."""
        self.assertEqual(SIGNAL_WEIGHTS["DWELL_TIME"], 2.5)
        self.assertEqual(SIGNAL_WEIGHTS["SCROLL_100"], 2.0)
        self.assertEqual(SIGNAL_WEIGHTS["LIKE"], 1.5)
        self.assertEqual(SIGNAL_WEIGHTS["COMMENT"], 3.0)

        # Publish a post
        post = publish_post(
            db=self.db,
            user_id=1,
            title="Đại Việt Sử Ký",
            content_snippet="Hào khí Đông A vang dội khắp bến Bình Than...",
            genre="Lịch Sử",
            tags=["Chiến Trận", "Dã Sử"],
            dsgo_entities=["Trần Quốc Tuấn"],
            dsgo_spaces=["Bến Bình Than"]
        )

        # Record interaction with comment
        _, meta = record_interaction(
            db=self.db,
            user_id=2,
            post_id=post.id,
            interaction_type="COMMENT",
            comment_text="Trần Quốc Tuấn miêu tả quá tuyệt vời và hào hùng!"
        )

        # Verify post comments count incremented
        self.assertEqual(post.comments_count, 1)

        # Verify user profile updated
        profile = self.db.query(UserInterestProfile).filter_by(user_id=2).first()
        self.assertIsNotNone(profile)
        genre_aff = json.loads(profile.genre_affinity)
        self.assertIn("Lịch Sử", genre_aff)
        self.assertGreater(genre_aff["Lịch Sử"], 0.0)

        entity_aff = json.loads(profile.entity_affinity)
        self.assertIn("Trần Quốc Tuấn", entity_aff)

    # ==================== 4. 3-STAGE HYBRID RECOMMENDER ENGINE ====================

    def test_3_stage_hybrid_recommender(self):
        """Test candidate generation, multi-task ranking, and MMR/Bandit re-ranking."""
        # Create a series of posts with different genres and view counts
        p1 = publish_post(self.db, 1, "Hịch Tướng Sĩ", "Sông Bạch Đằng cuộn sóng...", genre="Lịch Sử", dsgo_entities=["Trần Hưng Đạo"])
        p2 = publish_post(self.db, 1, "Thành Phố 2099", "Ánh đèn neon và cyborg...", genre="Cyberpunk")
        p3 = publish_post(self.db, 1, "Thiên Mệnh Kiếm", "Kiếm khí tung hoành giang hồ...", genre="Kiếm Hiệp")
        p4 = publish_post(self.db, 1, "Tác Phẩm Mới Tân Binh", "Một góc nhìn hoàn toàn mới...", genre="Hiện Đại")

        # Set specific interactions to test QualityScore and Cold-Start
        p1.views_count = 100
        p1.likes_count = 30
        p1.completion_count = 50
        p1.dwell_time_avg = 75.0

        p4.views_count = 5  # Cold-start pool (< 30)

        self.db.commit()

        # Generate feed for user who likes Lịch Sử
        feed = get_feed(self.db, user_id=2, limit=10)
        self.assertIn("items", feed)
        self.assertGreater(len(feed["items"]), 0)

        # Verify recommendation metadata contains genuine scores
        first_item = feed["items"][0]
        meta = first_item["recommendation_metadata"]
        self.assertIn("score", meta)
        self.assertIn("metrics", meta)
        self.assertIn("cosine_sim", meta["metrics"])
        self.assertIn("implicit_affinity", meta["metrics"])
        self.assertIn("freshness", meta["metrics"])
        self.assertIn("quality_score", meta["metrics"])

        # Check that cold-start exploration flag exists in feed items
        has_exploration_slot = any(item["recommendation_metadata"]["is_cold_start_exploration"] for item in feed["items"])
        self.assertTrue(has_exploration_slot)

    # ==================== 5. OPEN MESSENGER SERVICE ====================

    def test_user_directory_search(self):
        """Test user search across all users by username and full_name."""
        results = search_users(self.db, query="viet", current_user_id=2)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["username"], "writer_viet")

        results_by_name = search_users(self.db, query="Tran Thi", current_user_id=1)
        self.assertEqual(len(results_by_name), 1)
        self.assertEqual(results_by_name[0]["username"], "reader_minh")

    def test_idempotent_conversation_creation(self):
        """Test get_or_create_conversation is strictly idempotent between any two users."""
        conv1, created1 = get_or_create_conversation(self.db, user_id_1=1, user_id_2=2)
        self.assertTrue(created1)

        conv2, created2 = get_or_create_conversation(self.db, user_id_1=1, user_id_2=2)
        self.assertFalse(created2)
        self.assertEqual(conv1.id, conv2.id)

        # Reversed order should still return the exact same conversation
        conv3, created3 = get_or_create_conversation(self.db, user_id_1=2, user_id_2=1)
        self.assertFalse(created3)
        self.assertEqual(conv1.id, conv3.id)

    def test_send_message_read_receipts_and_unread_counts(self):
        """Test message persistence, unread counters, and mark-as-read mechanics."""
        conv, _ = get_or_create_conversation(self.db, user_id_1=1, user_id_2=2)

        # User 1 sends message to User 2
        msg1 = send_message(self.db, conversation_id=conv.id, sender_id=1, message_text="Chào bạn, tác phẩm rất hay!")
        self.assertIsNotNone(msg1.id)
        self.assertEqual(msg1.message_text, "Chào bạn, tác phẩm rất hay!")
        self.assertFalse(msg1.is_read)

        # User 2 unread count should be 1
        unread_u2 = get_total_unread_count(self.db, user_id=2)
        self.assertEqual(unread_u2, 1)

        # User 1 unread count should remain 0
        unread_u1 = get_total_unread_count(self.db, user_id=1)
        self.assertEqual(unread_u1, 0)

        # User 2 reads messages
        history = get_conversation_messages(self.db, conversation_id=conv.id, current_user_id=2)
        self.assertEqual(len(history["messages"]), 1)
        self.assertTrue(history["messages"][0]["is_read"])

        # After reading, User 2 unread count should be reset to 0
        unread_u2_after = get_total_unread_count(self.db, user_id=2)
        self.assertEqual(unread_u2_after, 0)

    # ==================== 6. ROUTER EXPOSURE ====================

    def test_routers_exported(self):
        """Test that social_router and messenger_router have all required route paths."""
        social_paths = {route.path for route in social_router.routes}
        self.assertIn("/feed", social_paths)
        self.assertIn("/publish", social_paths)
        self.assertIn("/interact", social_paths)
        self.assertIn("/post/{post_id}", social_paths)

        messenger_paths = {route.path for route in messenger_router.routes}
        self.assertIn("/users", messenger_paths)
        self.assertIn("/conversations", messenger_paths)
        self.assertIn("/conversations/{id}/messages", messenger_paths)
        self.assertIn("/unread-count", messenger_paths)


if __name__ == "__main__":
    unittest.main()
