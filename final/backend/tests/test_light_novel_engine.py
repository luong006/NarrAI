import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Ensure backend directory is in sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Set dummy keys if not present for agent initialization
os.environ.setdefault("GROQ_API_KEY", "gsk_test_dummy_key_for_unit_tests")
os.environ.setdefault("GROQ_API_KEY_COPILOT", "gsk_test_dummy_key_for_unit_tests")
os.environ.setdefault("GROQ_API_KEY_BIBLE", "gsk_test_dummy_key_for_unit_tests")

from agents.story_generator import (
    StoryGenerator,
    LIGHT_NOVEL_ENGINE_RULES,
    WRITING_RULES,
    MODERN_NOVEL_WRITING_RULES,
)
from agents.story_memory import StoryBible, StoryMemory
from agents.copilot_agent import CopilotAgent, DIRECT_EDIT_PROMPT
from agents.editor_agent import EditorAgent
from agents.qa_refiner import QARefiner


class TestLightNovelEngine(unittest.TestCase):
    """
    Test suite for Milestone 1: Modern Light Novel & Web Novel Engine.
    Verifies prompt reforms, 5-Beat Dramatic Architecture, StoryBible serialization,
    and agent persona alignment across all story generation subsystems.
    """

    # =========================================================================
    # 1. LIGHT NOVEL ENGINE RULES VERIFICATION
    # =========================================================================
    def test_rules_presence_and_aliases(self):
        """Verify LIGHT_NOVEL_ENGINE_RULES is defined and backward compatibility aliases exist."""
        self.assertIsNotNone(LIGHT_NOVEL_ENGINE_RULES)
        self.assertEqual(WRITING_RULES, LIGHT_NOVEL_ENGINE_RULES)
        self.assertEqual(MODERN_NOVEL_WRITING_RULES, LIGHT_NOVEL_ENGINE_RULES)

    def test_rules_tight_pov_content(self):
        """Verify Tight POV rule is present and enforces 1st or tight 3rd person."""
        self.assertIn("TIGHT POV", LIGHT_NOVEL_ENGINE_RULES)
        self.assertIn("Ngôi thứ nhất", LIGHT_NOVEL_ENGINE_RULES)
        self.assertIn("Ngôi thứ ba bám sát", LIGHT_NOVEL_ENGINE_RULES)

    def test_rules_rich_interior_monologue(self):
        """Verify Rich Interior Monologue rule is present."""
        self.assertIn("RICH INTERIOR MONOLOGUE", LIGHT_NOVEL_ENGINE_RULES)
        self.assertIn("độc thoại nội tâm", LIGHT_NOVEL_ENGINE_RULES.lower())
        self.assertIn("toan tính", LIGHT_NOVEL_ENGINE_RULES)
        self.assertIn("lo âu", LIGHT_NOVEL_ENGINE_RULES)
        self.assertIn("tự giễu cợt", LIGHT_NOVEL_ENGINE_RULES)

    def test_rules_sharp_youth_dialogue(self):
        """Verify Sharp Youth Dialogue rule prohibits translationese and enforces natural speech."""
        self.assertIn("SHARP YOUTH DIALOGUE", LIGHT_NOVEL_ENGINE_RULES)
        self.assertIn("giới trẻ", LIGHT_NOVEL_ENGINE_RULES)
        self.assertIn("subtext", LIGHT_NOVEL_ENGINE_RULES)
        self.assertIn("dịch thuật", LIGHT_NOVEL_ENGINE_RULES)
        self.assertIn("vi hành động", LIGHT_NOVEL_ENGINE_RULES)

    def test_rules_in_medias_res_hook_and_anti_cliche(self):
        """Verify In Medias Res Hook (0% weather rambling) and Anti-Cliché Banlist."""
        self.assertIn("IN MEDIAS RES", LIGHT_NOVEL_ENGINE_RULES)
        self.assertIn("0% tả thời tiết", LIGHT_NOVEL_ENGINE_RULES)
        self.assertIn("ANTI-CLICHÉ BANLIST", LIGHT_NOVEL_ENGINE_RULES)
        self.assertIn("vầng trăng vằng vặc", LIGHT_NOVEL_ENGINE_RULES)
        self.assertIn("tính từ trừu tượng", LIGHT_NOVEL_ENGINE_RULES)

    def test_rules_5_dramatic_beats_definition(self):
        """Verify 5 Dramatic Beats are explicitly outlined in the rules."""
        self.assertIn("5 NHỊP KỊCH TÍNH", LIGHT_NOVEL_ENGINE_RULES)
        self.assertIn("Beat 1: Hook (0-15%)", LIGHT_NOVEL_ENGINE_RULES)
        self.assertIn("Beat 2: Rising Friction", LIGHT_NOVEL_ENGINE_RULES)
        self.assertIn("Beat 3: Turning Point (40-70%)", LIGHT_NOVEL_ENGINE_RULES)
        self.assertIn("Beat 4: Visceral Climax (70-90%)", LIGHT_NOVEL_ENGINE_RULES)
        self.assertIn("Beat 5: Lingering Cliffhanger (90-100%)", LIGHT_NOVEL_ENGINE_RULES)

    # =========================================================================
    # 2. STORY GENERATOR PERSONA & 5 BEATS PROMPTS
    # =========================================================================
    @patch("llm.groq_client.Groq")
    def test_story_generator_persona_and_prompts(self, mock_groq):
        """Verify updated persona in _build_prompt and generate_chapter_stream."""
        gen = StoryGenerator()

        # Mock ontology extraction to return cleanly
        gen._extract_narrative_ontology = MagicMock(return_value="[MOCK_ONTOLOGY]")

        # Test _build_prompt
        messages, max_tokens = gen._build_prompt("Phác thảo truyện thanh xuân", "medium")
        sys_prompt = messages[0]["content"]

        self.assertIn("Bút vàng chuyên gia sáng tác Light Novel & Web Novel thịnh hành", sys_prompt)
        self.assertNotIn("đại tiểu thuyết gia xuất chúng tầm cỡ quốc tế", sys_prompt)
        self.assertIn("5 DRAMATIC BEATS", sys_prompt)
        self.assertIn("Lingering Cliffhanger", sys_prompt)

    @patch("llm.groq_client.Groq")
    def test_generate_chapter_stream_5_beats_enforcement(self, mock_groq):
        """Verify generate_chapter_stream enforces 5 dramatic beats and modern persona."""
        gen = StoryGenerator()
        gen.llm.chat_stream = MagicMock(return_value=iter(["Chương 1"]))

        bible = StoryBible(
            title="Thần Đạo Học Đường",
            genre="Học đường, Kỳ ảo",
            narrative_beats=[
                "Beat 1: Xung đột bùng nổ",
                "Beat 2: Trở ngại phát sinh",
                "Beat 3: Bước ngoặt lựa chọn",
                "Beat 4: Cao trào đối đầu",
                "Beat 5: Cliffhanger nghẹt thở",
            ]
        )
        memory = StoryMemory(story_bible=bible)
        memory.current_chapter = 0

        stream = gen.generate_chapter_stream(memory, user_instruction="Tập trung vào đối thoại")
        # Drain generator
        list(stream)

        # Inspect system prompt passed to chat_stream
        call_args = gen.llm.chat_stream.call_args
        messages = call_args[0][0]
        sys_prompt = messages[0]["content"]

        self.assertIn("Bút vàng chuyên gia sáng tác Light Novel & Web Novel thịnh hành", sys_prompt)
        self.assertNotIn("Ban la tac gia dang truc tiep viet mot chuong tieu thuyet", sys_prompt)
        self.assertIn("CẤU TRÚC 5 NHỊP KỊCH TÍNH (5 DRAMATIC BEATS)", sys_prompt)
        self.assertIn("Beat 1: Hook (0-15%)", sys_prompt)
        self.assertIn("Beat 2: Rising Friction", sys_prompt)
        self.assertIn("Beat 3: Turning Point (40-70%)", sys_prompt)
        self.assertIn("Beat 4: Visceral Climax (70-90%)", sys_prompt)
        self.assertIn("Beat 5: Lingering Cliffhanger (90-100%)", sys_prompt)

    @patch("llm.groq_client.Groq")
    def test_extract_narrative_ontology_prompt_structure(self, mock_groq):
        """Verify _extract_narrative_ontology prompt includes 5 dramatic beats request."""
        gen = StoryGenerator()
        captured_prompt = []

        def mock_chat(messages, **kwargs):
            captured_prompt.append(messages[1]["content"])
            return "[THỰC THỂ & NHÂN VẬT]: Minh\n[CẤU TRÚC 5 NHỊP KỊCH TÍNH (5 DRAMATIC BEATS)]:\n  + Beat 1: Hook"

        gen.llm.chat = mock_chat

        res = gen._extract_narrative_ontology("Một câu chuyện giả tưởng học đường kịch tính")
        self.assertTrue(len(captured_prompt) > 0)
        prompt_text = captured_prompt[0]

        self.assertIn("[CẤU TRÚC 5 NHỊP KỊCH TÍNH (5 DRAMATIC BEATS)]", prompt_text)
        self.assertIn("Beat 1: Hook", prompt_text)
        self.assertIn("Beat 2: Rising Friction", prompt_text)
        self.assertIn("Beat 3: Turning Point", prompt_text)
        self.assertIn("Beat 4: Visceral Climax", prompt_text)
        self.assertIn("Beat 5: Lingering Cliffhanger", prompt_text)
        self.assertIn("Beat 1: Hook", res)

    # =========================================================================
    # 3. STORYBIBLE NARRATIVE BEATS & SERIALIZATION
    # =========================================================================
    def test_story_bible_narrative_beats_default_and_custom(self):
        """Verify StoryBible stores narrative_beats with default empty list and custom values."""
        bible_empty = StoryBible()
        self.assertEqual(bible_empty.narrative_beats, [])

        beats = [
            "Beat 1: Hook nan giải",
            "Beat 2: Trở ngại dồn dập",
            "Beat 3: Biến cố bất ngờ",
            "Beat 4: Cao trào bùng nổ",
            "Beat 5: Cliffhanger treo",
        ]
        bible_custom = StoryBible(title="Vô Hạn Luân Hồi", narrative_beats=beats)
        self.assertEqual(bible_custom.narrative_beats, beats)

    def test_story_bible_serialization_roundtrip(self):
        """Verify StoryBible to_dict and from_dict preserve narrative_beats."""
        beats = ["Beat 1: Mở màn", "Beat 2: Rắc rối", "Beat 3: Ngã rẽ", "Beat 4: Trận chiến", "Beat 5: Nút thắt"]
        bible = StoryBible(
            title="Đại Lục Huyền Ảo",
            genre="Fantasy",
            world_setting="Thế giới ma thuật ngầm",
            narrative_beats=beats
        )

        data = bible.to_dict()
        self.assertIn("narrative_beats", data)
        self.assertEqual(data["narrative_beats"], beats)

        # Recreate via from_dict
        restored = StoryBible.from_dict(data)
        self.assertEqual(restored.title, "Đại Lục Huyền Ảo")
        self.assertEqual(restored.narrative_beats, beats)

    def test_story_bible_to_prompt_block(self):
        """Verify StoryBible to_prompt_block formats narrative beats cleanly."""
        beats = ["Beat 1: Hook tức thì", "Beat 5: Cliffhanger chấn động"]
        bible = StoryBible(title="Kiếm Khách Không Gian", narrative_beats=beats)
        block = bible.to_prompt_block()

        self.assertIn("=== STORY BIBLE ===", block)
        self.assertIn("Cau truc 5 nhip kich tinh (Narrative Beats):", block)
        self.assertIn("* Beat 1: Hook tức thì", block)
        self.assertIn("* Beat 5: Cliffhanger chấn động", block)

    def test_story_memory_persistence_with_narrative_beats(self):
        """Verify StoryMemory serializes and deserializes StoryBible with narrative beats."""
        beats = ["Nhịp 1: Bùng nổ", "Nhịp 5: Nút thắt"]
        bible = StoryBible(title="Ký Sự Thời Gian", narrative_beats=beats)
        memory = StoryMemory(story_bible=bible)
        memory.current_chapter = 2

        mem_dict = memory.to_dict()
        self.assertIn("narrative_beats", mem_dict["story_bible"])
        self.assertEqual(mem_dict["story_bible"]["narrative_beats"], beats)

        restored_mem = StoryMemory.from_dict(mem_dict)
        self.assertEqual(restored_mem.story_bible.title, "Ký Sự Thời Gian")
        self.assertEqual(restored_mem.story_bible.narrative_beats, beats)

    # =========================================================================
    # 4. COPILOT AGENT DIRECT_EDIT_PROMPT ALIGNMENT
    # =========================================================================
    def test_copilot_direct_edit_prompt_alignment(self):
        """Verify DIRECT_EDIT_PROMPT adheres strictly to Light Novel standards and prevents static prose."""
        prompt = DIRECT_EDIT_PROMPT
        self.assertIn("Light Novel & Web Novel", prompt)
        self.assertIn("Bút vàng Trưởng ban Biên tập", prompt)
        self.assertNotIn("Đại văn hào kiêm Biên tập viên hàng đầu", prompt)
        self.assertIn("In Medias Res Hook", prompt)
        self.assertIn("0% tả cảnh thời tiết", prompt)
        self.assertIn("Tight POV", prompt)
        self.assertIn("độc thoại nội tâm", prompt)
        self.assertIn("khẩu ngữ giới trẻ", prompt)
        self.assertIn("subtext", prompt)
        self.assertIn("Lingering Cliffhanger", prompt)
        self.assertIn("TUYỆT ĐỐI KHÔNG ĐỂ VĂN PHONG BỊ THỤT LÙI VỀ MIÊU TẢ TĨNH", prompt)

    # =========================================================================
    # 5. EDITOR AGENT PROMPT ALIGNMENT
    # =========================================================================
    @patch("llm.groq_client.Groq")
    def test_editor_agent_prompt_alignment(self, mock_groq):
        """Verify EditorAgent.edit_text prompt enforces Light Novel pacing, tight POV, and punchy dialogue."""
        editor = EditorAgent()
        captured_prompt = []

        def mock_chat(messages, **kwargs):
            captured_prompt.append(messages[0]["content"])
            return "Đoạn văn sau khi biên tập chuẩn Light Novel."

        editor.llm.chat = mock_chat

        res = editor.edit_text("Đoạn văn gốc miêu tả tĩnh.", "Làm cho kịch tính hơn")
        self.assertEqual(res, "Đoạn văn sau khi biên tập chuẩn Light Novel.")
        self.assertTrue(len(captured_prompt) > 0)
        sys_prompt = captured_prompt[0]

        self.assertIn("Light Novel & Web Novel", sys_prompt)
        self.assertIn("Tight POV", sys_prompt)
        self.assertIn("độc thoại nội tâm", sys_prompt)
        self.assertIn("punchy dialogue", sys_prompt)
        self.assertIn("Staccato Pacing", sys_prompt)
        self.assertIn("Show, don't tell", sys_prompt)
        self.assertNotIn("đại biên tập viên tiểu thuyết chuyên nghiệp và một nhà văn xuất sắc", sys_prompt)

    # =========================================================================
    # 6. QA REFINER 5-BEAT OUTLINE PROMPT
    # =========================================================================
    @patch("llm.groq_client.Groq")
    def test_qa_refiner_outline_5_beats_prompt(self, mock_groq):
        """Verify QARefiner.refine_prompt generates the 5-Beat Dramatic Architecture."""
        refiner = QARefiner()
        captured_prompt = []

        def mock_chat(messages, **kwargs):
            captured_prompt.append(messages[0]["content"])
            return "Bản Phác Thảo Cốt Truyện 5 Nhịp Kịch Tính"

        refiner.llm.chat = mock_chat

        history = [
            {"role": "user", "content": "Tôi muốn viết truyện về một thợ săn quái vật trong học đường hiện đại."},
            {"role": "assistant", "content": "Nghe rất hấp dẫn! Nhân vật chính có bí mật gì không?"},
            {"role": "user", "content": "Cậu ấy che giấu vết cắn nguyền rủa trên cánh tay phải."}
        ]

        res = refiner.refine_prompt(history)
        self.assertEqual(res, "Bản Phác Thảo Cốt Truyện 5 Nhịp Kịch Tính")
        self.assertTrue(len(captured_prompt) > 0)
        sys_prompt = captured_prompt[0]

        self.assertIn("Light Novel & Web Novel", sys_prompt)
        self.assertIn("CẤU TRÚC 5 NHỊP KỊCH TÍNH (5 DRAMATIC NARRATIVE BEATS)", sys_prompt)
        self.assertIn("Beat 1: Hook (0-15%)", sys_prompt)
        self.assertIn("Beat 2: Rising Friction / Complication (15-40%)", sys_prompt)
        self.assertIn("Beat 3: Turning Point (40-70%)", sys_prompt)
        self.assertIn("Beat 4: Visceral Climax (70-90%)", sys_prompt)
        self.assertIn("Beat 5: Lingering Cliffhanger (90-100%)", sys_prompt)
        self.assertNotIn("TIẾN TRÌNH CỐT TRUYỆN (Sườn logic nghiêm ngặt)", sys_prompt)

    # =========================================================================
    # 7. ADDITIONAL EDGE CASES & INTEGRATION CHECKS
    # =========================================================================
    def test_story_bible_none_handling(self):
        """Verify StoryBible safely normalizes None values for lists."""
        bible = StoryBible(characters=None, narrative_beats=None)
        self.assertEqual(bible.characters, [])
        self.assertEqual(bible.narrative_beats, [])

        # Test from_dict with None or malformed dict
        restored = StoryBible.from_dict({"characters": None, "narrative_beats": None})
        self.assertEqual(restored.characters, [])
        self.assertEqual(restored.narrative_beats, [])

        empty_obj = StoryBible.from_dict(None)
        self.assertIsInstance(empty_obj, StoryBible)
        self.assertEqual(empty_obj.title, "")

    def test_story_bible_empty_beats_prompt_block(self):
        """Verify StoryBible without narrative beats omits the beats block."""
        bible = StoryBible(title="Truyện Ngắn", narrative_beats=[])
        block = bible.to_prompt_block()
        self.assertNotIn("Cau truc 5 nhip kich tinh (Narrative Beats):", block)

    @patch("llm.groq_client.Groq")
    def test_story_generator_chapter_mode_prompt(self, mock_groq):
        """Verify _build_prompt with chapter_mode=True enforces 5 beats and cliffhanger."""
        gen = StoryGenerator()
        gen._extract_narrative_ontology = MagicMock(return_value="[ONTOLOGY]")
        messages, max_tokens = gen._build_prompt("Phác thảo", "long")
        sys_prompt = messages[0]["content"]

        self.assertIn("CHẾ ĐỘ VIẾT TỪNG CHƯƠNG", sys_prompt)
        self.assertIn("Triển khai trọn vẹn 5 nhịp kịch tính", sys_prompt)
        self.assertIn("Cliffhanger nghẹt thở", sys_prompt)

    @patch("llm.groq_client.Groq")
    def test_generate_ending_stream_prompt(self, mock_groq):
        """Verify generate_ending_stream uses Light Novel persona and rules."""
        gen = StoryGenerator()
        gen.llm.chat_stream = MagicMock(return_value=iter(["Đoạn kết"]))

        bible = StoryBible(title="Kết Thúc", narrative_beats=["Beat 1: Hook"])
        memory = StoryMemory(story_bible=bible)
        stream = gen.generate_ending_stream(memory)
        list(stream)

        call_args = gen.llm.chat_stream.call_args
        messages = call_args[0][0]
        sys_prompt = messages[0]["content"]

        self.assertIn("Bút vàng chuyên gia sáng tác Light Novel & Web Novel thịnh hành", sys_prompt)
        self.assertIn("Light Novel / Web Novel", sys_prompt)
        self.assertIn(LIGHT_NOVEL_ENGINE_RULES, sys_prompt)


if __name__ == "__main__":
    unittest.main()

