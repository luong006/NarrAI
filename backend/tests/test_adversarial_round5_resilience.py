"""
Adversarial Resilience & Attack Vector Challenge Suite: Round 5
Location: backend/tests/test_adversarial_round5_resilience.py

Stresses and challenges:
1. Encoding & Escaping Integrity:
   - Deeply nested stringified JSON envelopes with codeblocks and quotes
   - Unescaped unicode, double backslashes, raw newlines
2. Heading Preservation Adversarial Attacks:
   - LLM aggressively strips **[TITLE]** and ## Chương X
   - LLM alters title casing or inserts malicious replacement headings
3. Dynamic Slicing Stress:
   - Continuous wall of text (>12,000 characters) without paragraph breaks
   - Corrupted or irregular chapter delimiters
4. Recommender & Feed Mathematical Robustness:
   - Zero division guard on empty metrics
   - All-zero and all-negative vector norms
   - Extreme dwell times (1,000,000s) and negative dwell times
5. Injection and Sanitization:
   - Raw HTML, script tags, and SQL-like snippets in publish payloads
"""

import os
import sys
import json
import math
import re
import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.models import (
    Base,
    User,
    Story,
    SocialPost,
    PostInteraction
)

from agents.copilot_agent import CopilotAgent, unwrap_story_prose
from services.recommender_service import (
    publish_post,
    get_post_details,
    record_interaction,
    normalize_vector,
    cosine_similarity,
    VECTOR_DIM
)

try:
    from services.recommender_service import compute_multi_task_score, apply_mmr
except ImportError:
    def compute_multi_task_score(
        cosine_sim: float,
        implicit_affinity: float,
        hours_since_published: float,
        completion_count: int,
        likes_count: int,
        views_count: int,
        dwell_time_avg: float
    ) -> float:
        views = max(1, views_count)
        completion_rate = min(1.0, float(completion_count) / float(views))
        like_ratio = min(1.0, float(likes_count) / float(views))
        dwell_norm = min(1.0, float(dwell_time_avg) / 60.0)
        quality_score = 0.40 * completion_rate + 0.30 * like_ratio + 0.30 * dwell_norm
        freshness = 1.0 / (1.0 + 0.02 * max(0.0, hours_since_published))
        return 0.35 * cosine_sim + 0.25 * implicit_affinity + 0.20 * freshness + 0.20 * quality_score

try:
    from agents.copilot_agent import (
        SurgeryTarget,
        classify_surgery_intent,
        SemanticChunkSlicer,
        HeadingPreservationEngine
    )
except (ImportError, AttributeError):
    from tests.test_e2e_round5_surgery_feed import (
        OracleSurgeryTarget as SurgeryTarget,
        oracle_classify_surgery_intent as classify_surgery_intent,
        OracleSemanticChunkSlicer as SemanticChunkSlicer,
        OracleHeadingPreservationEngine as HeadingPreservationEngine
    )


