import os
import sys
import re
import unittest
from unittest.mock import patch, MagicMock

# Ensure backend directory is in sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

os.environ.setdefault("GROQ_API_KEY", "gsk_test_dummy_key_for_unit_tests")
os.environ.setdefault("GROQ_API_KEY_COMIC", "gsk_test_dummy_key_for_unit_tests")

from agents.comic_agent import (
    ComicDirectorAgent,
    STYLE_PREFIX,
    STYLE_SUFFIX,
    SPATIAL_ENCLOSURES,
    LAYOUT_MAP,
    resolve_spatial_enclosure,
    sanitize_spatial_prompt,
    extract_action_from_prose,
    sanitize_complete_dialogue,
    decompose_story_beats,
)
from services.cloudflare_ai import (
    BASE_NEGATIVE_PROMPT,
    MODERN_SCHOOL_EXCLUSIONS,
    get_master_negative_prompt,
    get_deterministic_comic_seed,
    generate_image_cf,
    get_cached_or_generate_image,
)


class TestChallengerR2M3Stress(unittest.TestCase):
    """
    Challenger 2 Empirical Stress Test Suite for Milestone 3.
    Target Focus Areas:
      1. 100% Panel Spatial Enclosure Anchoring (across all layouts, background/classroom keywords, contradictory settings)
      2. Structured Beat Fallback (malformed/invalid JSON, spatial/style/DNA inheritance, 0% ellipsis)
      3. Cloudflare AI Negative Prompt Suffixing (master negative prompt, school exclusions, robust suffix formatting)
    """

    @classmethod
    def setUpClass(cls):
        with patch("llm.groq_client.Groq"):
            cls.agent = ComicDirectorAgent()

    # =========================================================================
    # FOCUS AREA 1: 100% PANEL SPATIAL ENCLOSURE ANCHORING
    # =========================================================================

    def test_anchoring_across_all_layout_types(self):
        """Verify setting anchor is attached to 100% of panels across square, tall, wide, and mapped layouts."""
        setting_dna = {
            "location_name": "Phòng học 10B",
            "setting_anchor": "sunlit high school classroom with rows of wooden desks and large glass windows"
        }
        dna_map = {
            "Linh": {
                "gender": "female",
                "role": "lead",
                "aliases": ["Linh", "cô bé"],
                "dna": "16yo Vietnamese schoolgirl, short bob hair, white shirt with red ribbon tie"
            }
        }

        raw_panels = [
            {"panel_index": 1, "image_prompt": "establishing wide shot", "dialogue_text": "Tiết đầu tiên bắt đầu.", "layout_type": "wide"},
            {"panel_index": 2, "image_prompt": "Linh speaking at desk", "dialogue_text": "Linh: \"Hôm nay trời đẹp quá!\"", "layout_type": "square"},
            {"panel_index": 3, "image_prompt": "full body dramatic pose", "dialogue_text": "Linh đứng lên phát biểu.", "layout_type": "tall"},
            {"panel_index": 4, "image_prompt": "over the shoulder view", "dialogue_text": "Bạn cùng bàn chăm chú lắng nghe.", "layout_type": "vertical"},
            {"panel_index": 5, "image_prompt": "horizontal panoramic view", "dialogue_text": "Cả lớp im lặng theo dõi.", "layout_type": "horizontal"},
            {"panel_index": 6, "image_prompt": "close up emotional reaction", "dialogue_text": "Linh mỉm cười nhẹ.", "layout_type": "closeup"},
            {"panel_index": 7, "image_prompt": "unknown layout fallback", "dialogue_text": "Tiếng chuông reo báo hiệu giờ ra chơi.", "layout_type": "custom_unknown"},
        ]

        validated = self.agent._validate_panels(raw_panels, character_dna_map=dna_map, setting_dna=setting_dna)
        self.assertEqual(len(validated), 7)

        expected_anchor = "setting: sunlit high school classroom with rows of wooden desks and large glass windows"
        for i, panel in enumerate(validated):
            prompt = panel["image_prompt"]
            self.assertIn(
                expected_anchor,
                prompt,
                f"Panel {i+1} (layout_type={panel['layout_type']}) MUST contain the setting anchor! Got: {prompt}"
            )
            # Verify layout normalization
            self.assertIn(panel["layout_type"], ["square", "tall", "wide"])

    def test_anchoring_with_existing_background_and_classroom_words(self):
        """Verify setting anchor is attached even when prompt contains words 'background' or 'classroom'."""
        setting_dna = {
            "location_name": "Lớp học",
            "setting_anchor": "modern high school classroom with chalkboard and wooden chairs"
        }

        panels = [
            {
                "panel_index": 1,
                "image_prompt": "close-up of student face with soft blurred background and bokeh",
                "dialogue_text": "Tôi tự hỏi ngày mai sẽ ra sao.",
                "layout_type": "square"
            },
            {
                "panel_index": 2,
                "image_prompt": "medium shot sitting in classroom near chalkboard",
                "dialogue_text": "An chăm chú nghe giảng.",
                "layout_type": "square"
            },
            {
                "panel_index": 3,
                "image_prompt": "tall vertical panel, dark background shadow behind student",
                "dialogue_text": "Không khí trở nên căng thẳng.",
                "layout_type": "tall"
            }
        ]

        validated = self.agent._validate_panels(panels, character_dna_map={}, setting_dna=setting_dna)
        self.assertEqual(len(validated), 3)

        expected_anchor = "setting: modern high school classroom with chalkboard and wooden chairs"
        for i, panel in enumerate(validated):
            prompt = panel["image_prompt"]
            self.assertIn(
                expected_anchor,
                prompt,
                f"Panel {i+1} containing background/classroom word must still attach full setting anchor! Got: {prompt}"
            )

    def test_anchoring_with_contradictory_outdoor_settings(self):
        """Verify contradictory outdoor elements (street, cars, highway) are quarantined and setting anchor is enforced."""
        setting_dna = {
            "location_name": "Lớp học",
            "setting_anchor": "modern classroom interior with wooden desks"
        }

        panels = [
            {
                "panel_index": 1,
                "image_prompt": "student standing on the busy street with moving cars and traffic along highway",
                "dialogue_text": "An bước vào lớp.",
                "layout_type": "wide"
            },
            {
                "panel_index": 2,
                "image_prompt": "student gazing out at ancient palace and stone castle",
                "dialogue_text": "An nhìn ra phía xa.",
                "layout_type": "square"
            }
        ]

        validated = self.agent._validate_panels(panels, character_dna_map={}, setting_dna=setting_dna)
        self.assertEqual(len(validated), 2)

        p1_prompt = validated[0]["image_prompt"].lower()
        self.assertNotIn("street", p1_prompt)
        self.assertNotIn("cars", p1_prompt)
        self.assertNotIn("highway", p1_prompt)
        self.assertIn("setting: modern classroom interior with wooden desks", p1_prompt)

        p2_prompt = validated[1]["image_prompt"].lower()
        self.assertNotIn("palace", p2_prompt)
        self.assertNotIn("castle", p2_prompt)
        self.assertIn("setting: modern classroom interior with wooden desks", p2_prompt)

    def test_anchoring_empty_or_none_prompt(self):
        """Verify empty or None image_prompt still produces valid prompt with anchor and style."""
        panels = [
            {"panel_index": 1, "image_prompt": "", "dialogue_text": "Mở đầu.", "layout_type": "wide"},
            {"panel_index": 2, "image_prompt": None, "dialogue_text": "Diễn biến.", "layout_type": "square"},
        ]
        validated = self.agent._validate_panels(panels, character_dna_map={}, setting_dna=None)
        self.assertEqual(len(validated), 2)
        for p in validated:
            prompt = p["image_prompt"]
            self.assertTrue(prompt.startswith(STYLE_PREFIX))
            self.assertTrue(prompt.endswith(STYLE_SUFFIX))
            self.assertIn("setting:", prompt)

    # =========================================================================
    # FOCUS AREA 2: STRUCTURED BEAT FALLBACK
    # =========================================================================

    def test_fallback_triggered_on_invalid_llm_json(self):
        """Verify fallback triggers when LLM returns invalid or malformed JSON."""
        story_text = (
            "Tiết học bắt đầu trong sự im lặng của lớp 12A.\n"
            "An cặm cụi ghi chép bài vào vở.\n"
            "Bất chợt Minh quay sang thì thầm: \"Cậu cho tớ mượn cây thước được không?\"\n"
            "An mỉm cười gật đầu và đưa cây thước cho bạn."
        )
        dna_map = {
            "An": {
                "gender": "female",
                "role": "lead",
                "aliases": ["An", "cô bé"],
                "dna": "17yo Vietnamese schoolgirl, black hair with bangs, white shirt and navy ribbon tie"
            }
        }
        setting_dna = {
            "location_name": "Lớp 12A",
            "setting_anchor": "sunny classroom with wooden desks and tall glass windows"
        }

        # Mock LLM to return malformed/invalid JSON string
        with patch.object(self.agent.llm, "chat", return_value="Here is your manga storyboard: [ {'panel_index': 1, image_prompt: invalid_unquoted..."):
            panels = self.agent.generate_comic_script(story_text)

        self.assertIsInstance(panels, list)
        self.assertGreaterEqual(len(panels), 3)

        expected_anchor = "setting: sunny classroom with wooden desks and tall glass windows"
        for p in panels:
            prompt = p["image_prompt"]
            # 1. Spatial Enclosure attached
            self.assertIn("setting:", prompt)
            # 2. Style Prefix and Suffix attached
            self.assertTrue(prompt.startswith(STYLE_PREFIX))
            self.assertTrue(prompt.endswith(STYLE_SUFFIX))
            # 3. Complete dialogue with 0% ellipsis
            self.assertNotIn("...", p["dialogue_text"])
            self.assertNotIn("…", p["dialogue_text"])
            self.assertIn(p["layout_type"], ["square", "tall", "wide"])

    def test_fallback_triggered_on_json_object_instead_of_array(self):
        """Verify fallback triggers when LLM returns a JSON dict/object instead of a JSON list."""
        story_text = "Thầy giáo bước vào lớp. Cả lớp đứng dậy chào thầy."
        with patch.object(self.agent.llm, "chat", return_value='{"error": "rate limit exceeded"}'):
            panels = self.agent.generate_comic_script(story_text)

        self.assertIsInstance(panels, list)
        self.assertGreaterEqual(len(panels), 2)
        for p in panels:
            self.assertTrue(p["image_prompt"].startswith(STYLE_PREFIX))
            self.assertTrue(p["image_prompt"].endswith(STYLE_SUFFIX))
            self.assertIn("setting:", p["image_prompt"])

    def test_fallback_inherits_character_dna_and_extracted_actions(self):
        """Verify fallback panels inherit character visual DNA and extract actions from prose."""
        story_text = (
            "An cặm cụi ghi chép bài vào cuốn tập nhỏ.\n"
            "Sau đó, cô bé chống cằm nhìn ra cửa sổ lớp học."
        )
        dna_map = {
            "An": {
                "gender": "female",
                "role": "lead",
                "aliases": ["An", "cô bé"],
                "dna": "17yo Vietnamese schoolgirl, jet-black bob hair, white shirt with navy ribbon tie"
            }
        }
        setting_dna = {
            "location_name": "Lớp học",
            "setting_anchor": "peaceful high school classroom with morning sunlight"
        }

        panels = self.agent._create_structured_beat_fallback(story_text, dna_map, setting_dna)
        self.assertEqual(len(panels), 2)

        # Panel 1: writing attentively
        p1_prompt = panels[0]["image_prompt"]
        self.assertIn("17yo vietnamese schoolgirl", p1_prompt.lower())
        self.assertIn("writing attentively", p1_prompt.lower())
        self.assertIn("setting: peaceful high school classroom with morning sunlight", p1_prompt.lower())

        # Panel 2: gazing out window
        p2_prompt = panels[1]["image_prompt"]
        self.assertIn("17yo vietnamese schoolgirl", p2_prompt.lower())
        self.assertIn("gazing pensively through the glass", p2_prompt.lower())
        self.assertIn("setting: peaceful high school classroom with morning sunlight", p2_prompt.lower())

    def test_fallback_with_empty_story_text(self):
        """Verify fallback handles empty or whitespace story text gracefully."""
        panels = self.agent._create_structured_beat_fallback("", {}, None)
        self.assertEqual(len(panels), 2)
        for p in panels:
            self.assertTrue(p["image_prompt"].startswith(STYLE_PREFIX))
            self.assertTrue(p["image_prompt"].endswith(STYLE_SUFFIX))
            self.assertIn("setting:", p["image_prompt"])
            self.assertNotIn("...", p["dialogue_text"])

    # =========================================================================
    # FOCUS AREA 3: CLOUDFLARE AI NEGATIVE PROMPT SUFFIXING
    # =========================================================================

    def test_get_master_negative_prompt_contains_modern_school_exclusions(self):
        """Verify get_master_negative_prompt('school') bundles base and modern school exclusions."""
        neg_school = get_master_negative_prompt("school").lower()

        # Universal base exclusions
        self.assertIn("photorealistic", neg_school)
        self.assertIn("color", neg_school)
        self.assertIn("western comic", neg_school)
        self.assertIn("speech bubble", neg_school)
        self.assertIn("watermark", neg_school)
        self.assertIn("bad anatomy", neg_school)

        # Modern school exclusions
        self.assertIn("historical clothing", neg_school)
        self.assertIn("ancient robes", neg_school)
        self.assertIn("hanfu", neg_school)
        self.assertIn("kimono", neg_school)
        self.assertIn("huyền bào", neg_school)
        self.assertIn("armor", neg_school)
        self.assertIn("sword", neg_school)
        self.assertIn("ancient temple", neg_school)
        self.assertIn("palace", neg_school)
        self.assertIn("castle", neg_school)
        self.assertIn("busy highway", neg_school)
        self.assertIn("moving cars", neg_school)

        # The default must not impose school-only exclusions on unrelated genres.
        neg_default = get_master_negative_prompt().lower()
        self.assertNotIn("historical clothing", neg_default)
        self.assertNotIn("busy highway", neg_default)

        # Non-school genre test
        neg_generic = get_master_negative_prompt("scifi").lower()
        self.assertNotIn("huyền bào", neg_generic)
        self.assertIn("photorealistic", neg_generic)

    def test_generate_image_cf_suffix_formatting_robustness(self):
        """Verify custom negative prompt suffixes are cleanly appended without commas or formatting bugs."""
        with patch("services.cloudflare_ai.get_cloudflare_token", return_value="fake_token"), \
             patch("services.cloudflare_ai.get_account_id", return_value="fake_account"), \
             patch("requests.post") as mock_post:

            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.content = b"\xff\xd8" + (b"mock_jpeg_bytes" * 50)
            mock_post.return_value = mock_resp

            # Case A: Standard suffix
            generate_image_cf("test prompt", seed=100000, negative_prompt_suffix="extra_token_1")
            _, kwargs = mock_post.call_args
            neg1 = kwargs["json"]["negative_prompt"]
            self.assertTrue(neg1.endswith(", extra_token_1"))
            self.assertNotIn(", ,", neg1)

            # Case B: Suffix with leading and trailing commas and spaces
            generate_image_cf("test prompt", seed=100000, negative_prompt_suffix=" ,  extra_token_2 ,,, ")
            _, kwargs = mock_post.call_args
            neg2 = kwargs["json"]["negative_prompt"]
            self.assertTrue(neg2.endswith(", extra_token_2"))
            self.assertNotIn(", ,", neg2)

            # Case C: None or empty suffix
            generate_image_cf("test prompt", seed=100000, negative_prompt_suffix="")
            _, kwargs = mock_post.call_args
            neg3 = kwargs["json"]["negative_prompt"]
            self.assertFalse(neg3.endswith(","))
            self.assertFalse(neg3.endswith(" "))

            # Case D: Using custom_negative_prompt alias
            generate_image_cf("test prompt", seed=100000, custom_negative_prompt="alias_token_4")
            _, kwargs = mock_post.call_args
            neg4 = kwargs["json"]["negative_prompt"]
            self.assertTrue(neg4.endswith(", alias_token_4"))

    def test_deterministic_seed_consistency(self):
        """Verify get_deterministic_comic_seed produces consistent locked seeds across same story_id."""
        seed_1a = get_deterministic_comic_seed(42)
        seed_1b = get_deterministic_comic_seed(42)
        seed_2 = get_deterministic_comic_seed(43)

        self.assertEqual(seed_1a, seed_1b)
        self.assertNotEqual(seed_1a, seed_2)
        self.assertGreaterEqual(seed_1a, 100000)
        self.assertLessEqual(seed_1a, 999999)


if __name__ == "__main__":
    unittest.main(verbosity=2)
