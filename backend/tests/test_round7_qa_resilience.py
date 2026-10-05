"""
NarrAI Round 7 Test Suite: Backend AI Resilience & Q&A Interview Refiner
Location: backend/tests/test_round7_qa_resilience.py

Comprehensive tests covering:
1. Multi-Model Fallback progression (qwen/qwen3.8-27b -> llama-3.3-70b-versatile -> llama-3.1-8b-instant)
2. Multi-Key Fallback progression (GROQ_API_KEY_BIBLE -> GROQ_API_KEY -> GROQ_API_KEY_COPILOT)
3. Strict backward compatibility with self.llm mocks
4. Concept Mirroring and question generation formatting in system prompt
5. Dynamic heuristic fallback and anti-boilerplate enforcement
6. FastAPI /api/chat-interview endpoint error handling with HTTP 503 structured response
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Ensure backend root is on sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Ensure dummy keys for agent initialization
os.environ.setdefault("GROQ_API_KEY", "gsk_test_dummy_key_for_unit_tests")
os.environ.setdefault("GROQ_API_KEY_COPILOT", "gsk_test_dummy_key_for_unit_tests")
os.environ.setdefault("GROQ_API_KEY_BIBLE", "gsk_test_dummy_key_for_unit_tests")

from agents.qa_refiner import QARefiner


class TestRound7QARefinerResilience(unittest.TestCase):
    """Test suite for QARefiner Dual-Matrix Resilience (Models x Keys)."""

    def setUp(self):
        self.refiner = QARefiner()

    def test_qa_refiner_initialization_defaults(self):
        """Verify default models and key environment variable hierarchies."""
        self.assertEqual(
            self.refiner.MODELS,
            ["qwen/qwen3.8-27b", "llama-3.3-70b-versatile", "llama-3.1-8b-instant"]
        )
        self.assertEqual(
            self.refiner.KEY_ENV_VARS,
            ["GROQ_API_KEY_BIBLE", "GROQ_API_KEY", "GROQ_API_KEY_COPILOT"]
        )
        self.assertEqual(self.refiner.primary_model, "qwen/qwen3.8-27b")
        self.assertIsNotNone(self.refiner.llm)

    def test_qa_refiner_mock_compatibility(self):
        """Verify that mocking self.llm.chat continues to work 100% without triggering fallback."""
        mock_response = "Phản hồi mock cho thử nghiệm tương thích."
        self.refiner.llm.chat = MagicMock(return_value=mock_response)

        history = [{"role": "user", "content": "Ý tưởng kiếm hiệp hiện đại"}]
        result = self.refiner.chat_interview(history)

        self.assertEqual(result, mock_response)
        self.assertEqual(self.refiner.llm.chat.call_count, 1)
        self.assertEqual(self.refiner.last_model_used, "qwen/qwen3.8-27b")

    def test_chat_interview_sanitizes_metadata(self):
        """Verify chat_interview strips frontend metadata flags and keeps only role and content."""
        mock_response = "Phản hồi mock"
        self.refiner.llm.chat = MagicMock(return_value=mock_response)

        raw_history = [
            {
                "role": "user",
                "content": "Ý tưởng về vương triều",
                "is_offline_fallback": True,
                "error_message": "Network error",
                "failed_prompt": "failed",
                "is_ready": False,
            },
            {
                "role": "assistant",
                "content": "Gợi ý cốt truyện",
                "extra_field": 123,
            }
        ]

        result = self.refiner.chat_interview(raw_history)
        self.assertEqual(result, mock_response)

        call_messages = self.refiner.llm.chat.call_args[0][0]
        # First message is system prompt
        self.assertEqual(call_messages[0]["role"], "system")
        # Second message is sanitized user message
        self.assertEqual(call_messages[1], {"role": "user", "content": "Ý tưởng về vương triều"})
        self.assertNotIn("is_offline_fallback", call_messages[1])
        self.assertNotIn("error_message", call_messages[1])
        self.assertNotIn("failed_prompt", call_messages[1])
        self.assertNotIn("is_ready", call_messages[1])
        # Third message is sanitized assistant message
        self.assertEqual(call_messages[2], {"role": "assistant", "content": "Gợi ý cốt truyện"})
        self.assertNotIn("extra_field", call_messages[2])

    def test_multi_model_fallback_rate_limit_to_llama_70b(self):
        """Primary qwen fails with 429 rate limit; system must seamlessly fall back to llama-70b."""
        # 1. Primary client fails with 429
        self.refiner.llm.chat = MagicMock(side_effect=Exception("429 rate_limit_exceeded: TPM limit reached"))

        # 2. Mock _get_client to simulate llama-70b succeeding
        llama_70b_client = MagicMock()
        llama_70b_client.chat = MagicMock(return_value="Phản hồi thành công từ Llama-3.3-70b.")

        def mock_get_client(model, key):
            if model == "llama-3.3-70b-versatile":
                return llama_70b_client
            client = MagicMock()
            client.chat = MagicMock(side_effect=Exception(f"{model} rate limit"))
            return client

        self.refiner._get_client = mock_get_client

        history = [{"role": "user", "content": "Viết truyện trinh thám tâm lý"}]
        result = self.refiner.chat_interview(history)

        self.assertEqual(result, "Phản hồi thành công từ Llama-3.3-70b.")
        self.assertEqual(self.refiner.last_model_used, "llama-3.3-70b-versatile")

    def test_multi_model_fallback_tertiary_to_llama_8b(self):
        """Both qwen and llama-70b fail; system must fall back to tertiary llama-8b."""
        self.refiner.llm.chat = MagicMock(side_effect=Exception("qwen 429 rate limit"))

        llama_8b_client = MagicMock()
        llama_8b_client.chat = MagicMock(return_value="Phản hồi thành công từ Llama-3.1-8b.")

        def mock_get_client(model, key):
            if model == "llama-3.1-8b-instant":
                return llama_8b_client
            client = MagicMock()
            client.chat = MagicMock(side_effect=Exception(f"{model} failed"))
            return client

        self.refiner._get_client = mock_get_client

        history = [{"role": "user", "content": "Viết truyện kỳ ảo phương Đông"}]
        result = self.refiner.chat_interview(history)

        self.assertEqual(result, "Phản hồi thành công từ Llama-3.1-8b.")
        self.assertEqual(self.refiner.last_model_used, "llama-3.1-8b-instant")

    def test_multi_key_fallback_on_auth_quota_error(self):
        """Primary key GROQ_API_KEY_BIBLE fails with 401/quota; falls back to GROQ_API_KEY."""
        self.refiner.llm.chat = MagicMock(side_effect=Exception("401 Unauthorized or quota exhausted"))

        # Setup custom available keys
        self.refiner.get_available_keys = MagicMock(return_value=[
            ("GROQ_API_KEY_BIBLE", "gsk_invalid_bible_key"),
            ("GROQ_API_KEY", "gsk_valid_default_key"),
            ("GROQ_API_KEY_COPILOT", "gsk_backup_copilot_key")
        ])

        valid_client = MagicMock()
        valid_client.chat = MagicMock(return_value="Phản hồi thành công từ khóa dự phòng.")

        def mock_get_client(model, key):
            if key == "gsk_valid_default_key":
                return valid_client
            client = MagicMock()
            client.chat = MagicMock(side_effect=Exception(f"Key {key} failed"))
            return client

        self.refiner._get_client = mock_get_client

        history = [{"role": "user", "content": "Truyện ngắn đô thị"}]
        result = self.refiner.chat_interview(history)

        self.assertEqual(result, "Phản hồi thành công từ khóa dự phòng.")
        self.assertEqual(self.refiner.last_key_var_used, "GROQ_API_KEY")

    def test_multi_key_fallback_tertiary_copilot_key(self):
        """Both BIBLE and DEFAULT keys fail; falls back to tertiary GROQ_API_KEY_COPILOT."""
        self.refiner.llm.chat = MagicMock(side_effect=Exception("Primary failed"))

        self.refiner.get_available_keys = MagicMock(return_value=[
            ("GROQ_API_KEY_BIBLE", "key_1_fail"),
            ("GROQ_API_KEY", "key_2_fail"),
            ("GROQ_API_KEY_COPILOT", "key_3_pass")
        ])

        copilot_client = MagicMock()
        copilot_client.chat = MagicMock(return_value="Phản hồi từ Copilot Key.")

        def mock_get_client(model, key):
            if key == "key_3_pass":
                return copilot_client
            client = MagicMock()
            client.chat = MagicMock(side_effect=Exception(f"Key {key} rejected"))
            return client

        self.refiner._get_client = mock_get_client

        history = [{"role": "user", "content": "Kịch bản ma pháp"}]
        result = self.refiner.chat_interview(history)

        self.assertEqual(result, "Phản hồi từ Copilot Key.")
        self.assertEqual(self.refiner.last_key_var_used, "GROQ_API_KEY_COPILOT")

    def test_exhaustion_raises_runtime_error(self):
        """When all models and keys fail, chat_interview raises RuntimeError by default."""
        self.refiner.llm.chat = MagicMock(side_effect=Exception("Network unreachable"))

        def mock_get_client(model, key):
            client = MagicMock()
            client.chat = MagicMock(side_effect=Exception("Server 500"))
            return client

        self.refiner._get_client = mock_get_client

        history = [{"role": "user", "content": "Ý tưởng bất kỳ"}]
        with self.assertRaises(RuntimeError) as ctx:
            self.refiner.chat_interview(history, fallback_to_heuristic=False)

        self.assertIn("Tất cả mô hình và khóa API trong chuỗi dự phòng đều thất bại", str(ctx.exception))

    def test_heuristic_fallback_when_exhausted_and_enabled(self):
        """When all models fail and fallback_to_heuristic=True, heuristic generator is returned."""
        self.refiner.llm.chat = MagicMock(side_effect=Exception("All LLMs offline"))

        def mock_get_client(model, key):
            client = MagicMock()
            client.chat = MagicMock(side_effect=Exception("Down"))
            return client

        self.refiner._get_client = mock_get_client

        history = [{"role": "user", "content": "Thánh Gióng thời hiện đại"}]
        result = self.refiner.chat_interview(history, fallback_to_heuristic=True)

        self.assertIn("Thánh Gióng", result)
        self.assertEqual(self.refiner.last_model_used, "heuristic-fallback")
        self.assertEqual(self.refiner.last_key_var_used, "OFFLINE")


class TestConceptMirroringAndSystemPrompt(unittest.TestCase):
    """Test suite verifying Concept Mirroring prompt design and heuristic extraction."""

    def setUp(self):
        self.refiner = QARefiner()

    def test_system_prompt_concept_mirroring_mandate(self):
        """Verify system prompt mandates Concept Mirroring and bans canned greetings."""
        prompt = self.refiner.SYSTEM_PROMPT

        self.assertIn("CONCEPT MIRRORING", prompt)
        self.assertIn("NGHIÊM CẤM 100% các câu chào hỏi xã giao, sáo rỗng", prompt)
        self.assertIn("Ý tưởng của bạn rất hay/thú vị/cuốn hút!", prompt)
        self.assertIn("DEEP NARRATIVE PROBE", prompt)
        self.assertIn("1 ĐẾN 2 CÂU HỎI GỢI MỞ SÂU SẮC", prompt)
        self.assertIn("ngoặc đơn", prompt)
        self.assertIn("[READY]", prompt)
        self.assertIn("QUY TẮC LỊCH SỬ VIỆT NAM", prompt)
        self.assertIn("QUY TẮC BẢN QUYỀN", prompt)

        # Check absence of banned European realism persona
        lower_prompt = prompt.lower()
        self.assertNotIn("đại tiểu thuyết gia", lower_prompt)
        self.assertNotIn("đại văn hào", lower_prompt)
        self.assertNotIn("đại biên tập viên", lower_prompt)

    def test_concept_mirroring_historical_figures(self):
        """Verify heuristic generator mirrors historical figures and formats contrasting options."""
        history = [{"role": "user", "content": "Tôi muốn viết truyện về Trần Hưng Đạo và hội thề Sát Thát"}]
        output = self.refiner.generate_fallback_question(history)

        self.assertIn("Trần Hưng Đạo", output)
        self.assertIn("Chính sử", output)
        self.assertIn("Dã sử", output)
        self.assertIn("(", output)
        self.assertIn(")", output)
        # Ensure no boilerplate canned greeting
        self.assertNotIn("Ý tưởng của bạn rất hay", output)
        self.assertNotIn("Chào bạn", output)

    def test_concept_mirroring_scifi_cyberpunk(self):
        """Verify heuristic generator mirrors cyberpunk setting and constructs contrasting choices."""
        history = [{"role": "user", "content": "Ý tưởng Cyberpunk Sài Gòn 2099 với thám tử tư điều tra trí tuệ nhân tạo"}]
        output = self.refiner.generate_fallback_question(history)

        self.assertIn("Sài Gòn 2099", output)
        self.assertIn("(", output)
        self.assertIn(")", output)
        self.assertNotIn("Ý tưởng của bạn rất hay", output)

    def test_concept_mirroring_xianxia_fantasy(self):
        """Verify heuristic generator mirrors cultivation fantasy tropes."""
        history = [{"role": "user", "content": "Truyện tiên hiệp tu chân có pháp bảo và cấm địa cổ xưa"}]
        output = self.refiner.generate_fallback_question(history)

        self.assertTrue("tu chân" in output or "tiên hiệp" in output or "pháp bảo" in output)
        self.assertIn("(", output)
        self.assertIn(")", output)
        self.assertNotIn("Chào bạn", output)

    def test_concept_mirroring_proper_noun_extraction(self):
        """Verify proper noun extraction from general input without predefined keywords."""
        history = [{"role": "user", "content": "Một câu chuyện về chàng trai tên Minh Phong gánh vác lời nguyền"}]
        output = self.refiner.generate_fallback_question(history)

        self.assertIn("Minh Phong", output)
        self.assertIn("(", output)
        self.assertIn(")", output)

    def test_isekai_am_thuc_does_not_trigger_scifi(self):
        """Verify input 'Isekai ẩm thực' does NOT trigger sci-fi questions."""
        history = [{"role": "user", "content": "Isekai ẩm thực"}]
        output = self.refiner.generate_fallback_question(history)

        self.assertNotIn("Sài Gòn 2099", output)
        self.assertNotIn("thế giới tương lai", output)
        self.assertNotIn("thế giới neon", output)
        self.assertNotIn("công nghệ", output)
        self.assertNotIn("trí tuệ nhân tạo", output)

    def test_hai_tam_hon_co_don_does_not_trigger_scifi(self):
        """Verify input 'Hai tâm hồn cô đơn tại Hà Nội' does NOT trigger sci-fi questions."""
        history = [{"role": "user", "content": "Hai tâm hồn cô đơn tại Hà Nội"}]
        output = self.refiner.generate_fallback_question(history)

        self.assertNotIn("Sài Gòn 2099", output)
        self.assertNotIn("thế giới tương lai", output)
        self.assertNotIn("thế giới neon", output)
        self.assertNotIn("công nghệ", output)
        self.assertNotIn("trí tuệ nhân tạo", output)

    def test_ke_ve_does_not_extract_nhan_vat_ke(self):
        """Verify input 'Kể về một người thợ rèn' does NOT extract 'nhân vật Kể'."""
        history = [{"role": "user", "content": "Kể về một người thợ rèn"}]
        output = self.refiner.generate_fallback_question(history)

        self.assertNotIn("nhân vật Kể", output)
        self.assertIn("cốt truyện của bạn", output)

    def test_tham_tu_tu_triggers_thriller_not_scifi(self):
        """Verify input 'Thám tử tư điều tra vụ án' triggers detective/thriller question, not sci-fi."""
        history = [{"role": "user", "content": "Thám tử tư điều tra vụ án"}]
        output = self.refiner.generate_fallback_question(history)

        self.assertIn("Vụ án và nút thắt suy luận", output)
        self.assertNotIn("Sài Gòn 2099", output)
        self.assertNotIn("thế giới tương lai", output)
        self.assertNotIn("thế giới neon", output)


class TestApiChatInterviewEndpoint(unittest.TestCase):
    """Test suite for FastAPI /api/chat-interview endpoint integration."""

    @classmethod
    def setUpClass(cls):
        from fastapi.testclient import TestClient
        from main import app
        cls.client = TestClient(app)

    @patch("main.get_qa_refiner")
    def test_api_chat_interview_success(self, mock_get_qa):
        """Verify successful response structure with message, reply, and is_ready flag."""
        mock_qa = MagicMock()
        mock_qa.chat_interview.return_value = "Phản hồi câu hỏi mở sâu sắc [READY]"
        mock_qa.last_model_used = "qwen/qwen3.8-27b"
        mock_get_qa.return_value = mock_qa

        payload = {
            "chat_history": [{"role": "user", "content": "Đại chiến Bạch Đằng"}]
        }
        res = self.client.post("/api/chat-interview", json=payload)

        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["message"], "Phản hồi câu hỏi mở sâu sắc")
        self.assertEqual(data["reply"], "Phản hồi câu hỏi mở sâu sắc")
        self.assertTrue(data["is_ready"])
        self.assertEqual(data["detected_mode"], "qwen/qwen3.8-27b")

    @patch("main.get_qa_refiner")
    def test_api_chat_interview_with_user_input(self, mock_get_qa):
        """Verify optional user_input field is properly merged into history."""
        mock_qa = MagicMock()
        mock_qa.chat_interview.return_value = "Phản hồi tiếp theo"
        mock_get_qa.return_value = mock_qa

        payload = {
            "user_input": "Ý tưởng thứ hai",
            "chat_history": []
        }
        res = self.client.post("/api/chat-interview", json=payload)

        self.assertEqual(res.status_code, 200)
        # Check that qa.chat_interview was called with the user message in history
        call_args = mock_qa.chat_interview.call_args[0][0]
        self.assertEqual(call_args[-1]["content"], "Ý tưởng thứ hai")

    @patch("main.get_qa_refiner")
    def test_api_chat_interview_503_error_on_exhaustion(self, mock_get_qa):
        """Verify that when all models/keys fail, endpoint returns HTTP 503 structured JSON."""
        mock_qa = MagicMock()
        mock_qa.chat_interview.side_effect = RuntimeError("Tất cả mô hình và khóa API đều thất bại: 429 Too Many Requests")
        mock_get_qa.return_value = mock_qa

        payload = {
            "chat_history": [{"role": "user", "content": "Thử nghiệm lỗi máy chủ"}]
        }
        res = self.client.post("/api/chat-interview", json=payload)

        self.assertEqual(res.status_code, 503)
        data = res.json()
        self.assertEqual(data["status"], "error")
        self.assertIn("Dịch vụ AI tạm thời gián đoạn", data["message"])
        self.assertIn("429 Too Many Requests", data["detail"])
        self.assertEqual(data["retry_after"], 5)
        self.assertFalse(data["is_ready"])


if __name__ == "__main__":
    unittest.main()
