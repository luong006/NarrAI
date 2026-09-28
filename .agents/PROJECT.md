# Project: NarrAI Comprehensive Upgrade (R1-R7)

## Architecture
- **Internationalization & Presentation Layer (`frontend/src/`)**:
  - 100% Bilingual (Anh ⟷ Việt) support across the entire user experience. Zero hardcoded UI strings.
  - Unified Toast Notification System (`ToastProvider`, `useToast`) replacing browser `alert()`.
  - Full Name (`full_name`) display and localized form fields.
  - Multi-tier CSS monochrome filter backup in `frontend/src/app/globals.css`.
- **Authentication & Security Layer (`backend/db/models.py`, `backend/auth.py`, `backend/main.py`, `frontend/src/components/modals/AuthModal.tsx`)**:
  - `User.full_name` column with automatic inspection-based database upgrade for SQLite/PostgreSQL.
  - Strict 5-point bank-grade password security (`validate_bank_password`): min length 8-12, >=1 uppercase, >=1 lowercase, >=1 digit, >=1 special character, no whitespace.
  - Real-time animated Password Strength Meter and reactive 5-item visual checklist in `AuthModal.tsx`.
  - Thread-safe brute-force rate limiter (`LoginRateLimiter`) with 5 failed attempts lockout (HTTP 429).
- **Caching & Resilience Layer (`backend/services/cache_service.py`, `backend/main.py`)**:
  - Dual-mode `CacheManager` with connection-pooled `RedisCache` and zero-dependency in-process `ThreadSafeMemoryCache` (OrderedDict + RLock with per-key TTL and LRU eviction).
  - Graceful uninterrupted fallback to memory cache if Redis is offline or unavailable.
  - Session and draft caching guaranteeing query latency < 20ms (typically < 0.1ms).
- **AI Co-pilot & Direct Editing Layer (`backend/agents/copilot_agent.py`)**:
  - Bilingual intent classification (`_is_direct_edit_request`) supporting English quick prompts ("Rewrite in a darker...", "Write a completely different opening...", etc.) and Vietnamese commands.
  - Safe token sliding window: maximum 8,000 characters manuscript context, leaving >= 4,000 completion tokens.
  - Prompt deduplication in Master Controller Step 2 to eliminate token overflow and truncated JSON completions.
  - Multi-tier model fallback chain (`openai/gpt-oss-120b` -> `llama-3.3-70b-versatile` -> `llama-3.1-8b-instant`).
- **Modern Novel Engine Layer (`backend/agents/story_generator.py`, `editor_agent.py`, `copilot_agent.py`)**:
  - Comprehensive Anti-Cliché Banlist eliminating AI tropes ("nhanh như nhịp tim chậm rãi", "khoảng trống trong lòng", "nỗi lo đè nặng lên vai", "thở dài giọng nhẹ", empty philosophical preaching).
  - 4-Pillar Show Don't Tell rules (visceral physical sensations, micro-actions, micro-expressions, physical object interactions).
  - In Medias Res dramatic opening and sharp dialogue with subtext.
  - Programmatic compliance validator (`validate_anti_cliche_compliance`) guaranteeing 0 violations.
