import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Ensure backend directory is in sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Set dummy keys if not present for agent initialization
os.environ.setdefault("GROQ_API_KEY", "gsk_adversarial_test_dummy_key")
os.environ.setdefault("GROQ_API_KEY_COPILOT", "gsk_adversarial_test_dummy_key")
os.environ.setdefault("GROQ_API_KEY_BIBLE", "gsk_adversarial_test_dummy_key")

from agents.story_memory import StoryBible, StoryMemory
from agents.story_generator import (
    StoryGenerator,
    LIGHT_NOVEL_ENGINE_RULES,
    WRITING_RULES,
    MODERN_NOVEL_WRITING_RULES,
)
from agents.copilot_agent import CopilotAgent, DIRECT_EDIT_PROMPT
from agents.editor_agent import EditorAgent
from agents.qa_refiner import QARefiner


class TestStoryBibleAdversarialSerialization(unittest.TestCase):
    """
    Adversarial stress testing of StoryBible and StoryMemory serialization.
    Explores empty, missing, None, and corrupted narrative_beats payloads.
    """

    def test_empty_narrative_beats(self):
        """Verify StoryBible with empty list behaves cleanly."""
        bible = StoryBible(title="Thế Giới Ảo", narrative_beats=[])
        self.assertEqual(bible.narrative_beats, [])

        # to_prompt_block must omit the beats block and NOT contain "None"
        block = bible.to_prompt_block()
        self.assertNotIn("Cau truc 5 nhip kich tinh", block)
        self.assertNotIn("None", block)

        # to_dict must serialize as []
        d = bible.to_dict()
        self.assertEqual(d["narrative_beats"], [])

        # from_dict must restore []
        restored = StoryBible.from_dict(d)
        self.assertEqual(restored.narrative_beats, [])

    def test_missing_narrative_beats_key_in_dict(self):
        """Verify deserialization when 'narrative_beats' key is missing from dictionary."""
        d = {
            "title": "Truyện Không Beats",
            "genre": "Web Novel",
            "world_setting": "Học đường",
            "characters": [{"name": "Lâm", "role": "Nam chính"}],
        }
        bible = StoryBible.from_dict(d)
        self.assertIsInstance(bible.narrative_beats, list)
        self.assertEqual(bible.narrative_beats, [])

        block = bible.to_prompt_block()
        self.assertNotIn("Cau truc 5 nhip kich tinh", block)
        self.assertNotIn("None", block)

    def test_none_narrative_beats_normalization(self):
        """Verify None is normalized to [] in constructor and from_dict."""
        bible1 = StoryBible(narrative_beats=None)
        self.assertEqual(bible1.narrative_beats, [])

        bible2 = StoryBible.from_dict({"narrative_beats": None})
        self.assertEqual(bible2.narrative_beats, [])

    def test_corrupted_type_narrative_beats_int(self):
        """
        Stress test: What happens if narrative_beats in dict is an integer (e.g. from bad API input)?
        Documents failure mode: int is truthy, but not iterable.
        """
        d = {"title": "Lỗi Type Int", "narrative_beats": 42}
        bible = StoryBible.from_dict(d)
        # Note: d.get("narrative_beats") or [] returns 42 because 42 is truthy!
        if isinstance(bible.narrative_beats, int):
            # Calling list(bible.narrative_beats) or to_prompt_block() will raise TypeError
            with self.assertRaises(TypeError):
                bible.to_dict()
            with self.assertRaises(TypeError):
                bible.to_prompt_block()

    def test_corrupted_type_narrative_beats_string(self):
        """
        Stress test: What happens if narrative_beats in dict is a single string instead of a list?
        Documents character-iteration behavior if type is not strictly enforced.
        """
        d = {"title": "Lỗi Type String", "narrative_beats": "Beat 1: Hook"}
        bible = StoryBible.from_dict(d)
        if isinstance(bible.narrative_beats, str):
            block = bible.to_prompt_block()
            # If it's a string, 'for b in self.narrative_beats' iterates over chars: 'B', 'e', 'a', 't'
            self.assertIn("Cau truc 5 nhip kich tinh", block)

    def test_narrative_beats_containing_none_elements(self):
        """
        Stress test: What happens when narrative_beats is a list containing None or blank strings?
        Check if 'None' string literal is injected into the prompt block.
        """
        bible = StoryBible(
            title="Truyện Khuyết Điểm",
            narrative_beats=[None, "Beat 1: Hook bùng nổ", None, ""]
        )
        block = bible.to_prompt_block()
        # Vulnerability check: Does to_prompt_block() inject 'None' when an item is None?
        contains_literal_none = "* None" in block
        # Document empirical observation
        self.assertTrue(
            contains_literal_none,
            "Documented finding: StoryBible.to_prompt_block() injects '* None' if narrative_beats contains None elements."
        )

    def test_single_beat_prompt_block(self):
        """Verify prompt construction with exactly 1 beat."""
        bible = StoryBible(
            title="Đơn Nhịp",
            narrative_beats=["Beat 1: Hook giật gân mở màn"]
        )
        block = bible.to_prompt_block()
        self.assertIn("Cau truc 5 nhip kich tinh (Narrative Beats):", block)
        self.assertIn("* Beat 1: Hook giật gân mở màn", block)
        self.assertNotIn("None", block)

    def test_more_than_five_beats_prompt_block(self):
        """Verify prompt construction with >5 beats (e.g. 8 beats)."""
        beats = [f"Beat {i}: Diễn biến kịch tính {i}" for i in range(1, 9)]
        bible = StoryBible(title="Đa Nhịp", narrative_beats=beats)
        block = bible.to_prompt_block()
        self.assertIn("Cau truc 5 nhip kich tinh (Narrative Beats):", block)
        for b in beats:
            self.assertIn(f"* {b}", block)
        self.assertNotIn("None", block)

    def test_story_memory_roundtrip_resilience(self):
        """Verify StoryMemory serializes and deserializes StoryBible across edge cases."""
        # 1. Empty beats
        mem1 = StoryMemory(story_bible=StoryBible(title="Mem 1", narrative_beats=[]))
        mem1_dict = mem1.to_dict()
        restored1 = StoryMemory.from_dict(mem1_dict)
        self.assertEqual(restored1.story_bible.narrative_beats, [])

        # 2. 7 beats
        seven_beats = [f"Nhịp {i}" for i in range(1, 8)]
        mem2 = StoryMemory(story_bible=StoryBible(title="Mem 2", narrative_beats=seven_beats))
        mem2_dict = mem2.to_dict()
        restored2 = StoryMemory.from_dict(mem2_dict)
        self.assertEqual(restored2.story_bible.narrative_beats, seven_beats)


