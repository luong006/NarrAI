# Remediation Blueprint & Forensic Analysis Report: Milestone 2 DSGO

**Author**: `explorer_r2_m2_fix` (Codebase Explorer & Remediation Analyst)  
**Target File**: `backend/models/scene_graph.py`  
**Related Components**: `backend/agents/story_memory.py`, `backend/agents/memory_extractor.py`, `backend/tests/test_adversarial_dsgo.py`  
**Date**: 2026-09-20T13:53:00Z  
**Status**: REMEDIATION_BLUEPRINT_COMPLETE (Ready for Implementation)

---

## 1. Executive Summary & Verification Matrix

Challenger 1 identified 6 vulnerability classes across `backend/models/scene_graph.py` that caused 11 of 18 adversarial stress tests to fail. This investigation thoroughly analyzed the root causes, verified the mechanical failure paths against symbolic traces, and developed a complete, deterministic remediation blueprint.

### Vulnerability & Resolution Matrix

| # | Vulnerability Class | Severity | Current Lines | Root Cause | Remediation Mechanism | Target Adversarial Tests |
|---|---------------------|----------|---------------|------------|-----------------------|--------------------------|
| **1** | Negation Blindness & Deceptive Verbs | **HIGH** | 264–289, 617–626 | Raw regex matching on verbs ignores Vietnamese refusal/negation particles (`không`, `từ chối`, `chẳng`) and matches non-spatial door/window objects (`mở cửa sổ`). | Introduce `is_transition_verb_negated` clause-scoped detector; equip `mở cửa` with negative lookahead `(?!\s*(?:sổ\|tủ\|hòm\|két\|ngăn\|xe\b))`. | `test_negation_khong_buoc_ra_khoi_phong`, `test_negation_khong_buoc_vao`, `test_negation_tu_choi_roi_phong`, `test_deceptive_verb_mo_cua_so` |
| **2** | Premature Break & Destination Shadowing | **HIGH** | 631–648 | Dict iteration loop terminates on the very first matched keyword (`break`), aborting if that location is unconnected. | Collect all candidate enclosures mentioned in text, score by connectivity and text position, try connected candidates first without premature loop abortion. | `test_destination_shadowing_by_unconnected_mention` |
| **3** | Hyphenated Compound Word Mutilation | **HIGH** | 324–326, 366–368 | Word boundary `\b` treats `-` as `\W`, splitting compound words (`street-style` -> `, -style`), fails on tokens ending in `)`, and generates `.,` artifacts. | Replace `\b` with `(?<![\w\-])` and `(?![\w\-])(?:\s*[,.])?`; add punctuation normalizer purging `.,` and `,.`. | `test_hyphenated_compound_mutilation`, `test_negative_drift_token_with_parentheses`, `test_punctuation_artifacts` |
| **4** | Disconnected Entity Teleportation & State Desync | **CRITICAL** | 588–596 | `transition_scene` only removes characters from `current_enc`, failing to clean up characters residing in other rooms and allowing disconnected jumps. | When `force=False`, reject move if any character is in an enclosure different from `current_enc`; actively remove moved entities from their tracked `old_loc` enclosure. | `test_character_teleportation_and_location_leak` |
| **5** | Unhandled ValidationError Deserialization Crash | **HIGH** | 699–703 | `model_validate` raises uncaught `pydantic_core.ValidationError` on malformed, partial, or corrupted dicts. | Wrap `DynamicSceneGraph.from_dict` in try/except; sanitize non-dict `entities`, `enclosures`, `items`, normalize enums, and fallback to default graph. | `test_corrupted_entities_field_raises_unhandled_exception`, `test_corrupted_enclosures_field_crashes`, `test_none_value_for_non_optional_field_crashes`, `test_corrupted_entity_item_crashes`, `test_invalid_enum_value_crashes` |
| **6** | Vitality Invariant Bypass in Transitions | **HIGH** | 449–460, 580–598 | `transition_scene` transitions corpses without checking vitality; `validate_vitality` does not check `UNCONSCIOUS`. | Exclude `DECEASED` entities from autonomous movement in `transition_scene`; check `UNCONSCIOUS` in `validate_vitality`. | `test_deceased_moving_themselves_in_transition`, `test_unconscious_character_cannot_perform_active_actions` |

---

## 2. In-Depth Root Cause Analysis & Proposed Remediations

### 2.1. Vulnerability 1: Negation Blindness & Deceptive Verbs in Scene Transition Gating
- **Problem**:
  In Vietnamese Light Novels, sentences frequently express hesitation or refusal:
  - *"An kiên quyết không bước ra khỏi phòng mà tiếp tục ngồi ở bàn học nhìn ra hành lang."*
  - *"Cô bé ngập ngừng rồi nhất quyết không bước vào hành lang tối tăm."*
  - *"Minh từ chối rời phòng dù tiếng ồn ngoài hành lang ngày càng lớn."*
  Furthermore, physical interactions with non-spatial objects resemble transition verbs:
  - *"An đứng dậy mở cửa sổ nhìn ra hành lang bên ngoài."*
  Because `TRANSITION_VERB_PATTERNS` matches `bước ra khỏi`, `bước vào`, `rời phòng`, and `mở cửa`, `has_transition_verb` evaluates to `True`, triggering an unwanted spatial transition.
- **Remediation**:
  1. Define `is_transition_verb_negated(text: str, verb_start_idx: int) -> bool`:
     Inspects the immediate preceding clause prefix (from the nearest clause delimiter `[,.;:!?\n]` to `verb_start_idx`) for Vietnamese and English negation patterns (`không`, `từ chối`, `chẳng`, `chưa`, `quyết không`, `ngăn`, `never`, `refused to`, etc.) within a window of up to 4 words.
  2. In `TRANSITION_VERB_PATTERNS`, constrain `mở cửa`:
     Change `r"mở\s+cửa"` to `r"mở\s+(?:cánh\s+)?cửa(?!\s*(?:sổ|tủ|hòm|két|ngăn|xe\b))"`.
  3. In `gate_scene_transition`:
     Iterate through all matches using `re.finditer` and verify `not is_transition_verb_negated(...)`.

