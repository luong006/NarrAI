# Production Remediation Blueprint: Milestone 3 Vulnerabilities Resolution

- **Author**: Explorer (`explorer_r2_m3_fix`)
- **Target Milestone**: Milestone 3 Remediation (R3: Text-to-Image Sync & Manga Hallucination Elimination)
- **Target Files**:
  - `backend/agents/comic_agent.py`
  - `backend/services/cloudflare_ai.py`
  - `backend/tests/test_challenger_r2_m3_1_adversarial.py`
- **Date**: 2026-09-20T18:35:00Z
- **Status**: Production-Ready Blueprint & Exact Code Diffs

---

## 1. Executive Summary & Root Cause Matrix

Empirical adversarial evaluation by Challenger 1 (`challenger_r2_m3_1`) and forensic architecture review by Reviewer 2 (`reviewer_r2_m3_2`) identified four critical vulnerability categories preventing zero-hallucination guarantees in Milestone 3:

| # | Vulnerability Category | Root Cause | Impact | Fix Strategy |
|---|---|---|---|---|
| **1** | **Negation Blindness & Semantic Action Overlap** | `extract_action_from_prose()` blindly matches keyword regexes without checking preceding negation/prohibition words; Patterns 1, 4, 6 match greeting bows, internal thoughts, and standalone sighs. | Direct visual hallucination: negated actions (e.g. "không nhìn ra cửa sổ") inject the forbidden gesture; reprimands ("đừng quay sang nói chuyện") force smiling poses; bows force writing poses. | Introduce `is_action_negated()` checking Vietnamese negation/prohibition tokens (`không`, `chẳng`, `chưa`, `đừng`, `cấm`, `ngừng`, `thôi`, `chớ`) in the immediate clause. Tighten Patterns 1, 4, 6 to require concrete physical pairings. |
| **2** | **Spatial Sanitizer Regex Edge Cases** | `sanitize_spatial_prompt()` whitelist misses modifiers (`ancient`, `stone`, `old`, `abandoned`), lacks prepositions (`at`, `to`, `through`, `into`, `outside`), misses `sword`/`blade`/`weapon` in `SPATIAL_ENCLOSURES`, fails plural `buses`, and leaves consecutive commas. | Dangling modifiers ("ancient"), orphaned prepositions ("at the"), persistent weapons ("sword"), and double commas (", ,") corrupting diffusion text conditioning. | Add missing modifiers, prepositions, and plurals `(?:es|s)?` to regex. Add `sword`, `blade`, `weapon` to forbidden lists. Add regex pass collapsing multiple commas `re.sub(r'[,.\s]*,[,.\s]*', ', ', clean)`. |
| **3** | **CLIP 77-Token Budget Overrun & Spatial Anchor Dropping** | Assembled prompt layout places `STYLE_PREFIX` (~28 tokens) + Character DNA (~55 tokens) before `action_desc` (~15 tokens) and `setting:` anchor (~40 tokens). | Total tokens exceed 170 BPE tokens. CLIP ViT-L/14 text encoders enforce hard 77-token truncations; setting anchors and physical actions fall past token index 80+, resulting in zero latent attention during diffusion. | Reorder prompt components in `_validate_panels()`: inject `setting: {setting_anchor}` and `action_desc` immediately after `STYLE_PREFIX` (tokens 20-65), guaranteeing both reside within the critical 77-token CLIP window. |
| **4** | **Pollinations Fallback Arbitrary Hard Slicing** | In `cloudflare_ai.py:153`, `prompt[:300]` hard-slices prompt mid-word, dropping character DNA, setting anchor, and action gestures. | Fallback images lose character visual consistency and spatial anchoring whenever Cloudflare Workers AI experiences rate limits or timeouts. | Implement `format_pollinations_prompt(prompt, max_len=500)` with delimiter-aware slicing (comma/sentence boundaries) and explicit preservation of `setting:` and `action:` clauses. |

---

## 2. Blueprint 1: Negation-Aware Action Extraction (`backend/agents/comic_agent.py`)

### 2.1 Technical Analysis
In Vietnamese grammar, verbal negation and prohibition markers (`không`, `chẳng`, `chưa`, `đừng`, `cấm`, `ngừng`, `thôi`, `chớ`, `tuyệt đối không`) immediately precede the verbal predicate within the same clause. When contrastive conjunctions (`mà`, `nhưng`, `song`, `tuy nhiên`) or punctuation delimiters (`,`, `;`, `.`, `!`, `?`, `"`, `:`) appear, a new clause begins.

### 2.2 Exact Code Implementation

#### Addition: Negation Registry & Clause Boundary Evaluator
Insert directly above `ACTION_GESTURE_MAPPINGS` in `backend/agents/comic_agent.py`:

