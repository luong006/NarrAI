import os
import json
import re
from llm.groq_client import GroqClient
from agents.story_memory import StoryMemory

# STRICT style prefix and suffix to force Diffusion model attention to B&W Manga
STYLE_PREFIX = "black and white manga, Japanese manga comic art, monochrome ink drawing on paper, "
STYLE_SUFFIX = ", manga panel, screentone shading, bold ink outlines, high contrast black ink, clean lineart, no color, hand drawn 2D illustration, no photograph, no 3D render"

LAYOUT_MAP = {
    "wide": "wide", "horizontal": "wide", "landscape": "wide", "panoramic": "wide", "establishing": "wide",
    "tall": "tall", "vertical": "tall", "portrait": "tall", "dramatic": "tall",
    "square": "square", "medium": "square", "close-up": "square", "closeup": "square", "standard": "square",
}

# ==================== CHARACTER DNA EXTRACTOR ====================
DNA_EXTRACTOR_PROMPT = """You are a character design director for a manga studio.
Analyze the story text and extract the EXACT, IMMUTABLE visual physical traits for each named character.

For each character, specify:
1. Name
2. Exact age/gender appearance
3. Hairstyle and hair color
4. Signature outfit and clothing details
5. Distinctive facial features, accessories, or build

Return ONLY a valid JSON object mapping character name to a concise English Visual DNA string (under 35 words each).
Example:
{
  "Minh": "young Vietnamese man 24yo, messy textured dark hair, wearing black denim jacket over white t-shirt, silver stud on left ear, sharp eyes, athletic build",
  "Lan": "young Vietnamese woman 22yo, shoulder-length black hair in side ponytail, wearing beige knit cardigan over floral blouse, warm gentle brown eyes"
}
"""

# ==================== SPATIAL SETTING DNA EXTRACTOR ====================
SETTING_EXTRACTOR_PROMPT = """You are an art director and world-building designer for a manga studio.
Analyze the story text and extract the PRIMARY SPATIAL SETTING & ENVIRONMENT ANCHOR to guarantee strict background consistency across all manga panels.

For the primary location, specify:
1. Location type & time of day/era (e.g. vintage 1990s detective office at night, modern high-tech glass lab, ancient stone fortress)
2. Architectural details (walls, windows, flooring, distinctive structural columns)
3. Key persistent props & furniture (e.g. mahogany desk with scattered dossiers, vintage brass lamp, antique bookshelf)
4. Atmospheric lighting & shadows (e.g. moody chiaroscuro lighting, harsh fluorescent light, rain streaks on window)

Return ONLY a valid JSON object:
{
  "location_name": "Tên địa điểm ngắn gọn",
  "setting_anchor": "English visual description under 40 words specifying architecture, persistent props, and lighting atmosphere",
  "atmosphere": "e.g. gloomy noir with heavy shadows, clean sci-fi screentones, rustic vintage ink textures"
}
"""

# ==================== BEAT-BY-BEAT MANGA DIRECTOR ====================
BEAT_DIRECTOR_PROMPT = """You are a master manga director and storyboard artist (combining the meticulous narrative pacing of Naoki Urasawa, the spatial consistency of Inio Asano, and the expressive paneling of Eiichiro Oda).

YOUR MISSION: Faithfully adapt the provided Vietnamese story text into a SEQUENTIAL, BEAT-BY-BEAT MANGA SCRIPT.

ABSOLUTE CRITICAL RULES:
1. NO SKIPPING / NO SUMMARIZING: DO NOT summarize several paragraphs into one generic panel! Adapt EVERY significant exchange, dialogue line, reaction, and physical action into sequential panels.
   - If Character A says something and Character B responds, that is AT LEAST 2 sequential panels (Speaker A -> Reaction/Reply B).
   - If an action or dramatic gesture occurs (e.g. someone stands up, looks out the window, draws a breath, opens a door), give it its own panel.
2. CHARACTER CONSISTENCY: For any panel featuring a character, you MUST embed their exact Visual DNA from the CHARACTER REGISTRY into the `image_prompt`.
3. SETTING & BACKGROUND CONSISTENCY: Every panel taking place in the primary environment MUST maintain the architecture, lighting, and persistent props from the SETTING REGISTRY so backgrounds DO NOT drift, mutate, or hallucinate between panels.
4. IMAGE PROMPT (English): Under 65 words, describing camera angle (close-up, medium shot, low angle, over-the-shoulder), character expression/action, AND the specific background elements anchored from the setting.
5. DIALOGUE & CAPTION TEXT (Vietnamese): MUST BE EXPRESSIVE, COMPLETE, AND NUANCED!
   - Capture full character dialogue lines: `[Tên nhân vật]: "[Câu thoại trọn vẹn giàu cảm xúc]"`
   - For narration or inner monologue, provide evocative, tension-filled sentences.
   - DO NOT truncate words or cut sentences off midway. Use 25 to 45 words per panel to fully convey the story beat.
6. LAYOUT TYPE: Choose dynamically:
   - "wide": for establishing rooms, wide action scenes, panoramic moments.
   - "tall": for dramatic full-body poses, towering figures, intense emotional heights.
   - "square": for dialogues, face-to-face exchanges, medium shots.

OUTPUT FORMAT:
Return ONLY a valid JSON array of panel objects:
[
  {
    "panel_index": 1,
    "image_prompt": "wide establishing shot of...",
    "dialogue_text": "...",
    "layout_type": "wide"
  }
]
"""

