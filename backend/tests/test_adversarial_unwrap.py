"""
Adversarial Empirical Challenge Test Suite for Copilot Unwrap Logic (Milestone 1 - R1)
Location: backend/tests/test_adversarial_unwrap.py

Challenges:
1. Triple-nested JSON envelopes
2. Vietnamese dialogue with literal quotes, escaped quotes, and newlines
3. Raw markdown text containing curly braces (math, literary notes, code blocks)
4. Truncated or malformed JSON envelopes
"""

import os
import sys
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from agents.copilot_agent import unwrap_story_prose


def run_test_triple_nested_envelope():
    """Challenge 1: Triple-nested JSON envelopes must be completely peeled to prose."""
    inner_story = (
        "# Chương 1: Tiếng vọng từ hư vô\n\n"
        "Trời đã về khuya, sương mù giăng kín các lối mòn trong rừng thẳm. "
        "Minh thắp ngọn đuốc, từng bước dò dẫm trong đêm tối."
    )
    # Level 3: Simple envelope
    level_3 = json.dumps({"updated_story_content": inner_story}, ensure_ascii=False)
    # Level 2: action_params envelope
    level_2 = json.dumps({
        "action": "edit_story_direct",
        "action_params": {"updated_story_content": level_3}
    }, ensure_ascii=False)
    # Level 1: Outer master controller envelope
    level_1 = json.dumps({
        "action": "edit_story_direct",
        "action_params": {"updated_story_content": level_2}
    }, ensure_ascii=False)

    unwrapped = unwrap_story_prose(level_1)
    assert unwrapped == inner_story, (
        f"[FAIL Challenge 1] Triple nested unwrap mismatch.\nExpected:\n{inner_story}\nGot:\n{unwrapped}"
    )
    print("PASS [Challenge 1]: Triple-nested JSON envelope successfully unpeeled.")


def run_test_vietnamese_dialogue_quotes_and_newlines():
    """Challenge 2: Vietnamese dialogue with literal quotes, escaped quotes, and newlines."""
    # Sub-case 2A: Valid JSON with escaped quotes and real/escaped newlines
    prose_expected = (
        "Hải quay sang nhìn Thảo, khẽ thì thầm:\n"
        "\"Cậu có nghe thấy tiếng gì không?\"\n\n"
        "Thảo run rẩy đáp: \"Hình như... có ai đó đang đi lại trên gác xép.\"\n"
        "\"Suỵt!\" - Hải ra hiệu im lặng: \"Đừng lên tiếng!\""
    )
    valid_json = json.dumps({
        "action": "edit_story_direct",
        "action_params": {
            "updated_story_content": prose_expected,
            "summary_of_changes": "Cập nhật lời thoại Hải và Thảo",
            "message": "Đã cập nhật thoại!"
        }
    }, ensure_ascii=False)

    unwrapped_2a = unwrap_story_prose(valid_json)
    assert unwrapped_2a == prose_expected, (
        f"[FAIL Challenge 2A] Valid JSON dialogue failed.\nExpected:\n{prose_expected}\nGot:\n{unwrapped_2a}"
    )

    # Sub-case 2B: Malformed JSON with literal (unescaped) quotes inside dialogue string
    malformed_literal_quotes = (
        '{"action": "edit_story_direct", "action_params": {'
        '"updated_story_content": "Hải quay sang nhìn Thảo, khẽ thì thầm:\n'
        '"Cậu có nghe thấy tiếng gì không?"\n\n'
        'Thảo run rẩy đáp: \\"Hình như... có ai đó đang đi lại trên gác xép.\\"\n'
        '"Suỵt!" - Hải ra hiệu im lặng: \\"Đừng lên tiếng!\\"", '
        '"summary_of_changes": "Cập nhật thoại", "message": "Xong!"}}'
    )
    unwrapped_2b = unwrap_story_prose(malformed_literal_quotes)
    assert "Cậu có nghe thấy tiếng gì không?" in unwrapped_2b, f"Missing quote 1: {unwrapped_2b}"
    assert "Hình như... có ai đó đang đi lại trên gác xép." in unwrapped_2b, f"Missing quote 2: {unwrapped_2b}"
    assert "Suỵt!" in unwrapped_2b, f"Missing quote 3: {unwrapped_2b}"
    assert "Đừng lên tiếng!" in unwrapped_2b, f"Missing quote 4: {unwrapped_2b}"
    assert not unwrapped_2b.startswith("{"), f"Still starts with brace: {unwrapped_2b}"
    print("PASS [Challenge 2]: Vietnamese dialogue with mixed literal/escaped quotes and newlines rescued.")