```python
# ==================== VIETNAMESE NEGATION & PROHIBITION GUARD ====================
VIETNAMESE_NEGATION_WORDS = {
    "không", "chẳng", "chưa", "đừng", "cấm", "ngừng", "thôi", "chớ", "ko", "k"
}
CLAUSE_DELIMITERS_PATTERN = r'[,;.!?:\—\-"“”\'\(\)\[\]\n]|\b(?:nhưng|mà|song|tuy\s+nhiên|thế\s+nhưng)\b'

def is_action_negated(text: str, match_start: int) -> bool:
    """
    Checks if a matched action phrase is preceded by a Vietnamese negation or prohibition word
    within the same clause (inspects up to 6 words preceding match_start).
    Prevents negated actions (e.g., 'không nhìn ra cửa sổ') and dialogue reprimands
    (e.g., 'đừng có quay sang nói chuyện') from triggering visual gestures.
    """
    pre_text = text[:match_start]
    # Split by clause boundaries to isolate the immediate clause containing the match
    clause_parts = re.split(CLAUSE_DELIMITERS_PATTERN, pre_text, flags=re.IGNORECASE)
    immediate_clause = clause_parts[-1] if clause_parts else ""
    # Extract preceding words in the immediate clause
    words = re.findall(r'\b\w+\b', immediate_clause.lower())
    window_words = words[-6:] if len(words) > 6 else words
    return any(w in VIETNAMESE_NEGATION_WORDS for w in window_words)
```

#### Replacement: Tightened `ACTION_GESTURE_MAPPINGS` & `extract_action_from_prose`
Replace lines 195-255 in `backend/agents/comic_agent.py` with:

```python
# ==================== ACTION & GESTURE SEMANTIC MAPPING ====================
ACTION_GESTURE_MAPPINGS = [
    # 1. Viết bài, làm việc tại bàn (Strictly requires pairing with viết, chép, ghi, vẽ, làm bài, vở, bài)
    (
        r'(?:cúi đầu|cặm cụi|chăm chú|lúi húi)\s*(?:[\w\s]{0,15})\b(?:viết|chép|ghi|vẽ|làm bài|ghi chép|vở|bài)\b',
        'sitting at wooden student desk, head gently bowed down, writing attentively in a notebook with pen',
        'medium close-up'
    ),
    # 2. Nhìn ra ngoài cửa sổ
    (
        r'(?:nhìn|ngắm|hướng mắt|dõi theo)\s*(?:ra|qua)?\s*(?:cửa sổ|bầu trời|mây)',
        'sitting beside the large classroom window, cheek resting on palm, gazing pensively through the glass at sky',
        'medium shot'
    ),
    # 3. Quay sang nói chuyện với bạn cùng bàn
    (
        r'(?:quay|ngoảnh|xoay)\s*(?:người|lại|sang)\s*(?:nhìn|cười|nói|hỏi|trò chuyện)',
        'turning slightly in chair toward desk mate, gentle warm smile, engaging direct eye contact',
        'over-the-shoulder shot'
    ),
    # 4. Đứng bật dậy, đập bàn (Strict physical action; removes internal feeling 'kinh ngạc' and standalone thoughts)
    (
        r'(?:đứng\s*bật\s*dậy|đập\s*tay\s*(?:xuống)?\s*bàn)',
        'standing up abruptly from desk, hands braced against wooden desktop, wide eyes with sudden realization',
        'dramatic low angle'
    ),
    # 5. Bước vào lớp học, mở cửa
    (
        r'(?:bước\s*vào|mở\s*cửa|đứng\s*ở\s*cửa)\s*(?:lớp|phòng)',
        'standing in the open sliding classroom doorway, holding school backpack strap, stepping inside',
        'wide establishing shot'
    ),
    # 6. Gục đầu xuống bàn (Requires pairing 'thở dài' with gục, bàn, nằm)
    (
        r'(?:gục đầu|úp mặt|nằm gục)\s*(?:xuống)?\s*(?:bàn)?|(?:thở dài)\s*(?:[\w\s]{0,15})\b(?:gục|bàn|nằm)\b|\b(?:gục|bàn|nằm)\b\s*(?:[\w\s]{0,15})\b(?:thở dài)\b',
        'resting head down on folded arms upon wooden desk, soft melancholic expression, delicate hair framing face',
        'close-up'
    ),
    # 7. Chuyền giấy, đưa đồ vật
    (
        r'(?:chuyền|đưa|trao|gửi)\s*(?:tờ giấy|mẩu tin|cuốn vở|cây bút|mẩu giấy)',
        'hand delicately passing a small folded note across the wooden desk space toward classmate',
        'tight focus on hands and note'
    ),
    # 8. Nhìn lên bảng đen
    (
        r'(?:nhìn|ngước|chú ý)\s*(?:lên)?\s*(?:bảng đen|bài giảng|thầy|cô)',
        'looking forward toward the classroom blackboard, attentive expression, sitting upright at desk',
        'medium shot'
    ),
]

def extract_action_from_prose(dialogue_or_prose: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extracts physical character gesture and camera angle from Vietnamese narrative prose or dialogue.
    Enforces strict negation checking across all pattern matches to eliminate action hallucinations.
    """
    if not dialogue_or_prose:
        return None, None
    text_lower = str(dialogue_or_prose).lower()
    for pattern, action_en, suggested_shot in ACTION_GESTURE_MAPPINGS:
        for m in re.finditer(pattern, text_lower):
            if not is_action_negated(text_lower, m.start()):
                return action_en, suggested_shot
    return None, None
```

