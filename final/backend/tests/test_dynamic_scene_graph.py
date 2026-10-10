"""
Comprehensive Unit Test Suite for Dynamic Scene-Graph Ontology (DSGO) & Spatial Scene Enclosure.
Covers:
  1. Pydantic Model Creation & Aliases (CharacterEntity, SpaceEnclosure, EraGenreConstraint, DynamicSceneGraph)
  2. Automated Invariant Gatekeepers (Vitality, Spatial Exclusivity, Era Consistency, Universal Validator)
  3. Spatial & Era Drift Sanitizers (sanitize_spatial_prompt, sanitize_era_prompt, graph.sanitize_prompt)
  4. Scene Transition Gating (Enclosure locking vs valid transition vs disconnected gating)
  5. StoryMemory DSGO Integration & Serialization Roundtrip (to_dict, from_dict, backward compatibility)
  6. StoryGenerator & MemoryExtractor DSGO Integration (prompt block injection, spatial updates)
"""
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

os.environ.setdefault("GROQ_API_KEY", "gsk_test_dummy_key_for_unit_tests")
os.environ.setdefault("GROQ_API_KEY_COPILOT", "gsk_test_dummy_key_for_unit_tests")
os.environ.setdefault("GROQ_API_KEY_BIBLE", "gsk_test_dummy_key_for_unit_tests")

from models.scene_graph import (
    CharacterEntity,
    ItemEntity,
    SpaceEnclosure,
    EraGenreConstraint,
    DynamicSceneGraph,
    VitalityState,
    EntityRole,
    BoundaryType,
    EraType,
    sanitize_spatial_prompt,
    sanitize_era_prompt,
)
from agents.story_memory import StoryBible, StoryMemory
from agents.story_generator import StoryGenerator
from agents.memory_extractor import MemoryExtractor


class TestDynamicSceneGraphModels(unittest.TestCase):
    """1. Test Pydantic model creation, validations, properties and aliases."""

    def test_character_entity_creation_and_aliases(self):
        char = CharacterEntity(
            id="an",
            name="An",
            aliases=["Cô bé lớp phó", "An"],
            dna="An (17yo schoolgirl, blunt bob hair, white shirt with blue ribbon)",
            vitality=VitalityState.ALIVE,
            current_location_id="classroom_12a",
            inventory=["student_notebook", "pen"],
            emotional_state="lo lắng",
            role=EntityRole.LEAD,
            gender="female"
        )
        self.assertEqual(char.id, "an")
        self.assertEqual(char.name, "An")
        self.assertEqual(char.visual_dna, "An (17yo schoolgirl, blunt bob hair, white shirt with blue ribbon)")
        self.assertEqual(char.dna, char.visual_dna)
        self.assertEqual(char.vitality_state, VitalityState.ALIVE)
        self.assertEqual(char.vitality, VitalityState.ALIVE)
        self.assertTrue(char.is_alive)
        self.assertEqual(char.psychological_state, "lo lắng")
        self.assertEqual(char.emotional_state, "lo lắng")
        self.assertIn("student_notebook", char.inventory)

        # Test dictionary serialization roundtrip
        char_dict = char.to_dict()
        char_reloaded = CharacterEntity.from_dict(char_dict)
        self.assertEqual(char_reloaded.id, char.id)
        self.assertEqual(char_reloaded.dna, char.dna)

    def test_space_enclosure_creation_and_methods(self):
        enc = SpaceEnclosure(
            id="classroom_12a",
            name="Lớp học 12A3",
            boundary_type=BoundaryType.INDOOR_ENCLOSED,
            architectural_anchor="pastel green walls, large grid windows on the left",
            persistent_fixtures=["wooden student desks", "green chalkboard", "teacher lectern"],
            lighting_atmosphere="slanting afternoon sunlight streaming across wooden desks",
            negative_drift_tokens=["outdoor", "street", "trees", "cars", "sky"],
            connected_enclosures=["corridor_3f"]
        )
        self.assertEqual(enc.id, "classroom_12a")
        self.assertTrue(enc.is_enclosed())

        # Test build_enclosure_fragment
        frag = enc.build_enclosure_fragment()
        self.assertIn("inside Lớp học 12A3", frag)
        self.assertIn("pastel green walls", frag)
        self.assertIn("wooden student desks", frag)
        self.assertIn("afternoon sunlight", frag)

        # Outdoor enclosure test
        outdoor_enc = SpaceEnclosure(
            id="school_yard",
            name="Sân trường",
            boundary_type=BoundaryType.OUTDOOR_OPEN
        )
        self.assertFalse(outdoor_enc.is_enclosed())

    def test_era_genre_constraint_creation_and_aliases(self):
        era = EraGenreConstraint(
            era="modern_2020s",
            genre="Modern Campus Light Novel",
            world_axioms=["Không có phép thuật", "Công nghệ điện thoại thông minh"],
            forbidden_visual_tokens=["hanfu", "swords", "magic wand"],
            tech_level="modern"
        )
        self.assertEqual(era.era_name, "modern_2020s")
        self.assertEqual(era.era, "modern_2020s")
        self.assertEqual(era.genre_name, "Modern Campus Light Novel")
        self.assertIn("hanfu", era.era_banlist)
        self.assertIn("swords", era.era_banlist)

    def test_dynamic_scene_graph_creation(self):
        char = CharacterEntity(id="minh", name="Minh", visual_dna="Minh (17yo student)", current_location_id="classroom_12a")
        enc = SpaceEnclosure(id="classroom_12a", name="Lớp 12A", connected_enclosures=["corridor"])
        graph = DynamicSceneGraph(
            characters={"minh": char},
            spaces={"classroom_12a": enc},
            active_enclosure_id="classroom_12a"
        )
        self.assertIn("minh", graph.entities)
        self.assertIn("classroom_12a", graph.enclosures)
        self.assertEqual(graph.active_enclosure_id, "classroom_12a")
        self.assertEqual(graph.get_active_enclosure().name, "Lớp 12A")


