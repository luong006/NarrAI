# NarrAI Test Infrastructure & Architecture (TEST_INFRA.md)

**Project**: NarrAI — Literary Creation Platform & Next-Gen Social Network  
**Specification Reference**: `ORIGINAL_REQUEST.md` (Version `2026-09-28T01:01:31Z`) & `PROJECT.md`  
**Test Suite Architect**: E2E Test Writer (`teamwork_preview_test_writer`)  
**Scope**: Requirements 1, 2, and 3 (R1, R2, R3)  

---

## 1. Executive Summary & Testing Philosophy

The NarrAI E2E Test Infrastructure is an opaque-box, behavior-driven testing harness engineered to guarantee absolute correctness, security, and cultural fidelity across all core subsystems:
1. **Adaptive Open-Ontology & 3 Narrative Modes (R1)**: Verifies respect for authentic Vietnamese historical truth while granting complete creative liberty in out-of-domain fiction.
2. **Bank-Grade Currency Engine & Multi-Signal Anti-Clone Guard (R3)**: Guarantees concurrency isolation, eliminates race condition double-spending, enforces cryptographic SHA-256 chained ledger immutability, and protects against Sybil botnet abuse.
3. **Next-Gen Literary Recommender & Open Messenger (R2)**: Empirically validates 3-stage candidate ranking, exponential time decay dynamics ($\lambda = 0.05/\text{day}$), MMR genre diversification ($\lambda_{\text{MMR}} = 0.7$), Multi-Armed Bandit cold-start exploration ($\epsilon = 0.15$), and real-time 1-on-1 private messaging.

### Key Architectural Tenets
- **100% In-Memory Isolation**: Every test case runs against an ephemeral, isolated SQLite database (`sqlite:///:memory:`). No state leaks across tests; no persistent test artifacts contaminate the production database.
- **Zero External Network Dependencies**: All LLM and image diffusion calls are bounded or simulated locally. Network fluctuations, API quotas, or third-party outages cannot cause false test failures.
- **Authoritative Mathematical Oracles**: Expected outputs are derived directly from the explicit formulas and invariant specifications in `ORIGINAL_REQUEST.md`.

---

## 2. 4-Tier Test Methodology

Every functional requirement is verified across four distinct tiers of rigor:

```
┌────────────────────────────────────────────────────────────────────────┐
│                   TIER 4: REAL-WORLD APPLICATION SCENARIOS             │
│   Complete end-to-end user workflows, lifecycle simulations, & audits  │
├────────────────────────────────────────────────────────────────────────┤
│                   TIER 3: CROSS-FEATURE INTEGRATION                    │
│   Interactions driving decay & MMR, AI failures triggering refunds     │
├────────────────────────────────────────────────────────────────────────┤
│                   TIER 2: BOUNDARY & CORNER CASES                      │
│   Double-spending races, zero balances, ledger tampering, thresholds   │
├────────────────────────────────────────────────────────────────────────┤
│                   TIER 1: FEATURE COVERAGE (HAPPY PATH)                │
│   Isolated functional verification of enums, constants, & formulas     │
└────────────────────────────────────────────────────────────────────────┘
```

### Tier 1: Feature Coverage (Isolated Happy Path)
- Validates the core contractual behaviors of each class, function, and model in isolation.
- Inputs are well-formed and standard; outputs are asserted against authoritative specification values.

### Tier 2: Boundary, Limit & Corner Cases
- Tests behavior at exact mathematical boundaries:
  - Cultural similarity thresholds: $S_{cult} = 0.70$ (Tier 1), $S_{cult} = 0.69$ (Tier 2), $S_{cult} = 0.30$ (Tier 2), $S_{cult} = 0.29$ (Tier 3).
  - Currency limits: $0$ balance, exact cost deduction, empty inputs.
  - Concurrency stress: 10 parallel threads attempting to double-spend the exact same balance.
  - Subnet throttling: Max 2 trial grants per $/24$ subnet; 3rd attempt receives 0 coins.
  - Cryptographic tamper detection: Direct manual edits in the database trigger immediate audit failure.