class TestNarrativeOntologyAdversarialParsing(unittest.TestCase):
    """
    Adversarial stress testing of narrative ontology extraction and parsing in StoryGenerator.
    Explores LLM output omitting beats, malformed text, or failures.
    """

    @patch("llm.groq_client.Groq")
    def test_ontology_llm_omits_trailing_beats(self, mock_groq):
        """
        Stress test: When the LLM extracts ontology but cuts off or omits beats 3, 4, 5.
        Verifies that _extract_narrative_ontology returns the output without crashing,
        and documents downstream behavior.
        """
        gen = StoryGenerator()
        partial_llm_output = (
            "[THỰC THỂ & NHÂN VẬT]: Lâm (POV), Vy\n"
            "[QUAN HỆ & ĐỘNG CƠ]: Bạn học, cạnh tranh bí mật\n"
            "[QUY TẮC THẾ GIỚI & BỐI CẢNH (WORLD AXIOMS)]: Học viện Ma thuật hiện đại\n"
            "[CHUỖI NHÂN QUẢ CHÍNH]: Mất điểm -> Bị phạt -> Gặp gỡ\n"
            "[CẤU TRÚC 5 NHỊP KỊCH TÍNH (5 DRAMATIC BEATS)]:\n"
            "  + Beat 1: Hook (0-15%): Xung đột bùng nổ\n"
            "  + Beat 2: Rising Friction (15-40%): Trở ngại leo thang"
        )
        gen.llm.chat = MagicMock(return_value=partial_llm_output)

        res = gen._extract_narrative_ontology("Phác thảo truyện ngắn")
        self.assertIn("Beat 1: Hook", res)
        self.assertIn("Beat 2: Rising Friction", res)
        # Document: Missing beats are NOT backfilled by _extract_narrative_ontology
        self.assertNotIn("Beat 3: Turning Point", res)
        self.assertNotIn("Beat 4: Visceral Climax", res)
        self.assertNotIn("Beat 5: Lingering Cliffhanger", res)

    @patch("llm.groq_client.Groq")
    def test_ontology_llm_omits_entire_beats_section(self, mock_groq):
        """
        Stress test: When the LLM omits the entire [CẤU TRÚC 5 NHỊP KỊCH TÍNH] section.
        """
        gen = StoryGenerator()
        no_beats_output = (
            "[THỰC THỂ & NHÂN VẬT]: Lâm, Vy\n"
            "[QUAN HỆ & ĐỘNG CƠ]: Cạnh tranh\n"
            "[QUY TẮC THẾ GIỚI & BỐI CẢNH (WORLD AXIOMS)]: Hiện đại\n"
            "[CHUỖI NHÂN QUẢ CHÍNH]: A -> B"
        )
        gen.llm.chat = MagicMock(return_value=no_beats_output)

        res = gen._extract_narrative_ontology("Phác thảo")
        self.assertEqual(res, no_beats_output)
        self.assertNotIn("[CẤU TRÚC 5 NHỊP KỊCH TÍNH", res)

    @patch("llm.groq_client.Groq")
    def test_ontology_llm_empty_or_whitespace_triggers_complete_fallback(self, mock_groq):
        """
        Verify that when LLM returns empty or whitespace, the fallback provides all 5 beats.
        """
        gen = StoryGenerator()
        gen.llm.chat = MagicMock(return_value="   \n\t  ")

        res = gen._extract_narrative_ontology("Phác thảo giả lập")
        self.assertIn("[CẤU TRÚC 5 NHỊP KỊCH TÍNH (5 DRAMATIC BEATS)]", res)
        self.assertIn("Beat 1: Hook", res)
        self.assertIn("Beat 2: Rising Friction", res)
        self.assertIn("Beat 3: Turning Point", res)
        self.assertIn("Beat 4: Visceral Climax", res)
        self.assertIn("Beat 5: Lingering Cliffhanger", res)

    @patch("llm.groq_client.Groq")
    def test_ontology_llm_exception_triggers_complete_fallback(self, mock_groq):
        """
        Verify that when LLM call throws an exception, the fallback provides all 5 beats.
        """
        gen = StoryGenerator()
        gen.llm.chat = MagicMock(side_effect=RuntimeError("Groq API Timeout"))

        res = gen._extract_narrative_ontology("Phác thảo giả lập")
        self.assertIn("[CẤU TRÚC 5 NHỊP KỊCH TÍNH (5 DRAMATIC BEATS)]", res)
        self.assertIn("Beat 1: Hook", res)
        self.assertIn("Beat 2: Rising Friction", res)
        self.assertIn("Beat 3: Turning Point", res)
        self.assertIn("Beat 4: Visceral Climax", res)
        self.assertIn("Beat 5: Lingering Cliffhanger", res)

    def test_ontology_none_refined_prompt_pre_try_vulnerability(self):
        """
        Stress test: Calling _extract_narrative_ontology(None).
        Prompt string slicing 'refined_prompt[:3000]' happens before 'try:' block,
        which raises TypeError if refined_prompt is None.
        """
        gen = StoryGenerator()
        with self.assertRaises(TypeError):
            gen._extract_narrative_ontology(None)


