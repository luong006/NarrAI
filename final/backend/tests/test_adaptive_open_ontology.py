"""
Comprehensive Unit Test Suite for Milestone 1:
Adaptive Open-Ontology & 3 Narrative Modes in NarrAI.

Validates:
1. 3 Narrative Modes (Chính Sử, Dã Sử, Hư Cấu Tự Do) & Cultural Tiers (Tier 1, Tier 2, Tier 3)
2. HistoricalGroundingGatekeeper (Immutable national hero invariants & battle outcomes)
3. TriTierOntologyResolver (S_cult scoring, visual DNA, and Master Negative filters)
4. SmartSelectiveLanguageFilter (Chinese translation cliches vs Wuxia permission vs Universal AI cliches)
5. DynamicSceneGraph & EraGenreConstraint relaxation (non-modern / Tier 3 open-domain)
6. StoryBible & StoryMemory integration (mode & tier propagation, scene graph initialization)
7. ComicDirectorAgent & CloudflareAI visual pipeline (attire expansion, negative prompt injection)
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Ensure backend root is on sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

os.environ.setdefault("GROQ_API_KEY", "gsk_test_dummy_key_for_unit_tests")
os.environ.setdefault("GROQ_API_KEY_COPILOT", "gsk_test_dummy_key_for_unit_tests")
os.environ.setdefault("GROQ_API_KEY_BIBLE", "gsk_test_dummy_key_for_unit_tests")
os.environ.setdefault("GROQ_API_KEY_COMIC", "gsk_test_dummy_key_for_unit_tests")

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
from models.scene_graph import (
    CharacterEntity,
    SpaceEnclosure,
    EraGenreConstraint,
    DynamicSceneGraph,
    BoundaryType,
    VitalityState,
    sanitize_era_prompt,
)
from agents.story_memory import StoryBible, StoryMemory
from agents.story_generator import StoryGenerator
from agents.comic_agent import (
    ComicDirectorAgent,
    resolve_spatial_enclosure,
    DNA_EXTRACTOR_PROMPT,
)
from services.cloudflare_ai import (
    get_master_negative_prompt,
    VIETNAMESE_CANONICAL_NEGATIVE_PROMPT,
    MODERN_SCHOOL_EXCLUSIONS,
)


class TestHistoricalGroundingGatekeeper(unittest.TestCase):
    """Test suite for HistoricalGroundingGatekeeper national hero & battle invariants."""

    def test_canonical_heroes_valid_outcomes(self):
        """Authentic historical victory statements for all canonical heroes must pass."""
        valid_history_cases = [
            "Hai Bà Trưng khởi nghĩa chống ách đô hộ của nhà Đông Hán, giành lại độc lập cho 65 thành trì.",
            "Ngô Quyền cắm cọc nhọn bọc sắt trên sông Bạch Đằng đập tan thủy quân Nam Hán năm 938.",
            "Lý Thường Kiệt chặn đứng quân Tống trên sông Như Nguyệt với bài thơ thần Nam quốc sơn hà.",
            "Hưng Đạo Đại Vương Trần Quốc Tuấn ba lần đánh bại quân Nguyên Mông xâm lược Đại Việt.",
            "Bình Định Vương Lê Lợi lãnh đạo khởi nghĩa Lam Sơn toàn thắng, đuổi sạch giặc Minh.",
            "Hoàng đế Quang Trung hành quân thần tốc, đại phá 29 vạn quân Mãn Thanh tại Ngọc Hồi Đống Đa.",
            "Trận Bạch Đằng năm 1288 kết thúc với đại thắng vang dội của quân dân nhà Trần trước Thoát Hoan.",
        ]
        for case in valid_history_cases:
            ok, violations = HistoricalGroundingGatekeeper.validate_historical_invariants(
                case, mode=NarrativeMode.CHINH_SU
            )
            self.assertTrue(ok, f"Expected valid history to pass: {case}. Got: {violations}")
            self.assertEqual(len(violations), 0)

    def test_canonical_heroes_reversal_rejection(self):
        """Distortions, revisions, and defeats of national heroes must be rejected in Mode 1 (Chính Sử)."""
        distortions = [
            ("Trần Hưng Đạo bại trận Bạch Đằng và đầu hàng quân Nguyên.", "Trần Hưng Đạo"),
            ("Ngô Quyền bị Lưu Hoằng Tháo đánh bại trên sông Bạch Đằng.", "Ngô Quyền"),
            ("Lý Thường Kiệt đầu hàng tướng Quách Quỳ trên sông Như Nguyệt.", "Lý Thường Kiệt"),
            ("Lê Lợi đầu hàng Vương Thông và dâng đất Lam Sơn cho giặc Minh.", "Lê Lợi"),
            ("Quang Trung thua trận tại Ngọc Hồi Đống Đa trước quân Thanh.", "Quang Trung"),
            ("Hai Bà Trưng dâng đất xin hàng thái thú Tô Định.", "Hai Bà Trưng"),
            ("Quân Đại Việt thua tan tác trong trận Bạch Đằng năm 1288.", "Bạch Đằng"),
        ]
        for text, keyword in distortions:
            ok, violations = HistoricalGroundingGatekeeper.validate_historical_invariants(
                text, mode=NarrativeMode.CHINH_SU
            )
            self.assertFalse(ok, f"Expected distortion to fail: '{text}'")
            self.assertGreater(len(violations), 0)
            self.assertTrue(any("HISTORICAL_VIOLATION" in v for v in violations))

    def test_mode_3_bypass(self):
        """In Hư Cấu Tự Do (Mode 3), alternate fantasy history is permitted."""
        fantasy_text = "Trong thế giới ma pháp, Trần Hưng Đạo điều khiển rồng thần thất thủ trước binh đoàn quỷ dữ."
        ok, violations = HistoricalGroundingGatekeeper.validate_historical_invariants(
            fantasy_text, mode=NarrativeMode.HU_CAU_TU_DO
        )
        self.assertTrue(ok)
        self.assertEqual(len(violations), 0)

    def test_mode_2_da_su_retains_core_invariants(self):
        """In Dã Sử (Mode 2), core battle outcomes and heroic dignity remain protected."""
        bad_da_su = "Trong một tích dã sử kỳ lạ, Quang Trung đầu hàng giặc Thanh."
        ok, violations = HistoricalGroundingGatekeeper.validate_historical_invariants(
            bad_da_su, mode=NarrativeMode.DA_SU
        )
        self.assertFalse(ok)
        self.assertGreater(len(violations), 0)


class TestTriTierOntologyResolver(unittest.TestCase):
    """Test suite for S_cult similarity calculation and tri-tier ontology resolution."""

    def test_tier_1_canonical_vietnamese(self):
        prompt = "Trần Hưng Đạo duyệt binh bên bờ sông Bạch Đằng, tướng sĩ mặc áo ngũ thân oai phong lẫm liệt."
        sim = TriTierOntologyResolver.calculate_cultural_similarity(prompt)
        tier = TriTierOntologyResolver.resolve_tier(sim)
        self.assertGreaterEqual(sim, 0.70)
        self.assertEqual(tier, CulturalTier.TIER_1_CANONICAL_VN)

    def test_tier_2_cultural_fusion(self):
        prompt = "Thành phố Sài Gòn Cyberpunk năm 2088 với những biển quảng cáo phở và áo dài hologram."
        sim = TriTierOntologyResolver.calculate_cultural_similarity(prompt)
        tier = TriTierOntologyResolver.resolve_tier(sim)
        self.assertGreaterEqual(sim, 0.30)
        self.assertLess(sim, 0.70)
        self.assertEqual(tier, CulturalTier.TIER_2_CULTURAL_FUSION)

    def test_tier_3_open_domain(self):
        prompt = "Captain Vance steered the starship Endeavour past the rings of Saturn."
        sim = TriTierOntologyResolver.calculate_cultural_similarity(prompt)
        tier = TriTierOntologyResolver.resolve_tier(sim)
        self.assertLess(sim, 0.30)
        self.assertEqual(tier, CulturalTier.TIER_3_OPEN_DOMAIN)

    def test_tier_visual_dna_and_master_negative(self):
        # Tier 1
        pos1, neg1 = TriTierOntologyResolver.get_tier_visual_dna(CulturalTier.TIER_1_CANONICAL_VN)
        self.assertIn("Áo Ngũ Thân", pos1)
        self.assertIn("hanfu", neg1.lower())
        self.assertIn("kimono", neg1.lower())
        self.assertIn("samurai", neg1.lower())

        # Tier 2
        pos2, neg2 = TriTierOntologyResolver.get_tier_visual_dna(CulturalTier.TIER_2_CULTURAL_FUSION)
        self.assertIn("fusion", pos2.lower())
        self.assertIn("hanfu", neg2.lower())

        # Tier 3
        pos3, neg3 = TriTierOntologyResolver.get_tier_visual_dna(CulturalTier.TIER_3_OPEN_DOMAIN)
        self.assertNotIn("Áo Ngũ Thân", pos3)
        self.assertEqual(neg3, "")


class TestSmartSelectiveLanguageFilter(unittest.TestCase):
    """Test suite for selective suppression of Chinese clichés vs Wuxia permission vs Universal AI clichés."""

    def test_wuxia_permission_in_free_fiction(self):
        """Chinese translation clichés are allowed in Tiên hiệp / Kiếm hiệp under Hư Cấu Tự Do."""
        text = "Hắn khẽ nhếch mép tà mị, thân hình tiêu sái xuất kiếm, ánh mắt lãnh khốc nhìn về phía đế tôn."
        clean, violations = SmartSelectiveLanguageFilter.validate_smart_language_compliance(
            text, genre="Tiên hiệp tu chân", narrative_mode=NarrativeMode.HU_CAU_TU_DO
        )
        self.assertTrue(clean)
        self.assertEqual(len(violations), 0)

    def test_pure_vn_suppression(self):
        """Chinese translation clichés are banned in Vietnamese contemporary prose."""
        text = "Anh bước vào quán cà phê với dáng vẻ tiêu sái, nụ cười tà mị khiến cô bối rối."
        clean, violations = SmartSelectiveLanguageFilter.validate_smart_language_compliance(
            text, genre="Hiện thực đời thường", narrative_mode=NarrativeMode.HU_CAU_TU_DO
        )
        self.assertFalse(clean)
        self.assertTrue(any("tiêu sái" in v or "tà mị" in v for v in violations))

    def test_historical_mode_suppression(self):
        """Chinese translation clichés are strictly banned in Chính Sử regardless of genre parameter."""
        text = "Trần Hưng Đạo tiêu sái đứng trên thuyền rồng."
        clean, violations = SmartSelectiveLanguageFilter.validate_smart_language_compliance(
            text, genre="Tiên hiệp", narrative_mode=NarrativeMode.CHINH_SU
        )
        self.assertFalse(clean)
        self.assertTrue(any("tiêu sái" in v for v in violations))

    def test_universal_ai_cliches_always_banned(self):
        """Universal AI tropes are banned everywhere."""
        text = "Nhịp tim hắn nhanh như một nhịp tim chậm rãi, cảm thấy một khoảng trống trong lòng."
        clean, violations = SmartSelectiveLanguageFilter.validate_smart_language_compliance(
            text, genre="Tiên hiệp", narrative_mode=NarrativeMode.HU_CAU_TU_DO
        )
        self.assertFalse(clean)
        self.assertTrue(any("AI_CLICHE" in v for v in violations))


class TestDynamicSceneGraphRelaxation(unittest.TestCase):
    """Test suite for DynamicSceneGraph era relaxation and Vietnamese master negative integration."""

    def test_historical_mode_allows_swords_and_robes(self):
        era = EraGenreConstraint(
            era_name="vietnamese_canonical",
            genre_name="Chính sử Việt Nam",
            era_banlist=[],
            cultural_tier=1,
            narrative_mode="CHINH_SU"
        )
        graph = DynamicSceneGraph(era_genre=era)
        valid, violations = graph.validate_era_consistency(
            "Tướng quân rút gươm báu và chỉnh lại vạt áo ngũ thân trước khi xuất kích"
        )
        self.assertTrue(valid)
        self.assertEqual(len(violations), 0)

    def test_tier_3_open_domain_allows_fantasy_and_scifi(self):
        era = EraGenreConstraint(
            era_name="open_domain",
            genre_name="Space Fantasy",
            era_banlist=[],
            cultural_tier=3,
            narrative_mode="HU_CAU_TU_DO"
        )
        graph = DynamicSceneGraph(era_genre=era, cultural_tier=3)
        valid, violations = graph.validate_era_consistency(
            "The sorcerer swung a glowing broadsword while casting high magic"
        )
        self.assertTrue(valid)
        self.assertEqual(len(violations), 0)

    def test_sanitize_era_prompt_preserves_swords_in_historical(self):
        prompt = "1boy, holding sharp sword, traditional robes, heroic expression"
        era = EraGenreConstraint(
            era_name="vietnamese_canonical",
            cultural_tier=1,
            narrative_mode="CHINH_SU"
        )
        sanitized = sanitize_era_prompt(prompt, era)
        self.assertIn("sword", sanitized)
        self.assertIn("robes", sanitized)

    def test_master_negative_tokens_injected(self):
        era = EraGenreConstraint(
            era_name="vietnamese_canonical",
            cultural_tier=1,
            narrative_mode="CHINH_SU"
        )
        graph = DynamicSceneGraph(era_genre=era, cultural_tier=1, narrative_mode="CHINH_SU")
        neg_tokens = graph.get_combined_negative_tokens()
        self.assertIn("hanfu", neg_tokens)
        self.assertIn("kimono", neg_tokens)
        self.assertIn("samurai", neg_tokens)


class TestStoryMemoryAndBibleIntegration(unittest.TestCase):
    """Test suite for StoryBible and StoryMemory narrative mode & cultural tier propagation."""

    def test_story_bible_mode_and_tier_serialization(self):
        bible = StoryBible(
            title="Đại Việt Sử Ký",
            genre="Chính sử Việt Nam",
            narrative_mode="CHINH_SU",
            cultural_tier=1
        )
        d = bible.to_dict()
        self.assertEqual(d["narrative_mode"], "CHINH_SU")
        self.assertEqual(d["cultural_tier"], 1)

        restored = StoryBible.from_dict(d)
        self.assertEqual(restored.narrative_mode, "CHINH_SU")
        self.assertEqual(restored.cultural_tier, 1)

    def test_story_bible_prompt_block_contains_mode_and_tier(self):
        bible = StoryBible(
            title="Huyền Thoại Lam Sơn",
            genre="Lịch sử",
            narrative_mode="CHINH_SU",
            cultural_tier=1
        )
        block = bible.to_prompt_block()
        self.assertIn("CHINH_SU", block)
        self.assertIn("Cultural Tier: 1", block)

    def test_story_memory_init_scene_graph_historical(self):
        mem = StoryMemory()
        mem.story_bible = StoryBible(
            title="Bạch Đằng Giang",
            genre="Chính sử Việt Nam",
            world_setting="Chiến trường sông Bạch Đằng",
            narrative_mode="CHINH_SU",
            cultural_tier=1,
            characters=[{"name": "Trần Hưng Đạo", "role": "lead"}]
        )
        dsg = mem.init_scene_graph_from_bible()
        self.assertIsNotNone(dsg)
        self.assertEqual(dsg.era_genre.era_name, "vietnamese_canonical")
        self.assertEqual(dsg.cultural_tier, 1)
        self.assertEqual(dsg.narrative_mode, "CHINH_SU")
        self.assertIn("tran_hung_dao", dsg.entities)
        enc = dsg.get_active_enclosure()
        self.assertIsNotNone(enc)
        self.assertEqual(enc.boundary_type, BoundaryType.OUTDOOR_BOUNDED)

    def test_story_memory_init_scene_graph_tier_3_open_domain(self):
        mem = StoryMemory()
        mem.story_bible = StoryBible(
            title="Star Voyager",
            genre="Sci-Fi Space Opera",
            world_setting="Starship Bridge",
            narrative_mode="HU_CAU_TU_DO",
            cultural_tier=3,
            characters=[{"name": "Jack", "role": "lead"}]
        )
        dsg = mem.init_scene_graph_from_bible()
        self.assertIsNotNone(dsg)
        self.assertEqual(dsg.era_genre.era_name, "open_domain")
        self.assertEqual(dsg.cultural_tier, 3)


class TestComicAndCloudflareAIIntegration(unittest.TestCase):
    """Test suite for comic visual pipeline integration with cultural tiers and master negative prompt."""

    def test_dna_extractor_prompt_contains_vietnamese_attire(self):
        prompt_lower = DNA_EXTRACTOR_PROMPT.lower()
        self.assertIn("áo ngũ thân", prompt_lower)
        self.assertIn("khăn đóng", prompt_lower)
        self.assertIn("áo bà ba", prompt_lower)

    def test_cloudflare_ai_master_negative_prompt_vietnamese(self):
        neg_prompt = get_master_negative_prompt(cultural_tier=1, narrative_mode="CHINH_SU")
        self.assertIn("hanfu", neg_prompt.lower())
        self.assertIn("kimono", neg_prompt.lower())
        self.assertIn("samurai", neg_prompt.lower())
        self.assertIn("ninja", neg_prompt.lower())

    def test_cloudflare_ai_master_negative_tier_3_omits_vietnamese_ban(self):
        neg_prompt = get_master_negative_prompt(cultural_tier=3, narrative_mode="HU_CAU_TU_DO")
        self.assertNotIn("hanfu", neg_prompt.lower())
        self.assertNotIn("kimono", neg_prompt.lower())

    def test_resolve_spatial_enclosure_historical_and_open_domain(self):
        enc_vn = resolve_spatial_enclosure("doanh trại bên bờ sông", cultural_tier=1)
        self.assertIn("vietnamese", enc_vn.get("key", "").lower())

        enc_open = resolve_spatial_enclosure("alien spacecraft cockpit", cultural_tier=3)
        self.assertEqual(enc_open.get("key"), "open_domain")


if __name__ == "__main__":
    unittest.main()
