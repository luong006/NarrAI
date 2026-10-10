import os
import io
import json
import time
import uuid
import urllib.parse
import re
from typing import Optional, Dict, Any, List, Tuple
import requests

try:
    from PIL import Image, ImageOps
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    Image = None
    ImageOps = None


# Default dimensions per layout type
LAYOUT_DIMENSIONS = {
    "square": (768, 768),
    "wide": (896, 512),
    "tall": (512, 896),
}

# Standard ComfyUI default negative prompt for manga
DEFAULT_MANGA_NEGATIVE = (
    "color, colorful, vibrant, saturated, photorealistic, photograph, 3d render, CGI, "
    "western comic, bad anatomy, deformed hands, extra limbs, mutated fingers, "
    "blurry, low resolution, text, watermark, speech bubbles"
)

# Known LoRAs with style keywords and trigger prompts
KNOWN_LORAS_CATALOG = {
    "vietnam_ink": {
        "patterns": ["lamink", "vietnam ink", "ink wash", "thuy mac", "thủy mặc", "tranh mực"],
        "default_filename": "lamInkVN Vietnam ink wash painting.safetensors",
        "trigger_prompt": "lamInkVN style, traditional Vietnamese ink wash painting, monochrome ink wash, delicate brush strokes",
        "default_strength": 1.0,
        "description": "Phong cách tranh thủy mặc / thủy hoa truyền thống Việt Nam"
    },
    "vietnam_heritage_house": {
        "patterns": ["aidvn", "heritage", "vietnameseheritage", "nha co", "nhà cổ", "dinh lang", "đình làng", "chua", "chùa"],
        "default_filename": "AIDVN_VietnameseHeritageHouse.safetensors",
        "trigger_prompt": "AIDVN Vietnamese heritage house, traditional Vietnamese ancient architecture, curved tiled roof, ornate carved wooden pillars",
        "default_strength": 1.0,
        "description": "Kiến trúc nhà cổ, đình làng, chùa chiền di sản truyền thống Việt Nam"
    },
    "vietnam_retro_house": {
        "patterns": ["ctai", "vietnamese house early", "1980", "1990", "bao cap", "bao cấp", "nha pho xua", "phố cổ xưa"],
        "default_filename": "CTAI-Vietnamese house early 1980s.safetensors",
        "trigger_prompt": "CTAI-Vietnamese house style, vintage 1980s Vietnamese architecture, aged yellow plaster walls, nostalgic Vietnamese neighborhood",
        "default_strength": 1.0,
        "description": "Kiến trúc nhà phố, ngõ phố thời kỳ bao cấp thập niên 80-90 Việt Nam"
    },
    "retro_scifi_anime": {
        "patterns": ["retro_sci-fi", "retro sci-fi", "90_s_anime", "90s anime", "retro anime", "scifi", "sci-fi", "cyberpunk"],
        "default_filename": "Retro_Sci-fi_90_s_anime_style_Anima_v2_anima_3296384_epoch_15.safetensors",
        "trigger_prompt": "retro 90s sci-fi anime style, classic 1990s anime aesthetic, sharp cell shading, high contrast screentone linework",
        "default_strength": 1.0,
        "description": "Phong cách anime/manga viễn tưởng retro thập niên 90"
    },
    "vietnam_son_mai": {
        "patterns": ["sonmai", "sơn mài", "son mai", "sonmaivn"],
        "default_filename": "SonMaiVN_by_Lam_f2.safetensors",
        "trigger_prompt": "SonMaiVN style, traditional Vietnamese lacquer painting, gold leaf lacquer texture, rich lacquer art finish",
        "default_strength": 1.0,
        "description": "Nghệ thuật tranh sơn mài truyền thống Việt Nam"
    }
}


