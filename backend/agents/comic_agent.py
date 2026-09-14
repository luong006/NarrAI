import os
import json
import re
from llm.groq_client import GroqClient
from agents.story_memory import StoryMemory

STYLE_SUFFIX = ", manga panel, grayscale, monochrome, ink linework, black and white with gray tones, screentone shading, bold outlines, japanese manga style, high contrast, no color"

COMIC_COMPILER_PROMPT = """# SYSTEM ROLE -- MANGA PANEL PROMPT COMPILER

You are a Visual Prompt Engineer. You convert Vietnamese story text into image prompts for a manga comic.

## VISUAL STYLE (MANDATORY - APPEND TO EVERY image_prompt)
Every image_prompt MUST describe a GRAYSCALE manga scene. No color allowed.
End every prompt with: ", manga panel, grayscale, monochrome, ink linework, screentone shading, bold outlines, japanese manga style, high contrast, no color"

## NARRATIVE STRUCTURE (MANDATORY)
You must tell a coherent story across exactly 6 panels:
- Panel 1-2: INTRODUCTION - Establish setting, show main characters arriving/present
- Panel 3-4: CONFLICT - The main event/problem/action happens, tension rises
- Panel 5-6: RESOLUTION - Outcome, emotional reaction, conclusion

CRITICAL: Each panel MUST connect to the previous one. The dialogue_text must tell a readable story when read from panel 1 to 6 in sequence.

## RULES
1. Read the story text carefully. Extract the MAIN STORYLINE (not side details).
2. Create exactly 6 panels. Each depicts a DIFFERENT moment in sequence.
3. Characters must look IDENTICAL across all panels (same hair, clothes, features).
4. Write image_prompt in English only. Under 100 words each.
5. Write dialogue_text in Vietnamese. Under 25 words. Must advance the story.
6. Vary layout_type: "wide" for establishing shots, "square" for dialogue, "tall" for drama.
7. Keep compositions simple: 1-3 characters, simple backgrounds.

## OUTPUT FORMAT
Output ONLY a valid JSON array. No markdown, no explanations, no thinking.
[{"panel_index": 1, "image_prompt": "...", "dialogue_text": "...", "layout_type": "wide"}, ...]
"""

CONTINUE_PROMPT = """# SYSTEM ROLE -- MANGA CONTINUATION COMPILER

You continue an existing manga comic. You are given:
1. A summary of previous panels (what has been drawn so far)
2. New story text to adapt (the next part of the story)

## RULES
- Create exactly 6 NEW panels that CONTINUE from where the previous panels left off
- Do NOT repeat any scene from the previous panels
- Characters must look IDENTICAL to their previous descriptions
- The first new panel must naturally follow the last previous panel
- Follow the same GRAYSCALE manga style

## VISUAL STYLE
End every image_prompt with: ", manga panel, grayscale, monochrome, ink linework, screentone shading, bold outlines, japanese manga style, high contrast, no color"

## OUTPUT FORMAT
Output ONLY a valid JSON array. No markdown, no explanations.
[{"panel_index": 1, "image_prompt": "...", "dialogue_text": "...", "layout_type": "wide"}, ...]
"""


