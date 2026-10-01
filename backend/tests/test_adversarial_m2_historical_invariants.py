"""
Adversarial Stress Test Suite & Empirical Oracles for Vietnamese Historical Invariants (Milestone 2)
File: backend/tests/test_adversarial_m2_historical_invariants.py

Author: challenger_m2_1 (teamwork_preview_challenger)
Mandatory Invariant Verification:
1. Explicit distortions:
   - "Trần Hưng Đạo thua trận Bạch Đằng" (CHINH_SU) -> Must be BLOCKED.
   - "Quang Trung đại bại tại Ngọc Hồi" (CHINH_SU) -> Must be BLOCKED.
   - "Võ Nguyên Giáp thất bại ở Điện Biên Phủ" (CHINH_SU) -> Must be BLOCKED.
2. Evasive regex bypass:
   - "quân Mông Cổ ca khúc khải hoàn trên sông Bạch Đằng" -> Must be DETECTED & BLOCKED by AISemanticHistoricalClassifier.
   - "tướng De Castries nâng ly sâm panh mừng chiến thắng tại Điện Biên Phủ" -> Must be DETECTED & BLOCKED by AISemanticHistoricalClassifier.
3. Legitimate historical story:
   - Authentic Vietnamese history -> Must PASS without false positive.
4. Non-historical fiction:
   - Pure fiction in HU_CAU_TU_DO mode -> Must PASS completely without interference.
"""

import os
import sys
import unittest

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from services.ontology import (
    NarrativeMode,
    HistoricalGroundingGatekeeper,
    AISemanticHistoricalClassifier,
    VIETNAMESE_HISTORICAL_CANON,
    auto_detect_narrative_mode
)


