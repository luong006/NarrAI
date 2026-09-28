"""
Unit Test Suite for Architectural Bridge: M2 Dynamic Scene-Graph Ontology (DSGO) <-> M3 Comic Director
Verifies:
1. extract_setting_dna queries dynamic_scene_graph.get_active_enclosure()
2. extract_character_dna queries dynamic_scene_graph.entities with aliases & pronouns
3. Graceful fallback to story_bible when dynamic_scene_graph is empty or None
4. Graceful fallback when memory is None
5. resolve_spatial_enclosure cleanly propagates DSGO forbidden spatial tokens
6. End-to-end integration through _validate_panels
"""
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Ensure backend directory is in sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

os.environ.setdefault("GROQ_API_KEY", "gsk_test_dummy_key_for_unit_tests")
os.environ.setdefault("GROQ_API_KEY_COMIC", "gsk_test_dummy_key_for_unit_tests")

from models.scene_graph import (
    DynamicSceneGraph,
    CharacterEntity,
    SpaceEnclosure,
    EraGenreConstraint,
    BoundaryType,
    VitalityState,
    EntityRole,
)
from agents.story_memory import StoryBible, StoryMemory
from agents.comic_agent import (
    ComicDirectorAgent,
    resolve_spatial_enclosure,
    sanitize_spatial_prompt,
    SPATIAL_ENCLOSURES,
)


