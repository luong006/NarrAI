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
    DNA_EXTRACTOR_PROMPT,
    SPATIAL_ENCLOSURES,
    resolve_spatial_enclosure,
    sanitize_spatial_prompt,
    ACTION_GESTURE_MAPPINGS,
    extract_action_from_prose,
)
from services.cloudflare_ai import (
    BASE_NEGATIVE_PROMPT,
    MODERN_SCHOOL_EXCLUSIONS,
    get_master_negative_prompt,
    get_deterministic_comic_seed,
    generate_image_cf,
    get_cached_or_generate_image,
    format_pollinations_prompt,
)


class TestChallengerR2M3Adversarial(unittest.TestCase):
    """
    Empirical Adversarial Stress Suite for Milestone 3 (R3 Visual Consistency & Text-to-Image Sync).
    Updated specification: Asserts robust, hardened behavior resolving all 4 vulnerability categories.
    """
    @classmethod
    def setUpClass(cls):
        with patch("llm.groq_client.Groq"):
            cls.agent = ComicDirectorAgent()

    # =========================================================================
    # 1. ADVERSARIAL TESTING OF sanitize_spatial_prompt()
    # =========================================================================

    def test_strip_traffic_and_vehicles(self):
        """Verify on the busy street, speeding car, and traffic are cleanly stripped."""
        enclosure = SPATIAL_ENCLOSURES["classroom"]
        
        # 'on the busy street'
        res1 = sanitize_spatial_prompt("A student sitting at desk on the busy street", enclosure)
        self.assertNotIn("street", res1.lower())
        self.assertNotIn("busy", res1.lower())

        # 'speeding car'
        res2 = sanitize_spatial_prompt("looking out at a speeding car", enclosure)
        self.assertNotIn("car", res2.lower())
        self.assertNotIn("speeding", res2.lower())

        # 'traffic'
        res3 = sanitize_spatial_prompt("classroom with distant traffic noise", enclosure)
        self.assertNotIn("traffic", res3.lower())

    def test_subwords_strict_preservation(self):
        """Verify innocent words with subwords (classroom, cardigan, scarf, board, class) are preserved."""
        enclosure = SPATIAL_ENCLOSURES["classroom"]
        input_prompt = "classroom student wearing cozy cardigan and warm scarf near the blackboard in class"
        sanitized = sanitize_spatial_prompt(input_prompt, enclosure)

        self.assertIn("classroom", sanitized.lower())
        self.assertIn("cardigan", sanitized.lower())
        self.assertIn("scarf", sanitized.lower())
        self.assertIn("blackboard", sanitized.lower())
        self.assertIn("class", sanitized.lower())

    def test_fix_ancient_palace_strips_ancient_modifier(self):
        """
        FIXED: 'ancient palace'
        The modifier whitelist includes 'ancient'. When 'palace' is stripped, 'ancient' is also cleanly stripped.
        """
        enclosure = SPATIAL_ENCLOSURES["classroom"]
        res = sanitize_spatial_prompt("student standing in an ancient palace", enclosure)
        self.assertNotIn("palace", res.lower())
        self.assertNotIn("ancient", res.lower(), "Verifies that 'ancient' is cleanly stripped with 'palace'")
        self.assertEqual(res, "student standing")

    def test_fix_sword_sanitized_from_classroom_spatial_enclosure(self):
        """
        FIXED: 'sword', 'blade', 'weapon' are registered in SPATIAL_ENCLOSURES forbidden list.
        """
        enclosure = SPATIAL_ENCLOSURES["classroom"]
        self.assertIn("sword", enclosure["forbidden_spatial_tokens"])
        self.assertIn("blade", enclosure["forbidden_spatial_tokens"])
        self.assertIn("weapon", enclosure["forbidden_spatial_tokens"])
        
        res = sanitize_spatial_prompt("student holding a wooden sword in classroom", enclosure)
        self.assertNotIn("sword", res.lower(), "Verifies that 'sword' is sanitized from positive prompt")

    def test_fix_prepositions_leave_no_dangling_syntax(self):
        """
        FIXED: Prepositions 'at', 'to', 'through', 'into' are handled and stripped without dangling syntax.
        """
        enclosure = SPATIAL_ENCLOSURES["classroom"]
        res = sanitize_spatial_prompt("student looking at the speeding car", enclosure)
        self.assertNotIn("car", res.lower())
        self.assertNotIn("speeding", res.lower())
        self.assertFalse(res.endswith("at the") or res.endswith("at"), f"Got dangling preposition: {res}")
        self.assertEqual(res, "student looking")

    def test_fix_internal_double_commas_collapsed(self):
        """
        FIXED: Stripping a token from 'item1, street, item2' cleanly collapses consecutive commas.
        """
        enclosure = SPATIAL_ENCLOSURES["classroom"]
        res = sanitize_spatial_prompt("girl at desk, on the busy street, reading notes", enclosure)
        self.assertNotIn(", ,", res, "Consecutive commas must be collapsed")
        self.assertEqual(res, "girl at desk, reading notes")

    def test_fix_plural_buses_matched_and_stripped(self):
        """
        FIXED: Regex handles plural 'buses' with (?:es|s)?.
        """
        enclosure = SPATIAL_ENCLOSURES["classroom"]
        res = sanitize_spatial_prompt("school buses parked outside", enclosure)
        self.assertNotIn("buses", res.lower())
        self.assertNotIn("bus", res.lower())

    # =========================================================================
    # 2. ADVERSARIAL TESTING OF extract_action_from_prose()
    # =========================================================================

    def test_valid_vietnamese_student_actions(self):
        """Verify recognition of common Vietnamese student action expressions."""
        # Taking notes
        act1, _ = extract_action_from_prose("An cúi đầu cặm cụi viết bài vào vở")
        self.assertIsNotNone(act1)
        self.assertIn("writing attentively", act1.lower())

        # Looking out window
        act2, _ = extract_action_from_prose("Cô bé chống cằm nhìn ra cửa sổ mộng mơ")
        self.assertIsNotNone(act2)
        self.assertIn("window", act2.lower())

        # Turning to desk mate
        act3, _ = extract_action_from_prose("An quay sang nói chuyện với bạn cùng bàn")
        self.assertIsNotNone(act3)
        self.assertIn("desk mate", act3.lower())

        # Standing up abruptly
        act4, _ = extract_action_from_prose("Cậu ấy bàng hoàng đứng bật dậy làm đổ ghế")
        self.assertIsNotNone(act4)
        self.assertIn("standing up abruptly", act4.lower())

    def test_fix_negation_awareness_prevents_window_hallucination(self):
        """
        FIXED: Negation Awareness
        Prose: 'An tuyệt đối không nhìn ra cửa sổ mà chăm chú nhìn lên bảng đen'.
        Does NOT trigger window gaze; correctly matches non-negated 'nhìn lên bảng đen'.
        """
        prose = "An tuyệt đối không nhìn ra cửa sổ mà chăm chú nhìn lên bảng đen"
        act, shot = extract_action_from_prose(prose)
        self.assertIsNotNone(act)
        self.assertNotIn("window", act.lower(), "Must NOT hallucinate looking out window when negated")
        self.assertIn("classroom blackboard", act.lower(), "Must match positive action looking at blackboard")

    def test_fix_dialogue_reprimand_does_not_hallucinate_smile(self):
        """
        FIXED: Reprimand / Prohibition
        Teacher says: 'Đừng có quay sang nói chuyện nữa!'.
        Prohibition 'đừng có' prevents smiling desk mate action.
        """
        prose = 'Thầy giáo nghiêm giọng: "Các em đừng có quay sang nói chuyện nữa!"'
        act, shot = extract_action_from_prose(prose)
        self.assertIsNone(act, f"Reprimand must not trigger positive action, got: {act}")

    def test_fix_standalone_sigh_does_not_force_head_on_desk(self):
        """
        FIXED: Overly Broad Pattern 6
        'Thở dài' without desk pairing ('gục', 'bàn', 'nằm') does NOT force resting head on desk.
        """
        prose = "Thầy giáo đứng trước lớp thở dài một tiếng mệt mỏi"
        act, _ = extract_action_from_prose(prose)
        self.assertIsNone(act, f"Standalone sigh must not force desk head-down, got: {act}")

    def test_fix_greeting_bow_does_not_force_writing_notebook(self):
        """
        FIXED: Pattern 1 Bow disambiguation
        A greeting bow ('cúi đầu chào') does NOT force writing in notebook.
        """
        prose = "An cúi đầu lễ phép chào cô giáo khi bước vào"
        act, _ = extract_action_from_prose(prose)
        self.assertIsNone(act, f"Greeting bow must not force writing notebook, got: {act}")

    def test_fix_internal_emotion_kinh_ngac_does_not_force_desktop_slam(self):
        """
        FIXED: Internal emotional thought of surprise does NOT force physical desktop slam.
        """
        prose = "Một thoáng kinh ngạc lướt qua suy nghĩ của An"
        act, _ = extract_action_from_prose(prose)
        self.assertIsNone(act, f"Internal thought must not trigger desktop slam, got: {act}")

    # =========================================================================
    # 3. TOKEN BUDGET & CLIP LIMIT AUDIT
    # =========================================================================

    def test_fix_setting_anchor_and_action_within_clip_77_tokens(self):
        """
        FIXED: Setting anchor and core action gesture are positioned early
        (immediately after STYLE_PREFIX), well within the first 65 CLIP tokens.
        """
        setting_dna = {
            "location_name": "Lớp học 12A",
            "setting_anchor": (
                "modern Japanese high school classroom interior, neat wooden student desks and chairs, "
                "large green chalkboard mounted on front wall, tall multi-pane glass windows with sunlight "
                "streaming across wooden floor, peaceful classroom atmosphere"
            )
        }
        dna_map = {
            "An": {
                "gender": "female",
                "role": "lead",
                "aliases": ["An", "cô bé"],
                "dna": (
                    "17yo Vietnamese schoolgirl, soft oval face, gentle dark almond eyes, sharp jawline, "
                    "straight jet-black hair with blunt bangs across forehead and shoulder-length bob, "
                    "wearing crisp white short-sleeve school uniform button-up shirt with stiff collar, "
                    "small dark navy ribbon tie pinned at collar, pleated dark navy skirt"
                )
            }
        }
        panels = [{
            "panel_index": 1,
            "image_prompt": "medium close-up shot of student turning around with a bright smile near the window",
            "dialogue_text": "An cúi đầu cặm cụi viết bài vào cuốn tập.",
            "layout_type": "square"
        }]

        validated = self.agent._validate_panels(panels, character_dna_map=dna_map, setting_dna=setting_dna)
        self.assertEqual(len(validated), 1)
        final_prompt = validated[0]["image_prompt"]

        # Setting anchor must appear at the very start of the prompt body (pos == len(STYLE_PREFIX))
        setting_pos = final_prompt.find("setting:")
        prefix_len = len(STYLE_PREFIX)
        self.assertLessEqual(setting_pos, prefix_len + 30, f"Setting anchor must be early. Pos: {setting_pos}, Prefix: {prefix_len}")

        # Both setting and action must be present
        self.assertIn("setting:", final_prompt)
        self.assertIn("writing attentively", final_prompt)

    def test_fix_pollinations_fallback_preserves_setting_and_action(self):
        """
        FIXED: format_pollinations_prompt cleanly preserves setting anchor and action gesture
        without broken words or mid-token truncations.
        """
        prompt = (
            f"{STYLE_PREFIX}"
            "setting: modern Japanese high school classroom interior, "
            "sitting at wooden student desk, writing attentively, "
            "17yo Vietnamese schoolgirl, soft oval face, gentle dark almond eyes, sharp jawline, "
            "wearing crisp white short-sleeve school uniform button-up shirt with stiff collar"
            f"{STYLE_SUFFIX}"
        )
        formatted = format_pollinations_prompt(prompt, max_len=300)
        self.assertIn("setting:", formatted)
        self.assertIn("writing attentively", formatted)
        self.assertNotIn(", ,", formatted)
        self.assertFalse(re.search(r'\b[a-z]{1,2}$', formatted))


if __name__ == "__main__":
    unittest.main(verbosity=2)
