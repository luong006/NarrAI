"""
NarrAI Round 6 Test Suite: Copilot Manuscript Surgery & Slicer Optimization
Location: backend/tests/test_round6_copilot_surgery.py

Authoritative Specifications:
- ORIGINAL_REQUEST.md (§ R1. Copilot Biên Tập Bản Thảo Linh Hoạt Hoàn Toàn, 2026-09-30T16:30:48Z)
- PROJECT.md (§ Features 1-5, Milestone 1 & Milestone 5)
- Survey Report 1 (§ 2. Investigation of R1: Copilot Manuscript Surgery)

Coverage:
1. Chapter targeting: "sửa Chương 2" or "sửa Chương 3" correctly slices and edits only that chapter.
2. `instruction` parameter utilization in `SemanticChunkSlicer`.
3. `selectedText` & `cursorPosition` targeting from frontend.
4. Path B non-truncation: long story (>5000 chars) edited via Path B does NOT lose preceding text.
5. Intermediate heading preservation: multi-chapter edit preserves `## Chương 1`, `## Chương 2`, `## Chương 3` in correct relative order.
"""

import os
import sys
import re
import json
import unittest
import inspect
from unittest.mock import MagicMock, patch

# Ensure backend root is on sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from agents.copilot_agent import (
    CopilotAgent,
    SemanticChunkSlicer,
    HeadingPreservationEngine,
    SurgeryTarget,
    ChunkSlice,
    classify_surgery_intent,
    unwrap_story_prose
)


