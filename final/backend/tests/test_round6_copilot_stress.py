"""
NarrAI Round 6 Milestone 1 Stress & Oracle Verification Test Harness
File: backend/tests/test_round6_copilot_stress.py

Adversarial Stress Test Suite for Milestone 1:
1. Copilot Chapter Targeting:
   - Edit Chapter 2 in a 5-chapter story: Prefix (Title + Chapter 1) and Suffix (Chapters 3, 4, 5) untouched.
   - Edit Chapter 1 in a 5-chapter story: Title untouched, Suffix (Chapters 2, 3, 4, 5) untouched.
   - Edit Chapter 5 in a 5-chapter story: Prefix (Title + Chapters 1, 2, 3, 4) untouched, Suffix empty.
   - Non-existent Chapter 10: Graceful fallback without IndexError or data truncation.
2. Path B 2000-char Overwrite Prevention:
   - 10,000-character story edit via Path B Master Controller fallback.
   - Verify output length is ~10,000 chars (full 8,000+ char prefix preserved).
   - Verify output starts with the original story title and opening text.
3. Intermediate Chapter Title Placement:
   - Strip Chapter 2 heading from LLM output in multi-chapter story.
   - Verify HeadingPreservationEngine places '## Chương 2' strictly between Chapter 1 and Chapter 3.
   - Verify '## Chương 2' is NOT bunched at line 1.
   - Test multi-heading strip (stripping both Chapter 2 and Chapter 3).
"""

import os
import sys
import json
import unittest
from unittest.mock import MagicMock, patch

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