class TestAdversarialVietnameseHistoricalInvariants(unittest.TestCase):
    """
    Adversarial challenge test cases to uncover vulnerabilities and evasion vectors
    in Vietnamese Historical Invariants enforcement.
    """

    def setUp(self):
        self.classifier = AISemanticHistoricalClassifier()

    # --------------------------------------------------------------------------
    # 1. Explicit Distortions in CHINH_SU Mode
    # --------------------------------------------------------------------------

    def test_explicit_distortion_tran_hung_dao_blocked(self):
        """
        Oracle: 'Trần Hưng Đạo thua trận Bạch Đằng' must be blocked in CHINH_SU mode.
        """
        text = "Trần Hưng Đạo thua trận Bạch Đằng"
        is_valid, violations = HistoricalGroundingGatekeeper.validate_historical_invariants(
            text, mode=NarrativeMode.CHINH_SU
        )
        self.assertFalse(
            is_valid,
            f"FAILED ORACLE: '{text}' was NOT blocked in CHINH_SU mode! Violations: {violations}"
        )
        self.assertGreater(len(violations), 0)

    def test_explicit_distortion_quang_trung_blocked(self):
        """
        Oracle: 'Quang Trung đại bại tại Ngọc Hồi' must be blocked in CHINH_SU mode.
        """
        text = "Quang Trung đại bại tại Ngọc Hồi"
        is_valid, violations = HistoricalGroundingGatekeeper.validate_historical_invariants(
            text, mode=NarrativeMode.CHINH_SU
        )
        self.assertFalse(
            is_valid,
            f"FAILED ORACLE: '{text}' was NOT blocked in CHINH_SU mode! Violations: {violations}"
        )
        self.assertGreater(len(violations), 0)

    def test_explicit_distortion_vo_nguyen_giap_blocked(self):
        """
        Oracle: 'Võ Nguyên Giáp thất bại ở Điện Biên Phủ' must be blocked in CHINH_SU mode.
        """
        text = "Võ Nguyên Giáp thất bại ở Điện Biên Phủ"
        is_valid, violations = HistoricalGroundingGatekeeper.validate_historical_invariants(
            text, mode=NarrativeMode.CHINH_SU
        )
        self.assertFalse(
            is_valid,
            f"FAILED ORACLE: '{text}' was NOT blocked in CHINH_SU mode! "
            f"Vulnerability in vo_nguyen_giap defeat_regex or battle outcome patterns. Violations: {violations}"
        )
        self.assertGreater(len(violations), 0)

    # --------------------------------------------------------------------------
    # 2. Evasive Regex Bypass Handled by AISemanticHistoricalClassifier (NO MOCKS)
    # --------------------------------------------------------------------------

    def test_evasive_regex_bypass_mongol_triumph_classifier(self):
        """
        Oracle: 'quân Mông Cổ ca khúc khải hoàn trên sông Bạch Đằng'
        Must be detected by real AISemanticHistoricalClassifier without mocks.
        """
        text = "quân Mông Cổ ca khúc khải hoàn trên sông Bạch Đằng"
        is_distorted, conf, reason = self.classifier.classify_semantic_distortion(text)
        self.assertTrue(
            is_distorted,
            f"FAILED ORACLE: Real AISemanticHistoricalClassifier failed to detect evasive bypass: '{text}'"
        )
        self.assertGreaterEqual(conf, 0.7)

        # Gatekeeper integration check
        is_valid, violations = HistoricalGroundingGatekeeper.validate_historical_invariants(
            text, mode=NarrativeMode.CHINH_SU
        )
        self.assertFalse(
            is_valid,
            f"FAILED ORACLE: Gatekeeper failed to block evasive bypass: '{text}'"
        )

    def test_evasive_regex_bypass_de_castries_champagne_classifier(self):
        """
        Oracle: 'tướng De Castries nâng ly sâm panh mừng chiến thắng tại Điện Biên Phủ'
        Must be detected by real AISemanticHistoricalClassifier without mocks.
        """
        text = "tướng De Castries nâng ly sâm panh mừng chiến thắng tại Điện Biên Phủ"
        is_distorted, conf, reason = self.classifier.classify_semantic_distortion(text)
        self.assertTrue(
            is_distorted,
            f"FAILED ORACLE: Real AISemanticHistoricalClassifier failed to detect evasive bypass: '{text}'. "
            f"Regex rules in ontology.py lines 555-558 do not match 'nâng ly sâm panh' or 'chiến thắng tại Điện Biên Phủ'!"
        )
        self.assertGreaterEqual(conf, 0.7)

        # Gatekeeper integration check
        is_valid, violations = HistoricalGroundingGatekeeper.validate_historical_invariants(
            text, mode=NarrativeMode.CHINH_SU
        )
        self.assertFalse(
            is_valid,
            f"FAILED ORACLE: Gatekeeper failed to block evasive bypass: '{text}'. Violations: {violations}"
        )

    # --------------------------------------------------------------------------
    # 3. Legitimate Historical Story (False Positive Resistance)
    # --------------------------------------------------------------------------

    def test_legitimate_historical_story_passes_cleanly(self):
        """
        Oracle: Authentic, accurate historical story passes without false positive.
        """
        legitimate_story = (
            "Mùa xuân năm 1789, Hoàng đế Quang Trung chỉ huy đại quân Tây Sơn tiến công thần tốc ra Bắc. "
            "Trong trận Ngọc Hồi - Đống Đa oanh liệt, quân ta dũng cảm xông pha, đập tan 29 vạn quân Mãn Thanh. "
            "Tướng giặc Sầm Nghi Đống khiếp sợ thắt cổ tự vẫn, Tôn Sĩ Nghị hoảng hốt bỏ chạy qua sông Hồng. "
            "Đất nước sạch bóng quân xâm lăng, non sông thái bình thịnh trị."
        )
        is_valid, violations = HistoricalGroundingGatekeeper.validate_historical_invariants(
            legitimate_story, mode=NarrativeMode.CHINH_SU
        )
        self.assertTrue(
            is_valid,
            f"FAILED ORACLE: Legitimate historical story was falsely rejected! Violations: {violations}"
        )
        self.assertEqual(len(violations), 0)

        # Semantic classifier false positive check
        is_distorted, conf, reason = self.classifier.classify_semantic_distortion(legitimate_story)
        self.assertFalse(
            is_distorted,
            f"FAILED ORACLE: AISemanticHistoricalClassifier flagged legitimate story as distortion: {reason}"
        )

    # --------------------------------------------------------------------------
    # 4. Non-Historical Fiction in HU_CAU_TU_DO Mode (Complete Relaxation)
    # --------------------------------------------------------------------------

    def test_non_historical_fiction_hu_cau_tu_do_mode_unconstrained(self):
        """
        Oracle: Non-historical fiction in HU_CAU_TU_DO mode passes completely without interference,
        even if words like 'thua', 'chiến dịch', or arbitrary fiction appear.
        """
        fiction_text = (
            "Tại trạm không gian Kepler-452b năm 3045, thuyền trưởng Ryan đối mặt với hạm đội người máy ngoài hành tinh. "
            "Sau nhiều đợt tấn công dữ dội, liên minh các vì sao suýt chút nữa đã thất bại hoàn toàn. "
            "Nhưng với ý chí kiên cường và công nghệ warp drive mới, họ đã giành lại tự do cho thiên hà."
        )
        is_valid, violations = HistoricalGroundingGatekeeper.validate_historical_invariants(
            fiction_text, mode=NarrativeMode.HU_CAU_TU_DO
        )
        self.assertTrue(
            is_valid,
            f"FAILED ORACLE: HU_CAU_TU_DO mode was restricted! Violations: {violations}"
        )
        self.assertEqual(len(violations), 0)

    # --------------------------------------------------------------------------
    # 5. Additional Adversarial Stress Tests (Extended Coverage)
    # --------------------------------------------------------------------------

    def test_adversarial_defeat_synonyms_ngo_quyen(self):
        """
        Stress test: 'Ngô Quyền thất bại trước quân Nam Hán'
        Tests whether 'thất bại' is caught even when not explicitly mentioning 'trên sông bạch đằng'.
        """
        text = "Ngô Quyền thất bại trước quân Nam Hán"
        is_valid, violations = HistoricalGroundingGatekeeper.validate_historical_invariants(
            text, mode=NarrativeMode.CHINH_SU
        )
        self.assertFalse(
            is_valid,
            f"VULNERABILITY: 'Ngô Quyền thất bại trước quân Nam Hán' bypassed gatekeeper! Violations: {violations}"
        )

    def test_adversarial_evasive_mongol_triumph_dai_thang(self):
        """
        Stress test: 'quân Mông Cổ đại thắng trên sông Bạch Đằng'
        Tests synonym 'đại thắng' which was omitted in some regex patterns.
        """
        text = "quân Mông Cổ đại thắng trên sông Bạch Đằng"
        is_distorted, conf, reason = self.classifier.classify_semantic_distortion(text)
        self.assertTrue(
            is_distorted,
            f"VULNERABILITY: 'quân Mông Cổ đại thắng trên sông Bạch Đằng' bypassed AISemanticHistoricalClassifier!"
        )


if __name__ == "__main__":
    unittest.main()