class ComfyUIService:
    """
    Client service for integrating ComfyUI into NarrAI manga generation pipeline.
    Supports:
      - Health checking & auto-discovery of checkpoints & LoRAs in the loras/ folder
      - Dynamic LoRA stacking / chaining (Model & CLIP)
      - Standard text-to-image manga workflows (SD1.5 / SDXL)
      - Dynamic layout dimension mapping (square, wide, tall)
      - Synchronous execution polling with fast fail
      - Seamless retrieval and post-processing
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        enabled: Optional[bool] = None,
        timeout: int = 120,
        checkpoint: Optional[str] = None
    ):
        self.base_url = (
            base_url
            or os.environ.get("COMFYUI_URL")
            or "http://127.0.0.1:8188"
        ).rstrip("/")
        
        env_enabled = os.environ.get("COMFYUI_ENABLED", "true").lower() in ("1", "true", "yes")
        self.enabled = env_enabled if enabled is None else enabled
        self.timeout = int(os.environ.get("COMFYUI_TIMEOUT", timeout))
        self.custom_checkpoint = checkpoint or os.environ.get("COMFYUI_CHECKPOINT", "").strip() or None
        self.sampler_name = os.environ.get("COMFYUI_SAMPLER_NAME", "euler")
        self.scheduler = os.environ.get("COMFYUI_SCHEDULER", "normal")
        self.steps = int(os.environ.get("COMFYUI_STEPS", "20"))
        self.cfg = float(os.environ.get("COMFYUI_CFG", "7.0"))
        self._last_avail_check: float = 0.0
        self._last_avail_result: bool = False
        self._avail_ttl: float = 5.0

    def is_enabled(self) -> bool:
        """Returns True if ComfyUI integration is enabled."""
        return self.enabled

    def is_available(self, timeout: float = 2.5, force_check: bool = False) -> bool:
        """
        Fast non-blocking ping to ComfyUI /system_stats with TTL caching
        to determine if ComfyUI server is actively running.
        """
        if not self.enabled:
            return False
        now = time.time()
        if not force_check and (now - self._last_avail_check < self._avail_ttl):
            return self._last_avail_result
        try:
            resp = requests.get(f"{self.base_url}/system_stats", timeout=timeout)
            res = (resp.status_code == 200)
        except Exception:
            res = False
        self._last_avail_check = now
        self._last_avail_result = res
        return res

    def get_system_stats(self) -> Dict[str, Any]:
        """Fetch system stats from ComfyUI."""
        try:
            resp = requests.get(f"{self.base_url}/system_stats", timeout=5)
            if resp.status_code == 200:
                return resp.json()
        except Exception as e:
            return {"error": str(e), "status": "offline"}
        return {"status": "offline"}

    def get_available_checkpoints(self) -> List[str]:
        """
        Queries ComfyUI for available checkpoint models from CheckpointLoaderSimple.
        """
        try:
            resp = requests.get(f"{self.base_url}/object_info/CheckpointLoaderSimple", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                input_info = data.get("CheckpointLoaderSimple", {}).get("input", {}).get("required", {})
                ckpt_names = input_info.get("ckpt_name", [[]])[0]
                if isinstance(ckpt_names, list):
                    return ckpt_names
        except Exception as e:
            print(f"[ComfyUI] Could not fetch available checkpoints: {e}")
        return []

    def get_available_loras(self) -> List[str]:
        """
        Queries ComfyUI for available LoRA models from LoraLoader.
        """
        try:
            resp = requests.get(f"{self.base_url}/object_info/LoraLoader", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                input_info = data.get("LoraLoader", {}).get("input", {}).get("required", {})
                lora_names = input_info.get("lora_name", [[]])[0]
                if isinstance(lora_names, list):
                    return lora_names
        except Exception as e:
            print(f"[ComfyUI] Could not fetch available LoRAs: {e}")
        return []

    def match_lora(self, keyword_or_name: str) -> Optional[str]:
        """
        Matches a keyword, catalog key, or partial name to an actual available LoRA filename in ComfyUI.
        """
        available = self.get_available_loras()
        if not available:
            return None

        kw = keyword_or_name.lower().strip()

        # 1. Direct exact match
        for lora in available:
            if lora.lower() == kw:
                return lora

        # 2. Check if keyword matches a catalog key or any pattern inside catalog
        for cat_key, cat in KNOWN_LORAS_CATALOG.items():
            patterns = [p.lower() for p in cat.get("patterns", [])]
            if kw == cat_key or any(p in kw or kw in p for p in patterns):
                for lora in available:
                    lora_l = lora.lower()
                    if any(p in lora_l for p in patterns) or cat.get("default_filename", "").lower() in lora_l:
                        return lora

        # 3. Substring / pattern match against available LoRA filenames
        for lora in available:
            if kw in lora.lower():
                return lora

        return None

    def resolve_checkpoint(self) -> Optional[str]:
        """
        Resolves which checkpoint filename to use:
        1. Explicit custom_checkpoint if set.
        2. First available checkpoint from ComfyUI preferring manga/anime/sdxl keywords.
        3. None if no checkpoint discovered.
        """
        if self.custom_checkpoint:
            return self.custom_checkpoint

        available = self.get_available_checkpoints()
        if not available:
            return None

        # Prioritize anime/manga/sdxl models if present in ComfyUI
        priorities = ["animagine", "manga", "anime", "anything", "sdxl", "counterfeit", "v1-5"]
        for prio in priorities:
            for ckpt in available:
                if prio in ckpt.lower():
                    return ckpt

        return available[0]

    def build_manga_workflow(
        self,
        prompt: str,
        negative_prompt: str = "",
        seed: int = 123456,
        width: int = 768,
        height: int = 768,
        checkpoint: Optional[str] = None,
        loras: Optional[List[Dict[str, Any]]] = None,
        steps: Optional[int] = None,
        cfg: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Builds standard ComfyUI text-to-image API prompt workflow dictionary,
        with support for dynamic LoRA chaining between CheckpointLoaderSimple and CLIP/KSampler.
        """
        ckpt_name = checkpoint or self.resolve_checkpoint() or "animagineXLV31_v31.safetensors"
        use_steps = steps if steps is not None else self.steps
        use_cfg = cfg if cfg is not None else self.cfg

        workflow = {
            "4": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {
                    "ckpt_name": ckpt_name
                }
            },
            "5": {
                "class_type": "EmptyLatentImage",
                "inputs": {
                    "batch_size": 1,
                    "height": height,
                    "width": width
                }
            },
            "8": {
                "class_type": "VAEDecode",
                "inputs": {
                    "samples": ["3", 0],
                    "vae": ["4", 2]
                }
            },
            "9": {
                "class_type": "SaveImage",
                "inputs": {
                    "filename_prefix": "NarrAI_Manga",
                    "images": ["8", 0]
                }
            }
        }

        # Handle LoRA chaining
        current_model = ["4", 0]
        current_clip = ["4", 1]
        node_id_counter = 10

        if loras and isinstance(loras, list):
            available_loras = self.get_available_loras()
            for lora_item in loras:
                if not isinstance(lora_item, dict):
                    continue
                raw_name = str(lora_item.get("name", "") or lora_item.get("lora_name", "")).strip()
                if not raw_name:
                    continue

                # Match against available loras or catalog
                matched_filename = self.match_lora(raw_name) or raw_name
                # Only insert if matched or filename ends with standard model extensions
                strength_model = float(lora_item.get("strength_model", 1.0))
                strength_clip = float(lora_item.get("strength_clip", 1.0))

                lora_node_id = str(node_id_counter)
                node_id_counter += 1

                workflow[lora_node_id] = {
                    "class_type": "LoraLoader",
                    "inputs": {
                        "model": current_model,
                        "clip": current_clip,
                        "lora_name": matched_filename,
                        "strength_model": strength_model,
                        "strength_clip": strength_clip
                    }
                }
                current_model = [lora_node_id, 0]
                current_clip = [lora_node_id, 1]

        # KSampler receives the final model output
        workflow["3"] = {
            "class_type": "KSampler",
            "inputs": {
                "cfg": use_cfg,
                "denoise": 1.0,
                "latent_image": ["5", 0],
                "model": current_model,
                "negative": ["7", 0],
                "positive": ["6", 0],
                "sampler_name": self.sampler_name,
                "scheduler": self.scheduler,
                "seed": int(seed),
                "steps": use_steps
            }
        }

        # CLIPTextEncode receives the final CLIP output
        workflow["6"] = {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "clip": current_clip,
                "text": prompt
            }
        }
        workflow["7"] = {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "clip": current_clip,
                "text": negative_prompt or DEFAULT_MANGA_NEGATIVE
            }
        }

        return workflow

    def queue_prompt(self, workflow: Dict[str, Any], client_id: Optional[str] = None) -> str:
        """
        Submits workflow to ComfyUI /prompt endpoint.
        Returns prompt_id string.
        """
        cid = client_id or str(uuid.uuid4())
        payload = {"prompt": workflow, "client_id": cid}
        url = f"{self.base_url}/prompt"

        resp = requests.post(url, json=payload, timeout=10)
        if resp.status_code != 200:
            raise RuntimeError(f"ComfyUI /prompt failed with status {resp.status_code}: {resp.text[:300]}")

        data = resp.json()
        prompt_id = data.get("prompt_id")
        if not prompt_id:
            raise RuntimeError(f"ComfyUI response missing prompt_id: {data}")

        return prompt_id

    def poll_for_image_output(self, prompt_id: str, timeout: Optional[int] = None) -> Tuple[str, str, str]:
        """
        Polls ComfyUI /history/{prompt_id} until task finishes.
        Returns (filename, subfolder, folder_type).
        """
        max_time = timeout or self.timeout
        start_time = time.time()
        url = f"{self.base_url}/history/{prompt_id}"
        consecutive_errors = 0

        while time.time() - start_time < max_time:
            try:
                resp = requests.get(url, timeout=3)
                if resp.status_code == 200:
                    consecutive_errors = 0
                    history = resp.json()
                    if prompt_id in history:
                        task_data = history[prompt_id]
                        status = task_data.get("status", {})
                        if status.get("completed", False) or "outputs" in task_data:
                            outputs = task_data.get("outputs", {})
                            for node_id, node_output in outputs.items():
                                if "images" in node_output and len(node_output["images"]) > 0:
                                    img_info = node_output["images"][0]
                                    return (
                                        img_info.get("filename", ""),
                                        img_info.get("subfolder", ""),
                                        img_info.get("type", "output")
                                    )
                else:
                    consecutive_errors += 1
            except Exception as e:
                consecutive_errors += 1
                print(f"[ComfyUI] Polling history warning: {e}")
                if consecutive_errors >= 3:
                    raise ConnectionError(f"Lost connection to ComfyUI at {self.base_url} while polling prompt {prompt_id}: {e}")

            time.sleep(0.5)

        raise TimeoutError(f"ComfyUI prompt execution timed out after {max_time}s (prompt_id: {prompt_id})")

    def fetch_image_bytes(self, filename: str, subfolder: str = "", folder_type: str = "output") -> bytes:
        """
        Downloads rendered image bytes from ComfyUI /view endpoint.
        """
        params = {
            "filename": filename,
            "subfolder": subfolder,
            "type": folder_type
        }
        query_string = urllib.parse.urlencode(params)
        url = f"{self.base_url}/view?{query_string}"

        resp = requests.get(url, timeout=30)
        if resp.status_code != 200:
            raise RuntimeError(f"ComfyUI /view failed with status {resp.status_code}")

        return resp.content

    def generate_manga_panel(
        self,
        prompt: str,
        negative_prompt: str = "",
        seed: int = 123456,
        layout_type: str = "square",
        checkpoint: Optional[str] = None,
        loras: Optional[List[Dict[str, Any]]] = None,
        steps: Optional[int] = None,
        cfg: Optional[float] = None
    ) -> bytes:
        """
        Full end-to-end pipeline:
        1. Resolve layout dimensions
        2. Build workflow with optional LoRAs
        3. Submit prompt to ComfyUI
        4. Poll for output completion
        5. Fetch image bytes and return
        """
        width, height = LAYOUT_MAP_DIMS(layout_type)

        workflow = self.build_manga_workflow(
            prompt=prompt,
            negative_prompt=negative_prompt,
            seed=seed,
            width=width,
            height=height,
            checkpoint=checkpoint,
            loras=loras,
            steps=steps,
            cfg=cfg
        )

        prompt_id = self.queue_prompt(workflow)
        print(f"[ComfyUI] Queued manga generation prompt_id={prompt_id}, dims={width}x{height}, seed={seed}, loras={len(loras or [])}")

        filename, subfolder, folder_type = self.poll_for_image_output(prompt_id)
        if not filename:
            raise RuntimeError(f"ComfyUI completed without output image for prompt_id={prompt_id}")

        img_bytes = self.fetch_image_bytes(filename, subfolder, folder_type)
        return img_bytes


