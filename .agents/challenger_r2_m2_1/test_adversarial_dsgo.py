"""
Adversarial Stress-Test Suite for Milestone 2: Dynamic Scene-Graph Ontology (DSGO) & Spatial Scene Enclosure.
Author: challenger_r2_m2_1 (Adversarial Verifier Subagent)

Stress-tests:
1. Scene transition gating with complex Vietnamese sentences (negation, deceptive verbs, shadowing).
2. Spatial drift sanitization (subwords, compound words, punctuation, uppercase/lowercase).
3. Disconnected scene transitions and multi-hop movement (teleportation, location leakage).
4. Deceased character vitality invariant edge cases (speaking, moving, unconscious states).
5. Deserialization of malformed, partial, or corrupted dynamic_scene_graph dictionaries.
"""
import os
import sys
import unittest
from typing import Dict, Any

# Ensure backend is on sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

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


class TestAdversarialSceneTransitionGating(unittest.TestCase):
    """Adversarial testing of Scene Transition Gating."""

    def setUp(self):
        self.enc_room = SpaceEnclosure(
            id="classroom_12a",
            name="Lớp học 12A",
            boundary_type=BoundaryType.INDOOR_ENCLOSED,
            connected_enclosures=["corridor_3f"],
            active_entities=["an"]
        )
        self.enc_corridor = SpaceEnclosure(
            id="corridor_3f",
            name="Hành lang",
            boundary_type=BoundaryType.INDOOR_ENCLOSED,
            connected_enclosures=["classroom_12a", "school_rooftop"],
            active_entities=[]
        )
        self.enc_distant_field = SpaceEnclosure(
            id="soccer_field",
            name="Sân bóng",
            boundary_type=BoundaryType.OUTDOOR_OPEN,
            connected_enclosures=[],
            active_entities=[]
        )
        self.enc_rooftop = SpaceEnclosure(
            id="school_rooftop",
            name="Sân thượng",
            boundary_type=BoundaryType.OUTDOOR_CONFINED,
            connected_enclosures=["corridor_3f"],
            active_entities=[]
        )
        self.char = CharacterEntity(
            id="an",
            name="An",
            current_location_id="classroom_12a"
        )
        self.graph = DynamicSceneGraph(
            entities={"an": self.char},
            enclosures={
                "classroom_12a": self.enc_room,
                "corridor_3f": self.enc_corridor,
                "soccer_field": self.enc_distant_field,
                "school_rooftop": self.enc_rooftop
            },
            active_enclosure_id="classroom_12a"
        )

    def test_negation_khong_buoc_ra_khoi_phong(self):
        """
        FAIL CASE: Prose explicitly negates transition:
        'An kiên quyết không bước ra khỏi phòng mà tiếp tục ngồi ở bàn học nhìn ra hành lang.'
        Current gating matches 'bước ra khỏi' and transitions to 'corridor_3f'.
        Expected: Scene remains firmly locked at 'classroom_12a'.
        """
        prose = "An kiên quyết không bước ra khỏi phòng mà tiếp tục ngồi ở bàn học nhìn ra hành lang."
        result = self.graph.gate_scene_transition(prose)
        self.assertEqual(
            result, "classroom_12a",
            f"VULNERABILITY: Negation ignored! Transitioned to '{result}' despite 'không bước ra khỏi phòng'."
        )
        self.assertEqual(self.graph.active_enclosure_id, "classroom_12a")

    def test_negation_khong_buoc_vao(self):
        """
        FAIL CASE: Prose negates entering destination:
        'Cô bé ngập ngừng rồi nhất quyết không bước vào hành lang tối tăm.'
        Expected: Scene remains locked at 'classroom_12a'.
        """
        prose = "Cô bé ngập ngừng rồi nhất quyết không bước vào hành lang tối tăm."
        result = self.graph.gate_scene_transition(prose)
        self.assertEqual(
            result, "classroom_12a",
            f"VULNERABILITY: Negation ignored! Transitioned to '{result}' despite 'không bước vào'."
        )

    def test_negation_tu_choi_roi_phong(self):
        """
        FAIL CASE: Prose uses refusal verb:
        'Minh từ chối rời phòng dù tiếng ồn ngoài hành lang ngày càng lớn.'
        Expected: Scene remains locked at 'classroom_12a'.
        """
        prose = "Minh từ chối rời phòng dù tiếng ồn ngoài hành lang ngày càng lớn."
        result = self.graph.gate_scene_transition(prose)
        self.assertEqual(
            result, "classroom_12a",
            f"VULNERABILITY: Refusal ignored! Transitioned to '{result}' despite 'từ chối rời phòng'."
        )

    def test_deceptive_verb_mo_cua_so(self):
        """
        FAIL CASE: Deceptive verb:
        'An đứng dậy mở cửa sổ nhìn ra hành lang bên ngoài.'
        'mở cửa sổ' (opening window) matches r'mở\\s+cửa'.
        Expected: Scene remains at 'classroom_12a'.
        """
        prose = "An đứng dậy mở cửa sổ nhìn ra hành lang bên ngoài."
        result = self.graph.gate_scene_transition(prose)
        self.assertEqual(
            result, "classroom_12a",
            f"VULNERABILITY: Opening window triggered enclosure transition to '{result}'!"
        )

    def test_empty_and_whitespace_prose(self):
        """Test boundary conditions with empty, whitespace, and None text."""
        self.assertEqual(self.graph.gate_scene_transition(""), "classroom_12a")
        self.assertEqual(self.graph.gate_scene_transition("   \n\t  "), "classroom_12a")
        self.assertEqual(self.graph.gate_scene_transition(None), "classroom_12a")

    def test_destination_shadowing_by_unconnected_mention(self):
        """
        FAIL CASE: Text mentions an unconnected location in past memory before the real transition:
        'Nhớ lại trận chung kết nghẹt thở trên sân bóng hôm qua, An vội vã mở cửa bước vào hành lang.'
        If 'sân bóng' is matched first in dict iteration, transition_scene('soccer_field') fails (unconnected),
        and the break statement causes the loop to abort, completely missing 'hành lang'!
        Expected: Transition should succeed to 'corridor_3f'.
        """
        prose = "Nhớ lại trận chung kết nghẹt thở trên sân bóng hôm qua, An vội vã mở cửa bước vào hành lang."
        result = self.graph.gate_scene_transition(prose)
        self.assertEqual(
            result, "corridor_3f",
            f"VULNERABILITY: Destination shadowed! Failed to transition to 'corridor_3f', got '{result}'."
        )