- **Comic Visual DNA & 100% Monochrome Manga Pipeline (`backend/agents/comic_agent.py`, `backend/services/cloudflare_ai.py`, `backend/main.py`)**:
  - CLIP 77-Token Budget Prioritization: Character Visual DNA (Face, Hair, Outfits) placed at Position 1 (tokens 15-42) directly following the style prefix.
  - First-Person pronoun ("tôi", "mình") mapping to lead protagonist and sequential panel character context tracking.
  - Server-side Pillow post-processing pipeline (`process_manga_monochrome`: `Image.convert('L')` + `ImageOps.autocontrast`) stripping 100% color.
  - Elimination of `RedirectResponse` in `/api/comic/image/{panel_id}`; server directly returns HTTP 200 with local `get_guaranteed_monochrome_fallback` on any network failure (0% broken image icons).

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | 100% Bilingual Dictionary Expansion | Add 45+ missing translation keys across `vi` and `en` in `frontend/src/lib/i18n.ts` | M1 | ORIGINAL_REQUEST R1 |
| 2 | Unified Bilingual Toast System | Build `ToastProvider` and `useToast()` in frontend, replacing 100% of browser `alert()` calls | M1 | ORIGINAL_REQUEST R1 |
| 3 | Frontend Hardcoded String Elimination | Eliminate 35+ hardcoded strings across `ThemeToggle`, `LandingView`, `Phase1Idea`, `Phase2Interview`, `Phase3Controls`, `AICopilotPanel`, `ComicViewer`, `error.tsx`, `api.ts` | M1 | ORIGINAL_REQUEST R1 |
| 4 | User Full Name DB Auto-Migration | Add `full_name` column to `User` in `backend/db/models.py` with backward-compatible auto-migration | M1 | ORIGINAL_REQUEST R2 |
| 5 | Bank-Grade 5-Point Password Validator | Implement `validate_bank_password` in `backend/auth.py` and frontend validation | M1 | ORIGINAL_REQUEST R2 |
| 6 | Brute-Force Rate Limiter | Implement `LoginRateLimiter` in `backend/auth.py` (5 attempts / 5 min -> HTTP 429) | M1 | ORIGINAL_REQUEST R2 |
| 7 | AuthModal Real-Time Security Overhaul | Add Full Name, Confirm Password, Strength Meter (0-100%), and 5-rule checklist to `AuthModal.tsx` | M1 | ORIGINAL_REQUEST R2 |
| 8 | Dual-Mode CacheManager Service | Build `backend/services/cache_service.py` with `ThreadSafeMemoryCache` (TTL/LRU) and `RedisCache` fallback | M2 | ORIGINAL_REQUEST R3 |
| 9 | Backend Draft & Session Cache Integration | Integrate `CacheManager` into `backend/main.py` for user tokens, story sessions, and draft retrieval (< 20ms) | M2 | ORIGINAL_REQUEST R3 |
| 10 | Co-pilot Bilingual Intent Classifier | Expand `_is_direct_edit_request` in `backend/agents/copilot_agent.py` with English command phrases and edit verbs | M2 | ORIGINAL_REQUEST R4 |
| 11 | Co-pilot Context Budgeting & Deduplication | Enforce 8,000-char context window in direct edit and strip duplicated story payload in Step 2 | M2 | ORIGINAL_REQUEST R4 |
| 12 | Multi-Tier Co-pilot Model Fallback | Implement fallback chain (`openai/gpt-oss-120b` -> `llama-3.3-70b-versatile` -> `llama-3.1-8b-instant`) in `CopilotAgent` | M2 | ORIGINAL_REQUEST R4 |
| 13 | Comprehensive Anti-Cliché Banlist | Codify banned AI tropes and oxymoronic cliches in `story_generator.py`, `editor_agent.py`, and `copilot_agent.py` | M3 | ORIGINAL_REQUEST R5 |
| 14 | 4-Pillar Show Don't Tell & In Medias Res | Codify visceral physical sensations, micro-actions, micro-expressions, physical interactions, and In Medias Res | M3 | ORIGINAL_REQUEST R5 |
| 15 | Programmatic Anti-Cliché Validator | Implement `validate_anti_cliche_compliance` in `story_generator.py` guaranteeing 0 violations | M3 | ORIGINAL_REQUEST R5 |
| 16 | CLIP 77-Token DNA Prioritization | Reorder prompt assembly in `comic_agent.py`: Character Visual DNA at Position 1 (tokens 15-42) ahead of action and setting | M3 | ORIGINAL_REQUEST R6 |
| 17 | First-Person Pronoun & Sequential Identity | Add "tôi", "mình" to aliases and maintain sequential panel character memory in `comic_agent.py` | M3 | ORIGINAL_REQUEST R6 |
| 18 | Pillow Monochrome Post-Processing | Implement `process_manga_monochrome` (`Image.convert('L')` + `autocontrast`) in `cloudflare_ai.py` | M3 | ORIGINAL_REQUEST R7 |
| 19 | Zero-Redirect & Guaranteed Local Fallback | Eliminate `RedirectResponse` in `backend/main.py`; serve `get_guaranteed_monochrome_fallback` directly on error | M3 | ORIGINAL_REQUEST R7 |
| 20 | Multi-Layer Frontend Grayscale Defense | Add CSS grayscale filter in `frontend/src/app/globals.css` | M3 | ORIGINAL_REQUEST R7 |
| 21 | Full Verification & Forensic Quality Gate | Verify `py_compile`, `npm run build`, full unit/integration test suite, and forensic integrity audit | M4 | ORIGINAL_REQUEST Criteria |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | M1: 100% Bilingual i18n & Bank-Grade Auth | Features 1, 2, 3, 4, 5, 6, 7 (`i18n.ts`, `Toast.tsx`, `AuthModal.tsx`, all UI components, `models.py`, `auth.py`, `main.py`) | none | DONE |
| 2 | M2: Redis Cache Layer & Resilient AI Co-pilot | Features 8, 9, 10, 11, 12 (`cache_service.py`, `copilot_agent.py`, `main.py`) | none | IN_PROGRESS |
| 3 | M3: Professional Novel Engine & Manga Consistency | Features 13, 14, 15, 16, 17, 18, 19, 20 (`story_generator.py`, `comic_agent.py`, `cloudflare_ai.py`, `editor_agent.py`, `main.py`, `globals.css`) | none | IN_PROGRESS |
| 4 | M4: System Verification & Forensic Integrity Gate | Feature 21 (Full unit/adversarial test suite, py_compile, npm run build, auditor veto check) | M1, M2, M3 | PLANNED |

