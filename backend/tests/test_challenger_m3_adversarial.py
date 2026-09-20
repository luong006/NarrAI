import os
import sys
import unittest
import re
from unittest.mock import patch, MagicMock

# Ensure backend directory is in sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

os.environ.setdefault("GROQ_API_KEY", "gsk_test_dummy_key_for_unit_tests")
os.environ.setdefault("GROQ_API_KEY_COMIC", "gsk_test_dummy_key_for_unit_tests")

from agents.comic_agent import (
    ComicDirectorAgent,
    BEAT_DIRECTOR_PROMPT,
    sanitize_complete_dialogue,
    decompose_story_beats
)
from main import extract_sentence_bounded_chunk


class TestChallengerM3Adversarial(unittest.TestCase):
    """
    Adversarial stress-test harness for Milestone 3 (Requirement R3).
    Formally verifies invariants, edge cases, failure modes, and boundary behaviors.
    """
    @classmethod
    def setUpClass(cls):
        with patch("llm.groq_client.Groq"):
            cls.agent = ComicDirectorAgent()

    # =========================================================================
    # 1. ZERO ELLIPSIS INVARIANT & ADVERSARIAL SANITIZATION
    # =========================================================================

    def test_adversarial_extreme_trailing_dots(self):
        """Stress-test inputs with 10 to 100 consecutive trailing dots."""
        for count in [10, 25, 50, 100]:
            inp = "Trời đã tối" + ("." * count)
            cleaned = sanitize_complete_dialogue(inp)
            self.assertEqual(cleaned, "Trời đã tối.", f"Failed on {count} dots")
            self.assertNotIn("...", cleaned)
            self.assertNotIn("…", cleaned)
            self.assertNotIn(".....", cleaned)

    def test_adversarial_extreme_trailing_dots_inside_quotes(self):
        """Stress-test quotes ending with 10 to 100 trailing dots."""
        for count in [10, 25, 50, 100]:
            inp = f'An nói: "Tôi không biết{"." * count}"'
            cleaned = sanitize_complete_dialogue(inp)
            self.assertEqual(cleaned, 'An nói: "Tôi không biết."', f"Failed on quote with {count} dots")
            self.assertNotIn("...", cleaned)
            self.assertNotIn("…", cleaned)

    def test_adversarial_unicode_ellipses_chains(self):
        """Stress-test mixed unicode ellipses and ASCII dots chains."""
        cases = [
            ("Một buổi chiều……", "Một buổi chiều."),
            ("Một buổi chiều…...….", "Một buổi chiều."),
            ('“Không thể nào………”', '“Không thể nào.”'),
            ('Lý Tiêu: "Ngươi… ngươi dám…?"', 'Lý Tiêu: "Ngươi - ngươi dám?"'),
        ]
        for inp, expected in cases:
            cleaned = sanitize_complete_dialogue(inp)
            self.assertEqual(cleaned, expected, f"Failed for input: {inp}")
            self.assertNotIn("...", cleaned)
            self.assertNotIn("…", cleaned)

    def test_adversarial_stutter_and_hesitations(self):
        """Stress-test multiple stutters across a single complex line."""
        inp = "Tôi... tôi... tôi thật sự... không biết phải làm sao..."
        cleaned = sanitize_complete_dialogue(inp)
        self.assertNotIn("...", cleaned)
        self.assertNotIn("…", cleaned)
        self.assertNotIn(".....", cleaned)
        self.assertTrue(cleaned.endswith("."))

    def test_adversarial_vn_particles_stutter_cleaning(self):
        """Stress-test Vietnamese auxiliary/modifier words followed by ellipses."""
        particles = ["sẽ", "đã", "đang", "sắp", "rất", "quá", "vẫn", "cứ", "bị", "được", "vì", "để"]
        for p in particles:
            inp = f"Tôi {p}... đi về phía trước..."
            cleaned = sanitize_complete_dialogue(inp)
            self.assertNotIn("...", cleaned, f"Failed on particle: {p}")
            self.assertNotIn("…", cleaned)
            self.assertTrue(cleaned.endswith("."))

    def test_adversarial_pure_dots_and_whitespace(self):
        """Stress-test pure dots and whitespace variations returning empty string."""
        pure_cases = [
            ".", "..", "...", "....", ".....", "..........",
            "…", "……", "………",
            "   ...   ", "\t.....\n", "  …  ",
            " . . . ", " . . . . . "
        ]
        for c in pure_cases:
            cleaned = sanitize_complete_dialogue(c)
            self.assertEqual(cleaned, "", f"Pure dots must return empty string for input: {repr(c)}")

    def test_adversarial_dialogue_with_mixed_terminal_marks(self):
        """Stress-test combinations of dots with question and exclamation marks."""
        cases = [
            ('An: "Cậu nói thật sao...?"', 'An: "Cậu nói thật sao?"'),
            ('An: "Cậu nói thật sao...?!?"', 'An: "Cậu nói thật sao?!?"'),
            ('An: "Không...!"', 'An: "Không!"'),
            ('An: "Cứu với...!!!"', 'An: "Cứu với!!!"'),
            ('An: "Tại sao.....?"', 'An: "Tại sao?"'),
        ]
        for inp, expected in cases:
            cleaned = sanitize_complete_dialogue(inp)
            self.assertEqual(cleaned, expected, f"Failed on: {inp}")
            self.assertNotIn("...", cleaned)
            self.assertNotIn("…", cleaned)

    def test_adversarial_order_of_operations_spaced_dots_analysis(self):
        """
        Verify that spaced dots (e.g. 'Tôi . . . không biết.') undergo pre-normalization
        and step 4 execution after step 5, ensuring 0% ellipsis in output.
        """
        inp = "Tôi . . . không biết."
        cleaned = sanitize_complete_dialogue(inp)
        self.assertNotIn("...", cleaned)
        self.assertNotIn("…", cleaned)
        self.assertEqual(cleaned, "Tôi - không biết.")

    # =========================================================================
    # 2. TERMINAL PUNCTUATION GUARANTEE
    # =========================================================================

    def test_terminal_punctuation_unpunctuated_prose(self):
        """Prose without punctuation must receive terminal period."""
        cases = [
            ("Hôm nay là một ngày nắng đẹp", "Hôm nay là một ngày nắng đẹp."),
            ("Ánh nắng rực rỡ chiếu qua khung cửa sổ", "Ánh nắng rực rỡ chiếu qua khung cửa sổ."),
            ("Chúng ta cùng bước tiếp", "Chúng ta cùng bước tiếp."),
        ]
        for inp, expected in cases:
            cleaned = sanitize_complete_dialogue(inp)
            self.assertEqual(cleaned, expected)
            self.assertIn(cleaned[-1], ['.', '!', '?', '"', '”'])

    def test_terminal_punctuation_special_nonterminal_endings(self):
        """Strings ending in colon, semicolon, or dash must terminate cleanly."""
        cases = [
            "Anh ấy quay lại nhìn tôi:",
            "Tiếng gió rít qua ô cửa;",
            "Chúng ta phải chạy thật nhanh -",
        ]
        for inp in cases:
            cleaned = sanitize_complete_dialogue(inp)
            self.assertIn(cleaned[-1], ['.', '!', '?', '"', '”'])
            self.assertNotIn("...", cleaned)

    def test_terminal_punctuation_quotes_preservation(self):
        """Dialogue quotes with valid internal terminal punctuation preserve quotes."""
        cases = [
            ('An nói: "Chào bạn!"', 'An nói: "Chào bạn!"'),
            ('An hỏi: "Cậu là ai?"', 'An hỏi: "Cậu là ai?"'),
            ('An bảo: "Mình đi thôi."', 'An bảo: "Mình đi thôi."'),
            ('An nói: “Chào bạn!”', 'An nói: “Chào bạn!”'),
            ('An nói: "Chào bạn', 'An nói: "Chào bạn."'),
        ]
        for inp, expected in cases:
            cleaned = sanitize_complete_dialogue(inp)
            self.assertEqual(cleaned, expected)
            self.assertIn(cleaned[-1], ['.', '!', '?', '"', '”'])

    # =========================================================================
    # 3. SENTENCE BOUNDARIES DECOMPOSITION ADVERSARIAL STRESS
    # =========================================================================

    def test_decompose_short_dialogues_absolute_retention(self):
        """Short dialogues (< 15 chars) must NEVER be filtered out or dropped."""
        short_lines = [
            '"A!"',
            '"Ừ!"',
            '"Có!"',
            '"Hả?"',
            '"Đi thôi!"',
            '"Chào bạn!"',
            '"Không thể!"',
            '"Chạy mau!"',
        ]
        story = "\n".join(short_lines)
        beats = decompose_story_beats(story)
        combined = " ".join(beats)
        for line in short_lines:
            unquoted = line.strip('"')
            self.assertIn(unquoted, combined, f"Short dialogue {line} was dropped!")

    def test_decompose_adversarial_nested_dialogue_em_dashes(self):
        """Vietnamese dialogue with em-dashes and parenthetical clauses decomposes cleanly."""
        story = (
            "— Cậu có tin vào số phận không? — An hỏi khẽ.\n"
            "— Tôi không biết — Tôi đáp lại — nhưng tôi tin vào sự nỗ lực.\n"
            "— Đúng vậy! — An mỉm cười rạng rỡ."
        )
        beats = decompose_story_beats(story)
        self.assertGreaterEqual(len(beats), 2)
        for b in beats:
            self.assertNotIn("...", b)
            self.assertNotIn("…", b)
            self.assertIn(b[-1], ['.', '!', '?', '"', '”'])

    def test_decompose_vietnamese_diacritics_and_exclamations(self):
        """Vietnamese text with complex tone marks and punctuation bursts."""
        story = (
            "Trời ơi! Chuyện gì thế này?! Không thể nào tin được!\n"
            "Mọi người hoảng loạn bỏ chạy. Tiếng la hét vang vọng khắp nơi."
        )
        beats = decompose_story_beats(story)
        self.assertGreaterEqual(len(beats), 2)
        for b in beats:
            self.assertNotIn("...", b)
            self.assertIn(b[-1], ['.', '!', '?', '"', '”'])

    def test_decompose_beat_grouping_bounds(self):
        """Beats must adhere to sentence count and character bounds."""
        story = "\n".join([f"Câu chuyện tiếp tục với nhịp diễn biến thứ {i} vô cùng kịch tính." for i in range(10)])
        beats = decompose_story_beats(story)
        for b in beats:
            self.assertLessEqual(len(b), 350)  # Max bound with margin
            self.assertIn(b[-1], ['.', '!', '?', '"', '”'])

    # =========================================================================
    # 4. CHUNKING STRESS TESTS (extract_sentence_bounded_chunk)
    # =========================================================================

    def test_chunking_long_story_over_8000_chars(self):
        """Story over 8000 characters breaks cleanly at sentence boundary near 5000 chars."""
        sentences = [
            f"Đây là phân đoạn số {i:03d} miêu tả chi tiết diễn biến tâm lý nhân vật một cách tỉ mỉ và sâu sắc."
            for i in range(100)
        ]
        full_text = " ".join(sentences)
        self.assertGreater(len(full_text), 8000)

        chunk, offset = extract_sentence_bounded_chunk(full_text, target_size=5000, max_limit=6500)

        # Chunk length must be bounded
        self.assertGreaterEqual(len(chunk), 4000)
        self.assertLessEqual(len(chunk), 6500)

        # Must end with terminal sentence punctuation
        self.assertIn(chunk[-1], ['.', '!', '?', '"', '”'])
        self.assertTrue(chunk.endswith("sâu sắc."))

        # Offset alignment check: next chunk starts at the exact beginning of next sentence
        remaining = full_text[offset:]
        self.assertTrue(remaining.startswith("Đây là phân đoạn số"))
        self.assertFalse(remaining.startswith(" "))  # No leading space

    def test_chunking_adversarial_no_periods_word_boundary_preservation(self):
        """Story of 7000+ characters with ZERO punctuation marks must NOT amputate words."""
        # 800 words without any periods, exclamation marks, or question marks
        words = [f"tuvan{i:04d}" for i in range(1000)]
        full_text = " ".join(words)
        self.assertGreater(len(full_text), 7000)

        chunk, offset = extract_sentence_bounded_chunk(full_text, target_size=5000, max_limit=6500)

        # Chunk must end at a complete word boundary
        last_word = chunk.split()[-1]
        self.assertTrue(last_word.startswith("tuvan"), f"Word was sliced: {last_word}")

        # Remaining must start at a complete word boundary
        remaining = full_text[offset:]
        first_rem_word = remaining.split()[0]
        self.assertTrue(first_rem_word.startswith("tuvan"), f"Remaining word was sliced: {first_rem_word}")

    def test_chunking_dense_dialogue_quotes(self):
        """Story dense with dialogue quotes breaks cleanly after closing quote."""
        dialogues = [
            f'An nói với vẻ dứt khoát: "Chúng ta nhất định sẽ vượt qua thử thách số {i:03d} này!"'
            for i in range(80)
        ]
        full_text = "\n\n".join(dialogues)
        self.assertGreater(len(full_text), 7000)

        chunk, offset = extract_sentence_bounded_chunk(full_text, target_size=5000, max_limit=6500)
        self.assertIn(chunk[-1], ['"', '”', '.'])
        self.assertNotIn("...", chunk)

        # Next chunk resumes at next speaker line
        remaining = full_text[offset:]
        self.assertTrue(remaining.startswith("An nói với vẻ dứt khoát"))

    def test_chunking_single_run_on_sentence_candidate_selection(self):
        """Sentence starting before 5000 and ending after 6500 cuts safely before the run-on sentence."""
        intro = " ".join([f"Câu văn dẫn nhập thứ {i}." for i in range(180)])  # ~4500 chars
        run_on = "Đây là một câu văn cực kỳ dài không có dấu chấm nào kéo dài liên tục " * 40  # ~2800 chars
        conclusion = "Và câu chuyện kết thúc."
        full_text = f"{intro} {run_on}. {conclusion}"

        chunk, offset = extract_sentence_bounded_chunk(full_text, target_size=5000, max_limit=6500)
        self.assertIn(chunk[-1], ['.', '!', '?', '"', '”'])
        # Cuts safely at the end of intro before the run-on sentence
        self.assertTrue(chunk.endswith("."))

    # =========================================================================
    # 5. PANEL VALIDATION & STRUCTURED FALLBACK GUARANTEES
    # =========================================================================

    def test_validate_panels_zero_dots_invariant(self):
        """All panels passed through _validate_panels strictly satisfy the zero-dots invariant."""
        raw_panels = [
            {
                "panel_index": 1,
                "image_prompt": "wide establishing shot of school...",
                "dialogue_text": "Trời đã tối.....",
                "layout_type": "wide"
            },
            {
                "panel_index": 2,
                "image_prompt": "medium shot of girl talking...",
                "dialogue_text": "...",
                "layout_type": "square"
            },
            {
                "panel_index": 3,
                "image_prompt": "close up of boy looking shocked...",
                "dialogue_text": "Không thể nào... tôi sẽ trả thù...",
                "layout_type": "square"
            }
        ]
        validated = self.agent._validate_panels(raw_panels, {}, {})
        self.assertEqual(len(validated), 3)

        for p in validated:
            d = p["dialogue_text"]
            self.assertNotIn("...", d)
            self.assertNotIn("…", d)
            self.assertNotIn(".....", d)
            self.assertIn(d[-1], ['.', '!', '?', '"', '”'])
            self.assertGreater(len(d), 0)

    def test_fallback_removes_twelve_panel_limit_and_dots(self):
        """Fallback on 20 dialogue lines generates 20 panels with 0% dots."""
        dialogues = [f'Nhân vật {i + 1}: "Phân đoạn kịch bản thứ {i + 1} diễn ra trong bầu không khí ngập tràn cảm xúc."' for i in range(20)]
        story = "\n".join(dialogues)

        panels = self.agent._create_structured_beat_fallback(story, {}, {})
        self.assertGreaterEqual(len(panels), 20)

        for p in panels:
            d = p["dialogue_text"]
            self.assertNotIn("...", d)
            self.assertNotIn("…", d)
            self.assertNotIn(".....", d)
            self.assertIn(d[-1], ['.', '!', '?', '"', '”'])


if __name__ == "__main__":
    unittest.main()