class TestAutomatedInvariantGatekeepers(unittest.TestCase):
    """2. Test Automated Invariant Gatekeepers (Vitality, Spatial Exclusivity, Era Consistency)."""

    def setUp(self):
        self.char_alive = CharacterEntity(
            id="an", name="An", vitality_state=VitalityState.ALIVE, current_location_id="room_a", inventory=["key"]
        )
        self.char_dead = CharacterEntity(
            id="ghost", name="Hồn ma", vitality_state=VitalityState.DECEASED, current_location_id="room_a"
        )
        self.char_distant = CharacterEntity(
            id="minh", name="Minh", vitality_state=VitalityState.ALIVE, current_location_id="room_b"
        )
        self.char_connected = CharacterEntity(
            id="lan", name="Lan", vitality_state=VitalityState.ALIVE, current_location_id="corridor"
        )

        self.enc_a = SpaceEnclosure(id="room_a", name="Phòng A", connected_enclosures=["corridor"])
        self.enc_b = SpaceEnclosure(id="room_b", name="Phòng B", connected_enclosures=[])
        self.enc_corridor = SpaceEnclosure(id="corridor", name="Hành lang", connected_enclosures=["room_a"])

        self.graph = DynamicSceneGraph(
            entities={"an": self.char_alive, "ghost": self.char_dead, "minh": self.char_distant, "lan": self.char_connected},
            enclosures={"room_a": self.enc_a, "room_b": self.enc_b, "corridor": self.enc_corridor},
            active_enclosure_id="room_a"
        )

    def test_vitality_invariant_alive_acts(self):
        valid, err = self.graph.validate_vitality("an", "SPEAKS")
        self.assertTrue(valid)
        self.assertIsNone(err)

    def test_vitality_invariant_deceased_cannot_act(self):
        valid, err = self.graph.validate_vitality("ghost", "SPEAKS")
        self.assertFalse(valid)
        self.assertIn("VITALITY_VIOLATION", err)
        self.assertIn("DECEASED", err)

    def test_spatial_exclusivity_same_enclosure(self):
        valid, err = self.graph.validate_spatial_exclusivity("an", "ghost")
        self.assertTrue(valid)
        self.assertIsNone(err)

    def test_spatial_exclusivity_connected_enclosure(self):
        valid, err = self.graph.validate_spatial_exclusivity("an", "lan")
        self.assertTrue(valid)
        self.assertIsNone(err)

    def test_spatial_exclusivity_disconnected_enclosure(self):
        valid, err = self.graph.validate_spatial_exclusivity("an", "minh")
        self.assertFalse(valid)
        self.assertIn("SPATIAL_VIOLATION", err)
        self.assertIn("disconnected enclosure", err)

    def test_era_consistency_check(self):
        valid, violations = self.graph.validate_era_consistency("An mặc đồng phục học sinh bước vào lớp")
        self.assertTrue(valid)
        self.assertEqual(len(violations), 0)

        # Test prohibited tokens in modern setting
        invalid, violations = self.graph.validate_era_consistency("An rút flying sword và mặc hanfu lướt gió")
        self.assertFalse(invalid)
        self.assertTrue(any("flying sword" in v for v in violations))
        self.assertTrue(any("hanfu" in v for v in violations))

    def test_universal_validate_action(self):
        # Valid action
        valid, violations = self.graph.validate_action("an", "SPEAKS", target_id="lan", used_item="key")
        self.assertTrue(valid)
        self.assertEqual(len(violations), 0)

        # Multi-failure action: dead character using item not in inventory in disconnected room with sword
        valid, violations = self.graph.validate_action(
            actor_id="ghost",
            action_type="ATTACKS",
            target_id="minh",
            used_item="magic_staff",
            prompt="wearing robes and flying"
        )
        self.assertFalse(valid)
        self.assertTrue(any("VITALITY_VIOLATION" in v for v in violations))
        self.assertTrue(any("SPATIAL_VIOLATION" in v for v in violations))
        self.assertTrue(any("INVENTORY_VIOLATION" in v for v in violations))
        self.assertTrue(any("ERA_VIOLATION" in v for v in violations))


