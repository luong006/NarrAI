# Handoff Report: Milestone 3 Vulnerabilities Remediation Blueprint

- **Agent**: `explorer_r2_m3_fix` (Explorer / Read-Only Investigator)
- **Target**: Milestone 3 Remediation Blueprint (R3: Text-to-Image Sync & Manga Hallucination Elimination)
- **Working Directory**: `e:\NarrAI\.agents\explorer_r2_m3_fix`
- **Workspace**: `e:\NarrAI`
- **Parent ID**: `ec442b00-f5a6-451c-96d9-4ecd040bf695`
- **Date**: 2026-09-20T18:38:00Z
- **Deliverable**: `e:\NarrAI\.agents\explorer_r2_m3_fix\report.md`

---

## 1. Observation

Direct code analysis of `backend/agents/comic_agent.py`, `backend/services/cloudflare_ai.py`, and `backend/tests/test_challenger_r2_m3_1_adversarial.py`:

1. **Negation Blindness & Semantic Action Overlap (`comic_agent.py:195-255`)**:
   - `extract_action_from_prose()` iterates over `ACTION_GESTURE_MAPPINGS` and calls `re.search(pattern, text_lower)` without inspecting the preceding words for negation particles.
   - For `prose = "An tuyệt đối không nhìn ra cửa sổ mà chăm chú nhìn lên bảng đen"`, Pattern 2 matches `"nhìn ra cửa sổ"` and returns `'sitting beside the large classroom window...'`, directly hallucinating the negated action.
   - Pattern 1 contains `|\b(?:cúi đầu|cặm cụi)\b` at line 198, causing greeting bows (`"An cúi đầu lễ phép chào cô giáo"`) to trigger writing poses (`"sitting at wooden student desk... writing attentively"`).
   - Pattern 4 contains `|kinh ngạc)` at line 216, causing internal thoughts (`"Một thoáng kinh ngạc lướt qua suy nghĩ của An"`) to trigger physical desktop slams (`"standing up abruptly... hands braced against wooden desktop"`).
   - Pattern 6 has optional desk anchors `(?:xuống)?\s*(?:bàn)?` at line 228, causing isolated teacher sighs (`"Thầy giáo đứng trước lớp thở dài một tiếng"`) to trigger desk head-down poses (`"resting head down on folded arms upon wooden desk"`).

2. **Spatial Sanitizer Regex Edge Cases (`comic_agent.py:121-193`)**:
   - `SPATIAL_ENCLOSURES["classroom"]["forbidden_spatial_tokens"]` at lines 132-135 omits `"sword"`, `"blade"`, `"weapon"`.
   - The modifier whitelist `(?:busy|moving|crowded|noisy|outdoor|distant|speeding|passing)?` at line 181 omits `"ancient"`, `"stone"`, `"old"`, `"abandoned"`, `"wooden"`. Stripping `"palace"` from `"ancient palace"` leaves dangling `"ancient"`.
   - Prepositions `at`, `to`, `through`, `into`, `outside`, `towards` are missing from the preposition regex at line 181. Stripping `"speeding car"` from `"looking at the speeding car"` leaves dangling `"at the"`.
   - Plural pattern `\b{token}s?\b` fails on sibilant plurals like `"buses"`.
   - Line 188 only strips extra spaces (`\s{2,}`), leaving consecutive orphaned commas `", ,"` in the sanitized prompt when a token is removed from a comma-separated list.

3. **CLIP 77-Token Budget Overrun (`comic_agent.py:783-800`)**:
   - In `_validate_panels()`, prompts are assembled as:
     `STYLE_PREFIX` (~28 tokens) + `injected_dnas` (~55 tokens) + `clean_prompt` (~25 tokens) + `action_desc` (~15 tokens) + `setting: {setting_anchor}` (~40 tokens) + `STYLE_SUFFIX` (~35 tokens).
   - Total length exceeds 170 BPE tokens. Under standard CLIP ViT-L/14 tokenizers (77-token ceiling), `setting: {setting_anchor}` begins at token index 120+, resulting in 100% loss of spatial conditioning in diffusion attention.

4. **Pollinations Fallback Hard Slicing (`cloudflare_ai.py:153`)**:
   - Line 153 executes `bw_prompt = f"... {prompt[:300]}, screentone, no color"`.
   - `prompt[:300]` slices mid-word through character DNA, omitting `setting: {setting_anchor}` and `action_desc`.

5. **Adversarial Test Suite Status (`test_challenger_r2_m3_1_adversarial.py`)**:
   - The 11 tests in `test_challenger_r2_m3_1_adversarial.py` currently assert the presence of bugs (e.g. `self.assertIn("ancient", res.lower())`, `self.assertIn("window", act.lower())`).

