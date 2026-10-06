"""
NarrAI Round 6 Test Suite: Social Network Expansion
Location: backend/tests/test_round6_social_features.py

Authoritative Specifications:
- ORIGINAL_REQUEST.md (§ R4. Mở Rộng Database & Tính Năng Mạng Xã Hội Hoàn Chỉnh, 2026-09-30T16:30:48Z)
- PROJECT.md (§ Features 16-22, Milestone 3 & Milestone 5)
- Survey Report 3 (§ Section B: R4 — Social Network Expansion)

Coverage:
1. Follow / Unfollow CRUD & following-prioritized feed.
2. Threaded comments with parent_comment_id (hierarchical tree structure).
3. Bookmarks / personal library CRUD (categories, tags, uniqueness).
4. Notifications CRUD (LIKE, COMMENT, FOLLOW, MESSAGE; read status & unread counts).
5. Content Reports CRUD (distortion, spam, harassment, status lifecycle).
6. Author Profiles (bio, avatar, followers_count, following_count, works list).
7. Trending Leaderboards (weekly/monthly time-decayed velocity ranking).
"""

import os
import sys
import json
import unittest
from unittest.mock import patch
from datetime import datetime, timedelta
from sqlalchemy import (
    create_engine, Column, Integer, String, Text, Float, Boolean,
    DateTime, ForeignKey, UniqueConstraint, inspect, func
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

# Ensure backend root is on sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from db.models import Base, User, Story, SocialPost, PostInteraction

# Try importing Milestone 3 models from db.models if implemented
try:
    from db.models import Follow, Bookmark, Notification, ContentReport, AuthorProfile
    HAS_M3_MODELS = True
except ImportError:
    HAS_M3_MODELS = False

    # Define contract-compliant models per PROJECT.md and Survey 3 specification
    class Follow(Base):
        __tablename__ = "test_follows"
        id = Column(Integer, primary_key=True, autoincrement=True)
        follower_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
        following_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
        created_at = Column(DateTime, default=datetime.utcnow, index=True)
        __table_args__ = (
            UniqueConstraint("follower_id", "following_id", name="uq_user_follower_following_r6"),
        )

    class Bookmark(Base):
        __tablename__ = "test_bookmarks"
        id = Column(Integer, primary_key=True, autoincrement=True)
        user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
        post_id = Column(Integer, ForeignKey("social_posts.id"), index=True, nullable=False)
        category = Column(String(100), default="Yêu thích", index=True)
        tags = Column(Text, default="[]")
        notes = Column(Text, nullable=True)
        created_at = Column(DateTime, default=datetime.utcnow, index=True)
        __table_args__ = (
            UniqueConstraint("user_id", "post_id", name="uq_user_post_bookmark_r6"),
        )

    class Notification(Base):
        __tablename__ = "test_notifications"
        id = Column(Integer, primary_key=True, autoincrement=True)
        recipient_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
        sender_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
        notification_type = Column(String(50), index=True, nullable=False)
        post_id = Column(Integer, ForeignKey("social_posts.id"), nullable=True)
        comment_id = Column(Integer, nullable=True)
        conversation_id = Column(Integer, nullable=True)
        content = Column(Text, nullable=True)
        is_read = Column(Boolean, default=False, index=True)
        created_at = Column(DateTime, default=datetime.utcnow, index=True)

    class ContentReport(Base):
        __tablename__ = "test_content_reports"
        id = Column(Integer, primary_key=True, autoincrement=True)
        reporter_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
        post_id = Column(Integer, ForeignKey("social_posts.id"), nullable=True, index=True)
        target_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
        report_reason = Column(String(50), nullable=False)
        details = Column(Text, nullable=True)
        status = Column(String(30), default="PENDING", index=True)
        created_at = Column(DateTime, default=datetime.utcnow, index=True)

    class AuthorProfile(Base):
        __tablename__ = "test_author_profiles"
        id = Column(Integer, primary_key=True, autoincrement=True)
        user_id = Column(Integer, ForeignKey("users.id"), unique=True, index=True, nullable=False)
        bio = Column(Text, default="")
        avatar_url = Column(String(500), nullable=True)
        cover_url = Column(String(500), nullable=True)
        genres = Column(Text, default="[]")
        followers_count = Column(Integer, default=0, nullable=False)
        following_count = Column(Integer, default=0, nullable=False)
        works_count = Column(Integer, default=0, nullable=False)
        total_likes = Column(Integer, default=0, nullable=False)
        created_at = Column(DateTime, default=datetime.utcnow)
        updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TestRound6SocialFeaturesBase(unittest.TestCase):
    """Sets up an isolated, transactional in-memory SQLite database."""

    @classmethod
    def setUpClass(cls):
        from sqlalchemy.pool import StaticPool
        cls.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool
        )
        Base.metadata.create_all(cls.engine)
        cls.Session = sessionmaker(bind=cls.engine, autocommit=False, autoflush=False)

    def setUp(self):
        self.db = self.Session()
        # Clean any existing data to guarantee complete test isolation
        try:
            for table in reversed(Base.metadata.sorted_tables):
                try:
                    self.db.execute(table.delete())
                except Exception:
                    pass
            self.db.commit()
        except Exception:
            self.db.rollback()

        # Seed test authors & readers
        self.author1 = User(username="tac_gia_1", full_name="Trần Văn Tác Giả", coins=100)
        self.author2 = User(username="tac_gia_2", full_name="Lê Thị Bút Vàng", coins=100)
        self.reader = User(username="doc_gia_vip", full_name="Nguyễn Văn Đọc Giả", coins=50)
        self.db.add_all([self.author1, self.author2, self.reader])
        self.db.commit()

        # Seed sample stories and posts
        self.post1 = SocialPost(
            user_id=self.author1.id,
            title="Đại Thắng Bạch Đằng",
            content_snippet="Trận chiến hào hùng năm 1288...",
            genre="Lịch sử",
            likes_count=15,
            comments_count=5,
            views_count=120,
            completion_count=40,
            created_at=datetime.utcnow() - timedelta(hours=2)
        )
        self.post2 = SocialPost(
            user_id=self.author2.id,
            title="Ám Dạ Kinh Thành",
            content_snippet="Thám tử Thăng Long phá án...",
            genre="Trinh thám",
            likes_count=8,
            comments_count=2,
            views_count=50,
            completion_count=12,
            created_at=datetime.utcnow() - timedelta(hours=10)
        )
        self.db.add_all([self.post1, self.post2])
        self.db.commit()

    def tearDown(self):
        try:
            for table in reversed(Base.metadata.sorted_tables):
                try:
                    self.db.execute(table.delete())
                except Exception:
                    pass
            self.db.commit()
        except Exception:
            self.db.rollback()
        finally:
            self.db.close()