class TestDriftSanitizers(unittest.TestCase):
    """3. Test Spatial Scene Enclosure Sanitizers (sanitize_spatial_prompt & sanitize_era_prompt)."""

    def setUp(self):
        self.enclosed_room = SpaceEnclosure(
            id="classroom",
            name="Classroom",
            boundary_type=BoundaryType.INDOOR_ENCLOSED,
            architectural_anchor="chalkboard and wooden desks",
            negative_drift_tokens=["busy highway"]
        )
        self.open_outdoor = SpaceEnclosure(
            id="street",
            name="Tokyo Street",
            boundary_type=BoundaryType.OUTDOOR_OPEN,
            negative_drift_tokens=["bedroom"]
        )
        self.era_constraint = EraGenreConstraint(
            era_name="modern_2020s",
            era_banlist=["flying sword", "dragon chariot"]
        )

    def test_sanitize_spatial_prompt_enclosed_room(self):
        raw_prompt = "1girl, sitting at desk, blue sky, trees outside, street cars, busy highway, focused expression"
        sanitized = sanitize_spatial_prompt(raw_prompt, self.enclosed_room)
        self.assertNotIn("blue sky", sanitized)
        self.assertNotIn("trees", sanitized)
        self.assertNotIn("street", sanitized)
        self.assertNotIn("cars", sanitized)
        self.assertNotIn("busy highway", sanitized)
        self.assertIn("1girl", sanitized)
        self.assertIn("sitting at desk", sanitized)
        self.assertIn("focused expression", sanitized)

    def test_sanitize_spatial_prompt_subword_preservation(self):
        # "classroom" should not be corrupted when stripping room-like words
        raw_prompt = "1girl, inside classroom, pastel walls, road, outdoor"
        sanitized = sanitize_spatial_prompt(raw_prompt, self.enclosed_room)
        self.assertIn("classroom", sanitized)
        self.assertNotIn("road", sanitized)
        self.assertNotIn("outdoor", sanitized)

    def test_sanitize_spatial_prompt_outdoor_open(self):
        # Outdoor open enclosure should NOT strip blue sky or trees
        raw_prompt = "1girl, walking in street, blue sky, green trees, bedroom"
        sanitized = sanitize_spatial_prompt(raw_prompt, self.open_outdoor)
        self.assertIn("blue sky", sanitized)
        self.assertIn("green trees", sanitized)
        self.assertIn("street", sanitized)
        self.assertNotIn("bedroom", sanitized)

    def test_sanitize_era_prompt_modern_setting(self):
        raw_prompt = "1boy, student uniform, drawing swords, wearing hanfu, dragon chariot, holding pencil"
        sanitized = sanitize_era_prompt(raw_prompt, self.era_constraint)
        self.assertNotIn("swords", sanitized)
        self.assertNotIn("hanfu", sanitized)
        self.assertNotIn("dragon chariot", sanitized)
        self.assertIn("student uniform", sanitized)
        self.assertIn("holding pencil", sanitized)

    def test_graph_combined_sanitize_prompt(self):
        graph = DynamicSceneGraph(
            enclosures={"classroom": self.enclosed_room},
            era_genre=self.era_constraint,
            active_enclosure_id="classroom"
        )
        raw_prompt = "1girl, wooden desk, blue sky, wearing robes, holding textbook"
        sanitized = graph.sanitize_prompt(raw_prompt)
        self.assertNotIn("blue sky", sanitized)
        self.assertNotIn("robes", sanitized)
        self.assertIn("wooden desk", sanitized)
        self.assertIn("holding textbook", sanitized)

    def test_graph_get_combined_negative_tokens(self):
        graph = DynamicSceneGraph(
            enclosures={"classroom": self.enclosed_room},
            era_genre=self.era_constraint,
            active_enclosure_id="classroom"
        )
        neg_tokens = graph.get_combined_negative_tokens()
        self.assertIn("outdoor", neg_tokens)
        self.assertIn("street", neg_tokens)
        self.assertIn("hanfu", neg_tokens)
        self.assertIn("flying sword", neg_tokens)


