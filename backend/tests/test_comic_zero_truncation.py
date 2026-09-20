import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Ensure backend directory is in sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Set dummy key if not present for agent initialization
os.environ.setdefault("GROQ_API_KEY", "gsk_test_dummy_key_for_unit_tests")
os.environ.setdefault("GROQ_API_KEY_COMIC", "gsk_test_dummy_key_for_unit_tests")

from agents.comic_agent import (
    ComicDirectorAgent,
    BEAT_DIRECTOR_PROMPT,
    sanitize_complete_dialogue,
    decompose_story_beats
)
from main import extract_sentence_bounded_chunk


class TestComicZeroTruncation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with patch("llm.groq_client.Groq"):
            cls.agent = ComicDirectorAgent()

    # ======================================================================
    # 1. BEAT_DIRECTOR_PROMPT Schema Truncation Elimination
    # ======================================================================
    def test_beat_director_prompt_no_few_shot_dots_leak(self):
        """Verify BEAT_DIRECTOR_PROMPT does NOT contain 'dialogue_text': '...' or trailing 'shot of...'."""
        prompt = BEAT_DIRECTOR_PROMPT
        self.assertNotIn('"dialogue_text": "..."', prompt)
        self.assertNotIn('"image_prompt": "wide establishing shot of..."', prompt)
        # Verify complete Vietnamese sentence examples exist in prompt schema
        self.assertIn('"dialogue_text": "Hôm nay là một ngày thật đặc biệt đối với tôi."', prompt)
        self.assertIn('An: \\"Chào bạn, chúng ta cùng nhau cố gắng nhé!\\"', prompt.replace('\\"', '"'))

    def test_beat_director_prompt_explicit_prohibition_rules(self):
        """Verify prompt strictly prohibits ellipses '...', '…', and '.....'."""
        prompt = BEAT_DIRECTOR_PROMPT
        self.assertIn("TUYỆT ĐỐI CẤM SỬ DỤNG DẤU BA CHẤM", prompt)
        self.assertIn("...", prompt)
        self.assertIn("…", prompt)
        self.assertIn(".....", prompt)

    # ======================================================================
    # 2. Zero-Ellipsis Dialogue Sanitizer
    # ======================================================================
    def test_sanitize_handoff_spec_pattern(self):
        """Direct test from Explorer Survey 3 handoff requirement."""
        raw_text = 'Lý Tiêu: "Không thể nào..... tôi nhất định sẽ... trả thù..."'
        cleaned = sanitize_complete_dialogue(raw_text)
        expected = 'Lý Tiêu: "Không thể nào - tôi nhất định sẽ trả thù."'
        self.assertEqual(cleaned, expected)
        self.assertNotIn("...", cleaned)
        self.assertNotIn("…", cleaned)
        self.assertNotIn(".....", cleaned)

    def test_sanitize_trailing_ellipses_no_quotes(self):
        """Trailing dots at end of sentence must be cleaned to a single terminal period."""
        cases = [
            ("Câu chuyện vẫn tiếp diễn...", "Câu chuyện vẫn tiếp diễn."),
            ("Trời đã về chiều.....", "Trời đã về chiều."),
            ("Một ngày mới bắt đầu…", "Một ngày mới bắt đầu."),
            ("Chúng ta phải nhanh lên......", "Chúng ta phải nhanh lên."),
        ]
        for inp, expected in cases:
            res = sanitize_complete_dialogue(inp)
            self.assertEqual(res, expected, f"Failed for input: {inp}")
            self.assertNotIn("...", res)
            self.assertNotIn("…", res)

    def test_sanitize_trailing_ellipses_with_quotes(self):
        """Trailing dots before closing quotes must be placed inside or cleanly punctuated."""
        cases = [
            ('"Tôi hiểu rồi..."', '"Tôi hiểu rồi."'),
            ('“Tôi hiểu rồi…”', '“Tôi hiểu rồi.”'),
            ('An: "Cậu nói thật sao...?"', 'An: "Cậu nói thật sao?"'),
            ('An: "Nhanh lên nào...!"', 'An: "Nhanh lên nào!"'),
            ('Lý Tiêu: “Không thể nào.....”', 'Lý Tiêu: “Không thể nào.”'),
        ]
        for inp, expected in cases:
            res = sanitize_complete_dialogue(inp)
            self.assertEqual(res, expected, f"Failed for input: {inp}")
            self.assertNotIn("...", res)
            self.assertNotIn("…", res)

    def test_sanitize_mid_sentence_pause_conversion(self):
        """Mid-sentence hesitation or pauses converted smoothly without ellipsis."""
        # Speech stutter on repeated words
        res1 = sanitize_complete_dialogue("Tôi... tôi không biết.")
        self.assertEqual(res1, "Tôi - tôi không biết.")
        self.assertNotIn("...", res1)

        # Long dramatic pause
        res2 = sanitize_complete_dialogue("Đột nhiên..... một bóng đen xuất hiện.")
        self.assertEqual(res2, "Đột nhiên - một bóng đen xuất hiện.")
        self.assertNotIn("...", res2)

        # Mid-sentence pause between clauses
        res3 = sanitize_complete_dialogue("Chờ đã... cậu là ai?")
        self.assertEqual(res3, "Chờ đã - cậu là ai?")
        self.assertNotIn("...", res3)

    def test_sanitize_spaced_dots(self):
        """Spaced dots like 'Tôi . . . không biết.' must contain 0% ellipsis."""
        res = sanitize_complete_dialogue("Tôi . . . không biết.")
        self.assertNotIn("...", res)
        self.assertNotIn("…", res)
        self.assertEqual(res, "Tôi - không biết.")

    def test_sanitize_pure_dots_and_empty_strings(self):
        """Strings consisting only of dots/whitespace return empty string."""
        cases = ["...", ".....", "   …   ", "", None, "  ...  ", "......"]
        for inp in cases:
            res = sanitize_complete_dialogue(inp)
            self.assertEqual(res, "", f"Failed for input: {inp}")

    def test_sanitize_enforces_terminal_punctuation(self):
        """Strings without terminal punctuation must receive a terminal period."""
        res1 = sanitize_complete_dialogue("Hôm nay là một ngày thật đặc biệt đối với tôi")
        self.assertEqual(res1, "Hôm nay là một ngày thật đặc biệt đối với tôi.")

        res2 = sanitize_complete_dialogue('"Hôm nay là một ngày thật đặc biệt"')
        self.assertEqual(res2, '"Hôm nay là một ngày thật đặc biệt."')

        # Existing valid punctuation must be preserved
        res3 = sanitize_complete_dialogue("Chào bạn!")
        self.assertEqual(res3, "Chào bạn!")

        res4 = sanitize_complete_dialogue("Bạn là ai?")
        self.assertEqual(res4, "Bạn là ai?")

    # ======================================================================
    # 3. Sentence Boundaries Decomposition
    # ======================================================================
    def test_decompose_vietnamese_narrative_sentences(self):
        """Paragraph with multiple sentences decomposes cleanly at sentence boundaries."""
        story = (
            "Trời đã về chiều. Những tia nắng cuối ngày rớt trên mái trường im lìm.\n"
            "An quay sang nhìn tôi, ánh mắt chan chứa niềm hi vọng. "
            "Chúng tôi bước ra cổng trường khi chuông vừa điểm."
        )
        beats = decompose_story_beats(story)
        self.assertTrue(len(beats) >= 2)
        for b in beats:
            self.assertTrue(len(b) > 0)
            self.assertIn(b[-1], ['.', '!', '?', '"', '”'])
            self.assertNotIn("...", b)
            self.assertNotIn("…", b)

    def test_decompose_preserves_short_dialogues(self):
        """Short dialogues (< 15 chars) must NEVER be discarded."""
        story = (
            "An nhìn tôi.\n"
            '"Chào bạn!"\n'
            '"Đi thôi!"\n'
            "Tôi mỉm cười gật đầu."
        )
        beats = decompose_story_beats(story)
        # Both "Chào bạn!" (11 chars) and "Đi thôi!" (10 chars) must be present
        combined = " ".join(beats)
        self.assertIn("Chào bạn!", combined)
        self.assertIn("Đi thôi!", combined)

    def test_decompose_handles_em_dash_dialogues(self):
        """Vietnamese fiction em-dash dialogues are parsed into clean beats."""
        story = (
            "— Cậu có sao không? — An hỏi dồn.\n"
            "— Tôi không sao, cảm ơn cậu."
        )
        beats = decompose_story_beats(story)
        self.assertTrue(len(beats) >= 1)
        for b in beats:
            self.assertNotIn("...", b)
            self.assertNotIn("…", b)

    def test_decompose_zero_ellipsis_in_all_beats(self):
        """Input containing heavy ellipsis produces beats with 100% zero ellipsis."""
        story = (
            'Lý Tiêu hét lớn: "Không thể nào..... tôi nhất định sẽ... trả thù..."\n'
            "Bóng đêm dần bao phủ khắp căn phòng... Tiếng gió rít qua khe cửa..."
        )
        beats = decompose_story_beats(story)
        for b in beats:
            self.assertNotIn("...", b)
            self.assertNotIn("…", b)
            self.assertNotIn(".....", b)

    def test_decompose_empty_or_whitespace_story(self):
        """Empty or whitespace input returns empty list."""
        self.assertEqual(decompose_story_beats(""), [])
        self.assertEqual(decompose_story_beats("   \n\n  "), [])
        self.assertEqual(decompose_story_beats(None), [])

    # ======================================================================
    # 4. Fallback Generation Verification
    # ======================================================================
    def test_fallback_generation_zero_ellipsis(self):
        """Fallback panels must contain 0% ellipsis and complete sentences."""
        sample_story = (
            "Trời đã về chiều. Ánh nắng nhạt dần.\n"
            "An bước đến gần bàn học: \"Chào bạn, bài tập này khó quá!\"\n"
            "Tôi ngẩng đầu lên: \"Để mình giúp cậu nhé.\"\n"
            "Cả hai cùng nhau học tập thật chăm chỉ."
        )
        char_dna = {
            "An": {
                "gender": "female",
                "role": "lead",
                "dna": "17yo Vietnamese schoolgirl, crisp white shirt with navy ribbon tie",
                "aliases": ["An", "cô bé"]
            }
        }
        setting_dna = {
            "location_name": "Lớp học",
            "setting_anchor": "classroom with wooden desks by large windows"
        }

        panels = self.agent._create_structured_beat_fallback(sample_story, char_dna, setting_dna)
        self.assertTrue(len(panels) >= 3)
        for p in panels:
            dialogue = p.get("dialogue_text", "")
            prompt = p.get("image_prompt", "")
            self.assertNotIn("...", dialogue)
            self.assertNotIn("…", dialogue)
            self.assertNotIn(".....", dialogue)
            self.assertNotIn("...", prompt)
            self.assertIn(dialogue[-1], ['.', '!', '?', '"', '”'])

    def test_fallback_empty_story_creates_complete_panels(self):
        """Fallback with empty text generates complete panels with 0% dots."""
        panels = self.agent._create_structured_beat_fallback("", {}, {})
        self.assertEqual(len(panels), 2)
        for p in panels:
            dialogue = p.get("dialogue_text", "")
            self.assertNotIn("...", dialogue)
            self.assertNotIn("Câu chuyện bắt đầu...", dialogue)
            self.assertIn(dialogue[-1], ['.', '!', '?'])

    def test_fallback_no_twelve_panel_cutoff(self):
        """Fallback with 15 dialogue beats must generate at least 15 panels (no 12-panel cap)."""
        dialogues = [f'Nhân vật {i + 1}: "Câu thoại số {i + 1} diễn ra đầy kịch tính!"' for i in range(15)]
        long_story = "\n".join(dialogues)

        panels = self.agent._create_structured_beat_fallback(long_story, {}, {})
        self.assertGreaterEqual(len(panels), 15)

    def test_fallback_narrative_sentences_scaling(self):
        """Fallback with 45 narrative sentences must group into at least 15 panels."""
        narratives = [f"Câu văn miêu tả số {i + 1} diễn biến câu chuyện đầy hấp dẫn và kịch tính." for i in range(45)]
        long_story = "\n".join(narratives)

        panels = self.agent._create_structured_beat_fallback(long_story, {}, {})
        self.assertGreaterEqual(len(panels), 15)

    # ======================================================================
    # 5. Sentence-Bounded Chunking in backend/main.py
    # ======================================================================
    def test_extract_sentence_bounded_chunk_short_text(self):
        """Text under target_size returns full text and full length."""
        short_text = "Hôm nay là một ngày nắng đẹp. Tôi đến trường cùng An."
        chunk, offset = extract_sentence_bounded_chunk(short_text, target_size=5000, max_limit=6500)
        self.assertEqual(chunk, short_text)
        self.assertEqual(offset, len(short_text))

    def test_extract_sentence_bounded_chunk_long_story_breaks_at_sentence(self):
        """7000+ character story must break strictly at sentence boundary near target_size."""
        # Build 7500-char story with distinct numbered sentences
        sentences = [
            f"Đây là câu văn số {i:03d} miêu tả khung cảnh một buổi chiều êm đềm bên bờ sông rực rỡ nắng vàng."
            for i in range(80)
        ]
        full_text = " ".join(sentences)
        self.assertGreater(len(full_text), 6500)

        chunk, offset = extract_sentence_bounded_chunk(full_text, target_size=5000, max_limit=6500)
        
        # Must be within reasonable bounds
        self.assertTrue(4000 <= len(chunk) <= 6500)
        # Chunk MUST end with terminal punctuation
        self.assertIn(chunk[-1], ['.', '!', '?', '"', '”'])
        # Chunk must end with a full sentence, never an amputated word
        self.assertTrue(chunk.endswith("nắng vàng."))

        # The remaining text must start cleanly with a new sentence
        remaining = full_text[offset:].strip()
        self.assertTrue(remaining.startswith("Đây là câu văn số"))

    def test_extract_sentence_bounded_chunk_dialogue_quotes(self):
        """Text with dialogue quotes breaks cleanly after the closing quote."""
        dialogues = [
            f'Nhân vật {i:02d} cất tiếng nói rõ ràng: "Chúng ta nhất định sẽ thành công trong kế hoạch này!"'
            for i in range(70)
        ]
        full_text = "\n\n".join(dialogues)
        self.assertGreater(len(full_text), 6000)

        chunk, offset = extract_sentence_bounded_chunk(full_text, target_size=5000, max_limit=6500)
        self.assertIn(chunk[-1], ['"', '”', '.'])
        self.assertNotIn("...", chunk)

    # ======================================================================
    # 6. Panel Validation Smart DNA & Complete Sentences
    # ======================================================================
    def test_validate_panels_sanitizes_llm_truncation(self):
        """Raw script items with LLM dots are sanitized to complete sentences."""
        raw_script = [
            {
                "panel_index": 1,
                "image_prompt": "wide establishing shot of classroom",
                "dialogue_text": "Không thể nào.....",
                "layout_type": "wide"
            },
            {
                "panel_index": 2,
                "image_prompt": "close up of student talking",
                "dialogue_text": "...",
                "layout_type": "square"
            }
        ]
        validated = self.agent._validate_panels(raw_script, {}, {})
        self.assertEqual(len(validated), 2)
        
        # Panel 1: "Không thể nào....." -> "Không thể nào."
        self.assertEqual(validated[0]["dialogue_text"], "Không thể nào.")
        self.assertNotIn("...", validated[0]["dialogue_text"])

        # Panel 2: "..." was pure dots -> replaced with complete default sentence
        self.assertTrue(len(validated[1]["dialogue_text"]) > 5)
        self.assertNotIn("...", validated[1]["dialogue_text"])
        self.assertIn(validated[1]["dialogue_text"][-1], ['.', '!', '?'])

    def test_validate_panels_none_dialogue_fallback(self):
        """None/null dialogue_text must fall back to rich default sentence, NEVER 'None.'."""
        raw_script = [
            {
                "panel_index": 1,
                "image_prompt": "wide establishing shot of classroom",
                "dialogue_text": None,
                "layout_type": "wide"
            }
        ]
        validated = self.agent._validate_panels(raw_script, {}, {})
        self.assertEqual(len(validated), 1)
        dialogue = validated[0]["dialogue_text"]
        self.assertNotEqual(dialogue, "None.")
        self.assertNotEqual(dialogue, "None")
        self.assertNotIn("None", dialogue)
        self.assertGreater(len(dialogue), 10)
        self.assertIn(dialogue[-1], ['.', '!', '?'])


if __name__ == "__main__":
    unittest.main()