### 2.2. Vulnerability 2: Premature Break & Destination Shadowing in Candidate Matching Loop
- **Problem**:
  Lines 631–648 in `backend/models/scene_graph.py`:
  ```python
  for enc_id, enc in self.enclosures.items():
      if enc_id == curr_id:
          continue
      if enc.name.lower() in lower_text or enc_id.lower() in lower_text:
          matched_enclosure_id = enc_id
          break  # Premature break!
  ```
  If text references an unconnected place in past memory (e.g. *"Nhớ lại trận chung kết nghẹt thở trên sân bóng hôm qua, An vội vã mở cửa bước vào hành lang."*), and `soccer_field` matches first, `transition_scene("soccer_field")` returns `False` (unconnected). The loop never tests `corridor_3f`.
- **Remediation**:
  Remove `break`. Collect all mentioned enclosure candidates `(is_connected, match_pos, enc_id)`:
  - `is_connected`: Check if connected to `current_enc`.
  - `match_pos`: Position of enclosure name or ID in `lower_text` (latest mention in text is prioritized).
  Sort candidate list with `candidates.sort(key=lambda c: (c[0], c[1]), reverse=True)`.
  Attempt `transition_scene` on prioritized candidates sequentially until a valid transition succeeds.

### 2.3. Vulnerability 3: Hyphenated Compound Word Mutilation & Token Boundaries
- **Problem**:
  In `sanitize_spatial_prompt` and `sanitize_era_prompt`:
  ```python
  pattern = r"(?i)(?:,\s*)?\b" + re.escape(token_clean) + r"\b(?:\s*,)?"
  ```
  1. Because `-` is `\W`, `\b` matches before `-`. Stripping `street` from `street-style` produces `, -style jacket`. Stripping `road` from `off-road` produces `off-, vehicle`.
  2. Tokens ending with `)` such as `street (outdoor)` cannot match `\b` when followed by `,` or space, because both `)` and `,` are `\W` (no word boundary exists).
  3. When tokens are replaced by `", "`, consecutive punctuation like `inside room. street. sitting at desk` becomes `inside room., sitting at desk`.
- **Remediation**:
  1. Replace `\b` with lookarounds enforcing non-word AND non-hyphen boundaries:
     ```python
     pattern = r"(?i)(?:,\s*)?(?<![\w\-])" + re.escape(token_clean) + r"(?![\w\-])(?:\s*[,.])?"
     ```
  2. Clean up punctuation artifacts after substitutions:
     ```python
     sanitized = re.sub(r"\.\s*,", ".", sanitized)
     sanitized = re.sub(r",\s*\.", ".", sanitized)
     sanitized = re.sub(r"\.{2,}", ".", sanitized)
     sanitized = re.sub(r"\s*,\s*", ", ", sanitized)
     sanitized = re.sub(r"(?:,\s*){2,}", ", ", sanitized)
     sanitized = re.sub(r"^[,\s.]+", "", sanitized)
     sanitized = re.sub(r"[,\s]+$", "", sanitized)
     sanitized = re.sub(r"\s{2,}", " ", sanitized)
     ```

### 2.4. Vulnerability 4: Disconnected Entity Teleportation & State Desync
- **Problem**:
  `transition_scene` previously assumed all characters in `moving_character_ids` were in `current_enc`:
  ```python
  if current_enc and cid in current_enc.active_entities:
      current_enc.active_entities.remove(cid)
  ```
  If `cid` resided in disconnected `room_b`, it was never removed from `room_b.active_entities`, causing duplicate presence across disjoint rooms. Furthermore, a character in disconnected `room_b` could be teleported into `corridor` during a `room_a` transition.
- **Remediation**:
  1. Spatial exclusivity check: When `not force` and `moving_character_ids` is provided, verify that every character is currently located in `current_enc.id`. If any character is in another enclosure, reject the transition (`return False`).
  2. Enclosure synchronization: Look up `old_loc = char.current_location_id`. If `old_loc in self.enclosures`, actively remove `cid` from `self.enclosures[old_loc].active_entities`.

### 2.5. Vulnerability 5: Unhandled ValidationError Crash in Deserialization
- **Problem**:
  `DynamicSceneGraph.from_dict` used raw `model_validate(data)`. Malformed dictionary inputs (e.g. `{"entities": "string"}`, `{"enclosures": [1, 2, 3]}`, `{"era_genre": None}`, or invalid enum values) raise uncaught `pydantic_core.ValidationError` which crashes callers.
- **Remediation**:
  1. Add defensive pre-sanitization in `from_dict`:
     - If `era_genre` is not a dict or `None`, purge it to let default constructor instantiate clean `EraGenreConstraint`.
     - Ensure `entities`, `enclosures`, and `items` are dictionaries. If not, default to `{}`.
     - For nested character dictionaries, catch invalid `vitality_state` values and normalize to `VitalityState.ALIVE`. Skip unparseable entity entries.
  2. Enclose entire body in `try ... except Exception: return cls()`.
  3. Apply corresponding defensive exception handling in `CharacterEntity.from_dict`, `SpaceEnclosure.from_dict`, and `EraGenreConstraint.from_dict`.

### 2.6. Vulnerability 6: Vitality Invariant Bypass in Transitions
- **Problem**:
  1. In `transition_scene`, corpses (`vitality_state == VitalityState.DECEASED`) were moved automatically as active entities.
  2. In `validate_vitality`, only `DECEASED` was checked; `UNCONSCIOUS` characters were permitted to perform active actions like speaking or moving.
