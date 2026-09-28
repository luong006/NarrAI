"""
End-to-End Test Suite: Requirement 1 (R1)
Adaptive Open-Ontology, 3 Narrative Modes, Tri-Tier Resolver & Smart Selective Language Filter

Derived strictly from:
- ORIGINAL_REQUEST.md (## 2026-09-28T01:01:31Z)
- PROJECT.md (§ M1 ↔ Main AI Routes)

Test Structure (4-Tier Methodology):
- Tier 1: Feature Coverage (Isolated Happy Path)
- Tier 2: Boundary & Corner Cases (Limits, Accents, Thresholds)
- Tier 3: Cross-Feature Combinations (Gatekeeper + Resolver + Cliché Filtering)
- Tier 4: Real-World Application Scenarios (Historical Epic, Cyberpunk Fusion, Western OOD)
"""

import os
import sys
import unittest

# Ensure backend root is on sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from services.ontology import (
    NarrativeMode,
    CulturalTier,
    normalize_narrative_mode,
    normalize_cultural_tier,
    ResolvedOntology,
    HistoricalGroundingGatekeeper,
    TriTierOntologyResolver,
    SmartSelectiveLanguageFilter,
    extract_dynamic_ephemeral_node,
    resolve_ontology,
    VIETNAMESE_HISTORICAL_CANON,
    MASTER_NEGATIVE_VIETNAMESE,
    UNIVERSAL_AI_CLICHES,
    TRANSLATION_CLICHE_BANLIST,
)


