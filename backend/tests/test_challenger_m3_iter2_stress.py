import os
import sys
import unittest
import re
from unittest.mock import patch

# Ensure backend directory is in sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

os.environ.setdefault("GROQ_API_KEY", "gsk_test_dummy_key_for_unit_tests")
os.environ.setdefault("GROQ_API_KEY_COMIC", "gsk_test_dummy_key_for_unit_tests")

from agents.comic_agent import (
    ComicDirectorAgent,
    sanitize_complete_dialogue,
    decompose_story_beats
)
from agents.copilot_agent import unwrap_story_prose
from services.cloudflare_ai import get_deterministic_comic_seed
from main import extract_sentence_bounded_chunk


class TestChallengerM3Iter2Stress(unittest.TestCase):
    """
    Adversarial Stress Test Suite for Milestone 3 Iteration 2 remediations.
    Specifically challenges:
    1. Spaced dots challenge (varied spacing, zero ellipses guarantee).
    2. Terminal punctuation challenge (all outputs terminate in valid sentence marks: '.', '!', '?', '"', '”').
    3. Null / None dialogue fallback and beat pacing integrity.
    4. Milestone 1 and 2 regressions.
    """
    @classmethod
    def setUpClass(cls):
        with patch("llm.groq_client.Groq"):
            cls.agent = ComicDirectorAgent()

    VALID_TERMINAL_MARKS = ('.', '!', '?', '"', '”', "'")

    # =========================================================================
    # 1. SPACED DOTS CHALLENGE: VARIED SPACING & 100% ZERO ELLIPSES
    # =========================================================================

    def test_spaced_dots_exact_prompt_cases(self):
        """Test the exact 4 cases specified in the adversarial challenge assignment."""
        # Case 1: "Tôi . . . không biết."
        res1 = sanitize_complete_dialogue("Tôi . . . không biết.")
        self.assertNotIn("...", res1)
        self.assertNotIn("…", res1)
        self.assertNotIn(".....", res1)
        self.assertEqual(res1, "Tôi - không biết.")
        self.assertTrue(res1.endswith(self.VALID_TERMINAL_MARKS))

        # Case 2: "A  .  .  .  B"
        res2 = sanitize_complete_dialogue("A  .  .  .  B")
        self.assertNotIn("...", res2)
        self.assertNotIn("…", res2)
        self.assertEqual(res2, "A - B.")
        self.assertTrue(res2.endswith(self.VALID_TERMINAL_MARKS))

        # Case 3: " . . . " (pure dots/whitespace returns empty string)
        res3 = sanitize_complete_dialogue(" . . . ")
        self.assertEqual(res3, "")
        self.assertNotIn("...", res3)

        # Case 4: "... . . . ..." (pure dots/whitespace returns empty string)
        res4 = sanitize_complete_dialogue("... . . . ...")
        self.assertEqual(res4, "")
        self.assertNotIn("...", res4)

    def test_spaced_dots_varied_spacing_and_quantities(self):
        """Test wide array of spacing variations between dots mid-sentence."""
        cases = [
            ("Tôi . . không biết.", "Tôi - không biết."),
            ("Tôi . . . không biết.", "Tôi - không biết."),
            ("Tôi . . . . không biết.", "Tôi - không biết."),
            ("Tôi . . . . . không biết.", "Tôi - không biết."),
            ("Tôi  .  .  .  không biết.", "Tôi - không biết."),
            ("Tôi   .   .   .   không biết.", "Tôi - không biết."),
            ("Tôi .    .      . không biết.", "Tôi - không biết."),
            ("Tôi .\t.\t. không biết.", "Tôi - không biết."),
            ("Tôi .\n.\n. không biết.", "Tôi - không biết."),
        ]
        for inp, expected in cases:
            res = sanitize_complete_dialogue(inp)
            self.assertNotIn("...", res, f"Failed zero ellipses on: {inp}")
            self.assertNotIn("…", res, f"Failed zero ellipses on: {inp}")
            self.assertEqual(res, expected, f"Output mismatch for input: {inp}")
            self.assertTrue(res.endswith(self.VALID_TERMINAL_MARKS))

    def test_spaced_dots_mixed_with_contiguous_and_unicode_ellipses(self):
        """Test hybrid patterns mixing contiguous dots, unicode ellipses, and spaced dots."""
        cases = [
            ("Tôi... . . . không biết.", "Tôi - không biết."),
            ("Tôi . . . ... không biết.", "Tôi - không biết."),
            ("Tôi … . . … không biết.", "Tôi - không biết."),
            ("Tôi ... … ... không biết.", "Tôi - không biết."),
            ("Tôi … . . . … không biết.", "Tôi - không biết."),
            ("Tôi . . . - không biết.", "Tôi - không biết."),
            ("Tôi - . . . không biết.", "Tôi - không biết."),
        ]
        for inp, expected in cases:
            res = sanitize_complete_dialogue(inp)
            self.assertNotIn("...", res, f"Ellipsis leaked in: {res}")
            self.assertNotIn("…", res, f"Unicode ellipsis leaked in: {res}")
            self.assertEqual(res, expected, f"Mismatch for: {inp}")
            self.assertTrue(res.endswith(self.VALID_TERMINAL_MARKS))

    def test_spaced_dots_with_dialogue_particles_and_stutters(self):
        """Test Vietnamese auxiliary particles and speech stutters combined with spaced dots."""
        # Auxiliary particle with spaced dots: should normalize to particle + space
        res1 = sanitize_complete_dialogue("Tôi sẽ . . . trả thù cho bạn.")
        self.assertNotIn("...", res1)
        self.assertEqual(res1, "Tôi sẽ trả thù cho bạn.")

        res2 = sanitize_complete_dialogue("Chúng ta đã . . . làm hết sức mình.")
        self.assertNotIn("...", res2)
        self.assertEqual(res2, "Chúng ta đã làm hết sức mình.")

        # Stutter with spaced dots: should normalize to word - word
        res3 = sanitize_complete_dialogue("Tôi . . . tôi không thể tin được.")
        self.assertNotIn("...", res3)
        self.assertEqual(res3, "Tôi - tôi không thể tin được.")

        res4 = sanitize_complete_dialogue("Anh  .  .  .  anh bình tĩnh lại đi.")
        self.assertNotIn("...", res4)
        self.assertEqual(res4, "Anh - anh bình tĩnh lại đi.")

    def test_spaced_dots_leading_and_trailing(self):
        """Test spaced dots at beginning and end of strings, with and without quotes."""
        # Trailing spaced dots without quote
        res1 = sanitize_complete_dialogue("Không thể nào . . . ")
        self.assertEqual(res1, "Không thể nào.")
        self.assertNotIn("...", res1)

        # Trailing spaced dots with double quote
        res2 = sanitize_complete_dialogue('"Không thể nào . . . "')
        self.assertEqual(res2, '"Không thể nào."')
        self.assertNotIn("...", res2)

        # Trailing spaced dots with curly quote
        res3 = sanitize_complete_dialogue('“Không thể nào .  .  .  ”')
        self.assertEqual(res3, '“Không thể nào.”')
        self.assertNotIn("...", res3)

        # Trailing spaced dots with question mark
        res4 = sanitize_complete_dialogue("Cậu nói thật sao . . . ?")
        self.assertEqual(res4, "Cậu nói thật sao?")
        self.assertNotIn("...", res4)

        # Trailing spaced dots with exclamation mark
        res5 = sanitize_complete_dialogue("Dừng lại ngay . . . !")
        self.assertEqual(res5, "Dừng lại ngay!")
        self.assertNotIn("...", res5)

        # Leading spaced dots
        res6 = sanitize_complete_dialogue(" . . . Hôm nay trời thật đẹp.")
        self.assertEqual(res6, "- Hôm nay trời thật đẹp.")
        self.assertNotIn("...", res6)

    def test_spaced_dots_exhaustive_random_generator(self):
        """Fuzz testing: Generate 50+ adversarial spaced dot variations and verify 0% ellipses."""
        import random
        random.seed(42)

        words = ["Tôi", "không", "thể", "chấp", "nhận", "sự", "thật", "này"]
        for _ in range(60):
            # Construct a random dot/space pattern
            dot_count = random.randint(2, 8)
            spaced_pattern = "".join(random.choice([" ", "  ", "\t", ""]) + "." for _ in range(dot_count)) + " "
            w1 = random.choice(words)
            w2 = random.choice(words)
            test_str = f"{w1} {spaced_pattern} {w2}"

            res = sanitize_complete_dialogue(test_str)
            self.assertNotIn("...", res, f"Leak found with pattern '{spaced_pattern}' in '{test_str}' -> '{res}'")
            self.assertNotIn("…", res)
            self.assertNotIn(".....", res)
            self.assertFalse(re.search(r'\.{2,}', res), f"Consecutive dots leaked: {res}")
            self.assertTrue(res.endswith(self.VALID_TERMINAL_MARKS))

    # =========================================================================
    # 2. TERMINAL PUNCTUATION CHALLENGE: ALL OUTPUTS TERMINATE IN VALID MARKS
    # =========================================================================

    def test_terminal_punctuation_all_categories(self):
        """Verify all outputs strictly terminate in valid marks: '.', '!', '?', '\"', '”'."""
        test_cases = [
            # Standard unpunctuated
            ("Hôm nay là một ngày nắng đẹp", "."),
            ("Tôi đang trên đường tới trường", "."),
            # Already punctuated
            ("Chào buổi sáng!", "!"),
            ("Bạn có khỏe không?", "?"),
            ("Mọi chuyện rồi sẽ ổn thôi.", "."),
            # Multi-punctuation
            ("Trời ơi!!", "!"),
            ("Thật không?!", "!"),
            ("Cái gì!?", "?"),
            # Trailing ellipsis
            ("Tôi không biết...", "."),
            ("Tôi không biết…", "."),
            ("Tôi không biết.....", "."),
            ("Tôi không biết . . . ", "."),
            # Trailing quotes
            ('"Chào bạn"', '"'),
            ('"Chào bạn."', '"'),
            ('"Chào bạn!"', '"'),
            ('"Chào bạn?"', '"'),
            ('"Chào bạn..."', '"'),
            ('"Chào bạn . . . "', '"'),
            ('“Đi thôi”', '”'),
            ('“Đi thôi.”', '”'),
            ('“Đi thôi!”', '”'),
            ('“Đi thôi?”', '”'),
            ('“Đi thôi...”', '”'),
            ('“Đi thôi . . . ”', '”'),
            # Single quotes
            ("'Chào bạn'", "'"),
            ("'Chào bạn.'", "'"),
            ("'Chào bạn...'", "'"),
        ]

        for inp, expected_terminal in test_cases:
            res = sanitize_complete_dialogue(inp)
            self.assertTrue(len(res) > 0, f"Unexpected empty result for: {inp}")
            last_char = res[-1]
            self.assertIn(
                last_char,
                ['.', '!', '?', '"', '”', "'"],
                f"Invalid terminal punctuation '{last_char}' in '{res}' for input: '{inp}'"
            )
            self.assertEqual(last_char, expected_terminal, f"Terminal mismatch for input '{inp}': got '{last_char}'")
            self.assertNotIn("...", res)
            self.assertNotIn("…", res)

    # =========================================================================
    # 3. NULL / NONE DIALOGUE & NARRATOR PANEL VALIDATION INTEGRATION
    # =========================================================================

    def test_validate_panels_adversarial_spaced_dots_and_none(self):
        """Test _validate_panels end-to-end with spaced dots and None values."""
        raw_panels = [
            {
                "panel_index": 1,
                "image_prompt": "classroom view",
                "dialogue_text": "Tôi . . . không biết.",
                "narrator_text": "A  .  .  .  B",
                "layout_type": "wide"
            },
            {
                "panel_index": 2,
                "image_prompt": "student desk",
                "dialogue_text": " . . . ",
                "narrator_text": "... . . . ...",
                "layout_type": "square"
            },
            {
                "panel_index": 3,
                "image_prompt": "hallway",
                "dialogue_text": None,
                "narrator_text": None,
                "layout_type": "square"
            },
            {
                "panel_index": 4,
                "image_prompt": "hallway evening",
                "dialogue_text": "None",
                "narrator_text": "null",
                "layout_type": "square"
            }
        ]

        validated = self.agent._validate_panels(raw_panels, {}, {})
        self.assertEqual(len(validated), 4)

        # Panel 1: Dialogue sanitized to "Tôi - không biết."
        self.assertEqual(validated[0]["dialogue_text"], "Tôi - không biết.")
        self.assertNotIn("...", validated[0]["dialogue_text"])

        # Panel 2: Both pure dots -> receives rich default sentence
        p2_dialogue = validated[1]["dialogue_text"]
        self.assertNotIn("...", p2_dialogue)
        self.assertNotIn("…", p2_dialogue)
        self.assertIn(p2_dialogue[-1], ['.', '!', '?'])
        self.assertGreater(len(p2_dialogue), 10)

        # Panel 3: Both None -> receives rich default sentence, NEVER "None."
        p3_dialogue = validated[2]["dialogue_text"]
        self.assertNotEqual(p3_dialogue, "None.")
        self.assertNotEqual(p3_dialogue, "None")
        self.assertNotIn("None", p3_dialogue)
        self.assertIn(p3_dialogue[-1], ['.', '!', '?'])

        # Panel 4: Literal strings "None" and "null" -> safely handled, NEVER "None."
        p4_dialogue = validated[3]["dialogue_text"]
        self.assertNotEqual(p4_dialogue, "None.")
        self.assertNotIn("null", p4_dialogue)
        self.assertIn(p4_dialogue[-1], ['.', '!', '?'])

        # Check ALL panels terminate in valid marks
        for p in validated:
            d = p["dialogue_text"]
            self.assertTrue(d.endswith(self.VALID_TERMINAL_MARKS))
            self.assertNotIn("...", d)

    # =========================================================================
    # 4. FALLBACK SCALING AND BEAT PACING VERIFICATION
    # =========================================================================

    def test_fallback_scaling_dialogue_and_narrative(self):
        """Verify fallback scales dynamically without 12-panel cap for both dialogues and narratives."""
        # 15 dialogue lines -> >= 15 panels
        dialogues = [f'Nhân vật {i + 1}: "Câu thoại thứ {i + 1} diễn ra."' for i in range(15)]
        panels_d = self.agent._create_structured_beat_fallback("\n".join(dialogues), {}, {})
        self.assertGreaterEqual(len(panels_d), 15)
        for p in panels_d:
            self.assertNotIn("...", p["dialogue_text"])
            self.assertTrue(p["dialogue_text"].endswith(self.VALID_TERMINAL_MARKS))

        # 45 narrative sentences -> >= 15 panels (grouped 3 sentences/beat)
        narratives = [f"Câu miêu tả số {i + 1} diễn biến đầy kịch tính." for i in range(45)]
        panels_n = self.agent._create_structured_beat_fallback("\n".join(narratives), {}, {})
        self.assertGreaterEqual(len(panels_n), 15)
        for p in panels_n:
            self.assertNotIn("...", p["dialogue_text"])
            self.assertTrue(p["dialogue_text"].endswith(self.VALID_TERMINAL_MARKS))

    # =========================================================================
    # 5. REGRESSION SUITE: MILESTONE 1 AND MILESTONE 2 PRESERVATION
    # =========================================================================

    def test_regression_copilot_prose_unwrap(self):
        """Milestone 1 unwrap_story_prose functions flawlessly."""
        raw = '{"action": "edit_story_direct", "action_params": {"updated_story_content": "Hôm nay tôi gặp An."}}'
        unwrapped = unwrap_story_prose(raw)
        self.assertEqual(unwrapped, "Hôm nay tôi gặp An.")

    def test_regression_cloudflare_deterministic_seed(self):
        """Milestone 2 deterministic seed derivation remains consistent."""
        s1 = get_deterministic_comic_seed(12345)
        s2 = get_deterministic_comic_seed(12345)
        self.assertEqual(s1, s2)
        self.assertTrue(100000 <= s1 <= 999999)


if __name__ == "__main__":
    unittest.main()