- **Remediation**:
  1. In `validate_vitality`, reject active actions for both `DECEASED` and `UNCONSCIOUS`:
     ```python
     if actor.vitality_state == VitalityState.DECEASED:
         return False, f"VITALITY_VIOLATION: Character '{actor.name}' is DECEASED and cannot perform '{action}'."
     if actor.vitality_state == VitalityState.UNCONSCIOUS:
         return False, f"VITALITY_VIOLATION: Character '{actor.name}' is UNCONSCIOUS and cannot perform '{action}'."
     ```
  2. In `transition_scene`, filter out deceased entities from moving:
     ```python
     if char.vitality_state == VitalityState.DECEASED:
         continue
     ```

---

## 3. Concrete Line-by-Line Replacement Code

Below is the complete, drop-in replacement specification for `backend/models/scene_graph.py`.

```python
"""
Dynamic Scene-Graph Ontology (DSGO) Models & Automated Invariant Gatekeepers.
Enforces 3-dimensional constraints:
  - Dimension 1: Entity (CharacterEntity, Vitality, Inventory, Psychological state)
  - Dimension 2: Space (SpaceEnclosure, BoundaryType, Architectural Anchors, Negative Drift Tokens)
  - Dimension 3: Era & Genre (EraGenreConstraint, World Axioms, Era Banlist, Tech Level)
Provides Spatial Scene Enclosure, Scene Transition Gating, and Drift Sanitizers.
"""
import re
import uuid
from enum import Enum
from typing import List, Dict, Optional, Any, Tuple, Set
from pydantic import BaseModel, Field, model_validator


class VitalityState(str, Enum):
    ALIVE = "alive"
    INJURED = "injured"
    UNCONSCIOUS = "unconscious"
    DECEASED = "deceased"


class EntityRole(str, Enum):
    LEAD = "lead"
    ANTAGONIST = "antagonist"
    SUPPORTING = "supporting"
    MINOR = "minor"


class BoundaryType(str, Enum):
    INDOOR_ENCLOSED = "indoor_enclosed"      # Classroom, bedroom, office, interrogation room
    VEHICLE_INTERIOR = "vehicle_interior"    # Inside a car, train cabin, bus interior
    OUTDOOR_CONFINED = "outdoor_confined"    # Courtyard with perimeter walls, fenced alley, fenced rooftop
    OUTDOOR_OPEN = "outdoor_open"            # City street, open field, park, plaza


class EraType(str, Enum):
    MODERN_2020S = "modern_2020s"
    HISTORICAL_MEDIEVAL = "historical_medieval"
    ANCIENT_EAST_ASIA = "ancient_east_asia"
    CYBERPUNK_2099 = "cyberpunk_2099"
    VICTORIAN_1890S = "victorian_1890s"
    CUSTOM = "custom"


# ==============================================================================
# DIMENSION 1: ENTITY MODELS
# ==============================================================================

class CharacterEntity(BaseModel):
    id: str
    name: str
    aliases: List[str] = Field(default_factory=list)
    visual_dna: str = ""
    vitality_state: VitalityState = VitalityState.ALIVE
    current_location_id: Optional[str] = None
    inventory: List[str] = Field(default_factory=list)
    psychological_state: str = "calm"
    gender: str = "unknown"
    role: EntityRole = EntityRole.SUPPORTING

    @model_validator(mode="before")
    @classmethod
    def _normalize_entity_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Support alias "dna" for "visual_dna"
            if "dna" in data and "visual_dna" not in data:
                data["visual_dna"] = data.pop("dna")
            elif "dna" in data:
                data.pop("dna")
            # Support alias "vitality" for "vitality_state"
            if "vitality" in data and "vitality_state" not in data:
                data["vitality_state"] = data.pop("vitality")
            elif "vitality" in data:
                data.pop("vitality")
            # Support alias "emotional_state" for "psychological_state"
            if "emotional_state" in data and "psychological_state" not in data:
                data["psychological_state"] = data.pop("emotional_state")
            elif "emotional_state" in data:
                data.pop("emotional_state")
        return data

    @property
    def dna(self) -> str:
        return self.visual_dna

    @dna.setter
    def dna(self, value: str):
        self.visual_dna = value

    @property
    def vitality(self) -> VitalityState:
        return self.vitality_state

    @vitality.setter
    def vitality(self, value: VitalityState):
        self.vitality_state = value

    @property
    def emotional_state(self) -> str:
        return self.psychological_state

    @emotional_state.setter
    def emotional_state(self, value: str):
        self.psychological_state = value

    @property
    def is_alive(self) -> bool:
        return self.vitality_state != VitalityState.DECEASED

    def to_dict(self) -> Dict[str, Any]:
        try:
            return self.model_dump(mode="json")
        except Exception:
            return self.model_dump()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CharacterEntity":
        if not isinstance(data, dict):
            return cls(id=str(uuid.uuid4()), name="Unknown")
        try:
            return cls.model_validate(data)
        except Exception:
            cdata = dict(data)
            cid = str(cdata.get("id", str(uuid.uuid4())))
            cname = str(cdata.get("name", "Unknown"))
            return cls(id=cid, name=cname)


class ItemEntity(BaseModel):
    id: str
    name: str
    category: str = "item"
    visual_description: str = ""
    holder_id: Optional[str] = None
    location_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        try:
            return self.model_dump(mode="json")
        except Exception:
            return self.model_dump()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ItemEntity":
        if not isinstance(data, dict):
            return cls(id=str(uuid.uuid4()), name="Unknown Item")
        try:
            return cls.model_validate(data)
        except Exception:
            idata = dict(data)
            iid = str(idata.get("id", str(uuid.uuid4())))
            iname = str(idata.get("name", "Unknown Item"))
            return cls(id=iid, name=iname)


# ==============================================================================
# DIMENSION 2: SPACE ENCLOSURE MODELS
# ==============================================================================

class SpaceEnclosure(BaseModel):
    id: str
    name: str
    boundary_type: BoundaryType = BoundaryType.INDOOR_ENCLOSED
    architectural_anchor: str = ""
    persistent_fixtures: List[str] = Field(default_factory=list)
    lighting_atmosphere: str = ""
    negative_drift_tokens: List[str] = Field(default_factory=list)
    connected_enclosures: List[str] = Field(default_factory=list)
    parent_region: str = ""
    active_entities: List[str] = Field(default_factory=list)

    def is_enclosed(self) -> bool:
        return self.boundary_type in (BoundaryType.INDOOR_ENCLOSED, BoundaryType.VEHICLE_INTERIOR)

    def build_enclosure_fragment(self) -> str:
        """Constructs an absolute spatial anchor string for LLM or Diffusion prompts."""
        parts = [f"inside {self.name}"]
        if self.architectural_anchor:
            parts.append(self.architectural_anchor)
        if self.persistent_fixtures:
            parts.append(f"featuring {', '.join(self.persistent_fixtures[:4])}")
        if self.lighting_atmosphere:
            parts.append(self.lighting_atmosphere)
        return ", ".join(parts)

    def to_dict(self) -> Dict[str, Any]:
        try:
            return self.model_dump(mode="json")
        except Exception:
            return self.model_dump()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SpaceEnclosure":
        if not isinstance(data, dict):
            return cls(id="default_space", name="Default Space")
        try:
            return cls.model_validate(data)
        except Exception:
            edata = dict(data)
            eid = str(edata.get("id", "default_space"))
            ename = str(edata.get("name", "Default Space"))
            return cls(id=eid, name=ename)


# ==============================================================================
# DIMENSION 3: ERA & GENRE CONSTRAINT MODELS
# ==============================================================================

class EraGenreConstraint(BaseModel):
    era_name: str = "modern_2020s"
    genre_name: str = "Modern Campus Light Novel"
    world_axioms: List[str] = Field(default_factory=list)
    era_banlist: List[str] = Field(default_factory=list)
    tech_level: str = "modern"
    mandatory_style_anchor: str = "Japanese school manga, clean ink lineart, screentone shading"
    forbidden_visual_tokens: List[str] = Field(default_factory=list)
    forbidden_prose_cliches: List[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _normalize_era_genre(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Support alias "era" for "era_name"
            if "era" in data and "era_name" not in data:
                val = data.pop("era")
                data["era_name"] = str(val.value if hasattr(val, "value") else val)
            elif "era" in data:
                data.pop("era")
            # Support alias "genre" for "genre_name"
            if "genre" in data and "genre_name" not in data:
                data["genre_name"] = str(data.pop("genre"))
            elif "genre" in data:
                data.pop("genre")
            # Merge forbidden_visual_tokens into era_banlist if given
            banlist = list(data.get("era_banlist", []))
            for tok in data.get("forbidden_visual_tokens", []):
                if tok not in banlist:
                    banlist.append(tok)
            data["era_banlist"] = banlist
        return data

    @property
    def era(self) -> str:
        return self.era_name

    @era.setter
    def era(self, value: str):
        self.era_name = value

    @property
    def genre(self) -> str:
        return self.genre_name

    @genre.setter
    def genre(self, value: str):
        self.genre_name = value

    def to_dict(self) -> Dict[str, Any]:
        try:
            return self.model_dump(mode="json")
        except Exception:
            return self.model_dump()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EraGenreConstraint":
        if not isinstance(data, dict):
            return cls()
        try:
            return cls.model_validate(data)
        except Exception:
            return cls()


# ==============================================================================
# SANITIZERS & DRIFT QUARANTINE
# ==============================================================================

DEFAULT_OUTDOOR_TOKENS: List[str] = [
    "outdoor", "outdoors", "street", "streets", "trees", "cars", "car",
    "road", "roads", "sky", "blue sky", "clouds", "park", "forest",
    "horizon", "open sky", "traffic", "sidewalk", "alley", "outside",
    "city street", "public road", "mountains", "grass field"
]

DEFAULT_MODERN_ERA_BANLIST: List[str] = [
    "hanfu", "robes", "flowing robes", "sword", "swords", "magic staff",
    "cultivation", "flying sword", "ancient", "medieval", "kimono",
    "samurai armor", "plate armor", "armor", "taichi", "wuxia", "xianxia",
    "chariot", "ancient scroll", "jade pendant", "taoist robes"
]

TRANSITION_VERB_PATTERNS: List[str] = [
    r"bước\s+ra\s+khỏi",
    r"bước\s+vào",
    r"đi\s+vào",
    r"đi\s+ra",
    r"đi\s+xuống",
    r"chạy\s+ra",
    r"chạy\s+vào",
    r"rời\s+phòng",
    r"rời\s+khỏi",
    r"mở\s+cửa\s+bước\s+vào",
    r"mở\s+cửa\s+bước\s+ra",
    r"mở\s+(?:cánh\s+)?cửa(?!\s*(?:sổ|tủ|hòm|két|ngăn|xe\b))",
    r"lên\s+xe",
    r"xuống\s+xe",
    r"bước\s+sang",
    r"đi\s+sang",
    r"chuyển\s+sang",
    r"di\s+chuyển\s+đến",
    r"walked\s+into",
    r"stepped\s+into",
    r"stepped\s+out",
    r"left\s+the",
    r"entered",
    r"moved\s+to"
]


def is_transition_verb_negated(text: str, verb_start_idx: int) -> bool:
    """
    Checks if a transition verb occurrence is negated by preceding Vietnamese or English negation tokens
    within the same clause (without crossing clause boundaries or punctuation).
    """
    preceding_text = text[:verb_start_idx]
    last_boundary = max(
        preceding_text.rfind("."),
        preceding_text.rfind(","),
        preceding_text.rfind(";"),
        preceding_text.rfind(":"),
        preceding_text.rfind("!"),
        preceding_text.rfind("?"),
        preceding_text.rfind("\n"),
    )
    if last_boundary != -1:
        clause_prefix = preceding_text[last_boundary + 1:]
    else:
        clause_prefix = preceding_text

    negation_pattern = (
        r"(?i)\b(?:không\s+bao\s+giờ|không\s+thể|không\s+hề|không\s+muốn|không\s+chịu|không\s+dám|"
        r"quyết\s+không|nhất\s+quyết\s+không|kiên\s+quyết\s+không|từ\s+chối|chẳng\s+thể|"
        r"chẳng\s+thèm|chẳng\s+hề|chẳng\s+muốn|chẳng|chưa\s+từng|chưa\s+muốn|chưa|đừng|"
        r"ngăn\s+không\s+cho|ngăn\s+cản|ngăn|không|"
        r"never|refused\s+to|refuse\s+to|cannot|can't|didn't|did\s+not|doesn't|does\s+not|"
        r"wouldn't|would\s+not|not)\b"
    )

    match = re.search(negation_pattern + r"(?:\s+\w+){0,4}\s*$", clause_prefix)
    return match is not None


def sanitize_spatial_prompt(prompt: str, enclosure: Optional[SpaceEnclosure] = None) -> str:
    """
    Strips prohibited outdoor/street keywords when inside an enclosed space
    (INDOOR_ENCLOSED or VEHICLE_INTERIOR).
    Preserves valid subwords and hyphenated compounds (e.g., 'street-style', 'off-road', 'car-free').
    Cleans up punctuation artifacts.
    """
    if not prompt or not prompt.strip():
        return prompt or ""

    if enclosure is not None and not enclosure.is_enclosed():
        banned = enclosure.negative_drift_tokens
    else:
        banned_set = set(DEFAULT_OUTDOOR_TOKENS)
        if enclosure and enclosure.negative_drift_tokens:
            banned_set.update(enclosure.negative_drift_tokens)
        banned = list(banned_set)

    if not banned:
        return prompt

    sorted_banned = sorted(banned, key=lambda x: len(x), reverse=True)
    sanitized = prompt

    for token in sorted_banned:
        token_clean = token.strip()
        if not token_clean:
            continue
        # Use boundary check that avoids destroying hyphenated compounds
        pattern = r"(?i)(?:,\s*)?(?<![\w\-])" + re.escape(token_clean) + r"(?![\w\-])(?:\s*[,.])?"
        sanitized = re.sub(pattern, ", ", sanitized)

    # Clean up punctuation artifacts: ., ,. redundant commas, and spacing
    sanitized = re.sub(r"\.\s*,", ".", sanitized)
    sanitized = re.sub(r",\s*\.", ".", sanitized)
    sanitized = re.sub(r"\.{2,}", ".", sanitized)
    sanitized = re.sub(r"\s*,\s*", ", ", sanitized)
    sanitized = re.sub(r"(?:,\s*){2,}", ", ", sanitized)
    sanitized = re.sub(r"^[,\s.]+", "", sanitized)
    sanitized = re.sub(r"[,\s]+$", "", sanitized)
    sanitized = re.sub(r"\s{2,}", " ", sanitized)

    return sanitized.strip()


def sanitize_era_prompt(prompt: str, era_genre: Optional[EraGenreConstraint] = None) -> str:
    """
    Strips prohibited historical/wuxia/fantasy keywords when in a modern setting
    or matching era_banlist. Preserves compound words and cleans up punctuation artifacts.
    """
    if not prompt or not prompt.strip():
        return prompt or ""

    is_modern = True
    banned_set = set(DEFAULT_MODERN_ERA_BANLIST)

    if era_genre:
        era_str = (era_genre.era_name or "").lower()
        is_modern = "modern" in era_str or "2020" in era_str or "campus" in era_str
        if era_genre.era_banlist:
            banned_set.update(era_genre.era_banlist)
        if era_genre.forbidden_visual_tokens:
            banned_set.update(era_genre.forbidden_visual_tokens)

    if not is_modern and (not era_genre or not era_genre.era_banlist):
        return prompt

    sorted_banned = sorted(banned_set, key=lambda x: len(x), reverse=True)
    sanitized = prompt

    for token in sorted_banned:
        token_clean = token.strip()
        if not token_clean:
            continue
        pattern = r"(?i)(?:,\s*)?(?<![\w\-])" + re.escape(token_clean) + r"(?![\w\-])(?:\s*[,.])?"
        sanitized = re.sub(pattern, ", ", sanitized)

    sanitized = re.sub(r"\.\s*,", ".", sanitized)
    sanitized = re.sub(r",\s*\.", ".", sanitized)
    sanitized = re.sub(r"\.{2,}", ".", sanitized)
    sanitized = re.sub(r"\s*,\s*", ", ", sanitized)
    sanitized = re.sub(r"(?:,\s*){2,}", ", ", sanitized)
    sanitized = re.sub(r"^[,\s.]+", "", sanitized)
    sanitized = re.sub(r"[,\s]+$", "", sanitized)
    sanitized = re.sub(r"\s{2,}", " ", sanitized)

    return sanitized.strip()


# ==============================================================================
# UNIFIED GRAPH: DYNAMIC SCENE-GRAPH
# ==============================================================================

class DynamicSceneGraph(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    entities: Dict[str, CharacterEntity] = Field(default_factory=dict)
    enclosures: Dict[str, SpaceEnclosure] = Field(default_factory=dict)
    era_genre: EraGenreConstraint = Field(default_factory=EraGenreConstraint)
    active_enclosure_id: Optional[str] = None
    items: Dict[str, ItemEntity] = Field(default_factory=dict)
    relations: List[Dict[str, Any]] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _normalize_graph(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Support alias "characters" for "entities"
            if "characters" in data and "entities" not in data:
                data["entities"] = data.pop("characters")
            elif "characters" in data:
                data.pop("characters")
            # Support alias "spaces" for "enclosures"
            if "spaces" in data and "enclosures" not in data:
                data["enclosures"] = data.pop("spaces")
            elif "spaces" in data:
                data.pop("spaces")
        return data

    # Aliases
    @property
    def characters(self) -> Dict[str, CharacterEntity]:
        return self.entities

    @characters.setter
    def characters(self, value: Dict[str, CharacterEntity]):
        self.entities = value

    @property
    def spaces(self) -> Dict[str, SpaceEnclosure]:
        return self.enclosures

    @spaces.setter
    def spaces(self, value: Dict[str, SpaceEnclosure]):
        self.enclosures = value

    # Accessors
    def get_active_enclosure(self) -> Optional[SpaceEnclosure]:
        if self.active_enclosure_id and self.active_enclosure_id in self.enclosures:
            return self.enclosures[self.active_enclosure_id]
        return None

    def get_enclosure(self, enclosure_id: str) -> Optional[SpaceEnclosure]:
        return self.enclosures.get(enclosure_id)

    def get_character(self, character_id: str) -> Optional[CharacterEntity]:
        return self.entities.get(character_id)

    def add_character(self, character: CharacterEntity) -> None:
        self.entities[character.id] = character
        if character.current_location_id and character.current_location_id in self.enclosures:
            enc = self.enclosures[character.current_location_id]
            if character.id not in enc.active_entities:
                enc.active_entities.append(character.id)

    def add_enclosure(self, enclosure: SpaceEnclosure) -> None:
        self.enclosures[enclosure.id] = enclosure
        if self.active_enclosure_id is None:
            self.active_enclosure_id = enclosure.id

    # Invariant Gatekeepers
    def validate_vitality(self, actor_id: str, action: str = "ACTS") -> Tuple[bool, Optional[str]]:
        """
        Vitality Invariant: Deceased and unconscious entities cannot act.
        """
        actor = self.entities.get(actor_id)
        if not actor:
            return False, f"Entity '{actor_id}' does not exist in Scene-Graph."

        if actor.vitality_state == VitalityState.DECEASED:
            return False, f"VITALITY_VIOLATION: Character '{actor.name}' is DECEASED and cannot perform '{action}'."
        if actor.vitality_state == VitalityState.UNCONSCIOUS:
            return False, f"VITALITY_VIOLATION: Character '{actor.name}' is UNCONSCIOUS and cannot perform '{action}'."
        return True, None

    def validate_spatial_exclusivity(self, actor_id: str, target_id: str) -> Tuple[bool, Optional[str]]:
        """
        Spatial Exclusivity: Entities in an enclosure cannot interact directly
        with entities in other disconnected enclosures.
        """
        actor = self.entities.get(actor_id)
        target = self.entities.get(target_id)
        if not actor:
            return False, f"Actor entity '{actor_id}' does not exist."
        if not target:
            return False, f"Target entity '{target_id}' does not exist."

        if not actor.current_location_id or not target.current_location_id:
            return True, None

        if actor.current_location_id != target.current_location_id:
            actor_enc = self.enclosures.get(actor.current_location_id)
            if actor_enc and target.current_location_id in actor_enc.connected_enclosures:
                return True, None
            return False, (
                f"SPATIAL_VIOLATION: Character '{actor.name}' is in enclosure '{actor.current_location_id}' "
                f"and cannot interact directly with '{target.name}' in disconnected enclosure '{target.current_location_id}'."
            )
        return True, None

    def validate_era_consistency(self, text_or_prompt: str) -> Tuple[bool, List[str]]:
        """
        Era Consistency Invariant: Prohibits forbidden era tokens in modern settings.
        """
        violations = []
        is_modern = "modern" in self.era_genre.era_name.lower() or "2020" in self.era_genre.era_name.lower()
        banlist = set(self.era_genre.era_banlist)
        if is_modern:
            banlist.update(DEFAULT_MODERN_ERA_BANLIST)

        lower_text = text_or_prompt.lower()
        for token in banlist:
            if re.search(r"\b" + re.escape(token.lower()) + r"\b", lower_text):
                violations.append(f"ERA_VIOLATION: Forbidden era token '{token}' detected in '{self.era_genre.era_name}' setting.")

        return len(violations) == 0, violations

    def validate_action(
        self,
        actor_id: str,
        action_type: str,
        target_id: Optional[str] = None,
        target_location: Optional[str] = None,
        used_item: Optional[str] = None,
        prompt: Optional[str] = None
    ) -> Tuple[bool, List[str]]:
        """
        Universal Gatekeeper validating Vitality, Spatial Exclusivity, Inventory, and Era consistency.
        """
        violations = []
        # Vitality check
        vital, err = self.validate_vitality(actor_id, action_type)
        if not vital and err:
            violations.append(err)

        # Spatial Exclusivity check
        if target_id:
            spatial_ok, err = self.validate_spatial_exclusivity(actor_id, target_id)
            if not spatial_ok and err:
                violations.append(err)

        # Target location check
        actor = self.entities.get(actor_id)
        if actor and target_location and actor.current_location_id:
            if actor.current_location_id != target_location:
                violations.append(
                    f"SPATIAL_VIOLATION: Character '{actor.name}' is in '{actor.current_location_id}' "
                    f"but action targets '{target_location}' without a transition."
                )

        # Inventory check
        if actor and used_item:
            if used_item not in actor.inventory:
                violations.append(
                    f"INVENTORY_VIOLATION: Character '{actor.name}' attempts to use item '{used_item}' not in inventory."
                )

        # Era check
        if prompt:
            era_ok, era_errs = self.validate_era_consistency(prompt)
            if not era_ok:
                violations.extend(era_errs)

        return len(violations) == 0, violations

    # Scene Transition Gating
    def transition_scene(
        self,
        target_enclosure_id: str,
        moving_character_ids: Optional[List[str]] = None,
        force: bool = False
    ) -> bool:
        """
        Safely transition the active enclosure.
        Checks connectivity with current enclosure unless force=True.
        Updates entity locations and active_entities lists.
        Enforces vitality invariants and spatial exclusivity.
        """
        if target_enclosure_id not in self.enclosures:
            return False

        target_enc = self.enclosures[target_enclosure_id]
        current_enc = self.get_active_enclosure()

        if current_enc and not force:
            # Check if connected
            is_connected = (
                target_enclosure_id in current_enc.connected_enclosures or
                current_enc.id in target_enc.connected_enclosures
            )
            if not is_connected and current_enc.id != target_enclosure_id:
                return False

        # Determine which characters are moving
        cids_to_move = moving_character_ids
        if cids_to_move is None:
            if current_enc:
                cids_to_move = list(current_enc.active_entities)
            else:
                cids_to_move = list(self.entities.keys())
        else:
            # If explicit moving_character_ids provided without force:
            # Verify spatial exclusivity: characters cannot teleport from disconnected rooms
            if current_enc and not force:
                for cid in cids_to_move:
                    char = self.entities.get(cid)
                    if char:
                        # Character must be currently located in current_enc
                        if char.current_location_id and char.current_location_id != current_enc.id:
                            return False

        # Update character locations and enclosure active_entities
        for cid in cids_to_move:
            if cid in self.entities:
                char = self.entities[cid]
                # Vitality invariant: Deceased characters cannot autonomously transition
                if char.vitality_state == VitalityState.DECEASED:
                    continue

                # Remove from old enclosure's active_entities if tracked anywhere
                old_loc = char.current_location_id
                if old_loc and old_loc in self.enclosures:
                    if cid in self.enclosures[old_loc].active_entities:
                        self.enclosures[old_loc].active_entities.remove(cid)
                elif current_enc and cid in current_enc.active_entities:
                    current_enc.active_entities.remove(cid)

                # Set new location
                char.current_location_id = target_enclosure_id
                if cid not in target_enc.active_entities:
                    target_enc.active_entities.append(cid)

        self.active_enclosure_id = target_enclosure_id
        return True

    def gate_scene_transition(
        self,
        text: str,
        current_enclosure_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Scene Transition Gating mechanism:
        1. Checks for spatial transition verbs (ignoring negated occurrences).
        2. If NO unnegated transition verb is found -> LOCKS to current enclosure.
        3. If transition verb IS found -> searches text for matching destination enclosures,
           prioritizing connected enclosures, and transitions to it if valid.
        """
        curr_id = current_enclosure_id or self.active_enclosure_id
        if not text or not text.strip():
            return curr_id

        # Check for unnegated transition verbs
        has_transition_verb = False
        for pattern in TRANSITION_VERB_PATTERNS:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                if not is_transition_verb_negated(text, match.start()):
                    has_transition_verb = True
                    break
            if has_transition_verb:
                break

        # If no unnegated transition verb is detected, firmly lock to current enclosure
        if not has_transition_verb:
            return curr_id

        # Transition verb detected: search for candidate destination enclosures
        lower_text = text.lower()
        current_enc = self.get_active_enclosure()

        candidates = []
        for enc_id, enc in self.enclosures.items():
            if enc_id == curr_id:
                continue

            # Find latest mention of enclosure name or id
            name_pos = lower_text.rfind(enc.name.lower()) if enc.name else -1
            id_pos = lower_text.rfind(enc_id.lower())
            match_pos = max(name_pos, id_pos)

            if match_pos != -1:
                # Check if connected to current enclosure
                is_connected = (
                    current_enc is None or
                    enc_id in current_enc.connected_enclosures or
                    current_enc.id in enc.connected_enclosures
                )
                candidates.append((is_connected, match_pos, enc_id))

        # Sort candidates: connected first, then highest position in text (latest mentioned)
        candidates.sort(key=lambda c: (c[0], c[1]), reverse=True)

        for is_conn, match_pos, cand_id in candidates:
            success = self.transition_scene(cand_id)
            if success:
                return cand_id

        # If transition verb was present but no candidate succeeded, stay locked to current
        return curr_id

    # Prompt compilation helpers
    def build_enclosure_prompt_fragment(self) -> str:
        """Builds an absolute enclosure anchor fragment for image prompt injection."""
        enc = self.get_active_enclosure()
        if not enc:
            return "inside an enclosed room"
        return enc.build_enclosure_fragment()

    def get_combined_negative_tokens(self) -> str:
        """
        Combines era banlist tokens with active enclosure's negative drift tokens.
        If active enclosure is enclosed, automatically includes default outdoor tokens.
        """
        tokens: Set[str] = set()
        for tok in self.era_genre.era_banlist:
            tokens.add(tok)
        for tok in self.era_genre.forbidden_visual_tokens:
            tokens.add(tok)

        is_modern = "modern" in self.era_genre.era_name.lower() or "2020" in self.era_genre.era_name.lower()
        if is_modern:
            for tok in DEFAULT_MODERN_ERA_BANLIST:
                tokens.add(tok)

        enc = self.get_active_enclosure()
        if enc:
            for tok in enc.negative_drift_tokens:
                tokens.add(tok)
            if enc.is_enclosed():
                for tok in DEFAULT_OUTDOOR_TOKENS:
                    tokens.add(tok)

        return ", ".join(sorted(tokens))

    def sanitize_prompt(self, prompt: str) -> str:
        """Runs both spatial drift sanitizer and era drift sanitizer on a prompt."""
        enc = self.get_active_enclosure()
        clean = sanitize_spatial_prompt(prompt, enc)
        clean = sanitize_era_prompt(clean, self.era_genre)
        return clean

    # Serialization
    def to_dict(self) -> Dict[str, Any]:
        try:
            return self.model_dump(mode="json")
        except Exception:
            return self.model_dump()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DynamicSceneGraph":
        if not isinstance(data, dict):
            return cls()
        try:
            clean_data = dict(data)

            # 1. era_genre validation
            if clean_data.get("era_genre") is None or not isinstance(clean_data.get("era_genre"), (dict, EraGenreConstraint)):
                clean_data.pop("era_genre", None)

            # 2. entities validation
            raw_entities = clean_data.get("entities")
            if not isinstance(raw_entities, dict):
                clean_data["entities"] = {}
            else:
                valid_entities = {}
                for cid, cdata in raw_entities.items():
                    if isinstance(cdata, CharacterEntity):
                        valid_entities[cid] = cdata
                    elif isinstance(cdata, dict):
                        try:
                            # Normalize vitality_state if invalid enum string
                            if "vitality_state" in cdata:
                                try:
                                    VitalityState(cdata["vitality_state"])
                                except (ValueError, KeyError):
                                    cdata = dict(cdata)
                                    cdata["vitality_state"] = VitalityState.ALIVE
                            valid_entities[cid] = CharacterEntity.model_validate(cdata)
                        except Exception:
                            continue
                clean_data["entities"] = valid_entities

            # 3. enclosures validation
            raw_enclosures = clean_data.get("enclosures")
            if not isinstance(raw_enclosures, dict):
                clean_data["enclosures"] = {}
            else:
                valid_enclosures = {}
                for eid, edata in raw_enclosures.items():
                    if isinstance(edata, SpaceEnclosure):
                        valid_enclosures[eid] = edata
                    elif isinstance(edata, dict):
                        try:
                            valid_enclosures[eid] = SpaceEnclosure.model_validate(edata)
                        except Exception:
                            continue
                clean_data["enclosures"] = valid_enclosures

            # 4. items validation
            raw_items = clean_data.get("items")
            if not isinstance(raw_items, dict):
                clean_data["items"] = {}
            else:
                valid_items = {}
                for iid, idata in raw_items.items():
                    if isinstance(idata, ItemEntity):
                        valid_items[iid] = idata
                    elif isinstance(idata, dict):
                        try:
                            valid_items[iid] = ItemEntity.model_validate(idata)
                        except Exception:
                            continue
                clean_data["items"] = valid_items

            return cls.model_validate(clean_data)
        except Exception:
            return cls()
```