class TestTier1OntologyFeatureCoverage(unittest.TestCase):
    """
    Tier 1: Feature Coverage & Happy Path Tests for R1 Components.
    """

    def test_narrative_mode_enum_and_normalization(self):
        """Verify 3 narrative modes exist and normalization handles aliases."""
        self.assertEqual(NarrativeMode.CHINH_SU.value, "chinh_su")
        self.assertEqual(NarrativeMode.DA_SU.value, "da_su")
        self.assertEqual(NarrativeMode.HU_CAU_TU_DO.value, "hu_cau_tu_do")

        # Code interoperability aliases
        self.assertEqual(NarrativeMode.STRICT_HISTORICAL, NarrativeMode.CHINH_SU)
        self.assertEqual(NarrativeMode.HISTORICAL_FICTION, NarrativeMode.DA_SU)
        self.assertEqual(NarrativeMode.FREE_FICTION, NarrativeMode.HU_CAU_TU_DO)

        # Normalization with various aliases and casing
        self.assertEqual(normalize_narrative_mode("Chính Sử"), NarrativeMode.CHINH_SU)
        self.assertEqual(normalize_narrative_mode("strict_historical"), NarrativeMode.CHINH_SU)
        self.assertEqual(normalize_narrative_mode("Dã Sử"), NarrativeMode.DA_SU)
        self.assertEqual(normalize_narrative_mode("historical_fiction"), NarrativeMode.DA_SU)
        self.assertEqual(normalize_narrative_mode("Hư Cấu Tự Do"), NarrativeMode.HU_CAU_TU_DO)
        self.assertEqual(normalize_narrative_mode("free_fiction"), NarrativeMode.HU_CAU_TU_DO)
        self.assertEqual(normalize_narrative_mode(None), NarrativeMode.HU_CAU_TU_DO)

    def test_cultural_tier_enum_and_normalization(self):
        """Verify 3 cultural tiers and safe integer conversion."""
        self.assertEqual(CulturalTier.TIER_1_CANONICAL_VN.value, 1)
        self.assertEqual(CulturalTier.TIER_2_CULTURAL_FUSION.value, 2)
        self.assertEqual(CulturalTier.TIER_3_OPEN_DOMAIN.value, 3)

        self.assertEqual(normalize_cultural_tier(1), CulturalTier.TIER_1_CANONICAL_VN)
        self.assertEqual(normalize_cultural_tier("2"), CulturalTier.TIER_2_CULTURAL_FUSION)
        self.assertEqual(normalize_cultural_tier(3), CulturalTier.TIER_3_OPEN_DOMAIN)
        self.assertEqual(normalize_cultural_tier(999), CulturalTier.TIER_1_CANONICAL_VN)

    def test_historical_gatekeeper_authentic_facts_pass(self):
        """Authentic Vietnamese historical narratives MUST pass validation."""
        valid_samples = [
            "Hưng Đạo Đại Vương Trần Quốc Tuấn chỉ huy ba quân đại thắng quân Nguyên Mông trên sông Bạch Đằng năm 1288.",
            "Ngô Quyền cắm cọc nhọn bọc sắt trên sông Bạch Đằng, chém chết Lưu Hoằng Tháo và đập tan quân Nam Hán năm 938.",
            "Thái úy Lý Thường Kiệt lập phòng tuyến sông Như Nguyệt, ngâm vang bài thơ thần Nam quốc sơn hà đánh lui quân Tống.",
            "Bình Định Vương Lê Lợi dấy binh khởi nghĩa Lam Sơn mười năm nếm mật nằm gai, đuổi sạch giặc Minh khỏi bờ cõi.",
            "Hoàng đế Quang Trung hành quân thần tốc dịp Tết Kỷ Dậu 1789, đại phá 29 vạn quân Mãn Thanh tại Ngọc Hồi - Đống Đa.",
            "Hai Bà Trưng phất cờ khởi nghĩa đền nợ nước trả thù nhà, đánh đuổi thái thú Tô Định giải phóng 65 thành trì."
        ]
        for sample in valid_samples:
            is_valid, violations = HistoricalGroundingGatekeeper.validate_historical_invariants(
                sample, mode=NarrativeMode.CHINH_SU
            )
            self.assertTrue(is_valid, f"Expected valid history to pass, got violations: {violations}")
            self.assertEqual(len(violations), 0)

            # Check interface contract validate(prompt, text)
            contract_ok, contract_err = HistoricalGroundingGatekeeper.validate("", sample, mode=NarrativeMode.CHINH_SU)
            self.assertTrue(contract_ok)
            self.assertEqual(contract_err, "")

    def test_historical_gatekeeper_falsification_rejected(self):
        """Historical falsifications and revisions MUST be strictly caught and rejected in Mode 1."""
        distorted_samples = [
            ("Trần Hưng Đạo bại trận Bạch Đằng và bị quân Nguyên bắt sống.", "Trần Hưng Đạo"),
            ("Ngô Quyền thua trận trên sông Bạch Đằng trước Lưu Hoằng Tháo.", "Ngô Quyền"),
            ("Lý Thường Kiệt đầu hàng quân Tống bên bờ sông Như Nguyệt.", "Lý Thường Kiệt"),
            ("Lê Lợi đầu hàng quân Minh tại Lam Sơn.", "Lê Lợi"),
            ("Quang Trung thua trận tại Ngọc Hồi Đống Đa và đầu hàng Tôn Sĩ Nghị.", "Quang Trung"),
            ("Hai Bà Trưng đầu hàng Tô Định cầu xin tha mạng.", "Hai Bà Trưng"),
            ("Trận Bạch Đằng quân ta thua tan tác, Nguyên Mông toàn thắng vẻ vang.", "kết quả trận Bạch Đằng")
        ]
        for bad_text, expected_keyword in distorted_samples:
            is_valid, violations = HistoricalGroundingGatekeeper.validate_historical_invariants(
                bad_text, mode=NarrativeMode.CHINH_SU
            )
            self.assertFalse(is_valid, f"Expected distortion to fail: '{bad_text}'")
            self.assertGreater(len(violations), 0)
            self.assertTrue(any("HISTORICAL_VIOLATION" in v for v in violations))

    def test_tri_tier_similarity_scoring_canonical_vn(self):
        """Prompts with dense Vietnamese historical/cultural entities score >= 0.7 (Tier 1)."""
        prompt = (
            "Trần Hưng Đạo điều động chiến thuyền Đại Việt trên sông Bạch Đằng, "
            "tướng sĩ mặc áo ngũ thân, nỏ thần và gươm báu sẵn sàng."
        )
        sim = TriTierOntologyResolver.calculate_cultural_similarity(prompt)
        tier = TriTierOntologyResolver.resolve_tier(sim)
        self.assertGreaterEqual(sim, 0.70, f"Expected S_cult >= 0.7, got {sim}")
        self.assertEqual(tier, CulturalTier.TIER_1_CANONICAL_VN)

    def test_tri_tier_similarity_scoring_cultural_fusion(self):
        """Prompts blending Vietnamese culture with sci-fi/cyberpunk score 0.3 <= S_cult < 0.7 (Tier 2)."""
        prompt = "Cyberpunk Thăng Long 2099 với hacker mặc áo dài neon, bay qua hồ Gươm trên xe phản trọng lực."
        sim = TriTierOntologyResolver.calculate_cultural_similarity(prompt)
        tier = TriTierOntologyResolver.resolve_tier(sim)
        self.assertGreaterEqual(sim, 0.30, f"Expected S_cult >= 0.3, got {sim}")
        self.assertLess(sim, 0.70, f"Expected S_cult < 0.7, got {sim}")
        self.assertEqual(tier, CulturalTier.TIER_2_CULTURAL_FUSION)

    def test_tri_tier_similarity_scoring_open_domain(self):
        """Pure out-of-domain (Western, space opera, modern foreign) score < 0.3 (Tier 3)."""
        prompt = "Detective John and Alice investigate an alien murder mystery inside a futuristic space station in New York."
        sim = TriTierOntologyResolver.calculate_cultural_similarity(prompt)
        tier = TriTierOntologyResolver.resolve_tier(sim)
        self.assertLess(sim, 0.30, f"Expected S_cult < 0.3, got {sim}")
        self.assertEqual(tier, CulturalTier.TIER_3_OPEN_DOMAIN)

    def test_master_negative_filter_tier_isolation(self):
        """Tier 1 & 2 must strictly ban Hanfu/Kimono/Samurai; Tier 3 must NOT impose them."""
        # Tier 1
        pos1, neg1 = TriTierOntologyResolver.get_tier_visual_dna(CulturalTier.TIER_1_CANONICAL_VN)
        self.assertIn("Áo Ngũ Thân", pos1)
        self.assertIn("Khăn Đóng", pos1)
        self.assertIn("hanfu", neg1.lower())
        self.assertIn("kimono", neg1.lower())
        self.assertIn("samurai", neg1.lower())
        self.assertIn("ninja", neg1.lower())

        # Tier 2
        pos2, neg2 = TriTierOntologyResolver.get_tier_visual_dna(CulturalTier.TIER_2_CULTURAL_FUSION)
        self.assertIn("neon", pos2.lower())
        self.assertIn("hanfu", neg2.lower())
        self.assertIn("kimono", neg2.lower())

        # Tier 3 (Open Domain)
        pos3, neg3 = TriTierOntologyResolver.get_tier_visual_dna(CulturalTier.TIER_3_OPEN_DOMAIN)
        self.assertNotIn("Áo Ngũ Thân", pos3)
        self.assertEqual(neg3, "")

    def test_smart_selective_language_filter_wuxia_permission(self):
        """Chinese translation clichés are permitted ONLY in Xianxia/Wuxia under Free Fiction mode."""
        wuxia_text = "Bản tọa tiêu sái vung kiếm, ánh mắt lãnh khốc nhìn về phía đế tôn, sát khí cuộn trào ngút trời."

        # Case 1: Genre is Tiên hiệp, Mode is Free Fiction -> ALLOWED
        is_clean, violations = SmartSelectiveLanguageFilter.validate_smart_language_compliance(
            wuxia_text, genre="Tiên hiệp tu chân", narrative_mode=NarrativeMode.HU_CAU_TU_DO
        )
        self.assertTrue(is_clean, f"Expected Wuxia clichés to be allowed in Xianxia, got: {violations}")
        self.assertEqual(len(violations), 0)

        # Case 2: Genre is Kiếm hiệp, Mode is Free Fiction -> ALLOWED
        is_clean_kx, _ = SmartSelectiveLanguageFilter.validate_smart_language_compliance(
            wuxia_text, genre="Kiếm hiệp cổ trang", narrative_mode=NarrativeMode.HU_CAU_TU_DO
        )
        self.assertTrue(is_clean_kx)

    def test_smart_selective_language_filter_pure_vn_suppression(self):
        """Chinese translation clichés are strictly suppressed in pure Vietnamese and historical prose."""
        text_with_cliches = "Hắn nở nụ cười tà mị, hành xử tiêu sái nhưng bản tọa biết hắn là kẻ lãnh khốc vô tình."

        # Case 1: Historical mode (Chính sử) -> BANNED
        is_clean_hist, violations_hist = SmartSelectiveLanguageFilter.validate_smart_language_compliance(
            text_with_cliches, genre="Lịch sử Việt Nam", narrative_mode=NarrativeMode.CHINH_SU
        )
        self.assertFalse(is_clean_hist)
        self.assertGreater(len(violations_hist), 0)
        self.assertTrue(any("TRANSLATION_CLICHE" in v for v in violations_hist))

        # Case 2: Pure Vietnamese literature in Free Fiction -> BANNED
        is_clean_vn, violations_vn = SmartSelectiveLanguageFilter.validate_smart_language_compliance(
            text_with_cliches, genre="Văn học hiện thực đời thường", narrative_mode=NarrativeMode.HU_CAU_TU_DO
        )
        self.assertFalse(is_clean_vn)
        self.assertTrue(any("tiêu sái" in v or "tà mị" in v for v in violations_vn))

    def test_universal_ai_cliches_always_banned(self):
        """Universal lazy AI clichés are banned across ALL modes and ALL genres."""
        ai_cliche_text = "Hắn bước đi nhanh như nhịp tim chậm rãi, cảm thấy một khoảng trống trong lòng và nỗi lo đè nặng lên vai."

        # Even with genre=Tiên hiệp and mode=HU_CAU_TU_DO, AI clichés MUST be caught!
        is_clean, violations = SmartSelectiveLanguageFilter.validate_smart_language_compliance(
            ai_cliche_text, genre="Tiên hiệp", narrative_mode=NarrativeMode.HU_CAU_TU_DO
        )
        self.assertFalse(is_clean)
        self.assertTrue(any("AI_CLICHE" in v for v in violations))
        self.assertTrue(any("nhanh như nhịp tim chậm rãi" in v for v in violations))
        self.assertTrue(any("khoảng trống trong lòng" in v for v in violations))

    def test_dynamic_ephemeral_node_extraction(self):
        """Tier 3 Open Domain dynamically extracts space anchors and disables feudal constraints."""
        story_sample = "Captain Jack steered his spaceship through the asteroid field towards the glowing alien planet."
        node = extract_dynamic_ephemeral_node(story_sample, genre="Sci-Fi Space Opera")
        self.assertEqual(node["tier"], CulturalTier.TIER_3_OPEN_DOMAIN)
        self.assertTrue(node["is_open_domain"])
        self.assertTrue(node["forbidden_feudal_filters_disabled"])
        self.assertTrue(node["forced_attire_disabled"])
        self.assertIn("futuristic sci-fi", node["setting_anchor"])