class TestCopilotChapterTargetingStress(unittest.TestCase):
    """
    Empirical Oracles for Chapter Targeting:
    5-chapter novel sliced and edited chapter-by-chapter.
    """

    def setUp(self):
        self.story_5_chapters = (
            "**Bạch Đằng Ký Sử Toàn Thư**\n\n"
            "## Chương 1: Gió Nổi Sông Rừng\n"
            "Tháng Chạp buốt giá, chiến thuyền Đại Việt bí mật tập kết tại bến Vạn Kiếp.\n"
            "Trần Hưng Đạo dõi mắt nhìn con nước triều dâng, suy tính thế trận mai phục muôn đời.\n\n"
            "## Chương 2: Trận Địa Cọc Lim Bịt Sắt\n"
            "Hàng vạn thân gỗ lim già được đốn hạ từ rừng sâu, vót nhọn và bọc sắt kiên cố.\n"
            "Dưới sự chỉ huy của Yết Kiêu, thủy quân lặn ngụp ngày đêm cắm cọc xuống lòng sông.\n\n"
            "## Chương 3: Dử Địch Vào Trận Địa\n"
            "Tướng quân Nguyễn Khoái dẫn đoàn thuyền nhẹ ra khiêu chiến rồi giả vờ thua chạy.\n"
            "Ô Mã Nhi cùng Phàn Tiếp đắc thắng thúc toàn bộ chiến thuyền đuổi riết vào lạch sâu.\n\n"
            "## Chương 4: Thủy Triều Rút Và Huyết Chiến\n"
            "Nước triều đột ngột rút nhanh, cọc nhọn nhô lên đâm thủng liên tiếp đáy thuyền giặc.\n"
            "Tiếng tù và vang dậy đôi bờ, quân ta bốn phía đổ ra giáp chiến, tên lửa rực trời.\n\n"
            "## Chương 5: Khải Hoàn Đại Thắng Non Sông\n"
            "Bắt sống Ô Mã Nhi, bắt sống Tích Lệ Cơ Ngọc. Đoàn thuyền giặc bị tiêu diệt hoàn toàn.\n"
            "Bờ cõi Đại Việt ngàn năm vững bền, muôn dân reo hò đón chào đoàn quân thắng trận trở về."
        )

    def test_stress_edit_chapter_2_prefix_and_suffix_untouched(self):
        """
        Oracle: Slicing Chapter 2 in a 5-chapter story must leave
        Prefix (Title + Chapter 1) and Suffix (Chapters 3, 4, 5) 100% untouched.
        """
        instruction = "sửa Chương 2: bổ sung chi tiết Yết Kiêu hướng dẫn binh sĩ kiểm tra độ nghiêng của cọc lim"
        slice_result = SemanticChunkSlicer.slice_manuscript(
            story=self.story_5_chapters,
            target=SurgeryTarget.GENERAL_SURGERY,
            instruction=instruction
        )

        self.assertIsInstance(slice_result, ChunkSlice)

        # 1. Verify Prefix integrity
        expected_prefix = (
            "**Bạch Đằng Ký Sử Toàn Thư**\n\n"
            "## Chương 1: Gió Nổi Sông Rừng\n"
            "Tháng Chạp buốt giá, chiến thuyền Đại Việt bí mật tập kết tại bến Vạn Kiếp.\n"
            "Trần Hưng Đạo dõi mắt nhìn con nước triều dâng, suy tính thế trận mai phục muôn đời.\n\n"
        )
        self.assertEqual(slice_result.prefix, expected_prefix)
        self.assertIn("**Bạch Đằng Ký Sử Toàn Thư**", slice_result.prefix)
        self.assertIn("## Chương 1: Gió Nổi Sông Rừng", slice_result.prefix)
        self.assertNotIn("## Chương 2", slice_result.prefix)

        # 2. Verify Window integrity
        expected_window = (
            "## Chương 2: Trận Địa Cọc Lim Bịt Sắt\n"
            "Hàng vạn thân gỗ lim già được đốn hạ từ rừng sâu, vót nhọn và bọc sắt kiên cố.\n"
            "Dưới sự chỉ huy của Yết Kiêu, thủy quân lặn ngụp ngày đêm cắm cọc xuống lòng sông."
        )
        self.assertEqual(slice_result.window_to_edit, expected_window)
        self.assertIn("## Chương 2: Trận Địa Cọc Lim Bịt Sắt", slice_result.window_to_edit)
        self.assertNotIn("## Chương 1", slice_result.window_to_edit)
        self.assertNotIn("## Chương 3", slice_result.window_to_edit)

        # 3. Verify Suffix integrity
        expected_suffix_start = "\n\n## Chương 3: Dử Địch Vào Trận Địa"
        self.assertTrue(slice_result.suffix.startswith(expected_suffix_start))
        self.assertIn("## Chương 3: Dử Địch Vào Trận Địa", slice_result.suffix)
        self.assertIn("## Chương 4: Thủy Triều Rút Và Huyết Chiến", slice_result.suffix)
        self.assertIn("## Chương 5: Khải Hoàn Đại Thắng Non Sông", slice_result.suffix)
        self.assertNotIn("## Chương 2", slice_result.suffix)

        # 4. Invariant: Perfect concatenation reconstructs original
        reconstructed = f"{slice_result.prefix}{slice_result.window_to_edit}{slice_result.suffix}"
        self.assertEqual(reconstructed.strip(), self.story_5_chapters.strip())

    @patch("agents.copilot_agent.CopilotAgent._chat_with_fallback")
    def test_full_pipeline_edit_chapter_2_end_to_end(self, mock_chat):
        """
        Verify end-to-end CopilotAgent execution when editing Chapter 2:
        Prefix and Suffix are byte-preserved, and Chapter 2 is revised.
        """
        agent = CopilotAgent()
        new_ch2_prose = (
            "## Chương 2: Trận Địa Cọc Lim Bịt Sắt\n"
            "Yết Kiêu ngậm dùi đồng lặn sâu dưới đáy sông Bạch Đằng, đo góc nghiêng từng chiếc cọc gỗ.\n"
            "Toàn bộ cọc sắt được cắm chuẩn xác theo con nước triều."
        )
        mock_chat.return_value = (
            json.dumps({"updated_story_content": new_ch2_prose}),
            "llama-3.1-70b-versatile"
        )

        payload = json.dumps({
            "user_message": "sửa Chương 2: thêm cảnh Yết Kiêu lặn kiểm tra góc cọc",
            "current_story": self.story_5_chapters
        })
        res = agent.process_event("USER_CHAT", payload)

        self.assertEqual(res.get("action"), "edit_story_direct")
        updated = res["action_params"]["updated_story_content"]

        # Prefix unchanged
        self.assertIn("**Bạch Đằng Ký Sử Toàn Thư**", updated)
        self.assertIn("## Chương 1: Gió Nổi Sông Rừng", updated)
        self.assertIn("Trần Hưng Đạo dõi mắt nhìn con nước triều dâng", updated)

        # Chapter 2 modified
        self.assertIn("Yết Kiêu ngậm dùi đồng lặn sâu dưới đáy sông", updated)

        # Suffix unchanged
        self.assertIn("## Chương 3: Dử Địch Vào Trận Địa", updated)
        self.assertIn("## Chương 4: Thủy Triều Rút Và Huyết Chiến", updated)
        self.assertIn("## Chương 5: Khải Hoàn Đại Thắng Non Sông", updated)

    def test_stress_edit_chapter_1_preserves_title_and_suffix(self):
        """
        Oracle: Slicing Chapter 1 must preserve the title in prefix (or window),
        and keep Chapters 2, 3, 4, 5 completely untouched in suffix.
        """
        instruction = "sửa Chương 1: mở đầu thêm phần kịch tính hơn"
        slice_result = SemanticChunkSlicer.slice_manuscript(
            story=self.story_5_chapters,
            target=SurgeryTarget.GENERAL_SURGERY,
            instruction=instruction
        )

        self.assertIn("**Bạch Đằng Ký Sử Toàn Thư**", slice_result.prefix)
        self.assertIn("## Chương 1: Gió Nổi Sông Rừng", slice_result.window_to_edit)
        self.assertNotIn("## Chương 2", slice_result.window_to_edit)
        self.assertIn("## Chương 2: Trận Địa Cọc Lim Bịt Sắt", slice_result.suffix)
        self.assertIn("## Chương 5: Khải Hoàn Đại Thắng Non Sông", slice_result.suffix)

        reconstructed = f"{slice_result.prefix}{slice_result.window_to_edit}{slice_result.suffix}"
        self.assertEqual(reconstructed.strip(), self.story_5_chapters.strip())

    def test_stress_edit_chapter_5_last_chapter_empty_suffix(self):
        """
        Oracle: Slicing Chapter 5 (last chapter) must leave Chapters 1, 2, 3, 4
        in prefix untouched, place Chapter 5 in window, and leave suffix empty.
        """
        instruction = "viết lại Chương 5 cho hùng tráng hơn"
        slice_result = SemanticChunkSlicer.slice_manuscript(
            story=self.story_5_chapters,
            target=SurgeryTarget.GENERAL_SURGERY,
            instruction=instruction
        )

        self.assertIn("## Chương 1: Gió Nổi Sông Rừng", slice_result.prefix)
        self.assertIn("## Chương 2: Trận Địa Cọc Lim Bịt Sắt", slice_result.prefix)
        self.assertIn("## Chương 3: Dử Địch Vào Trận Địa", slice_result.prefix)
        self.assertIn("## Chương 4: Thủy Triều Rút Và Huyết Chiến", slice_result.prefix)
        self.assertIn("## Chương 5: Khải Hoàn Đại Thắng Non Sông", slice_result.window_to_edit)
        self.assertEqual(slice_result.suffix.strip(), "")

        reconstructed = f"{slice_result.prefix}{slice_result.window_to_edit}{slice_result.suffix}"
        self.assertEqual(reconstructed.strip(), self.story_5_chapters.strip())

    def test_stress_nonexistent_chapter_10_graceful_fallback(self):
        """
        Oracle: Asking to edit non-existent Chapter 10 must NOT raise an error
        and must fall back gracefully without corrupting or truncating the story.
        """
        instruction = "sửa Chương 10: thêm ngoại truyện về danh tướng Đại Việt"
        slice_result = SemanticChunkSlicer.slice_manuscript(
            story=self.story_5_chapters,
            target=SurgeryTarget.GENERAL_SURGERY,
            instruction=instruction
        )

        self.assertIsInstance(slice_result, ChunkSlice)
        combined = f"{slice_result.prefix}\n\n{slice_result.window_to_edit}\n\n{slice_result.suffix}".strip()
        self.assertIn("## Chương 1", combined)
        self.assertIn("## Chương 5", combined)
        self.assertIn("**Bạch Đằng Ký Sử Toàn Thư**", combined)