### Tier 3: Cross-Feature Combinations
- Tests interactions between separate architectural components:
  - Coin deduction $\rightarrow$ External AI call exception $\rightarrow$ Compensating transaction rollback (`REFUND_FAILED_GENERATION`) $\rightarrow$ Cryptographic ledger verification.
  - User reader interactions (Dwell $>60$s, Scroll $100\%$, Like, Comment) $\rightarrow$ Exponential decay profile update $\rightarrow$ Recommender candidate retrieval shift $\rightarrow$ MMR genre balance.
  - Narrative mode selection overriding genre-based cliché exceptions (Chính Sử strictly suppresses translation clichés even if user specifies Xianxia).

### Tier 4: Real-World Application Scenarios
- End-to-end journey simulations mirroring real production users:
  - Vietnamese Historical Epic authoring workflow (Bạch Đằng 1288).
  - Sybil botnet defense: Automated proxy attack where only genuine account receives 8 coins while 4 clones receive 0.
  - Full author-reader literary community journey: Publication, Bandit cold-start discovery, deep reading, comment entity extraction, and Open Messenger 1-on-1 dialogue.

---

## 3. Comprehensive Test Suite Inventory

### 3.1 `backend/tests/test_e2e_ontology_modes.py`
**Target Subsystem**: R1 (Adaptive Open-Ontology, 3 Narrative Modes, Gatekeeper, Smart Cliché Filter)

| Tier | Test Case | Target Feature / Invariant | Authoritative Source |
|---|---|---|---|
| 1 | `test_narrative_mode_enum_and_normalization` | 3 modes + English/Vietnamese aliases | `ORIGINAL_REQUEST.md` § R1.1 |
| 1 | `test_cultural_tier_enum_and_normalization` | 3 cultural tiers + safe integer parsing | `ORIGINAL_REQUEST.md` § R1.2 |
| 1 | `test_historical_gatekeeper_authentic_facts_pass` | Authentic VN history passes (Bạch Đằng, Như Nguyệt, Đống Đa) | `ORIGINAL_REQUEST.md` § R1.1 |
| 1 | `test_historical_gatekeeper_falsification_rejected` | Historical distortions rejected in Mode 1 | `ORIGINAL_REQUEST.md` § R1.1 |
| 1 | `test_tri_tier_similarity_scoring_canonical_vn` | $S_{cult} \ge 0.7 \rightarrow$ Tier 1 Canonical | `ORIGINAL_REQUEST.md` § R1.2 |
| 1 | `test_tri_tier_similarity_scoring_cultural_fusion` | $0.3 \le S_{cult} < 0.7 \rightarrow$ Tier 2 Hybrid | `ORIGINAL_REQUEST.md` § R1.2 |
| 1 | `test_tri_tier_similarity_scoring_open_domain` | $S_{cult} < 0.3 \rightarrow$ Tier 3 Open Domain | `ORIGINAL_REQUEST.md` § R1.2 |
| 1 | `test_master_negative_filter_tier_isolation` | Ban Hanfu/Kimono/Samurai in Tiers 1-2; unconstrained in Tier 3 | `ORIGINAL_REQUEST.md` § R1.2 |
| 1 | `test_smart_selective_language_filter_wuxia_permission` | Allow Chinese clichés in Xianxia/Wuxia | `ORIGINAL_REQUEST.md` § R1.3 |
| 1 | `test_smart_selective_language_filter_pure_vn_suppression` | Strictly ban Chinese clichés in pure VN/historical | `ORIGINAL_REQUEST.md` § R1.3 |
| 1 | `test_universal_ai_cliches_always_banned` | Always ban 36+ universal AI tropes | `ORIGINAL_REQUEST.md` § R1.3 |
| 1 | `test_dynamic_ephemeral_node_extraction` | Dynamically extract setting without feudal defaults | `ORIGINAL_REQUEST.md` § R1.2 |
| 2 | `test_empty_and_none_inputs` | Graceful handling of empty/None strings | BVA & Robustness |
| 2 | `test_exact_tier_similarity_boundary_thresholds` | Thresholds $0.70, 0.69, 0.30, 0.29$ | BVA Specification |
| 2 | `test_historical_mode_forces_tier_1_canonical` | Mode 1 & 2 force Tier 1 regardless of prompt length | `PROJECT.md` § M1 |
| 2 | `test_case_insensitivity_and_vietnamese_diacritics` | Diacritic & uppercase variation invariance | Unicode Robustness |
| 2 | `test_mode_3_bypasses_historical_gatekeeper` | Mode 3 allows complete semantic freedom | `ORIGINAL_REQUEST.md` § R1.1 |
| 3 | `test_resolver_coordinates_visual_dna_and_negative_filters` | Unified `ResolvedOntology` integration | `PROJECT.md` § M1 |
| 3 | `test_mode_override_on_cliche_filter` | Mode 1 overrides Xianxia genre cliché exemption | Integrity Invariant |
| 4 | `test_workflow_historical_epic_chinh_su` | E2E strict historical novel authoring | Scenario Workflow |
| 4 | `test_workflow_hybrid_cyberpunk_thang_long` | E2E Cyberpunk Thăng Long authoring | Scenario Workflow |
| 4 | `test_workflow_western_detective_open_domain` | E2E Victorian detective authoring | Scenario Workflow |