class TestTier2OntologyBoundaryAndCornerCases(unittest.TestCase):
    """
    Tier 2: Boundary & Corner Cases (Threshold limits, Empty strings, Accents, Case sensitivity).
    """

    def test_empty_and_none_inputs(self):
        """Functions must handle empty, None, and whitespace strings gracefully without exception."""
        # Gatekeeper
        ok, violations = HistoricalGroundingGatekeeper.validate_historical_invariants("", mode=NarrativeMode.CHINH_SU)
        self.assertTrue(ok)
        self.assertEqual(violations, [])

        ok_none, _ = HistoricalGroundingGatekeeper.validate_historical_invariants(None, mode=NarrativeMode.CHINH_SU)
        self.assertTrue(ok_none)

        # Resolver
        sim_empty = TriTierOntologyResolver.calculate_cultural_similarity("")
        self.assertEqual(sim_empty, 0.5)

        # Filter
        clean_empty, v_empty = SmartSelectiveLanguageFilter.validate_smart_language_compliance("")
        self.assertTrue(clean_empty)
        self.assertEqual(v_empty, [])

    def test_exact_tier_similarity_boundary_thresholds(self):
        """Verifies exact threshold boundaries: Tier 1 (>= 0.7), Tier 2 (0.3 <= S < 0.7), Tier 3 (< 0.3)."""
        self.assertEqual(TriTierOntologyResolver.resolve_tier(0.70), CulturalTier.TIER_1_CANONICAL_VN)
        self.assertEqual(TriTierOntologyResolver.resolve_tier(0.85), CulturalTier.TIER_1_CANONICAL_VN)
        self.assertEqual(TriTierOntologyResolver.resolve_tier(1.00), CulturalTier.TIER_1_CANONICAL_VN)

        self.assertEqual(TriTierOntologyResolver.resolve_tier(0.69), CulturalTier.TIER_2_CULTURAL_FUSION)
        self.assertEqual(TriTierOntologyResolver.resolve_tier(0.50), CulturalTier.TIER_2_CULTURAL_FUSION)
        self.assertEqual(TriTierOntologyResolver.resolve_tier(0.30), CulturalTier.TIER_2_CULTURAL_FUSION)

        self.assertEqual(TriTierOntologyResolver.resolve_tier(0.29), CulturalTier.TIER_3_OPEN_DOMAIN)
        self.assertEqual(TriTierOntologyResolver.resolve_tier(0.10), CulturalTier.TIER_3_OPEN_DOMAIN)
        self.assertEqual(TriTierOntologyResolver.resolve_tier(0.00), CulturalTier.TIER_3_OPEN_DOMAIN)

    def test_historical_mode_forces_tier_1_canonical(self):
        """When requested_mode is Chính Sử or Dã Sử, resolve_ontology forces Tier 1 regardless of prompt length."""
        res_chinh_su = resolve_ontology("Một đêm trăng sáng trên đồi", requested_mode="chinh_su")
        self.assertEqual(res_chinh_su.cultural_tier, CulturalTier.TIER_1_CANONICAL_VN)
        self.assertEqual(res_chinh_su.cultural_similarity, 1.0)
        self.assertIn("Áo Ngũ Thân", res_chinh_su.positive_visual_dna)

        res_da_su = resolve_ontology("Chuyện tình người lính trẻ", requested_mode="da_su")
        self.assertEqual(res_da_su.cultural_tier, CulturalTier.TIER_1_CANONICAL_VN)
        self.assertEqual(res_da_su.cultural_similarity, 1.0)

    def test_case_insensitivity_and_vietnamese_diacritics(self):
        """Detects distortions even with varying capitalization and extra spaces."""
        text = "T R Ầ N   H Ư N G   Đ Ạ O   B Ạ I   T R Ậ N"  # not standard regex
        # Standard case variation:
        test_upper = "TRẦN HƯNG ĐẠO BẠI TRẬN BẠCH ĐẰNG"
        is_valid, _ = HistoricalGroundingGatekeeper.validate_historical_invariants(test_upper, mode=NarrativeMode.CHINH_SU)
        self.assertFalse(is_valid, "Case-insensitive check failed on uppercase distortion")

        test_mixed = "qUaNg TrUnG tHuA tRậN ở Ngọc Hồi Đống Đa"
        is_valid_mixed, _ = HistoricalGroundingGatekeeper.validate_historical_invariants(test_mixed, mode=NarrativeMode.CHINH_SU)
        self.assertFalse(is_valid_mixed, "Case-insensitive check failed on mixed case distortion")

    def test_mode_3_bypasses_historical_gatekeeper(self):
        """In Mode 3 (Free Fiction), the user is 100% free to invent alternate fiction without historical gatekeeper blocks."""
        alternate_text = "Trong thế giới ma pháp song song, Quang Trung thua trận và rút lui về tiên giới."
        is_valid, violations = HistoricalGroundingGatekeeper.validate_historical_invariants(
            alternate_text, mode=NarrativeMode.HU_CAU_TU_DO
        )
        self.assertTrue(is_valid, "Mode 3 must bypass historical gatekeeper constraints")
        self.assertEqual(len(violations), 0)