class ComicDirectorAgent:
    def __init__(self):
        api_key = os.environ.get("GROQ_API_KEY_COMIC") or os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise ValueError("Thiếu GROQ_API_KEY_COMIC hoặc GROQ_API_KEY")
        self.llm = GroqClient(model_name="qwen/qwen3.8-27b", api_key=api_key)

    def extract_character_dna(self, story_text: str, memory: StoryMemory = None) -> dict:
        """Extracts immutable visual character DNA to anchor diffusion models across all panels."""
        existing_dna = {}
        if memory and memory.story_bible and memory.story_bible.characters:
            for c in memory.story_bible.characters:
                if isinstance(c, dict) and c.get("name") and c.get("appearance"):
                    existing_dna[c["name"]] = c["appearance"]

        try:
            sample_text = story_text[:3500]
            resp = self.llm.chat(
                messages=[
                    {"role": "system", "content": DNA_EXTRACTOR_PROMPT},
                    {"role": "user", "content": f"Extract Visual DNA for characters in this story:\n\n{sample_text}"}
                ],
                temperature=0.2,
                max_tokens=1000
            )
            cleaned = re.sub(r'```(?:json)?\s*', '', resp).strip()
            match = re.search(r'\{.*\}', cleaned, re.DOTALL)
            if match:
                parsed = json.loads(match.group(0))
                if isinstance(parsed, dict):
                    existing_dna.update(parsed)
        except Exception as e:
            print(f"[Comic] Character DNA extraction fallback ({e})")
            if not existing_dna:
                existing_dna["Protagonist"] = "young Asian person in contemporary casual clothes, dark hair, expressive eyes"

        return existing_dna

    def extract_setting_dna(self, story_text: str, memory: StoryMemory = None) -> dict:
        """Extracts immutable spatial setting anchor to lock background consistency across panels."""
        existing_setting = {}
        if memory and memory.story_bible and memory.story_bible.world_setting:
            existing_setting["location_name"] = "Bối cảnh chính"
            existing_setting["setting_anchor"] = memory.story_bible.world_setting
            existing_setting["atmosphere"] = "atmospheric manga screentone background"

        try:
            sample_text = story_text[:3500]
            resp = self.llm.chat(
                messages=[
                    {"role": "system", "content": SETTING_EXTRACTOR_PROMPT},
                    {"role": "user", "content": f"Extract Primary Spatial Setting DNA for this story:\n\n{sample_text}"}
                ],
                temperature=0.2,
                max_tokens=800
            )
            cleaned = re.sub(r'```(?:json)?\s*', '', resp).strip()
            match = re.search(r'\{.*\}', cleaned, re.DOTALL)
            if match:
                parsed = json.loads(match.group(0))
                if isinstance(parsed, dict):
                    existing_setting.update(parsed)
        except Exception as e:
            print(f"[Comic] Setting DNA extraction fallback ({e})")
            if not existing_setting:
                existing_setting = {
                    "location_name": "Bối cảnh chung",
                    "setting_anchor": "detailed indoor room with wooden furniture and ambient window lighting",
                    "atmosphere": "dramatic high contrast manga screentone"
                }

        return existing_setting

    def _parse_json_array(self, raw_output):
        """Extract and parse a JSON array from LLM output."""
        cleaned = re.sub(r'```(?:json)?\s*', '', raw_output).strip()
        match = re.search(r'\[.*\]', cleaned, re.DOTALL)
        if match:
            cleaned = match.group(0)
        return json.loads(cleaned, strict=False)

    def _validate_panels(self, script_data, character_dna_map=None, setting_dna=None):
        """Validate, normalize layout, enforce character visual DNA, background anchor, and style tokens."""
        if not isinstance(script_data, list):
            raise ValueError("Output is not a JSON array")

        dna_map = character_dna_map or {}
        setting_anchor = ""
        if setting_dna and isinstance(setting_dna, dict):
            setting_anchor = setting_dna.get("setting_anchor", "").strip()

        validated = []
        for i, item in enumerate(script_data):
            prompt = item.get("image_prompt", "a detailed manga scene").strip()

            # Check if any character is mentioned without their DNA, and inject if missing
            char_injected = False
            for char_name, dna_str in dna_map.items():
                if char_name.lower() in prompt.lower() and dna_str.lower() not in prompt.lower():
                    prompt = f"{dna_str}, {prompt}"
                    char_injected = True

            # Blend setting anchor to preserve background consistency across panels
            if setting_anchor and setting_anchor.lower() not in prompt.lower():
                raw_layout_check = str(item.get("layout_type", "square")).lower()
                if raw_layout_check == "wide" or i == 0 or "background" not in prompt.lower():
                    prompt = f"{prompt}, setting: {setting_anchor}"

            # Clean duplicate style tags
            clean_prompt = prompt
            for tag in ["manga panel", "black and white", "monochrome", "screentone", "comic art"]:
                clean_prompt = re.sub(re.escape(tag), "", clean_prompt, flags=re.IGNORECASE)
            clean_prompt = clean_prompt.strip(" ,.-")

            final_prompt = f"{STYLE_PREFIX}{clean_prompt}{STYLE_SUFFIX}"

            raw_layout = str(item.get("layout_type", "square")).lower().strip()
            normalized_layout = LAYOUT_MAP.get(raw_layout, "square")

            dialogue = str(item.get("dialogue_text", "")).strip()
            # Allow rich dialogues and expressive sentences (up to 55 words) without truncation
            words = dialogue.split()
            if len(words) > 55:
                dialogue = " ".join(words[:50]) + "..."

            validated.append({
                "panel_index": i + 1,
                "image_prompt": final_prompt,
                "dialogue_text": dialogue,
                "layout_type": normalized_layout
            })
        return validated

    def generate_comic_script(self, story_text: str, memory: StoryMemory = None) -> list:
        """
        Adapts the story text into a beat-by-beat sequential manga storyboard.
        Produces detailed sequential panels closely tracking every dialogue and action beat.
        """
        print(f"[Comic] Generating beat-by-beat storyboard for {len(story_text)} chars...")
        character_dna = self.extract_character_dna(story_text, memory=memory)
        setting_dna = self.extract_setting_dna(story_text, memory=memory)
        dna_context = "\n".join([f"- {name}: {dna}" for name, dna in character_dna.items()])
        setting_context = f"Location: {setting_dna.get('location_name', 'Main Setting')}\nAnchor: {setting_dna.get('setting_dna', '')}\nAtmosphere: {setting_dna.get('atmosphere', '')}"

        system_instruction = f"{BEAT_DIRECTOR_PROMPT}\n\nCHARACTER VISUAL REGISTRY (IMMUTABLE):\n{dna_context}\n\nSETTING VISUAL ANCHOR (IMMUTABLE):\n{setting_context}\n"

        user_content = f"""Adapt this Vietnamese story text into sequential manga panels beat-by-beat.
DO NOT SKIP ANY DIALOGUE OR MAJOR ACTION. Ensure every character line and key reaction is depicted with expressive dialogue text.
Aim for 8 to 14 detailed panels covering the entire excerpt.

STORY TEXT:
{story_text}
"""
        try:
            response = self.llm.chat(
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.3,
                max_tokens=4000
            )
            panels_raw = self._parse_json_array(response)
            validated_panels = self._validate_panels(panels_raw, character_dna_map=character_dna, setting_dna=setting_dna)
            print(f"[Comic] Successfully created {len(validated_panels)} detailed beat-by-beat panels with background & character consistency.")
            return validated_panels
        except Exception as e:
            print(f"[Comic] Storyboard LLM failed ({e}), creating structured beat fallback...")
            return self._create_structured_beat_fallback(story_text, character_dna, setting_dna)

    def generate_continuation(self, previous_summary: str, new_text: str, memory: StoryMemory = None) -> list:
        """Continues an existing comic with new sequential panels from newly added text."""
        character_dna = self.extract_character_dna(new_text, memory=memory)
        setting_dna = self.extract_setting_dna(new_text, memory=memory)
        dna_context = "\n".join([f"- {name}: {dna}" for name, dna in character_dna.items()])
        setting_context = f"Location: {setting_dna.get('location_name', 'Main Setting')}\nAnchor: {setting_dna.get('setting_dna', '')}\nAtmosphere: {setting_dna.get('atmosphere', '')}"

        system_instruction = f"""{BEAT_DIRECTOR_PROMPT}

PREVIOUS COMIC PROGRESSION:
{previous_summary}

CHARACTER VISUAL REGISTRY (IMMUTABLE):
{dna_context}

SETTING VISUAL ANCHOR (IMMUTABLE):
{setting_context}
"""
        user_content = f"""Continue the comic from the previous progression with sequential panels adapting this new text beat-by-beat.
DO NOT SKIP DIALOGUES OR ACTIONS. Keep dialogue text expressive, complete, and rich in meaning.

NEW STORY TEXT:
{new_text}
"""
        try:
            response = self.llm.chat(
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.3,
                max_tokens=4000
            )
            panels_raw = self._parse_json_array(response)
            validated = self._validate_panels(panels_raw, character_dna_map=character_dna, setting_dna=setting_dna)
            return validated
        except Exception as e:
            print(f"[Comic] Continuation failed ({e}), creating structured fallback...")
            return self._create_structured_beat_fallback(new_text, character_dna, setting_dna)

    def _create_structured_beat_fallback(self, story_text: str, character_dna: dict, setting_dna: dict = None) -> list:
        """Parses raw text paragraphs into individual dialogue and action panels as a guaranteed fallback."""
        lines = [line.strip() for line in story_text.split("\n") if len(line.strip()) > 15]
        panels = []
        lead_dna = list(character_dna.values())[0] if character_dna else "young Asian protagonist in casual clothes"
        bg_anchor = setting_dna.get("setting_anchor", "detailed indoor room with wooden furniture") if setting_dna else "indoor room"

        for idx, line in enumerate(lines[:10]):
            is_dialogue = '"' in line or '“' in line or '-' in line[:3]
            layout = "square" if is_dialogue else ("wide" if idx == 0 else "tall")
            
            clean_line = line.replace('"', '').replace('“', '').replace('”', '').strip()
            short_dialogue = clean_line[:200] + ("..." if len(clean_line) > 200 else "")

            prompt = f"{STYLE_PREFIX}{lead_dna}, {'expressive dialogue close-up, talking intensely' if is_dialogue else 'dramatic narrative scene, engaging posture'}, setting: {bg_anchor}, manga panel{STYLE_SUFFIX}"

            panels.append({
                "panel_index": idx + 1,
                "image_prompt": prompt,
                "dialogue_text": short_dialogue,
                "layout_type": layout
            })

        if not panels:
            panels = [
                {"panel_index": 1, "image_prompt": f"{STYLE_PREFIX}{lead_dna}, wide establishing shot of {bg_anchor}{STYLE_SUFFIX}", "dialogue_text": "Câu chuyện bắt đầu...", "layout_type": "wide"},
                {"panel_index": 2, "image_prompt": f"{STYLE_PREFIX}{lead_dna}, medium shot of character speaking with intense emotion, setting: {bg_anchor}{STYLE_SUFFIX}", "dialogue_text": "Chúng ta phải tiếp tục!", "layout_type": "square"},
            ]
        return panels
