# Deep Adversarial Security & Invariant Analysis: Milestone 2 DSGO

**Auditor**: `challenger_r2_m2_1` (Empirical Challenger)  
**Target**: Milestone 2 DSGO & Spatial Scene Enclosure (`backend/models/scene_graph.py`, `backend/agents/story_memory.py`, `backend/agents/memory_extractor.py`)  
**Date**: 2026-09-20T13:48:00Z  
**Verdict**: **REQUEST_CHANGES** (11/18 Stress Tests Failed; Critical State Leak & Deserialization Crash Identified)

---

## 1. Adversarial Test Results Matrix

| # | Test Category | Test Name | Input / Attack Scenario | Expected Behavior | Actual Behavior | Result | Severity |
|---|---------------|-----------|-------------------------|-------------------|-----------------|--------|----------|
| 1 | Scene Gating | `test_negation_khong_buoc_ra_khoi_phong` | "An kiên quyết không bước ra khỏi phòng mà tiếp tục ngồi ở bàn học nhìn ra hành lang." | Scene locked at `classroom_12a` | Transitioned to `corridor_3f` | **FAIL** | HIGH |
| 2 | Scene Gating | `test_negation_khong_buoc_vao` | "Cô bé ngập ngừng rồi nhất quyết không bước vào hành lang tối tăm." | Scene locked at `classroom_12a` | Transitioned to `corridor_3f` | **FAIL** | HIGH |
| 3 | Scene Gating | `test_negation_tu_choi_roi_phong` | "Minh từ chối rời phòng dù tiếng ồn ngoài hành lang ngày càng lớn." | Scene locked at `classroom_12a` | Transitioned to `corridor_3f` | **FAIL** | HIGH |
| 4 | Scene Gating | `test_deceptive_verb_mo_cua_so` | "An đứng dậy mở cửa sổ nhìn ra hành lang bên ngoài." | Scene locked at `classroom_12a` | Transitioned to `corridor_3f` | **FAIL** | MEDIUM |
| 5 | Scene Gating | `test_empty_and_whitespace_prose` | `""`, `"   \n\t   "`, `None` | Scene locked at `classroom_12a` | Scene locked at `classroom_12a` | **PASS** | LOW |
| 6 | Scene Gating | `test_destination_shadowing_by_unconnected_mention` | "Nhớ lại trận chung kết nghẹt thở trên sân bóng hôm qua, An vội vã mở cửa bước vào hành lang." | Transition to connected `corridor_3f` | Aborted at unconnected `soccer_field`, returned `classroom_12a` | **FAIL** | HIGH |
| 7 | Spatial Drift | `test_subword_preservation` | "inside classroom, wearing streetwear, bathed in sunlight" | Preserves `classroom`, `streetwear`, `sunlight` | Preserved correctly | **PASS** | LOW |
| 8 | Spatial Drift | `test_hyphenated_compound_mutilation` | "wearing street-style jacket, driving off-road vehicle, entering car-free zone" | Clean prompt or untouched compounds | Mutilated into `, -style jacket`, `off-, vehicle`, `, -free zone` | **FAIL** | HIGH |
| 9 | Spatial Drift | `test_negative_drift_token_with_parentheses` | Negative token `street (outdoor)` with raw prompt "sitting at desk, street (outdoor)" | Strips `street (outdoor)` | Regex `\b` boundary fails, token remains untouched | **FAIL** | MEDIUM |
| 10 | Spatial Drift | `test_punctuation_artifacts` | "inside room. street. sitting at desk" | Clean sentence punctuation | Injected `.,` punctuation artifact | **FAIL** | LOW |
| 11 | Spatial Exclusivity | `test_direct_disconnected_jump_rejected` | Jump from Room A to Room C without visiting corridor | Rejected (returns False) | Rejected (returns False) | **PASS** | LOW |
| 12 | Spatial Exclusivity | `test_character_teleportation_and_location_leak` | Transition Room A -> Corridor with `moving_character_ids=['minh']` where Minh is in disconnected Room B | Disconnected entity cannot move; no state desync | Minh moved to corridor, but NOT removed from Room B (duplicated in active entities) | **FAIL** | **CRITICAL** |
| 13 | Vitality Invariant | `test_deceased_cannot_act` | Deceased character attempting `SPEAKS` via `validate_vitality` | Rejected with `VITALITY_VIOLATION` | Rejected with `VITALITY_VIOLATION` | **PASS** | LOW |
| 14 | Vitality Invariant | `test_deceased_moving_themselves_in_transition` | Deceased character included in `transition_scene` | Corpse cannot autonomously transition location | Corpse autonomously transitions to new room | **FAIL** | HIGH |
| 15 | Vitality Invariant | `test_unconscious_character_cannot_perform_active_actions` | Unconscious character attempting `SPEAKS` | Rejected (unconscious cannot speak) | Permitted (returns True) | **FAIL** | MEDIUM |
| 16 | Deserialization | `test_corrupted_entities_field_raises_unhandled_exception` | `DynamicSceneGraph.from_dict({'entities': 'invalid'})` | Safe fallback to default graph | Crashes with unhandled `pydantic_core.ValidationError` | **FAIL** | HIGH |
| 17 | Deserialization | `test_corrupted_enclosures_field_crashes` | `DynamicSceneGraph.from_dict({'enclosures': [1, 2, 3]})` | Safe fallback to default graph | Crashes with unhandled `pydantic_core.ValidationError` | **FAIL** | HIGH |
| 18 | Deserialization | `test_none_value_for_non_optional_field_crashes` | `DynamicSceneGraph.from_dict({'era_genre': None})` | Safe fallback to default graph | Crashes with unhandled `pydantic_core.ValidationError` | **FAIL** | HIGH |