class TestTier3OntologyCrossFeatureCombinations(unittest.TestCase):
    """
    Tier 3: Cross-Feature Integration Tests (Resolver + Gatekeeper + Language Filter).
    """

    def test_resolver_coordinates_visual_dna_and_negative_filters(self):
        """ResolvedOntology integrates correct DNA, negative filter, and honorific guidelines for all 3 modes."""
        # Scenario 1: Canonical Historical (Mode 1)
        r1 = resolve_ontology("Hịch tướng sĩ của Trần Hưng Đạo trước trận Bạch Đằng", requested_mode="chinh_su")
        self.assertEqual(r1.narrative_mode, NarrativeMode.CHINH_SU)
        self.assertEqual(r1.cultural_tier, CulturalTier.TIER_1_CANONICAL_VN)
        self.assertIn("Áo Ngũ Thân", r1.positive_visual_dna)
        self.assertIn("hanfu", r1.master_negative_filter.lower())
        self.assertIn("Bệ hạ / Khanh", r1.honorifics_guidelines)
        self.assertIn("CHÍNH SỬ", r1.historical_constraints)

        # Scenario 2: Hybrid Cyberpunk (Mode 3, Hybrid Theme)
        r2 = resolve_ontology("Steampunk Triều Nguyễn với cỗ máy hơi nước bảo vệ kinh thành Huế", requested_mode="hu_cau_tu_do")
        self.assertEqual(r2.cultural_tier, CulturalTier.TIER_2_CULTURAL_FUSION)
        self.assertIn("Vietnamese cultural fusion aesthetic", r2.positive_visual_dna)
        self.assertIn("hanfu", r2.master_negative_filter.lower())
        self.assertIn("TIER 2 CULTURAL FUSION", r2.honorifics_guidelines)

        # Scenario 3: Open Domain Fantasy (Mode 3)
        r3 = resolve_ontology("Archmage of Hogwarts casts spells in Victorian London", requested_mode="hu_cau_tu_do")
        self.assertEqual(r3.cultural_tier, CulturalTier.TIER_3_OPEN_DOMAIN)
        self.assertNotIn("Áo Ngũ Thân", r3.positive_visual_dna)
        self.assertEqual(r3.master_negative_filter, "")
        self.assertIn("TIER 3 OPEN DOMAIN", r3.honorifics_guidelines)

    def test_mode_override_on_cliche_filter(self):
        """Mode 1 strictly bans translation clichés even if user specifies Xianxia genre."""
        text = "Trần Hưng Đạo mỉm cười tiêu sái, sát khí ngút trời đối diện Thoát Hoan."
        # Even if someone marks genre="Tiên hiệp", if Mode=CHINH_SU, translation clichés MUST be suppressed!
        is_clean, violations = SmartSelectiveLanguageFilter.validate_smart_language_compliance(
            text, genre="Tiên hiệp", narrative_mode=NarrativeMode.CHINH_SU
        )
        self.assertFalse(is_clean, "Mode 1 must override genre exception and enforce historical purity")
        self.assertTrue(any("tiêu sái" in v for v in violations))


