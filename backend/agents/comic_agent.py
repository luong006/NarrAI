import os
import json
import re
from llm.groq_client import GroqClient
from agents.story_memory import StoryMemory

STYLE_SUFFIX = ", manga panel, grayscale, monochrome, ink linework, black and white with gray tones, screentone shading, bold outlines, japanese manga style, high contrast, no color"

# ============ PASS 1: SCENE SPLITTER ============
SCENE_SPLITTER_PROMPT = """# SYSTEM ROLE -- STORY SCENE ANALYZER

You are a Story Structure Analyzer. You read Vietnamese story text and split it into distinct SCENES.

## WHAT IS A SCENE?
A scene is a self-contained narrative unit where:
- The same characters are in the same location
- A single event or interaction happens
- When location, time, or character group changes = NEW SCENE

## RULES
1. Read the full text carefully
2. Identify natural scene breaks (location change, time skip, new character enters, mood shift)
3. Split into 2-5 scenes (minimum 2, maximum 5)
4. Each scene should have enough content for 4-6 comic panels
5. Write a brief summary for each scene
6. Include the EXACT text portion that belongs to each scene

## OUTPUT FORMAT
Output ONLY a valid JSON array. No markdown, no explanations.
[{"scene_index": 1, "summary": "Brief description of what happens", "text_chunk": "The exact portion of the story text for this scene"}, ...]
"""

# ============ PASS 2: PANEL GENERATOR (per scene) ============
PANEL_GENERATOR_PROMPT = """# SYSTEM ROLE -- MANGA PANEL PROMPT COMPILER

You convert a SINGLE SCENE from a Vietnamese story into manga panels.

## VISUAL STYLE (MANDATORY)
Every image_prompt MUST end with: ", manga panel, grayscale, monochrome, ink linework, screentone shading, bold outlines, japanese manga style, high contrast, no color"

## NARRATIVE FLOW
Tell this scene's story across exactly 4 panels:
- Panel 1: SETUP - Where are we? Who is present?
- Panel 2: ACTION - What starts happening?
- Panel 3: REACTION - How do characters respond?
- Panel 4: OUTCOME - How does this scene end/transition?

Each panel MUST connect to the previous. dialogue_text must form a readable mini-story.

## RULES
1. Focus ONLY on the scene text provided. Do not invent content outside this scene.
2. Characters must look IDENTICAL to their ontology descriptions.
3. image_prompt in English, under 100 words.
4. dialogue_text in Vietnamese, under 25 words, must advance the story.
5. Vary layout_type: "wide" for establishing, "square" for dialogue, "tall" for drama.
6. Simple compositions: 1-3 characters, simple backgrounds.

## OUTPUT FORMAT
Output ONLY a valid JSON array. No markdown, no explanations, no thinking.
[{"panel_index": 1, "image_prompt": "...", "dialogue_text": "...", "layout_type": "wide"}, ...]
"""

# ============ CONTINUATION PROMPT ============
CONTINUE_PROMPT = """# SYSTEM ROLE -- MANGA CONTINUATION COMPILER

Continue an existing manga. You are given previous panel summaries and new scene text.

## RULES
- Create exactly 4 NEW panels continuing from the previous panels
- Do NOT repeat any previous scene
- Characters must look IDENTICAL to their descriptions
- Follow GRAYSCALE manga style

## VISUAL STYLE
End every image_prompt with: ", manga panel, grayscale, monochrome, ink linework, screentone shading, bold outlines, japanese manga style, high contrast, no color"

## OUTPUT FORMAT
Output ONLY a valid JSON array. No markdown, no explanations.
[{"panel_index": 1, "image_prompt": "...", "dialogue_text": "...", "layout_type": "wide"}, ...]
"""

LAYOUT_MAP = {
    "wide": "wide", "horizontal": "wide", "landscape": "wide", "panoramic": "wide",
    "tall": "tall", "vertical": "tall", "portrait": "tall",
    "square": "square", "medium": "square", "close-up": "square", "closeup": "square",
}


