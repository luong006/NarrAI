# NarrAI Round 6 Testing Infrastructure Specification (`TEST_INFRA.md`)

**Track**: E2E Testing & Quality Assurance (Milestone 5)  
**Author**: `test_writer_r6` (teamwork_preview_test_writer)  
**Date**: 2026-09-30  
**Parent Orchestrator**: `orchestrator_r6_1` (Conversation ID: `92e67f82-c02c-4fa1-9967-5963454f8d77`)  
**Scope Directory**: `backend/tests/`  

---

## 1. Executive Overview

The NarrAI Round 6 upgrade introduces critical improvements across five major system dimensions:
1. **Copilot Flexible Manuscript Surgery**: Exact chapter targeting ("sửa Chương X"), `instruction` parameter activation, `selectedText` / `cursorPosition` targeting from frontend, elimination of the Path B 2000-char manuscript truncation bug, and non-bunching intermediate heading preservation.
2. **Vietnamese Historical Canon & Copyright Guardrails**: Expansion from 6 to 31 heroes across 6 historical epochs, AI semantic classification to defeat regex evasion, post-generation validation wired into generation pipelines, auto-detection of 3 narrative modes (`CHINH_SU`, `DA_SU`, `HU_CAU_TU_DO`), and commercial IP detection with fanfiction disclaimer attachment on publish.
3. **Social Network Expansion**: Follow/Unfollow & prioritized following feed, threaded comments with `parent_comment_id`, bookmarks/personal library CRUD with category/tag filtering, notification lifecycle, content reporting, author profiles with stats, and trending leaderboards with time-decayed velocity scoring.
4. **Database WAL Mode & High-Performance Indexing**: SQLite WAL mode (`PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL;`), composite indexes on hot query paths, and FastAPI `GZipMiddleware(minimum_size=500)` payload compression.
5. **TensorFlow.js Hybrid Architecture**: Exporting 128-dimensional concept vectors (`GET /api/recommender/export-vectors`) for client-side on-device recommendation re-ranking and MMR search.

To ensure strict compliance with the authoritative user request (`ORIGINAL_REQUEST.md`) and architecture contracts (`PROJECT.md`), the test track establishes an opaque-box, requirement-driven, 4-tier testing methodology.

---

## 2. 4-Tier Testing Methodology

```
┌────────────────────────────────────────────────────────┐
│ Tier 4: Adversarial & E2E Real-World User Journeys     │
│ (Regex evasion, Path B truncation defense, Cold-start)  │
├────────────────────────────────────────────────────────┤
│ Tier 3: Cross-Feature Integration Contracts            │
│ (Slicing + Heading Preservation, Canon + Semantic AI)  │
├────────────────────────────────────────────────────────┤
│ Tier 2: Boundary & Corner Cases                        │
│ (Multi-chapter novels, whitespace limits, delta sync)  │
├────────────────────────────────────────────────────────┤
│ Tier 1: Isolated Feature & Happy Path Coverage         │
│ (Chapter slicing, WAL mode pragma, 128-dim vectors)   │
└────────────────────────────────────────────────────────┘
```

### Tier 1: Isolated Feature Coverage
- Each feature is tested in isolation against its interface contract.
- Pure unit tests with mocked transport boundaries (LLM calls mocked with deterministic JSON responses).
- Database operations executed on transactional in-memory or isolated temporary databases.

### Tier 2: Boundary & Edge Conditions
- Extreme string lengths (stories > 5000 chars, empty instructions, non-existent chapter numbers like "sửa Chương 99").
- Multiple identical phrases across a novel disambiguated via `cursorPosition`.
- Whitespace resilience (leading/trailing spaces in text selections).
- Zero-count states (empty database, delta sync with future timestamps).

### Tier 3: Cross-Feature Integration
- Interaction between `SemanticChunkSlicer` and `HeadingPreservationEngine` during multi-chapter edits.
- Correlation between author following and feed filtering (`feed?filter=following`).
- Co-existence of historical gatekeeper checks with commercial IP fanfiction detection during story publication.

### Tier 4: Adversarial & Real-World User Scenarios
- **Regex Evasion Attacks**: Metaphorical framing ("ngọn cờ thêu sáu chữ vàng chìm nghỉm..."), inverted subjects ("quân Mông Cổ ca khúc khải hoàn trên sông Bạch Đằng..."), and historical defamation outside the hardcoded 6-hero list.
- **Path B Context Loss Defense**: Verifying that falling through to the Master Controller on a 6000-character story preserves all preceding chapters.
- **Client MMR Simulation**: Simulating on-device TF.js MMR re-ranking on exported 128-dim vectors.

---

## 3. Test Suites Inventory & Coverage Matrix

