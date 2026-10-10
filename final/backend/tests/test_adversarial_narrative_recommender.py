"""
Empirical Adversarial Test Suite for NarrAI:
Narrative Modes, Cultural Ontology, Recommender MMR/MAB, and Open Messenger.

Targeting:
1. Historical Falsification & Narrative Modes (Mode 1 Chính Sử vs Mode 2 Dã Sử vs Mode 3 Hư Cấu Tự Do)
2. Cultural Similarity Threshold Boundaries (0.70 vs 0.69, 0.30 vs 0.29) & Master Negative Filter
3. Cliché Bypass Attempts (Chinese translation clichés in pure VN vs Xianxia/Wuxia, Universal AI clichés)
4. Recommender MMR Diversity (Echo-Chamber Prevention) & Multi-Armed Bandit Cold-Start (15% Exploration)
5. Open Messenger Directory Search & 1-1 Chat Edge Cases
6. Adversarial Attack Probing (Multiline evasion, spacing variations, boundary anomalies)
"""

import math
import json
import os
import sys
import unittest
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Ensure backend root is on sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.models import (
    Base,
    User,
    SocialPost,
    PostInteraction,
    UserInterestProfile,
    Conversation,
    ConversationParticipant,
    ChatMessage
)

from services.ontology import (
    NarrativeMode,
    CulturalTier,
    normalize_narrative_mode,
    normalize_cultural_tier,
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

from services.recommender_service import (
    VECTOR_DIM,
    DECAY_LAMBDA_PER_DAY,
    MMR_LAMBDA,
    BANDIT_EXPLORATION_RATIO,
    COLD_START_VIEW_THRESHOLD,
    SIGNAL_WEIGHTS,
    W_COSINE,
    W_AFFINITY,
    W_FRESHNESS,
    W_QUALITY,
    normalize_vector,
    cosine_similarity,
    generate_concept_vector,
    extract_sentiment_and_entities,
    get_or_create_user_profile,
    apply_exponential_decay,
    update_user_interest_on_interaction,
    HybridRecommenderEngine,
    get_feed,
    publish_post,
    record_interaction,
    get_post_details
)

from services.messenger_service import (
    sanitize_message_text,
    search_users,
    get_or_create_conversation,
    send_message,
    get_conversation_messages,
    list_conversations,
    get_total_unread_count
)


# ==============================================================================
# 1. ADVERSARIAL HISTORICAL FALSIFICATION & NARRATIVE MODES
# ==============================================================================

class TestAdversarialHistoricalModes(unittest.TestCase):
    """
    Adversarially attacks the Historical Grounding Gatekeeper under all 3 Narrative Modes.
    """

    def test_mode1_chinh_su_blocks_all_national_hero_reversals(self):
        """
        Mode 1 (Chính Sử): Gatekeeper MUST catch every distortion, defeat assertion,
        or slander against all 6 inviolable national heroes.
        """
        hero_distortion_payloads = [
            # Hai Bà Trưng
            ("Hai Bà Trưng đầu hàng Tô Định sau thất bại nặng nề.", "hai_ba_trung"),
            ("Trưng Trắc dâng sớ quy hàng quân Đông Hán.", "hai_ba_trung"),
            ("Hai Bà Trưng phản bội nghĩa sĩ và bán nước cầu vinh.", "hai_ba_trung"),
            # Ngô Quyền
            ("Ngô Quyền bại trận trên sông Bạch Đằng năm 938.", "ngo_quyen"),
            ("Tiền Ngô Vương bị Lưu Hoằng Tháo giết trên sông Bạch Đằng.", "ngo_quyen"),
            ("Ngô Quyền đầu hàng quân Nam Hán.", "ngo_quyen"),
            # Lý Thường Kiệt
            ("Lý Thường Kiệt bại trận trước quân Tống.", "ly_thuong_kiet"),
            ("Lý Thường Kiệt đầu hàng quân Tống trên sông Như Nguyệt.", "ly_thuong_kiet"),
            ("Thái úy Lý Thường Kiệt thua Quách Quỳ tại trận Như Nguyệt.", "ly_thuong_kiet"),
            # Trần Hưng Đạo
            ("Trần Hưng Đạo bại trận Bạch Đằng năm 1288.", "tran_hung_dao"),
            ("Trần Quốc Tuấn đầu hàng quân Nguyên Mông.", "tran_hung_dao"),
            ("Hưng Đạo Đại Vương chui ống đồng trốn chạy.", "tran_hung_dao"),
            ("Trần Quốc Tuấn bị Thoát Hoan bắt sống.", "tran_hung_dao"),
            # Lê Lợi
            ("Lê Lợi đầu hàng quân Minh ở Lam Sơn.", "le_loi"),
            ("Bình Định Vương bị Liễu Thăng bắt tại Chi Lăng.", "le_loi"),
            ("Lê Lợi thất bại hoàn toàn trước Vương Thông.", "le_loi"),
            # Quang Trung
            ("Quang Trung đầu hàng quân Thanh mùng 5 Tết.", "quang_trung"),
            ("Nguyễn Huệ thua Tôn Sĩ Nghị tại Ngọc Hồi.", "quang_trung"),
            ("Hoàng đế Quang Trung thất bại ở Đống Đa.", "quang_trung"),
        ]

        for payload, hero_key in hero_distortion_payloads:
            is_valid, violations = HistoricalGroundingGatekeeper.validate_historical_invariants(
                payload, mode=NarrativeMode.CHINH_SU
            )
            self.assertFalse(
                is_valid,
                f"[Mode 1 FALSIFICATION PASSED - CRITICAL BUG]: Payload '{payload}' was not caught!"
            )
            self.assertGreater(len(violations), 0)
            self.assertTrue(
                any("HISTORICAL_VIOLATION" in v for v in violations),
                f"Violation must cite HISTORICAL_VIOLATION: {violations}"
            )

    def test_mode1_chinh_su_blocks_major_battle_reversals(self):
        """Mode 1: Gatekeeper must block battle reversals even without explicit hero names."""
        battle_distortions = [
            "Trận Bạch Đằng quân ta thua tan tác, xác chất thành núi.",
            "Trận Bạch Đằng Đại Việt thất bại trước hạm đội địch.",
            "Trận Bạch Đằng Nguyên Mông toàn thắng thu phục phương Nam.",
            "Trận Như Nguyệt quân ta thua tan tành.",
            "Trận Ngọc Hồi Quang Trung thua chạy về phương Nam.",
            "Khởi nghĩa Lam Sơn bị quân Minh tiêu diệt hoàn toàn.",
        ]
        for b_payload in battle_distortions:
            is_valid, violations = HistoricalGroundingGatekeeper.validate_historical_invariants(
                b_payload, mode=NarrativeMode.CHINH_SU
            )
            self.assertFalse(
                is_valid,
                f"[Mode 1 BATTLE FALSIFICATION PASSED - CRITICAL BUG]: '{b_payload}' was not caught!"
            )
            self.assertGreater(len(violations), 0)

    def test_mode1_chinh_su_allows_valid_history_and_praise(self):
        """Mode 1: Authentic victories and praising text must NEVER be falsely blocked."""
        valid_history = [
            "Trần Hưng Đạo ba lần đại thắng quân Nguyên Mông, ghi danh sử sách.",
            "Quang Trung hành quân thần tốc, đại phá 29 vạn quân Mãn Thanh.",
            "Lý Thường Kiệt chặn đứng giặc Tống bên sông Như Nguyệt.",
            "Ngô Quyền cắm cọc ngầm bọc sắt trên sông Bạch Đằng tiêu diệt quân Nam Hán.",
            "Lê Lợi gian khổ nếm mật nằm gai mười năm lãnh đạo khởi nghĩa Lam Sơn toàn thắng.",
            "Hai Bà Trưng phất cờ khởi nghĩa Mê Linh, đuổi thái thú Tô Định chạy về nước."
        ]
        for text in valid_history:
            is_valid, violations = HistoricalGroundingGatekeeper.validate_historical_invariants(
                text, mode=NarrativeMode.CHINH_SU
            )
            self.assertTrue(is_valid, f"[Mode 1 FALSE POSITIVE]: Valid history '{text}' was blocked! Violations: {violations}")
            self.assertEqual(len(violations), 0)

    def test_mode2_da_su_blocks_macro_distortion_allows_micro_fiction(self):
        """
        Mode 2 (Dã Sử):
        - Fictional micro-stories around soldiers, couples, and secret missions are ALLOWED.
        - Macro historical distortion of national heroes is STILL BLOCKED.
        """
        # Allowed micro-fiction
        allowed_micro = (
            "Một người lính cấm vệ quân vô danh tên là Vũ thầm yêu cô gái gánh nước bên bờ sông Lam. "
            "Chàng cùng nghĩa quân theo chủ tướng Lê Lợi tham gia chiến dịch Chi Lăng Xương Giang."
        )
        ok_micro, viol_micro = HistoricalGroundingGatekeeper.validate_historical_invariants(
            allowed_micro, mode=NarrativeMode.DA_SU
        )
        self.assertTrue(ok_micro, f"Dã Sử should allow micro-fiction. Got: {viol_micro}")

        # Blocked macro distortion
        blocked_macro = (
            "Trong một diễn biến dã sử bí mật, Trần Hưng Đạo bại trận Bạch Đằng và đầu hàng giặc."
        )
        ok_macro, viol_macro = HistoricalGroundingGatekeeper.validate_historical_invariants(
            blocked_macro, mode=NarrativeMode.DA_SU
        )
        self.assertFalse(ok_macro, "Dã Sử MUST NOT allow macro distortion of Trần Hưng Đạo!")
        self.assertGreater(len(viol_macro), 0)

    def test_mode3_hu_cau_tu_do_complete_relaxation(self):
        """
        Mode 3 (Hư Cấu Tự Do): Complete semantic relaxation.
        Alternate universe, sci-fi, or fantasy twists are 100% permitted.
        """
        fantasy_payloads = [
            "Trong vũ trụ ma pháp song song, Trần Hưng Đạo bại trận Bạch Đằng trước chúa tể bóng tối ngoài hành tinh.",
            "Tại thế giới cyberpunk 2099, Quang Trung thua trận tại Ngọc Hồi Đống Đa trước binh đoàn robot hủy diệt.",
            "Trận Bạch Đằng quân ta thua trước quái vật Kraken thần thoại cổ đại."
        ]
        for f_payload in fantasy_payloads:
            ok, viol = HistoricalGroundingGatekeeper.validate_historical_invariants(
                f_payload, mode=NarrativeMode.HU_CAU_TU_DO
            )
            self.assertTrue(
                ok,
                f"[Mode 3 VIOLATION - RIGIDITY BUG]: Mode 3 should allow free fiction! Blocked: {f_payload}"
            )
            self.assertEqual(len(viol), 0)


# ==============================================================================
# 2. CULTURAL SIMILARITY THRESHOLD BOUNDARIES & MASTER NEGATIVES
# ==============================================================================

class TestAdversarialCulturalSimilarityAndMasterNegative(unittest.TestCase):
    """
    Stress-tests threshold boundaries: 0.70 vs 0.69, 0.30 vs 0.29,
    and Master Negative filter enforcement.
    """

    def test_boundary_tier1_vs_tier2_exact_thresholds(self):
        """
        Exact threshold boundary test:
        - S_cult >= 0.70 -> Tier 1 (Canonical Vietnamese)
        - S_cult = 0.699999 -> Tier 2 (Cultural Fusion)
        - S_cult = 0.69 -> Tier 2 (Cultural Fusion)
        """
        self.assertEqual(TriTierOntologyResolver.resolve_tier(0.70), CulturalTier.TIER_1_CANONICAL_VN)
        self.assertEqual(TriTierOntologyResolver.resolve_tier(0.7001), CulturalTier.TIER_1_CANONICAL_VN)
        self.assertEqual(TriTierOntologyResolver.resolve_tier(1.0), CulturalTier.TIER_1_CANONICAL_VN)

        self.assertEqual(TriTierOntologyResolver.resolve_tier(0.699999), CulturalTier.TIER_2_CULTURAL_FUSION)
        self.assertEqual(TriTierOntologyResolver.resolve_tier(0.69), CulturalTier.TIER_2_CULTURAL_FUSION)
        self.assertEqual(TriTierOntologyResolver.resolve_tier(0.50), CulturalTier.TIER_2_CULTURAL_FUSION)

    def test_boundary_tier2_vs_tier3_exact_thresholds(self):
        """
        Exact threshold boundary test:
        - S_cult = 0.30 -> Tier 2 (Cultural Fusion)
        - S_cult = 0.299999 -> Tier 3 (Open Domain)
        - S_cult = 0.29 -> Tier 3 (Open Domain)
        - S_cult = 0.0 -> Tier 3 (Open Domain)
        """
        self.assertEqual(TriTierOntologyResolver.resolve_tier(0.30), CulturalTier.TIER_2_CULTURAL_FUSION)
        self.assertEqual(TriTierOntologyResolver.resolve_tier(0.3001), CulturalTier.TIER_2_CULTURAL_FUSION)

        self.assertEqual(TriTierOntologyResolver.resolve_tier(0.299999), CulturalTier.TIER_3_OPEN_DOMAIN)
        self.assertEqual(TriTierOntologyResolver.resolve_tier(0.29), CulturalTier.TIER_3_OPEN_DOMAIN)
        self.assertEqual(TriTierOntologyResolver.resolve_tier(0.0), CulturalTier.TIER_3_OPEN_DOMAIN)

    def test_master_negative_filter_enforcement_by_tier(self):
        """
        Master Negative Filter enforcement:
        - Tier 1: MUST include Hanfu, Kimono, Hanbok, Samurai, Ninja exclusions.
        - Tier 2: MUST STILL include Hanfu, Kimono, Samurai exclusions (protecting hybrid Vietnamese aesthetics).
        - Tier 3: MUST be empty string (no traditional clothing exclusions imposed on Western/Fantasy).
        """
        # Tier 1
        pos1, neg1 = TriTierOntologyResolver.get_tier_visual_dna(CulturalTier.TIER_1_CANONICAL_VN)
        self.assertIn("Áo Ngũ Thân", pos1)
        self.assertIn("hanfu", neg1.lower())
        self.assertIn("kimono", neg1.lower())
        self.assertIn("samurai", neg1.lower())
        self.assertIn("ninja", neg1.lower())
        self.assertIn("hanbok", neg1.lower())

        # Tier 2
        pos2, neg2 = TriTierOntologyResolver.get_tier_visual_dna(CulturalTier.TIER_2_CULTURAL_FUSION)
        self.assertIn("fusion", pos2.lower())
        self.assertIn("hanfu", neg2.lower())
        self.assertIn("kimono", neg2.lower())
        self.assertIn("samurai", neg2.lower())

        # Tier 3
        pos3, neg3 = TriTierOntologyResolver.get_tier_visual_dna(CulturalTier.TIER_3_OPEN_DOMAIN)
        self.assertEqual(neg3, "", "Tier 3 MUST NOT have Master Negative Vietnamese exclusions!")
        self.assertNotIn("Áo Ngũ Thân", pos3)
        self.assertNotIn("hanfu", neg3.lower())

    def test_mode_override_forces_tier1(self):
        """
        When NarrativeMode is CHINH_SU or DA_SU, resolve_ontology must override
        similarity to 1.0 and lock cultural_tier to Tier 1, even if prompt is ambiguous.
        """
        res_chinh_su = resolve_ontology(
            prompt="Một buổi sáng tại bến cảng",
            user_genre="Chính sử",
            requested_mode="CHINH_SU"
        )
        self.assertEqual(res_chinh_su.cultural_tier, CulturalTier.TIER_1_CANONICAL_VN)
        self.assertEqual(res_chinh_su.cultural_similarity, 1.0)
        self.assertIn("hanfu", res_chinh_su.master_negative_filter.lower())

        res_da_su = resolve_ontology(
            prompt="Một quán rượu nhỏ",
            user_genre="Dã sử",
            requested_mode="DA_SU"
        )
        self.assertEqual(res_da_su.cultural_tier, CulturalTier.TIER_1_CANONICAL_VN)
        self.assertEqual(res_da_su.cultural_similarity, 1.0)

    def test_open_domain_story_resolves_to_tier3_without_feudal_filters(self):
        """Tier 3 story (Sci-Fi, Western) must have zero feudal filters."""
        res_ood = resolve_ontology(
            prompt="Detective John investigated the crime scene in downtown Chicago near the subway.",
            user_genre="Western Detective",
            requested_mode="HU_CAU_TU_DO"
        )
        self.assertEqual(res_ood.cultural_tier, CulturalTier.TIER_3_OPEN_DOMAIN)
        self.assertLess(res_ood.cultural_similarity, 0.30)
        self.assertEqual(res_ood.master_negative_filter, "")


# ==============================================================================
# 3. CLICHÉ BYPASS ATTEMPTS & SELECTIVE ENFORCEMENT
# ==============================================================================

class TestAdversarialClicheFilters(unittest.TestCase):
    """
    Adversarially tests SmartSelectiveLanguageFilter:
    - Chinese translation clichés blocked in pure VN and historical prose
    - Chinese clichés allowed in Xianxia / Wuxia under Free Fiction
    - Universal AI clichés unconditionally blocked everywhere
    """

    def test_chinese_cliches_blocked_in_pure_vietnamese(self):
        """Chinese translation clichés MUST be rejected in pure Vietnamese prose."""
        banned_pure_vn_samples = [
            ("Dáng người tiêu sái đứng trước sân trường.", "tiêu sái"),
            ("Hắn nở nụ cười tà mị nhìn vào mắt nàng.", "tà mị"),
            ("Ánh mắt lãnh khốc nhìn về phía đối phương.", "lãnh khốc"),
            ("Bản tọa hôm nay đến đây để lấy mạng ngươi.", "bản tọa"),
            ("Bổn tọa không bao giờ tha thứ cho ngươi.", "bổn tọa"),
            ("Đế tôn uy nghiêm đứng trên đỉnh núi cao.", "đế tôn"),
            ("Hắn không khỏi hít vào một ngụm khí lạnh vì kinh ngạc.", "hít vào một ngụm khí lạnh"),
            ("Sát khí ngút trời bao trùm cả căn phòng.", "sát khí ngút trời"),
            ("Lão phu khuyên các ngươi đừng manh động.", "lão phu"),
            ("Tên tiểu súc sinh kia mau đứng lại!", "tiểu súc sinh"),
            ("Đạo hữu xin hãy dừng bước!", "đạo hữu"),
        ]

        for text, keyword in banned_pure_vn_samples:
            ok, viol = SmartSelectiveLanguageFilter.validate_smart_language_compliance(
                text=text,
                genre="Hiện đại đời thường",
                narrative_mode=NarrativeMode.HU_CAU_TU_DO
            )
            self.assertFalse(
                ok,
                f"[CHINESE CLICHE BYPASS]: Keyword '{keyword}' passed in pure Vietnamese prose! Text: '{text}'"
            )
            self.assertTrue(
                any("TRANSLATION_CLICHE" in v for v in viol),
                f"Violation must cite TRANSLATION_CLICHE: {viol}"
            )

    def test_chinese_cliches_blocked_in_mode1_even_with_wuxia_genre(self):
        """
        Adversarial bypass attempt: User sets genre='tiên hiệp' but chooses Mode 1 (Chính Sử).
        Historical Mode 1 MUST STRICTLY OVERRIDE and ban Chinese translation clichés!
        """
        trick_text = "Trần Hưng Đạo thân hình tiêu sái, ánh mắt lãnh khốc nhìn tướng giặc."
        ok, viol = SmartSelectiveLanguageFilter.validate_smart_language_compliance(
            text=trick_text,
            genre="Tiên hiệp huyền huyễn",
            narrative_mode=NarrativeMode.CHINH_SU
        )
        self.assertFalse(
            ok,
            "[CRITICAL BYPASS IN MODE 1]: Translation clichés allowed in Chính Sử when genre='tiên hiệp'!"
        )
        self.assertTrue(any("tiêu sái" in v or "lãnh khốc" in v for v in viol))

    def test_chinese_cliches_permitted_in_wuxia_free_fiction(self):
        """Chinese translation clichés are allowed in Xianxia/Wuxia under Mode 3 (Hư Cấu Tự Do)."""
        wuxia_text = (
            "Đế tôn khẽ nhếch mép tà mị, thân hình tiêu sái vung kiếm. "
            "Bổn tọa hôm nay sẽ cho đạo hữu thấy sát khí ngút trời của môn phái."
        )
        ok, viol = SmartSelectiveLanguageFilter.validate_smart_language_compliance(
            text=wuxia_text,
            genre="Tiên hiệp kiếm hiệp tu chân",
            narrative_mode=NarrativeMode.HU_CAU_TU_DO
        )
        self.assertTrue(
            ok,
            f"Wuxia under Mode 3 should permit Chinese genre tropes! Got violations: {viol}"
        )
        self.assertEqual(len(viol), 0)

    def test_universal_ai_cliches_unconditionally_banned_everywhere(self):
        """
        Universal AI clichés MUST BE BANNED across ALL modes, ALL genres, and ALL tiers.
        Zero tolerance for lazy AI writing tropes.
        """
        ai_cliche_samples = [
            ("Nhanh như nhịp tim chậm rãi, chàng bước về phía nàng.", "nhanh như nhịp tim chậm rãi"),
            ("Hắn cảm thấy một khoảng trống trong lòng không gì lấp đầy.", "khoảng trống trong lòng"),
            ("Nỗi lo đè nặng lên vai khiến ông thở dốc.", "nỗi lo đè nặng lên vai"),
            ("Nàng thở dài giọng nhẹ giữa đêm đông.", "thở dài giọng nhẹ"),
            ("Trái tim đập thình thịch như muốn nhảy ra khỏi lồng ngực.", "trái tim đập thình thịch"),
            ("Nụ cười bí ẩn nở trên môi vị giáo sư.", "nụ cười bí ẩn nở trên môi"),
            ("Đôi mắt sáng rực lên đầy hứng khởi.", "đôi mắt sáng rực lên"),
            ("Cảm xúc trào dâng trong lồng ngực khi nghe tin.", "cảm xúc trào dâng trong lồng ngực"),
            ("Lòng tôi chợt nặng trĩu những suy tư.", "lòng tôi chợt nặng trĩu"),
            ("Một cảm giác kỳ lạ lan tỏa khắp châu thân.", "một cảm giác kỳ lạ lan tỏa"),
            ("Thế giới dường như dừng lại trong khoảnh khắc ấy.", "thế giới dường như dừng lại"),
            ("Thời gian như ngừng trôi khi hai ánh mắt chạm nhau.", "thời gian như ngừng trôi"),
            ("Tim tôi nhói đau từng cơn quằn quại.", "tim tôi nhói đau"),
            ("Giọng nói ấm áp như nắng mùa xuân vỗ về.", "giọng nói ấm áp như nắng"),
            ("Nỗi buồn man mác dâng trào trong bóng chiều.", "nỗi buồn man mác"),
        ]

        # Test in Tiên hiệp under Mode 3
        for text, trope in ai_cliche_samples:
            ok, viol = SmartSelectiveLanguageFilter.validate_smart_language_compliance(
                text=text,
                genre="Tiên hiệp tu chân",
                narrative_mode=NarrativeMode.HU_CAU_TU_DO
            )
            self.assertFalse(
                ok,
                f"[AI CLICHE LEAK in Wuxia Mode 3]: Trope '{trope}' was not blocked!"
            )
            self.assertTrue(
                any("AI_CLICHE" in v for v in viol),
                f"Violation must cite AI_CLICHE: {viol}"
            )

        # Test in Mode 1 (Chính Sử)
        ok_hist, viol_hist = SmartSelectiveLanguageFilter.validate_smart_language_compliance(
            text="Trần Hưng Đạo thở dài giọng nhẹ, cảm thấy một khoảng trống trong lòng.",
            genre="Chính sử",
            narrative_mode=NarrativeMode.CHINH_SU
        )
        self.assertFalse(ok_hist, "AI clichés must be blocked in Chính Sử!")
        self.assertGreater(len(viol_hist), 0)


# ==============================================================================
# 4. RECOMMENDER MMR DIVERSITY & BANDIT COLD-START STRESS HARNESS
# ==============================================================================

class TestAdversarialRecommenderAndBandit(unittest.TestCase):
    """
    Stress-tests recommendation ranking:
    - MMR diversity prevents single-genre echo chambers
    - Multi-Armed Bandit Thompson Sampling reserves exactly 15% exploration slots
    - Exponential decay converges stably
    """

    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.db = self.Session()

        # Seed test user
        self.user = User(id=1, username="test_reader", full_name="Le Van Test", coins=100)
        self.db.add(self.user)
        self.db.commit()

    def tearDown(self):
        self.db.close()

    def test_mmr_diversity_breaks_single_genre_echo_chamber(self):
        """
        Echo-Chamber Attack:
        We create 15 'Kiếm Hiệp' posts and 5 'Khoa Học Viễn Tưởng' posts.
        Without MMR penalty, all 15 'Kiếm Hiệp' posts would monopolize the top feed.
        With MMR (lambda = 0.70), redundant 'Kiếm Hiệp' posts must be penalized
        and 'Khoa Học Viễn Tưởng' posts MUST be promoted into early feed slots.
        """
        now = datetime.utcnow()
        kh_posts = []
        for i in range(15):
            p = SocialPost(
                id=100 + i,
                user_id=1,
                title=f"Kiếm Hiệp Bí Truyền {i+1}",
                content_snippet=f"Kiếm khí tung hoành chương {i+1}...",
                genre="Kiếm Hiệp",
                views_count=100 + i * 10,
                likes_count=40 + i,
                completion_count=30,
                dwell_time_avg=50.0,
                concept_vector=json.dumps(generate_concept_vector(f"kiem hiep {i}", "Kiếm Hiệp")),
                created_at=now - timedelta(hours=i)
            )
            kh_posts.append(p)

        scifi_posts = []
        for i in range(5):
            p = SocialPost(
                id=200 + i,
                user_id=1,
                title=f"Du Hành Không Gian {i+1}",
                content_snippet=f"Tàu vũ trụ vượt qua tinh vân {i+1}...",
                genre="Khoa Học Viễn Tưởng",
                views_count=80 + i * 5,
                likes_count=35 + i,
                completion_count=25,
                dwell_time_avg=45.0,
                concept_vector=json.dumps(generate_concept_vector(f"sci fi {i}", "Khoa Học Viễn Tưởng")),
                created_at=now - timedelta(hours=i)
            )
            scifi_posts.append(p)

        self.db.add_all(kh_posts + scifi_posts)
        self.db.commit()

        # Score candidates with stage 2
        candidates = kh_posts + scifi_posts
        profile = get_or_create_user_profile(self.db, user_id=1)
        profile.genre_affinity = json.dumps({"Kiếm Hiệp": 5.0})
        self.db.commit()

        scored = HybridRecommenderEngine.stage2_multi_task_ranking(candidates, profile, now=now)

        # Apply Stage 3 MMR reranking
        feed_items = HybridRecommenderEngine.stage3_reranking_and_serendipity(
            scored_candidates=scored,
            all_candidate_posts=candidates,
            feed_limit=10
        )

        genres_in_top_10 = [item["post"].genre for item in feed_items[:10]]

        # Empirical assertion: MMR diversity must prevent Kiếm Hiệp from holding 100% of top 10
        self.assertIn(
            "Khoa Học Viễn Tưởng",
            genres_in_top_10,
            "[ECHO CHAMBER DETECTED]: MMR failed to diversify feed! Top 10 had only: " + str(genres_in_top_10)
        )

    def test_multi_armed_bandit_cold_start_allocates_15_percent(self):
        """
        Multi-Armed Bandit Cold-Start Test:
        In a feed of limit=20 items, exactly 15% (i.e. 3 slots) must be reserved
        for newly published cold-start works (views < 30).
        """
        now = datetime.utcnow()
        posts = []
        # 20 mature posts (views >= 100)
        for i in range(20):
            p = SocialPost(
                id=300 + i,
                user_id=1,
                title=f"Truyện Đã Nổi Tiếng {i}",
                content_snippet="Nội dung cuốn hút...",
                genre="Lịch Sử",
                views_count=200,
                likes_count=50,
                completion_count=40,
                dwell_time_avg=60.0,
                concept_vector=json.dumps(generate_concept_vector(f"popular {i}", "Lịch Sử")),
                created_at=now - timedelta(days=2)
            )
            posts.append(p)

        # 5 cold-start posts (views < 30)
        for i in range(5):
            p = SocialPost(
                id=400 + i,
                user_id=1,
                title=f"Tác Phẩm Tân Binh Mới {i}",
                content_snippet="Nội dung tân binh mới xuất bản...",
                genre="Hiện Đại",
                views_count=5,  # < 30
                likes_count=1,
                completion_count=1,
                dwell_time_avg=20.0,
                concept_vector=json.dumps(generate_concept_vector(f"rookie {i}", "Hiện Đại")),
                created_at=now - timedelta(hours=1)
            )
            posts.append(p)

        self.db.add_all(posts)
        self.db.commit()

        # Retrieve feed with limit=20
        feed = get_feed(self.db, user_id=1, limit=20)
        items = feed.get("items", [])
        self.assertEqual(len(items), 20)

        # Count cold start exploration slots
        cold_start_items = [
            it for it in items
            if it.get("recommendation_metadata", {}).get("is_cold_start_exploration") is True
        ]

        expected_cold_count = int(math.ceil(20 * BANDIT_EXPLORATION_RATIO))  # ceil(20 * 0.15) = 3
        self.assertEqual(
            len(cold_start_items),
            expected_cold_count,
            f"[BANDIT SLOT ALLOCATION ERROR]: Expected {expected_cold_count} exploration slots (15%), got {len(cold_start_items)}"
        )

        for cs in cold_start_items:
            self.assertEqual(cs["recommendation_metadata"]["exploration_strategy"], "thompson_sampling_beta")
            self.assertLess(cs["views_count"], COLD_START_VIEW_THRESHOLD)

    def test_exponential_decay_mathematical_convergence(self):
        """Tests that exponential decay with lambda=0.05/day decays smoothly without underflow."""
        profile = get_or_create_user_profile(self.db, user_id=1)
        profile.genre_affinity = json.dumps({"Lich Su": 100.0})
        self.db.commit()

        # Decay after 0 days
        now = datetime.utcnow()
        profile.last_decay_time = now
        apply_exponential_decay(profile, now=now)
        aff0 = json.loads(profile.genre_affinity)
        self.assertAlmostEqual(aff0["Lich Su"], 100.0, places=2)

        # Decay after 20 days: 100 * exp(-0.05 * 20) = 100 * exp(-1.0) ~ 36.7879
        apply_exponential_decay(profile, now=now + timedelta(days=20))
        aff20 = json.loads(profile.genre_affinity)
        self.assertAlmostEqual(aff20["Lich Su"], 100.0 * math.exp(-1.0), places=1)

        # Decay after 200 days: should not crash or produce NaN
        apply_exponential_decay(profile, now=now + timedelta(days=200))
        aff200 = json.loads(profile.genre_affinity)
        self.assertIsInstance(aff200, dict)


# ==============================================================================
# 5. OPEN MESSENGER DIRECTORY & 1-1 CHAT EDGE CASES
# ==============================================================================

class TestAdversarialMessengerEdgeCases(unittest.TestCase):
    """
    Stress-tests Open Messenger edge cases:
    - Case-insensitive search and self-exclusion
    - Idempotent conversation generation
    - Self-chat attempt rejection
    - Non-existent user rejection
    - Empty / whitespace message rejection
    - XSS injection sanitation
    - Unauthorized access & read status tracking
    """

    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.db = self.Session()

        # Seed 3 users
        self.alice = User(id=1, username="alice_writer", full_name="Alice Nguyen", coins=100)
        self.bob = User(id=2, username="bob_reader", full_name="Bob Tran", coins=50)
        self.eve = User(id=3, username="eve_intruder", full_name="Eve Hacker", coins=0)
        self.db.add_all([self.alice, self.bob, self.eve])
        self.db.commit()

    def tearDown(self):
        self.db.close()

    def test_search_directory_excludes_self_and_matches_case_insensitively(self):
        """Directory search must exclude current user and support case-insensitive matching."""
        # Searching 'alice' while logged in as Alice (id=1) must return 0 results
        results_self = search_users(self.db, query="alice", current_user_id=1)
        self.assertEqual(len(results_self), 0, "Current user must be excluded from directory search!")

        # Searching 'BOB' (uppercase) must find Bob
        results_upper = search_users(self.db, query="BOB", current_user_id=1)
        self.assertEqual(len(results_upper), 1)
        self.assertEqual(results_upper[0]["username"], "bob_reader")

        # Searching by full name 'Tran'
        results_name = search_users(self.db, query="Tran", current_user_id=1)
        self.assertEqual(len(results_name), 1)
        self.assertEqual(results_name[0]["full_name"], "Bob Tran")

    def test_self_chat_attempt_raises_error(self):
        """User cannot create a conversation with themselves."""
        with self.assertRaises(ValueError) as ctx:
            get_or_create_conversation(self.db, user_id_1=1, user_id_2=1)
        self.assertIn("yourself", str(ctx.exception).lower())

    def test_nonexistent_user_raises_error(self):
        """Conversation with non-existent user ID must be rejected."""
        with self.assertRaises(ValueError) as ctx:
            get_or_create_conversation(self.db, user_id_1=1, user_id_2=99999)
        self.assertIn("not exist", str(ctx.exception).lower())

    def test_idempotent_conversation_creation_order_invariant(self):
        """
        Creating conversation (user1, user2) and then (user2, user1)
        must return the EXACT same conversation ID without duplicating rows.
        """
        conv1, created1 = get_or_create_conversation(self.db, 1, 2)
        self.assertTrue(created1)

        conv2, created2 = get_or_create_conversation(self.db, 2, 1)
        self.assertFalse(created2)
        self.assertEqual(conv1.id, conv2.id)

        # Check participants count in database
        parts = self.db.query(ConversationParticipant).filter_by(conversation_id=conv1.id).all()
        self.assertEqual(len(parts), 2)

    def test_empty_or_whitespace_message_rejected(self):
        """Empty or whitespace-only messages must be rejected."""
        conv, _ = get_or_create_conversation(self.db, 1, 2)
        empty_payloads = ["", "   ", "\n\t  \n  ", None]

        for payload in empty_payloads:
            with self.assertRaises(ValueError) as ctx:
                send_message(self.db, conversation_id=conv.id, sender_id=1, message_text=payload)
            self.assertIn("empty", str(ctx.exception).lower())

    def test_xss_message_sanitization(self):
        """XSS payloads must be safely HTML escaped upon persistence."""
        conv, _ = get_or_create_conversation(self.db, 1, 2)
        xss_payload = "<script>alert('pwned')</script><img src=x onerror=alert(1)>"
        
        msg = send_message(self.db, conversation_id=conv.id, sender_id=1, message_text=xss_payload)
        self.assertNotIn("<script>", msg.message_text)
        self.assertIn("&lt;script&gt;", msg.message_text)
        self.assertNotIn("<img", msg.message_text)
        self.assertIn("&lt;img", msg.message_text)

    def test_unauthorized_user_cannot_send_or_read_conversation(self):
        """Eve (user 3) must be forbidden from sending into or reading Alice-Bob conversation."""
        conv, _ = get_or_create_conversation(self.db, 1, 2)
        send_message(self.db, conversation_id=conv.id, sender_id=1, message_text="Hello Bob!")

        # Eve attempts to send a message into Alice-Bob conversation
        with self.assertRaises(PermissionError) as ctx_send:
            send_message(self.db, conversation_id=conv.id, sender_id=3, message_text="I am Eve!")
        self.assertIn("not a participant", str(ctx_send.exception).lower())

        # Eve attempts to read Alice-Bob messages
        with self.assertRaises(PermissionError) as ctx_read:
            get_conversation_messages(self.db, conversation_id=conv.id, current_user_id=3)
        self.assertIn("not a participant", str(ctx_read.exception).lower())

    def test_read_receipts_reset_unread_count_cleanly(self):
        """
        When Alice sends 3 messages to Bob:
        - Bob unread_count = 3
        - Alice unread_count = 0
        When Bob views conversation messages:
        - Bob unread_count resets to 0
        - Alice unread_count remains 0
        """
        conv, _ = get_or_create_conversation(self.db, 1, 2)

        # Alice sends 3 messages
        send_message(self.db, conv.id, sender_id=1, message_text="Tin nhắn 1")
        send_message(self.db, conv.id, sender_id=1, message_text="Tin nhắn 2")
        send_message(self.db, conv.id, sender_id=1, message_text="Tin nhắn 3")

        self.assertEqual(get_total_unread_count(self.db, user_id=2), 3)
        self.assertEqual(get_total_unread_count(self.db, user_id=1), 0)

        # Bob reads messages
        messages_result = get_conversation_messages(self.db, conversation_id=conv.id, current_user_id=2)
        self.assertEqual(len(messages_result["messages"]), 3)

        # Bob unread count must be 0
        self.assertEqual(get_total_unread_count(self.db, user_id=2), 0)
        self.assertEqual(get_total_unread_count(self.db, user_id=1), 0)


# ==============================================================================
# 6. ADVERSARIAL ATTACK PROBING & VULNERABILITY AUDIT
# ==============================================================================

class TestAdversarialAttackProbing(unittest.TestCase):
    """
    Dedicated probing test cases checking known attack surfaces:
    - Line-break / newline evasion in regex gatekeeper
    - Whitespace variations in cliché matching
    - Direct verification of regex flags
    """

    def test_probe_multiline_line_break_evasion(self):
        """
        Audits whether '.*?' in defeat_regex matches across newlines.
        When hero name is followed by '\\n' before defeat keyword:
        Documents whether standard (?i) regex allows bypass without (?s) / re.DOTALL.
        """
        payload = "Trần Hưng Đạo\nbại trận Bạch Đằng và đầu hàng quân Nguyên."
        canon = VIETNAMESE_HISTORICAL_CANON["tran_hung_dao"]
        raw_pattern = canon["defeat_regex"]

        # Test with raw pattern without DOTALL
        raw_match = bool(re.search(raw_pattern, payload))

        # Test with (?s) flag injected
        dotall_pattern = raw_pattern.replace("(?i)", "(?is)")
        dotall_match = bool(re.search(dotall_pattern, payload))

        # The empirical audit records:
        # 1. raw_match is False (vulnerability exists: newline bypasses filter)
        # 2. dotall_match is True (mitigation: (?is) or re.DOTALL closes the bypass)
        self.assertFalse(raw_match, "CONFIRMED VULNERABILITY: Raw defeat_regex failed to match across newline '\\n'")
        self.assertTrue(dotall_match, "CONFIRMED FIX: Adding (?is) successfully detects multiline evasion!")

    def test_probe_double_spacing_cliche_evasion(self):
        """
        Audits whether translation cliché regex handles double-spaces or tabs.
        E.g. 'tiêu  sái' (2 spaces) vs 'tiêu sái' (1 space).
        """
        text_double_space = "Dáng người tiêu  sái đứng trước cổng."
        raw_pattern = r"tiêu sái"
        flexible_pattern = r"tiêu\s+sái"

        raw_match = bool(re.search(raw_pattern, text_double_space))
        flex_match = bool(re.search(flexible_pattern, text_double_space))

        # The empirical audit records:
        # 1. raw_match is False (vulnerability exists: double space bypasses literal string)
        # 2. flex_match is True (mitigation: \\s+ closes the bypass)
        self.assertFalse(raw_match, "CONFIRMED VULNERABILITY: Literal spacing 'tiêu sái' failed on double-space")
        self.assertTrue(flex_match, "CONFIRMED FIX: Flexible regex 'tiêu\\s+sái' catches double-space evasion!")


if __name__ == "__main__":
    unittest.main()
