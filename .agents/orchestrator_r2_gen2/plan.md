# Execution Plan — Orchestrator Generation 2

## Goal
Complete Gate 3 evaluation for Milestone 3, execute Milestone 4 (Full System Verification & Final Quality Gate), and prepare the final project handoff for the Sentinel parent.

## Steps

### Step 1: Initialize Orchestrator State [IN PROGRESS]
- Setup `BRIEFING.md`, `plan.md`, `progress.md`, `GATE_STATUS.md`.
- Ensure heartbeat cron is active.

### Step 2: Milestone 3 Gate Verification [PENDING]
- Review Worker implementation report from `e:\NarrAI\.agents\worker_r2_m3\handoff.md`.
- Files under review:
  * `backend/agents/comic_agent.py`
  * `backend/services/cloudflare_ai.py`
  * `backend/tests/test_comic_modern_school_sync.py`
- Dispatch independent verification team:
  1. `reviewer_r2_m3_1` (`teamwork_preview_reviewer`): Code quality, interface compliance, style locking, DNA extractor clean-up, prompt sanitization.
  2. `reviewer_r2_m3_2` (`teamwork_preview_reviewer`): 100% panel spatial anchoring, action/gesture mapping, negative prompt exclusions in Cloudflare AI, regression safety.
  3. `challenger_r2_m3_1` (`teamwork_preview_challenger`): Adversarial stress testing of spatial quarantine regex, edge cases in action extraction, CLIP token budget (<30 words), prompt collisions.
  4. `challenger_r2_m3_2` (`teamwork_preview_challenger`): End-to-end comic generation pipeline simulation, layout tests (`wide`, `square`, `tall`), negative prompt suffixing.
  5. `auditor_r2_m3_1` (`teamwork_preview_auditor`): Forensic integrity audit (zero cheating, genuine implementation, no dummy mocks, no hardcoded test assertions).
- Collect verdicts in `GATE_STATUS.md`.
- If unanimous APPROVE and CLEAN audit -> Mark M3 DONE.

### Step 3: Milestone 4 Full System Verification & Quality Gate [PENDING]
- Dispatch `worker_r2_m4` (`teamwork_preview_worker`):
  * Run `py_compile` across all backend python files.
  * Run `npm run build` in `frontend/`.
  * Run all unit, integration, and adversarial test suites:
    - `backend/tests/test_light_novel_engine.py`
    - `backend/tests/test_dynamic_scene_graph.py`
    - `backend/tests/test_adversarial_dsgo.py`
    - `backend/tests/test_comic_modern_school_sync.py`
    - `backend/tests/test_comic_dna_seed.py`
    - `backend/tests/test_comic_zero_truncation.py`
    - other existing test suites.
  * Report comprehensive test matrix, build logs, and layout verification.
- Dispatch final verification team:
  * Final Reviewer (`reviewer_r2_m4_1`).
  * Final Forensic Auditor (`auditor_r2_m4_1`) for full-system integrity audit.
- Gate 4 evaluation.

### Step 4: Final Synthesis, Handoff & Notification [PENDING]
- Update `PROJECT.md` to reflect all milestones DONE.
- Compile comprehensive project report into `handoff.md`.
- Notify Sentinel parent agent with complete deliverables summary.