class TestSceneTransitionGating(unittest.TestCase):
    """4. Test Scene Transition Gating (locking vs valid transitions)."""

    def setUp(self):
        self.enc1 = SpaceEnclosure(
            id="room_12a",
            name="Lớp học 12A",
            connected_enclosures=["corridor_3f"],
            active_entities=["an"]
        )
        self.enc2 = SpaceEnclosure(
            id="corridor_3f",
            name="Hành lang tầng ba",
            connected_enclosures=["room_12a", "school_rooftop"],
            active_entities=[]
        )
        self.enc3 = SpaceEnclosure(
            id="school_rooftop",
            name="Sân thượng trường",
            connected_enclosures=["corridor_3f"],
            active_entities=[]
        )
        self.char = CharacterEntity(id="an", name="An", current_location_id="room_12a")

        self.graph = DynamicSceneGraph(
            entities={"an": self.char},
            enclosures={"room_12a": self.enc1, "corridor_3f": self.enc2, "school_rooftop": self.enc3},
            active_enclosure_id="room_12a"
        )

    def test_lock_enclosure_when_no_transition_verb(self):
        # Paragraph with intense action/monologue but NO spatial transition verbs
        prose = "An nắm chặt tay lại, ánh mắt nhìn thẳng về phía bảng đen. Nhịp tim đập thình thịch trong lồng ngực."
        gated = self.graph.gate_scene_transition(prose)
        self.assertEqual(gated, "room_12a")
        self.assertEqual(self.graph.active_enclosure_id, "room_12a")
        self.assertEqual(self.char.current_location_id, "room_12a")

    def test_valid_scene_transition_connected_enclosure(self):
        # Transition verb present and destination is connected
        prose = "An đứng dậy, mở cửa bước vào hành lang tầng ba vắng lặng."
        gated = self.graph.gate_scene_transition(prose)
        self.assertEqual(gated, "corridor_3f")
        self.assertEqual(self.graph.active_enclosure_id, "corridor_3f")
        self.assertEqual(self.char.current_location_id, "corridor_3f")
        self.assertIn("an", self.enc2.active_entities)
        self.assertNotIn("an", self.enc1.active_entities)

    def test_disconnected_scene_transition_rejected(self):
        # Direct jump from room_12a to school_rooftop (not directly connected)
        success = self.graph.transition_scene("school_rooftop", force=False)
        self.assertFalse(success)
        self.assertEqual(self.graph.active_enclosure_id, "room_12a")