class ComicDirectorAgent:
    def __init__(self):
        api_key = os.environ.get("GROQ_API_KEY_COMIC") or os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise ValueError("Missing GROQ_API_KEY_COMIC or GROQ_API_KEY")
        self.llm = GroqClient(model_name="qwen/qwen3.8-27b", api_key=api_key)

    def _build_ontology(self, memory):
        """Build ontology context block from StoryMemory."""
        if not memory:
            return ""
        lines = ["=== ONTOLOGY (Character & Setting Map) ==="]
        if memory.story_bible and memory.story_bible.characters:
            lines.append("CHARACTERS:")
            for c in memory.story_bible.characters:
                if isinstance(c, dict):
                    name = c.get("name", "?")
                    appearance = c.get("appearance", "unknown")
                    role = c.get("role", "")
                    lines.append(f"  - {name}: {role}. Appearance: {appearance}")
                elif isinstance(c, str):
                    lines.append(f"  - {c}")
        if memory.character_states:
            lines.append("CURRENT STATES:")
            for name, state in memory.character_states.items():
                lines.append(f"  - {name}: {state}")
        if memory.relationship_map:
            lines.append("RELATIONSHIPS:")
            for pair, desc in memory.relationship_map.items():
                lines.append(f"  - {pair}: {desc}")
        if memory.story_bible and memory.story_bible.world_setting:
            lines.append(f"SETTING: {memory.story_bible.world_setting}")
        return "\n".join(lines) + "\n\n"

    def _parse_json_array(self, raw_output):
        """Extract and parse a JSON array from LLM output."""
        cleaned = re.sub(r'```(?:json)?\s*', '', raw_output)
        cleaned = cleaned.strip()
        match = re.search(r'\[.*\]', cleaned, re.DOTALL)
        if match:
            cleaned = match.group(0)
        return json.loads(cleaned, strict=False)

    def _validate_panels(self, script_data, max_panels=6):
        """Validate and normalize panel data."""
        if not isinstance(script_data, list):
            raise ValueError("Output is not a JSON array")

        validated = []
        for i, item in enumerate(script_data[:max_panels]):
            prompt = item.get("image_prompt", "a manga scene")
            if "grayscale" not in prompt.lower():
                prompt += STYLE_SUFFIX
            raw_layout = item.get("layout_type", "square").lower().strip()
            normalized_layout = LAYOUT_MAP.get(raw_layout, "square")

            validated.append({
                "panel_index": i + 1,
                "image_prompt": prompt,
                "dialogue_text": item.get("dialogue_text", ""),
                "layout_type": normalized_layout
            })
        return validated

    # ==================== PASS 1: SCENE SPLITTING ====================
    def _split_into_scenes(self, story_text):
        """Pass 1: Split story text into distinct scenes using LLM."""
        try:
            response = self.llm.chat(
                messages=[
                    {"role": "system", "content": SCENE_SPLITTER_PROMPT},
                    {"role": "user", "content": f"Split this story into 2-5 scenes. Output ONLY a JSON array.\n\n{story_text[:6000]}"}
                ],
                temperature=0.2,
                max_tokens=3000
            )
            scenes = self._parse_json_array(response)
            if not isinstance(scenes, list) or len(scenes) == 0:
                raise ValueError("Scene splitter returned empty result")

            # Validate scenes (cap at 5)
            validated = []
            for i, s in enumerate(scenes[:5]):
                validated.append({
                    "scene_index": i + 1,
                    "summary": s.get("summary", f"Scene {i+1}"),
                    "text_chunk": s.get("text_chunk", "")
                })
            return validated
        except Exception as e:
            print(f"Scene splitting failed: {e}")
            # Fallback: treat entire text as 1 scene
            return [{"scene_index": 1, "summary": "Full story", "text_chunk": story_text[:6000]}]

    # ==================== PASS 2: PANELS PER SCENE ====================
    def _generate_panels_for_scene(self, scene, ontology_block, previous_summary=""):
        """Pass 2: Generate 4 panels for a single scene."""
        try:
            context = ontology_block
            if previous_summary:
                context += f"=== PREVIOUS PANELS ===\n{previous_summary}\n\n"
            context += f"=== SCENE TO DRAW ===\nScene summary: {scene['summary']}\n\nScene text:\n{scene['text_chunk']}"

            prompt_to_use = PANEL_GENERATOR_PROMPT if not previous_summary else CONTINUE_PROMPT

            response = self.llm.chat(
                messages=[
                    {"role": "system", "content": prompt_to_use},
                    {"role": "user", "content": f"Create exactly 4 manga panels for this scene. Output ONLY a JSON array.\n\n{context}"}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            panels = self._parse_json_array(response)
            return self._validate_panels(panels, max_panels=4)
        except Exception as e:
            print(f"Panel generation failed for scene {scene.get('scene_index')}: {e}")
            return self._fallback_panels_mini()

    # ==================== MAIN PUBLIC METHODS ====================
    def generate_comic_script(self, story_text, memory=None):
        """2-pass pipeline: Split into scenes, then generate panels per scene."""
        ontology_block = self._build_ontology(memory)

        # Pass 1: Split into scenes
        print(f"[Comic] Pass 1: Splitting {len(story_text)} chars into scenes...")
        scenes = self._split_into_scenes(story_text)
        print(f"[Comic] Found {len(scenes)} scenes")

        # Pass 2: Generate panels for each scene
        all_panels = []
        running_summary = ""
        global_index = 0

        for scene in scenes:
            print(f"[Comic] Pass 2: Generating panels for scene {scene['scene_index']}: {scene['summary'][:60]}...")
            panels = self._generate_panels_for_scene(scene, ontology_block, running_summary)

            # Re-index panels globally
            for p in panels:
                global_index += 1
                p["panel_index"] = global_index

            all_panels.extend(panels)

            # Build running summary for next scene's context
            scene_dialogues = " -> ".join([p["dialogue_text"] for p in panels if p["dialogue_text"]])
            running_summary += f"Scene {scene['scene_index']}: {scene_dialogues}\n"

        print(f"[Comic] Total panels generated: {len(all_panels)}")
        return all_panels

    def generate_continuation(self, previous_summary, new_text, memory=None):
        """Continue comic from new text with scene-aware splitting."""
        ontology_block = self._build_ontology(memory)

        # Split new text into scenes
        scenes = self._split_into_scenes(new_text)

        all_panels = []
        running_summary = previous_summary
        global_index = 0

        for scene in scenes:
            panels = self._generate_panels_for_scene(scene, ontology_block, running_summary)

            for p in panels:
                global_index += 1
                p["panel_index"] = global_index

            all_panels.extend(panels)

            scene_dialogues = " -> ".join([p["dialogue_text"] for p in panels if p["dialogue_text"]])
            running_summary += f"\nScene {scene['scene_index']}: {scene_dialogues}"

        return all_panels

    def _fallback_panels_mini(self):
        """Fallback: 2 minimal panels for a failed scene."""
        return [
            {"panel_index": 1, "image_prompt": "establishing shot of a scene" + STYLE_SUFFIX, "dialogue_text": "...", "layout_type": "wide"},
            {"panel_index": 2, "image_prompt": "characters interacting in the scene" + STYLE_SUFFIX, "dialogue_text": "...", "layout_type": "square"},
        ]

    def _fallback_panels(self):
        """Fallback: 3 panels for total failure."""
        return [
            {"panel_index": 1, "image_prompt": "wide establishing shot of a scenic landscape" + STYLE_SUFFIX, "dialogue_text": "Cau chuyen bat dau...", "layout_type": "wide"},
            {"panel_index": 2, "image_prompt": "medium shot of a young character looking determined" + STYLE_SUFFIX, "dialogue_text": "Hay bat dau cuoc phieu luu!", "layout_type": "square"},
            {"panel_index": 3, "image_prompt": "dramatic low angle shot of characters walking forward" + STYLE_SUFFIX, "dialogue_text": "Va hanh trinh tiep tuc...", "layout_type": "wide"},
        ]
