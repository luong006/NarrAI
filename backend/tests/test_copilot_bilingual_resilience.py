"""
Unit tests for Copilot Bilingual Intent Recognition, Token Windowing, and Model Fallback Resilience (Requirement R4).
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Ensure backend directory is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agents.copilot_agent import CopilotAgent, unwrap_story_prose
from agents.story_memory import StoryMemory, StoryBible


class TestCopilotBilingualResilience(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ["GROQ_API_KEY"] = os.environ.get("GROQ_API_KEY", "dummy_key_for_test")

    def setUp(self):
        with patch("agents.copilot_agent.GroqClient"):
            self.agent = CopilotAgent()

    def test_english_quick_commands_trigger_direct_edit(self):
        """All 4 English quick prompts from frontend must trigger direct manuscript edit."""
        quick_commands = [
            "Write a completely different opening for this story",
            "Make the ending much more dramatic and suspenseful",
            "Rewrite in a darker, more gripping thriller tone",
            "Add deeper internal thoughts and character dialogues",
        ]
        for cmd in quick_commands:
            self.assertTrue(
                self.agent._is_direct_edit_request(cmd),
                f"Expected '{cmd}' to trigger direct edit, but got False",
            )

    def test_english_action_verbs_and_descriptors(self):
        """Test variations of English action verbs and target nouns/tones."""
        test_cases = [
            ("Please rewrite the intro to make it punchier", True),
            ("Can you edit the ending to have a cliffhanger?", True),
            ("Shorten this chapter and make it faster paced", True),
            ("Revise the dialogue between the characters", True),
            ("Make the style darker and more suspenseful", True),
            ("Update the manuscript with more action", True),
            ("Expand the opening scene with sensory details", True),
            # Conversational non-edit exclusions
            ("What if the hero went home instead of fighting?", False),
            ("Can we talk about the characters rather than writing?", False),
            ("What if the villain is actually good?", False),
            # Vietnamese preservation
            ("Tôi muốn viết lại đoạn mở đầu", True),
            ("Hãy sửa đoạn kết kịch tính hơn", True),
            ("Thay vì đánh nhau họ làm hòa", False),
        ]
        for prompt, expected in test_cases:
            res = self.agent._is_direct_edit_request(prompt)
            self.assertEqual(res, expected, f"Failed for prompt: '{prompt}' (got {res}, expected {expected})")

    def test_manuscript_windowing_large_story(self):
        """Manuscript windowing on > 15,000 char story must enforce MAX_MANUSCRIPT_CHARS = 8000."""
        # Create a large story with distinct paragraphs (~16,000 characters)
        paragraph = "Đây là đoạn văn mẫu miêu tả cảnh vật và sự kiện xảy ra trong thế giới huyền ảo rộng lớn với nhiều chi tiết hấp dẫn.\n\n"
        large_story = paragraph * 140
        self.assertGreater(len(large_story), 15000)

        # 1. Opening edit windowing
        prefix, window, suffix = self.agent._get_windowed_manuscript("Write a completely different opening", large_story)
        self.assertEqual(prefix, "")
        self.assertLessEqual(len(window), self.agent.MAX_MANUSCRIPT_CHARS)
        self.assertGreater(len(suffix), 0)
        self.assertEqual((prefix + window + suffix), large_story)

        # 2. Ending edit windowing
        prefix, window, suffix = self.agent._get_windowed_manuscript("Make the ending much more dramatic", large_story)
        self.assertEqual(suffix, "")
        self.assertLessEqual(len(window), self.agent.MAX_MANUSCRIPT_CHARS)
        self.assertGreater(len(prefix), 0)
        self.assertEqual((prefix + window + suffix), large_story)

        # 3. Tone edit active windowing
        prefix, window, suffix = self.agent._get_windowed_manuscript("Rewrite in a darker, more gripping thriller tone", large_story)
        self.assertEqual(prefix, "")
        self.assertLessEqual(len(window), self.agent.MAX_MANUSCRIPT_CHARS)
        self.assertGreater(len(suffix), 0)
        self.assertEqual((prefix + window + suffix), large_story)

    def test_multi_tier_model_fallback(self):
        """Primary model failure triggers fallback to secondary model in chain."""
        mock_primary = MagicMock()
        mock_primary.chat.side_effect = Exception("429 Rate Limit Exceeded on gpt-oss-120b")

        mock_secondary = MagicMock()
        mock_secondary.model = "llama-3.3-70b-versatile"
        mock_secondary.chat.return_value = '{"updated_story_content": "Bản thảo mới sau khi fallback thành công.", "summary_of_changes": "Sửa thành công", "message": "Đã sửa xong!"}'

        self.agent.llm = mock_primary
        self.agent._clients["llama-3.3-70b-versatile"] = mock_secondary

        res = self.agent._perform_direct_manuscript_edit(
            "Rewrite in a darker, more gripping thriller tone",
            "Nội dung truyện ban đầu."
        )

        self.assertIsNotNone(res)
        self.assertEqual(res.get("action"), "edit_story_direct")
        self.assertIn("Bản thảo mới sau khi fallback thành công.", res["action_params"]["updated_story_content"])
        self.assertIn("llama-3.3-70b-versatile", res.get("thought", ""))

    def test_payload_deduplication_in_step_2(self):
        """Master controller strips duplicated current_story from payload before LLM request."""
        mock_llm = MagicMock()
        mock_llm.model = "openai/gpt-oss-120b"
        mock_llm.chat.return_value = '{"thought": "Phản hồi người dùng", "action": "reply_user", "action_params": {"message": "Xin chào!"}}'
        self.agent.llm = mock_llm

        event_data = '{"user_message": "Tell me about the story so far", "current_story": "' + ("A" * 15000) + '"}'
        res = self.agent.process_event("USER_CHAT", event_data)

        self.assertEqual(res.get("action"), "reply_user")
        called_args = mock_llm.chat.call_args[0][0]
        user_prompt = called_args[1]["content"]

        # Confirm 15,000 char story was stripped from user payload
        self.assertNotIn("A" * 15000, user_prompt)
        self.assertIn("Tell me about the story so far", user_prompt)

    def test_polite_language_aware_fallback_when_all_fail(self):
        """When all models fail, returns a polite message in user's language."""
        mock_primary = MagicMock()
        mock_primary.chat.side_effect = Exception("Service unavailable")
        self.agent.llm = mock_primary

        with patch.object(self.agent, "_chat_with_fallback", side_effect=RuntimeError("All models failed")):
            # English request
            res_en = self.agent.process_event("USER_CHAT", '{"user_message": "Can you give me an idea for chapter 2?"}')
            self.assertEqual(res_en.get("action"), "reply_user")
            self.assertIn("temporarily experiencing technical difficulties", res_en["action_params"]["message"])

            # Vietnamese request
            res_vi = self.agent.process_event("USER_CHAT", '{"user_message": "Cho tôi ý tưởng cho chương 2"}')
            self.assertEqual(res_vi.get("action"), "reply_user")
            self.assertIn("Hệ thống chỉ huy đang gặp trục trặc nhẹ", res_vi["action_params"]["message"])


if __name__ == "__main__":
    unittest.main()
