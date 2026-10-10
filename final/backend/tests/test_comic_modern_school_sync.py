import os
import sys
import re
import unittest
from unittest.mock import patch, MagicMock

# Ensure backend directory is in sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

os.environ.setdefault("GROQ_API_KEY", "gsk_test_dummy_key_for_unit_tests")
os.environ.setdefault("GROQ_API_KEY_COMIC", "gsk_test_dummy_key_for_unit_tests")

from agents.comic_agent import (
    ComicDirectorAgent,
    STYLE_PREFIX,
    STYLE_SUFFIX,
    DNA_EXTRACTOR_PROMPT,
    SPATIAL_ENCLOSURES,
    resolve_spatial_enclosure,
    sanitize_spatial_prompt,
    ACTION_GESTURE_MAPPINGS,
    extract_action_from_prose,
)
from services.cloudflare_ai import (
    BASE_NEGATIVE_PROMPT,
    MODERN_SCHOOL_EXCLUSIONS,
    get_master_negative_prompt,
    get_deterministic_comic_seed,
    generate_image_cf,
    get_cached_or_generate_image,
)


class TestComicModernSchoolSync(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with patch("llm.groq_client.Groq"):
            cls.agent = ComicDirectorAgent()

    # =========================================================================
    # 1. STYLE LOCKING & DNA PROMPT WUXIA PURGE
    # =========================================================================
    def test_style_prefix_and_suffix_modern_school_manga(self):
        """Verify STYLE_PREFIX and STYLE_SUFFIX enforce monochrome school manga art."""
        prefix_lower = STYLE_PREFIX.lower()
        suffix_lower = STYLE_SUFFIX.lower()

        self.assertIn("monochrome japanese manga illustration", prefix_lower)
        self.assertIn("professional manga comic art", prefix_lower)
        self.assertIn("crisp clean black and white ink lineart", prefix_lower)

        self.assertIn("clean g-pen lineart", suffix_lower)
        self.assertIn("screentone shading", suffix_lower)
        self.assertIn("pure monochrome", suffix_lower)
        self.assertIn("no color", suffix_lower)

    def test_dna_extractor_prompt_lacks_wuxia_priming(self):
        """Verify all ancient/wuxia tokens are purged from DNA_EXTRACTOR_PROMPT."""
        prompt_lower = DNA_EXTRACTOR_PROMPT.lower()

        # Ancient / Wuxia tokens that must NOT exist
        forbidden_wuxia = [
            "huyền bào",
            "dragon hem",
            "jade pendant on red cord",
            "crimson red mantle",
            "mandarin collar",
            "sash belt",
            "martial arts robes",
        ]
        for token in forbidden_wuxia:
            self.assertNotIn(token, prompt_lower, f"Forbidden wuxia token '{token}' found in DNA_EXTRACTOR_PROMPT")

        # Modern school uniform tokens that MUST exist
        self.assertIn("crisp button-up", prompt_lower)
        self.assertIn("blazer", prompt_lower)
        self.assertIn("pleated skirt", prompt_lower)
        self.assertIn("tailored trousers", prompt_lower)
        self.assertIn("ribbon tie", prompt_lower)
        self.assertIn("badge", prompt_lower)
        self.assertIn("30 words", prompt_lower)

    def test_dna_extractor_prompt_structure_integrity(self):
        """Ensure backward compatibility with test_comic_dna_seed assertions."""
        prompt_lower = DNA_EXTRACTOR_PROMPT.lower()
        self.assertIn("costume", prompt_lower)
        self.assertIn("garment type", prompt_lower)
        self.assertIn("fabric", prompt_lower)
        self.assertIn("collar", prompt_lower)
        self.assertTrue("ribbon tie" in prompt_lower or "bow tie" in prompt_lower)
        self.assertTrue("pendant" in prompt_lower or "brooch" in prompt_lower or "collar pin" in prompt_lower)
        self.assertIn("hairstyle", prompt_lower)
        self.assertIn("bangs", prompt_lower)
        self.assertIn("parting", prompt_lower)
        self.assertIn("facial", prompt_lower)
        self.assertIn("eye shape", prompt_lower)
        self.assertIn("jawline", prompt_lower)
        self.assertIn("gender", prompt_lower)
        self.assertIn("role", prompt_lower)
        self.assertIn("aliases", prompt_lower)
        self.assertIn("dna", prompt_lower)

    # =========================================================================
    # 2. ACTION & GESTURE SEMANTIC MAPPING
    # =========================================================================
    def test_action_writing_attentively(self):
        """Test 'An cặm cụi ghi chép bài' maps to sitting at desk, writing attentively."""
        action, shot = extract_action_from_prose("An cặm cụi ghi chép bài")
        self.assertIsNotNone(action)
        action_lower = action.lower()
        self.assertIn("sitting at wooden student desk", action_lower)
        self.assertIn("writing attentively", action_lower)

    def test_action_looking_out_window(self):
        """Test 'nhìn ra cửa sổ' maps to sitting beside window gazing out."""
        action, shot = extract_action_from_prose("Cô bé chống cằm nhìn ra cửa sổ lớp học")
        self.assertIsNotNone(action)
        action_lower = action.lower()
        self.assertIn("sitting beside the large classroom window", action_lower)
        self.assertIn("gazing pensively", action_lower)

    def test_action_turning_to_deskmate(self):
        """Test 'quay sang nói chuyện' maps to turning slightly toward desk mate."""
        action, shot = extract_action_from_prose("An quay sang nói chuyện với bạn cùng bàn")
        self.assertIsNotNone(action)
        action_lower = action.lower()
        self.assertIn("turning slightly in chair toward desk mate", action_lower)

    def test_action_standing_up_abruptly(self):
        """Test 'đứng bật dậy' maps to standing up abruptly from desk."""
        action, shot = extract_action_from_prose("Cậu ấy bàng hoàng đứng bật dậy làm đổ cả ghế")
        self.assertIsNotNone(action)
        action_lower = action.lower()
        self.assertIn("standing up abruptly from desk", action_lower)

    def test_action_head_down_melancholic(self):
        """Test 'gục đầu xuống bàn' maps to resting head on folded arms upon desk."""
        action, shot = extract_action_from_prose("Sau giờ học, cô bé mệt mỏi gục đầu xuống bàn")
        self.assertIsNotNone(action)
        action_lower = action.lower()
        self.assertIn("resting head down on folded arms upon wooden desk", action_lower)

    def test_action_looking_at_blackboard(self):
        """Test 'nhìn lên bảng đen' maps to looking forward toward blackboard."""
        action, shot = extract_action_from_prose("Cả lớp chăm chú nhìn lên bảng đen")
        self.assertIsNotNone(action)
        action_lower = action.lower()
        self.assertIn("looking forward toward the classroom blackboard", action_lower)

    # =========================================================================
    # 3. SPATIAL QUARANTINE FILTER
    # =========================================================================
    def test_spatial_quarantine_filter_strips_street_and_cars(self):
        """Test 'sitting at desk near busy street and moving cars' strips street and cars."""
        raw_prompt = "sitting at desk near busy street and moving cars"
        enclosure = SPATIAL_ENCLOSURES["classroom"]
        sanitized = sanitize_spatial_prompt(raw_prompt, enclosure)

        self.assertNotIn("street", sanitized.lower())
        self.assertNotIn("car", sanitized.lower())
        self.assertNotIn("cars", sanitized.lower())
        self.assertIn("sitting at desk", sanitized)

    def test_spatial_quarantine_preserves_subwords(self):
        """Test filter strictly preserves subwords like 'classroom', 'cardigan', and 'scarf'."""
        raw_prompt = "A student sitting in classroom wearing a cozy knit cardigan and warm scarf near busy street"
        enclosure = SPATIAL_ENCLOSURES["classroom"]
        sanitized = sanitize_spatial_prompt(raw_prompt, enclosure)

        # 'street' must be stripped
        self.assertNotIn("street", sanitized.lower())
        # Subwords must be preserved intact
        self.assertIn("classroom", sanitized.lower())
        self.assertIn("cardigan", sanitized.lower())
        self.assertIn("scarf", sanitized.lower())

    def test_spatial_quarantine_strips_ancient_and_outdoor_elements(self):
        """Test filter strips palaces, castles, temples, highways, and battlefields."""
        raw_prompt = "student standing in front of ancient palace and stone castle along the highway"
        enclosure = SPATIAL_ENCLOSURES["classroom"]
        sanitized = sanitize_spatial_prompt(raw_prompt, enclosure)

        self.assertNotIn("palace", sanitized.lower())
        self.assertNotIn("castle", sanitized.lower())
        self.assertNotIn("highway", sanitized.lower())

    def test_resolve_spatial_enclosure_selection(self):
        """Test resolve_spatial_enclosure selects appropriate enclosure."""
        # Classroom keyword
        enc1 = resolve_spatial_enclosure("Trong lớp học 12A buổi sáng", {})
        self.assertIn("classroom", enc1["anchor_description"].lower())

        # Hallway keyword
        enc2 = resolve_spatial_enclosure("Hai người đi dọc hành lang vắng", {})
        self.assertIn("hallway", enc2["anchor_description"].lower())

        # Rooftop keyword
        enc3 = resolve_spatial_enclosure("Họ hẹn nhau trên sân thượng lộng gió", {})
        self.assertIn("rooftop", enc3["anchor_description"].lower())

        # Fallback to classroom
        enc4 = resolve_spatial_enclosure("Một buổi sáng yên tĩnh", {})
        self.assertIn("classroom", enc4["anchor_description"].lower())

    # =========================================================================
    # 4. 100% PANEL SPATIAL ENCLOSURE ANCHOR ATTACHMENT
    # =========================================================================
    def test_100_percent_panel_anchor_attachment_across_layouts(self):
        """Test setting_anchor is attached to 100% of panels across square, tall, and wide layouts."""
        setting_dna = {
            "location_name": "Lớp học 12A",
            "setting_anchor": "sunny high-school classroom with wooden desks and large glass windows"
        }
        dna_map = {
            "An": {
                "gender": "female",
                "role": "lead",
                "aliases": ["An", "cô bé"],
                "dna": "17yo Vietnamese schoolgirl, blunt bangs, navy ribbon tie"
            }
        }

        panels = [
            {
                "panel_index": 1,
                "image_prompt": "wide establishing shot of classroom interior",
                "dialogue_text": "Tiết học bắt đầu.",
                "layout_type": "wide"
            },
            {
                "panel_index": 2,
                "image_prompt": "close-up of An talking with background blurred",
                "dialogue_text": "An: \"Cậu đã làm xong bài tập chưa?\"",
                "layout_type": "square"
            },
            {
                "panel_index": 3,
                "image_prompt": "dramatic tall panel of An standing up, dark background shadow",
                "dialogue_text": "An đứng bật dậy.",
                "layout_type": "tall"
            },
            {
                "panel_index": 4,
                "image_prompt": "medium shot with background showing wooden lockers",
                "dialogue_text": "Cả lớp tiếp tục làm bài.",
                "layout_type": "square"
            }
        ]

        validated = self.agent._validate_panels(panels, character_dna_map=dna_map, setting_dna=setting_dna)
        self.assertEqual(len(validated), 4)

        expected_anchor = "setting: sunny high-school classroom with wooden desks and large glass windows"
        for idx, p in enumerate(validated):
            prompt = p["image_prompt"]
            self.assertIn(
                expected_anchor,
                prompt,
                f"Panel {idx + 1} (layout={p['layout_type']}) must have setting anchor attached. Got: {prompt}"
            )

    def test_panel_specific_location_overrides_primary_setting(self):
        setting_dna = {
            "location_name": "Lớp học 12A",
            "setting_anchor": "sunny high-school classroom with wooden desks and large glass windows"
        }
        panels = self.agent._validate_panels(
            [{
                "panel_index": 1,
                "image_prompt": "close-up of An standing on the school rooftop",
                "dialogue_text": "An nhìn về phía thành phố trên sân thượng.",
                "layout_type": "square"
            }],
            setting_dna=setting_dna
        )

        prompt = panels[0]["image_prompt"].lower()
        self.assertIn("school rooftop", prompt)
        self.assertNotIn("sunny high-school classroom", prompt)

    def test_action_integration_into_panel_prompt(self):
        """Test prose action is cleanly integrated into panel image_prompt."""
        panels = [
            {
                "panel_index": 1,
                "image_prompt": "medium shot at desk",
                "dialogue_text": "An cặm cụi ghi chép bài vào cuốn tập nhỏ.",
                "layout_type": "square"
            }
        ]
        validated = self.agent._validate_panels(panels)
        self.assertEqual(len(validated), 1)
        prompt = validated[0]["image_prompt"]

        self.assertIn("sitting at wooden student desk", prompt)
        self.assertIn("writing attentively", prompt)

    def test_fallback_uses_extracted_actions(self):
        """Test _create_structured_beat_fallback extracts actions from beats."""
        story = (
            "An cặm cụi ghi chép bài.\n"
            "Bất chợt cô bé nhìn ra cửa sổ.\n"
            "Rồi cô bé quay sang nói chuyện với bạn cùng bàn."
        )
        panels = self.agent._create_structured_beat_fallback(story, {})
        self.assertGreaterEqual(len(panels), 3)

        prompts = [p["image_prompt"] for p in panels]
        combined = " ".join(prompts)
        self.assertIn("writing attentively", combined)
        self.assertIn("gazing pensively", combined)
        self.assertIn("turning slightly in chair toward desk mate", combined)

    # =========================================================================
    # 5. CLOUDFLARE AI MASTER NEGATIVE PROMPT & EXCLUSIONS
    # =========================================================================
    def test_cloudflare_master_negative_prompt_contains_modern_school_exclusions(self):
        """Verify get_master_negative_prompt combines BASE_NEGATIVE_PROMPT and MODERN_SCHOOL_EXCLUSIONS."""
        master_neg = get_master_negative_prompt("school").lower()

        # Base exclusions
        self.assertIn("color", master_neg)
        self.assertIn("photorealistic", master_neg)
        self.assertIn("western comic", master_neg)
        self.assertIn("speech bubble", master_neg)
        self.assertIn("watermark", master_neg)

        # School genre exclusions
        self.assertIn("historical clothing", master_neg)
        self.assertIn("ancient robes", master_neg)
        self.assertIn("hanfu", master_neg)
        self.assertIn("kimono", master_neg)
        self.assertIn("armor", master_neg)
        self.assertIn("sword", master_neg)
        self.assertIn("palace", master_neg)
        self.assertIn("castle", master_neg)
        self.assertIn("busy highway", master_neg)
        self.assertIn("moving cars", master_neg)

    def test_generic_default_does_not_ban_story_settings(self):
        default_negative_prompt = get_master_negative_prompt().lower()
        self.assertNotIn("palace", default_negative_prompt)
        self.assertNotIn("sword", default_negative_prompt)
        self.assertNotIn("historical clothing", default_negative_prompt)

    def test_generate_image_cf_applies_master_negative_prompt_and_suffix(self):
        """Verify generate_image_cf sends master negative prompt with custom suffix."""
        with patch("services.cloudflare_ai.get_cloudflare_token", return_value="fake_token"), \
             patch("services.cloudflare_ai.get_account_id", return_value="fake_account"), \
             patch("requests.post") as mock_post:

            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.content = b"\xff\xd8" + (b"fake_valid_image_bytes" * 50)
            mock_post.return_value = mock_resp

            with patch("services.cloudflare_ai._is_valid_image_payload", return_value=True):
                generate_image_cf(
                    prompt="test manga prompt",
                    seed=796919,
                    negative_prompt_suffix="extra_custom_exclusion_token",
                    genre="school"
                )

            mock_post.assert_called_once()
            _, kwargs = mock_post.call_args
            payload = kwargs.get("json", {})
            neg_sent = payload.get("negative_prompt", "")

            self.assertIn("extra_custom_exclusion_token", neg_sent)
            self.assertIn("historical clothing", neg_sent)
            self.assertIn("speech bubble", neg_sent)
            self.assertEqual(payload.get("seed"), 796919)


if __name__ == "__main__":
    unittest.main(verbosity=2)