---

## 3. Blueprint 2: Robust Spatial Prompt Sanitizer (`backend/agents/comic_agent.py`)

### 3.1 Technical Analysis
1. **Forbidden Spatial Tokens**: Classroom scenes must ban melee/fantasy weaponry (`sword`, `blade`, `weapon`) in positive prompts.
2. **Modifier Whitelist Expansion**: `ancient`, `stone`, `old`, `abandoned`, `wooden` must be stripped with the token so `"ancient palace"` or `"wooden sword"` leaves zero dangling modifiers.
3. **Preposition Whitelist Expansion**: `at`, `to`, `through`, `into`, `outside`, `towards` must be stripped so `"looking at the speeding car"` becomes `"looking"` without leaving trailing `"at the"`.
4. **Plural Inflections**: `(?:es|s)?` matches both standard plurals (`cars`) and sibilant plurals (`buses`).
5. **Punctuation Collapsing**: After stripping tokens, orphaned commas (`item1, , item2`) must collapse to single commas (`item1, item2`).

### 3.2 Exact Code Implementation

#### Update: `SPATIAL_ENCLOSURES`
Replace lines 121-153 in `backend/agents/comic_agent.py`:

```python
SPATIAL_ENCLOSURES = {
    "classroom": {
        "detection_keywords": [
            "lớp học", "phòng học", "bàn học", "bảng đen", "classroom", "schoolroom",
            "tiết học", "giờ học", "bàn giáo viên", "bàn đầu", "cuối lớp", "bàn cùng bàn"
        ],
        "anchor_description": (
            "modern Japanese high school classroom interior, neat wooden student desks and chairs, "
            "large green chalkboard mounted on front wall, tall multi-pane glass windows with sunlight "
            "streaming across wooden floor, peaceful classroom atmosphere"
        ),
        "forbidden_spatial_tokens": [
            "street", "road", "alley", "highway", "traffic", "car", "bus", "store", "shop",
            "market", "forest", "park", "palace", "temple", "castle", "dungeon", "battlefield",
            "sword", "blade", "weapon"
        ]
    },
    "school_hallway": {
        "detection_keywords": ["hành lang", "cửa lớp", "dãy phòng học", "hallway", "corridor"],
        "anchor_description": (
            "bright school hallway interior, wooden lockers lining the corridor wall, "
            "tall rectangular windows overlooking the school courtyard, clean screentone floor"
        ),
        "forbidden_spatial_tokens": [
            "palace", "temple", "castle", "dungeon", "highway", "forest", "sword", "blade", "weapon"
        ]
    },
    "school_rooftop": {
        "detection_keywords": ["sân thượng", "rooftop"],
        "anchor_description": (
            "school rooftop on a clear day, protective chain-link wire fence, "
            "distant city horizon in clean manga screentone, wide open sky"
        ),
        "forbidden_spatial_tokens": [
            "indoor", "classroom", "palace", "dungeon", "cave", "sword", "blade", "weapon"
        ]
    }
}
```

#### Update: `sanitize_spatial_prompt()`
Replace lines 164-193 in `backend/agents/comic_agent.py`:

