# Detailed Code Changes — Milestone 2 (Iteration 2)

**Worker**: `worker_m2_iter2`  
**Milestone**: Milestone 2 (R2 Manga Character Visual Consistency & Deterministic Seed)  
**Date**: 2026-09-19  

---

## 1. Summary of Changes

| File | Scope | Summary of Modifications |
|---|---|---|
| `backend/agents/comic_agent.py` | Defect 1: Gender Resolution Substring Defect | Fixed lines 132–146 and 299–319. Replaced substring checks (`"male" in gender`, `cue in app_lower`) with exact membership (`gender in ["female", "woman", "nữ"]`, `gender in ["male", "man", "nam"]`), regex word boundaries `\b(?:female|woman)\b` and `\b(?:male|man)\b`, and regex word boundaries for DNA/appearance descriptors (`\b{re.escape(cue)}\b`). Guaranteed `is_male and not is_female` so female characters never evaluate as `is_male: True`. |
| `backend/agents/comic_agent.py` | Defect 2: Vietnamese Compound Token Collisions | Fixed lines 370–388. For alias `"an"`, added boundary checks: (1) preceding Vietnamese compound prefix words (`"bất"`, `"bình"`, `"công"`, `"trị"`, `"quốc"`, `"bảo"`), (2) following Vietnamese compound suffix words (`"toàn"`, `"tâm"`, `"ninh"`, `"dưỡng"`, `"bài"`, `"nghỉ"`, `"ủi"`, `"nhiên"`, `"lạc"`, `"vui"`, `"cư"`, `"phận"`), and (3) expanded English article lookahead words (`old`, `ancient`, `isolated`, etc.). Multi-match loop ensures genuine `"An"` in the same sentence as compound words still correctly injects character DNA. |
| `backend/tests/test_comic_dna_seed.py` | Test Enhancement | Enhanced `test_regex_boundary_protection_an_false_positives` with Test 6 (asserting Vietnamese compound words like `"bất an"`, `"bình an"`, `"an toàn"`, `"an tâm"`, `"an ninh"`, `"an dưỡng"` do not inject character `"An"`) and Test 7 (asserting genuine character `"An"` alongside compound words like `"bất an"` in the same dialogue is accurately detected and injected). |
| `backend/tests/test_challenger_m2_adversarial.py` | Test Enhancement & Bug Resolution | Updated `test_false_positive_vietnamese_token_bat_an` with explicit assertion `self.assertFalse(is_leaked)`. Added `test_false_positive_vietnamese_compound_words_an` covering multiple Vietnamese sentences and mixed genuine/compound dialogue. Confirmed `test_reproduce_critical_gender_classification_bug` now passes with both assertions (`an_injected == False` and `minh_injected == True`). |

---

## 2. File Diffs and Explanations

### 2.1 `backend/agents/comic_agent.py`

#### A. In `extract_character_dna` (lines 131–146):
**Before:**
```python
app_lower = c_app.lower()
is_female = (
    c_gender == "female" or "nữ" in c_gender or "nữ" in c_role or
    any(cue in app_lower for cue in ["schoolgirl", "girl", "woman", "female"])
)
is_male = (
    c_gender == "male" or "nam" in c_gender or "nam" in c_role or
    any(cue in app_lower for cue in ["schoolboy", "boy", "man", "male"])
)
```
**After:**
```python
app_lower = c_app.lower()
is_female = (
    c_gender in ["female", "woman", "nữ"] or
    bool(re.search(r"\b(?:female|woman)\b", c_gender)) or
    "nữ" in c_gender or "nữ" in c_role or
    any(re.search(rf"\b{re.escape(cue)}\b", app_lower) for cue in ["schoolgirl", "girl", "woman", "female"])
)
is_male = (
    (
        c_gender in ["male", "man", "nam"] or
        bool(re.search(r"\b(?:male|man)\b", c_gender)) or
        "nam" in c_gender or "nam" in c_role or
        any(re.search(rf"\b{re.escape(cue)}\b", app_lower) for cue in ["schoolboy", "boy", "man", "male"])
    )
    and not is_female
)
```
**Rationale**:
- `"male"` is a strict substring of `"female"`, and `"man"` is a strict substring of `"woman"`.
- Without word-boundary regex `\b{cue}\b`, searching `cue = "male"` in `app_lower` matching `"female"` evaluated `is_male` to `True` for female characters.
- Word boundaries ensure `\bmale\b` does not match within `"female"`, and `\bman\b` does not match within `"woman"`.
- `and not is_female` provides strict mutual exclusivity when `is_female` is identified.

---