class TestStoryMemoryDSGOIntegration(unittest.TestCase):
    """5. Test StoryMemory DSGO integration, serialization, and backward compatibility."""

    def test_story_memory_serialization_roundtrip(self):
        char = CharacterEntity(id="minh", name="Minh", visual_dna="Minh (uniform)", current_location_id="lab")
        enc = SpaceEnclosure(id="lab", name="Phòng thí nghiệm", boundary_type=BoundaryType.INDOOR_ENCLOSED)
        era = EraGenreConstraint(era_name="modern_2020s", genre_name="Sci-Fi Campus")
        dsg = DynamicSceneGraph(
            entities={"minh": char},
            enclosures={"lab": enc},
            era_genre=era,
            active_enclosure_id="lab"
        )

        bible = StoryBible(title="Hành Trình Bí Mật", genre="Sci-Fi Campus")
        mem = StoryMemory(story_bible=bible, dynamic_scene_graph=dsg)
        mem.append_chapter("Chương 1 nội dung khởi đầu.")

        # Serialize
        dumped = mem.to_dict()
        self.assertIn("dynamic_scene_graph", dumped)
        self.assertIsNotNone(dumped["dynamic_scene_graph"])

        # Deserialize
        loaded_mem = StoryMemory.from_dict(dumped)
        self.assertIsNotNone(loaded_mem.dynamic_scene_graph)
        self.assertEqual(loaded_mem.dynamic_scene_graph.active_enclosure_id, "lab")
        self.assertIn("minh", loaded_mem.dynamic_scene_graph.entities)
        self.assertEqual(loaded_mem.dynamic_scene_graph.era_genre.era_name, "modern_2020s")

    def test_story_memory_legacy_backward_compatibility(self):
        # Legacy dict without dynamic_scene_graph
        legacy_dict = {
            "session_id": "legacy-session-123",
            "story_bible": {"title": "Truyện cũ", "characters": [{"name": "An", "appearance": "tóc ngắn"}]},
            "chapter_summaries": ["Chương 1 tóm tắt"],
            "current_chapter": 1
        }
        mem = StoryMemory.from_dict(legacy_dict)
        self.assertIsNone(mem.dynamic_scene_graph)
        self.assertEqual(mem.story_bible.title, "Truyện cũ")

        # Auto-init from bible
        new_dsg = mem.init_scene_graph_from_bible()
        self.assertIsNotNone(new_dsg)
        self.assertIsNotNone(mem.dynamic_scene_graph)
        self.assertIn("an", mem.dynamic_scene_graph.entities)

    def test_story_memory_to_prompt_block_formatting(self):
        char = CharacterEntity(id="an", name="An", visual_dna="An (uniform)", current_location_id="classroom")
        enc = SpaceEnclosure(
            id="classroom",
            name="Lớp học 12A",
            architectural_anchor="bàn gỗ thẳng hàng, cửa sổ ô lớn",
            persistent_fixtures=["bảng xanh", "phấn trắng"]
        )
        dsg = DynamicSceneGraph(
            entities={"an": char},
            enclosures={"classroom": enc},
            active_enclosure_id="classroom"
        )
        mem = StoryMemory(dynamic_scene_graph=dsg)
        prompt_block = mem.to_prompt_block()

        self.assertIn("DYNAMIC SCENE-GRAPH (RÀNG BUỘC 3 CHIỀU)", prompt_block)
        self.assertIn("Lớp học 12A", prompt_block)
        self.assertIn("bàn gỗ thẳng hàng", prompt_block)
        self.assertIn("An -> Lớp học 12A", prompt_block)
        self.assertIn("LONG-TERM MEMORY", prompt_block)