class TestRound6CopilotChapterTargeting(unittest.TestCase):
    """
    Tests for Requirement R1.2 & R1.3:
    Targeting specific chapters ("sửa Chương 2", "sửa Chương 3") in multi-chapter manuscripts,
    and active utilization of the `instruction` parameter in SemanticChunkSlicer.
    """

    def setUp(self):
        self.sample_novel = (
            "**Bạch Đằng Phong Vân**\n\n"
            "## Chương 1: Gió Nổi Cửa Biển\n"
            "Tháng Chạp năm Đinh Hợi, gió mùa đông bắc rít liên hồi trên sông Bạch Đằng.\n"
            "Trần Hưng Đạo đứng trên mạn thuyền, ánh mắt trầm tĩnh nhìn con nước thủy triều lên xuống.\n\n"
            "## Chương 2: Bày Binh Bố Trận\n"
            "Hàng ngàn cây cọc lim vót nhọn bịt sắt được bí mật đóng xuống lòng sông Bạch Đằng.\n"
            "Yết Kiêu và Dã Tượng đích thân chỉ huy các toán thủy binh luồn sâu trong rừng đước.\n\n"
            "## Chương 3: Huyết Chiến Bến Vạn Kiếp\n"
            "Chiến thuyền giặc Ô Mã Nhi nối đuôi nhau lọt vào trận địa mai phục.\n"
            "Hiệu lệnh nổi lên, tên lửa như sao sa, quân Đại Việt dũng mãnh phản công toàn diện.\n\n"
            "## Chương 4: Khải Hoàn Đại Việt\n"
            "Bắt sống tướng giặc Ô Mã Nhi và Phàn Tiếp. Toàn bộ thủy quân Nguyên Mông bị tiêu diệt hoàn toàn.\n"
            "Giang sơn gấm vóc từ đây sạch bóng quân thù, ngàn năm thái bình thịnh trị."
        )

    def test_chapter_targeting_chapter_2(self):
        """
        Verify that instruction 'sửa Chương 2' slices exactly Chapter 2:
        - prefix contains Chapter 1
        - window_to_edit contains Chapter 2
        - suffix contains Chapter 3 and Chapter 4
        """
        instruction = "Hãy sửa Chương 2: thêm cảnh Yết Kiêu lặn xuống sông kiểm tra các cọc gỗ lim"
        
        # Test slice_manuscript with instruction
        slicer_result = SemanticChunkSlicer.slice_manuscript(
            story=self.sample_novel,
            target=SurgeryTarget.GENERAL_SURGERY,
            instruction=instruction
        )

        self.assertIsInstance(slicer_result, ChunkSlice)
        # Chapter 1 must be strictly in prefix
        self.assertIn("## Chương 1: Gió Nổi Cửa Biển", slicer_result.prefix)
        self.assertIn("Trần Hưng Đạo đứng trên mạn thuyền", slicer_result.prefix)

        # Chapter 2 must be in window_to_edit
        self.assertIn("## Chương 2: Bày Binh Bố Trận", slicer_result.window_to_edit)
        self.assertIn("Hàng ngàn cây cọc lim", slicer_result.window_to_edit)

        # Chapter 3 & 4 must NOT be in window_to_edit
        self.assertNotIn("## Chương 3: Huyết Chiến", slicer_result.window_to_edit)
        self.assertNotIn("## Chương 4: Khải Hoàn", slicer_result.window_to_edit)

        # Chapter 3 & 4 must be in suffix
        self.assertIn("## Chương 3: Huyết Chiến Bến Vạn Kiếp", slicer_result.suffix)
        self.assertIn("## Chương 4: Khải Hoàn Đại Việt", slicer_result.suffix)

    def test_chapter_targeting_chapter_3(self):
        """
        Verify that instruction 'viết lại Chương 3 cho kịch tính hơn' slices exactly Chapter 3:
        - prefix contains Chapter 1 & 2
        - window_to_edit contains Chapter 3
        - suffix contains Chapter 4
        """
        instruction = "viết lại Chương 3 cho kịch tính hơn, đẩy cao trào trận đánh"
        
        slicer_result = SemanticChunkSlicer.slice_manuscript(
            story=self.sample_novel,
            target=SurgeryTarget.GENERAL_SURGERY,
            instruction=instruction
        )

        # Chapter 1 and Chapter 2 in prefix
        self.assertIn("## Chương 1: Gió Nổi Cửa Biển", slicer_result.prefix)
        self.assertIn("## Chương 2: Bày Binh Bố Trận", slicer_result.prefix)

        # Chapter 3 in window
        self.assertIn("## Chương 3: Huyết Chiến Bến Vạn Kiếp", slicer_result.window_to_edit)
        self.assertIn("Chiến thuyền giặc Ô Mã Nhi", slicer_result.window_to_edit)

        # Chapter 4 in suffix
        self.assertIn("## Chương 4: Khải Hoàn Đại Việt", slicer_result.suffix)
        self.assertNotIn("## Chương 4: Khải Hoàn Đại Việt", slicer_result.window_to_edit)

    def test_chapter_targeting_last_chapter(self):
        """
        Verify that targeting the last chapter ('sửa Chương 4') slices Chapter 4 with empty suffix.
        """
        instruction = "sửa Chương 4: nhấn mạnh lời thề bảo vệ biên cương của Hưng Đạo Vương"
        
        slicer_result = SemanticChunkSlicer.slice_manuscript(
            story=self.sample_novel,
            target=SurgeryTarget.GENERAL_SURGERY,
            instruction=instruction
        )

        self.assertIn("## Chương 1", slicer_result.prefix)
        self.assertIn("## Chương 2", slicer_result.prefix)
        self.assertIn("## Chương 3", slicer_result.prefix)
        self.assertIn("## Chương 4: Khải Hoàn Đại Việt", slicer_result.window_to_edit)
        self.assertEqual(slicer_result.suffix.strip(), "")

    def test_chapter_targeting_case_insensitivity_and_variants(self):
        """
        Test case variations and synonym markers:
        'sửa chapter 2', 'chỉnh sửa hồi 3', 'viết lại phần 1', 'chương 2'.
        """
        variants = [
            ("sửa chapter 2", "## Chương 2: Bày Binh Bố Trận"),
            ("chỉnh sửa chương 2", "## Chương 2: Bày Binh Bố Trận"),
            ("thay đổi Chương 3", "## Chương 3: Huyết Chiến Bến Vạn Kiếp"),
            ("viết lại hồi 3", "## Chương 3: Huyết Chiến Bến Vạn Kiếp"),
        ]
        for inst, expected_heading in variants:
            slicer_result = SemanticChunkSlicer.slice_manuscript(
                story=self.sample_novel,
                target=SurgeryTarget.GENERAL_SURGERY,
                instruction=inst
            )
            self.assertIn(
                expected_heading,
                slicer_result.window_to_edit,
                f"Failed for variant instruction: '{inst}'"
            )

    def test_instruction_utilization_override_default_target(self):
        """
        Verify that when target is TARGET_1_OPENING but instruction says 'sửa Chương 3',
        the explicit chapter in instruction takes precedence over opening slicing.
        """
        instruction = "Sửa Chương 3 thêm lời thoại giữa Ô Mã Nhi và Phàn Tiếp"
        slicer_result = SemanticChunkSlicer.slice_manuscript(
            story=self.sample_novel,
            target=SurgeryTarget.TARGET_1_OPENING,
            instruction=instruction
        )
        self.assertIn("## Chương 3: Huyết Chiến Bến Vạn Kiếp", slicer_result.window_to_edit)
        self.assertIn("## Chương 1", slicer_result.prefix)