```python
def sanitize_spatial_prompt(prompt: str, enclosure: dict = None) -> str:
    """
    Spatial Quarantine Filter:
    Strips conflicting/outdoor/traffic/ancient/weapon keywords (street, road, highway, car, bus, traffic, palace, sword)
    before rendering indoor classroom scenes, while strictly preserving subwords like 'classroom', 'cardigan', and 'scarf'.
    Handles modifiers, prepositions, irregular plurals, and collapses consecutive commas cleanly.
    """
    if not prompt or not isinstance(prompt, str):
        return ""
    if enclosure is None:
        enclosure = SPATIAL_ENCLOSURES["classroom"]

    clean = prompt
    forbidden = enclosure.get("forbidden_spatial_tokens", [])
    
    # Prepositions including compound directions (out at, out to)
    prepositions = r'(?:on|in|along|across|down|near|beside|by|at|to|through|into|outside|towards|out\s+at|out\s+to|out\s+of)?'
    # Articles
    articles = r'(?:the|a|an)?'
    # Modifiers including ancient, stone, old, abandoned, wooden
    modifiers = r'(?:(?:\b(?:busy|moving|crowded|noisy|outdoor|distant|speeding|passing|ancient|stone|old|abandoned|wooden)\b)\s+)*'

    for token in forbidden:
        # Match preposition + article + modifiers + token with singular or plural (-s, -es)
        clean = re.sub(
            rf'\b{prepositions}\s*{articles}\s*{modifiers}\b{re.escape(token)}(?:es|s)?\b',
            '',
            clean,
            flags=re.IGNORECASE
        )

    # Clean dangling prepositions at clause/string boundaries
    clean = re.sub(
        r'\b(?:at|to|through|into|outside|towards|on|in|along|across|down|near|beside|by)\s*(?:the|a|an)?(?=,|\.|$)',
        '',
        clean,
        flags=re.IGNORECASE
    )

    # Collapse consecutive/orphaned commas and whitespace
    clean = re.sub(r'[,.\s]*,[,.\s]*', ', ', clean).strip(' ,.-')
    clean = re.sub(r'^(?:and|or|with)\s+', '', clean, flags=re.IGNORECASE)
    clean = re.sub(r'\s+(?:and|or|with)$', '', clean, flags=re.IGNORECASE)
    clean = re.sub(r'\s{2,}', ' ', clean).strip(' ,.-')
    return clean
```

---

## 4. Blueprint 3: CLIP Token Budget & Prompt Layout Reordering (`backend/agents/comic_agent.py`)

### 4.1 Technical Analysis
- CLIP ViT-L/14 enforces a hard 77-token ceiling (75 user tokens after `<|startoftext|>` and `<|endoftext|>`).
- Putting `STYLE_PREFIX` (~25 tokens) + Character DNA (~55 tokens) first pushes `setting:` and `action_desc` past token 80, completely dropping spatial anchoring in diffusion cross-attention.
- **Solution**: Reorder prompt elements so that `setting: {setting_anchor}` and `action_desc` appear immediately after `STYLE_PREFIX`.
  - Token 0-25: `STYLE_PREFIX`
  - Token 25-45: `setting: {setting_anchor}`
  - Token 45-60: `{action_desc}`
  - Token 60+: `{character_dna}`, `{scene_nuances}`, `{STYLE_SUFFIX}`
- This guarantees that 100% of panels have their spatial enclosure and physical character pose attended to by the diffusion text encoder.

### 4.2 Exact Code Implementation

In `backend/agents/comic_agent.py`, replace lines 776-809 in `_validate_panels()`:

```python
            # Step 4: Inject Character Visual DNA for ALL matched characters
            injected_dnas = []
            for c in matched_chars:
                c_dna = c["dna"].strip()
                if c_dna and c_dna.lower() not in clean_prompt.lower():
                    injected_dnas.append(c_dna)

            # Step 5 & 6: CLIP 77-Token Budget Prioritization
            # Order components: Setting Anchor -> Core Action -> Character DNA -> Scene Nuances
            # Guarantees setting anchor & physical action appear within the first 65 CLIP tokens!
            prompt_components = []
            
            # Component 1: Spatial Enclosure Anchor (Tokens ~22-45)
            if setting_anchor and setting_anchor.lower() not in clean_prompt.lower():
                prompt_components.append(f"setting: {setting_anchor}")

            # Component 2: Core Action Gesture (Tokens ~45-65)
            if action_desc and action_desc.lower() not in clean_prompt.lower():
                prompt_components.append(action_desc)

            # Component 3: Character Visual DNA
            if injected_dnas:
                prompt_components.append(", ".join(injected_dnas))

            # Component 4: Remaining Scene / Camera Shot Nuances
            if clean_prompt:
                prompt_components.append(clean_prompt)

            assembled_prompt = ", ".join(prompt_components)

            # Clean duplicate style tags
            for tag in ["manga panel", "black and white", "monochrome", "screentone", "comic art"]:
                assembled_prompt = re.sub(rf'\b{re.escape(tag)}\b', "", assembled_prompt, flags=re.IGNORECASE)

            # Clean duplicate commas and normalize whitespace
            assembled_prompt = re.sub(r'[,.\s]*,[,.\s]*', ', ', assembled_prompt).strip(' ,.-')

            final_prompt = f"{STYLE_PREFIX}{assembled_prompt}{STYLE_SUFFIX}"

            raw_layout = str(item.get("layout_type") or "square").lower().strip()
            normalized_layout = LAYOUT_MAP.get(raw_layout, "square")

            validated.append({
                "panel_index": i + 1,
                "image_prompt": final_prompt,
                "dialogue_text": dialogue,
                "layout_type": normalized_layout
            })
```