---

## 2. Logic Chain

1. **Step 1 (Semantic Accuracy)**: Because Vietnamese negation words (`không`, `chẳng`, `chưa`, `đừng`, `cấm`, `ngừng`, `thôi`, `chớ`) precede verbs within the same clause, implementing `is_action_negated()` with clause boundary detection (`CLAUSE_DELIMITERS_PATTERN`) stops negated actions from triggering while allowing positive subsequent clauses (`mà chăm chú nhìn lên bảng đen`) to match.
2. **Step 2 (Regex Hardening)**: Removing loose wildcards (`|\b(?:cúi đầu|cặm cụi)\b`, `|kinh ngạc)`) and requiring desk context for `thở dài` ensures only genuine physical student actions map to manga poses.
3. **Step 3 (Quarantine Completeness)**: Adding missing modifiers (`ancient`, `stone`, `old`, `abandoned`), prepositions (`at`, `to`, `through`), plural inflection `(?:es|s)?`, and comma collapsing (`re.sub(r'[,.\s]*,[,.\s]*', ', ', clean)`) ensures zero syntax artifacts or dangling tokens remain.
4. **Step 4 (CLIP Attention Alignment)**: Moving `setting: {setting_anchor}` and `action_desc` immediately after `STYLE_PREFIX` places them at tokens 22-65. This guarantees that diffusion models attend to both room architecture and character pose within the 77-token window before character clothing details.
5. **Step 5 (Fallback Continuity)**: Introducing `format_pollinations_prompt(prompt, max_len=500)` with delimiter-aware truncation and setting anchor preservation prevents broken words and guarantees spatial anchoring during Cloudflare outages.
6. **Step 6 (Test Inversion)**: Inverting the assertions in `test_challenger_r2_m3_1_adversarial.py` creates an automated regression and adversarial verification suite for the remediated codebase.

---

## 3. Caveats

- **No Source Modification**: As an Explorer (read-only investigator), no project source files or test files were directly edited. All exact blueprints and drop-in code implementations are documented in `e:\NarrAI\.agents\explorer_r2_m3_fix\report.md`.
- **Dynamic Scene Graph Integration**: The DSGO architectural bridge (`StoryMemory.dynamic_scene_graph` query from `comic_agent.py`) is scheduled for Milestone 4 and was excluded from this M3 visual prompt remediation scope as agreed in Reviewer 2's handoff.

---

## 4. Conclusion

A comprehensive, production-ready remediation blueprint has been formulated and documented in `e:\NarrAI\.agents\explorer_r2_m3_fix\report.md`:
- **Blueprint 1**: Complete implementation of `is_action_negated()` and tightened `ACTION_GESTURE_MAPPINGS` (Patterns 1, 4, 6) in `comic_agent.py`.
- **Blueprint 2**: Enhanced `SPATIAL_ENCLOSURES` and robust `sanitize_spatial_prompt()` with prepositions, modifiers, plural `(?:es|s)?`, and comma collapsing.
- **Blueprint 3**: CLIP 77-token layout prioritizing `setting:` anchor and `action_desc` at tokens 22-65.
- **Blueprint 4**: `format_pollinations_prompt()` in `cloudflare_ai.py` with clean delimiter slicing and spatial preservation.
- **Blueprint 5**: Complete drop-in code for `test_challenger_r2_m3_1_adversarial.py` asserting fixed, robust behavior.

---

## 5. Verification Method

Once the implementer applies the blueprint from `report.md`:

```bash
# 1. Compilation
python -m py_compile backend/agents/comic_agent.py backend/services/cloudflare_ai.py backend/tests/test_challenger_r2_m3_1_adversarial.py backend/tests/test_comic_modern_school_sync.py

# 2. Hardened Adversarial Suite
python -m unittest backend/tests/test_challenger_r2_m3_1_adversarial.py -v

# 3. Existing Milestone 3 Sync Suite
python -m unittest backend/tests/test_comic_modern_school_sync.py -v

# 4. Regression Suites
python -m unittest backend/tests/test_comic_dna_seed.py -v
python -m unittest backend/tests/test_comic_zero_truncation.py -v
python -m unittest backend/tests/test_challenger_m3_2_stress.py -v
```

### Invalidation Conditions:
- Any occurrence of dangling `"ancient"` or trailing `"at the"` in sanitized spatial prompts.
- `extract_action_from_prose()` returning a positive window pose for `"không nhìn ra cửa sổ"`.
- Setting anchor positioned at index > `len(STYLE_PREFIX) + 50` in validated panel prompts.