class TestAdversarialSpatialDriftSanitization(unittest.TestCase):
    """Adversarial testing of Spatial Drift Sanitization."""

    def setUp(self):
        self.enclosure = SpaceEnclosure(
            id="classroom",
            name="Classroom",
            boundary_type=BoundaryType.INDOOR_ENCLOSED,
            negative_drift_tokens=["street (outdoor)", "sun-sky"]
        )

    def test_subword_preservation(self):
        """
        Verify subwords containing banned keywords are preserved:
        'classroom' (contains room), 'streetwear' (contains street), 'sunlight' (contains sun/light).
        """
        raw = "1girl, inside classroom, wearing streetwear, bathed in sunlight, outdoor, street cars, blue sky"
        sanitized = sanitize_spatial_prompt(raw, self.enclosure)
        self.assertIn("classroom", sanitized)
        self.assertIn("streetwear", sanitized)
        self.assertIn("sunlight", sanitized)
        self.assertNotIn("outdoor", sanitized)
        self.assertNotIn("blue sky", sanitized)

    def test_hyphenated_compound_mutilation(self):
        """
        FAIL CASE: Hyphenated compound words:
        Regex \\b matches between \\w and \\W. Hyphen '-' is \\W!
        So 'street-style jacket, off-road vehicle, car-free zone'
        gets mutilated into ', -style jacket, off-, vehicle, , -free zone'.
        """
        raw = "1boy, wearing street-style jacket, driving off-road vehicle, entering car-free zone"
        sanitized = sanitize_spatial_prompt(raw, self.enclosure)
        # Should not produce broken punctuation tokens like ', -style' or 'off-, '
        self.assertNotIn(", -style", sanitized, "VULNERABILITY: Hyphenated word mutilated into ', -style'!")
        self.assertNotIn("off-, ", sanitized, "VULNERABILITY: Hyphenated word mutilated into 'off-, '!")
        self.assertNotIn(", -free", sanitized, "VULNERABILITY: Hyphenated word mutilated into ', -free'!")

    def test_negative_drift_token_with_parentheses(self):
        """
        FAIL CASE: Custom negative drift token containing parentheses 'street (outdoor)'.
        Regex \\b after ')' fails because ')' and ',' or ' ' are both \\W!
        So 'street (outdoor)' is NEVER removed!
        """
        raw = "1girl, sitting at desk, street (outdoor), quiet atmosphere"
        sanitized = sanitize_spatial_prompt(raw, self.enclosure)
        self.assertNotIn(
            "street (outdoor)", sanitized,
            "VULNERABILITY: Token with parentheses was not stripped due to \\b regex boundary failure!"
        )

    def test_punctuation_artifacts(self):
        """
        FAIL CASE: Banned token followed by period or semicolon:
        'inside room. street. sitting at desk'
        Replacing 'street' with ', ' produces 'inside room., sitting at desk' with broken '.,' syntax.
        """
        raw = "inside room. street. sitting at desk"
        sanitized = sanitize_spatial_prompt(raw, self.enclosure)
        self.assertNotIn(".,", sanitized, "VULNERABILITY: Sanitizer created illegal '.,' punctuation artifact!")


