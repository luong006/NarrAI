# DISPATCH

## 2026-10-01T06:26:06Z
You are worker_m2_fix.
Your working directory is: e:\NarrAI\.agents\teamwork\worker_m2_fix
You exclusively own and modify:
1. backend/services/ontology.py
2. backend/tests/test_round6_historical_copyright.py

MANDATORY FIRST STEP:
Read e:\NarrAI\.agents\teamwork\ORIGINAL_REQUEST.md before doing any work.
Also read e:\NarrAI\.agents\teamwork\challenger_m2_1\handoff.md which contains the exact diagnosis and suggested code fixes from the challenger.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Detailed Tasks:
1. In backend/services/ontology.py:
   - In VIETNAMESE_HISTORICAL_CANON["vo_nguyen_giap"]["defeat_regex"]:
     Expand the pattern to cleanly match phrases like "Võ Nguyên Giáp thất bại ở Điện Biên Phủ", "thất bại tại/ở", "thua trận", "đầu hàng", "bại trận". For example:
     r"(?i)\b(?:võ\s+nguyên\s+giáp|đại\s+tướng\s+giáp)\b.*?\b(?:thua\s+trận|thất\s+bại|bại\s+trận|đầu\s+hàng)\b"
     Also ensure BATTLE_OUTCOME_DISTORTION_PATTERNS or canon patterns cover "Võ Nguyên Giáp thất bại ở Điện Biên Phủ".
   - In AISemanticHistoricalClassifier.classify_semantic_distortion:
     Ensure Pattern 2 handles evasive bypasses such as "tướng De Castries nâng ly sâm panh mừng chiến thắng tại Điện Biên Phủ". Support phrases like "nâng ly", "sâm panh|champagne", and "chiến\s+thắng\s+(?:tại|ở)?\s*(?:điện\s+biên|mường\s+thanh)".
     Verify both Pattern 2a and 2b in AISemanticHistoricalClassifier.
2. In backend/tests/test_round6_historical_copyright.py:
   - In TestRound6AISemanticHistoricalClassifier (lines 245-295):
     REMOVE all `with patch.object(classifier, "classify_semantic_distortion", ...):` mocks! The tests must run against the real implementation of AISemanticHistoricalClassifier.
     Make sure test phrases include both the required prompt ("tướng De Castries nâng ly sâm panh mừng chiến thắng tại Điện Biên Phủ") and existing test vectors, verifying real detection.
3. Verification:
   - Run: python -m unittest backend/tests/test_adversarial_m2_historical_invariants.py
     Verify that ALL 7 tests in this suite pass 100%!
   - Run: python -m unittest backend/tests/test_round6_historical_copyright.py
     Verify that all tests in this suite pass 100% without any mock bypass.
   - Run: python -m unittest backend/tests/test_round6_e2e_integration.py
     Verify no regressions in integration tests.

When finished, write your handoff report to:
e:\NarrAI\.agents\teamwork\worker_m2_fix\handoff.md
And send a message back to the orchestrator summarizing your changes and verification results.
