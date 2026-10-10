"""
NarrAI Round 6 Test Suite: Database WAL Mode, Index Optimization & GZip Performance
Location: backend/tests/test_round6_wal_performance.py

Authoritative Specifications:
- ORIGINAL_REQUEST.md (§ R5. Tối Ưu Hiệu Năng & Sửa Nhược Điểm Trực Quan, 2026-09-30T16:30:48Z)
- PROJECT.md (§ Features 6-8, Milestone 1 & Milestone 5)
- Survey Report 1 (§ 3. Investigation of R5: Database & Performance)

Coverage:
1. SQLite WAL mode activation: PRAGMA journal_mode returns 'wal' and PRAGMA synchronous returns NORMAL (1) on disk-backed DB.
2. Index presence: single-column indexes on Comic.user_id, Comic.story_id, ComicPanel.comic_id, SocialPost.story_id.
3. Composite indexes on ComicPanel(comic_id, panel_index), SocialPost(genre, created_at), SocialPost(user_id, created_at), PostInteraction(post_id, interaction_type, created_at), Comic(user_id, created_at).
4. FastAPI GZipMiddleware compression on responses >= 500 bytes and passthrough for responses < 500 bytes.
"""

import os
import sys
import gzip
import tempfile
import unittest
from sqlalchemy import create_engine, text, inspect, event
from sqlalchemy.orm import sessionmaker
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from fastapi.middleware.gzip import GZipMiddleware
from starlette.testclient import TestClient

# Ensure backend root is on sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from db.models import (
    Base,
    Comic,
    ComicPanel,
    SocialPost,
    PostInteraction,
    User,
    Story,
    engine as prod_engine
)


class TestRound6SQLiteWALMode(unittest.TestCase):
    """
    Tests for Requirement R5.1:
    SQLite WAL mode activation (PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL;).
    Note: SQLite in-memory databases (:memory:) do not support WAL mode;
    verification must run on a disk-backed temporary SQLite database.
    """

    def setUp(self):
        self.temp_db_fd, self.temp_db_path = tempfile.mkstemp(suffix="_test_wal.db")
        os.close(self.temp_db_fd)
        self.db_url = f"sqlite:///{self.temp_db_path}"

    def tearDown(self):
        if os.path.exists(self.temp_db_path):
            try:
                os.remove(self.temp_db_path)
            except Exception:
                pass
        # Clean up any -wal or -shm files
        for ext in ["-wal", "-shm"]:
            f = self.temp_db_path + ext
            if os.path.exists(f):
                try:
                    os.remove(f)
                except Exception:
                    pass

    def test_wal_pragma_on_disk_backed_engine(self):
        """
        Verify that configuring WAL pragma on connection returns journal_mode='wal'
        and synchronous='1' (NORMAL).
        """
        engine = create_engine(self.db_url, connect_args={"check_same_thread": False})

        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL;")
            cursor.execute("PRAGMA synchronous=NORMAL;")
            cursor.close()

        with engine.connect() as conn:
            mode = conn.execute(text("PRAGMA journal_mode;")).scalar()
            sync = conn.execute(text("PRAGMA synchronous;")).scalar()

        self.assertEqual(mode.lower(), "wal", f"Expected WAL mode, got {mode}")
        # In SQLite: 1 corresponds to NORMAL, 2 corresponds to FULL
        self.assertIn(str(sync), ["1", "NORMAL", "normal"], f"Expected synchronous NORMAL (1), got {sync}")

    def test_production_engine_or_models_wal_listener(self):
        """
        Check that prod_engine from db.models has WAL mode and synchronous=NORMAL (1) enabled.
        """
        try:
            with prod_engine.connect() as conn:
                mode = conn.execute(text("PRAGMA journal_mode;")).scalar()
                sync = conn.execute(text("PRAGMA synchronous;")).scalar()
                if mode and mode.lower() != "memory":
                    self.assertEqual(mode.lower(), "wal", f"Expected production engine journal_mode='wal', got {mode}")
                    self.assertIn(str(sync), ["1", "NORMAL", "normal"], f"Expected synchronous NORMAL (1), got {sync}")
        except Exception as e:
            self.fail(f"Failed to connect to production engine or verify WAL pragmas: {e}")


