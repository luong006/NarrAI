import os
import io
import json
import time
import uuid
import urllib.parse
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


class ComfyUIService:
    """
    Client service for integrating ComfyUI into NarrAI manga generation pipeline.
    Supports:
      - Health checking & auto-discovery of available checkpoints
      - Standard text-to-image manga workflows (SD1.5 / SDXL)
      - Dynamic layout dimension mapping (square, wide, tall)
      - Synchronous execution polling with timeout
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
        self._avail_ttl: float = 3.0

    def is_enabled(self) -> bool:
        """Returns True if ComfyUI integration is enabled."""
        return self.enabled

    def is_available(self, timeout: float = 0.5, force_check: bool = False) -> bool:
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
        priorities = ["manga", "anime", "animagine", "anything", "sdxl", "counterfeit", "v1-5"]
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
        steps: Optional[int] = None,
        cfg: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Builds standard ComfyUI text-to-image API prompt workflow dictionary.
        """
        ckpt_name = checkpoint or self.resolve_checkpoint() or "v1-5-pruned-emaonly.safetensors"
        use_steps = steps if steps is not None else self.steps
        use_cfg = cfg if cfg is not None else self.cfg

        workflow = {
            "3": {
                "class_type": "KSampler",
                "inputs": {
                    "cfg": use_cfg,
                    "denoise": 1.0,
                    "latent_image": ["5", 0],
                    "model": ["4", 0],
                    "negative": ["7", 0],
                    "positive": ["6", 0],
                    "sampler_name": self.sampler_name,
                    "scheduler": self.scheduler,
                    "seed": int(seed),
                    "steps": use_steps
                }
            },
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
            "6": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "clip": ["4", 1],
                    "text": prompt
                }
            },
            "7": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "clip": ["4", 1],
                    "text": negative_prompt or DEFAULT_MANGA_NEGATIVE
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
        steps: Optional[int] = None,
        cfg: Optional[float] = None
    ) -> bytes:
        """
        Full end-to-end pipeline:
        1. Resolve layout dimensions
        2. Build workflow
        3. Submit prompt to ComfyUI
        4. Poll for output completion
        5. Fetch image bytes and return
        """
        width, height = LAYOUT_DIMENSIONS.get(layout_type.lower(), LAYOUT_DIMENSIONS["square"])

        workflow = self.build_manga_workflow(
            prompt=prompt,
            negative_prompt=negative_prompt,
            seed=seed,
            width=width,
            height=height,
            checkpoint=checkpoint,
            steps=steps,
            cfg=cfg
        )

        prompt_id = self.queue_prompt(workflow)
        print(f"[ComfyUI] Queued manga generation prompt_id={prompt_id}, dims={width}x{height}, seed={seed}")

        filename, subfolder, folder_type = self.poll_for_image_output(prompt_id)
        if not filename:
            raise RuntimeError(f"ComfyUI completed without output image for prompt_id={prompt_id}")

        img_bytes = self.fetch_image_bytes(filename, subfolder, folder_type)
        return img_bytes


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
    genre: str = ""
) -> bytes:
    """
    Convenience wrapper to generate a manga panel with ComfyUI,
    incorporating cultural and genre-specific negative prompts.
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
        layout_type=layout_type
    )