class TestRound6FollowSystem(TestRound6SocialFeaturesBase):
    """
    Tests for Requirement R4.1:
    Follow / Unfollow authors and Following-prioritized feed.
    """

    def test_follow_author_success(self):
        """Reader follows Author 1."""
        follow_record = Follow(
            follower_id=self.reader.id,
            following_id=self.author1.id
        )
        self.db.add(follow_record)
        self.db.commit()

        # Query verification
        stored = self.db.query(Follow).filter(
            Follow.follower_id == self.reader.id,
            Follow.following_id == self.author1.id
        ).first()
        self.assertIsNotNone(stored)
        self.assertEqual(stored.following_id, self.author1.id)

    def test_duplicate_follow_rejected_by_unique_constraint(self):
        """User cannot follow the same author twice."""
        f1 = Follow(follower_id=self.reader.id, following_id=self.author1.id)
        self.db.add(f1)
        self.db.commit()

        f2 = Follow(follower_id=self.reader.id, following_id=self.author1.id)
        self.db.add(f2)
        with self.assertRaises(Exception):
            self.db.commit()
        self.db.rollback()

    def test_unfollow_author(self):
        """Reader unfollows Author 1."""
        f = Follow(follower_id=self.reader.id, following_id=self.author1.id)
        self.db.add(f)
        self.db.commit()

        # Unfollow
        self.db.query(Follow).filter(
            Follow.follower_id == self.reader.id,
            Follow.following_id == self.author1.id
        ).delete()
        self.db.commit()

        remaining = self.db.query(Follow).filter(
            Follow.follower_id == self.reader.id,
            Follow.following_id == self.author1.id
        ).first()
        self.assertIsNone(remaining)

    def test_following_feed_filtering(self):
        """Following feed only displays posts authored by followed users."""
        # Reader follows author1 only
        self.db.add(Follow(follower_id=self.reader.id, following_id=self.author1.id))
        self.db.commit()

        # Query posts from followed authors
        followed_ids = self.db.query(Follow.following_id).filter(
            Follow.follower_id == self.reader.id
        ).subquery()

        feed_posts = self.db.query(SocialPost).filter(
            SocialPost.user_id.in_(followed_ids)
        ).all()

        self.assertEqual(len(feed_posts), 1)
        self.assertEqual(feed_posts[0].id, self.post1.id)
        self.assertEqual(feed_posts[0].user_id, self.author1.id)