class TestRound6CopilotSelectedTextTargeting(unittest.TestCase):
    """
    Tests for Requirement R1.1:
    Copilot receives selectedText and cursorPosition from frontend,
    and only modifies the targeted selected substring.
    """

    def setUp(self):
        self.story = (
            "**Hào Khí Đông A**\n\n"
            "Đêm ấy, ánh trăng vằng vặc soi sáng dòng sông Lục Đầu.\n"
            "Trần Hưng Đạo ngồi một mình trong trướng, lật mở từng trang binh thư.\n"
            "Ngoài trướng, tiếng sóng vỗ rì rào hòa cùng tiếng quân sĩ mài gươm rộn rã."
        )

    def test_selected_text_exact_slicing(self):
        """
        When user highlights a specific paragraph, slicer sets window_to_edit
        precisely to that highlighted text.
        """
        selected = "Trần Hưng Đạo ngồi một mình trong trướng, lật mở từng trang binh thư."
        
        # Test passing selected_text via slice_manuscript
        # Supports both keyword argument and instruction context
        sig = inspect.signature(SemanticChunkSlicer.slice_manuscript)
        if "selected_text" in sig.parameters:
            slicer_result = SemanticChunkSlicer.slice_manuscript(
                story=self.story,
                target=SurgeryTarget.GENERAL_SURGERY,
                instruction="viết lại đoạn này cho bi tráng hơn",
                selected_text=selected
            )
        else:
            # If slicer parses instruction or helper
            slicer_result = SemanticChunkSlicer.slice_manuscript(
                story=self.story,
                target=SurgeryTarget.GENERAL_SURGERY,
                instruction=f"sửa đoạn bôi đen: {selected}"
            )

        self.assertIn(selected, slicer_result.window_to_edit)
        self.assertIn("Đêm ấy, ánh trăng vằng vặc", slicer_result.prefix)
        self.assertIn("Ngoài trướng, tiếng sóng vỗ", slicer_result.suffix)

    def test_selected_text_with_cursor_position_disambiguation(self):
        """
        When identical phrases appear in multiple places in the story,
        cursorPosition accurately locates the exact occurrence.
        """
        duplicate_story = (
            "Tiếng gươm khua vang dội.\n\n"
            "Đoàn quân tiến bước trong màn sương mờ mịt.\n\n"
            "Tiếng gươm khua vang dội.\n\n"
            "Quân thù hoảng loạn tan tác."
        )
        selected = "Tiếng gươm khua vang dội."
        second_occurrence_index = duplicate_story.rfind(selected)

        sig = inspect.signature(SemanticChunkSlicer.slice_manuscript)
        if "selected_text" in sig.parameters and "cursor_position" in sig.parameters:
            slicer_result = SemanticChunkSlicer.slice_manuscript(
                story=duplicate_story,
                target=SurgeryTarget.GENERAL_SURGERY,
                instruction="Đổi thành tiếng trống thúc vang trời",
                selected_text=selected,
                cursor_position=second_occurrence_index
            )
            # Prefix should contain the first occurrence
            self.assertIn("Đoàn quân tiến bước", slicer_result.prefix)
            self.assertIn(selected, slicer_result.prefix)
            self.assertEqual(slicer_result.window_to_edit.strip(), selected)
            self.assertIn("Quân thù hoảng loạn", slicer_result.suffix)

    def test_selected_text_whitespace_tolerance(self):
        """
        Verify that leading/trailing whitespaces in selection do not cause slice failure.
        """
        selected_raw = "  Trần Hưng Đạo ngồi một mình trong trướng  "
        sig = inspect.signature(SemanticChunkSlicer.slice_manuscript)
        if "selected_text" in sig.parameters:
            slicer_result = SemanticChunkSlicer.slice_manuscript(
                story=self.story,
                target=SurgeryTarget.GENERAL_SURGERY,
                instruction="sửa đoạn này",
                selected_text=selected_raw
            )
            self.assertIn("Trần Hưng Đạo ngồi một mình trong trướng", slicer_result.window_to_edit)