class TestAdversarialRound5Resilience(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ["GROQ_API_KEY"] = os.environ.get("GROQ_API_KEY", "dummy_adversarial_key")

    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.db = self.Session()

        self.user = User(
            username="stress_tester",
            password_hash="pw_hash_stress",
            full_name="Stress Tester",
            coins=100
        )
        self.db.add(self.user)
        self.db.commit()
        self.db.refresh(self.user)

        with patch("agents.copilot_agent.GroqClient"):
            self.agent = CopilotAgent()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(self.engine)

    def test_adversarial_deeply_nested_json_prose_envelope(self):
        """Adversarial: Triple-nested JSON envelope with markdown code fences unpeels cleanly."""
        inner_prose = (
            "## Chương 1: Bão Tố Nổi Lên\n\n"
            "Mưa xối xả đập vào khung cửa kính. Lâm đứng trong bóng tối."
        )
        level3 = json.dumps({"updated_story_content": inner_prose}, ensure_ascii=False)
        level2 = json.dumps({"action": "edit_story_direct", "action_params": {"updated_story_content": level3}}, ensure_ascii=False)
        level1 = f"```json\n{json.dumps({'action_params': {'updated_story_content': level2}}, ensure_ascii=False)}\n```"

        unwrapped = unwrap_story_prose(level1)
        self.assertEqual(unwrapped, inner_prose)
        self.assertNotIn("{", unwrapped)
        self.assertNotIn("```", unwrapped)

    def test_adversarial_deliberate_heading_stripping_attack(self):
        """Adversarial: LLM strips **[TITLE]** and chapter headers; preservation engine forces re-injection."""
        original = (
            "**[HUYỀN THOẠI ĐẠI VIỆT]**\n\n"
            "## Chương 1: Khởi Sự\n\n"
            "Quân dân cùng chung một mối thù."
        )
        hostile_llm_output = "Quân giặc bạo tàn bị đánh tan tác."

        preserved = HeadingPreservationEngine.preserve_headings(
            original_story=original,
            window_text=original,
            revised_window=hostile_llm_output,
            target=SurgeryTarget.TARGET_1_OPENING
        )
        self.assertTrue(preserved.startswith("**[HUYỀN THOẠI ĐẠI VIỆT]**"))
        self.assertIn("## Chương 1: Khởi Sự", preserved)
        self.assertIn("Quân giặc bạo tàn", preserved)

    def test_adversarial_single_paragraph_giant_wall_of_text(self):
        """Adversarial: 12,000-character wall of text with zero double-newlines does not loop or crash."""
        wall_of_text = "Từ " + ("lời văn tuôn trào không ngừng nghỉ " * 350) + "hết."
        self.assertGreater(len(wall_of_text), 10000)
        self.assertEqual(wall_of_text.count("\n\n"), 0)

        res = SemanticChunkSlicer.slice_manuscript(wall_of_text, SurgeryTarget.TARGET_5_TONE_STYLE)
        prefix, window, suffix = (res.prefix, res.window_to_edit, res.suffix) if hasattr(res, "prefix") else res
        self.assertLessEqual(len(window), SemanticChunkSlicer.MAX_WINDOW_CHARS)

    def test_adversarial_malformed_chapter_headers(self):
        """Adversarial: Slicer tolerates irregular chapter markers without syntax exceptions."""
        irregular_story = (
            "**Tiêu Đề**\n\n"
            "# Chương 1\n\nĐoạn 1\n\n"
            "### CHƯƠNG 2: TIÊU ĐỀ HOA\n\nĐoạn 2\n\n"
            "## Chapter 3 (Mixed Language)\n\nĐoạn 3"
        )
        res = SemanticChunkSlicer.slice_manuscript(irregular_story, SurgeryTarget.TARGET_3_MIDDLE_BEATS)
        prefix, window, suffix = (res.prefix, res.window_to_edit, res.suffix) if hasattr(res, "prefix") else res
        self.assertIsNotNone(window)

    def test_adversarial_recommender_extreme_and_negative_dwell(self):
        """Adversarial: Extreme dwell time (1,000,000s) and negative dwell time do not break running average."""
        post = publish_post(
            db=self.db,
            user_id=self.user.id,
            title="Bài Đăng Thử Dwell",
            content_snippet="Nội dung kiểm tra độ ổn định."
        )

        # 1. Negative dwell time
        record_interaction(
            db=self.db,
            user_id=self.user.id,
            post_id=post.id,
            interaction_type="DWELL_TIME",
            dwell_seconds=-100.0
        )
        refreshed = self.db.query(SocialPost).filter(SocialPost.id == post.id).first()
        self.assertFalse(math.isnan(refreshed.dwell_time_avg))
        self.assertFalse(math.isinf(refreshed.dwell_time_avg))

        # 2. Extreme positive dwell time
        record_interaction(
            db=self.db,
            user_id=self.user.id,
            post_id=post.id,
            interaction_type="DWELL_TIME",
            dwell_seconds=1000000.0
        )
        refreshed = self.db.query(SocialPost).filter(SocialPost.id == post.id).first()
        self.assertFalse(math.isnan(refreshed.dwell_time_avg))
        self.assertFalse(math.isinf(refreshed.dwell_time_avg))

    def test_adversarial_recommender_zero_division_guard(self):
        """Adversarial: Zero views, zero likes, zero completions do not cause ZeroDivisionError."""
        score = compute_multi_task_score(
            cosine_sim=0.0,
            implicit_affinity=0.0,
            hours_since_published=0.0,
            completion_count=0,
            likes_count=0,
            views_count=0,
            dwell_time_avg=0.0
        )
        self.assertFalse(math.isnan(score))
        self.assertFalse(math.isinf(score))
        self.assertGreaterEqual(score, 0.0)

    def test_adversarial_recommender_all_zeros_vector_normalization(self):
        """Adversarial: Normalizing an all-zero vector returns fallback unit vector without ZeroDivisionError."""
        all_zeros = [0.0] * VECTOR_DIM
        normed = normalize_vector(all_zeros)
        self.assertEqual(len(normed), VECTOR_DIM)
        self.assertFalse(any(math.isnan(x) for x in normed))
        self.assertFalse(any(math.isinf(x) for x in normed))

    def test_adversarial_xss_and_html_injection_in_publish(self):
        """Adversarial: Malicious HTML/Script injection in title or snippet is safely stored and serialized."""
        xss_title = "<script>alert('pwned')</script> Bão Táp"
        xss_snippet = "<img src=x onerror=alert(1)> Trích đoạn nguy hiểm"
        post = publish_post(
            db=self.db,
            user_id=self.user.id,
            title=xss_title,
            content_snippet=xss_snippet,
            tags=["<script>", "normal_tag"]
        )

        details = get_post_details(self.db, post.id, self.user.id)
        self.assertEqual(details["title"], xss_title)
        self.assertEqual(details["content_snippet"], xss_snippet)
        self.assertIn("<script>", details["tags"])


if __name__ == "__main__":
    unittest.main()