---

## 2. In-Depth Vulnerability Analysis

### Vulnerability 1: Negation Blindness & Deceptive Substrings in Scene Transition Gating (HIGH)
- **Source**: `backend/models/scene_graph.py`, lines 264-289, 617-648.
- **Root Cause**:
  1. `gate_scene_transition` uses raw regex searches `re.search(pattern, text, re.IGNORECASE)` across `TRANSITION_VERB_PATTERNS` without checking for Vietnamese negation words (`không`, `chẳng`, `chưa`, `đừng`, `từ chối`, `ngăn`, `không hề`).
  2. Substring pattern `r"mở\s+cửa"` eagerly matches `"mở cửa sổ"` (opening a window) or `"mở cửa tủ"` (opening a cabinet), erroneously flagging non-spatial actions as transitions.
- **Impact**:
  Prose describing characters refusing to move ("An không bước ra khỏi phòng mà nhìn ra hành lang") erroneously triggers a spatial transition to the corridor. This directly violates Requirement R2 (Spatial Scene Enclosure).

### Vulnerability 2: Premature Break & Destination Shadowing in Candidate Matching (HIGH)
- **Source**: `backend/models/scene_graph.py`, lines 631-647.
- **Code Snippet**:
  ```python
  for enc_id, enc in self.enclosures.items():
      if enc_id == curr_id:
          continue
      if enc.name.lower() in lower_text or enc_id.lower() in lower_text:
          matched_enclosure_id = enc_id
          break  # <-- PREMATURE BREAK!

  if matched_enclosure_id:
      success = self.transition_scene(matched_enclosure_id)
      if success:
          return matched_enclosure_id
  return curr_id
  ```
- **Root Cause**:
  The loop breaks on the *first* enclosure matched in Python dictionary iteration order. If the prose mentions an unconnected place (e.g. nostalgic memory of "sân bóng") followed by an actual transition ("bước vào hành lang"), if "sân bóng" is evaluated first, `transition_scene("soccer_field")` returns `False`, and the function immediately aborts, never checking "hành lang"!
- **Impact**:
  Legitimate, connected transitions fail silently whenever any unconnected setting is mentioned earlier in the paragraph or appears earlier in dictionary iteration.

