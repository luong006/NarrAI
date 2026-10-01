## 2026-10-01T06:38:53Z
You are worker_m2_fix2.
Your working directory is: e:\NarrAI\.agents\teamwork\worker_m2_fix2
You exclusively own and modify:
1. backend/services/ontology.py
2. backend/tests/test_round6_historical_copyright.py

MANDATORY FIRST STEP:
Read e:\NarrAI\.agents\teamwork\ORIGINAL_REQUEST.md before doing any work.
Also read e:\NarrAI\.agents\teamwork\reviewer_m2_fix\handoff.md, especially Section 5, which provides the exact regex fix and test cases to eliminate false positives on legitimate historical narratives.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Detailed Tasks:
1. In backend/services/ontology.py:
   - For `vo_nguyen_giap` defeat_regex (line ~494): Replace the broad unconstrained `.*?` pattern with the proximity-constrained and clause-specific regex from Section 5 of reviewer_m2_fix/handoff.md:
     ```python
     "defeat_regex": (
         r"(?i)(?:"
         r"\b(?:võ\s+nguyên\s+giáp|đại\s+tướng\s+(?:võ\s+nguyên\s+)?giáp)\b"
         r"(?:\s+(?:đã|lại|bị|phải|chịu|suýt|hoàn\s+toàn|cay\s+đắng|ở|tại\s+điện\s+biên(?:\s+phủ)?)){0,4}\s+"
         r"(?:thua\s+trận|thất\s+bại|bại\s+trận|đại\s+bại|đầu\s+hàng|thua\s+cuộc|quy\s+hàng|thua\s+(?:quân\s+)?pháp|thua\s+đờ\s+cát|bị\s+(?:bắt|giết|tiêu\s+diệt))\b"
         r"|"
         r"\b(?:võ\s+nguyên\s+giáp|đại\s+tướng\s+(?:võ\s+nguyên\s+)?giáp)\b.*?\b(?:đầu\s+hàng|quy\s+hàng|chịu\s+thua)\s+(?:quân\s+)?(?:pháp|đờ\s+cát|de\s+castries)\b"
         r"|"
         r"\b(?:thất\s+bại|sự\s+thất\s+bại|việc\s+đầu\s+hàng)\s+của\s+(?:đại\s+tướng\s+)?(?:võ\s+nguyên\s+)?giáp\b"
         r")"
     )
     ```
   - For `ngo_quyen` defeat_regex (line ~223): Replace with the proximity-constrained regex from Section 5 of reviewer_m2_fix/handoff.md:
     ```python
     "defeat_regex": (
         r"(?i)(?:"
         r"\b(?:ngô\s+quyền|tiền\s+ngô\s+vương)\b"
         r"(?:\s+(?:đã|lại|bị|phải|chịu|suýt|hoàn\s+toàn|cay\s+đắng|ở|trên\s+sông\s+bạch\s+đằng)){0,4}\s+"
         r"(?:bại\s+trận|thua\s+trận|thất\s+bại|đại\s+bại|đầu\s+hàng|bị\s+lưu\s+hoằng\s+tháo\s+(?:bắt|giết)|thua\s+quân\s+nam\s+hán)\b"
         r"|"
         r"\b(?:ngô\s+quyền|tiền\s+ngô\s+vương)\b.*?\b(?:đầu\s+hàng|quy\s+hàng|chịu\s+thua)\s+(?:quân\s+)?(?:nam\s+hán|lưu\s+hoằng\s+tháo)\b"
         r"|"
         r"\b(?:thất\s+bại|sự\s+thất\s+bại)\s+của\s+(?:ngô\s+quyền|tiền\s+ngô\s+vương)\b"
         r")"
     )
     ```
2. In backend/tests/test_round6_historical_copyright.py:
   - Add unit tests validating that legitimate historical narratives celebrating General Giap and Ngo Quyen are NOT falsely flagged:
     - `test_legitimate_vo_nguyen_giap_victory_not_flagged`:
       - "Đại tướng Võ Nguyên Giáp chỉ huy quân dân ta đánh bại thực dân Pháp, buộc tướng Đờ Cát phải đầu hàng."
       - "Đại tướng Võ Nguyên Giáp chỉ huy chiến dịch Điện Biên Phủ toàn thắng, toàn bộ cứ điểm quân Pháp bị tiêu diệt."
       - "Dưới sự lãnh đạo của Đại tướng Võ Nguyên Giáp, quân Pháp chuốc lấy thất bại nặng nề tại Điện Biên Phủ."
     - `test_legitimate_ngo_quyen_victory_not_flagged`:
       - "Ngô Quyền cắm cọc nhọn trên sông Bạch Đằng, quân Nam Hán thất bại thảm hại."
3. Verification:
   - Run: python -m unittest backend/tests/test_adversarial_m2_historical_invariants.py
   - Run: python -m unittest backend/tests/test_round6_historical_copyright.py
   Confirm 100% pass for both distortion rejection AND legitimate victory retention!

When complete, write your handoff report to:
e:\NarrAI\.agents\teamwork\worker_m2_fix2\handoff.md
And send a message back to the orchestrator.