#### B. In `_validate_panels` (lines 299–319):
**Before:**
```python
is_female = (
    gender == "female" or
    "female" in gender or
    "nữ" in gender or
    "nữ" in role or
    any(cue in dna_lower for cue in ["schoolgirl", "girl", "woman", "female", "her ", "she "]) or
    any(cue in alias_set for cue in ["cô bé", "nữ sinh", "cô ấy", "nàng", "cô gái", "she", "girl"])
)

is_male = (
    gender == "male" or
    "male" in gender or
    "nam" in gender or
    "nam" in role or
    any(cue in dna_lower for cue in ["schoolboy", "boy", "man", "male", "his ", "he "]) or
    any(cue in alias_set for cue in ["anh bạn", "bạn cùng bàn", "học sinh nam", "cậu ấy", "chàng trai", "anh ấy", "he", "boy"])
)
```
**After:**
```python
is_female = (
    gender in ["female", "woman", "nữ"] or
    bool(re.search(r"\b(?:female|woman)\b", gender)) or
    "nữ" in gender or
    "nữ" in role or
    any(re.search(rf"\b{re.escape(cue)}\b", dna_lower) for cue in ["schoolgirl", "girl", "woman", "female", "her", "she"]) or
    any(cue in alias_set for cue in ["cô bé", "nữ sinh", "cô ấy", "nàng", "cô gái", "she", "girl"])
)

is_male = (
    (
        gender in ["male", "man", "nam"] or
        bool(re.search(r"\b(?:male|man)\b", gender)) or
        "nam" in gender or
        "nam" in role or
        any(re.search(rf"\b{re.escape(cue)}\b", dna_lower) for cue in ["schoolboy", "boy", "man", "male", "his", "he"]) or
        any(cue in alias_set for cue in ["anh bạn", "bạn cùng bàn", "học sinh nam", "cậu ấy", "chàng trai", "anh ấy", "he", "boy"])
    )
    and not is_female
)
```
**Rationale**:
- Eliminates `"male" in gender`, which was unconditionally `True` for `gender = "female"`.
- Prevents fallback selection `males = [c for c in char_entry_list if c.get("is_male")]` from containing female characters, directly fixing `test_gender_aware_fallback`.

---

#### C. In `_validate_panels` (lines 370–388):
**Before:**
```python
if alias_clean.lower() == "an":
    has_valid_char_match = False
    for m in matches:
        after_text = search_text[m.end():].lstrip()
        if re.match(r'^(?:establishing|extreme|overhead|wide|interior|exterior|empty|aerial|eye-level|illustration|action|anime|epic|intense|indoor|outdoor|open|ornate|ambient|abandoned|shot|close-up|closeup|panel|angle)\b', after_text, re.IGNORECASE):
            continue
        has_valid_char_match = True
        break
    if not has_valid_char_match:
        continue
```
**After:**
```python
if alias_clean.lower() == "an":
    has_valid_char_match = False
    for m in matches:
        before_text = search_text[:m.start()]
        after_text = search_text[m.end():].lstrip()
        # 1. If preceded by Vietnamese compound prefix words (e.g. "bất an", "bình an", "công an", "trị an", "quốc an", "bảo an")
        if re.search(r'(?<!\w)(?:bất|bình|công|trị|quốc|bảo)[\s\-_]*$', before_text, re.IGNORECASE):
            continue
        # 2. If followed by Vietnamese compound suffix words (e.g. "an toàn", "an tâm", "an ninh", "an dưỡng", "an bài", "an nghỉ", "an ủi", "an nhiên", "an lạc", "an vui", "an cư", "an phận")
        if re.match(r'^(?:toàn|tâm|ninh|dưỡng|bài|nghỉ|ủi|nhiên|lạc|vui|cư|phận)(?!\w)', after_text, re.IGNORECASE):
            continue
        # 3. If followed by English camera shot, scene description, or vowel adjectives (indefinite article "an")
        if re.match(r'^(?:establishing|extreme|overhead|wide|interior|exterior|empty|aerial|eye-level|illustration|action|anime|epic|intense|indoor|outdoor|open|ornate|ambient|abandoned|shot|close-up|closeup|panel|angle|old|ancient|isolated|overgrown|ominous|elaborate|unusual|elderly|intricate|ordinary|eerie|electric|enormous)\b', after_text, re.IGNORECASE):
            continue
        has_valid_char_match = True
        break
    if not has_valid_char_match:
        continue
```
**Rationale**:
- In Vietnamese dialogue, common vocabulary words like `"bất an"`, `"bình an"`, `"an toàn"`, `"an tâm"`, `"an ninh"`, `"an dưỡng"` contain the word `"an"`.
- By inspecting `before_text` for prefix words and `after_text` for suffix words, general vocabulary does not falsely inject character `"An"`.
- Iterating across all matches allows sentences like `"Dù cảm thấy bất an, An vẫn mỉm cười"` to skip the compound word match and correctly identify the genuine character name.

---

### 2.2 `backend/tests/test_comic_dna_seed.py`

Enhanced `test_regex_boundary_protection_an_false_positives` by adding:
- Test 6: Iterates through 6 Vietnamese compound word sentences (`"bất an"`, `"bình an"`, `"an toàn"`, `"an tâm"`, `"an ninh"`, `"an dưỡng"`) and asserts `"17yo schoolgirl An"` is NOT in `image_prompt`.
- Test 7: Tests mixed dialogue (`"Dù trong lòng rất bất an, An vẫn bình thản mỉm cười."`) and asserts `"17yo schoolgirl An"` IS correctly injected.

---

### 2.3 `backend/tests/test_challenger_m2_adversarial.py`

- In `test_false_positive_vietnamese_token_bat_an`: Added assertion `self.assertFalse(is_leaked)`.
- Added `test_false_positive_vietnamese_compound_words_an`: Tests compound words across multiple sentences and mixed dialogue.
- Confirmed `test_reproduce_critical_gender_classification_bug` now passes with `an_injected == False` and `minh_injected == True`.
