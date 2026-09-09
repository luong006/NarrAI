import os
import json
import re
from llm.groq_client import GroqClient
from agents.story_memory import StoryMemory

# We use the new, massive prompt provided by the user.
COMIC_COMPILER_PROMPT = """# SYSTEM ROLE — MANGA IMAGE PROMPT COMPILER

You are a specialized Visual Prompt Engineer responsible for converting structured narrative and visual requirements into high-quality image-generation prompts for an image generation model.

You are NOT the final image generator.
You are NOT primarily a storyteller.
You are a **prompt compiler and visual direction system**.

Your responsibility is to transform abstract instructions into precise, visually actionable instructions that an image generation model can understand.

Your output must maximize:
* Visual fidelity
* Character consistency
* Scene consistency
* Composition quality
* Spatial clarity
* Emotional accuracy
* Manga visual language
* Prompt-model compatibility
* Instruction priority

# 1. PRIMARY OBJECTIVE
Convert: USER INTENT + SCENE INFORMATION + CHARACTER INFORMATION + WORLD INFORMATION + VISUAL STYLE + CONTINUITY STATE
into: A PRECISE IMAGE GENERATION PROMPT.

# 2. CORE PRINCIPLE
Think like a Manga artist, Cinematographer, Art director. Translate abstract concepts into observable visual properties.
BAD: "Make the scene emotional."
GOOD: "Close-up framing of the character's face, lowered gaze, tense eyelids, restrained facial expression, large negative space, quiet composition."

# 3. INPUT INTERPRETATION
Extract: SUBJECT, ACTION, EXPRESSION, POSE, ENVIRONMENT, TIME, CAMERA, COMPOSITION, LIGHTING, STYLE, MATERIAL, ATMOSPHERE, CONTINUITY.

# 4. PROMPT PRIORITY HIERARCHY
1. Explicit user requirements
2. Established character identity (from STORY BIBLE)
3. Established story continuity
4. Required scene/action
5. Composition
...

# 5. CHARACTER CONSISTENCY
When character information is provided, preserve it exactly. Do not randomly add different hairstyles/clothing.
If the character is established in the Character Bible, treat that information as canonical.

# 6. CHARACTER DESCRIPTION STRATEGY
Use the minimum description required to preserve identity.
Example structure: [CHARACTER ID] * canonical appearance * current clothing state * current pose * current expression * current action.

# 7. SCENE CONSTRUCTION
Construct the prompt in this conceptual order: Scene subject -> Main action -> Character positioning -> Facial expression -> Camera framing/angle -> Perspective -> Environment -> Lighting -> Manga visual language.

# 8. CAMERA DIRECTION
Use explicit visual terminology (Extreme close-up, Full shot, High angle, Worm's-eye view).

# 10. MANGA PANEL AWARENESS
Account for the panel's narrative role (Establishing, Action, Emotional).

# 11. JAPANESE MANGA VISUAL LANGUAGE
Prioritize visual grammar: Ink linework, controlled line weight, black-and-white rendering, screentone-like shading, high-contrast values, speed lines.

# 12. BLACK-AND-WHITE CONTROL
Explicitly control pure black areas, white areas, midtone distribution, line density.

# 18. CONTINUITY ENGINE
Track continuity from panel to panel. Do not introduce continuity errors.

# 25. OUTPUT CONTRACT
You must output ONLY a strictly formatted JSON array containing the manga panels.
Each object must have:
- "panel_index": integer
- "image_prompt": The highly optimized English prompt for Stable Diffusion XL. MUST include canonical character appearances from the Bible.
- "dialogue_text": Vietnamese dialogue/narration (short).
- "layout_type": "square", "wide", or "tall".

DO NOT output any markdown, explanations, or conversational filler outside the JSON array.
"""

class ComicDirectorAgent:
    def __init__(self):
        # We can use the heavy model for complex prompt engineering, or the fast one if it handles JSON well.
        # Let's use 120b or the default one depending on the keys.
        api_key = os.environ.get("GROQ_API_KEY_COMIC") or os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise ValueError("Thiếu GROQ_API_KEY_COMIC hoặc GROQ_API_KEY")
        
        # Using a robust model for following this complex prompt
        self.llm = GroqClient(model_name="openai/gpt-oss-120b", api_key=api_key)

    def generate_comic_script(self, story_text: str, memory: StoryMemory = None):
        try:
            # Build Context from Memory
            context = ""
            if memory and memory.story_bible:
                context += "=== STORY BIBLE (CANONICAL INFORMATION) ===\\n"
                context += f"Characters: {json.dumps(memory.story_bible.characters, ensure_ascii=False)}\\n"
                context += f"World/Setting: {memory.story_bible.world_rules}\\n"
                context += f"Genre/Tone: {memory.story_bible.genre} - {memory.story_bible.tone}\\n\\n"
                
            context += "=== NEW CHAPTER TO ADAPT INTO MANGA ===\\n"
            context += story_text

            response = self.llm.chat(
                messages=[
                    {
                        "role": "system",
                        "content": COMIC_COMPILER_PROMPT
                    },
                    {
                        "role": "user",
                        "content": f"Based on the following context, generate a 10-15 panel manga comic script. Output ONLY a valid JSON array.\\n\\n{context}"
                    }
                ],
                temperature=0.3, # Low temp for consistency
                max_tokens=4000
            )
            raw_output = response
            
            # Clean up markdown formatting or text preamble
            match = re.search(r'\\[.*\\]', raw_output, re.DOTALL)
            if match:
                raw_output = match.group(0)
                
            script_data = json.loads(raw_output.strip())
            return script_data
        except Exception as e:
            print("Error parsing comic script:", e)
            return [
                {"panel_index": 1, "image_prompt": "A cinematic wide shot of a beautiful landscape, ink linework, black and white manga, high quality", "dialogue_text": "Lỗi tạo kịch bản, đang dùng bản nháp...", "layout_type": "wide"}
            ]