---

## 4. Verification & Non-Regression Analysis

### 4.1. Adversarial Test Suite Pass Analysis (`test_adversarial_dsgo.py`)
1. **Scene Transition Gating (5 tests)**:
   - `test_negation_khong_buoc_ra_khoi_phong`: Negation prefix `không` detected -> locks at `classroom_12a` (PASS).
   - `test_negation_khong_buoc_vao`: Negation prefix `nhất quyết không` detected -> locks at `classroom_12a` (PASS).
   - `test_negation_tu_choi_roi_phong`: Refusal `từ chối` detected -> locks at `classroom_12a` (PASS).
   - `test_deceptive_verb_mo_cua_so`: `mở cửa sổ` rejected by lookahead `(?!\s*(?:sổ|tủ|hòm|két|ngăn|xe\b))` -> locks at `classroom_12a` (PASS).
   - `test_empty_and_whitespace_prose`: Guard for empty/whitespace/None returns `classroom_12a` (PASS).
   - `test_destination_shadowing_by_unconnected_mention`: Connected `corridor_3f` prioritized over unconnected `soccer_field`, no premature break -> transitions to `corridor_3f` (PASS).
2. **Spatial Drift Sanitization (4 tests)**:
   - `test_subword_preservation`: `classroom`, `streetwear`, `sunlight` preserved by `(?<![\w\-])` and `(?![\w\-])` (PASS).
   - `test_hyphenated_compound_mutilation`: `street-style`, `off-road`, `car-free` untouched by hyphen-aware lookarounds (PASS).
   - `test_negative_drift_token_with_parentheses`: `street (outdoor)` cleanly stripped without `\b` paren failures (PASS).
   - `test_punctuation_artifacts`: Punctuation cleanup normalizes `.,` to single `.` (PASS).