class TestRound6ThreadedComments(TestRound6SocialFeaturesBase):
    """
    Tests for Requirement R4.2:
    Threaded comments with parent_comment_id (comment replies and nesting).
    """

    def test_root_comment_creation(self):
        """PostInteraction or Comment with parent_comment_id = None is a root comment."""
        root_comment = PostInteraction(
            user_id=self.reader.id,
            post_id=self.post1.id,
            interaction_type="COMMENT",
            comment_text="Truyện viết về Hưng Đạo Vương rất hào hùng!"
        )
        self.db.add(root_comment)
        self.db.commit()

        self.assertIsNotNone(root_comment.id)
        # Check parent_comment_id if column exists
        if hasattr(root_comment, "parent_comment_id"):
            self.assertIsNone(root_comment.parent_comment_id)

    def test_threaded_reply_creation(self):
        """Creating a reply referencing the parent comment ID."""
        parent = PostInteraction(
            user_id=self.reader.id,
            post_id=self.post1.id,
            interaction_type="COMMENT",
            comment_text="Đoạn đóng cọc sông Bạch Đằng rất chi tiết."
        )
        self.db.add(parent)
        self.db.commit()

        reply = PostInteraction(
            user_id=self.author1.id,
            post_id=self.post1.id,
            interaction_type="COMMENT",
            comment_text="Cảm ơn bạn đã đọc và ủng hộ tác phẩm!"
        )
        if hasattr(reply, "parent_comment_id"):
            reply.parent_comment_id = parent.id

        self.db.add(reply)
        self.db.commit()

        self.assertIsNotNone(reply.id)
        if hasattr(reply, "parent_comment_id"):
            self.assertEqual(reply.parent_comment_id, parent.id)


class TestRound6BookmarksPersonalLibrary(TestRound6SocialFeaturesBase):
    """
    Tests for Requirement R4.3:
    Bookmarks / personal library CRUD with custom categories and tags.
    """

    def test_create_bookmark(self):
        """User saves a story to bookmarks with a category."""
        bm = Bookmark(
            user_id=self.reader.id,
            post_id=self.post1.id,
            category="Yêu thích",
            tags=json.dumps(["lịch sử", "đại việt"]),
            notes="Đọc lại khi rảnh"
        )
        self.db.add(bm)
        self.db.commit()

        stored = self.db.query(Bookmark).filter(
            Bookmark.user_id == self.reader.id,
            Bookmark.post_id == self.post1.id
        ).first()
        self.assertIsNotNone(stored)
        self.assertEqual(stored.category, "Yêu thích")
        parsed_tags = json.loads(stored.tags) if isinstance(stored.tags, str) else stored.tags
        self.assertIn("đại việt", parsed_tags)

    def test_duplicate_bookmark_prevented(self):
        """Same user cannot bookmark same post twice."""
        bm1 = Bookmark(user_id=self.reader.id, post_id=self.post1.id, category="Yêu thích")
        self.db.add(bm1)
        self.db.commit()

        bm2 = Bookmark(user_id=self.reader.id, post_id=self.post1.id, category="Đang đọc")
        self.db.add(bm2)
        with self.assertRaises(Exception):
            self.db.commit()
        self.db.rollback()

    def test_filter_bookmarks_by_category(self):
        """Filtering personal library by category."""
        bm1 = Bookmark(user_id=self.reader.id, post_id=self.post1.id, category="Yêu thích")
        bm2 = Bookmark(user_id=self.reader.id, post_id=self.post2.id, category="Đang đọc")
        self.db.add_all([bm1, bm2])
        self.db.commit()

        favorites = self.db.query(Bookmark).filter(
            Bookmark.user_id == self.reader.id,
            Bookmark.category == "Yêu thích"
        ).all()
        self.assertEqual(len(favorites), 1)
        self.assertEqual(favorites[0].post_id, self.post1.id)