## Interface Contracts
### Cache Service ↔ Backend Endpoints
- `CacheManager.get_session(session_id: str) -> Optional[dict]`
- `CacheManager.set_session(session_id: str, memory_dict: dict, ttl: int = 86400)`
- `CacheManager.get_draft(story_id: int) -> Optional[dict]`
- `CacheManager.set_draft(story_id: int, story_dict: dict, ttl: int = 3600)`
- `CacheManager.benchmark_latency(iterations: int = 100) -> dict` (reports avg latency < 20ms)

### Auth ↔ Database & Security
- `validate_bank_password(password: str) -> Tuple[bool, str, str]`
- `LoginRateLimiter.record_failure(key: str) -> Tuple[bool, int]`
- `User`: `full_name = Column(String(100), nullable=True, default="")`

### Story Generator ↔ Quality Gate
- `validate_anti_cliche_compliance(text: str) -> Tuple[bool, List[str]]` (returns (True, []) for 0 violations)

### Comic Agent ↔ Image Pipeline
- `image_prompt`: `f"{STYLE_PREFIX}{character_dna}, {action_desc}, setting: {setting_anchor}, {clean_prompt}{STYLE_SUFFIX}"`
- `process_manga_monochrome(image_bytes: bytes) -> bytes` (100% mode 'L' grayscale, no color leakage)
- `get_guaranteed_monochrome_fallback(panel_index: int) -> bytes` (always returns valid 800x800 JPEG bytes)
- `/api/comic/image/{panel_id}`: always returns HTTP 200 with `media_type="image/jpeg"` (zero external 307 redirects)

## Code Layout
- `backend/services/cache_service.py`: Redis cache + in-memory LRU/TTL fallback.
- `backend/agents/copilot_agent.py`: Bilingual intent classifier, token budgeting, multi-model fallback.
- `backend/agents/story_generator.py`: Anti-cliché banlist, 4-pillar Show Don't Tell, In Medias Res, compliance validator.
- `backend/agents/comic_agent.py`: CLIP 77-token character DNA prioritization, pronoun aliases, sequential panel memory.
- `backend/services/cloudflare_ai.py`: Server-side Pillow monochrome processing, guaranteed local fallback image.
- `backend/auth.py`: Bank password validator, brute-force rate limiter.
- `backend/db/models.py`: User model with `full_name` auto-migration.
- `frontend/src/lib/i18n.ts`: Expanded bilingual dictionaries (vi & en).
- `frontend/src/components/ui/Toast.tsx`: Unified bilingual toast notification system.
- `frontend/src/components/modals/AuthModal.tsx`: Bank-grade auth UI with Strength Meter and checklist.
- `frontend/src/components/`: Fully localized UI components.