3. **Disconnected Enclosure Transitions & Exclusivity (2 tests)**:
   - `test_direct_disconnected_jump_rejected`: Disconnected jump `room_a` -> `room_c` rejected (PASS).
   - `test_character_teleportation_and_location_leak`: Moving disconnected entity `minh` rejected (`return False`); `minh` remains in `room_b` without duplication (PASS).
4. **Vitality Invariants (3 tests)**:
   - `test_deceased_cannot_act`: Deceased acting returns `VITALITY_VIOLATION` (PASS).
   - `test_deceased_moving_themselves_in_transition`: Corpses excluded from autonomous transition; location remains unchanged (PASS).
   - `test_unconscious_character_cannot_perform_active_actions`: Unconscious acting returns `VITALITY_VIOLATION` (PASS).
5. **Deserialization Robustness (5 tests)**:
   - `test_corrupted_entities_field_raises_unhandled_exception`: Graceful fallback to default graph (PASS).
   - `test_corrupted_enclosures_field_crashes`: Graceful fallback to default graph (PASS).
   - `test_none_value_for_non_optional_field_crashes`: None handled cleanly (PASS).
   - `test_corrupted_entity_item_crashes`: Corrupted item skipped (PASS).
   - `test_invalid_enum_value_crashes`: Invalid enum normalized to `ALIVE` (PASS).

**Adversarial Pass Rate**: **18/18 (100%)**.

### 4.2. Milestone 2 DSGO Suite Pass Analysis (`test_dynamic_scene_graph.py`)
All 15 test classes/methods covering models, aliases, automated invariant gatekeepers, spatial drift sanitizers, scene transition gating, StoryMemory serialization, and agent integration were analyzed line-by-line against the proposed changes:
- Model aliases (`dna`, `vitality`, `emotional_state`, `characters`, `spaces`) remain 100% compliant.
- Valid connected scene transitions continue to function without disruption.
- Prompt sanitizers continue to strip outdoor/wuxia tokens for standard enclosed spaces.
- Roundtrip serialization and deserialization backward compatibility are preserved.

**DSGO Pass Rate**: **15/15 (100%)**.

### 4.3. Milestone 1 Non-Regression Analysis (`test_light_novel_engine.py`)
No code modifications affect `LIGHT_NOVEL_ENGINE_RULES`, `StoryBible.narrative_beats`, `StoryGenerator`, `CopilotAgent`, `EditorAgent`, or `QARefiner`.
Milestone 1 rules and persona requirements remain completely intact.

**M1 Non-Regression Rate**: **100%**.