| Test Suite File | Feature IDs | Targeted Modules | Test Count | Key Coverage Areas |
|---|---|---|:---:|---|
| `backend/tests/test_round6_copilot_surgery.py` | Features 1–5 | `agents/copilot_agent.py` | 13 | Chapter targeting ("sửa Chương X"), slicer `instruction` utilization, `selectedText` & `cursorPosition` targeting, Path B non-truncation (>5000 chars preserved), intermediate heading relative ordering. |
| `backend/tests/test_round6_historical_copyright.py` | Features 9–12, 14–15 | `services/ontology.py`, `agents/story_generator.py` | 18 | 31-hero canon across 6 epochs, rejection of historical distortion ("Trần Hưng Đạo thua Bạch Đằng"), AI semantic classifier regex evasion, 3 narrative modes auto-detect, commercial IP detection & fanfiction disclaimer. |
| `backend/tests/test_round6_social_features.py` | Features 16–22 | `db/models.py`, `routers/social_router.py` | 16 | Follow/Unfollow CRUD & following feed, threaded comments (`parent_comment_id`), bookmarks/library, notification lifecycle, content reports, author profiles, trending leaderboards with velocity formula. |
| `backend/tests/test_round6_wal_performance.py` | Features 6–8 | `db/models.py`, `main.py` | 8 | SQLite WAL mode (`PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL;`), indexes on Comic, ComicPanel, SocialPost, composite indexes, FastAPI GZipMiddleware compression on payloads >= 500 bytes. |
| `backend/tests/test_round6_tfjs_export.py` | Features 26, 28, 29 | `services/recommender_service.py`, `routers/social_router.py` | 7 | `GET /api/recommender/export-vectors`, 128-dim vector shape verification, L2 normalization (`norm ≈ 1.0`), pagination (`limit`), delta sync (`since`), client MMR simulation. |

**Total Round 6 Test Cases**: **62 test cases** across 5 test suites.

---

## 4. Authoritative Expected Output Derivation

Every expected value and assertion is derived strictly from specifications:

1. **Chapter Targeting Slicer Boundary**:
   - `story = prefix + window_to_edit + suffix` when window is untouched.
   - For "sửa Chương 2": `slice.prefix` contains Chapter 1; `slice.window_to_edit` starts at `## Chương 2`; `slice.suffix` starts at `## Chương 3`.
2. **Intermediate Heading Preservation**:
   - For multi-chapter texts with $H_1, H_2, H_3$, relative character offsets satisfy: $\text{pos}(H_1) < \text{pos}(H_2) < \text{pos}(H_3)$.
   - Headings are placed at proportional paragraph breaks, not bunched at the very top.
3. **Historical Grounding Invariant Rules**:
   - `validate_historical_invariants(text, mode=CHINH_SU)` returns `(False, [violations])` if any hero defeat pattern or battle loss regex matches.
   - Compliant history returns `(True, [])`.
   - `HU_CAU_TU_DO` mode returns `(True, [])` unconditionally.
4. **Trending Velocity Mathematical Formula**:
   $$\text{TrendingScore}(p) = \frac{3 \cdot \text{likes} + 5 \cdot \text{comments} + 0.5 \cdot \text{views} + 4 \cdot \text{completions}}{(\text{age\_in\_hours} + 2)^{1.4}}$$
5. **Vector Dimensions & Normalization**:
   - $\text{dim}(v) = 128$.
   - $\sqrt{\sum_{i=1}^{128} v_i^2} = 1.0 \pm 0.05$.
6. **SQLite WAL Mode**:
   - `PRAGMA journal_mode;` returns `'wal'` on disk-backed DB.
   - `PRAGMA synchronous;` returns `'1'` or `'NORMAL'`.
7. **FastAPI GZip Compression Threshold**:
   - Body length $< 500$ bytes $\rightarrow$ `Content-Encoding` has no `gzip`.
   - Body length $\ge 500$ bytes with `Accept-Encoding: gzip` $\rightarrow$ `Content-Encoding: gzip`.

---

## 5. Independent Verification & Execution Commands

### A. Run Round 6 Test Suites Individually
```powershell
# 1. Copilot Surgery & Dynamic Slicing
python backend/tests/test_round6_copilot_surgery.py

# 2. Historical Canon & Commercial IP Protection
python backend/tests/test_round6_historical_copyright.py

# 3. Social Network Expansion
python backend/tests/test_round6_social_features.py

# 4. SQLite WAL Mode & Performance
python backend/tests/test_round6_wal_performance.py

# 5. TensorFlow.js 128-Dim Vector Export
python backend/tests/test_round6_tfjs_export.py
```

### B. Run All Round 6 Test Suites via Unittest Discovery
```powershell
python -m unittest discover -s backend/tests -p "test_round6_*.py" -v
```

### C. Run Full Regression Test Suite
```powershell
python backend/tests/run_all_tests.py
```

---

## 6. Escalations & Findings for Implementing Agents

During test suite design and codebase inspection, the following critical implementation details were identified for the implementing agents:

1. **`SemanticChunkSlicer.slice_manuscript` signature expansion**:
   - Currently accepts `(cls, story: str, target: Any, instruction: str = "")`.
   - Must be updated in `copilot_agent.py` to support `selected_text: str = ""` and `cursor_position: Optional[int] = None` (or kwargs) and actively parse chapter numbers from `instruction` via regex `r'(?:sửa|chỉnh\s*sửa|viết\s*lại|chương)\s*(\d+)'`.
2. **`HeadingPreservationEngine.preserve_headings` proportional placement**:
   - Currently prepends all missing headings to the very top in lines 330–338, which causes reverse bunching (`Chương 3\n\nChương 2\n\nChương 1`).
   - Must calculate proportional paragraph positions: $k = \max(1, \text{round}(r_i \times \text{len}(\text{paragraphs})))$ to restore intermediate headings between chapters.
3. **`VIETNAMESE_HISTORICAL_CANON` expansion**:
   - Currently has 6 heroes. Must be expanded to $\ge 20$ (target 31) entries with `invariants` and `defeat_regex`.
4. **Wiring `validate_historical_invariants` post-generation**:
   - Must be invoked inside `story_generator.py` and `copilot_agent.py` so that generation/editing is rejected and coins are refunded on violation.
5. **FastAPI GZipMiddleware**:
   - Must be added after `CORSMiddleware` in `backend/main.py`: `app.add_middleware(GZipMiddleware, minimum_size=500)`.