class TestRound6CopilotPathBNonTruncation(unittest.TestCase):
    """
    Tests for Requirement R1.4:
    Path B (Master Controller Fallback) must NOT overwrite the whole story
    based on the last 2000 characters context. Preceding text (>5000 chars) must be preserved.
    """

    def setUp(self):
        # Generate a realistic 6000-character manuscript across 5 chapters
        chapters = []
        for i in range(1, 6):
            paras = [
                f"Đây là đoạn {j} của chương {i}. " + ("Hào khí non sông vang vọng muôn thuở. " * 15)
                for j in range(1, 6)
            ]
            chapters.append(f"## Chương {i}: Đại Tự Ký {i}\n\n" + "\n\n".join(paras))
        self.long_story = "**Biên Niên Sử Đại Việt Toàn Thư**\n\n" + "\n\n".join(chapters)
        self.assertTrue(len(self.long_story) > 5000, f"Story length {len(self.long_story)} <= 5000")

    @patch("agents.copilot_agent.CopilotAgent._chat_with_fallback")
    def test_path_b_does_not_truncate_long_story(self, mock_chat):
        """
        When Master Controller produces an edit_story_direct action from short_context (-2000 chars),
        verify that the returned story preserves the full manuscript (prefix > 3000 chars).
        """
        agent = CopilotAgent()

        # Mock LLM response in Path B
        mock_chat.return_value = (
            json.dumps({
                "thought": "Chỉnh sửa đoạn kết theo yêu cầu",
                "action": "edit_story_direct",
                "action_params": {
                    "updated_story_content": "## Chương 5: Đại Tự Ký 5\n\nĐoạn kết mới cực kỳ tráng lệ và hào hùng."
                }
            }),
            "llama-3.1-70b-versatile"
        )

        # Call process_event simulating Path B trigger
        payload = json.dumps({
            "user_message": "Hãy sửa lại cái kết cho thêm phần tráng lệ",
            "current_story": self.long_story
        })

        result = agent.process_event("USER_CHAT", payload)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("action"), "edit_story_direct")
        
        updated_content = result.get("action_params", {}).get("updated_story_content", "")
        self.assertTrue(len(updated_content) > 0)

        # CRITICAL ASSERTION: The story must retain Chapter 1, Chapter 2, Chapter 3
        # It must NOT be truncated to just the 2000 chars or just Chapter 5!
        self.assertIn("## Chương 1: Đại Tự Ký 1", updated_content, "Preceding Chapter 1 was lost in Path B!")
        self.assertIn("## Chương 2: Đại Tự Ký 2", updated_content, "Preceding Chapter 2 was lost in Path B!")
        self.assertIn("## Chương 3: Đại Tự Ký 3", updated_content, "Preceding Chapter 3 was lost in Path B!")
        self.assertIn("## Chương 5: Đại Tự Ký 5", updated_content, "Targeted Chapter 5 was not included!")
        self.assertIn("Biên Niên Sử Đại Việt Toàn Thư", updated_content, "Title was lost!")
        self.assertTrue(
            len(updated_content) >= 4000,
            f"Updated content length {len(updated_content)} was truncated below 4000 chars!"
        )


