import os
import sys
import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch, MagicMock

# Ensure backend directory is in sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Set dummy key if not present for agent initialization
os.environ.setdefault("GROQ_API_KEY", "gsk_test_dummy_key_for_unit_tests")

from agents.comic_agent import (
    ComicDirectorAgent,
    DNA_EXTRACTOR_PROMPT,
    _format_character_dna_registry,
)
from services.cloudflare_ai import get_deterministic_comic_seed, get_cached_or_generate_image
from agents.story_memory import StoryMemory, StoryBible
import main


class TestComicDNASeed(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with patch("llm.groq_client.Groq"):
            cls.agent = ComicDirectorAgent()

    # ----------------------------------------------------------------------
    # 1. DNA Prompt Structure Verification
    # ----------------------------------------------------------------------
    def test_dna_extractor_prompt_structure(self):
        """Verify DNA_EXTRACTOR_PROMPT has extreme detail rules for costumes, accessories, and metadata."""
        prompt = DNA_EXTRACTOR_PROMPT.lower()
        
        # Costume and fabric
        self.assertIn("costume", prompt)
        self.assertIn("garment type", prompt)
        self.assertIn("fabric", prompt)
        
        # Collar and accessories
        self.assertIn("collar", prompt)
        self.assertTrue("ribbon tie" in prompt or "bow tie" in prompt)
        self.assertTrue("pendant" in prompt or "brooch" in prompt or "collar pin" in prompt)
        
        # Hair details
        self.assertIn("hairstyle", prompt)
        self.assertIn("bangs", prompt)
        self.assertIn("parting", prompt)
        
        # Facial details
        self.assertIn("facial", prompt)
        self.assertIn("eye shape", prompt)
        self.assertIn("jawline", prompt)
        
        # Metadata fields in schema
        self.assertIn("gender", prompt)
        self.assertIn("role", prompt)
        self.assertIn("aliases", prompt)
        self.assertIn("dna", prompt)

    def test_character_registry_prompt_includes_story_dna_and_aliases(self):
        registry = _format_character_dna_registry({
            "An": {
                "dna": "17yo schoolgirl with blunt bangs and navy ribbon tie",
                "gender": "female",
                "role": "lead",
                "aliases": ["Trần Thị An", "cô bé", "nữ sinh"],
            }
        })

        self.assertIn("17yo schoolgirl with blunt bangs and navy ribbon tie", registry)
        self.assertIn("aliases: Trần Thị An, cô bé, nữ sinh", registry)
        self.assertIn("female, lead", registry)

    # ----------------------------------------------------------------------
    # 2. Character DNA Extraction & Story Bible Aliases
    # ----------------------------------------------------------------------
    def test_extract_character_dna_story_bible_aliases(self):
        """Verify extract_character_dna enriches aliases from StoryMemory with Vietnamese pronouns and name tokens."""
        memory = StoryMemory()
        memory.story_bible = StoryBible()
        memory.story_bible.characters = [
            {
                "name": "Trần Thị An",
                "appearance": "17yo Vietnamese schoolgirl, shoulder-length black bob with blunt bangs, wearing white collared uniform shirt with navy ribbon tie, dark blue pleated skirt",
                "role": "lead student",
                "gender": "female"
            },
            {
                "name": "Nguyễn Văn Minh",
                "appearance": "17yo Vietnamese schoolboy, neat dark side-parted hair, wearing white button-down uniform shirt with dark trousers",
                "role": "desk mate, classmate",
                "gender": "male"
            }
        ]

        # Call extract_character_dna without network call by having story_bible populate existing_dna
        with patch.object(self.agent.llm, "chat", return_value="{}"):
            dna_map = self.agent.extract_character_dna("Truyện học đường...", memory=memory)

        # Check female lead An
        self.assertIn("Trần Thị An", dna_map)
        an_data = dna_map["Trần Thị An"]
        an_aliases = [a.lower() for a in an_data["aliases"]]
        self.assertIn("trần thị an", an_aliases)
        self.assertIn("an", an_aliases)
        self.assertTrue(any(p in an_aliases for p in ["cô bé", "nữ sinh", "cô ấy", "cô gái"]))

        # Check male desk mate Minh
        self.assertIn("Nguyễn Văn Minh", dna_map)
        minh_data = dna_map["Nguyễn Văn Minh"]
        minh_aliases = [a.lower() for a in minh_data["aliases"]]
        self.assertIn("nguyễn văn minh", minh_aliases)
        self.assertIn("minh", minh_aliases)
        self.assertTrue(any(p in minh_aliases for p in ["anh bạn", "bạn cùng bàn", "cậu ấy", "nam sinh"]))

    def test_story_bible_character_dna_remains_canonical(self):
        """LLM extraction may add aliases but must not overwrite established visual canon."""
        memory = StoryMemory()
        memory.story_bible = StoryBible()
        memory.story_bible.characters = [{
            "name": "Trần Thị An",
            "appearance": "17yo Vietnamese schoolgirl, blunt black bangs, white uniform shirt and navy ribbon tie",
            "role": "lead",
            "gender": "female",
        }]
        llm_result = {
            "Trần Thị An": {
                "gender": "female",
                "role": "lead",
                "aliases": ["An mới"],
                "dna": "adult woman with long blonde hair wearing a red evening dress",
            }
        }

        with patch.object(self.agent.llm, "chat", return_value=json.dumps(llm_result, ensure_ascii=False)):
            dna_map = self.agent.extract_character_dna("An bước vào lớp học.", memory=memory)

        an_data = dna_map["Trần Thị An"]
        self.assertEqual(
            an_data["dna"],
            "17yo Vietnamese schoolgirl, blunt black bangs, white uniform shirt and navy ribbon tie",
        )
        self.assertIn("An mới", an_data["aliases"])

    def test_story_bible_setting_anchor_remains_canonical(self):
        """A newly extracted setting cannot replace the setting already stored in story memory."""
        memory = StoryMemory()
        memory.story_bible = StoryBible()
        memory.story_bible.world_setting = "Sân thượng trường học với lan can kim loại"
        llm_result = {
            "location_name": "Ancient palace",
            "setting_anchor": "ornate palace hall with gold pillars and red banners",
            "atmosphere": "dramatic candlelight",
        }

        with patch.object(self.agent.llm, "chat", return_value=json.dumps(llm_result)):
            setting = self.agent.extract_setting_dna("An nhìn ra sân trường.", memory=memory)

        self.assertEqual(setting["setting_anchor"], "Sân thượng trường học với lan can kim loại")
        self.assertEqual(setting["location_name"], "Bối cảnh chính")

    # ----------------------------------------------------------------------
    # 3. Smart DNA Injection with Vietnamese Pronouns
    # ----------------------------------------------------------------------
    def test_smart_dna_injection_female_pronoun(self):
        """Dialogue with female pronoun ('cô bé') injects female lead's DNA even without name in prompt."""
        dna_map = {
            "An": {
                "dna": "17yo Vietnamese schoolgirl, blunt bangs, navy ribbon tie",
                "gender": "female",
                "role": "lead",
                "aliases": ["An", "cô bé", "nữ sinh"]
            }
        }
        panels = [
            {
                "panel_index": 1,
                "image_prompt": "Looking outside the window with gentle smile",
                "dialogue_text": "Cô bé nhìn bầu trời xanh và khẽ thở dài.",
                "layout_type": "square"
            }
        ]
        validated = self.agent._validate_panels(panels, character_dna_map=dna_map)
        self.assertEqual(len(validated), 1)
        # DNA should be injected into image_prompt
        self.assertIn("17yo Vietnamese schoolgirl, blunt bangs, navy ribbon tie", validated[0]["image_prompt"])

    def test_smart_dna_injection_male_deskmate_pronoun(self):
        """Dialogue with male/desk mate pronoun ('anh bạn cùng bàn') injects desk mate's DNA."""
        dna_map = {
            "Minh": {
                "dna": "17yo Vietnamese schoolboy, side-parted hair, white button-down shirt",
                "gender": "male",
                "role": "desk mate",
                "aliases": ["Minh", "anh bạn cùng bàn", "bạn cùng bàn", "cậu ấy"]
            }
        }
        panels = [
            {
                "panel_index": 1,
                "image_prompt": "Turning to the side, passing a notebook",
                "dialogue_text": "Anh bạn cùng bàn khẽ cười: 'Bài tập hôm nay khó thật đấy.'",
                "layout_type": "square"
            }
        ]
        validated = self.agent._validate_panels(panels, character_dna_map=dna_map)
        self.assertEqual(len(validated), 1)
        self.assertIn("17yo Vietnamese schoolboy, side-parted hair, white button-down shirt", validated[0]["image_prompt"])

    # ----------------------------------------------------------------------
    # 4. Regex Word Boundary Protection Against False Positives
    # ----------------------------------------------------------------------
    def test_regex_boundary_protection_an_false_positives(self):
        """Character named 'An' must NOT match English article 'an establishing shot', 'clean', or 'another'."""
        dna_map = {
            "An": {
                "dna": "17yo schoolgirl An, blunt bangs, navy ribbon tie",
                "gender": "female",
                "role": "lead",
                "aliases": ["An"]
            }
        }
        
        # Test 1: "An establishing shot"
        p1 = [{"panel_index": 1, "image_prompt": "An establishing shot of classroom", "dialogue_text": "Khung cảnh lớp học buổi sáng yên ả."}]
        v1 = self.agent._validate_panels(p1, character_dna_map=dna_map)
        self.assertNotIn("17yo schoolgirl An", v1[0]["image_prompt"], "Should NOT match 'An establishing shot'")

        # Test 2: Substring "clean"
        p2 = [{"panel_index": 1, "image_prompt": "A wide shot of clean classroom interior", "dialogue_text": "Phòng học sạch sẽ tinh tươm."}]
        v2 = self.agent._validate_panels(p2, character_dna_map=dna_map)
        self.assertNotIn("17yo schoolgirl An", v2[0]["image_prompt"], "Should NOT match substring in 'clean'")

        # Test 3: Substring "another"
        p3 = [{"panel_index": 1, "image_prompt": "Another view of the school garden", "dialogue_text": "Góc vườn trường xanh mát."}]
        v3 = self.agent._validate_panels(p3, character_dna_map=dna_map)
        self.assertNotIn("17yo schoolgirl An", v3[0]["image_prompt"], "Should NOT match substring in 'another'")

        # Test 4: Genuine match in image_prompt
        p4 = [{"panel_index": 1, "image_prompt": "An is writing notes attentively", "dialogue_text": "Chăm chú chép bài."}]
        v4 = self.agent._validate_panels(p4, character_dna_map=dna_map)
        self.assertIn("17yo schoolgirl An", v4[0]["image_prompt"], "Should match genuine character 'An'")

        # Test 5: Genuine match in dialogue_text
        p5 = [{"panel_index": 1, "image_prompt": "Medium shot by the door", "dialogue_text": "An khẽ mở cửa bước vào phòng học."}]
        v5 = self.agent._validate_panels(p5, character_dna_map=dna_map)
        self.assertIn("17yo schoolgirl An", v5[0]["image_prompt"], "Should match genuine character 'An' from dialogue")

        # Test 6: Vietnamese compound words 'bất an', 'bình an', 'an toàn', 'an tâm', 'an ninh', 'an dưỡng'
        compound_cases = [
            "Cảm giác bất an bao trùm toàn bộ hành lang vắng.",
            "Chúc các bạn một ngày mới bình an và nhiều niềm vui.",
            "Nơi này tuyệt đối an toàn cho tất cả mọi người.",
            "Hãy an tâm chuẩn bị cho kỳ thi sắp tới.",
            "Đội ngũ an ninh kiểm tra nghiêm ngặt từng lối ra vào.",
            "Khu an dưỡng nằm tách biệt nơi ngoại ô yên tĩnh."
        ]
        for c_text in compound_cases:
            p_comp = [{"panel_index": 1, "image_prompt": "A quiet empty corridor", "dialogue_text": c_text}]
            v_comp = self.agent._validate_panels(p_comp, character_dna_map=dna_map)
            self.assertNotIn("17yo schoolgirl An", v_comp[0]["image_prompt"], f"Should NOT match Vietnamese compound in: '{c_text}'")

        # Test 7: Genuine character 'An' appearing alongside compound words
        p7 = [{"panel_index": 1, "image_prompt": "Anxious moment in classroom", "dialogue_text": "Dù trong lòng rất bất an, An vẫn bình thản mỉm cười."}]
        v7 = self.agent._validate_panels(p7, character_dna_map=dna_map)
        self.assertIn("17yo schoolgirl An", v7[0]["image_prompt"], "Genuine character 'An' must match even when compound word 'bất an' is in dialogue")

    # ----------------------------------------------------------------------
    # 5. Multi-Character Scene Injection (No Premature Early Break)
    # ----------------------------------------------------------------------
    def test_multi_character_injection_no_early_break(self):
        """Panels featuring two characters must inject BOTH visual DNAs without dropping either."""
        dna_map = {
            "Lý Tiêu": {
                "dna": "Lý Tiêu (high ponytail, black-gold embroidered robes, cold amber eyes)",
                "gender": "male",
                "role": "protagonist",
                "aliases": ["Lý Tiêu", "ly tieu", "lý", "tiêu"]
            },
            "Hắc Ma Quân": {
                "dna": "Hắc Ma Quân (flowing crimson cape, demonic armor, sinister grin)",
                "gender": "male",
                "role": "antagonist",
                "aliases": ["Hắc Ma Quân", "hac ma quan", "ma quân"]
            }
        }
        panels = [
            {
                "panel_index": 1,
                "image_prompt": "Lý Tiêu faces Hắc Ma Quân in dramatic showdown",
                "dialogue_text": "Lý Tiêu: 'Hắc Ma Quân, nợ máu hôm nay phải trả!'",
                "layout_type": "wide"
            }
        ]
        validated = self.agent._validate_panels(panels, character_dna_map=dna_map)
        self.assertEqual(len(validated), 1)
        prompt_out = validated[0]["image_prompt"]
        
        # Verify BOTH character DNAs are present
        self.assertIn("high ponytail, black-gold embroidered robes", prompt_out, "Lý Tiêu DNA must be present")
        self.assertIn("flowing crimson cape, demonic armor", prompt_out, "Hắc Ma Quân DNA must be present")

    def test_multi_character_pronoun_dialogue(self):
        """Scene where dialogue mentions both 'cô bé' and 'anh bạn cùng bàn' injects both DNAs."""
        dna_map = {
            "An": {
                "dna": "An (female student, blunt bangs, blue ribbon tie)",
                "gender": "female",
                "role": "lead",
                "aliases": ["An", "cô bé", "nữ sinh"]
            },
            "Minh": {
                "dna": "Minh (male student, messy dark hair, white shirt)",
                "gender": "male",
                "role": "desk mate",
                "aliases": ["Minh", "anh bạn cùng bàn", "cậu bạn"]
            }
        }
        panels = [
            {
                "panel_index": 1,
                "image_prompt": "Two students sitting in the classroom during afternoon sunlight",
                "dialogue_text": "Cô bé nhìn anh bạn cùng bàn mỉm cười rạng rỡ.",
                "layout_type": "wide"
            }
        ]
        validated = self.agent._validate_panels(panels, character_dna_map=dna_map)
        self.assertEqual(len(validated), 1)
        prompt_out = validated[0]["image_prompt"]
        
        self.assertIn("An (female student, blunt bangs, blue ribbon tie)", prompt_out)
        self.assertIn("Minh (male student, messy dark hair, white shirt)", prompt_out)

    # ----------------------------------------------------------------------
    # 6. Gender and Role Aware Fallback
    # ----------------------------------------------------------------------
    def test_gender_aware_fallback(self):
        """When no alias matches explicitly, human indicators resolve by gender cues."""
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
        
        # Prompt depicting a girl
        p_female = [{"panel_index": 1, "image_prompt": "A schoolgirl walking under the rain alone", "dialogue_text": ""}]
        v_female = self.agent._validate_panels(p_female, character_dna_map=dna_map)
        self.assertIn("An (17yo girl, blunt bob, ribbon tie)", v_female[0]["image_prompt"])
        self.assertNotIn("Minh (17yo boy", v_female[0]["image_prompt"])

        # Prompt depicting a boy
        p_male = [{"panel_index": 1, "image_prompt": "A schoolboy sitting quietly reading in the library", "dialogue_text": ""}]
        v_male = self.agent._validate_panels(p_male, character_dna_map=dna_map)
        self.assertIn("Minh (17yo boy", v_male[0]["image_prompt"])
        self.assertNotIn("An (17yo girl", v_male[0]["image_prompt"])

    # ----------------------------------------------------------------------
    # 7. Deterministic Seed Calculation
    # ----------------------------------------------------------------------
    def test_deterministic_comic_seed_formula_and_range(self):
        """Verify formula (story_id * 7919 + 4289000) % 900000 + 100000 and 6-digit range."""
        # story_id = 1
        expected_seed_1 = (1 * 7919 + 4289000) % 900000 + 100000
        self.assertEqual(get_deterministic_comic_seed(1), expected_seed_1)
        self.assertEqual(expected_seed_1, 796919)

        # story_id = 2
        expected_seed_2 = (2 * 7919 + 4289000) % 900000 + 100000
        self.assertEqual(get_deterministic_comic_seed(2), expected_seed_2)
        self.assertEqual(expected_seed_2, 804838)

        # Invariance across 100 calls
        for _ in range(100):
            self.assertEqual(get_deterministic_comic_seed(42), (42 * 7919 + 4289000) % 900000 + 100000)

        # Range bounds [100000, 999999] for various IDs
        for sid in [0, 1, 5, 10, 99, 1000, 42890, 999999]:
            s = get_deterministic_comic_seed(sid)
            self.assertTrue(100000 <= s <= 999999, f"Seed {s} for story_id {sid} is outside [100000, 999999]")

    def test_get_cached_or_generate_image_uses_story_id(self):
        """Verify get_cached_or_generate_image respects story_id to compute deterministic seed."""
        story_id = 7
        story_seed = get_deterministic_comic_seed(story_id)
        panel_id = 12345
        expected_seed = 100000 + ((story_seed - 100000 + panel_id * 7919) % 900000)
        
        with patch("services.cloudflare_ai.generate_image_cf", return_value=b"\xff\xd8fakejpgdata") as mock_cf, \
             patch("services.cloudflare_ai._is_valid_image_payload", return_value=True), \
             patch("os.path.isfile", return_value=False), \
             patch("builtins.open", MagicMock()):
            
            get_cached_or_generate_image(panel_id=panel_id, prompt="Test prompt", seed=None, story_id=story_id)
            mock_cf.assert_called_once()
            _, kwargs = mock_cf.call_args
            self.assertEqual(kwargs.get("seed"), expected_seed)

    def test_panel_seeds_differ_within_the_same_story(self):
        story_seed = get_deterministic_comic_seed(7)
        seeds = {
            100000 + ((story_seed - 100000 + panel_id * 7919) % 900000)
            for panel_id in range(1, 8)
        }
        self.assertEqual(len(seeds), 7)

    def test_image_generation_failure_is_not_silently_accepted(self):
        with patch("services.cloudflare_ai.generate_image_cf", side_effect=RuntimeError("model unavailable")), \
             patch("services.cloudflare_ai.requests.get", return_value=MagicMock(status_code=503, content=b"")), \
             patch("os.path.isfile", return_value=False):
            with self.assertRaisesRegex(RuntimeError, "all image providers failed"):
                get_cached_or_generate_image(panel_id=9876, prompt="A character in a room", story_id=7)

    def test_force_refresh_bypasses_and_clears_cached_panel(self):
        """Explicit retries discard cached bytes and ask the image provider for a fresh render."""
        panel_id = 654321
        with patch("services.cloudflare_ai.os.remove") as remove, \
             patch("services.cloudflare_ai.os.path.isfile") as isfile, \
             patch("services.cloudflare_ai.generate_image_cf", return_value=b"\xff\xd8fresh-image") as mock_cf, \
             patch("services.cloudflare_ai._is_valid_image_payload", return_value=True), \
             patch("services.cloudflare_ai.process_manga_monochrome", side_effect=lambda image: image), \
             patch("builtins.open", MagicMock()):
            image, media_type = get_cached_or_generate_image(
                panel_id=panel_id,
                prompt="Canonical character in the story setting",
                story_id=7,
                force_refresh=True,
            )

        remove.assert_called_once()
        self.assertTrue(remove.call_args.args[0].endswith(f"panel_{panel_id}.jpg"))
        isfile.assert_not_called()
        mock_cf.assert_called_once()
        self.assertEqual(image, b"\xff\xd8fresh-image")
        self.assertEqual(media_type, "image/jpeg")

    def test_comic_image_route_forwards_retry_as_cache_bypass(self):
        panel = SimpleNamespace(
            id=321,
            comic_id=7,
            image_prompt="An in the classroom",
            comic=SimpleNamespace(story_id=7),
        )
        story = SimpleNamespace(genre="school")
        panel_query = MagicMock()
        panel_query.filter.return_value.first.return_value = panel
        story_query = MagicMock()
        story_query.filter.return_value.first.return_value = story
        db = MagicMock()
        db.query.side_effect = [panel_query, story_query]

        with patch.object(main, "_get_story_memory", return_value=None), \
             patch.object(main, "get_deterministic_comic_seed", return_value=123456), \
             patch.object(
                 main,
                 "get_cached_or_generate_image",
                 return_value=(b"\xff\xd8fresh-image", "image/jpeg"),
             ) as generate:
            response = main.get_comic_image(panel_id=321, retry=1, db=db)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["cache-control"], "no-store")
        self.assertTrue(generate.call_args.kwargs["force_refresh"])

    def test_comic_image_route_returns_actionable_uncached_failure(self):
        panel = SimpleNamespace(
            id=322,
            comic_id=7,
            image_prompt="An in the classroom",
            comic=SimpleNamespace(story_id=7),
        )
        story = SimpleNamespace(genre="school")
        panel_query = MagicMock()
        panel_query.filter.return_value.first.return_value = panel
        story_query = MagicMock()
        story_query.filter.return_value.first.return_value = story
        db = MagicMock()
        db.query.side_effect = [panel_query, story_query]

        with patch.object(main, "_get_story_memory", return_value=None), \
             patch.object(main, "get_deterministic_comic_seed", return_value=123456), \
             patch.object(
                 main,
                 "get_cached_or_generate_image",
                 side_effect=RuntimeError("provider detail should not leak"),
             ) as generate:
            response = main.get_comic_image(panel_id=322, retry=1, db=db)

        generate.assert_called_once()
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.headers["cache-control"], "no-store")
        self.assertIn(b"Retry to request a fresh render", response.body)
        self.assertNotIn(b"provider detail", response.body)


if __name__ == "__main__":
    unittest.main(verbosity=2)