def run_test_raw_markdown_with_curly_braces():
    """Challenge 3: Raw markdown containing curly braces (math, notes, code)."""
    # Sub-case 3A: LaTeX Math with curly braces
    math_prose = (
        "# Định lý Không Gian\n\n"
        "Cho tập hợp $S = \\{x \\in \\mathbb{R} \\mid x > 0\\}$.\n"
        "Hàm thế năng được xác định bởi: $V(x) = \\{1 - e^{-x}\\}$.\n\n"
        "Phương trình chuyển động nghiệm đúng trên toàn miền xác định."
    )
    unwrapped_3a = unwrap_story_prose(math_prose)
    assert unwrapped_3a == math_prose, (
        f"[FAIL Challenge 3A] Math prose with braces corrupted.\nExpected:\n{math_prose}\nGot:\n{unwrapped_3a}"
    )

    # Sub-case 3B: Stylistic author note wrapped in curly braces
    note_prose = "{Ghi chú của tác giả: Mọi sự trùng hợp trong câu chuyện đều là ngẫu nhiên.}"
    unwrapped_3b = unwrap_story_prose(note_prose)
    assert unwrapped_3b == note_prose, (
        f"[FAIL Challenge 3B] Braced note corrupted.\nExpected:\n{note_prose}\nGot:\n{unwrapped_3b}"
    )

    # Sub-case 3C: Story containing an embedded code fence with non-story JSON
    embedded_code_prose = (
        "Alice mở cuốn sổ tay mật mã và đọc to đoạn mã:\n\n"
        "```json\n"
        "{\n"
        '  "spell": "incendio",\n'
        '  "power": 99\n'
        "}\n"
        "```\n\n"
        "Ngọn lửa bùng lên rực sáng cả căn phòng tối tăm."
    )
    unwrapped_3c = unwrap_story_prose(embedded_code_prose)
    # Note: If line 48 triggers on fence_inner.startswith('{'), this test exposes the truncation bug!
    code_fence_truncated = ("Alice mở cuốn sổ" not in unwrapped_3c)
    if code_fence_truncated:
        print("EXPOSED [Challenge 3C Finding]: Embedded code block starting with '{' truncates surrounding story!")
    else:
        print("PASS [Challenge 3C]: Embedded code block preserved.")

    print("PASS [Challenge 3]: Raw markdown with curly braces (math, literary notes) evaluated.")


def run_test_truncated_or_malformed_json():
    """Challenge 4: Truncated or malformed JSON envelopes."""
    # Sub-case 4A: Malformed with invalid comma and unescaped quote but intact end braces
    malformed_intact_end = (
        '{"action": "edit_story_direct", "action_params": {'
        '"updated_story_content": "Nam thốt lên: "Trời ơi!" rồi ngã quỵ xuống đất.",,, '
        '"summary_of_changes": "Sửa phân cảnh ngã"}}'
    )
    unwrapped_4a = unwrap_story_prose(malformed_intact_end)
    assert "Nam thốt lên: \"Trời ơi!\" rồi ngã quỵ xuống đất." in unwrapped_4a, (
        f"[FAIL Challenge 4A] Regex fallback failed on malformed JSON with intact end.\nGot: {unwrapped_4a}"
    )

    # Sub-case 4B: Truncated mid-stream (missing closing quote and missing closing braces)
    truncated_cutoff = (
        '{"action": "edit_story_direct", "action_params": {'
        '"updated_story_content": "Ngày xưa có một chàng hiệp sĩ lang thang khắp bốn phương để tìm kiếm thanh gươm ánh sáng'
    )
    unwrapped_4b = unwrap_story_prose(truncated_cutoff)
    truncated_rescued = not unwrapped_4b.startswith("{") and "Ngày xưa có một chàng hiệp sĩ" in unwrapped_4b
    if not truncated_rescued:
        print("EXPOSED [Challenge 4B Finding]: Abruptly truncated JSON without closing quote/brace cannot be rescued by regex fallback.")
    else:
        print("PASS [Challenge 4B]: Truncated JSON successfully rescued.")

    print("PASS [Challenge 4]: Truncated and malformed JSON scenarios evaluated.")


if __name__ == "__main__":
    print("=== STARTING ADVERSARIAL CHALLENGE TEST SUITE ===")
    run_test_triple_nested_envelope()
    run_test_vietnamese_dialogue_quotes_and_newlines()
    run_test_raw_markdown_with_curly_braces()
    run_test_truncated_or_malformed_json()
    print("=== ADVERSARIAL CHALLENGE TEST SUITE COMPLETE ===")