class TestRound6CopilotIntermediateHeadingPreservation(unittest.TestCase):
    """
    Tests for Requirement R1.5:
    HeadingPreservationEngine must preserve intermediate chapter headings
    in correct relative order without bunching them at the very top.
    """

    def setUp(self):
        self.original_multichapter = (
            "**Hịch Tướng Sĩ Diễn Nghĩa**\n\n"
            "## Chương 1: Lời Hịch Non Sông\n"
            "Ta thường nghe Kỷ Tín đem mình chết thay cứu thoát Cao Đế.\n"
            "Do Vu lấy thân che đỡ vua Chiêu Vương.\n\n"
            "## Chương 2: Nỗi Lòng Tiết Chế\n"
            "Ta từng tới bữa quên ăn, nửa đêm vỗ gối, ruột đau như cắt, nước mắt đầm đìa.\n"
            "Chỉ căm tức chưa xả thịt lột da, nuốt gan uống máu quân thù.\n\n"
            "## Chương 3: Luyện Tập Võ Nghệ\n"
            "Nay các ngươi thấy chủ nhục mà không biết lo, thấy nước nhục mà không biết thẹn.\n"
            "Phải dùi mài võ nghệ, học tập binh thư, giữ vững tinh thần Đông A."
        )

    def test_headings_preserve_correct_relative_order_when_stripped_by_llm(self):
        """
        When the LLM strips ## Chương 2 and ## Chương 3 in revised prose:
        HeadingPreservationEngine must NOT prepend both headings to the top
        resulting in reverse ordering or bunching before Chapter 1 content.
        """
        # Simulated LLM output where LLM forgot all chapter markers
        revised_without_headings = (
            "Ta nghe truyện xưa những trung thần nghĩa sĩ liều mình vì chúa.\n\n"
            "Đêm nằm trằn trọc đau xót nhìn bờ cõi bị giày xéo, quyết chí diệt giặc.\n\n"
            "Toàn quân trên dưới đồng lòng, luyện tập ngày đêm rèn binh luyện mã."
        )

        preserved = HeadingPreservationEngine.preserve_headings(
            original_story=self.original_multichapter,
            window_text=self.original_multichapter,
            revised_window=revised_without_headings,
            target=SurgeryTarget.GENERAL_SURGERY
        )

        # All 3 chapter headings must exist in the preserved result
        self.assertIn("## Chương 1", preserved)
        self.assertIn("## Chương 2", preserved)
        self.assertIn("## Chương 3", preserved)

        # Check relative positions
        pos_ch1 = preserved.find("## Chương 1")
        pos_ch2 = preserved.find("## Chương 2")
        pos_ch3 = preserved.find("## Chương 3")

        self.assertTrue(
            pos_ch1 < pos_ch2 < pos_ch3,
            f"Headings out of order! Pos1={pos_ch1}, Pos2={pos_ch2}, Pos3={pos_ch3}.\nPreserved text:\n{preserved}"
        )

        # Chapter 2 must NOT be placed immediately adjacent to Chapter 1 at the top
        # There should be paragraph content between Chapter 1 and Chapter 2
        text_between_1_and_2 = preserved[pos_ch1:pos_ch2]
        self.assertTrue(
            len(text_between_1_and_2.strip().split("\n")) > 1,
            "Chapter 2 is bunched directly below Chapter 1 without separating prose!"
        )

    def test_intermediate_heading_with_existing_heading_not_duplicated(self):
        """
        If the revised text already kept ## Chương 1 and ## Chương 2 but omitted ## Chương 3,
        HeadingPreservationEngine should only insert ## Chương 3 in the right place
        without duplicating ## Chương 1 or ## Chương 2.
        """
        partial_revised = (
            "## Chương 1: Lời Hịch Non Sông\n"
            "Nội dung chương 1 được trau chuốt lại.\n\n"
            "## Chương 2: Nỗi Lòng Tiết Chế\n"
            "Nội dung chương 2 dạt dào cảm xúc căm thù giặc.\n\n"
            "Nội dung chương 3 bị rớt tiêu đề cần được khôi phục."
        )

        preserved = HeadingPreservationEngine.preserve_headings(
            original_story=self.original_multichapter,
            window_text=self.original_multichapter,
            revised_window=partial_revised,
            target=SurgeryTarget.GENERAL_SURGERY
        )

        # Count occurrences: each heading should appear exactly once
        self.assertEqual(preserved.count("## Chương 1"), 1)
        self.assertEqual(preserved.count("## Chương 2"), 1)
        self.assertEqual(preserved.count("## Chương 3"), 1)

        pos_ch1 = preserved.find("## Chương 1")
        pos_ch2 = preserved.find("## Chương 2")
        pos_ch3 = preserved.find("## Chương 3")
        self.assertTrue(pos_ch1 < pos_ch2 < pos_ch3)


