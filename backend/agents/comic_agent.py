import os
import json
import re
from llm.groq_client import GroqClient
from agents.story_memory import StoryMemory

# STRICT style prefix and suffix to force Diffusion model attention to B&W Manga
STYLE_PREFIX = "black and white manga, Japanese manga comic art, monochrome ink drawing on paper, "
STYLE_SUFFIX = ", manga panel, screentone shading, bold ink outlines, high contrast black ink, clean lineart, no color, hand drawn 2D illustration, no photograph, no 3D render"

# ==================== PASS 1: SCENE ANALYZER & DIRECTOR ====================
SCENE_SPLITTER_PROMPT = """You are a master manga editor and novelist (in the tradition of Weekly Shonen Jump editors).

Your mission: Read a Vietnamese novel/story excerpt and divide it into 2 to 4 distinct NARRATIVE SCENES for a manga chapter.

A scene changes when:
1. The location changes (e.g. from home to school, from office to cafe).
2. The time jumps (e.g. morning to evening, next day).
3. A major event or turning point alters the mood completely.
4. New characters enter the scene.

CRITICAL RULES FOR ADAPTATION:
- Scene 1 MUST ALWAYS be the OPENING SCENE: It introduces the setting (where & when) and the protagonist in their normal world before the drama begins.
- Subsequent scenes escalate the action, bring the conflict/turning point, and lead to an emotional resolution or cliffhanger.
- Each scene must be focused, self-contained, and depict a clear beat of the story.

OUTPUT FORMAT:
Return ONLY a valid JSON array of objects. No markdown wrappers, no introductory or concluding text:
[
  {
    "scene_index": 1,
    "summary": "Brief English summary of what happens in this scene",
    "text_chunk": "The exact Vietnamese text segment corresponding to this scene"
  }
]
"""

# ==================== PASS 2: FIRST SCENE (OPENING PAGE) PROMPT ====================
FIRST_SCENE_PROMPT = """You are a legendary manga artist (combining the world-building of Eiichiro Oda and the visual pacing of Takehiko Inoue).
You are directing the OPENING PAGE of a manga chapter.

The opening of a manga chapter MUST orient and captivate the reader using the classical Kishōtenketsu structure:
- Panel 1: WIDE ESTABLISHING SHOT (Ki / Origin). Panoramic view of the environment/city/room. Sets the atmosphere, time, and weather. Minimal character presence (silhouettes or distant view). Text is atmospheric narration. NO sudden dialogues.
- Panel 2: PROTAGONIST INTRODUCTION (Sho / Development). Full-body or medium shot of the main character in their normal environment. Shows their signature clothing, hair, and posture clearly.
- Panel 3: INTIMATE FOCUS / REACTION (Sho / Deepening). Close-up of the protagonist's face or hands interacting with an object. Conveys their inner mood or emotions.
- Panel 4: INCITING MOMENT / TURNING POINT (Ten / Turn). An unexpected event, a ringtone, an arrival, or a realization that shatters the calm and kicks off the adventure.

CRITICAL VISUAL CONSISTENCY RULES:
1. You MUST copy the EXACT physical description of characters (hair, clothes, eyes, features) from the ONTOLOGY into every image_prompt they appear in.
2. For image_prompt: Write in descriptive English, focusing on composition, camera angle, character appearance, and environment. Keep under 70 words.
3. For dialogue_text: Write in natural Vietnamese. MAXIMUM 12 WORDS per panel! Short and punchy like real manga speech bubbles.
4. Vary layout_type: Use "wide" for the establishing shot, "square" for medium/dialogue, and "tall" or "square" for dramatic close-ups.

OUTPUT FORMAT:
Return ONLY a valid JSON array:
[
  {"panel_index": 1, "image_prompt": "...", "dialogue_text": "...", "layout_type": "wide"},
  {"panel_index": 2, "image_prompt": "...", "dialogue_text": "...", "layout_type": "square"},
  {"panel_index": 3, "image_prompt": "...", "dialogue_text": "...", "layout_type": "square"},
  {"panel_index": 4, "image_prompt": "...", "dialogue_text": "...", "layout_type": "tall"}
]
"""