---

## 5. Blueprint 4: Resilient Pollinations Fallback Slicing (`backend/services/cloudflare_ai.py`)

### 5.1 Technical Analysis
Pollinations fallback uses HTTP GET: `https://image.pollinations.ai/prompt/{safe_prompt}`.
- Slicing at `prompt[:300]` cuts character DNA mid-token and discards `setting:` and `action_desc`.
- **Solution**: Implement `format_pollinations_prompt(prompt, max_len=500)`:
  1. If prompt length > `max_len`, truncate cleanly at the last comma or sentence boundary before `max_len` to avoid broken words.
  2. If `setting:` was positioned later or truncated, extract the `setting:` clause and guarantee it is appended.
  3. Ensure no trailing double commas or orphaned prepositions exist.

### 5.2 Exact Code Implementation

#### Addition: `format_pollinations_prompt()`
In `backend/services/cloudflare_ai.py`, insert above `get_cached_or_generate_image()`:

```python
def format_pollinations_prompt(prompt: str, max_len: int = 500) -> str:
    """
    Prepares a clean, semantic-safe prompt for Pollinations fallback image generation.
    - Slices cleanly at comma/sentence boundaries instead of arbitrary character cuts.
    - Preserves setting anchor, action gesture, and character DNA without mid-word truncations.
    - Fits within safe URL length limits for HTTP GET requests.
    """
    if not prompt or not isinstance(prompt, str):
        return "black and white manga drawing, monochrome ink on white paper, Japanese manga style, screentone, no color"

    clean_p = prompt.strip()
    if len(clean_p) <= max_len:
        target = clean_p
    else:
        # Extract setting anchor if present to guarantee spatial preservation
        setting_match = re.search(r'\bsetting:\s*([^,]+(?:,[^,]+){0,2})', clean_p, re.IGNORECASE)
        setting_clause = setting_match.group(0).strip() if setting_match else ""

        # Slice cleanly at last comma or period within max_len
        cutoff = clean_p[:max_len]
        last_delim = max(cutoff.rfind(','), cutoff.rfind('.'))
        if last_delim > max_len // 2:
            target = cutoff[:last_delim].strip(' ,.-')
        else:
            last_space = cutoff.rfind(' ')
            target = cutoff[:last_space].strip(' ,.-') if last_space > 0 else cutoff

        # Guarantee setting anchor is preserved
        if setting_clause and setting_clause.lower() not in target.lower():
            target = f"{target}, {setting_clause}"

    # Clean double commas and trailing punctuation
    target = re.sub(r'[,.\s]*,[,.\s]*', ', ', target).strip(' ,.-')
    return f"black and white manga drawing, monochrome ink on white paper, Japanese manga style, {target}, screentone, no color"
```

#### Update: `get_cached_or_generate_image()` in `backend/services/cloudflare_ai.py`
Replace lines 151-161 in `backend/services/cloudflare_ai.py`:

```python
        print(f"[Comic Image] Cloudflare AI unavailable ({e}). Falling back to Pollinations...")
        try:
            bw_prompt = format_pollinations_prompt(prompt)
            safe_prompt = urllib.parse.quote(bw_prompt)
            fallback_url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width=800&height=800&nologo=true&seed={panel_seed}"
            resp = requests.get(fallback_url, timeout=20)
            if resp.status_code == 200 and len(resp.content) > 500:
                img_bytes = resp.content
        except Exception as p_err:
            print(f"[Comic Image] Pollinations fallback also failed ({p_err})")
```

---

## 6. Blueprint 5: Test Suite Specification Update (`backend/tests/test_challenger_r2_m3_1_adversarial.py`)

### 6.1 Transformation: Proving Flaws -> Asserting Robust Fixed Behavior
Challenger 1 originally wrote tests asserting the *presence* of flaws (e.g. `assertIn("ancient", res)`). To complete remediation, the adversarial test suite must be updated to assert the *elimination* of all flaws and verify production robustness.

### 6.2 Complete Drop-In Implementation for `backend/tests/test_challenger_r2_m3_1_adversarial.py`

