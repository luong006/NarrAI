import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from agents.copilot_agent import unwrap_story_prose, CopilotAgent


def test_single_level_json():
    raw = '{"action": "edit_story_direct", "action_params": {"updated_story_content": "Ngày xửa ngày xưa có một chàng hiệp sĩ."}}'
    unwrapped = unwrap_story_prose(raw)
    assert unwrapped == "Ngày xửa ngày xưa có một chàng hiệp sĩ.", f"Failed: {unwrapped}"
    print("PASS: test_single_level_json")


def test_root_level_key():
    raw = '{"updated_story_content": "Chương mới bắt đầu trong đêm trăng sáng."}'
    unwrapped = unwrap_story_prose(raw)
    assert unwrapped == "Chương mới bắt đầu trong đêm trăng sáng.", f"Failed: {unwrapped}"
    print("PASS: test_root_level_key")


def test_nested_json():
    inner = '{"updated_story_content": "Đoạn văn đa tầng lồng nhau.\\n\\nTiếp tục câu chuyện."}'
    import json
    outer = json.dumps({"action": "edit_story_direct", "action_params": {"updated_story_content": inner}})
    unwrapped = unwrap_story_prose(outer)
    expected = "Đoạn văn đa tầng lồng nhau.\n\nTiếp tục câu chuyện."
    assert unwrapped == expected, f"Failed: got {repr(unwrapped)}, expected {repr(expected)}"
    print("PASS: test_nested_json")


def test_escaped_newlines_unconditional():
    # Contains both literal \n and real \n
    raw = 'Dòng mở đầu thực tế.\nĐoạn văn tiếp theo\\n\\nKết thúc chương.'
    unwrapped = unwrap_story_prose(raw)
    expected = 'Dòng mở đầu thực tế.\nĐoạn văn tiếp theo\n\nKết thúc chương.'
    assert unwrapped == expected, f"Failed: got {repr(unwrapped)}, expected {repr(expected)}"
    print("PASS: test_escaped_newlines_unconditional")


def test_dialogue_with_quotes_regex_fallback():
    # Invalid JSON due to unescaped double quotes inside dialogue
    raw = '{"updated_story_content": "Lan nhìn Nam rồi nói: "Chúng ta phải đi ngay!" trước khi trời sáng.", "summary_of_changes": "Cập nhật lời thoại của Lan"}'
    unwrapped = unwrap_story_prose(raw)
    assert "Chúng ta phải đi ngay!" in unwrapped, f"Failed: {unwrapped}"
    assert "Lan nhìn Nam rồi nói:" in unwrapped, f"Failed: {unwrapped}"
    assert not unwrapped.startswith("{"), f"Failed: still starts with brace {unwrapped}"
    print("PASS: test_dialogue_with_quotes_regex_fallback")


def test_markdown_codeblock():
    raw = """```json
{
  "updated_story_content": "Nội dung nằm trọn trong markdown fence codeblock."
}
```"""
    unwrapped = unwrap_story_prose(raw)
    assert unwrapped == "Nội dung nằm trọn trong markdown fence codeblock.", f"Failed: {unwrapped}"
    print("PASS: test_markdown_codeblock")


def test_plain_markdown_prose_undamaged():
    prose = "# Chương 1: Khởi Đầu\n\nTrời thu se se lạnh. Nam bước đi trên con đường rợp bóng lá vàng.\n\n\"Chào bạn!\" một giọng nói vang lên."
    unwrapped = unwrap_story_prose(prose)
    assert unwrapped == prose, f"Failed: got {repr(unwrapped)}, expected {repr(prose)}"
    print("PASS: test_plain_markdown_prose_undamaged")


def test_is_direct_edit_request_keywords():
    agent = CopilotAgent.__new__(CopilotAgent)
    # Test extended keywords
    assert agent._is_direct_edit_request("tôi muốn một mở đầu khác") is True
    assert agent._is_direct_edit_request("sửa bản thảo này giúp tôi") is True
    assert agent._is_direct_edit_request("hãy chỉnh đoạn kết kịch tính hơn") is True
    assert agent._is_direct_edit_request("thay cái kết buồn bằng kết vui") is True
    assert agent._is_direct_edit_request("đổi tên nhân vật chính") is True
    assert agent._is_direct_edit_request("viết lại toàn bộ chương 1") is True
    assert agent._is_direct_edit_request("soạn lại phần mở bài") is True
    # Test non-edit requests
    assert agent._is_direct_edit_request("bạn thấy cốt truyện này thế nào?") is False
    assert agent._is_direct_edit_request("chào bạn") is False
    print("PASS: test_is_direct_edit_request_keywords")