class TestAdversarialDisconnectedAndMultiHop(unittest.TestCase):
    """Adversarial testing of Disconnected Enclosure Transitions & State Leakage."""

    def setUp(self):
        self.enc_a = SpaceEnclosure(id="room_a", name="Phòng A", connected_enclosures=["corridor"], active_entities=["an"])
        self.enc_corridor = SpaceEnclosure(id="corridor", name="Hành lang", connected_enclosures=["room_a", "room_c"], active_entities=[])
        self.enc_b_distant = SpaceEnclosure(id="room_b", name="Phòng B (cách biệt)", connected_enclosures=[], active_entities=["minh"])
        self.enc_c = SpaceEnclosure(id="room_c", name="Phòng C", connected_enclosures=["corridor"], active_entities=[])

        self.char_an = CharacterEntity(id="an", name="An", current_location_id="room_a")
        self.char_minh = CharacterEntity(id="minh", name="Minh", current_location_id="room_b")

        self.graph = DynamicSceneGraph(
            entities={"an": self.char_an, "minh": self.char_minh},
            enclosures={"room_a": self.enc_a, "corridor": self.enc_corridor, "room_b": self.enc_b_distant, "room_c": self.enc_c},
            active_enclosure_id="room_a"
        )

    def test_direct_disconnected_jump_rejected(self):
        """Multi-hop jump Room A -> Room C without visiting corridor must be rejected."""
        success = self.graph.transition_scene("room_c", force=False)
        self.assertFalse(success)
        self.assertEqual(self.graph.active_enclosure_id, "room_a")

    def test_character_teleportation_and_location_leak(self):
        """
        CRITICAL VULNERABILITY: Teleportation & State Desync.
        Character 'Minh' is in disconnected 'room_b'.
        Caller transitions from 'room_a' to 'corridor' (which is connected to room_a),
        but passes moving_character_ids=['minh'].
        Current transition_scene logic:
        1. Checks if corridor is connected to room_a (YES).
        2. Sets minh.current_location_id = 'corridor'.
        3. Attempts to remove 'minh' from current_enc.active_entities (room_a).
           Minh is NOT in room_a, so room_b is NEVER updated!
        4. Minh is now in room_b.active_entities AND corridor.active_entities!
        Expected: Characters in disconnected enclosures cannot be moved across unrelated transitions.
        """
        success = self.graph.transition_scene("corridor", moving_character_ids=["minh"], force=False)
        # Check if Minh remained in room_b or was illegally duplicated/teleported
        if success:
            self.assertNotIn(
                "minh", self.enc_b_distant.active_entities,
                "VULNERABILITY: Minh was teleported to corridor but still remains in room_b.active_entities (entity duplication)!"
            )
            # Also verify if teleporting an entity from a disconnected room is prohibited
            self.assertEqual(
                self.char_minh.current_location_id, "room_b",
                "VULNERABILITY: Entity in disconnected room was teleported into corridor during an unrelated transition!"
            )