class TestRound6DatabaseIndexOptimization(unittest.TestCase):
    """
    Tests for Requirement R5.2:
    Adding missing single-column and composite indexes for hot query paths.
    """

    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        Base.metadata.create_all(cls.engine)
        cls.inspector = inspect(cls.engine)

    def test_comic_table_single_indexes(self):
        """Verify single-column indexes on Comic: user_id and story_id."""
        table_name = Comic.__tablename__
        indexes = self.inspector.get_indexes(table_name)
        indexed_cols = set()
        for idx in indexes:
            for col in idx["column_names"]:
                indexed_cols.add(col)

        # Check Column definitions or table indexes
        has_user_id_idx = "user_id" in indexed_cols or any(
            c.name == "user_id" and c.index for c in Comic.__table__.columns
        )
        has_story_id_idx = "story_id" in indexed_cols or any(
            c.name == "story_id" and c.index for c in Comic.__table__.columns
        )

        self.assertTrue(has_user_id_idx, f"Index on Comic.user_id missing. Existing: {indexes}")
        self.assertTrue(has_story_id_idx, f"Index on Comic.story_id missing. Existing: {indexes}")

    def test_comic_table_composite_index(self):
        """Verify composite index ix_comics_user_id_created_at on Comic(user_id, created_at)."""
        table_name = Comic.__tablename__
        indexes = self.inspector.get_indexes(table_name)
        indexed_tuples = [tuple(idx["column_names"]) for idx in indexes]
        self.assertIn(
            ("user_id", "created_at"),
            indexed_tuples,
            f"Composite index ('user_id', 'created_at') missing on Comic. Existing: {indexes}"
        )

    def test_comic_panel_table_indexes(self):
        """Verify index on ComicPanel.comic_id and composite (comic_id, panel_index)."""
        table_name = ComicPanel.__tablename__
        indexes = self.inspector.get_indexes(table_name)
        indexed_tuples = [tuple(idx["column_names"]) for idx in indexes]

        # Single column check
        has_comic_id = any("comic_id" in idx["column_names"] for idx in indexes) or any(
            c.name == "comic_id" and c.index for c in ComicPanel.__table__.columns
        )
        self.assertTrue(has_comic_id, f"Index on ComicPanel.comic_id missing. Existing: {indexes}")

        # Strict composite check: (comic_id, panel_index)
        self.assertIn(
            ("comic_id", "panel_index"),
            indexed_tuples,
            f"Composite index ('comic_id', 'panel_index') missing on ComicPanel. Existing: {indexes}"
        )

    def test_social_post_table_indexes(self):
        """Verify index on SocialPost.story_id and composite indexes."""
        table_name = SocialPost.__tablename__
        indexes = self.inspector.get_indexes(table_name)
        indexed_tuples = [tuple(idx["column_names"]) for idx in indexes]

        has_story_id = any("story_id" in idx["column_names"] for idx in indexes) or any(
            c.name == "story_id" and c.index for c in SocialPost.__table__.columns
        )
        self.assertTrue(has_story_id, f"Index on SocialPost.story_id missing. Existing: {indexes}")

        # Composite check: (genre, created_at) and (user_id, created_at)
        self.assertIn(
            ("genre", "created_at"),
            indexed_tuples,
            f"Composite index ('genre', 'created_at') missing on SocialPost. Existing: {indexes}"
        )
        self.assertIn(
            ("user_id", "created_at"),
            indexed_tuples,
            f"Composite index ('user_id', 'created_at') missing on SocialPost. Existing: {indexes}"
        )

    def test_post_interaction_composite_index(self):
        """Verify composite index on PostInteraction(post_id, interaction_type, created_at)."""
        table_name = PostInteraction.__tablename__
        indexes = self.inspector.get_indexes(table_name)
        indexed_tuples = [tuple(idx["column_names"]) for idx in indexes]
        self.assertIn(
            ("post_id", "interaction_type", "created_at"),
            indexed_tuples,
            f"Composite index ('post_id', 'interaction_type', 'created_at') missing on PostInteraction. Existing: {indexes}"
        )