def test_conversational_idioms_excluded():
    agent = CopilotAgent.__new__(CopilotAgent)
    # Common conversational questions that previously triggered false positives
    assert agent._is_direct_edit_request("Thay vì đi vào hang, nhân vật nên làm gì?") is False
    assert agent._is_direct_edit_request("Đổi lại là bạn thì bạn sẽ chọn ai?") is False
    assert agent._is_direct_edit_request("Bớt giận đi bạn ơi") is False
    assert agent._is_direct_edit_request("Thay cho lời tạm biệt, họ bắt tay nhau.") is False
    assert agent._is_direct_edit_request("Xóa tan mọi nghi ngờ trong lòng") is False
    # Legitimate edits must still be recognized
    assert agent._is_direct_edit_request("hãy thay đổi kết truyện") is True
    assert agent._is_direct_edit_request("bớt đoạn đối thoại dài dòng") is True
    assert agent._is_direct_edit_request("xóa đoạn 2 giúp tôi") is True
    print("PASS: test_conversational_idioms_excluded")


def test_operator_precedence_in_direct_edit():
    import json
    agent = CopilotAgent.__new__(CopilotAgent)
    
    class MockLLM:
        def chat(self, messages, **kwargs):
            return json.dumps({
                "updated_story_content": "Đoạn văn mới được chỉnh sửa chi tiết.",
                "summary_of_changes": "Đã sửa đoạn mở đầu kịch tính hơn.",
                "message": "Tôi đã sửa trực tiếp mở đầu bản thảo cho bạn!"
            }, ensure_ascii=False)
            
    agent.llm = MockLLM()
    res = agent._perform_direct_manuscript_edit("sửa mở đầu", "Cũ...")
    assert res is not None, "Direct edit returned None!"
    assert res["action"] == "edit_story_direct"
    assert res["action_params"]["summary_of_changes"] == "Đã sửa đoạn mở đầu kịch tính hơn."
    assert res["action_params"]["message"] == "Tôi đã sửa trực tiếp mở đầu bản thảo cho bạn!"
    assert res["action_params"]["updated_story_content"] == "Đoạn văn mới được chỉnh sửa chi tiết."
    print("PASS: test_operator_precedence_in_direct_edit")


def test_direct_edit_short_prose():
    import json
    agent = CopilotAgent.__new__(CopilotAgent)
    
    # Sub-case A: Short prose inside JSON schema (<= 50 chars)
    class MockLLMShortJSON:
        def chat(self, messages, **kwargs):
            return json.dumps({
                "updated_story_content": "Chỉ một câu ngắn gọn.",
                "summary_of_changes": "Rút gọn",
                "message": "Đã rút gọn!"
            }, ensure_ascii=False)
            
    agent.llm = MockLLMShortJSON()
    res_a = agent._perform_direct_manuscript_edit("rút gọn", "Cũ dài...")
    assert res_a is not None, "Failed on short prose inside JSON"
    assert res_a["action_params"]["updated_story_content"] == "Chỉ một câu ngắn gọn."
    
    # Sub-case B: Short prose directly returned as plain text (<= 50 chars)
    class MockLLMShortText:
        def chat(self, messages, **kwargs):
            return "Chỉ một câu ngắn gọn không qua JSON."
            
    agent.llm = MockLLMShortText()
    res_b = agent._perform_direct_manuscript_edit("viết ngắn", "Cũ...")
    assert res_b is not None, "Failed on short plain text prose"
    assert res_b["action_params"]["updated_story_content"] == "Chỉ một câu ngắn gọn không qua JSON."
    print("PASS: test_direct_edit_short_prose")


def test_master_controller_root_normalization():
    import json
    agent = CopilotAgent.__new__(CopilotAgent)
    
    # Master controller returns root updated_story_content without action_params wrapping
    class MockLLMController:
        def chat(self, messages, **kwargs):
            return json.dumps({
                "thought": "Biên tập trực tiếp bản thảo",
                "action": "edit_story_direct",
                "updated_story_content": '{"updated_story_content": "Nội dung truyện chuẩn từ root controller."}'
            }, ensure_ascii=False)
            
    agent.llm = MockLLMController()
    res = agent.process_event("USER_CHAT", json.dumps({"user_message": "hỏi thăm"}))
    assert res["action"] == "edit_story_direct"
    assert "action_params" in res
    assert res["action_params"]["updated_story_content"] == "Nội dung truyện chuẩn từ root controller."
    print("PASS: test_master_controller_root_normalization")