class TestPromptConstructionNoNoneOrFailure(unittest.TestCase):
    """
    Verifies that prompt construction does not inject None or fail
    when narrative_beats has 0, 1, or >5 items across all generation workflows.
    """

    @patch("llm.groq_client.Groq")
    def test_build_prompt_with_different_lengths_no_none(self, mock_groq):
        """Verify _build_prompt does not inject None across short, medium, and long lengths."""
        gen = StoryGenerator()
        gen._extract_narrative_ontology = MagicMock(return_value="[ONTOLOGY_BLOCK_5_BEATS]")

        for length in ["short", "medium", "long", "unknown_fallback"]:
            messages, max_tokens = gen._build_prompt("Bản thảo kiểm tra", length)
            sys_msg = messages[0]["content"]
            user_msg = messages[1]["content"]

            self.assertNotIn("None", sys_msg)
            self.assertNotIn("None", user_msg)
            self.assertIn("Bút vàng chuyên gia sáng tác Light Novel & Web Novel thịnh hành", sys_msg)
            self.assertIn("5 DRAMATIC BEATS", sys_msg)

    @patch("llm.groq_client.Groq")
    def test_generate_chapter_stream_zero_beats_no_none(self, mock_groq):
        """Verify generate_chapter_stream with 0 narrative beats does not inject None."""
        gen = StoryGenerator()
        gen.llm.chat_stream = MagicMock(return_value=iter(["Prose"]))

        bible = StoryBible(title="Không Beat", narrative_beats=[])
        memory = StoryMemory(story_bible=bible)
        memory.current_chapter = 0

        stream = gen.generate_chapter_stream(memory, user_instruction="")
        list(stream)

        call_args = gen.llm.chat_stream.call_args
        messages = call_args[0][0]
        sys_msg = messages[0]["content"]
        user_msg = messages[1]["content"]

        self.assertNotIn("None", sys_msg)
        self.assertNotIn("None", user_msg)
        self.assertIn("Bút vàng chuyên gia sáng tác Light Novel & Web Novel thịnh hành", sys_msg)
        self.assertIn("Beat 1: Hook (0-15%)", sys_msg)
        self.assertIn("Beat 5: Lingering Cliffhanger (90-100%)", sys_msg)

    @patch("llm.groq_client.Groq")
    def test_generate_chapter_stream_one_beat_no_none(self, mock_groq):
        """Verify generate_chapter_stream with 1 narrative beat does not inject None."""
        gen = StoryGenerator()
        gen.llm.chat_stream = MagicMock(return_value=iter(["Prose"]))

        bible = StoryBible(title="Một Beat", narrative_beats=["Beat 1: Khởi đầu nan giải"])
        memory = StoryMemory(story_bible=bible)
        memory.current_chapter = 1

        stream = gen.generate_chapter_stream(memory, user_instruction="Chú ý nhịp điệu")
        list(stream)

        call_args = gen.llm.chat_stream.call_args
        messages = call_args[0][0]
        sys_msg = messages[0]["content"]
        user_msg = messages[1]["content"]

        self.assertNotIn("None", sys_msg)
        self.assertNotIn("None", user_msg)
        self.assertIn("* Beat 1: Khởi đầu nan giải", sys_msg)

    @patch("llm.groq_client.Groq")
    def test_generate_chapter_stream_eight_beats_no_none(self, mock_groq):
        """Verify generate_chapter_stream with >5 narrative beats (e.g. 8 beats) formats cleanly without None."""
        gen = StoryGenerator()
        gen.llm.chat_stream = MagicMock(return_value=iter(["Prose"]))

        beats = [f"Beat {i}: Tình tiết số {i}" for i in range(1, 9)]
        bible = StoryBible(title="Tám Beat", narrative_beats=beats)
        memory = StoryMemory(story_bible=bible)
        memory.current_chapter = 3

        stream = gen.generate_chapter_stream(memory)
        list(stream)

        call_args = gen.llm.chat_stream.call_args
        messages = call_args[0][0]
        sys_msg = messages[0]["content"]

        self.assertNotIn("None", sys_msg)
        for b in beats:
            self.assertIn(f"* {b}", sys_msg)

    @patch("llm.groq_client.Groq")
    def test_generate_ending_stream_with_zero_one_and_many_beats(self, mock_groq):
        """Verify generate_ending_stream across 0, 1, and >5 beats."""
        gen = StoryGenerator()
        gen.llm.chat_stream = MagicMock(return_value=iter(["Ending"]))

        for beat_list in [[], ["Beat 1: Độc nhất"], [f"Beat {i}" for i in range(1, 10)]]:
            bible = StoryBible(title="Kết Truyện", narrative_beats=beat_list)
            memory = StoryMemory(story_bible=bible)
            stream = gen.generate_ending_stream(memory)
            list(stream)

            call_args = gen.llm.chat_stream.call_args
            messages = call_args[0][0]
            sys_msg = messages[0]["content"]
            user_msg = messages[1]["content"]

            self.assertNotIn("None", sys_msg)
            self.assertNotIn("None", user_msg)
            self.assertIn("Bút vàng chuyên gia sáng tác Light Novel & Web Novel thịnh hành", sys_msg)


