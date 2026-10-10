import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add backend directory to sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from services.comfyui_service import ComfyUIService, generate_image_comfyui
from services.cloudflare_ai import get_cached_or_generate_image, CACHE_DIR


class TestComfyUIService(unittest.TestCase):
    """Unit test suite for ComfyUI manga panel generation service."""

    def setUp(self):
        self.service = ComfyUIService(
            base_url="http://127.0.0.1:8188",
            enabled=True,
            timeout=10,
            checkpoint="animagineXLV31_v31.safetensors"
        )

    def test_initialization(self):
        self.assertEqual(self.service.base_url, "http://127.0.0.1:8188")
        self.assertTrue(self.service.is_enabled())
        self.assertEqual(self.service.custom_checkpoint, "animagineXLV31_v31.safetensors")

    @patch("requests.get")
    def test_is_available_true(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_get.return_value = mock_resp
        self.assertTrue(self.service.is_available())
        mock_get.assert_called_once_with("http://127.0.0.1:8188/system_stats", timeout=0.5)

    @patch("requests.get")
    def test_is_available_false_on_connection_error(self, mock_get):
        mock_get.side_effect = Exception("Connection refused")
        self.assertFalse(self.service.is_available())

    def test_is_available_false_when_disabled(self):
        disabled_service = ComfyUIService(enabled=False)
        self.assertFalse(disabled_service.is_available())

    @patch("requests.get")
    def test_get_available_checkpoints(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "CheckpointLoaderSimple": {
                "input": {
                    "required": {
                        "ckpt_name": [
                            ["sd_xl_base_1.0.safetensors", "animagine_manga.safetensors", "v1-5-pruned.safetensors"]
                        ]
                    }
                }
            }
        }
        mock_get.return_value = mock_resp

        models = self.service.get_available_checkpoints()
        self.assertIn("animagine_manga.safetensors", models)
        self.assertEqual(len(models), 3)

    @patch("requests.get")
    def test_resolve_checkpoint_priority(self, mock_get):
        auto_service = ComfyUIService(checkpoint=None)
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "CheckpointLoaderSimple": {
                "input": {
                    "required": {
                        "ckpt_name": [
                            ["standard_v1.safetensors", "japanese_manga_sdxl.safetensors", "general_photo.safetensors"]
                        ]
                    }
                }
            }
        }
        mock_get.return_value = mock_resp

        resolved = auto_service.resolve_checkpoint()
        self.assertEqual(resolved, "japanese_manga_sdxl.safetensors")

    def test_build_manga_workflow_nodes(self):
        workflow = self.service.build_manga_workflow(
            prompt="black and white manga drawing of a schoolgirl",
            negative_prompt="color, 3d, realistic",
            seed=428900,
            width=896,
            height=512,
            checkpoint="test_model.safetensors",
            steps=25,
            cfg=6.5
        )
        self.assertIn("3", workflow) # KSampler
        self.assertIn("4", workflow) # CheckpointLoaderSimple
        self.assertIn("5", workflow) # EmptyLatentImage
        self.assertIn("6", workflow) # Positive CLIP
        self.assertIn("7", workflow) # Negative CLIP
        self.assertIn("8", workflow) # VAEDecode
        self.assertIn("9", workflow) # SaveImage

        self.assertEqual(workflow["5"]["inputs"]["width"], 896)
        self.assertEqual(workflow["5"]["inputs"]["height"], 512)
        self.assertEqual(workflow["3"]["inputs"]["seed"], 428900)
        self.assertEqual(workflow["3"]["inputs"]["steps"], 25)
        self.assertEqual(workflow["3"]["inputs"]["cfg"], 6.5)
        self.assertEqual(workflow["4"]["inputs"]["ckpt_name"], "test_model.safetensors")
        self.assertEqual(workflow["6"]["inputs"]["text"], "black and white manga drawing of a schoolgirl")
        self.assertEqual(workflow["7"]["inputs"]["text"], "color, 3d, realistic")

    @patch("requests.post")
    def test_queue_prompt_success(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"prompt_id": "test-prompt-uuid-1234"}
        mock_post.return_value = mock_resp

        prompt_id = self.service.queue_prompt({"test": "workflow"})
        self.assertEqual(prompt_id, "test-prompt-uuid-1234")

    @patch("requests.get")
    def test_poll_for_image_output(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "test-prompt-uuid-1234": {
                "status": {"completed": True},
                "outputs": {
                    "9": {
                        "images": [
                            {"filename": "NarrAI_Manga_00001_.png", "subfolder": "", "type": "output"}
                        ]
                    }
                }
            }
        }
        mock_get.return_value = mock_resp

        filename, subfolder, ftype = self.service.poll_for_image_output("test-prompt-uuid-1234", timeout=5)
        self.assertEqual(filename, "NarrAI_Manga_00001_.png")
        self.assertEqual(ftype, "output")

    @patch("requests.get")
    def test_fetch_image_bytes(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.content = b"\x89PNG\r\n\x1a\n" + b"\x00" * 600
        mock_get.return_value = mock_resp

        img_bytes = self.service.fetch_image_bytes("NarrAI_Manga_00001_.png")
        self.assertTrue(img_bytes.startswith(b"\x89PNG"))

    @patch.object(ComfyUIService, "fetch_image_bytes")
    @patch.object(ComfyUIService, "poll_for_image_output")
    @patch.object(ComfyUIService, "queue_prompt")
    def test_generate_manga_panel_end_to_end(self, mock_queue, mock_poll, mock_fetch):
        mock_queue.return_value = "prompt-abc"
        mock_poll.return_value = ("manga_output.png", "", "output")
        valid_png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 800
        mock_fetch.return_value = valid_png

        result = self.service.generate_manga_panel(
            prompt="manga scene with wide view",
            layout_type="wide",
            seed=999
        )
        self.assertEqual(result, valid_png)
        mock_queue.assert_called_once()
        mock_poll.assert_called_once_with("prompt-abc")
        mock_fetch.assert_called_once_with("manga_output.png", "", "output")


    @patch("requests.get")
    def test_get_available_loras(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "LoraLoader": {
                "input": {
                    "required": {
                        "lora_name": [
                            [
                                "lamInkVN Vietnam ink wash painting.safetensors",
                                "AIDVN_VietnameseHeritageHouse.safetensors",
                                "CTAI-Vietnamese house early 1980s.safetensors",
                                "Retro_Sci-fi_90_s_anime_style.safetensors"
                            ]
                        ]
                    }
                }
            }
        }
        mock_get.return_value = mock_resp

        loras = self.service.get_available_loras()
        self.assertEqual(len(loras), 4)
        self.assertIn("lamInkVN Vietnam ink wash painting.safetensors", loras)

    @patch("requests.get")
    def test_match_lora(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "LoraLoader": {
                "input": {
                    "required": {
                        "lora_name": [
                            [
                                "lamInkVN Vietnam ink wash painting.safetensors",
                                "AIDVN_VietnameseHeritageHouse.safetensors"
                            ]
                        ]
                    }
                }
            }
        }
        mock_get.return_value = mock_resp

        matched = self.service.match_lora("vietnam_ink")
        self.assertEqual(matched, "lamInkVN Vietnam ink wash painting.safetensors")

        matched_heritage = self.service.match_lora("nhà cổ")
        self.assertEqual(matched_heritage, "AIDVN_VietnameseHeritageHouse.safetensors")

    def test_build_manga_workflow_with_chained_loras(self):
        loras = [
            {"name": "lamInkVN Vietnam ink wash painting.safetensors", "strength_model": 0.9, "strength_clip": 0.8},
            {"name": "AIDVN_VietnameseHeritageHouse.safetensors", "strength_model": 1.0, "strength_clip": 1.0}
        ]
        workflow = self.service.build_manga_workflow(
            prompt="manga scene with traditional house",
            loras=loras
        )
        # Verify LoRA 1 node created at "10"
        self.assertIn("10", workflow)
        self.assertEqual(workflow["10"]["class_type"], "LoraLoader")
        self.assertEqual(workflow["10"]["inputs"]["model"], ["4", 0])
        self.assertEqual(workflow["10"]["inputs"]["clip"], ["4", 1])
        self.assertEqual(workflow["10"]["inputs"]["strength_model"], 0.9)

        # Verify LoRA 2 node created at "11" chained from "10"
        self.assertIn("11", workflow)
        self.assertEqual(workflow["11"]["class_type"], "LoraLoader")
        self.assertEqual(workflow["11"]["inputs"]["model"], ["10", 0])
        self.assertEqual(workflow["11"]["inputs"]["clip"], ["10", 1])

        # Verify KSampler receives output from last LoRA node ("11")
        self.assertEqual(workflow["3"]["inputs"]["model"], ["11", 0])
        # Verify CLIPTextEncode receives clip from last LoRA node ("11")
        self.assertEqual(workflow["6"]["inputs"]["clip"], ["11", 1])
        self.assertEqual(workflow["7"]["inputs"]["clip"], ["11", 1])


class TestComicPromptAgent(unittest.TestCase):
    """Test ComicPromptAgent prompt generation and LoRA detection."""

    def setUp(self):
        from agents.comic_prompt_agent import ComicPromptAgent
        self.agent = ComicPromptAgent()

    def test_detect_vietnamese_ink_lora(self):
        story = "Khung cảnh sông nước mênh mông, nét vẽ phong cách tranh thủy mặc cổ điển."
        loras = self.agent.detect_scene_loras(story)
        self.assertTrue(any("lamInkVN" in l["name"] for l in loras))

    def test_detect_heritage_house_lora(self):
        story = "Hai người đứng trước gian nhà cổ ba gian lợp mái ngói rêu phong, hàng cột gỗ lim uy nghiêm."
        loras = self.agent.detect_scene_loras(story)
        self.assertTrue(any("AIDVN" in l["name"] for l in loras))

    def test_detect_retro_scifi_lora(self):
        story = "Chiếc phi thuyền viễn tưởng lướt qua thành phố cyberpunk trong đêm mưa."
        loras = self.agent.detect_scene_loras(story)
        self.assertTrue(any("Retro_Sci-fi" in l["name"] for l in loras))

    def test_craft_panel_prompt_heuristic_fallback(self):
        story = "An nhìn Minh bằng ánh mắt nghi ngờ khi đứng trước ngôi nhà cổ."
        char_map = {"An": {"dna": "17yo Vietnamese schoolgirl, black hair"}, "Minh": {"dna": "17yo Vietnamese boy"}}
        result = self.agent.craft_panel_prompt(
            story_text=story,
            character_dna_map=char_map,
            setting_anchor="ancient wooden courtyard"
        )
        self.assertIn("image_prompt", result)
        self.assertIn("AIDVN", result["image_prompt"])
        self.assertIn("pure monochrome", result["image_prompt"])
        self.assertIn("recommended_loras", result)


class TestComfyUIIntegrationInPipeline(unittest.TestCase):
    """Test ComfyUI integration inside get_cached_or_generate_image."""

    def setUp(self):
        self.test_panel_id = 99991
        self.cache_file = os.path.join(CACHE_DIR, f"panel_{self.test_panel_id}.jpg")
        if os.path.isfile(self.cache_file):
            os.remove(self.cache_file)

    def tearDown(self):
        if os.path.isfile(self.cache_file):
            os.remove(self.cache_file)

    @patch("services.comfyui_service.is_comfyui_available", return_value=True)
    @patch("services.comfyui_service.is_comfyui_enabled", return_value=True)
    @patch("services.comfyui_service.generate_image_comfyui")
    def test_pipeline_uses_comfyui_when_available(self, mock_gen, mock_enabled, mock_avail):
        # Provide valid PNG bytes that Pillow can process (> 500 bytes)
        from PIL import Image
        import io
        img = Image.new("RGB", (512, 512), color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        valid_img_bytes = buf.getvalue()

        mock_gen.return_value = valid_img_bytes

        img_bytes, media_type = get_cached_or_generate_image(
            panel_id=self.test_panel_id,
            prompt="Test manga prompt via ComfyUI",
            force_refresh=True
        )
        self.assertIsNotNone(img_bytes)
        self.assertIn(media_type, ["image/jpeg", "image/png"])
        mock_gen.assert_called_once()

    @patch("services.comfyui_service.is_comfyui_available", return_value=False)
    @patch("services.cloudflare_ai.generate_image_cf")
    def test_pipeline_falls_back_when_comfyui_offline(self, mock_cf, mock_avail):
        from PIL import Image
        import io
        img = Image.new("RGB", (512, 512), color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        valid_img_bytes = buf.getvalue()

        mock_cf.return_value = valid_img_bytes

        img_bytes, media_type = get_cached_or_generate_image(
            panel_id=self.test_panel_id,
            prompt="Fallback test prompt",
            force_refresh=True
        )
        self.assertIsNotNone(img_bytes)
        mock_cf.assert_called_once()


if __name__ == "__main__":
    unittest.main()