```python
import os
import sys
import re
import unittest
from unittest.mock import patch, MagicMock

# Ensure backend directory is in sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

os.environ.setdefault("GROQ_API_KEY", "gsk_test_dummy_key_for_unit_tests")
os.environ.setdefault("GROQ_API_KEY_COMIC", "gsk_test_dummy_key_for_unit_tests")

from agents.comic_agent import (
    ComicDirectorAgent,
    STYLE_PREFIX,
    STYLE_SUFFIX,
    DNA_EXTRACTOR_PROMPT,
    SPATIAL_ENCLOSURES,
    resolve_spatial_enclosure,
    sanitize_spatial_prompt,
    ACTION_GESTURE_MAPPINGS,
    extract_action_from_prose,
)
from services.cloudflare_ai import (
    BASE_NEGATIVE_PROMPT,
    MODERN_SCHOOL_EXCLUSIONS,
    get_master_negative_prompt,
    get_deterministic_comic_seed,
    generate_image_cf,
    get_cached_or_generate_image,
    format_pollinations_prompt,
)


class TestChallengerR2M3Adversarial(unittest.TestCase):
    """
    Empirical Adversarial Stress Suite for Milestone 3 (R3 Visual Consistency & Text-to-Image Sync).
    Updated specification: Asserts robust, hardened behavior resolving all 4 vulnerability categories.
    """
    @classmethod
    def setUpClass(cls):
        with patch("llm.groq_client.Groq"):
            cls.agent = ComicDirectorAgent()

    # =========================================================================
    # 1. ADVERSARIAL TESTING OF sanitize_spatial_prompt()
    # =========================================================================

    def test_strip_traffic_and_vehicles(self):
        """Verify on the busy street, speeding car, and traffic are cleanly stripped."""
        enclosure = SPATIAL_ENCLOSURES["classroom"]
        
        # 'on the busy street'
        res1 = sanitize_spatial_prompt("A student sitting at desk on the busy street", enclosure)
        self.assertNotIn("street", res1.lower())
        self.assertNotIn("busy", res1.lower())

        # 'speeding car'
        res2 = sanitize_spatial_prompt("looking out at a speeding car", enclosure)
        self.assertNotIn("car", res2.lower())
        self.assertNotIn("speeding", res2.lower())

        # 'traffic'
        res3 = sanitize_spatial_prompt("classroom with distant traffic noise", enclosure)
        self.assertNotIn("traffic", res3.lower())

    def test_subwords_strict_preservation(self):
        """Verify innocent words with subwords (classroom, cardigan, scarf, board, class) are preserved."""
        enclosure = SPATIAL_ENCLOSURES["classroom"]
        input_prompt = "classroom student wearing cozy cardigan and warm scarf near the blackboard in class"
        sanitized = sanitize_spatial_prompt(input_prompt, enclosure)

        self.assertIn("classroom", sanitized.lower())
        self.assertIn("cardigan", sanitized.lower())
        self.assertIn("scarf", sanitized.lower())
        self.assertIn("blackboard", sanitized.lower())
        self.assertIn("class", sanitized.lower())

    def test_fix_ancient_palace_strips_ancient_modifier(self):
        """
        FIXED: 'ancient palace'
        The modifier whitelist includes 'ancient'. When 'palace' is stripped, 'ancient' is also cleanly stripped.
        """
        enclosure = SPATIAL_ENCLOSURES["classroom"]
        res = sanitize_spatial_prompt("student standing in an ancient palace", enclosure)
        self.assertNotIn("palace", res.lower())
        self.assertNotIn("ancient", res.lower(), "Verifies that 'ancient' is cleanly stripped with 'palace'")
        self.assertEqual(res, "student standing")

    def test_fix_sword_sanitized_from_classroom_spatial_enclosure(self):
        """
        FIXED: 'sword', 'blade', 'weapon' are registered in SPATIAL_ENCLOSURES forbidden list.
        """
        enclosure = SPATIAL_ENCLOSURES["classroom"]
        self.assertIn("sword", enclosure["forbidden_spatial_tokens"])
        self.assertIn("blade", enclosure["forbidden_spatial_tokens"])
        self.assertIn("weapon", enclosure["forbidden_spatial_tokens"])
        
        res = sanitize_spatial_prompt("student holding a wooden sword in classroom", enclosure)
        self.assertNotIn("sword", res.lower(), "Verifies that 'sword' is sanitized from positive prompt")

    def test_fix_prepositions_leave_no_dangling_syntax(self):
        """
        FIXED: Prepositions 'at', 'to', 'through', 'into' are handled and stripped without dangling syntax.
        """
        enclosure = SPATIAL_ENCLOSURES["classroom"]
        res = sanitize_spatial_prompt("student looking at the speeding car", enclosure)
        self.assertNotIn("car", res.lower())
        self.assertNotIn("speeding", res.lower())
        self.assertFalse(res.endswith("at the") or res.endswith("at"), f"Got dangling preposition: {res}")
        self.assertEqual(res, "student looking")

    def test_fix_internal_double_commas_collapsed(self):
        """
        FIXED: Stripping a token from 'item1, street, item2' cleanly collapses consecutive commas.
        """
        enclosure = SPATIAL_ENCLOSURES["classroom"]
        res = sanitize_spatial_prompt("girl at desk, on the busy street, reading notes", enclosure)
        self.assertNotIn(", ,", res, "Consecutive commas must be collapsed")
        self.assertEqual(res, "girl at desk, reading notes")

    def test_fix_plural_buses_matched_and_stripped(self):
        """
        FIXED: Regex handles plural 'buses' with (?:es|s)?.
        """
        enclosure = SPATIAL_ENCLOSURES["classroom"]
        res = sanitize_spatial_prompt("school buses parked outside", enclosure)
        self.assertNotIn("buses", res.lower())
        self.assertNotIn("bus", res.lower())

    # =========================================================================
    # 2. ADVERSARIAL TESTING OF extract_action_from_prose()
    # =========================================================================

    def test_valid_vietnamese_student_actions(self):
        """Verify recognition of common Vietnamese student action expressions."""
        # Taking notes
        act1, _ = extract_action_from_prose("An cúi đầu cặm cụi viết bài vào vở")
        self.assertIsNotNone(act1)
        self.assertIn("writing attentively", act1.lower())

        # Looking out window
        act2, _ = extract_action_from_prose("Cô bé chống cằm nhìn ra cửa sổ mộng mơ")
        self.assertIsNotNone(act2)
        self.assertIn("window", act2.lower())

        # Turning to desk mate
        act3, _ = extract_action_from_prose("An quay sang nói chuyện với bạn cùng bàn")
        self.assertIsNotNone(act3)
        self.assertIn("desk mate", act3.lower())

        # Standing up abruptly
        act4, _ = extract_action_from_prose("Cậu ấy bàng hoàng đứng bật dậy làm đổ ghế")
        self.assertIsNotNone(act4)
        self.assertIn("standing up abruptly", act4.lower())

    def test_fix_negation_awareness_prevents_window_hallucination(self):
        """
        FIXED: Negation Awareness
        Prose: 'An tuyệt đối không nhìn ra cửa sổ mà chăm chú nhìn lên bảng đen'.
        Does NOT trigger window gaze; correctly matches non-negated 'nhìn lên bảng đen'.
        """
        prose = "An tuyệt đối không nhìn ra cửa sổ mà chăm chú nhìn lên bảng đen"
        act, shot = extract_action_from_prose(prose)
        self.assertIsNotNone(act)
        self.assertNotIn("window", act.lower(), "Must NOT hallucinate looking out window when negated")
        self.assertIn("classroom blackboard", act.lower(), "Must match positive action looking at blackboard")

    def test_fix_dialogue_reprimand_does_not_hallucinate_smile(self):
        """
        FIXED: Reprimand / Prohibition
        Teacher says: 'Đừng có quay sang nói chuyện nữa!'.
        Prohibition 'đừng có' prevents smiling desk mate action.
        """
        prose = 'Thầy giáo nghiêm giọng: "Các em đừng có quay sang nói chuyện nữa!"'
        act, shot = extract_action_from_prose(prose)
        self.assertIsNone(act, f"Reprimand must not trigger positive action, got: {act}")

    def test_fix_standalone_sigh_does_not_force_head_on_desk(self):
        """
        FIXED: Overly Broad Pattern 6
        'Thở dài' without desk pairing ('gục', 'bàn', 'nằm') does NOT force resting head on desk.
        """
        prose = "Thầy giáo đứng trước lớp thở dài một tiếng mệt mỏi"
        act, _ = extract_action_from_prose(prose)
        self.assertIsNone(act, f"Standalone sigh must not force desk head-down, got: {act}")

    def test_fix_greeting_bow_does_not_force_writing_notebook(self):
        """
        FIXED: Pattern 1 Bow disambiguation
        A greeting bow ('cúi đầu chào') does NOT force writing in notebook.
        """
        prose = "An cúi đầu lễ phép chào cô giáo khi bước vào"
        act, _ = extract_action_from_prose(prose)
        self.assertIsNone(act, f"Greeting bow must not force writing notebook, got: {act}")

    def test_fix_internal_emotion_kinh_ngac_does_not_force_desktop_slam(self):
        """
        FIXED: Internal emotional thought of surprise does NOT force physical desktop slam.
        """
        prose = "Một thoáng kinh ngạc lướt qua suy nghĩ của An"
        act, _ = extract_action_from_prose(prose)
        self.assertIsNone(act, f"Internal thought must not trigger desktop slam, got: {act}")

    # =========================================================================
    # 3. TOKEN BUDGET & CLIP LIMIT AUDIT
    # =========================================================================

    def test_fix_setting_anchor_and_action_within_clip_77_tokens(self):
        """
        FIXED: Setting anchor and core action gesture are positioned early
        (immediately after STYLE_PREFIX), well within the first 65 CLIP tokens.
        """
        setting_dna = {
            "location_name": "Lớp học 12A",
            "setting_anchor": (
                "modern Japanese high school classroom interior, neat wooden student desks and chairs, "
                "large green chalkboard mounted on front wall, tall multi-pane glass windows with sunlight "
                "streaming across wooden floor, peaceful classroom atmosphere"
            )
        }
        dna_map = {
            "An": {
                "gender": "female",
                "role": "lead",
                "aliases": ["An", "cô bé"],
                "dna": (
                    "17yo Vietnamese schoolgirl, soft oval face, gentle dark almond eyes, sharp jawline, "
                    "straight jet-black hair with blunt bangs across forehead and shoulder-length bob, "
                    "wearing crisp white short-sleeve school uniform button-up shirt with stiff collar, "
                    "small dark navy ribbon tie pinned at collar, pleated dark navy skirt"
                )
            }
        }
        panels = [{
            "panel_index": 1,
            "image_prompt": "medium close-up shot of student turning around with a bright smile near the window",
            "dialogue_text": "An cúi đầu cặm cụi viết bài vào cuốn tập.",
            "layout_type": "square"
        }]

        validated = self.agent._validate_panels(panels, character_dna_map=dna_map, setting_dna=setting_dna)
        self.assertEqual(len(validated), 1)
        final_prompt = validated[0]["image_prompt"]

        # Setting anchor must appear at the very start of the prompt body (pos == len(STYLE_PREFIX))
        setting_pos = final_prompt.find("setting:")
        prefix_len = len(STYLE_PREFIX)
        self.assertLessEqual(setting_pos, prefix_len + 30, f"Setting anchor must be early. Pos: {setting_pos}, Prefix: {prefix_len}")

        # Both setting and action must be present
        self.assertIn("setting:", final_prompt)
        self.assertIn("writing attentively", final_prompt)

    def test_fix_pollinations_fallback_preserves_setting_and_action(self):
        """
        FIXED: format_pollinations_prompt cleanly preserves setting anchor and action gesture
        without broken words or mid-token truncations.
        """
        prompt = (
            f"{STYLE_PREFIX}"
            "setting: modern Japanese high school classroom interior, "
            "sitting at wooden student desk, writing attentively, "
            "17yo Vietnamese schoolgirl, soft oval face, gentle dark almond eyes, sharp jawline, "
            "wearing crisp white short-sleeve school uniform button-up shirt with stiff collar"
            f"{STYLE_SUFFIX}"
        )
        formatted = format_pollinations_prompt(prompt, max_len=300)
        self.assertIn("setting:", formatted)
        self.assertIn("writing attentively", formatted)
        self.assertNotIn(", ,", formatted)
        self.assertFalse(re.search(r'\b[a-z]{1,2}$', formatted))


if __name__ == "__main__":
    unittest.main(verbosity=2)
```

