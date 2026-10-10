import os
import json
import re
from typing import Dict, Any, List, Optional, Tuple
from llm.groq_client import GroqClient
from agents.story_memory import StoryMemory

try:
    from services.comfyui_service import KNOWN_LORAS_CATALOG, get_comfyui_service
except ImportError:
    from backend.services.comfyui_service import KNOWN_LORAS_CATALOG, get_comfyui_service


PROMPT_DIRECTOR_SYSTEM_PROMPT = """You are a Master Manga Art Director and Lead AI Prompt Engineer for a top-tier Japanese manga studio and cultural storytelling platform.

YOUR MISSION:
Analyze the given Vietnamese story beat, character registry, setting description, and visual style tags, then craft a FLAWLESS, HIGH-DENSITY English Diffusion prompt for ComfyUI / Stable Diffusion XL manga panel generation.

MANDATORY RULES:
1. VISUAL FIDELITY & ACTION GROUNDING:
   - Describe the exact physical gesture, micro-expression (e.g., narrowed eyes in suspicion, a trembling smile), and eye line of the characters.
   - Ground characters directly into their physical environment (sitting on a wooden bench, leaning against an aged plaster wall, holding a teacup).
   - NEVER generate generic, vague prompts like "anime boy standing". Always specify clothing texture, posture, and lighting.

2. CAMERA & COMPOSITION GRAMMAR:
   - Select precise manga cinematographic framing:
     * "establishing wide shot" (for environment, world-building, grand arrival)
     * "intense close-up / extreme close-up" (for emotional shock, betrayal, realization)
     * "over-the-shoulder medium shot" (for dramatic dialogues, tension between two characters)
     * "dynamic low-angle shot" (for heroic or intimidating moments)
     * "split dramatic panel" (for parallel reactions)

3. LORA AWARENESS & TRIGGER INJECTION:
   If the scene matches any available cultural or aesthetic style LoRAs, seamlessly incorporate their exact trigger phrases into the prompt:
   - Vietnamese Ink Wash / Thủy Mặc: "lamInkVN style, traditional Vietnamese ink wash painting, monochrome ink wash, delicate brush strokes"
   - Vietnamese Ancient Heritage House: "AIDVN Vietnamese heritage house, traditional Vietnamese ancient architecture, curved tiled roof, ornate carved wooden pillars"
   - Vietnamese 1980s/1990s Retro House / Bao Cấp: "CTAI-Vietnamese house style, vintage 1980s Vietnamese architecture, aged yellow plaster walls, nostalgic Vietnamese neighborhood"
   - Retro 90s Sci-Fi Anime: "retro 90s sci-fi anime style, classic 1990s anime aesthetic, sharp cell shading, high contrast screentones"

4. MONOCHROME MANGA INK AESTHETICS:
   Always ensure prompts include: "masterpiece monochrome Japanese manga illustration, crisp clean black and white ink lineart, clean G-pen lineart, delicate screentone shading, high contrast black ink on bright white paper, no color, pure monochrome".

OUTPUT FORMAT (STRICT JSON ONLY):
{
  "image_prompt": "masterpiece monochrome Japanese manga illustration, [camera framing], [character DNA + expression + gesture], [setting + props], [LoRA triggers], clean G-pen lineart, screentone shading, high contrast black ink on white paper, no color",
  "negative_prompt_suffix": "color, 3d render, photograph, western comic, blurry, text, speech bubble",
  "layout_type": "wide" | "tall" | "square",
  "recommended_loras": [
    {
      "name": "lamInkVN Vietnam ink wash painting.safetensors",
      "strength_model": 1.0,
      "strength_clip": 1.0
    }
  ],
  "camera_shot": "medium close-up",
  "dramatic_focus": "Brief explanation of the emotional/visual core"
}
"""