class TestAbsenceOfNineteenthCenturyPersona(unittest.TestCase):
    """
    Verifies total absence of 19th-century European/Russian realism persona keywords
    ('đại tiểu thuyết gia', 'Đại văn hào', 'đại biên tập viên', 'tầm cỡ quốc tế')
    across story_generator.py, copilot_agent.py, editor_agent.py, and qa_refiner.py.
    """

    def _read_module_source(self, filename: str) -> str:
        filepath = os.path.join(backend_dir, "agents", filename)
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()

    def test_absence_in_story_generator(self):
        content = self._read_module_source("story_generator.py").lower()
        self.assertNotIn("đại tiểu thuyết gia", content)
        self.assertNotIn("đại văn hào", content)
        self.assertNotIn("đại biên tập viên", content)
        self.assertNotIn("tầm cỡ quốc tế", content)

    def test_absence_in_copilot_agent(self):
        content = self._read_module_source("copilot_agent.py").lower()
        self.assertNotIn("đại tiểu thuyết gia", content)
        self.assertNotIn("đại văn hào", content)
        self.assertNotIn("đại biên tập viên", content)
        self.assertNotIn("tầm cỡ quốc tế", content)

    def test_absence_in_editor_agent(self):
        content = self._read_module_source("editor_agent.py").lower()
        self.assertNotIn("đại tiểu thuyết gia", content)
        self.assertNotIn("đại văn hào", content)
        self.assertNotIn("đại biên tập viên", content)
        self.assertNotIn("tầm cỡ quốc tế", content)

    def test_absence_in_qa_refiner(self):
        content = self._read_module_source("qa_refiner.py").lower()
        self.assertNotIn("đại tiểu thuyết gia", content)
        self.assertNotIn("đại văn hào", content)
        self.assertNotIn("đại biên tập viên", content)
        self.assertNotIn("tầm cỡ quốc tế", content)

    def test_modern_persona_active_in_all_agents(self):
        """Verify modern Light Novel / Web Novel persona is explicitly present in all agents."""
        story_gen_src = self._read_module_source("story_generator.py")
        self.assertIn("Bút vàng chuyên gia sáng tác Light Novel & Web Novel thịnh hành", story_gen_src)

        copilot_src = self._read_module_source("copilot_agent.py")
        self.assertIn("Bút vàng Trưởng ban Biên tập Light Novel & Web Novel thịnh hành", copilot_src)

        editor_src = self._read_module_source("editor_agent.py")
        self.assertIn("Biên tập viên Light Novel & Web Novel sắc sảo kiêm Bút vàng thịnh hành", editor_src)

        qa_src = self._read_module_source("qa_refiner.py")
        self.assertIn("chuyên gia biên soạn kịch bản Light Novel & Web Novel chuyên nghiệp", qa_src)


if __name__ == "__main__":
    unittest.main()