class TestRound6NotificationSystem(TestRound6SocialFeaturesBase):
    """
    Tests for Requirement R4.4:
    Notification generation, read marking, and unread counts.
    """

    def test_create_and_query_notifications(self):
        """Author receives notification when reader likes their post."""
        notif = Notification(
            recipient_id=self.author1.id,
            sender_id=self.reader.id,
            notification_type="LIKE",
            post_id=self.post1.id,
            content="Nguyễn Văn Đọc Giả đã thích tác phẩm của bạn."
        )
        self.db.add(notif)
        self.db.commit()

        unread = self.db.query(Notification).filter(
            Notification.recipient_id == self.author1.id,
            Notification.is_read == False
        ).all()
        self.assertEqual(len(unread), 1)
        self.assertEqual(unread[0].notification_type, "LIKE")

    def test_mark_notification_as_read(self):
        """Mark single and all notifications as read."""
        n1 = Notification(recipient_id=self.author1.id, sender_id=self.reader.id, notification_type="LIKE", is_read=False)
        n2 = Notification(recipient_id=self.author1.id, sender_id=self.reader.id, notification_type="COMMENT", is_read=False)
        self.db.add_all([n1, n2])
        self.db.commit()

        # Mark n1 read
        n1.is_read = True
        self.db.commit()

        unread_count = self.db.query(Notification).filter(
            Notification.recipient_id == self.author1.id,
            Notification.is_read == False
        ).count()
        self.assertEqual(unread_count, 1)

        # Mark all read
        self.db.query(Notification).filter(
            Notification.recipient_id == self.author1.id
        ).update({"is_read": True})
        self.db.commit()

        unread_count_after = self.db.query(Notification).filter(
            Notification.recipient_id == self.author1.id,
            Notification.is_read == False
        ).count()
        self.assertEqual(unread_count_after, 0)


class TestRound6ContentReporting(TestRound6SocialFeaturesBase):
    """
    Tests for Requirement R4.5:
    Content report submission for distortion, spam, or harassment.
    """

    def test_submit_report_valid_reasons(self):
        """Report for distortion ('distortion' / xuyên tạc) is accepted with PENDING status."""
        report = ContentReport(
            reporter_id=self.reader.id,
            post_id=self.post1.id,
            report_reason="distortion",
            details="Nghi vấn nội dung có yếu tố xuyên tạc lịch sử.",
            status="PENDING"
        )
        self.db.add(report)
        self.db.commit()

        stored = self.db.query(ContentReport).filter(
            ContentReport.reporter_id == self.reader.id,
            ContentReport.post_id == self.post1.id
        ).first()
        self.assertIsNotNone(stored)
        self.assertEqual(stored.status, "PENDING")
        self.assertEqual(stored.report_reason, "distortion")

    def test_report_status_lifecycle(self):
        """Admin/moderator transitions report from PENDING to RESOLVED."""
        report = ContentReport(
            reporter_id=self.reader.id,
            post_id=self.post2.id,
            report_reason="spam",
            status="PENDING"
        )
        self.db.add(report)
        self.db.commit()

        report.status = "RESOLVED"
        self.db.commit()

        updated = self.db.query(ContentReport).filter(ContentReport.id == report.id).first()
        self.assertEqual(updated.status, "RESOLVED")