class ComicPromptAgent:
    """
    Dedicated AI Agent that generates hyper-targeted, culturally authentic English prompts
    for ComfyUI manga panel generation based on story text and character/setting context.
    """

    def __init__(self, groq_client: Optional[GroqClient] = None):
        if groq_client:
            self.groq_client = groq_client
        else:
            api_key = (
                os.environ.get("GROQ_API_KEY_COMIC")
                or os.environ.get("GROQ_API_KEY_COPILOT")
                or os.environ.get("GROQ_API_KEY")
            )
            try:
                self.groq_client = GroqClient(api_key=api_key) if api_key else None
            except Exception:
                self.groq_client = None

    def detect_scene_loras(self, story_text: str, setting_text: str = "", genre: str = "") -> List[Dict[str, Any]]:
        """
        Heuristically identifies relevant LoRAs based on story content, setting, and keywords.
        """
        combined = f"{story_text} {setting_text} {genre}".lower()
        selected_loras = []

        # 1. Check Vietnamese Ink Wash
        if any(kw in combined for kw in ["thủy mặc", "thuỷ mặc", "tranh mực", "bút lông", "mực tàu", "ink wash", "lamink", "sông nước", "núi non"]):
            selected_loras.append({
                "name": "lamInkVN Vietnam ink wash painting.safetensors",
                "strength_model": 1.0,
                "strength_clip": 1.0,
                "triggers": KNOWN_LORAS_CATALOG["vietnam_ink"]["trigger_prompt"]
            })

        # 2. Check Vietnamese Heritage Architecture
        if any(kw in combined for kw in ["nhà cổ", "đình làng", "chùa", "cung đình", "thành quách", "cột gỗ", "mái ngói", "di sản", "aidvn", "gian nhà gỗ"]):
            selected_loras.append({
                "name": "AIDVN_VietnameseHeritageHouse.safetensors",
                "strength_model": 1.0,
                "strength_clip": 1.0,
                "triggers": KNOWN_LORAS_CATALOG["vietnam_heritage_house"]["trigger_prompt"]
            })

        # 3. Check Vietnamese 1980s/1990s Retro Architecture
        if any(kw in combined for kw in ["bao cấp", "thập niên 80", "thập niên 90", "ngõ nhỏ", "tường vàng", "nhà tập thể", "quán cóc", "ctai"]):
            selected_loras.append({
                "name": "CTAI-Vietnamese house early 1980s.safetensors",
                "strength_model": 1.0,
                "strength_clip": 1.0,
                "triggers": KNOWN_LORAS_CATALOG["vietnam_retro_house"]["trigger_prompt"]
            })

        # 4. Check Retro Sci-Fi / 90s Anime
        if any(kw in combined for kw in ["viễn tưởng", "sci-fi", "robot", "máy bay", "không gian", "cyberpunk", "khoa học", "retro anime", "mecha"]):
            selected_loras.append({
                "name": "Retro_Sci-fi_90_s_anime_style.safetensors",
                "strength_model": 1.0,
                "strength_clip": 1.0,
                "triggers": KNOWN_LORAS_CATALOG["retro_scifi_anime"]["trigger_prompt"]
            })

        return selected_loras

    def craft_panel_prompt(
        self,
        story_text: str,
        character_dna_map: Optional[Dict[str, Any]] = None,
        setting_anchor: Optional[str] = None,
        genre: str = "",
        narrative_mode: Optional[str] = None,
        cultural_tier: Optional[int] = None,
        available_loras: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Uses LLM to craft a comprehensive, context-aware prompt object for a story beat.
        """
        detected_loras = self.detect_scene_loras(story_text, setting_anchor or "", genre)
        
        # Build prompt context
        dna_context_str = ""
        if character_dna_map:
            dna_lines = []
            for name, data in character_dna_map.items():
                if isinstance(data, dict):
                    dna = data.get("dna", "") or data.get("description", "")
                    dna_lines.append(f"- {name}: {dna}")
                else:
                    dna_lines.append(f"- {name}: {data}")
            dna_context_str = "\n".join(dna_lines)

        user_message = f"""STORY BEAT (Vietnamese):
{story_text}

GENRE / ERA: {genre or 'Drama / Storytelling'}
NARRATIVE MODE: {narrative_mode or 'hu_cau_tu_do'}
CULTURAL TIER: {cultural_tier or 1}

SETTING ANCHOR:
{setting_anchor or 'Consistent story environment'}

CHARACTER DNA REGISTRY:
{dna_context_str or 'Infer visually consistent character traits based on story'}

DETECTED RELEVANT LORAS:
{json.dumps(detected_loras, ensure_ascii=False, indent=2)}

Please construct the structured Manga Diffusion Prompt JSON now."""

        try:
            response_text = self.groq_client.generate(
                prompt=user_message,
                system_prompt=PROMPT_DIRECTOR_SYSTEM_PROMPT,
                temperature=0.3,
                max_tokens=600
            )
            parsed = self._clean_and_parse_json(response_text)
            if parsed and isinstance(parsed, dict) and "image_prompt" in parsed:
                # Merge detected LoRAs if LLM missed them
                if not parsed.get("recommended_loras") and detected_loras:
                    parsed["recommended_loras"] = detected_loras
                return parsed
        except Exception as e:
            print(f"[ComicPromptAgent] LLM generation failed ({e}), using heuristic director fallback...")

        # Fallback Heuristic Generation
        return self._heuristic_prompt_fallback(
            story_text=story_text,
            character_dna_map=character_dna_map,
            setting_anchor=setting_anchor,
            detected_loras=detected_loras,
            genre=genre
        )

    def _heuristic_prompt_fallback(
        self,
        story_text: str,
        character_dna_map: Optional[Dict[str, Any]] = None,
        setting_anchor: Optional[str] = None,
        detected_loras: Optional[List[Dict[str, Any]]] = None,
        genre: str = ""
    ) -> Dict[str, Any]:
        """
        Rule-based deterministic prompt generation ensuring zero breakage.
        """
        loras = detected_loras or []
        lora_triggers = " ".join([l.get("triggers", "") for l in loras if l.get("triggers")])

        # Pick framing based on text length or action keywords
        if any(w in story_text.lower() for w in ["nhìn", "mắt", "khóc", "cười", "ngạc nhiên", "sợ hãi", "nói"]):
            camera_shot = "medium close-up shot"
            layout_type = "square"
        elif any(w in story_text.lower() for w in ["đứng", "bước", "đi", "toàn cảnh", "bầu trời", "ngôi nhà", "phòng"]):
            camera_shot = "wide establishing shot"
            layout_type = "wide"
        else:
            camera_shot = "dramatic medium shot"
            layout_type = "tall"

        # Character snippet
        char_snippet = ""
        if character_dna_map:
            first_char = next(iter(character_dna_map.values()), None)
            if isinstance(first_char, dict):
                char_snippet = first_char.get("dna", "")
            elif isinstance(first_char, str):
                char_snippet = first_char

        setting_snippet = setting_anchor or "atmospheric background"

        prompt_parts = [
            "masterpiece monochrome Japanese manga illustration",
            camera_shot,
            f"scene depicting: {story_text[:120].strip()}",
        ]
        if char_snippet:
            prompt_parts.append(char_snippet)
        if setting_snippet:
            prompt_parts.append(f"setting: {setting_snippet}")
        if lora_triggers:
            prompt_parts.append(lora_triggers)

        prompt_parts.append(
            "crisp clean black and white ink lineart, clean G-pen lineart, "
            "delicate screentone shading, high contrast black ink on bright white paper, no color, pure monochrome"
        )

        full_prompt = ", ".join([p.strip(" ,.") for p in prompt_parts if p.strip()])

        return {
            "image_prompt": full_prompt,
            "negative_prompt_suffix": "color, 3d render, photograph, western comic, blurry, text, speech bubble",
            "layout_type": layout_type,
            "recommended_loras": loras,
            "camera_shot": camera_shot,
            "dramatic_focus": "Heuristic scene composition"
        }

    def _clean_and_parse_json(self, text: str) -> Optional[Dict[str, Any]]:
        """Cleans markdown JSON blocks and parses dictionary."""
        if not text:
            return None
        cleaned = re.sub(r"^```json\s*", "", text.strip(), flags=re.MULTILINE)
        cleaned = re.sub(r"^```\s*", "", cleaned, flags=re.MULTILINE)
        cleaned = cleaned.strip()

        # Extract first JSON object
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            cleaned = match.group(0)

        try:
            return json.loads(cleaned)
        except Exception:
            return None
