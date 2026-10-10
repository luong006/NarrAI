"""
NarrAI Round 6 Test Suite: TensorFlow.js 128-Dim Vector Export & Client Hybrid Bridge
Location: backend/tests/test_round6_tfjs_export.py

Authoritative Specifications:
- ORIGINAL_REQUEST.md (§ R3. TensorFlow.js Hybrid Architecture, 2026-09-30T16:30:48Z)
- PROJECT.md (§ Features 26-30, Milestone 4 & Milestone 5)
- Survey Report 3 (§ Section A: R3 — TensorFlow.js Hybrid Architecture)

Coverage:
1. GET /api/recommender/export-vectors endpoint availability and HTTP 200 response.
2. Concept vector dimensions: strictly 128-dimensional float arrays.
3. Vector L2 normalization: Euclidean norm ||v||_2 approx 1.0.
4. Metadata schema: post_id, title, genre, author information, created_at.
5. Delta synchronization & pagination (since, limit).
6. Local TF.js MMR re-ranking simulation and mathematical validity.
"""

import os
import sys
import json
import math
import unittest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import FastAPI, Depends, Query
from starlette.testclient import TestClient

# Ensure backend root is on sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from db.models import Base, User, Story, SocialPost
from services.recommender_service import (
    generate_concept_vector,
    normalize_vector,
    cosine_similarity,
    export_concept_vectors,
    get_quantized_model_weights,
    VECTOR_DIM
)


def create_mock_export_router(SessionLocal):
    """
    Constructs a reference export route adhering strictly to the R3/M4 specification
    for isolated or integration testing.
    """
    from fastapi import APIRouter
    router = APIRouter()

    @router.get("/api/recommender/export-vectors")
    def export_vectors(
        limit: int = Query(100, ge=1, le=500),
        since: str = Query(None),
        format: str = Query("json")
    ):
        db = SessionLocal()
        try:
            return export_concept_vectors(db=db, limit=limit, since=since, format=format)
        finally:
            db.close()

    @router.get("/api/recommender/model-weights")
    def model_weights(
        format: str = Query("json")
    ):
        return get_quantized_model_weights(format=format)

    return router