### Vulnerability 3: Hyphenated Compound Word Mutilation in Spatial Drift Sanitizer (HIGH)
- **Source**: `backend/models/scene_graph.py`, lines 324-326.
- **Code Snippet**:
  ```python
  pattern = r"(?i)(?:,\s*)?\b" + re.escape(token_clean) + r"\b(?:\s*,)?"
  sanitized = re.sub(pattern, ", ", sanitized)
  ```
- **Root Cause**:
  In regex, `\b` defines a boundary between `\w` (word character) and `\W` (non-word character). Hyphen `-` is `\W`!
  When stripping `"street"` from `"street-style jacket"`:
  - Before `s` is boundary.
  - After `t` is `-` (which is `\W`, satisfying `\b`).
  - `"street"` is replaced by `", "`, transforming `"street-style jacket"` into `", -style jacket"`.
  - Similarly, `"off-road"` becomes `"off-, "`, and `"car-free"` becomes `", -free"`.
- **Impact**:
  Corrupted tokens (`-style`, `off-, `, `-free`) get injected into Diffusion prompts for Cloudflare AI, corrupting character fashion and visual rendering.

### Vulnerability 4: Disconnected Entity Teleportation & State Desync (CRITICAL)
- **Source**: `backend/models/scene_graph.py`, lines 588-596.
- **Code Snippet**:
  ```python
  for cid in cids_to_move:
      if cid in self.entities:
          char = self.entities[cid]
          char.current_location_id = target_enclosure_id
          if current_enc and cid in current_enc.active_entities:
              current_enc.active_entities.remove(cid)
          if cid not in target_enc.active_entities:
              target_enc.active_entities.append(cid)
  ```
- **Root Cause**:
  When transitioning from `current_enc` to `target_enc`, `transition_scene` only removes characters from `current_enc.active_entities`. If `moving_character_ids` includes an entity currently located in a different enclosure (`disconnected_enc`), the entity:
  1. Has its `current_location_id` overwritten to `target_enc`.
  2. Is appended to `target_enc.active_entities`.
  3. Is **NEVER removed** from `disconnected_enc.active_entities`.
  4. Teleports across disconnected boundaries without any spatial validation.
- **Impact**:
  Character entities become duplicated across multiple enclosure `active_entities` lists simultaneously. Physical exclusivity invariant is completely broken.

### Vulnerability 5: Unhandled `ValidationError` Crash in `DynamicSceneGraph.from_dict` (HIGH)
- **Source**: `backend/models/scene_graph.py`, lines 699-703.
- **Code Snippet**:
  ```python
  @classmethod
  def from_dict(cls, data: Dict[str, Any]) -> "DynamicSceneGraph":
      if not isinstance(data, dict):
          return cls()
      return cls.model_validate(data)  # <-- UNHANDLED VALIDATION ERROR!
  ```
- **Root Cause**:
  `model_validate(data)` raises `pydantic_core.ValidationError` if any field or nested model inside `data` is malformed (e.g. `{"entities": "not_a_dict"}`, `{"era_genre": None}`, `{"enclosures": [1,2,3]}`). Unlike `StoryMemory.from_dict` which catches exceptions, any direct consumer calling `DynamicSceneGraph.from_dict(data)` directly crashes.
- **Impact**:
  Database deserialization of corrupted chapter memory or malformed API payloads causes immediate uncaught 500 crashes.

### Vulnerability 6: Vitality Invariant Bypass in Spatial Scene Transitions (HIGH)
- **Source**: `backend/models/scene_graph.py`, lines 588-598.
- **Root Cause**:
  `transition_scene` performs zero vitality verification. When moving active entities, deceased characters (`vitality_state == VitalityState.DECEASED`) are automatically transitioned alongside living characters as if walking under their own power.
- **Impact**:
  Dead bodies autonomously navigate rooms across chapters, violating narrative and physical invariants.

---

## 3. Concrete Actionable Mitigations

