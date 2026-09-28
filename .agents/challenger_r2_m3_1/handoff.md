# Handoff Report: Milestone 3 Empirical Adversarial Challenge

- **Agent**: `challenger_r2_m3_1` (Critic & Specialist)
- **Target**: Milestone 3 (R3: Text-to-Image Sync & Manga Hallucination Elimination)
- **Working Directory**: `e:\NarrAI\.agents\challenger_r2_m3_1`
- **Workspace**: `e:\NarrAI`
- **Date**: 2026-09-20T18:25:00Z
- **Verdict**: **REQUEST_CHANGES**

---

## 1. Observation

Direct empirical code inspection and regex trace of `backend/agents/comic_agent.py`, `backend/services/cloudflare_ai.py`, and `backend/tests/test_comic_modern_school_sync.py`:

### Observation 1.1: Regex Edge Cases in `sanitize_spatial_prompt()`
1. **Dangling Modifier Leakage ("ancient palace")** (`comic_agent.py:180-185`):
   ```python
   clean = re.sub(
       rf'\b(?:on|in|along|across|down|near|beside|by)?\s*(?:the|a|an)?\s*(?:busy|moving|crowded|noisy|outdoor|distant|speeding|passing)?\s*\b{re.escape(token)}s?\b',
       '',
       clean,
       flags=re.IGNORECASE
   )
   ```
   - For `token = "palace"` on input `"student standing in an ancient palace"`, `"ancient"` is **not** in the modifier whitelist `(?:busy|moving|crowded|noisy|outdoor|distant|speeding|passing)`.
   - The regex matches only `"palace"`. Resulting output: `"student standing in an ancient"`. `"ancient"` is left as dangling garbage.
2. **Missing "sword" in Spatial Forbidden Tokens** (`comic_agent.py:132-135`):
   - `SPATIAL_ENCLOSURES["classroom"]["forbidden_spatial_tokens"]` contains:
     `["street", "road", "alley", "highway", "traffic", "car", "bus", "store", "shop", "market", "forest", "park", "palace", "temple", "castle", "dungeon", "battlefield"]`.
   - `"sword"`, `"blade"`, and `"weapon"` are completely absent from `forbidden_spatial_tokens`. On input `"student holding a wooden sword in classroom"`, `sanitize_spatial_prompt()` leaves `"sword"` completely untouched. (It is present only in diffusion negative prompts in `cloudflare_ai.py`).
3. **Punctuation Artifacts (Consecutive Orphaned Commas)** (`comic_agent.py:188-191`):
   - On input `"girl at desk, on the busy street, reading notes"`, after `"on the busy street"` is removed, the text becomes `"girl at desk, , reading notes"`.
   - Lines 188-191 only perform `re.sub(r'\s{2,}', ' ', clean).strip(' ,.-')` which collapses spaces, but fails to collapse `,\s*,`. The double comma is forwarded directly to the diffusion prompt.
4. **Missing Common Prepositions**:
   - The preposition list `(?:on|in|along|across|down|near|beside|by)` omits `at`, `to`, `through`, `outside`, `into`.
   - On input `"student looking at the speeding car"`, `"speeding car"` is removed, leaving `"student looking at the"`.
5. **Irregular Plural Mismatch ("buses")**:
   - Pattern uses `\b{token}s?\b`. For `token = "bus"`, it matches `bus` or `buss`, failing on English plural `"buses"`. `"school buses parked outside"` leaves `"buses"`.

### Observation 1.2: Negation Blindness & Semantic Action Hallucinations in `extract_action_from_prose()`
1. **Negation Blindness (`comic_agent.py:204, 251-254`)**:
   - Pattern 2: `r'(?:nhìn|ngắm|hướng mắt|dõi theo)\s*(?:ra|qua)?\s*(?:cửa sổ|bầu trời|mây)'`.
   - On input `"An tuyệt đối không nhìn ra cửa sổ mà chăm chú nhìn lên bảng đen"`, the regex lacks negative lookbehind or negation checking.
   - It matches `"nhìn ra cửa sổ"` and returns:
     `'sitting beside the large classroom window, cheek resting on palm, gazing pensively through the glass at sky'`.
   - This directly inverts author intent and forces an action the text explicitly denies.
2. **Reprimands and Prohibitions in Dialogue**:
   - On dialogue: `'Thầy giáo quát: "Các em đừng có quay sang nói chuyện nữa!"'`.
   - Pattern 3 matches `"quay sang nói chuyện"` and injects:
     `'turning slightly in chair toward desk mate, gentle warm smile, engaging direct eye contact'`.