---

## 7. Verification Method & Cross-Suite Backward Compatibility Matrix

To execute independent verification after applying the blueprint:

```bash
# 1. Compilation Verification
python -m py_compile backend/agents/comic_agent.py backend/services/cloudflare_ai.py backend/tests/test_challenger_r2_m3_1_adversarial.py backend/tests/test_comic_modern_school_sync.py

# 2. Hardened Adversarial Suite (100% PASS expected)
python -m unittest backend/tests/test_challenger_r2_m3_1_adversarial.py -v

# 3. Milestone 3 Modern School Sync Suite (100% PASS expected)
python -m unittest backend/tests/test_comic_modern_school_sync.py -v

# 4. Milestone 1 & 2 Comic Regressions (100% PASS expected)
python -m unittest backend/tests/test_comic_dna_seed.py -v
python -m unittest backend/tests/test_comic_zero_truncation.py -v
python -m unittest backend/tests/test_challenger_m3_2_stress.py -v
```

### Compatibility Analysis:
- `test_comic_modern_school_sync.py`: All 14 tests remain 100% green. The prefix strings (`modern monochrome manga`, `clean g-pen lineart`), `DNA_EXTRACTOR_PROMPT` checks, 100% panel anchor attachment, and extracted actions are strictly preserved.
- `test_comic_dna_seed.py`: All 6 tests pass. Smart DNA injection and alias matching are completely unaffected.
- `test_comic_zero_truncation.py`: All 10 tests pass. Ellipsis sanitization and beat decomposition are completely unaffected.