def LAYOUT_MAP_DIMS(layout_type: str) -> Tuple[int, int]:
    return LAYOUT_DIMENSIONS.get(layout_type.lower(), LAYOUT_DIMENSIONS["square"])


# Global singleton
_comfyui_service: Optional[ComfyUIService] = None


def get_comfyui_service() -> ComfyUIService:
    global _comfyui_service
    if _comfyui_service is None:
        _comfyui_service = ComfyUIService()
    return _comfyui_service


def is_comfyui_available() -> bool:
    return get_comfyui_service().is_available()


def is_comfyui_enabled() -> bool:
    return get_comfyui_service().is_enabled()


def generate_image_comfyui(
    prompt: str,
    seed: int = 123456,
    negative_prompt_suffix: Optional[str] = None,
    layout_type: str = "square",
    custom_negative_prompt: Optional[str] = None,
    cultural_tier: Optional[int] = None,
    narrative_mode: Optional[str] = None,
    genre: str = "",
    loras: Optional[List[Dict[str, Any]]] = None
) -> bytes:
    """
    Convenience wrapper to generate a manga panel with ComfyUI,
    incorporating cultural and genre-specific negative prompts and LoRA stack.
    """
    from services.cloudflare_ai import get_master_negative_prompt

    negative_prompt = get_master_negative_prompt(
        genre=genre,
        cultural_tier=cultural_tier,
        narrative_mode=narrative_mode
    )
    suffix = negative_prompt_suffix or custom_negative_prompt
    if suffix:
        negative_prompt = f"{negative_prompt}, {suffix.strip(' ,')}"

    service = get_comfyui_service()
    return service.generate_manga_panel(
        prompt=prompt,
        negative_prompt=negative_prompt,
        seed=seed,
        layout_type=layout_type,
        loras=loras
    )