---

### 3.2 `backend/tests/test_e2e_banking_security.py`
**Target Subsystem**: R3 (100 Coin Model, Concurrency Isolation, Rollback, Ledger, Anti-Clone)

| Tier | Test Case | Target Feature / Invariant | Authoritative Source |
|---|---|---|---|
| 1 | `test_server_pricing_constants` | 8/12/16/2/16 pricing, 8 trial, 100k = 100 coins | `ORIGINAL_REQUEST.md` § R3.1 |
| 1 | `test_initial_grant_for_fresh_device` | Fresh device/subnet receives 8 coins + genesis ledger entry | `ORIGINAL_REQUEST.md` § R3.3 |
| 1 | `test_atomic_coin_deduction` | Atomic deduction with dual-locking & negative ledger entry | `ORIGINAL_REQUEST.md` § R3.2 |
| 1 | `test_compensating_refund_transaction` | `REFUND_FAILED_GENERATION` credits 100% coins back | `ORIGINAL_REQUEST.md` § R3.2 |
| 1 | `test_cryptographic_ledger_hash_chain_formula` | $tx\_hash = \text{SHA256}(prev\_hash + u + a + b + ts)$ | `ORIGINAL_REQUEST.md` § R3.2 |
| 1 | `test_verify_ledger_integrity_clean` | Clean ledger chain verified with 100% integrity | `ORIGINAL_REQUEST.md` § R3.2 |
| 2 | `test_insufficient_balance_rejection_http_402` | Reject deduction if balance < cost with HTTP 402 | `ORIGINAL_REQUEST.md` § R3.2 |
| 2 | `test_zero_balance_rejection` | 0 balance cannot execute paid operations | Boundary Condition |
| 2 | `test_concurrency_race_condition_double_spending` | 10 concurrent threads on 8 coins: exactly 1 succeeds, 9 fail with 402 | `ORIGINAL_REQUEST.md` § R3.2 |
| 2 | `test_absolute_server_authority_ignores_client_costs` | Client-specified costs ignored by server pricing table | `ORIGINAL_REQUEST.md` § R3.2 |
| 2 | `test_cryptographic_ledger_tamper_detection` | Direct SQLite modifications detected by auditor | `ORIGINAL_REQUEST.md` § R3.2 |
| 2 | `test_anti_clone_duplicate_device_gets_zero_coins` | Duplicate device receives 0 initial coins | `ORIGINAL_REQUEST.md` § R3.3 |
| 2 | `test_anti_clone_subnet_throttling_limit` | Max 2 trial grants per $/24$ subnet; 3rd gets 0 | `ORIGINAL_REQUEST.md` § R3.3 |
| 2 | `test_anti_clone_graceful_missing_signals` | Handles blocked canvas/audio gracefully | Fallback Robustness |
| 3 | `test_paid_ai_pipeline_with_automatic_compensating_rollback` | Deduct $\rightarrow$ AI 5xx $\rightarrow$ Rollback $\rightarrow$ Unbroken chain | `ORIGINAL_REQUEST.md` § R3.2 |
| 3 | `test_100_coin_package_lifecycle` | 100 coins = 2 med + 1 long + 10 edits + 2 comics (~92 coins) | `ORIGINAL_REQUEST.md` § R3.1 |
| 4 | `test_sybil_botnet_attack_defense` | 5 bot accounts from same subnet throttled to 0 coins | Security Hardening |