class ComicDirectorAgent:
    def __init__(self):
        api_key = os.environ.get("GROQ_API_KEY_COMIC") or os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise ValueError("Thieu GROQ_API_KEY_COMIC hoac GROQ_API_KEY")
        self.llm = GroqClient(model_name="qwen/qwen3.8-27b", api_key=api_key)

    def _build_ontology(self, memory):
        """Build ontology context block from StoryMemory for character/setting consistency."""
        if not memory:
            return ""
        lines = ["=== ONTOLOGY (Character & Setting Map) ==="]
        
        # Characters from bible
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
        
        # Character states
        if memory.character_states:
            lines.append("CURRENT STATES:")
            for name, state in memory.character_states.items():
                lines.append(f"  - {name}: {state}")
        
        # Relationships
        if memory.relationship_map:
            lines.append("RELATIONSHIPS:")
            for pair, desc in memory.relationship_map.items():
                lines.append(f"  - {pair}: {desc}")
        
        # Setting
        if memory.story_bible and memory.story_bible.world_setting:
            lines.append(f"SETTING: {memory.story_bible.world_setting}")
        
        return "\n".join(lines) + "\n\n"

    def _parse_response(self, raw_output):
        """Parse LLM response into validated panel list."""
        # Remove markdown wrappers
        cleaned = re.sub(r'```(?:json)?\s*', '', raw_output)
        cleaned = cleaned.strip()
        
        # Extract JSON array
        match = re.search(r'\[.*\]', cleaned, re.DOTALL)
        if match:
            cleaned = match.group(0)
        
        script_data = json.loads(cleaned, strict=False)
        
        if not isinstance(script_data, list):
            raise ValueError("Output is not a JSON array")
        
        # Cap at 6 panels and validate
        # Normalize layout_type: LLMs often invent names outside our CSS set
        LAYOUT_MAP = {
            "wide": "wide", "horizontal": "wide", "landscape": "wide", "panoramic": "wide",
            "tall": "tall", "vertical": "tall", "portrait": "tall",
            "square": "square", "medium": "square", "close-up": "square", "closeup": "square",
        }
        
        validated = []
        for i, item in enumerate(script_data[:6]):
            prompt = item.get("image_prompt", "a manga scene")
            # Enforce grayscale style suffix if not present
            if "grayscale" not in prompt.lower():
                prompt += STYLE_SUFFIX
            
            raw_layout = item.get("layout_type", "square").lower().strip()
            normalized_layout = LAYOUT_MAP.get(raw_layout, "square")
            
            validated.append({
                "panel_index": item.get("panel_index", i + 1),
                "image_prompt": prompt,
                "dialogue_text": item.get("dialogue_text", ""),
                "layout_type": normalized_layout
            })
        
        return validated

    def generate_comic_script(self, story_text, memory=None):
        """Generate initial comic panels from story text."""
        try:
            context = self._build_ontology(memory)
            context += "=== STORY TEXT TO ADAPT ===\n"
            context += story_text[:6000]

            response = self.llm.chat(
                messages=[
                    {"role": "system", "content": COMIC_COMPILER_PROMPT},
                    {"role": "user", "content": f"Create exactly 6 manga panels from this story. Output ONLY a JSON array.\n\n{context}"}
                ],
                temperature=0.3,
                max_tokens=3000
            )
            return self._parse_response(response)
        except Exception as e:
            print(f"Error parsing comic script: {e}")
            try:
                print(f"RAW OUTPUT: {response[:500]}")
            except:
                pass
            return self._fallback_panels()

    def generate_continuation(self, previous_summary, new_text, memory=None):
        """Generate continuation panels from new story text, given previous panel summary."""
        try:
            context = self._build_ontology(memory)
            context += f"=== PREVIOUS PANELS SUMMARY ===\n{previous_summary}\n\n"
            context += f"=== NEW STORY TEXT TO ADAPT ===\n{new_text[:6000]}"

            response = self.llm.chat(
                messages=[
                    {"role": "system", "content": CONTINUE_PROMPT},
                    {"role": "user", "content": f"Continue the manga with 6 new panels. Output ONLY a JSON array.\n\n{context}"}
                ],
                temperature=0.3,
                max_tokens=3000
            )
            return self._parse_response(response)
        except Exception as e:
            print(f"Error parsing continuation: {e}")
            return self._fallback_panels()

    def _fallback_panels(self):
        return [
            {"panel_index": 1, "image_prompt": "wide establishing shot of a scenic landscape" + STYLE_SUFFIX, "dialogue_text": "Cau chuyen bat dau...", "layout_type": "wide"},
            {"panel_index": 2, "image_prompt": "medium shot of a young character looking determined" + STYLE_SUFFIX, "dialogue_text": "Hay bat dau cuoc phieu luu!", "layout_type": "square"},
            {"panel_index": 3, "image_prompt": "dramatic low angle shot of characters walking forward" + STYLE_SUFFIX, "dialogue_text": "Va hanh trinh tiep tuc...", "layout_type": "wide"},
        ]