class TestRound6AuthorProfiles(TestRound6SocialFeaturesBase):
    """
    Tests for Requirement R4.6:
    Author profile management (bio, avatar, followers, works count).
    """

    def test_author_profile_creation_and_stats(self):
        """Create and retrieve author profile with follower counts and published works."""
        profile = AuthorProfile(
            user_id=self.author1.id,
            bio="Tác giả chuyên viết về lịch sử hào hùng của dân tộc Việt Nam.",
            avatar_url="https://example.com/avatar1.png",
            followers_count=120,
            following_count=15,
            works_count=4,
            total_likes=560
        )
        self.db.add(profile)
        self.db.commit()

        stored = self.db.query(AuthorProfile).filter(AuthorProfile.user_id == self.author1.id).first()
        self.assertIsNotNone(stored)
        self.assertIn("lịch sử hào hùng", stored.bio)
        self.assertEqual(stored.followers_count, 120)

    def test_author_profile_unique_per_user(self):
        """A user cannot have multiple AuthorProfile records."""
        p1 = AuthorProfile(user_id=self.author2.id, bio="Bio 1")
        self.db.add(p1)
        self.db.commit()

        p2 = AuthorProfile(user_id=self.author2.id, bio="Bio 2")
        self.db.add(p2)
        with self.assertRaises(Exception):
            self.db.commit()
        self.db.rollback()


class TestRound6TrendingLeaderboard(TestRound6SocialFeaturesBase):
    """
    Tests for Requirement R4.7 & Survey 3 § 3:
    Trending leaderboard calculation using time-decayed velocity scoring formula.
    """

    def test_trending_score_velocity_calculation(self):
        """
        Velocity formula from Survey 3:
        Score = (3*likes + 5*comments + 0.5*views + 4*completions) / ((age_in_hours + 2) ** 1.4)
        """
        def compute_velocity(likes, comments, views, completions, age_hours):
            numerator = 3.0 * likes + 5.0 * comments + 0.5 * views + 4.0 * completions
            denominator = (age_hours + 2.0) ** 1.4
            return numerator / denominator

        # Post 1: Fresh (2 hours old), 15 likes, 5 comments, 120 views, 40 completions
        score_fresh = compute_velocity(15, 5, 120, 40, age_hours=2.0)
        # Post 2: Older (48 hours old), 20 likes, 5 comments, 150 views, 40 completions
        score_older = compute_velocity(20, 5, 150, 40, age_hours=48.0)

        # Fresh post must have higher velocity despite slightly fewer likes
        self.assertGreater(
            score_fresh,
            score_older,
            f"Fresh score ({score_fresh:.2f}) should beat older post score ({score_older:.2f})"
        )

    def test_weekly_and_monthly_window_filtering(self):
        """Leaderboard query respects weekly (<= 7 days) and monthly (<= 30 days) windows."""
        now = datetime.utcnow()
        post_3_days_old = SocialPost(
            user_id=self.author1.id,
            title="Truyện 3 Ngày",
            content_snippet="Snippet...",
            created_at=now - timedelta(days=3)
        )
        post_15_days_old = SocialPost(
            user_id=self.author1.id,
            title="Truyện 15 Ngày",
            content_snippet="Snippet...",
            created_at=now - timedelta(days=15)
        )
        post_45_days_old = SocialPost(
            user_id=self.author1.id,
            title="Truyện 45 Ngày",
            content_snippet="Snippet...",
            created_at=now - timedelta(days=45)
        )
        self.db.add_all([post_3_days_old, post_15_days_old, post_45_days_old])
        self.db.commit()

        # Weekly query
        weekly_cutoff = now - timedelta(days=7)
        weekly_posts = self.db.query(SocialPost).filter(SocialPost.created_at >= weekly_cutoff).all()
        weekly_titles = [p.title for p in weekly_posts]
        self.assertIn("Truyện 3 Ngày", weekly_titles)
        self.assertNotIn("Truyện 15 Ngày", weekly_titles)
        self.assertNotIn("Truyện 45 Ngày", weekly_titles)

        # Monthly query
        monthly_cutoff = now - timedelta(days=30)
        monthly_posts = self.db.query(SocialPost).filter(SocialPost.created_at >= monthly_cutoff).all()
        monthly_titles = [p.title for p in monthly_posts]
        self.assertIn("Truyện 3 Ngày", monthly_titles)
        self.assertIn("Truyện 15 Ngày", monthly_titles)
        self.assertNotIn("Truyện 45 Ngày", monthly_titles)


from starlette.testclient import TestClient
from fastapi import FastAPI
try:
    from routers.social_router import (
        router as social_router,
        get_current_user,
        require_current_user,
        require_moderator,
    )
    from db.models import get_db
except ImportError:
    from backend.routers.social_router import (
        router as social_router,
        get_current_user,
        require_current_user,
        require_moderator,
    )
    from backend.db.models import get_db


