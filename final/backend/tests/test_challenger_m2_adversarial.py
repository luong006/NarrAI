import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Ensure backend directory is in sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

os.environ.setdefault("GROQ_API_KEY", "gsk_test_dummy_key_for_unit_tests")

from agents.comic_agent import ComicDirectorAgent
from services.cloudflare_ai import get_deterministic_comic_seed


class TestChallengerM2Adversarial(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with patch("llm.groq_client.Groq"):
            cls.agent = ComicDirectorAgent()

    # =========================================================================
    # 1. PRONOUN EDGE CASES IN VIETNAMESE DIALOGUE
    # =========================================================================
    def test_pronoun_co_be_single_female(self):
        """Dialogue with 'cô bé' injects female character DNA."""
        dna_map = {
            "An": {
                "dna": "An (17yo schoolgirl, blunt bob, navy ribbon tie)",
                "gender": "female",
                "role": "lead",
                "aliases": ["An"]
            }
        }
        panels = [{
            "panel_index": 1,
            "image_prompt": "Looking outside the window with gentle smile",
            "dialogue_text": "Cô bé nhìn bầu trời xanh và khẽ thở dài.",
            "layout_type": "square"
        }]
        validated = self.agent._validate_panels(panels, character_dna_map=dna_map)
        self.assertIn("An (17yo schoolgirl, blunt bob, navy ribbon tie)", validated[0]["image_prompt"])

    def test_pronoun_anh_ban_cung_ban_male_deskmate(self):
        """Dialogue with 'anh bạn cùng bàn' injects desk mate character DNA."""
        dna_map = {
            "Minh": {
                "dna": "Minh (17yo schoolboy, side-parted hair, white button-down shirt)",
                "gender": "male",
                "role": "desk mate",
                "aliases": ["Minh"]
            }
        }
        panels = [{
            "panel_index": 1,
            "image_prompt": "Turning to the side, passing a notebook",
            "dialogue_text": "Anh bạn cùng bàn khẽ cười: 'Bài tập hôm nay khó thật đấy.'",
            "layout_type": "square"
        }]
        validated = self.agent._validate_panels(panels, character_dna_map=dna_map)
        self.assertIn("Minh (17yo schoolboy, side-parted hair, white button-down shirt)", validated[0]["image_prompt"])

    def test_pronoun_cau_ay_male(self):
        """Dialogue with 'cậu ấy' injects male character DNA."""
        dna_map = {
            "Minh": {
                "dna": "Minh (17yo schoolboy, messy hair, glasses)",
                "gender": "male",
                "role": "classmate",
                "aliases": ["Minh"]
            }
        }
        panels = [{
            "panel_index": 1,
            "image_prompt": "Walking hurriedly through the hallway",
            "dialogue_text": "Cậu ấy ôm tập sách chạy thật nhanh về phía phòng thí nghiệm.",
            "layout_type": "square"
        }]
        validated = self.agent._validate_panels(panels, character_dna_map=dna_map)
        self.assertIn("Minh (17yo schoolboy, messy hair, glasses)", validated[0]["image_prompt"])

    def test_pronoun_hoc_sinh_general_student(self):
        """Dialogue with 'học sinh' matches student character."""
        dna_map = {
            "An": {
                "dna": "An (Vietnamese student, school uniform)",
                "gender": "female",
                "role": "student",
                "aliases": ["An"]
            }
        }
        panels = [{
            "panel_index": 1,
            "image_prompt": "Sitting at the front desk",
            "dialogue_text": "Người học sinh chăm chú lắng nghe bài giảng.",
            "layout_type": "square"
        }]
        validated = self.agent._validate_panels(panels, character_dna_map=dna_map)
        self.assertIn("An (Vietnamese student, school uniform)", validated[0]["image_prompt"])

    # =========================================================================
    # 2. FALSE POSITIVE BOUNDARIES
    # =========================================================================
    def test_false_positive_english_establishing_shot(self):
        """Character 'An' must NOT match 'an establishing shot'."""
        dna_map = {
            "An": {
                "dna": "An (schoolgirl, blunt bob)",
                "gender": "female",
                "role": "lead",
                "aliases": ["An"]
            }
        }
        panels = [{
            "panel_index": 1,
            "image_prompt": "An establishing shot of the high school courtyard",
            "dialogue_text": "Buổi sáng đầu thu trong lành tĩnh lặng.",
            "layout_type": "wide"
        }]
        validated = self.agent._validate_panels(panels, character_dna_map=dna_map)
        self.assertNotIn("An (schoolgirl, blunt bob)", validated[0]["image_prompt"])

    def test_false_positive_english_clean_and_panoramic(self):
        """Substrings in 'clean' or 'panoramic' must NOT trigger 'An'."""
        dna_map = {
            "An": {
                "dna": "An (schoolgirl, blunt bob)",
                "gender": "female",
                "role": "lead",
                "aliases": ["An"]
            }
        }
        panels = [{
            "panel_index": 1,
            "image_prompt": "A panoramic view of a clean classroom interior",
            "dialogue_text": "Không gian yên tĩnh.",
            "layout_type": "wide"
        }]
        validated = self.agent._validate_panels(panels, character_dna_map=dna_map)
        self.assertNotIn("An (schoolgirl, blunt bob)", validated[0]["image_prompt"])

    def test_false_positive_vietnamese_token_bat_an(self):
        """Adversarial stress-test: Vietnamese word 'bất an' (anxious) should NOT inject character 'An'."""
        dna_map = {
            "An": {
                "dna": "An (schoolgirl, blunt bob)",
                "gender": "female",
                "role": "lead",
                "aliases": ["An"]
            }
        }
        # In this scene, Minh is alone feeling anxious ('bất an')
        panels = [{
            "panel_index": 1,
            "image_prompt": "A dark empty hallway at night",
            "dialogue_text": "Cảm giác bất an bao trùm toàn bộ hành lang vắng.",
            "layout_type": "square"
        }]
        validated = self.agent._validate_panels(panels, character_dna_map=dna_map)
        is_leaked = "An (schoolgirl, blunt bob)" in validated[0]["image_prompt"]
        print(f"[Stress Test] 'bất an' false positive leak detected: {is_leaked}")
        self.assertFalse(
            is_leaked,
            "Vietnamese compound word 'bất an' must NOT falsely inject character 'An'!"
        )

    def test_false_positive_vietnamese_compound_words_an(self):
        """Comprehensive verification: 'bình an', 'an toàn', 'an tâm', 'an ninh', 'an dưỡng' do not trigger character 'An'."""
        dna_map = {
            "An": {
                "dna": "An (schoolgirl, blunt bob)",
                "gender": "female",
                "role": "lead",
                "aliases": ["An"]
            }
        }
        compound_sentences = [
            "Chúc mọi người một ngày bình an và may mắn.",
            "Khu vực này tuyệt đối an toàn.",
            "Xin mọi người hãy an tâm nghỉ ngơi.",
            "Lực lượng an ninh đang túc trực bên ngoài.",
            "Khu an dưỡng nằm sâu trong rừng thông yên tĩnh."
        ]
        for sentence in compound_sentences:
            panels = [{
                "panel_index": 1,
                "image_prompt": "A quiet peaceful hallway",
                "dialogue_text": sentence,
                "layout_type": "square"
            }]
            validated = self.agent._validate_panels(panels, character_dna_map=dna_map)
            self.assertNotIn(
                "An (schoolgirl, blunt bob)",
                validated[0]["image_prompt"],
                f"Vietnamese compound word in '{sentence}' must NOT falsely inject character 'An'!"
            )

        # But genuine occurrence of An in the presence of compound word must match!
        panels_genuine = [{
            "panel_index": 1,
            "image_prompt": "Classroom interior",
            "dialogue_text": "Dù cảm thấy bất an, An vẫn mỉm cười nhẹ nhàng.",
            "layout_type": "square"
        }]
        validated_genuine = self.agent._validate_panels(panels_genuine, character_dna_map=dna_map)
        self.assertIn(
            "An (schoolgirl, blunt bob)",
            validated_genuine[0]["image_prompt"],
            "Genuine character 'An' must be injected even when 'bất an' appears in the same sentence!"
        )

    # =========================================================================
    # 3. MULTI-CHARACTER SCENE PROMPT CONSTRUCTION
    # =========================================================================
    def test_multi_character_injection_no_crash(self):
        """Both characters' DNAs must be injected into image_prompt without crashing."""
        dna_map = {
            "Lý Tiêu": {
                "dna": "Lý Tiêu (high ponytail, black-gold robes)",
                "gender": "male",
                "role": "lead",
                "aliases": ["Lý Tiêu", "ly tieu"]
            },
            "Hắc Ma Quân": {
                "dna": "Hắc Ma Quân (crimson cape, demonic armor)",
                "gender": "male",
                "role": "antagonist",
                "aliases": ["Hắc Ma Quân", "ma quan"]
            }
        }
        panels = [{
            "panel_index": 1,
            "image_prompt": "Lý Tiêu faces Hắc Ma Quân atop the mountain peak",
            "dialogue_text": "Lý Tiêu: 'Hôm nay ta và ngươi quyết một trận tử chiến!'",
            "layout_type": "wide"
        }]
        validated = self.agent._validate_panels(panels, character_dna_map=dna_map)
        self.assertEqual(len(validated), 1)
        res_prompt = validated[0]["image_prompt"]
        self.assertIn("Lý Tiêu (high ponytail, black-gold robes)", res_prompt)
        self.assertIn("Hắc Ma Quân (crimson cape, demonic armor)", res_prompt)

    def test_multi_character_pronoun_dialogue(self):
        """Dialogue with both 'cô bé' and 'anh bạn cùng bàn' injects both DNAs."""
        dna_map = {
            "An": {
                "dna": "An (female student, blunt bangs, blue ribbon tie)",
                "gender": "female",
                "role": "lead",
                "aliases": ["An"]
            },
            "Minh": {
                "dna": "Minh (male student, messy dark hair, white shirt)",
                "gender": "male",
                "role": "desk mate",
                "aliases": ["Minh"]
            }
        }
        panels = [{
            "panel_index": 1,
            "image_prompt": "Two students sitting in the classroom during afternoon sunlight",
            "dialogue_text": "Cô bé nhìn anh bạn cùng bàn mỉm cười rạng rỡ.",
            "layout_type": "wide"
        }]
        validated = self.agent._validate_panels(panels, character_dna_map=dna_map)
        res_prompt = validated[0]["image_prompt"]
        self.assertIn("An (female student, blunt bangs, blue ribbon tie)", res_prompt)
        self.assertIn("Minh (male student, messy dark hair, white shirt)", res_prompt)

    # =========================================================================
    # 4. DETERMINISTIC SEED FORMULA AND BOUNDS
    # =========================================================================
    def test_seed_determinism_and_bounds(self):
        """Verify identical story IDs yield identical seeds and all seeds fall in [100000, 999999]."""
        # Invariance across repeated calls
        for sid in [1, 2, 42, 999, 123456]:
            seed_first = get_deterministic_comic_seed(sid)
            for _ in range(50):
                self.assertEqual(get_deterministic_comic_seed(sid), seed_first)

        # Bounds testing across 1,000 distinct story IDs
        for sid in range(1000):
            seed = get_deterministic_comic_seed(sid)
            self.assertTrue(100000 <= seed <= 999999, f"Seed {seed} for story_id {sid} out of bounds")

        # Edge cases: None, 0, negative story_id
        for sid in [None, 0, -1, -9999]:
            seed = get_deterministic_comic_seed(sid)
            self.assertTrue(100000 <= seed <= 999999, f"Seed {seed} for story_id {sid} out of bounds")

    # =========================================================================
    # 5. CRITICAL BUG REPRODUCTION: GENDER CLASSIFICATION SUBSTRING DEFECT
    # =========================================================================
    def test_reproduce_critical_gender_classification_bug(self):
        """
        EMPIRICAL BUG REPRODUCTION:
        In comic_agent.py line 304:
            is_male = gender == 'male' or 'male' in gender ...
        Because 'male' is a substring of 'female' ('male' in 'female' is True),
        any character with gender='female' evaluates to is_male=True!

        As a consequence, when a prompt has a male cue ('schoolboy'),
        males = [c for c in char_entry_list if c.get('is_male')] includes the female character,
        and selects the female character instead of the male character!
        """
        dna_map = {
            "An": {
                "dna": "An (17yo girl, blunt bob, ribbon tie)",
                "gender": "female",
                "role": "lead",
                "aliases": ["An"]
            },
            "Minh": {
                "dna": "Minh (17yo boy, neat hair, school uniform)",
                "gender": "male",
                "role": "supporting",
                "aliases": ["Minh"]
            }
        }

        # Prompt explicitly describing a boy
        p_male = [{
            "panel_index": 1,
            "image_prompt": "A schoolboy sitting quietly reading in the library",
            "dialogue_text": ""
        }]
        v_male = self.agent._validate_panels(p_male, character_dna_map=dna_map)

        # Expected correct behavior: Minh is injected, An is NOT injected.
        # Defective behavior: An is injected because 'male' in 'female' is True!
        an_injected = "An (17yo girl" in v_male[0]["image_prompt"]
        minh_injected = "Minh (17yo boy" in v_male[0]["image_prompt"]

        print(f"\n[CRITICAL BUG CHECK] Prompt: 'A schoolboy sitting quietly reading in the library'")
        print(f"[CRITICAL BUG CHECK] Injected output: {v_male[0]['image_prompt']}")
        print(f"[CRITICAL BUG CHECK] Did female character An get injected? {an_injected}")
        print(f"[CRITICAL BUG CHECK] Did male character Minh get injected? {minh_injected}")

        # This assertion demonstrates the bug:
        self.assertFalse(
            an_injected,
            "CRITICAL DEFECT: Female character An was injected into male scene because 'male' in 'female' evaluates to True!"
        )
        self.assertTrue(
            minh_injected,
            "CRITICAL DEFECT: Male character Minh was NOT injected into male scene!"
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