class TestComicDSGOBridge(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with patch("llm.groq_client.Groq"):
            cls.agent = ComicDirectorAgent()

    def setUp(self):
        # Create a standard DSGO graph for testing
        self.era = EraGenreConstraint(
            era_name="modern_2020s",
            genre_name="Modern Campus Light Novel",
            era_banlist=["hanfu", "robes", "sword", "ancient", "magic"]
        )
        self.enclosure = SpaceEnclosure(
            id="chem_lab_101",
            name="Phòng thực hành hóa học",
            boundary_type=BoundaryType.INDOOR_ENCLOSED,
            architectural_anchor="sunlit chemistry laboratory with marble benches and glass beakers",
            persistent_fixtures=["fume hood", "marble benches", "microscopes"],
            lighting_atmosphere="bright cool fluorescent lighting reflecting off glassware",
            negative_drift_tokens=["outdoor", "street", "highway", "traffic", "palace", "sword"],
            connected_enclosures=["corridor_1f"],
            active_entities=["an_student", "minh_friend"]
        )
        self.char1 = CharacterEntity(
            id="an_student",
            name="An",
            aliases=["Lớp phó An", "An"],
            dna="17yo Vietnamese schoolgirl, shoulder-length black hair with blunt bangs, crisp white collared uniform shirt with dark navy ribbon tie",
            gender="female",
            role=EntityRole.LEAD
        )
        self.char2 = CharacterEntity(
            id="minh_friend",
            name="Minh",
            aliases=["Bạn Minh", "Minh"],
            dna="17yo Vietnamese student, short messy dark hair, charcoal grey school blazer over white shirt",
            gender="male",
            role=EntityRole.SUPPORTING
        )
        self.dsg = DynamicSceneGraph(
            session_id="test_session_dsgo_bridge",
            era_genre=self.era,
            entities={
                "an_student": self.char1,
                "minh_friend": self.char2,
            },
            enclosures={"chem_lab_101": self.enclosure},
            active_enclosure_id="chem_lab_101"
        )
        self.memory_with_dsg = StoryMemory(
            story_bible=StoryBible(
                title="Thí nghiệm thanh xuân",
                genre="Modern Campus Light Novel",
                world_setting="Lớp học phổ thông",
                characters=[
                    {"name": "An", "appearance": "Nữ sinh tóc ngắn", "role": "lead", "gender": "female"}
                ]
            ),
            dynamic_scene_graph=self.dsg
        )

        self.memory_bible_only = StoryMemory(
            story_bible=StoryBible(
                title="Chuyện ngày hè",
                genre="Campus",
                world_setting="Sân thượng trường học với lan can kim loại",
                characters=[
                    {"name": "Linh", "appearance": "Nữ sinh cột tóc đuôi ngựa cao, đeo nơ xanh", "role": "lead", "gender": "female"},
                    {"name": "Khang", "appearance": "Nam sinh cao ráo, mặc áo sơ mi trắng", "role": "bạn cùng bàn", "gender": "male"}
                ]
            ),
            dynamic_scene_graph=None
        )

    # -------------------------------------------------------------------------
    # 1. SETTING DNA EXTRACTION BRIDGE
    # -------------------------------------------------------------------------
    def test_extract_setting_dna_from_dsgo_active_enclosure(self):
        """Verify extract_setting_dna extracts spatial anchor and attributes directly from DSGO active enclosure."""
        setting_dna = self.agent.extract_setting_dna("", memory=self.memory_with_dsg)

        self.assertEqual(setting_dna.get("location_name"), "Phòng thực hành hóa học")
        self.assertIn("sunlit chemistry laboratory", setting_dna.get("setting_anchor", ""))
        self.assertIn("fluorescent lighting", setting_dna.get("atmosphere", ""))
        self.assertIn("fume hood", setting_dna.get("persistent_fixtures", []))
        self.assertIn("sword", setting_dna.get("forbidden_spatial_tokens", []))
        self.assertIn("traffic", setting_dna.get("forbidden_spatial_tokens", []))
        self.assertTrue(len(setting_dna.get("quarantine_negative_tokens", "")) > 0)

    def test_extract_setting_dna_graceful_fallback_to_story_bible(self):
        """Verify extract_setting_dna falls back gracefully to story_bible when DSGO is absent."""
        setting_dna = self.agent.extract_setting_dna("", memory=self.memory_bible_only)

        self.assertEqual(setting_dna.get("location_name"), "Bối cảnh chính")
        self.assertEqual(setting_dna.get("setting_anchor"), "Sân thượng trường học với lan can kim loại")
        self.assertIn("screentone", setting_dna.get("atmosphere", ""))

    def test_extract_setting_dna_fallback_when_memory_none(self):
        """Verify extract_setting_dna returns robust default when memory is None."""
        setting_dna = self.agent.extract_setting_dna("", memory=None)
        self.assertIn("setting_anchor", setting_dna)
        self.assertTrue(len(setting_dna["setting_anchor"]) > 0)

    # -------------------------------------------------------------------------
    # 2. CHARACTER DNA EXTRACTION BRIDGE
    # -------------------------------------------------------------------------
    def test_extract_character_dna_from_dsgo_entities(self):
        """Verify extract_character_dna queries CharacterEntity objects from DSGO and enriches aliases/pronouns."""
        char_dna = self.agent.extract_character_dna("", memory=self.memory_with_dsg)

        self.assertIn("An", char_dna)
        self.assertIn("Minh", char_dna)

        # Check An's DNA and enriched pronoun aliases
        an_info = char_dna["An"]
        self.assertIn("blunt bangs", an_info["dna"])
        self.assertEqual(an_info["gender"], "female")
        self.assertIn("cô bé", an_info["aliases"])
        self.assertIn("nữ sinh", an_info["aliases"])
        self.assertIn("she", an_info["aliases"])

        # Check Minh's DNA and enriched pronoun aliases
        minh_info = char_dna["Minh"]
        self.assertIn("blazer", minh_info["dna"])
        self.assertEqual(minh_info["gender"], "male")
        self.assertIn("cậu ấy", minh_info["aliases"])
        self.assertIn("nam sinh", minh_info["aliases"])
        self.assertIn("he", minh_info["aliases"])

    def test_extract_character_dna_graceful_fallback_to_story_bible(self):
        """Verify extract_character_dna falls back gracefully to story_bible when DSGO is absent."""
        char_dna = self.agent.extract_character_dna("", memory=self.memory_bible_only)

        self.assertIn("Linh", char_dna)
        self.assertIn("Khang", char_dna)
        self.assertIn("đuôi ngựa", char_dna["Linh"]["dna"])
        self.assertIn("cô bé", char_dna["Linh"]["aliases"])
        self.assertIn("bạn cùng bàn", char_dna["Khang"]["aliases"])

    def test_extract_character_dna_fallback_when_memory_none(self):
        """Verify extract_character_dna returns protagonist fallback when memory is None."""
        char_dna = self.agent.extract_character_dna("", memory=None)
        self.assertIn("Protagonist", char_dna)
        self.assertIn("lead", char_dna["Protagonist"]["role"])

    # -------------------------------------------------------------------------
    # 3. SPATIAL RESOLUTION & SANITIZATION WITH DSGO TOKENS
    # -------------------------------------------------------------------------
    def test_resolve_spatial_enclosure_merges_dsgo_forbidden_tokens(self):
        """Verify resolve_spatial_enclosure merges custom forbidden tokens from DSGO setting_dna."""
        setting_dna = self.agent.extract_setting_dna("", memory=self.memory_with_dsg)
        resolved = resolve_spatial_enclosure("", setting_dna=setting_dna)

        # Forbidden tokens from DSGO should be included
        self.assertIn("sword", resolved["forbidden_spatial_tokens"])
        self.assertIn("traffic", resolved["forbidden_spatial_tokens"])
        self.assertIn("highway", resolved["forbidden_spatial_tokens"])

    def test_validate_panels_integrates_dsgo_setting_and_character_dna(self):
        """Verify _validate_panels cleanly injects DSGO setting anchor and character DNA."""
        setting_dna = self.agent.extract_setting_dna("", memory=self.memory_with_dsg)
        char_dna = self.agent.extract_character_dna("", memory=self.memory_with_dsg)

        raw_panels = [
            {
                "panel_index": 1,
                "image_prompt": "An cặm cụi ghi chép bài thí nghiệm",
                "dialogue_text": "An: \"Phản ứng này tạo ra kết tủa rất đẹp.\"",
                "layout_type": "square"
            }
        ]
        validated = self.agent._validate_panels(raw_panels, character_dna_map=char_dna, setting_dna=setting_dna)

        self.assertEqual(len(validated), 1)
        prompt = validated[0]["image_prompt"]

        # Setting anchor from DSGO must be injected
        self.assertIn("setting: sunlit chemistry laboratory with marble benches and glass beakers", prompt)
        # Character DNA from DSGO must be injected
        self.assertIn("blunt bangs", prompt)
        # Action gesture from prose must be mapped
        self.assertIn("writing attentively in a notebook", prompt)
        # Dialogue must be preserved without ellipsis
        self.assertEqual(validated[0]["dialogue_text"], "An: \"Phản ứng này tạo ra kết tủa rất đẹp.\"")


if __name__ == "__main__":
    unittest.main()