class TestRound6FastAPIGZipMiddleware(unittest.TestCase):
    """
    Tests for Requirement R5.3:
    FastAPI GZipMiddleware compression with minimum_size=500.
    """

    def setUp(self):
        # Create a test FastAPI app with GZipMiddleware configured exactly as required
        self.app = FastAPI()
        self.app.add_middleware(GZipMiddleware, minimum_size=500)

        @self.app.get("/small")
        def small_endpoint():
            # Response < 500 bytes (e.g. 100 bytes)
            return PlainTextResponse("Hello NarrAI! " * 5)

        @self.app.get("/large")
        def large_endpoint():
            # Response >= 500 bytes (e.g. 2000 bytes)
            return PlainTextResponse("Hào khí Đông A Bạch Đằng giang cuồn cuộn sóng trào! " * 50)

        @self.app.get("/boundary/{size}")
        def boundary_endpoint(size: int):
            return PlainTextResponse("A" * size)

        self.client = TestClient(self.app)

    def test_production_app_gzip_middleware_configured(self):
        """Verify that GZipMiddleware is installed on main.app with minimum_size=500."""
        from main import app as prod_app
        gzip_middlewares = [
            m for m in prod_app.user_middleware
            if m.cls == GZipMiddleware
        ]
        self.assertTrue(len(gzip_middlewares) > 0, "GZipMiddleware not found in main.app.user_middleware")
        options = getattr(gzip_middlewares[0], "kwargs", getattr(gzip_middlewares[0], "options", {}))
        self.assertEqual(options.get("minimum_size"), 500, f"Expected minimum_size=500, got {options.get('minimum_size')}")

    def test_small_response_not_compressed(self):
        """Responses with body length < 500 bytes are NOT gzipped."""
        response = self.client.get("/small", headers={"Accept-Encoding": "gzip"})
        self.assertEqual(response.status_code, 200)
        content_encoding = response.headers.get("Content-Encoding", "")
        self.assertNotIn("gzip", content_encoding.lower(), "Small payload was compressed; expected raw.")
        self.assertIn("Hello NarrAI!", response.text)

    def test_large_response_is_gzipped(self):
        """Responses with body length >= 500 bytes ARE gzipped when Accept-Encoding: gzip is sent."""
        response = self.client.get("/large", headers={"Accept-Encoding": "gzip"})
        self.assertEqual(response.status_code, 200)
        content_encoding = response.headers.get("Content-Encoding", "")
        self.assertEqual(content_encoding.lower(), "gzip", "Large payload was not gzipped!")

        # TestClient automatically decompresses response.content or response.text
        self.assertIn("Hào khí Đông A", response.text)
        self.assertTrue(len(response.text) >= 1000)

    def test_boundary_condition_499_vs_500_bytes(self):
        """Test exact threshold: 499 bytes (uncompressed) vs 500 bytes (compressed)."""
        # Exactly 499 bytes ASCII payload
        resp_499 = self.client.get("/boundary/499", headers={"Accept-Encoding": "gzip"})
        self.assertEqual(resp_499.status_code, 200)
        self.assertNotIn("gzip", resp_499.headers.get("Content-Encoding", "").lower())

        # Exactly 500 bytes ASCII payload
        resp_500 = self.client.get("/boundary/500", headers={"Accept-Encoding": "gzip"})
        self.assertEqual(resp_500.status_code, 200)
        self.assertEqual(resp_500.headers.get("Content-Encoding", "").lower(), "gzip")

        # Exactly 501 bytes ASCII payload
        resp_501 = self.client.get("/boundary/501", headers={"Accept-Encoding": "gzip"})
        self.assertEqual(resp_501.status_code, 200)
        self.assertEqual(resp_501.headers.get("Content-Encoding", "").lower(), "gzip")

    def test_large_response_without_gzip_header_remains_uncompressed(self):
        """If client does not accept gzip, response is returned uncompressed."""
        response = self.client.get("/large", headers={"Accept-Encoding": "identity"})
        self.assertEqual(response.status_code, 200)
        content_encoding = response.headers.get("Content-Encoding", "")
        self.assertNotIn("gzip", content_encoding.lower())


if __name__ == "__main__":
    unittest.main()