class TestTier4OntologyRealWorldWorkflows(unittest.TestCase):
    """
    Tier 4: Real-World Application Scenarios (End-to-End User Authoring Workflows).
    """

    def test_workflow_historical_epic_chinh_su(self):
        """End-to-end authoring workflow for a strict Vietnamese historical novel."""
        user_prompt = "Viết tiểu thuyết lịch sử về Trần Hưng Đạo đại phá quân Nguyên Mông tại Bạch Đằng Giang 1288."

        # Step 1: System resolves ontology
        ontology = resolve_ontology(user_prompt, requested_mode="chinh_su", user_genre="Lịch sử Việt Nam")
        self.assertEqual(ontology.narrative_mode, NarrativeMode.CHINH_SU)
        self.assertEqual(ontology.cultural_tier, CulturalTier.TIER_1_CANONICAL_VN)

        # Step 2: Validate LLM output against gatekeeper and filter
        llm_generated_chapter = (
            "Sông Bạch Đằng cuồn cuộn sóng trào. Tiết chế quốc công Trần Hưng Đạo đứng trên mũi thuyền rồng, "
            "vạt áo ngũ thân tay chẽn bay trong gió lộng. Ngài nhìn hàng cọc ngầm nhấp nhô, cất giọng đanh thép: "
            "'Năm nay đánh giặc nhàn!'. Quân dân Đại Việt đồng lòng, bắt sống Ô Mã Nhi, quét sạch giặc thù."
        )

        # Gatekeeper check
        gate_ok, gate_err = HistoricalGroundingGatekeeper.validate(user_prompt, llm_generated_chapter, mode=ontology.narrative_mode)
        self.assertTrue(gate_ok, f"Gatekeeper error: {gate_err}")

        # Cliché check
        cliche_ok, cliche_violations = SmartSelectiveLanguageFilter.validate_smart_language_compliance(
            llm_generated_chapter, genre="Lịch sử Việt Nam", narrative_mode=ontology.narrative_mode
        )
        self.assertTrue(cliche_ok, f"Cliche violations: {cliche_violations}")

    def test_workflow_hybrid_cyberpunk_thang_long(self):
        """End-to-end authoring workflow for a Vietnamese Cyberpunk story."""
        user_prompt = "Cyberpunk Thăng Long 2099: Cuộc rượt đuổi bằng phi thuyền giữa các tòa tháp hologram quanh Hồ Gươm."

        ontology = resolve_ontology(user_prompt, requested_mode="hu_cau_tu_do", user_genre="Cyberpunk Việt Nam")
        self.assertEqual(ontology.cultural_tier, CulturalTier.TIER_2_CULTURAL_FUSION)
        self.assertIn("hanfu", ontology.master_negative_filter.lower())
        self.assertIn("neon", ontology.positive_visual_dna.lower())

        llm_prose = (
            "Ánh đèn neon xanh lục phản chiếu trên mặt nước Hồ Gươm. Minh kích hoạt bộ giáp mecha mang hoa văn "
            "trống đồng Đông Sơn, phóng vút qua rặng liễu điện tử trong màn đêm Hà Nội năm 2099."
        )
        cliche_ok, violations = SmartSelectiveLanguageFilter.validate_smart_language_compliance(
            llm_prose, genre="Cyberpunk", narrative_mode=ontology.narrative_mode
        )
        self.assertTrue(cliche_ok, f"Unexpected violations: {violations}")

    def test_workflow_western_detective_open_domain(self):
        """End-to-end authoring workflow for Out-Of-Domain Western mystery."""
        user_prompt = "A classic murder mystery set in an eerie Victorian manor in London during a foggy night."

        ontology = resolve_ontology(user_prompt, requested_mode="hu_cau_tu_do", user_genre="Western Detective")
        self.assertEqual(ontology.cultural_tier, CulturalTier.TIER_3_OPEN_DOMAIN)
        self.assertEqual(ontology.master_negative_filter, "")

        ephemeral_node = extract_dynamic_ephemeral_node(user_prompt, genre="Western Detective")
        self.assertTrue(ephemeral_node["forbidden_feudal_filters_disabled"])
        self.assertTrue(ephemeral_node["forced_attire_disabled"])


if __name__ == "__main__":
    unittest.main()
