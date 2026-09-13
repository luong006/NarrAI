import os
import json
import re
from llm.groq_client import GroqClient
from agents.story_memory import StoryMemory

# System prompt optimized for Shin-chan / classic manga panel style
COMIC_COMPILER_PROMPT = """# SYSTEM ROLE -- MANGA PANEL PROMPT COMPILER

You are a specialized Visual Prompt Engineer. You convert Vietnamese story text into image-generation prompts for a manga comic.

## VISUAL STYLE (MANDATORY FOR ALL PANELS)
Every image_prompt you generate MUST end with this exact style suffix:
", manga panel, clean ink linework, black and white, simple bold outlines, expressive cartoon characters, screentone shading, white background, japanese manga style, high contrast"

## RULES
1. Read the story text carefully. Identify the KEY MOMENTS that advance the plot.
2. Create exactly 6 panels that tell the story visually.
3. Each panel must depict a DIFFERENT scene/moment (do not repeat the same scene).
4. Focus on CHARACTER ACTIONS and EXPRESSIONS - show don't tell.
5. If character descriptions are provided in the STORY BIBLE, use them exactly. Do not change hair color, clothing, or features.
6. Write image_prompt in English only. Keep it under 120 words.
7. Write dialogue_text in Vietnamese. Keep it SHORT (under 30 words) - like speech bubbles.
8. Vary layout_type to create visual rhythm: mix "wide" for establishing/action shots, "square" for dialogue/reaction, "tall" for dramatic moments.

## PANEL COMPOSITION GUIDE (Shin-chan manga style)
- Use simple, clean compositions with 1-3 characters per panel
- Characters should have exaggerated facial expressions (surprise, anger, joy, shock)
- Include speech bubble space in composition (leave open areas near character faces)
- Background should be simple: indoor rooms, streets, parks - not overly detailed
- Use comedic framing: zoomed-in reaction faces, chibi proportions for comedy

## OUTPUT FORMAT
Output ONLY a valid JSON array. No markdown, no explanations.
Each object: {"panel_index": int, "image_prompt": "...", "dialogue_text": "...", "layout_type": "square|wide|tall"}
"""

class ComicDirectorAgent:
    def __init__(self):
        api_key = os.environ.get("GROQ_API_KEY_COMIC") or os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise ValueError("Thieu GROQ_API_KEY_COMIC hoac GROQ_API_KEY")
        
        # Using a fast model to avoid timeout on free hosting (30s limit)
        self.llm = GroqClient(model_name="qwen/qwen3.8-27b", api_key=api_key)

    def generate_comic_script(self, story_text: str, memory: StoryMemory = None):
        try:
            # Build Context from Memory
            context = ""
            if memory and memory.story_bible:
                context += "=== STORY BIBLE (CHARACTER APPEARANCES - USE EXACTLY) ===\n"
                context += f"Characters: {json.dumps(memory.story_bible.characters, ensure_ascii=False)}\n"
                context += f"World/Setting: {memory.story_bible.world_rules}\n"
                context += f"Genre/Tone: {memory.story_bible.genre} - {memory.story_bible.tone}\n\n"
                
            context += "=== STORY TEXT TO ADAPT ===\n"
            # Limit text to prevent token overflow
            context += story_text[:6000]

            response = self.llm.chat(
                messages=[
                    {
                        "role": "system",
                        "content": COMIC_COMPILER_PROMPT
                    },
                    {
                        "role": "user",
                        "content": f"Create exactly 6 manga panels from this story. Output ONLY a JSON array.\n\n{context}"
                    }
                ],
                temperature=0.3,
                max_tokens=3000
            )
            raw_output = response
            
            # Clean up markdown formatting
            # Remove ```json ... ``` wrapper if present
            cleaned = re.sub(r'```(?:json)?\s*', '', raw_output)
            cleaned = cleaned.strip()
            
            # Extract JSON array
            match = re.search(r'\[.*\]', cleaned, re.DOTALL)
            if match:
                cleaned = match.group(0)
                
            script_data = json.loads(cleaned, strict=False)
            
            # Validate and ensure exactly 6 panels max
            if not isinstance(script_data, list):
                raise ValueError("Output is not a JSON array")
            
            # Cap at 6 panels
            script_data = script_data[:6]
            
            # Validate each panel has required fields
            validated = []
            for i, item in enumerate(script_data):
                validated.append({
                    "panel_index": item.get("panel_index", i + 1),
                    "image_prompt": item.get("image_prompt", "a manga scene, black and white, clean linework"),
                    "dialogue_text": item.get("dialogue_text", ""),
                    "layout_type": item.get("layout_type", "square")
                })
            
            return validated
            
        except Exception as e:
            print(f"Error parsing comic script: {e}")
            try:
                print(f"RAW OUTPUT WAS: {raw_output[:500]}")
            except:
                pass
            # Return 3 fallback panels instead of 1
            return [
                {"panel_index": 1, "image_prompt": "wide establishing shot of a scenic landscape, manga panel, clean ink linework, black and white, simple bold outlines, japanese manga style, high contrast", "dialogue_text": "Cau chuyen bat dau...", "layout_type": "wide"},
                {"panel_index": 2, "image_prompt": "medium shot of a young character looking determined, manga panel, clean ink linework, black and white, expressive cartoon face, japanese manga style", "dialogue_text": "Hay bat dau cuoc phieu luu!", "layout_type": "square"},
                {"panel_index": 3, "image_prompt": "dramatic low angle shot of characters walking towards horizon, manga panel, clean ink linework, black and white, simple bold outlines, high contrast", "dialogue_text": "Va hanh trinh bat dau tu day...", "layout_type": "wide"},
            ]
