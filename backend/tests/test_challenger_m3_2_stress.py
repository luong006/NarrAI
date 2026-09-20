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
from agents.copilot_agent import unwrap_story_prose
from services.cloudflare_ai import get_deterministic_comic_seed
from main import extract_sentence_bounded_chunk


class TestChallengerM32Stress(unittest.TestCase):
    """
    Independent Adversarial Challenge & Stress-Test Harness for Milestone 3 (Requirement R3).
    Executed by challenger_m3_2.
    """
    @classmethod
    def setUpClass(cls):
        with patch("llm.groq_client.Groq"):
            cls.agent = ComicDirectorAgent()

    # =========================================================================
    # 1. FALLBACK GENERATION STRESS & SCALE (> 20 BEATS, ZERO ELLIPSIS, NO CAP)
    # =========================================================================

    def test_fallback_scales_beyond_twenty_beats_dialogue(self):
        """Verify fallback scales dynamically to 25+ beats with dialogue turns without 12-panel cap."""
        dialogues = [
            f'Nhân vật {i + 1}: "Phân cảnh đối thoại số {i + 1} diễn ra đầy kịch tính!"'
            for i in range(25)
        ]
        story_text = "\n".join(dialogues)
        char_dna = {
            "Lý Tiêu": {
                "dna": "Lý Tiêu (18yo swordsman, jet-black hair, high-collar black robe)",
                "gender": "male",
                "role": "lead",
                "aliases": ["Lý Tiêu", "chàng trai"]
            }
        }
        setting_dna = {
            "location_name": "Rừng bí ẩn",
            "setting_anchor": "ancient foggy bamboo forest with towering trees"
        }

        panels = self.agent._create_structured_beat_fallback(story_text, char_dna, setting_dna)
        self.assertGreaterEqual(len(panels), 25, "Fallback failed to generate at least 25 panels for 25 dialogue turns!")
        
        # Verify sequential panel indexing from 1 to N
        for idx, panel in enumerate(panels):
            self.assertEqual(panel["panel_index"], idx + 1)
            dialogue = panel.get("dialogue_text", "")
            prompt = panel.get("image_prompt", "")
            # Verify ZERO ellipsis in dialogue and prompt
            self.assertNotIn("...", dialogue)
            self.assertNotIn("…", dialogue)
            self.assertNotIn(".....", dialogue)
            self.assertNotIn("...", prompt)
            self.assertIn(dialogue[-1], ['.', '!', '?', '"', '”'])

    def test_fallback_narrative_beat_grouping_ratio(self):
        """
        Adversarial Analysis of Narrative Beat Grouping:
        decompose_story_beats groups up to 3 non-dialogue sentences into a single beat.
        Therefore, 75 narrative sentences yield 25 beats and 25 panels.
        Conversely, 15 narrative sentences yield only 5 beats, causing
        test_comic_zero_truncation.py:244 to fail if asserted for 15 panels.
        """
        narrative_75 = "\n".join([
            f"Câu văn miêu tả phân đoạn số {i + 1} về sự thay đổi của thời tiết và cảnh vật."
            for i in range(75)
        ])
        panels = self.agent._create_structured_beat_fallback(narrative_75, {}, {})
        self.assertEqual(len(panels), 25, "75 narrative sentences must group into 25 panels (3 sentences/beat)")

    def test_fallback_scales_to_fifty_beats(self):
        """Stress-test fallback scaling to 50 distinct dialogue beats."""
        dialogues = [
            f'Nhân vật {i:02d}: "Đây là câu thoại thứ {i:02d} trong chuỗi đối thoại căng thẳng!"'
            for i in range(50)
        ]
        story_text = "\n".join(dialogues)
        panels = self.agent._create_structured_beat_fallback(story_text, {}, {})
        self.assertGreaterEqual(len(panels), 50, "Fallback failed to scale to 50 dialogue beats!")
        for panel in panels:
            dialogue = panel["dialogue_text"]
            self.assertNotIn("...", dialogue)
            self.assertNotIn("…", dialogue)
            self.assertIn(dialogue[-1], ['.', '!', '?', '"', '”'])

    def test_fallback_empty_text_never_uses_cau_chuyen_bat_dau_dots(self):
        """Fallback on empty or whitespace story text must NOT contain 'Câu chuyện bắt đầu...'."""
        empty_inputs = ["", "   ", "\n\n\t  \n"]
        for empty_text in empty_inputs:
            panels = self.agent._create_structured_beat_fallback(empty_text, {}, {})
            self.assertEqual(len(panels), 2)
            for p in panels:
                d = p["dialogue_text"]
                self.assertNotIn("...", d)
                self.assertNotIn("Câu chuyện bắt đầu...", d)
                self.assertIn(d[-1], ['.', '!', '?'])
            # Verify exact complete default sentences
            self.assertEqual(panels[0]["dialogue_text"], "Câu chuyện bắt đầu với những diễn biến đầy bất ngờ.")
            self.assertEqual(panels[1]["dialogue_text"], "Chúng ta nhất định phải kiên trì bước tiếp!")

    # =========================================================================
    # 2. PANEL VALIDATION: SANITIZATION & SMART DNA / SETTING ANCHOR PRESERVATION
    # =========================================================================

    def test_validate_panels_sanitizes_both_dialogue_and_narrator(self):
        """_validate_panels must sanitize both dialogue_text and narrator_text with zero ellipsis."""
        raw_panels = [
            {
                "panel_index": 1,
                "image_prompt": "establishing wide shot",
                "dialogue_text": "Không thể tin được.....",
                "narrator_text": "Màn đêm dần buông xuống...",
                "layout_type": "wide"
            },
            {
                "panel_index": 2,
                "image_prompt": "close up shot",
                "dialogue_text": "",  # Empty dialogue -> should fall back to narrator_text
                "narrator_text": "Tiếng bước chân vang vọng khắp hành lang...",
                "layout_type": "square"
            },
            {
                "panel_index": 3,
                "image_prompt": "medium shot",
                "dialogue_text": "...",  # Pure dots -> should be cleaned and receive rich default
                "narrator_text": "...",  # Pure dots -> should also be cleaned
                "layout_type": "square"
            }
        ]
        validated = self.agent._validate_panels(raw_panels, {}, {})
        self.assertEqual(len(validated), 3)

        # Panel 1: Dialogue sanitized to complete sentence
        self.assertEqual(validated[0]["dialogue_text"], "Không thể tin được.")
        self.assertNotIn("...", validated[0]["dialogue_text"])

        # Panel 2: Empty dialogue falls back to sanitized narrator_text
        self.assertEqual(validated[1]["dialogue_text"], "Tiếng bước chân vang vọng khắp hành lang.")
        self.assertNotIn("...", validated[1]["dialogue_text"])

        # Panel 3: Pure dots replaced with rich default sentence
        self.assertEqual(validated[2]["dialogue_text"], "Diễn biến tiếp tục trong không gian đầy cảm xúc.")
        self.assertNotIn("...", validated[2]["dialogue_text"])

    def test_validate_panels_preserves_character_dna_and_setting_anchors(self):
        """_validate_panels must maintain Smart Character DNA injection and Setting Anchors from M2."""
        dna_map = {
            "An": {
                "gender": "female",
                "role": "lead",
                "aliases": ["An", "cô bé", "nữ sinh"],
                "dna": "17yo Vietnamese schoolgirl, jet-black hair with blunt bangs, crisp white shirt with dark navy ribbon tie"
            },
            "Minh": {
                "gender": "male",
                "role": "desk mate",
                "aliases": ["Minh", "anh bạn cùng bàn", "cậu bạn"],
                "dna": "17yo Vietnamese schoolboy, messy textured dark hair, white button-up shirt"
            }
        }
        setting_dna = {
            "location_name": "Phòng học 12A",
            "setting_anchor": "sunny high-school classroom with wooden desks and large glass windows"
        }

        panels = [
            {
                "panel_index": 1,
                "image_prompt": "wide establishing shot of classroom",
                "dialogue_text": "Hôm nay là buổi học đầu tiên của năm học mới.",
                "layout_type": "wide"
            },
            {
                "panel_index": 2,
                "image_prompt": "medium shot of desk",
                "dialogue_text": 'Cô bé mỉm cười quay sang: "Chào bạn, mình cùng cố gắng nhé!"',
                "layout_type": "square"
            },
            {
                "panel_index": 3,
                "image_prompt": "medium shot of two students studying together",
                "dialogue_text": 'An và anh bạn cùng bàn cùng nhau mở sách vở.',
                "layout_type": "square"
            }
        ]

        validated = self.agent._validate_panels(panels, character_dna_map=dna_map, setting_dna=setting_dna)
        self.assertEqual(len(validated), 3)

        # Panel 1: Wide layout blends setting anchor
        self.assertIn("sunny high-school classroom with wooden desks and large glass windows", validated[0]["image_prompt"])

        # Panel 2: Dialogue has pronoun "Cô bé" -> Injects An's DNA
        self.assertIn("17yo Vietnamese schoolgirl, jet-black hair with blunt bangs", validated[1]["image_prompt"])

        # Panel 3: Mentions BOTH "An" and "anh bạn cùng bàn" -> Injects BOTH An's and Minh's DNA (no early break!)
        self.assertIn("17yo Vietnamese schoolgirl", validated[2]["image_prompt"])
        self.assertIn("17yo Vietnamese schoolboy", validated[2]["image_prompt"])

    def test_validate_panels_an_false_positive_prevention(self):
        """English indefinite article 'an' or Vietnamese compound words must not falsely inject character 'An'."""
        dna_map = {
            "An": {
                "gender": "female",
                "role": "lead",
                "aliases": ["An"],
                "dna": "17yo schoolgirl An"
            }
        }
        panels = [
            {
                "panel_index": 1,
                "image_prompt": "an establishing shot of an abandoned street",
                "dialogue_text": "Mọi người mong muốn một cuộc sống bình an và an toàn.",
                "layout_type": "wide"
            }
        ]
        validated = self.agent._validate_panels(panels, character_dna_map=dna_map)
        # Should NOT inject "17yo schoolgirl An" because 'an establishing' is English article and 'bình an' / 'an toàn' are compound words
        self.assertNotIn("17yo schoolgirl An", validated[0]["image_prompt"])

    # =========================================================================
    # 3. SENTENCE BOUNDARY DECOMPOSITION EDGE CASES & SHORT DIALOGUE PRESERVATION
    # =========================================================================

    def test_decompose_preserves_short_dialogues_under_15_chars(self):
        """Verify dialogues like 'A!', 'Ừ!', 'Đi thôi!' are 100% preserved."""
        story = (
            '— "A!" — An giật mình.\n'
            '— "Ừ!" — Minh gật đầu.\n'
            '— "Đi thôi!"\n'
            '— "Chào bạn!"'
        )
        beats = decompose_story_beats(story)
        combined = " ".join(beats)
        self.assertIn("A!", combined)
        self.assertIn("Ừ!", combined)
        self.assertIn("Đi thôi!", combined)
        self.assertIn("Chào bạn!", combined)

    def test_decompose_complex_vietnamese_punctuation_and_em_dashes(self):
        """Verify Vietnamese fiction em-dashes and exclamation/question marks decompose cleanly."""
        story = (
            "— Cậu có chắc chắn về điều đó không?! — An gặng hỏi.\n"
            "— Tôi hoàn toàn chắc chắn — Minh đáp với ánh mắt kiên định.\n"
            "— Vậy thì chúng ta bắt đầu thôi!"
        )
        beats = decompose_story_beats(story)
        self.assertGreaterEqual(len(beats), 3)
        for b in beats:
            self.assertNotIn("...", b)
            self.assertNotIn("…", b)
            self.assertIn(b[-1], ['.', '!', '?', '"', '”'])

    # =========================================================================
    # 4. CHUNKING BOUNDARY & WORD PRESERVATION (extract_sentence_bounded_chunk)
    # =========================================================================

    def test_chunking_long_story_over_8000_chars(self):
        """Long narrative exceeding 8000 chars cuts strictly at sentence boundary without word slicing."""
        sentences = [
            f"Đoạn văn số {i:03d} tường thuật lại diễn biến của cuộc phiêu lưu kì thú trên thảo nguyên bao la."
            for i in range(90)
        ]
        story_text = " ".join(sentences)
        self.assertGreater(len(story_text), 8000)

        chunk, offset = extract_sentence_bounded_chunk(story_text, target_size=5000, max_limit=6500)
        self.assertTrue(4000 <= len(chunk) <= 6500)
        self.assertIn(chunk[-1], ['.', '!', '?', '"', '”'])
        self.assertTrue(chunk.endswith("bao la."))

        # Verify next slice begins cleanly with next sentence
        remaining = story_text[offset:]
        self.assertTrue(remaining.startswith("Đoạn văn số"))
        self.assertFalse(remaining.startswith(" "))

    def test_chunking_unpunctuated_prose_word_boundary_safety(self):
        """Run-on story with zero punctuation falls back to word boundary without amputating words."""
        words = [f"từkhoá{i:04d}" for i in range(1200)]
        story_text = " ".join(words)
        self.assertGreater(len(story_text), 8000)

        chunk, offset = extract_sentence_bounded_chunk(story_text, target_size=5000, max_limit=6500)
        last_word = chunk.split()[-1]
        self.assertTrue(last_word.startswith("từkhoá"), f"Word was amputated: {last_word}")

        remaining = story_text[offset:]
        first_rem_word = remaining.split()[0]
        self.assertTrue(first_rem_word.startswith("từkhoá"), f"Remaining word was amputated: {first_rem_word}")

    # =========================================================================
    # 5. BACKWARDS COMPATIBILITY (MILESTONE 1 UNWRAP & MILESTONE 2 SEED)
    # =========================================================================

    def test_backwards_compatibility_copilot_unwrap_prose(self):
        """Verify Milestone 1 unwrap_story_prose functions flawlessly with nested JSON and markdown codeblocks."""
        nested_json_payload = '```json\n{"action": "edit_story_direct", "action_params": {"updated_story_content": "Đoạn văn mới sạch sẽ không có JSON."}}\n```'
        unwrapped = unwrap_story_prose(nested_json_payload)
        self.assertEqual(unwrapped, "Đoạn văn mới sạch sẽ không có JSON.")
        self.assertNotIn("{", unwrapped)
        self.assertNotIn("updated_story_content", unwrapped)

    def test_backwards_compatibility_cloudflare_deterministic_seed(self):
        """Verify Milestone 2 get_deterministic_comic_seed produces valid, deterministic seeds in range [100000, 999999]."""
        for sid in [1, 2, 42, 999, 100000]:
            seed1 = get_deterministic_comic_seed(sid)
            seed2 = get_deterministic_comic_seed(sid)
            self.assertEqual(seed1, seed2, f"Seed is non-deterministic for story_id={sid}")
            self.assertTrue(100000 <= seed1 <= 999999, f"Seed {seed1} out of bounds for story_id={sid}")

        # None handling
        seed_none = get_deterministic_comic_seed(None)
        self.assertEqual(seed_none, get_deterministic_comic_seed(1))


if __name__ == "__main__":
    unittest.main()