class TestAdversarialVitalityInvariant(unittest.TestCase):
    """Adversarial testing of Character Vitality Invariant."""

    def setUp(self):
        self.corpse = CharacterEntity(
            id="corpse",
            name="Xác chết",
            vitality_state=VitalityState.DECEASED,
            current_location_id="room_a"
        )
        self.unconscious_char = CharacterEntity(
            id="sleeping_beauty",
            name="Hôn mê",
            vitality_state=VitalityState.UNCONSCIOUS,
            current_location_id="room_a"
        )
        self.living_char = CharacterEntity(
            id="an",
            name="An",
            vitality_state=VitalityState.ALIVE,
            current_location_id="room_a"
        )
        self.enc_a = SpaceEnclosure(id="room_a", name="Phòng A", connected_enclosures=["corridor"], active_entities=["corpse", "sleeping_beauty", "an"])
        self.enc_corridor = SpaceEnclosure(id="corridor", name="Hành lang", connected_enclosures=["room_a"], active_entities=[])

        self.graph = DynamicSceneGraph(
            entities={"corpse": self.corpse, "sleeping_beauty": self.unconscious_char, "an": self.living_char},
            enclosures={"room_a": self.enc_a, "corridor": self.enc_corridor},
            active_enclosure_id="room_a"
        )

    def test_deceased_cannot_act(self):
        """Deceased character must not perform active actions."""
        valid, err = self.graph.validate_vitality("corpse", "SPEAKS")
        self.assertFalse(valid)
        self.assertIn("VITALITY_VIOLATION", err)

    def test_deceased_moving_themselves_in_transition(self):
        """
        FAIL CASE: Can a deceased character walk into another room during scene transition?
        Current transition_scene moves all active_entities (including deceased) without checking vitality.
        A corpse cannot walk into the next room on their own!
        """
        # Call transition_scene with corpse moving on its own
        self.graph.transition_scene("corridor", moving_character_ids=["corpse"])
        # Expected: A deceased character should not autonomously transition location
        self.assertNotEqual(
            self.corpse.current_location_id, "corridor",
            "VULNERABILITY: Deceased character walked autonomously into corridor during transition!"
        )

    def test_unconscious_character_cannot_perform_active_actions(self):
        """
        FAIL CASE: Unconscious character attempting to SPEAK or RUN.
        Current validate_vitality only checks vitality_state == VitalityState.DECEASED.
        An UNCONSCIOUS character is allowed to speak or run!
        """
        valid, err = self.graph.validate_vitality("sleeping_beauty", "SPEAKS")
        self.assertFalse(
            valid,
            "VULNERABILITY: Unconscious character was allowed to SPEAK! validate_vitality only checked DECEASED."
        )


class TestAdversarialDeserialization(unittest.TestCase):
    """Adversarial testing of Malformed, Partial, or Corrupted Dictionary Deserialization."""

    def test_corrupted_entities_field_raises_unhandled_exception(self):
        """
        CRITICAL VULNERABILITY: from_dict() does not wrap model_validate in try/except.
        Passing {'entities': 'corrupted_string'} crashes with unhandled pydantic_core.ValidationError!
        Expected: from_dict should gracefully handle corrupted data and return a safe default graph.
        """
        corrupted_data = {
            "session_id": "test-crash",
            "entities": "invalid_not_a_dict",
            "enclosures": {}
        }
        try:
            graph = DynamicSceneGraph.from_dict(corrupted_data)
            self.assertIsInstance(graph, DynamicSceneGraph)
        except Exception as e:
            self.fail(f"VULNERABILITY: DynamicSceneGraph.from_dict crashed with unhandled {type(e).__name__}: {e}")

    def test_corrupted_enclosures_field_crashes(self):
        """Passing {'enclosures': [1, 2, 3]} crashes with unhandled ValidationError."""
        corrupted_data = {
            "enclosures": [1, 2, 3]
        }
        try:
            graph = DynamicSceneGraph.from_dict(corrupted_data)
            self.assertIsInstance(graph, DynamicSceneGraph)
        except Exception as e:
            self.fail(f"VULNERABILITY: DynamicSceneGraph.from_dict crashed with unhandled {type(e).__name__}: {e}")

    def test_none_value_for_non_optional_field_crashes(self):
        """Passing {'era_genre': None} crashes with unhandled ValidationError."""
        corrupted_data = {
            "era_genre": None
        }
        try:
            graph = DynamicSceneGraph.from_dict(corrupted_data)
            self.assertIsInstance(graph, DynamicSceneGraph)
        except Exception as e:
            self.fail(f"VULNERABILITY: DynamicSceneGraph.from_dict crashed with unhandled {type(e).__name__}: {e}")

    def test_corrupted_entity_item_crashes(self):
        """Entity dictionary missing mandatory 'name' field crashes with unhandled ValidationError."""
        corrupted_data = {
            "entities": {
                "char_broken": {"id": "c1"}  # missing 'name'
            }
        }
        try:
            graph = DynamicSceneGraph.from_dict(corrupted_data)
            self.assertIsInstance(graph, DynamicSceneGraph)
        except Exception as e:
            self.fail(f"VULNERABILITY: DynamicSceneGraph.from_dict crashed with unhandled {type(e).__name__}: {e}")

    def test_invalid_enum_value_crashes(self):
        """Entity dictionary with invalid enum value 'zombie' crashes with unhandled ValidationError."""
        corrupted_data = {
            "entities": {
                "c1": {"id": "c1", "name": "C1", "vitality_state": "undead_zombie"}
            }
        }
        try:
            graph = DynamicSceneGraph.from_dict(corrupted_data)
            self.assertIsInstance(graph, DynamicSceneGraph)
        except Exception as e:
            self.fail(f"VULNERABILITY: DynamicSceneGraph.from_dict crashed with unhandled {type(e).__name__}: {e}")


if __name__ == "__main__":
    unittest.main()