class TestCopilotPathBOverwriteStress(unittest.TestCase):
    """
    Empirical Oracles for Path B 2000-character Overwrite Bug Elimination.
    """

    def setUp(self):
        # Generate a realistic 10,000+ character story spanning 6 long chapters
        chapters = []
        for i in range(1, 7):
            paras = []
            for j in range(1, 8):
                paras.append(
                    f"Phân đoạn {j} của chương {i}: Quân sĩ Đại Việt kiên cường giữ vững phòng tuyến. "
                    "Gió mùa đông bắc thổi qua bãi cọc nhọn hoắt, cờ thêu sáu chữ vàng phấp phới tung bay. "
                    "Ý chí sát Thát ngùn ngụt bốc cao trong huyết quản của muôn vạn tráng sĩ. "
                    "Không một tấc đất nào của giang sơn gấm vóc để lọt vào tay quân thù bạo ngược. "
                )
            chapters.append(f"## Chương {i}: Bản Hùng Ca Thời Đại {i}\n\n" + "\n\n".join(paras))
        self.story_10k = "**Đại Việt Sử Thi Vạn Cổ Hùng Anh**\n\n" + "\n\n".join(chapters)
        self.assertGreaterEqual(len(self.story_10k), 10000, f"Story length {len(self.story_10k)} < 10000")

    @patch("agents.copilot_agent.CopilotAgent._chat_with_fallback")
    def test_path_b_fallback_merges_full_manuscript(self, mock_chat):
        """
        Oracle: When Path B fallback executes with short rewritten ending (~300 chars),
        the final story must retain the full ~10,000 chars, start with the original opening,
        and not truncate preceding chapters 1 to 5.
        """
        agent = CopilotAgent()

        rewritten_ending = (
            "## Chương 6: Bản Hùng Ca Thời Đại 6\n\n"
            "Cờ khải hoàn tung bay rực rỡ khắp non sông Đại Việt. Ngàn năm thái bình thịnh trị mở ra."
        )

        # Mock Path B LLM returning rewritten ending
        mock_chat.return_value = (
            json.dumps({
                "thought": "Chỉnh sửa kết thúc theo lệnh chỉ huy",
                "action": "edit_story_direct",
                "action_params": {
                    "updated_story_content": rewritten_ending
                }
            }),
            "llama-3.1-70b-versatile"
        )

        # Force execution into Path B fallback by bypassing Path A
        with patch.object(agent, "_perform_direct_manuscript_edit", return_value=None):
            payload = json.dumps({
                "user_message": "Hãy cho một cái kết thật huy hoàng",
                "current_story": self.story_10k
            })
            res = agent.process_event("USER_CHAT", payload)

        self.assertEqual(res.get("action"), "edit_story_direct")
        updated = res["action_params"]["updated_story_content"]

        # Output length must be ~10,000 characters (> 8,300 chars, not just 2000 chars)
        self.assertGreaterEqual(
            len(updated),
            8300,
            f"Path B truncated the story! Length was {len(updated)}, expected >= 8300 chars."
        )

        # Output must start with the original opening and title
        expected_title = "**Đại Việt Sử Thi Vạn Cổ Hùng Anh**"
        self.assertTrue(
            updated.startswith(expected_title),
            f"Story does not start with original title! Starts with: {updated[:80]}"
        )

        # Preceding chapters must be 100% preserved
        self.assertIn("## Chương 1: Bản Hùng Ca Thời Đại 1", updated)
        self.assertIn("## Chương 2: Bản Hùng Ca Thời Đại 2", updated)
        self.assertIn("## Chương 3: Bản Hùng Ca Thời Đại 3", updated)
        self.assertIn("## Chương 4: Bản Hùng Ca Thời Đại 4", updated)
        self.assertIn("## Chương 5: Bản Hùng Ca Thời Đại 5", updated)
        self.assertIn("Cờ khải hoàn tung bay rực rỡ khắp non sông", updated)