3. **Overly Broad Trigger on `thở dài` (`comic_agent.py:228`)**:
   - Pattern 6: `r'(?:thở dài|gục đầu|úp mặt|nằm gục)\s*(?:xuống)?\s*(?:bàn)?'`.
   - Because `(?:xuống)?\s*(?:bàn)?` are both optional, any standalone occurrence of `"thở dài"` (sigh) triggers:
     `'resting head down on folded arms upon wooden desk, soft melancholic expression, delicate hair framing face'`.
   - On prose: `"Thầy giáo đứng trước lớp thở dài một tiếng"`, the standing teacher is depicted as resting their head on the desk with delicate hair.
4. **Overly Broad Trigger on `cúi đầu` (`comic_agent.py:198`)**:
   - Pattern 1 ends with `|\b(?:cúi đầu|cặm cụi)\b`.
   - On greeting or apologetic bow: `"An cúi đầu lễ phép chào cô giáo"`, the system extracts:
     `'sitting at wooden student desk, head gently bowed down, writing attentively in a notebook with pen'`.
5. **Mental State Trigger on `kinh ngạc` (`comic_agent.py:216`)**:
   - Pattern 4 ends with `|kinh ngạc)`.
   - Internal feeling: `"Một thoáng kinh ngạc lướt qua suy nghĩ của An"` forces:
     `'standing up abruptly from desk, hands braced against wooden desktop, wide eyes with sudden realization'`.

### Observation 1.3: Token Budget Overrun & Semantic Truncation Blindness
1. **Assembled Prompt Length (`comic_agent.py:787-809`)**:
   - `STYLE_PREFIX`: 22 words (~29 CLIP tokens)
   - Character DNA: ~43 words (~54 CLIP tokens)
   - Scene Prompt: ~21 words (~26 CLIP tokens)
   - Action Gesture: ~17 words (~22 CLIP tokens)
   - Setting Anchor: ~33 words (~44 CLIP tokens)
   - `STYLE_SUFFIX`: 32 words (~41 CLIP tokens)
   - Total assembled prompt length: **~168 words / ~216 CLIP BPE tokens**.
2. **CLIP ViT-L/14 Context Window**:
   - Stable Diffusion XL and base CLIP models enforce a hard 77-token ceiling (75 effective user tokens).
   - In `_validate_panels`, the setting anchor (`"setting: modern Japanese high school classroom..."`) is placed at token index ~120+, and `STYLE_SUFFIX` at token index ~175+.
   - **Both the setting anchor and the action gesture fall beyond token 77**. Standard CLIP tokenizers truncate tokens > 77, meaning the diffusion model's cross-attention never attends to the spatial setting anchor or physical action gesture!
3. **Pollinations Fallback Hard Truncation (`cloudflare_ai.py:153`)**:
   - `bw_prompt = f"black and white manga drawing, monochrome ink on white paper, Japanese manga style, {prompt[:300]}, screentone, no color"`
   - `STYLE_PREFIX` consumes 162 characters. `prompt[:300]` leaves only 138 characters, cutting character DNA mid-word and completely omitting the setting anchor and action gesture.

---

## 2. Logic Chain

1. **Premise 1 (R3 Core Requirement)**: Milestone 3 requires "100% Panel Spatial Enclosure Anchoring (Zero drift)" and "Loại bỏ ảo giác khung tranh Manga (bám sát trực tiếp hành động, cử chỉ, trang phục và bối cảnh)".
2. **Inference 1 (Negation Hallucination)**: Because `ACTION_GESTURE_MAPPINGS` relies on regex keyword matching without checking for negation particles (`không`, `chẳng`, `chưa`, `đừng`, `cấm`), negated actions (e.g. `"không nhìn ra cửa sổ"`) and reprimands (`"đừng quay sang nói chuyện"`) produce the exact opposite physical gesture. This introduces direct visual hallucinations into panels.
3. **Inference 2 (Semantic Truncation Blindness)**: Placing `STYLE_PREFIX` (~29 tokens) + Character DNA (~54 tokens) at the start of the prompt pushes the Setting Anchor and Action Description past token index 77. Because diffusion text encoders truncate attention at 77 tokens, the Setting Anchor is dropped before diffusion latent generation. Thus, the guarantee of "100% Panel Spatial Enclosure Anchoring" is technically defeated in diffusion inference unless the prompt components are prioritized within the budget.
4. **Inference 3 (Sanitizer Leakage & Syntax Degradation)**: `sanitize_spatial_prompt()` leaves dangling words for "ancient palace" ("ancient"), skips "sword", misses prepositions (`at`, `through`), and leaves orphaned double commas (`, ,`). While these do not crash the service, they pollute the visual embedding and degrade lineart quality.