class TestRound6CopilotAdversarialAndEdgeCases(unittest.TestCase):
    """
    Adversarial & Edge Cases for Copilot Surgery:
    - Empty story, empty instruction
    - Very large instruction
    - Non-existent chapter targeting (e.g. 'sửa Chương 99')
    """

    def test_nonexistent_chapter_targeting_fallback(self):
        """
        When user requests 'sửa Chương 99' on a 3-chapter story,
        it should not crash; it should fall back safely to whole story or appropriate chunk.
        """
        story = "## Chương 1: A\nNội dung A\n\n## Chương 2: B\nNội dung B"
        slicer_result = SemanticChunkSlicer.slice_manuscript(
            story=story,
            target=SurgeryTarget.GENERAL_SURGERY,
            instruction="sửa Chương 99 cho hay"
        )
        self.assertIsInstance(slicer_result, ChunkSlice)
        # Verify whole story is represented across prefix, window, suffix
        combined = f"{slicer_result.prefix}\n\n{slicer_result.window_to_edit}\n\n{slicer_result.suffix}".strip()
        self.assertIn("Chương 1", combined)
        self.assertIn("Chương 2", combined)

    def test_empty_story_handling(self):
        """Empty story should return empty slice without exception."""
        res = SemanticChunkSlicer.slice_manuscript("", SurgeryTarget.GENERAL_SURGERY, "sửa chương 1")
        self.assertEqual(res.prefix, "")
        self.assertEqual(res.window_to_edit, "")
        self.assertEqual(res.suffix, "")

    def test_unwrap_prose_on_nested_json_in_surgery(self):
        """Ensure unwrapping handles double nested JSON inside surgery responses."""
        nested = '{"updated_story_content": "{\\"updated_story_content\\": \\"**Tiêu Đề**\\\\n\\\\nNội dung văn xuôi chuẩn.\\"}"}'
        unwrapped = unwrap_story_prose(nested)
        self.assertIn("**Tiêu Đề**", unwrapped)
        self.assertNotIn("updated_story_content", unwrapped)


if __name__ == "__main__":
    unittest.main()