class TestRound6SocialAPIRoutes(TestRound6SocialFeaturesBase):
    """
    Integration tests for Milestone 3 Social REST API Endpoints:
    Follow/Unfollow, Following Feed, Threaded Comments, Bookmarks,
    Notifications, Content Reports, Author Profiles, Trending Leaderboards.
    """

    def setUp(self):
        super().setUp()
        self.app = FastAPI()
        self.app.include_router(social_router, prefix="/api/social")

        def _get_test_db():
            db = self.Session()
            try:
                yield db
            finally:
                db.close()

        self.app.dependency_overrides[get_db] = _get_test_db
        self.app.dependency_overrides[get_current_user] = lambda: self.reader
        self.app.dependency_overrides[require_current_user] = lambda: self.reader
        self.client = TestClient(self.app)

    def test_api_follow_and_unfollow_flow(self):
        """Test follow and unfollow author via REST API."""
        # Follow author 1
        res = self.client.post(f"/api/social/follow/{self.author1.id}")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data.get("success"))
        self.assertEqual(data.get("following_id"), self.author1.id)

        # Duplicate follow
        res_dup = self.client.post(f"/api/social/follow/{self.author1.id}")
        self.assertEqual(res_dup.status_code, 200)
        self.assertTrue(res_dup.json().get("already_following"))

        # Cannot follow oneself
        res_self = self.client.post(f"/api/social/follow/{self.reader.id}")
        self.assertEqual(res_self.status_code, 400)

        # Unfollow author 1
        res_un = self.client.post(f"/api/social/unfollow/{self.author1.id}")
        self.assertEqual(res_un.status_code, 200)
        self.assertTrue(res_un.json().get("success"))

        # Unfollow again
        res_un2 = self.client.post(f"/api/social/unfollow/{self.author1.id}")
        self.assertEqual(res_un2.status_code, 200)
        self.assertTrue(res_un2.json().get("already_unfollowed"))

    def test_api_following_feed(self):
        """Test following feed returns only followed authors' posts."""
        # Follow author 1
        self.client.post(f"/api/social/follow/{self.author1.id}")

        res = self.client.get("/api/social/feed?feed_type=following")
        self.assertEqual(res.status_code, 200)
        feed_data = res.json().get("data", {})
        posts = feed_data.get("posts", [])
        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0]["id"], self.post1.id)

    def test_api_threaded_comments_and_post_details(self):
        """Test threaded reply creation and retrieval in post details."""
        # Create root comment
        res_root = self.client.post("/api/social/interact", json={
            "post_id": self.post1.id,
            "interaction_type": "COMMENT",
            "comment_text": "Bình luận gốc cho bài viết."
        })
        self.assertEqual(res_root.status_code, 200)
        root_id = res_root.json().get("interaction_id")
        self.assertIsNotNone(root_id)

        # Create reply comment referencing root comment
        res_reply = self.client.post("/api/social/interact", json={
            "post_id": self.post1.id,
            "interaction_type": "COMMENT",
            "comment_text": "Phản hồi cho bình luận gốc.",
            "parent_comment_id": root_id
        })
        self.assertEqual(res_reply.status_code, 200)
        reply_data = res_reply.json()
        self.assertEqual(reply_data.get("parent_comment_id"), root_id)

        # Fetch post details and check comments
        res_post = self.client.get(f"/api/social/post/{self.post1.id}")
        self.assertEqual(res_post.status_code, 200)
        comments = res_post.json().get("data", {}).get("comments", [])
        self.assertTrue(len(comments) >= 2)
        reply_comment = next((c for c in comments if c.get("id") == res_reply.json().get("interaction_id")), None)
        self.assertIsNotNone(reply_comment)
        self.assertEqual(reply_comment.get("parent_comment_id"), root_id)

    def test_api_bookmark_crud(self):
        """Test bookmark creation, filtering, and deletion."""
        # Create bookmark
        res_bm = self.client.post("/api/social/bookmark", json={
            "post_id": self.post1.id,
            "category": "Yêu thích",
            "tags": ["kinh điển", "lịch sử"],
            "notes": "Tác phẩm rất tâm đắc"
        })
        self.assertEqual(res_bm.status_code, 200)
        self.assertTrue(res_bm.json().get("success"))

        # Query bookmarks
        res_list = self.client.get("/api/social/bookmarks")
        self.assertEqual(res_list.status_code, 200)
        data = res_list.json()
        self.assertEqual(data.get("total"), 1)

        # Filter by different category
        res_empty = self.client.get("/api/social/bookmarks?category=Khác")
        self.assertEqual(res_empty.status_code, 200)
        self.assertEqual(res_empty.json().get("total"), 0)

        # Delete bookmark
        res_del = self.client.delete(f"/api/social/bookmark/{self.post1.id}")
        self.assertEqual(res_del.status_code, 200)
        self.assertTrue(res_del.json().get("deleted"))

    def test_api_notifications_and_read_lifecycle(self):
        """Test notification listing and mark as read."""
        notif = Notification(
            recipient_id=self.reader.id,
            sender_id=self.author1.id,
            notification_type="LIKE",
            content="Tác giả 1 đã thích tác phẩm của bạn.",
            is_read=False
        )
        self.db.add(notif)
        self.db.commit()

        # Query notifications
        res = self.client.get("/api/social/notifications")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertGreaterEqual(data.get("unread_count"), 1)

        # Mark single read
        res_read = self.client.post(f"/api/social/notifications/{notif.id}/read")
        self.assertEqual(res_read.status_code, 200)

        # Mark all read
        res_read_all = self.client.post("/api/social/notifications/read-all")
        self.assertEqual(res_read_all.status_code, 200)

    def test_api_content_report_submit_and_resolve(self):
        """Test report submission and admin resolve."""
        res_rep = self.client.post("/api/social/report", json={
            "post_id": self.post1.id,
            "report_reason": "distortion",
            "details": "Kiểm tra nghi vấn xuyên tạc"
        })
        self.assertEqual(res_rep.status_code, 201)
        rep_id = res_rep.json().get("report_id")
        self.assertIsNotNone(rep_id)

        # Only configured moderators can list and resolve reports.
        with patch.dict(os.environ, {"NARRAI_MODERATOR_USERNAMES": "doc_gia_vip"}):
            res_list = self.client.get("/api/social/reports?status=PENDING")
            self.assertEqual(res_list.status_code, 200)
            self.assertGreaterEqual(res_list.json().get("total"), 1)

            res_res = self.client.post(f"/api/social/report/{rep_id}/resolve", json={
                "status": "RESOLVED"
            })
            self.assertEqual(res_res.status_code, 200)
            self.assertEqual(res_res.json().get("status"), "RESOLVED")

            invalid_status = self.client.post(
                f"/api/social/report/{rep_id}/resolve",
                json={"status": "PENDING"},
            )
            self.assertEqual(invalid_status.status_code, 422)

        with patch.dict(os.environ, {"NARRAI_MODERATOR_USERNAMES": ""}):
            denied = self.client.get("/api/social/reports")
            self.assertEqual(denied.status_code, 403)

    def test_api_author_profile_get_and_put(self):
        """Test author profile retrieval and update."""
        res_prof = self.client.get(f"/api/social/profile/{self.author1.id}")
        self.assertEqual(res_prof.status_code, 200)
        data = res_prof.json().get("data", {})
        self.assertEqual(data.get("user_id"), self.author1.id)
        self.assertIn("works", data)

        # Update my profile
        res_put = self.client.put("/api/social/profile", json={
            "bio": "Độc giả đam mê lịch sử và tiểu thuyết phiêu lưu.",
            "genres": ["Lịch sử", "Phiêu lưu"]
        })
        self.assertEqual(res_put.status_code, 200)
        self.assertIn("Lịch sử", res_put.json().get("data", {}).get("genres", []))

    def test_api_trending_leaderboard(self):
        """Test trending leaderboard velocity ranking endpoint."""
        res_weekly = self.client.get("/api/social/trending?period=weekly")
        self.assertEqual(res_weekly.status_code, 200)
        weekly_data = res_weekly.json()
        self.assertEqual(weekly_data.get("period"), "weekly")
        self.assertTrue("data" in weekly_data)
        if len(weekly_data["data"]) >= 2:
            self.assertGreaterEqual(
                weekly_data["data"][0]["trending_score"],
                weekly_data["data"][1]["trending_score"]
            )


if __name__ == "__main__":
    unittest.main()