---

## 3. Caveats

- **API Tokenizer Behavior**: While standard CLIP truncates at 77 tokens, some advanced SDXL implementations use dual text encoders (CLIP ViT-L + OpenCLIP ViT-bigG) or chunked prompt weighting (e.g. CompVis / AUTOMATIC1111 token chunking). However, Cloudflare Workers AI Text-to-Image endpoints (`@cf/bytedance/stable-diffusion-xl-lightning`) run standard Hugging Face diffusers pipelines that apply `max_length=77, truncation=True` by default.
- **Intent of Wuxia Purge**: The worker successfully purged historical wuxia tokens from `DNA_EXTRACTOR_PROMPT` and `cloudflare_ai.py` master negative prompts, which is a major positive improvement.
- **Compilation**: Code compiles cleanly via `py_compile`.

---

## 4. Conclusion & Verdict

**Verdict: REQUEST_CHANGES**

While the worker successfully implemented the structural components of Milestone 3, empirical testing revealed high-impact failure modes that violate Milestone 3's zero-hallucination requirement:
1. **Critical**: Negation blindness and overly broad regexes in `extract_action_from_prose()` that inject incorrect physical gestures on negated actions, dialogue reprimands, standalone sighs, and greeting bows.
2. **Critical**: Prompt length layout placing setting anchors and actions beyond CLIP's 77-token attention horizon.
3. **Moderate**: Regex sanitization edge cases in `sanitize_spatial_prompt()` (dangling "ancient", missing "sword" in spatial forbidden list, double commas, and irregular plural `buses`).
4. **Moderate**: Pollinations fallback slicing at 300 characters mid-word and dropping setting anchors.

### Concrete Actionable Remediations Required:
1. **Negation-Aware Action Extractor (`comic_agent.py`)**:
   - Add a negation guard before matching action patterns: if preceding 1-4 words contain `không`, `chẳng`, `chưa`, `đừng`, `cấm`, `ngừng`, skip the pattern.
   - Tighten Pattern 6 (`thở dài`): require `thở dài` to be paired with `gục đầu` or `bàn` before forcing head-down desk pose.
   - Tighten Pattern 1 (`cúi đầu`): require `cúi đầu` to be paired with `viết` or `bài` (remove standalone `|\b(?:cúi đầu|cặm cụi)\b`).
   - Tighten Pattern 4 (`kinh ngạc`): remove standalone `|kinh ngạc)`.
2. **Prompt Budget Compacting & Reordering (`comic_agent.py`)**:
   - Compact `STYLE_PREFIX` from 22 words to ~10 high-weight tokens (e.g., `"monochrome manga, Japanese school manga art style, crisp ink lineart, "`).
   - Position the Core Action and Setting Anchor **immediately after the character name / short DNA**, before lengthy clothing details, ensuring action and setting are within the 77-token window.
3. **Spatial Sanitizer Fixes (`comic_agent.py`)**:
   - Add `"sword"`, `"blade"` to `SPATIAL_ENCLOSURES["classroom"]["forbidden_spatial_tokens"]`.
   - Add `"ancient"`, `"stone"`, `"old"` to modifier list.
   - Add `"at"`, `"to"`, `"through"` to preposition list.
   - Handle irregular plural `(?:es|s)?`.
   - Add `clean = re.sub(r'[,.\s]*,[,.\s]*', ', ', clean)` to collapse double commas.
4. **Pollinations Fallback Clean Slicing (`cloudflare_ai.py`)**:
   - Slice at sentence/comma boundaries instead of hard `[:300]`.

---

## 5. Verification Method

To independently verify these findings, run the newly added adversarial test suite:

```bash
python -m unittest backend/tests/test_challenger_r2_m3_1_adversarial.py -v
```

### Inspect Test File:
- `backend/tests/test_challenger_r2_m3_1_adversarial.py`:
  - `test_flaw_ancient_palace_leaves_dangling_ancient`
  - `test_flaw_sword_not_in_spatial_forbidden_tokens`
  - `test_flaw_internal_double_commas_not_collapsed`
  - `test_flaw_plural_buses_not_matched`
  - `test_flaw_negation_hallucination_window`
  - `test_flaw_dialogue_reprimand_triggers_hallucinated_smile`
  - `test_flaw_standalone_sigh_forces_head_on_desk`
  - `test_flaw_greeting_bow_forces_writing_notebook`
  - `test_flaw_internal_emotion_kinh_ngac_forces_desktop_slam`
  - `test_token_budget_exceeds_clip_77_tokens`
  - `test_pollinations_fallback_300_char_hard_truncation`