class TestAgentIntegration(unittest.TestCase):
    """6. Test StoryGenerator & MemoryExtractor integration with DSGO."""

    @patch("llm.groq_client.Groq")
    def test_story_generator_extract_narrative_ontology(self, mock_groq):
        gen = StoryGenerator()
        gen.llm.chat = MagicMock(return_value="""[THỰC THỂ & NHÂN VẬT]: An và Minh
[QUAN HỆ & ĐỘNG CƠ]: Bạn cùng bàn
[QUY TẮC THẾ GIỚI & BỐI CẢNH (WORLD AXIOMS)]: Học đường hiện đại 2024
[KHÔNG GIAN PHÂN CẢNH & NEO GIỮ KIẾN TRÚC (SPATIAL SCENE ENCLOSURE)]: Lớp 12A, cửa kính, bàn gỗ
[CHUỖI NHÂN QUẢ CHÍNH]: Bí mật -> Phát hiện -> Đối đầu
[CẤU TRÚC 5 NHỊP KỊCH TÍNH (5 DRAMATIC BEATS)]:
  + Beat 1: Hook
  + Beat 2: Rising Friction
  + Beat 3: Turning Point
  + Beat 4: Visceral Climax
  + Beat 5: Lingering Cliffhanger""")

        ontology = gen._extract_narrative_ontology("Phác thảo bối cảnh học đường")
        self.assertIn("THỰC THỂ & NHÂN VẬT", ontology)
        self.assertIn("SPATIAL SCENE ENCLOSURE", ontology)
        self.assertIn("5 DRAMATIC BEATS", ontology)

    @patch("llm.groq_client.Groq")
    def test_memory_extractor_spatial_transitions(self, mock_groq):
        extractor = MemoryExtractor()
        # Mock LLM return with spatial transitions JSON
        extractor.llm.chat = MagicMock(return_value="""{
            "chapter_summary": "An và Minh nói chuyện trong lớp rồi An bước vào thư viện.",
            "character_states": {"An": "quyết tâm tìm manh mối", "Minh": "nghi ngờ"},
            "new_threads": ["Manh mối cuốn sách cổ"],
            "resolved_threads": [],
            "relationships": {"An-Minh": "thăm dò lẫn nhau"},
            "spatial_transitions": [
                {"character": "An", "new_location": "Thư viện trường", "action": "bước vào thư viện"}
            ],
            "active_scene_location": "Thư viện trường"
        }""")

        char = CharacterEntity(id="an", name="An", current_location_id="classroom")
        enc = SpaceEnclosure(id="classroom", name="Lớp học", connected_enclosures=[])
        dsg = DynamicSceneGraph(
            entities={"an": char},
            enclosures={"classroom": enc},
            active_enclosure_id="classroom"
        )
        mem = StoryMemory(dynamic_scene_graph=dsg)

        updated_mem = extractor.extract_memory("An mở cửa bước vào thư viện trường...", mem)
        self.assertEqual(len(updated_mem.chapter_summaries), 1)
        # Verify An's location updated
        self.assertIn("an", updated_mem.dynamic_scene_graph.entities)
        self.assertNotEqual(updated_mem.dynamic_scene_graph.entities["an"].current_location_id, "classroom")

    @patch("llm.groq_client.Groq")
    def test_story_generator_chapter_stream_spatial_enclosure(self, mock_groq):
        gen = StoryGenerator()
        gen.llm.chat_stream = MagicMock(return_value=iter(["Chương 2", " tiếp tục..."]))

        enc = SpaceEnclosure(
            id="lab_room",
            name="Phòng thực hành Hóa",
            boundary_type=BoundaryType.INDOOR_ENCLOSED,
            architectural_anchor="bàn thí nghiệm mặt đá đen, tủ kính đựng hóa chất"
        )
        dsg = DynamicSceneGraph(
            enclosures={"lab_room": enc},
            active_enclosure_id="lab_room"
        )
        mem = StoryMemory(dynamic_scene_graph=dsg)

        # Call generate_chapter_stream
        gen.generate_chapter_stream(mem, user_instruction="Thêm đối thoại kịch tính")

        # Verify chat_stream called with messages containing SPATIAL SCENE ENCLOSURE
        call_args = gen.llm.chat_stream.call_args
        self.assertIsNotNone(call_args)
        messages = call_args[0][0]
        sys_prompt = messages[0]["content"]

        self.assertIn("SPATIAL SCENE ENCLOSURE", sys_prompt)
        self.assertIn("Phòng thực hành Hóa", sys_prompt)
        self.assertIn("bàn thí nghiệm mặt đá đen", sys_prompt)


if __name__ == "__main__":
    unittest.main()