def test_safe_code_fence_unwrapping():
    # Embedded markdown code block starting with { inside story text
    prose_with_code = (
        "Alice mở cuốn sổ tay mật mã và đọc to đoạn mã:\n\n"
        "```json\n"
        "{\n"
        '  "spell": "incendio",\n'
        '  "power": 99\n'
        "}\n"
        "```\n\n"
        "Ngọn lửa bùng lên rực sáng cả căn phòng tối tăm."
    )
    unwrapped = unwrap_story_prose(prose_with_code)
    assert "Alice mở cuốn sổ tay mật mã" in unwrapped, f"Story beginning wiped! Got: {unwrapped}"
    assert "Ngọn lửa bùng lên rực sáng" in unwrapped, f"Story ending wiped! Got: {unwrapped}"
    assert "spell" in unwrapped
    print("PASS: test_safe_code_fence_unwrapping")


def test_truncated_stream_regex_recovery():
    # Abruptly cutoff JSON stream lacking closing quotation and closing brace
    truncated_cutoff = (
        '{"action": "edit_story_direct", "action_params": {'
        '"updated_story_content": "Ngày xưa có một chàng hiệp sĩ lang thang khắp bốn phương để tìm kiếm thanh gươm ánh sáng'
    )
    unwrapped = unwrap_story_prose(truncated_cutoff)
    assert not unwrapped.startswith("{"), f"Failed to peel JSON: {unwrapped}"
    assert "Ngày xưa có một chàng hiệp sĩ lang thang" in unwrapped, f"Failed recovery: {unwrapped}"
    print("PASS: test_truncated_stream_regex_recovery")


def test_database_quarantine_guard_neutralization():
    # Simulate DB quarantine logic from backend/main.py
    def simulate_quarantine(result):
        if result.get("action") == "edit_story_direct":
            if "action_params" not in result or not isinstance(result.get("action_params"), dict):
                result["action_params"] = {}
            params = result["action_params"]
            if "updated_story_content" not in params and "updated_story_content" in result:
                params["updated_story_content"] = result["updated_story_content"]
            updated_content = params.get("updated_story_content")
            if updated_content:
                clean_prose = unwrap_story_prose(updated_content)
                params["updated_story_content"] = clean_prose
                updated_content = clean_prose

                is_raw_json = (
                    updated_content.strip().startswith("{")
                    or '"updated_story_content"' in updated_content
                    or '"action":' in updated_content
                )
                if is_raw_json:
                    clean_prose = unwrap_story_prose(updated_content)
                    if not clean_prose.strip().startswith("{") and '"updated_story_content"' not in clean_prose:
                        updated_content = clean_prose
                        params["updated_story_content"] = clean_prose
                    else:
                        updated_content = None
                        params["updated_story_content"] = None
                        params["message"] = "Hệ thống phát hiện lỗi định dạng bản thảo và đã ngăn chặn ghi đè để bảo vệ tác phẩm của bạn."
            return updated_content, params
        return None, {}

    # Case A: Corrupted JSON that cannot be unwrapped
    corrupted_result = {
        "action": "edit_story_direct",
        "action_params": {
            "updated_story_content": '{"broken_raw_json": { "nested": 123 }}'
        }
    }
    content, params = simulate_quarantine(corrupted_result)
    assert content is None, "Quarantine should have blocked DB write!"
    assert params["updated_story_content"] is None, "Quarantine should have neutralized updated_story_content!"
    assert "ngăn chặn ghi đè" in params["message"], "Quarantine message missing!"

    # Case B: Valid story wrapped in JSON
    valid_result = {
        "action": "edit_story_direct",
        "action_params": {
            "updated_story_content": '{"updated_story_content": "Văn bản hợp lệ sau khi giải nén."}'
        }
    }
    content, params = simulate_quarantine(valid_result)
    assert content == "Văn bản hợp lệ sau khi giải nén."
    assert params["updated_story_content"] == "Văn bản hợp lệ sau khi giải nén."
    print("PASS: test_database_quarantine_guard_neutralization")


if __name__ == "__main__":
    test_single_level_json()
    test_root_level_key()
    test_nested_json()
    test_escaped_newlines_unconditional()
    test_dialogue_with_quotes_regex_fallback()
    test_markdown_codeblock()
    test_plain_markdown_prose_undamaged()
    test_is_direct_edit_request_keywords()
    test_conversational_idioms_excluded()
    test_operator_precedence_in_direct_edit()
    test_direct_edit_short_prose()
    test_master_controller_root_normalization()
    test_safe_code_fence_unwrapping()
    test_truncated_stream_regex_recovery()
    test_database_quarantine_guard_neutralization()
    print("\nALL 15 COPILOT UNWRAP TESTS PASSED!")