### Mitigation for Vulnerability 1 (Negation & Deceptive Verbs):
1. Add a negation detector:
   ```python
   NEGATION_PREFIX_PATTERN = r"(không\s+thể|không|chẳng|chưa|đừng|từ\s+chối|ngăn|không\s+hề|không\s+bao\s+giờ)\s+(?:được\s+)?"
   ```
   If a transition verb is immediately preceded by `NEGATION_PREFIX_PATTERN` (e.g. within 1-3 words), discard the transition verb.
2. Refine deceptive verbs:
   Replace `r"mở\s+cửa"` with `r"mở\s+cửa(?!\s+sổ|\s+tủ|\s+hòm|\s+xe)"` or require `r"mở\s+cửa\s+(?:bước|đi|ra|vào)"`.

### Mitigation for Vulnerability 2 (Destination Matching Loop):
Remove `break`. Iterate through all candidates in text and select the candidate that is connected to `current_enc` or has the highest proximity to the transition verb in the text:
```python
valid_candidates = []
for enc_id, enc in self.enclosures.items():
    if enc_id == curr_id:
        continue
    if enc.name.lower() in lower_text or enc_id.lower() in lower_text:
        # Check if actually connected before locking in
        if not current_enc or enc_id in current_enc.connected_enclosures or current_enc.id in enc.connected_enclosures:
            valid_candidates.append(enc_id)

for cand_id in valid_candidates:
    if self.transition_scene(cand_id):
        return cand_id
```

### Mitigation for Vulnerability 3 (Spatial Drift Sanitizer Hyphenation):
1. Ensure `\b` is flanked by whitespace or punctuation, and avoid matching inside hyphenated compounds:
   ```python
   pattern = r"(?i)(?:,\s*)?(?<![\w\-])" + re.escape(token_clean) + r"(?![\w\-])(?:\s*,)?"
   ```
2. Clean up resulting punctuation artifacts:
   ```python
   sanitized = re.sub(r"\.\s*,", ".", sanitized)
   sanitized = re.sub(r",\s*\.", ".", sanitized)
   ```

### Mitigation for Vulnerability 4 (State Desync & Teleportation):
1. In `transition_scene`, verify that every character in `cids_to_move` is currently located in `current_enc`. If not, either reject the move or look up their actual current enclosure and remove them from that enclosure's `active_entities`:
   ```python
   for cid in cids_to_move:
       if cid in self.entities:
           char = self.entities[cid]
           # Remove from old enclosure if different
           old_loc = char.current_location_id
           if old_loc and old_loc in self.enclosures:
               if cid in self.enclosures[old_loc].active_entities:
                   self.enclosures[old_loc].active_entities.remove(cid)
           char.current_location_id = target_enclosure_id
           if cid not in target_enc.active_entities:
               target_enc.active_entities.append(cid)
   ```

### Mitigation for Vulnerability 5 (Deserialization Safety):
Wrap `model_validate` in `DynamicSceneGraph.from_dict`:
```python
@classmethod
def from_dict(cls, data: Dict[str, Any]) -> "DynamicSceneGraph":
    if not isinstance(data, dict):
        return cls()
    try:
        # Pre-clean known malformed values
        clean_data = dict(data)
        if clean_data.get("era_genre") is None:
            clean_data.pop("era_genre", None)
        if not isinstance(clean_data.get("entities"), dict):
            clean_data["entities"] = {}
        if not isinstance(clean_data.get("enclosures"), dict):
            clean_data["enclosures"] = {}
        return cls.model_validate(clean_data)
    except Exception:
        return cls()
```

### Mitigation for Vulnerability 6 (Vitality in Transition Scene):
Exclude deceased characters from moving unless carried:
```python
for cid in cids_to_move:
    char = self.entities.get(cid)
    if char and char.vitality_state == VitalityState.DECEASED:
        # Cannot walk autonomously
        continue
```
And expand `validate_vitality` to check `UNCONSCIOUS` for active verbs:
```python
if actor.vitality_state in (VitalityState.DECEASED, VitalityState.UNCONSCIOUS):
    return False, f"VITALITY_VIOLATION: Character '{actor.name}' is {actor.vitality_state.value} and cannot perform '{action}'."
```