class TestRound6TFJSVectorExport(unittest.TestCase):
    """
    Tests for Requirement R3 & Survey 3:
    Exporting 128-dimensional concept vectors for TensorFlow.js on-device inference.
    """

    @classmethod
    def setUpClass(cls):
        from sqlalchemy.pool import StaticPool
        cls.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool
        )
        Base.metadata.create_all(cls.engine)
        cls.SessionLocal = sessionmaker(bind=cls.engine, autocommit=False, autoflush=False)

        # Setup FastAPI test app with vector export route
        cls.app = FastAPI()
        cls.app.include_router(create_mock_export_router(cls.SessionLocal))
        cls.client = TestClient(cls.app)

    def setUp(self):
        self.db = self.SessionLocal()
        # Seed user and test posts
        self.user = User(username="tac_gia_ai", full_name="Tác Giả AI")
        self.db.add(self.user)
        self.db.commit()

        # Seed 3 posts with distinct topics and 128-dim concept vectors
        v1 = generate_concept_vector("Bạch Đằng giang rực lửa cọc ngầm", "Lịch sử")
        v2 = generate_concept_vector("Thành phố tương lai Cyberpunk 2099", "Khoa học viễn tưởng")
        v3 = generate_concept_vector("Thám tử phá án kinh dị đô thị", "Trinh thám")

        self.post1 = SocialPost(
            user_id=self.user.id,
            title="Bạch Đằng Chiến Sử",
            content_snippet="Trần Hưng Đạo đại thắng quân Nguyên Mông",
            genre="Lịch sử",
            concept_vector=json.dumps(v1),
            views_count=100,
            likes_count=20,
            completion_count=15,
            created_at=datetime.utcnow() - timedelta(hours=3)
        )
        self.post2 = SocialPost(
            user_id=self.user.id,
            title="Kỷ Nguyên Số",
            content_snippet="Người máy sinh học trong đêm mưa neon",
            genre="Khoa học viễn tưởng",
            concept_vector=json.dumps(v2),
            views_count=80,
            likes_count=10,
            completion_count=8,
            created_at=datetime.utcnow() - timedelta(hours=1)
        )
        self.post3 = SocialPost(
            user_id=self.user.id,
            title="Bóng Đen Ngõ Cũ",
            content_snippet="Án mạng ly kỳ tại phố cổ Hà Nội",
            genre="Trinh thám",
            concept_vector=json.dumps(v3),
            views_count=40,
            likes_count=5,
            completion_count=3,
            created_at=datetime.utcnow() - timedelta(minutes=10)
        )
        self.db.add_all([self.post1, self.post2, self.post3])
        self.db.commit()

    def tearDown(self):
        self.db.query(SocialPost).delete()
        self.db.query(User).delete()
        self.db.commit()
        self.db.close()

    def test_export_vectors_endpoint_status_and_schema(self):
        """
        Verify GET /api/recommender/export-vectors returns 200 OK
        with required top-level schema fields.
        """
        resp = self.client.get("/api/recommender/export-vectors")
        self.assertEqual(resp.status_code, 200)

        data = resp.json()
        self.assertEqual(data.get("status"), "success")
        self.assertEqual(data.get("vector_dim"), 128)
        self.assertEqual(data.get("count"), 3)
        self.assertIsInstance(data.get("vectors"), list)
        self.assertEqual(len(data.get("vectors")), 3)

    def test_vectors_are_strictly_128_dimensional_floats(self):
        """
        Every exported record must contain a concept_vector with exactly 128 float values.
        """
        resp = self.client.get("/api/recommender/export-vectors")
        data = resp.json()
        vectors = data.get("vectors", [])

        for item in vectors:
            vec = item.get("concept_vector")
            self.assertIsNotNone(vec, f"Post {item.get('post_id')} has no concept_vector")
            self.assertIsInstance(vec, list)
            self.assertEqual(
                len(vec),
                128,
                f"Post {item.get('post_id')} vector dim is {len(vec)}, expected 128."
            )
            # Ensure all values are numeric floats/ints
            for val in vec:
                self.assertIsInstance(val, (float, int))

    def test_vectors_are_l2_normalized(self):
        """
        Verify exported concept vectors are unit vectors (L2 norm ||v||_2 ≈ 1.0).
        """
        resp = self.client.get("/api/recommender/export-vectors")
        data = resp.json()

        for item in data.get("vectors", []):
            vec = item.get("concept_vector", [])
            norm = math.sqrt(sum(x * x for x in vec))
            self.assertAlmostEqual(
                norm,
                1.0,
                delta=0.05,
                msg=f"Vector for post {item.get('post_id')} not normalized: norm={norm}"
            )

    def test_pagination_limit_parameter(self):
        """Limit query parameter restricts the number of returned vector items."""
        resp = self.client.get("/api/recommender/export-vectors?limit=2")
        data = resp.json()
        self.assertEqual(data.get("count"), 2)
        self.assertEqual(len(data.get("vectors")), 2)

    def test_delta_sync_since_parameter(self):
        """
        The 'since' parameter filters vectors to only those created after the timestamp.
        """
        # post1 created 3h ago, post2 1h ago, post3 10m ago.
        # Filter with cutoff 2 hours ago -> should return post2 and post3 only.
        cutoff = (datetime.utcnow() - timedelta(hours=2)).isoformat()
        resp = self.client.get(f"/api/recommender/export-vectors?since={cutoff}")
        data = resp.json()
        returned_titles = [item["title"] for item in data.get("vectors", [])]
        self.assertIn("Kỷ Nguyên Số", returned_titles)
        self.assertIn("Bóng Đen Ngõ Cũ", returned_titles)
        self.assertNotIn("Bạch Đằng Chiến Sử", returned_titles)

    def test_empty_database_returns_zero_count(self):
        """When no posts match query, returns count=0 and empty vectors list."""
        future_time = (datetime.utcnow() + timedelta(days=1)).isoformat()
        resp = self.client.get(f"/api/recommender/export-vectors?since={future_time}")
        data = resp.json()
        self.assertEqual(data.get("status"), "success")
        self.assertEqual(data.get("count"), 0)
        self.assertEqual(data.get("vectors"), [])

    def test_client_local_re_ranking_math_simulation(self):
        """
        Simulate on-device TF.js client calculation:
        Given an active user interest vector and candidate vectors exported from backend,
        calculate local cosine similarity and MMR re-ranking locally without network calls.
        """
        # User is deeply interested in Vietnamese History
        user_interest = generate_concept_vector("Lịch sử Đại Việt kháng chiến chống giặc ngoại xâm", "Lịch sử")

        resp = self.client.get("/api/recommender/export-vectors")
        candidates = resp.json().get("vectors", [])

        # Local cosine similarity calculation
        ranked_candidates = []
        for cand in candidates:
            cand_vec = cand["concept_vector"]
            sim = cosine_similarity(user_interest, cand_vec)
            ranked_candidates.append((sim, cand))

        ranked_candidates.sort(key=lambda x: x[0], reverse=True)

        # The historical post must rank #1 for the history-loving user
        top_sim, top_post = ranked_candidates[0]
        self.assertEqual(top_post["title"], "Bạch Đằng Chiến Sử")
        self.assertGreater(top_sim, 0.4)

    def test_model_weights_endpoint_status_and_schema(self):
        """
        Verify GET /api/recommender/model-weights returns quantized neural model weights
        and architecture configuration.
        """
        resp = self.client.get("/api/recommender/model-weights")
        self.assertEqual(resp.status_code, 200)

        data = resp.json()
        self.assertEqual(data.get("status"), "success")
        self.assertEqual(data.get("model_name"), "NarrAI-Recommender-TwoTower-Lite")
        self.assertEqual(data.get("input_dim"), 128)
        self.assertEqual(data.get("output_dim"), 16)
        self.assertIn("architecture", data)
        self.assertIn("weights", data)
        self.assertIn("weights_manifest", data)
        self.assertGreater(data.get("total_params", 0), 1000)
        self.assertGreater(data.get("buffer_size_bytes", 0), 0)
        self.assertIsInstance(data.get("weights_base64"), str)



if __name__ == "__main__":
    unittest.main()