# ==================== PASS 2: SUBSEQUENT SCENE PROMPT ====================
SCENE_PANEL_PROMPT = """You are a master manga director adapting an ongoing scene of a story into 4 visual panels.

NARRATIVE FLOW (4 Panels):
- Panel 1: SETUP - Show the characters in the new setting or ready for the new action.
- Panel 2: ACTION / DIALOGUE - The key interaction, dialogue, or confrontation occurs.
- Panel 3: CLIMAX / REACTION - Dynamic perspective or dramatic close-up showing the emotional peak of this scene.
- Panel 4: RESOLUTION / CLIFFHANGER - The immediate consequence or transition into the next beat.

CRITICAL VISUAL CONSISTENCY RULES:
1. You MUST copy the EXACT physical description of characters (hair, clothes, eyes, features) from the ONTOLOGY into every image_prompt they appear in.
2. Characters MUST NOT change outfits, hairstyles, or ages randomly!
3. For image_prompt: Write in descriptive English. Keep under 70 words.
4. For dialogue_text: Write in natural Vietnamese. MAXIMUM 12 WORDS per panel!
5. Vary layout_type: "wide", "square", or "tall".

OUTPUT FORMAT:
Return ONLY a valid JSON array of 4 panel objects:
[
  {"panel_index": 1, "image_prompt": "...", "dialogue_text": "...", "layout_type": "wide"}, ...
]
"""

# ==================== CONTINUATION PROMPT ====================
CONTINUE_PANEL_PROMPT = """You are a master manga director continuing an existing comic with NEW panels from newly written story text.

RULES:
1. Read the summary of previous panels so the new scene connects seamlessly.
2. Create 4 NEW panels that continue from the exact point the story left off.
3. Maintain 100% visual consistency: Use identical character descriptions and clothes.
4. dialogue_text in Vietnamese, MAXIMUM 12 WORDS.
5. layout_type: "wide", "square", or "tall".

OUTPUT FORMAT:
Return ONLY a valid JSON array of 4 panel objects:
[
  {"panel_index": 1, "image_prompt": "...", "dialogue_text": "...", "layout_type": "wide"}, ...
]
"""

LAYOUT_MAP = {
    "wide": "wide", "horizontal": "wide", "landscape": "wide", "panoramic": "wide", "establishing": "wide",
    "tall": "tall", "vertical": "tall", "portrait": "tall", "dramatic": "tall",
    "square": "square", "medium": "square", "close-up": "square", "closeup": "square", "standard": "square",
}