---

### 3.3 `backend/tests/test_e2e_recommender_messenger.py`
**Target Subsystem**: R2 (Social Graph, 3-Stage Recommender, Open Messenger)

| Tier | Test Case | Target Feature / Invariant | Authoritative Source |
|---|---|---|---|
| 1 | `test_social_models_creation_and_attributes` | `SocialPost`, `PostInteraction`, `UserInterestProfile` | `ORIGINAL_REQUEST.md` § R2.1 |
| 1 | `test_exponential_time_decay_mathematical_oracle` | $U_{\text{decayed}} = U_{\text{old}} \cdot e^{-\lambda \Delta t}$, $\lambda = 0.05/\text{day}$ | `ORIGINAL_REQUEST.md` § R2.1 |
| 1 | `test_interaction_weights_and_sentiment_adjustment` | $w(\text{Dwell}) = 2.5, w(\text{Scroll}) = 2.0, w(\text{Cmt}) = 3.0 \cdot (1 + s)$ | `ORIGINAL_REQUEST.md` § R2.1 |
| 1 | `test_multi_task_ranking_scoring_oracle` | $\text{Score} = 0.35C + 0.25A + 0.20F + 0.20Q$ | `ORIGINAL_REQUEST.md` § R2.2 |
| 1 | `test_mmr_diversity_score_oracle` | $\text{MMR\_Score} = 0.7 \cdot \text{Score} - 0.3 \cdot \text{Sim}$, genre diversity | `ORIGINAL_REQUEST.md` § R2.2 |
| 1 | `test_open_messenger_models_and_1_to_1_chat` | `Conversation`, `ChatMessage`, read receipts, unread counter | `ORIGINAL_REQUEST.md` § R2.3 |
| 1 | `test_user_directory_search_query` | Search across all registered users excluding self | `ORIGINAL_REQUEST.md` § R2.3 |
| 2 | `test_cold_start_new_user_empty_profile` | Zero-vector profile handled without division by zero | Cold-Start Robustness |
| 2 | `test_zero_views_post_safe_quality_score` | 0 views post safely computes quality score | BVA Robustness |
| 2 | `test_vector_normalization_with_all_zeros` | All-zero vector normalization returns zeros safely | Mathematical Edge Case |
| 2 | `test_conversation_participant_unique_constraint` | Participant uniqueness per conversation | Relational Integrity |
| 3 | `test_user_interaction_drives_profile_shift_and_scoring` | Interactions shift profile toward historical domain | `ORIGINAL_REQUEST.md` § R2.1 |
| 3 | `test_comment_entity_extraction_boosts_affinity` | Positive comment boosts entity affinity score | `ORIGINAL_REQUEST.md` § R2.1 |
| 4 | `test_full_community_journey_publish_discover_read_chat` | E2E Author publication, reader discovery, chat exchange | Scenario Workflow |

---

## 4. Execution Commands

### Run Full E2E Test Track
```powershell
python backend/tests/run_all_tests.py
```

### Run Individual Test Suites
```powershell
# R1: Ontology, Narrative Modes & Filters
python -m unittest backend/tests/test_e2e_ontology_modes.py

# R3: Banking, Atomic Locks & Anti-Clone
python -m unittest backend/tests/test_e2e_banking_security.py

# R2: Recommender Models & Messenger
python -m unittest backend/tests/test_e2e_recommender_messenger.py
```

---

## 5. Quality Status & Acceptance Criteria

- [x] **Zero Mock Facades**: All tests exercise genuine programmatic logic, database ORM relations, or exact mathematical formulas.
- [x] **Adversarial Hardening**: Covers race-condition concurrency double-spending, manual database ledger tampering, and Sybil proxy subnet flooding.
- [x] **Progressive Testability**: Operates cleanly against current database models and service implementations with zero external network lockouts.
- [x] **Clean Python Compilation**: Fully compliant with `python -m py_compile`.