class TestIntermediateHeadingPreservationStress(unittest.TestCase):
    """
    Empirical Oracles for Intermediate Chapter Title Placement:
    HeadingPreservationEngine must place '## Chương 2' between Chapter 1 and Chapter 3,
    and NEVER at line 1.
    """

    def setUp(self):
        self.multichapter_story = (
            "**Nam Quốc Sơn Hà Kỷ**\n\n"
            "## Chương 1: Lời Thề Bến Đông Bộ Đầu\n"
            "Vua tôi nhà Trần cùng chung một ý chí diệt giặc cứu nguy cho xã tắc muôn dân.\n"
            "Tiếng gươm khua rộn rã bên bờ sông Hồng, ánh lửa trại bập bùng suốt canh thâu.\n\n"
            "## Chương 2: Hội Nghị Diên Hồng\n"
            "Các bô lão khắp mọi miền đất nước tề tựu đông đủ trước thềm điện Diên Hồng tráng lệ.\n"
            "Khi vua hỏi nên hòa hay nên đánh, muôn người đồng thanh hô vang như sấm dậy: ĐÁNH!\n\n"
            "## Chương 3: Trận Phản Công Vạn Kiếp\n"
            "Chiến thuyền cờ xí rợp trời tiến thẳng về phía quân Mông Cổ hung hãn bạo tàn.\n"
            "Quân ta xung trận dũng mãnh, phá tan tác hàng ngũ quân thù, giành lại giang sơn."
        )

    def test_intermediate_heading_placed_between_chapters_not_at_line_1(self):
        """
        Oracle: When LLM output omits '## Chương 2: Hội Nghị Diên Hồng',
        HeadingPreservationEngine must restore it between Chapter 1 and Chapter 3.
        It must NOT appear at line 1.
        """
        # Revised text where LLM completely stripped '## Chương 2: Hội Nghị Diên Hồng'
        revised_missing_ch2 = (
            "**Nam Quốc Sơn Hà Kỷ**\n\n"
            "## Chương 1: Lời Thề Bến Đông Bộ Đầu\n"
            "Vua tôi nhà Trần cùng chung một ý chí diệt giặc cứu nguy cho xã tắc muôn dân.\n"
            "Tiếng gươm khua rộn rã bên bờ sông Hồng, ánh lửa trại bập bùng suốt canh thâu.\n\n"
            "Các bô lão khắp mọi miền đất nước tề tựu đông đủ trước thềm điện Diên Hồng tráng lệ.\n"
            "Khi vua hỏi nên hòa hay nên đánh, muôn người đồng thanh hô vang như sấm dậy: ĐÁNH!\n\n"
            "## Chương 3: Trận Phản Công Vạn Kiếp\n"
            "Chiến thuyền cờ xí rợp trời tiến thẳng về phía quân Mông Cổ hung hãn bạo tàn.\n"
            "Quân ta xung trận dũng mãnh, phá tan tác hàng ngũ quân thù, giành lại giang sơn."
        )

        preserved = HeadingPreservationEngine.preserve_headings(
            original_story=self.multichapter_story,
            window_text=self.multichapter_story,
            revised_window=revised_missing_ch2,
            target=SurgeryTarget.GENERAL_SURGERY
        )

        # 1. Heading 2 must be restored
        self.assertIn("## Chương 2: Hội Nghị Diên Hồng", preserved)

        # 2. Positional assertions
        pos_ch1 = preserved.find("## Chương 1")
        pos_ch2 = preserved.find("## Chương 2")
        pos_ch3 = preserved.find("## Chương 3")

        self.assertGreater(pos_ch1, 0, "Chapter 1 missing")
        self.assertGreater(pos_ch2, pos_ch1, "Chapter 2 must come after Chapter 1")
        self.assertGreater(pos_ch3, pos_ch2, "Chapter 3 must come after Chapter 2")

        # 3. Heading 2 must NOT be at line 1
        lines = preserved.strip().split("\n")
        first_content_line = lines[0].strip()
        self.assertNotEqual(
            first_content_line,
            "## Chương 2: Hội Nghị Diên Hồng",
            "Chapter 2 was placed at line 1!"
        )

        # 4. Check paragraph distance between Chapter 1 and Chapter 2
        intermediate_text = preserved[pos_ch1:pos_ch2]
        self.assertIn("Vua tôi nhà Trần", intermediate_text)

    def test_multiple_headings_stripped_restored_in_sequential_order(self):
        """
        Oracle: When LLM output strips BOTH Chapter 2 and Chapter 3,
        HeadingPreservationEngine must restore both in strict ascending order (Ch1 < Ch2 < Ch3).
        """
        revised_missing_ch2_and_ch3 = (
            "## Chương 1: Lời Thề Bến Đông Bộ Đầu\n"
            "Nội dung chương 1.\n\n"
            "Nội dung chương 2 tại Diên Hồng.\n\n"
            "Nội dung chương 3 trận phản công lớn."
        )

        preserved = HeadingPreservationEngine.preserve_headings(
            original_story=self.multichapter_story,
            window_text=self.multichapter_story,
            revised_window=revised_missing_ch2_and_ch3,
            target=SurgeryTarget.GENERAL_SURGERY
        )

        pos_ch1 = preserved.find("## Chương 1")
        pos_ch2 = preserved.find("## Chương 2")
        pos_ch3 = preserved.find("## Chương 3")

        self.assertTrue(
            pos_ch1 < pos_ch2 < pos_ch3,
            f"Headings out of order! Ch1: {pos_ch1}, Ch2: {pos_ch2}, Ch3: {pos_ch3}"
        )


if __name__ == "__main__":
    unittest.main()