class ComicDirectorAgent:
    def __init__(self):
        api_key = os.environ.get("GROQ_API_KEY_COMIC") or os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise ValueError("Thiếu GROQ_API_KEY_COMIC hoặc GROQ_API_KEY")
        self.llm = GroqClient(model_name="qwen/qwen3.8-27b", api_key=api_key)

    def _build_ontology(self, memory):
        """Build ontology context block from StoryMemory for visual consistency."""
        if not memory:
            return ""
        lines = ["=== ONTOLOGY (Character & Setting Visual Guide) ==="]
        if memory.story_bible and memory.story_bible.characters:
            lines.append("CHARACTERS (YOU MUST MAINTAIN THESE EXACT VISUAL DESCRIPTIONS):")
            for c in memory.story_bible.characters:
                if isinstance(c, dict):
                    name = c.get("name", "?")
                    appearance = c.get("appearance", "unknown")
                    role = c.get("role", "")
                    lines.append(f"  * {name} ({role}): Appearance -> {appearance}")
                elif isinstance(c, str):
                    lines.append(f"  * {c}")
        if memory.character_states:
            lines.append("CURRENT CHARACTER STATES:")
            for name, state in memory.character_states.items():
                lines.append(f"  * {name}: {state}")
        if memory.relationship_map:
            lines.append("RELATIONSHIPS:")
            for pair, desc in memory.relationship_map.items():
                lines.append(f"  * {pair}: {desc}")
        if memory.story_bible and memory.story_bible.world_setting:
            lines.append(f"CANONICAL SETTING: {memory.story_bible.world_setting}")
        return "\n".join(lines) + "\n\n"

    def _parse_json_array(self, raw_output):
        """Extract and parse a JSON array from LLM output."""
        cleaned = re.sub(r'```(?:json)?\s*', '', raw_output).strip()
        match = re.search(r'\[.*\]', cleaned, re.DOTALL)
        if match:
            cleaned = match.group(0)
        return json.loads(cleaned, strict=False)

    def _validate_panels(self, script_data, max_panels=4):
        """Validate, normalize layout, enforce style prefix & suffix, and cap dialogue length."""
        if not isinstance(script_data, list):
            raise ValueError("Output is not a JSON array")

        validated = []
        for i, item in enumerate(script_data[:max_panels]):
            prompt = item.get("image_prompt", "a manga scene").strip()
            
            # Remove any duplicate style tags if LLM already included them
            clean_prompt = prompt
            for tag in ["manga panel", "black and white", "monochrome", "screentone"]:
                clean_prompt = re.sub(re.escape(tag), "", clean_prompt, flags=re.IGNORECASE)
            clean_prompt = clean_prompt.strip(" ,.-")

            # Prepend STYLE_PREFIX and append STYLE_SUFFIX
            final_prompt = f"{STYLE_PREFIX}{clean_prompt}{STYLE_SUFFIX}"

            raw_layout = str(item.get("layout_type", "square")).lower().strip()
            normalized_layout = LAYOUT_MAP.get(raw_layout, "square")

            # Strictly enforce short dialogue (max 15 words) so speech bubbles never scroll
            dialogue = str(item.get("dialogue_text", "")).strip()
            words = dialogue.split()
            if len(words) > 15:
                dialogue = " ".join(words[:13]) + "..."

            validated.append({
                "panel_index": i + 1,
                "image_prompt": final_prompt,
                "dialogue_text": dialogue,
                "layout_type": normalized_layout
            })
        return validated

    def _split_into_scenes(self, story_text):
        """Pass 1: Split story into distinct scenes."""
        try:
            response = self.llm.chat(
                messages=[
                    {"role": "system", "content": SCENE_SPLITTER_PROMPT},
                    {"role": "user", "content": f"Analyze and split this Vietnamese story excerpt into 2 to 4 distinct manga scenes:\n\n{story_text[:6000]}"}
                ],
                temperature=0.2,
                max_tokens=3000
            )
            scenes = self._parse_json_array(response)
            if not isinstance(scenes, list) or len(scenes) == 0:
                raise ValueError("Empty scene list returned by LLM")
            validated = []
            for i, s in enumerate(scenes[:4]):
                validated.append({
                    "scene_index": i + 1,
                    "summary": s.get("summary", f"Scene {i+1}"),
                    "text_chunk": s.get("text_chunk", "")
                })
            return validated
        except Exception as e:
            print(f"[Comic] Scene splitting failed ({e}), falling back to single scene.")
            return [{"scene_index": 1, "summary": "Full Scene", "text_chunk": story_text[:6000]}]

    def _generate_panels_for_scene(self, scene, ontology_block, is_first_scene=False, previous_summary=""):
        """Pass 2: Generate 4 manga panels for a single scene."""
        try:
            context = ontology_block
            if previous_summary:
                context += f"=== PREVIOUS PANELS SUMMARY ===\n{previous_summary}\n\n"
            context += f"=== CURRENT SCENE TO ADAPT ===\nSummary: {scene['summary']}\n\nText:\n{scene['text_chunk']}"

            if is_first_scene and not previous_summary:
                prompt_to_use = FIRST_SCENE_PROMPT
            elif previous_summary:
                prompt_to_use = CONTINUE_PANEL_PROMPT
            else:
                prompt_to_use = SCENE_PANEL_PROMPT

            response = self.llm.chat(
                messages=[
                    {"role": "system", "content": prompt_to_use},
                    {"role": "user", "content": f"Create exactly 4 manga panels for this scene. Output ONLY a valid JSON array.\n\n{context}"}
                ],
                temperature=0.3,
                max_tokens=2500
            )
            panels = self._parse_json_array(response)
            return self._validate_panels(panels, max_panels=4)
        except Exception as e:
            print(f"[Comic] Panel generation failed for scene {scene.get('scene_index')}: {e}")
            return self._fallback_panels_for_scene(is_first_scene)

    def generate_comic_script(self, story_text, memory=None):
        """2-pass pipeline: Split story into scenes, then generate sequential panels per scene."""
        ontology_block = self._build_ontology(memory)

        print(f"[Comic] Pass 1: Splitting {len(story_text)} chars into scenes...")
        scenes = self._split_into_scenes(story_text)
        print(f"[Comic] Found {len(scenes)} scenes to adapt.")

        all_panels = []
        running_summary = ""
        global_index = 0

        for i, scene in enumerate(scenes):
            is_first = (i == 0)
            print(f"[Comic] Pass 2: Adapting Scene {scene['scene_index']} ('{scene['summary'][:50]}')...")
            panels = self._generate_panels_for_scene(
                scene, ontology_block,
                is_first_scene=is_first,
                previous_summary=running_summary if not is_first else ""
            )

            for p in panels:
                global_index += 1
                p["panel_index"] = global_index

            all_panels.extend(panels)

            scene_dialogues = " -> ".join([p["dialogue_text"] for p in panels if p["dialogue_text"]])
            running_summary += f"Scene {scene['scene_index']}: {scene_dialogues}\n"

        print(f"[Comic] Total manga panels generated: {len(all_panels)}")
        return all_panels

    def generate_continuation(self, previous_summary, new_text, memory=None):
        """Continue existing comic from new story text."""
        ontology_block = self._build_ontology(memory)
        scenes = self._split_into_scenes(new_text)

        all_panels = []
        running_summary = previous_summary
        global_index = 0

        for scene in scenes:
            panels = self._generate_panels_for_scene(scene, ontology_block, previous_summary=running_summary)
            for p in panels:
                global_index += 1
                p["panel_index"] = global_index
            all_panels.extend(panels)
            scene_dialogues = " -> ".join([p["dialogue_text"] for p in panels if p["dialogue_text"]])
            running_summary += f"\nScene {scene['scene_index']}: {scene_dialogues}"

        return all_panels

    def _fallback_panels_for_scene(self, is_first_scene=False):
        """Clean fallback panels with guaranteed B&W style."""
        if is_first_scene:
            return [
                {"panel_index": 1, "image_prompt": f"{STYLE_PREFIX}wide panoramic establishing shot of the city street at dawn, peaceful morning atmosphere{STYLE_SUFFIX}", "dialogue_text": "Buổi sáng tại thành phố...", "layout_type": "wide"},
                {"panel_index": 2, "image_prompt": f"{STYLE_PREFIX}medium shot of the main character standing near a window, gentle expression, morning sunlight{STYLE_SUFFIX}", "dialogue_text": "Một ngày mới lại bắt đầu.", "layout_type": "square"},
                {"panel_index": 3, "image_prompt": f"{STYLE_PREFIX}close-up shot of the protagonist holding a warm cup, looking thoughtful{STYLE_SUFFIX}", "dialogue_text": "Mọi thứ dường như thật yên bình...", "layout_type": "square"},
                {"panel_index": 4, "image_prompt": f"{STYLE_PREFIX}dynamic shot of a phone screen suddenly ringing with an urgent notification{STYLE_SUFFIX}", "dialogue_text": "Nhưng rồi điều bất ngờ ập đến!", "layout_type": "tall"},
            ]
        else:
            return [
                {"panel_index": 1, "image_prompt": f"{STYLE_PREFIX}medium establishing shot of the characters at the new location{STYLE_SUFFIX}", "dialogue_text": "Tại điểm hẹn...", "layout_type": "wide"},
                {"panel_index": 2, "image_prompt": f"{STYLE_PREFIX}two characters in serious dialogue, tense expressions{STYLE_SUFFIX}", "dialogue_text": "Chúng ta phải hành động ngay.", "layout_type": "square"},
                {"panel_index": 3, "image_prompt": f"{STYLE_PREFIX}dramatic low angle perspective of character stepping forward{STYLE_SUFFIX}", "dialogue_text": "Tôi sẽ không lùi bước!", "layout_type": "square"},
                {"panel_index": 4, "image_prompt": f"{STYLE_PREFIX}wide reaction shot of the room as a new figure enters{STYLE_SUFFIX}", "dialogue_text": "Ai đó vừa đến...", "layout_type": "tall"},
            ]
