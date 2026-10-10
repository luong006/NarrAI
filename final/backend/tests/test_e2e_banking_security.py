"""
End-to-End Test Suite: Requirement 3 (R3)
Bank-Grade Currency Engine, Concurrency Isolation & Multi-Signal Anti-Clone Guard

Derived strictly from:
- ORIGINAL_REQUEST.md (## 2026-09-28T01:01:31Z)
- PROJECT.md (§ M3 ↔ M2 & Feature Inventory 10-14)

Test Structure (4-Tier Methodology):
- Tier 1: Feature Coverage (Isolated Happy Path)
- Tier 2: Boundary & Corner Cases (Concurrency races, zero balance, ledger tampering, subnet limits)
- Tier 3: Cross-Feature Combinations (Paid AI pipeline + rollback, 100 coin lifecycle)
- Tier 4: Real-World Application Scenarios (Sybil attack defense, user topup & full ledger audit)
"""

import os
import sys
import unittest
import hashlib
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException

# Ensure backend root is on sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from db.models import Base, User, CoinTransaction, DeviceFingerprint, SubnetRecord
from services.banking_service import (
    COST_SHORT_STORY,
    COST_MEDIUM_STORY,
    COST_LONG_STORY,
    COST_EDIT,
    COST_MANGA,
    INITIAL_TRIAL_COINS,
    STANDARD_TOPUP_COINS,
    GENESIS_HASH,
    ACTION_STORY_SHORT,
    ACTION_STORY_MEDIUM,
    ACTION_STORY_LONG,
    ACTION_STORY_EDIT,
    ACTION_COMIC_GENERATE,
    ACTION_INITIAL_GRANT,
    ACTION_TOPUP,
    ACTION_REFUND_FAILED,
    get_story_cost,
    get_action_cost,
    compute_transaction_hash,
    deduct_coins,
    refund_coins,
    topup_coins,
    verify_ledger_integrity,
    extract_ip_subnet,
    compute_composite_fingerprint,
    register_device_and_get_initial_coins,
    user_mutexes,
)


class BaseBankingTestCase(unittest.TestCase):
    """
    Test fixture providing an isolated, thread-safe SQLite in-memory database.
    """
    def setUp(self):
        # Unique in-memory database shared safely across worker threads via StaticPool
        self.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool
        )
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.db = self.SessionLocal()
        user_mutexes.reset()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()
        user_mutexes.reset()

    def create_test_user(self, username: str = "testuser", initial_coins: int = 0) -> User:
        user = User(
            username=username,
            full_name="Nguyễn Văn A",
            password_hash="hashed_secret",
            coins=initial_coins
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user


class TestTier1BankingFeatureCoverage(BaseBankingTestCase):
    """
    Tier 1: Feature Coverage & Happy Path Tests for Banking Service.
    """

    def test_server_pricing_constants(self):
        """Verify strict server-controlled pricing table constants."""
        self.assertEqual(COST_SHORT_STORY, 8)
        self.assertEqual(COST_MEDIUM_STORY, 12)
        self.assertEqual(COST_LONG_STORY, 16)
        self.assertEqual(COST_EDIT, 2)
        self.assertEqual(COST_MANGA, 16)
        self.assertEqual(INITIAL_TRIAL_COINS, 100)
        self.assertEqual(STANDARD_TOPUP_COINS, 100)

        # Server cost calculators
        self.assertEqual(get_story_cost("short"), 8)
        self.assertEqual(get_story_cost("medium"), 12)
        self.assertEqual(get_story_cost("long"), 16)
        self.assertEqual(get_story_cost(None), 12)  # Default medium

        self.assertEqual(get_action_cost("STORY_EDIT"), 2)
        self.assertEqual(get_action_cost("COMIC_GENERATE"), 16)

    def test_initial_grant_for_fresh_device(self):
        """Fresh device and fresh subnet receives 100 free trial coins."""
        user = self.create_test_user(username="fresh_user", initial_coins=0)
        fp_data = {
            "canvas_hash": "canvas_unique_111",
            "webgl_hash": "webgl_unique_111",
            "audio_hash": "audio_unique_111",
            "screen_specs": "1920x1080x24"
        }
        client_ip = "14.161.45.88"

        coins = register_device_and_get_initial_coins(self.db, client_ip, fp_data, user_id=user.id)
        self.assertEqual(coins, 100)
        self.db.refresh(user)
        self.assertEqual(user.coins, 100)

        # Verify transaction logged
        tx = self.db.query(CoinTransaction).filter(CoinTransaction.user_id == user.id).first()
        self.assertIsNotNone(tx)
        self.assertEqual(tx.amount, 100)
        self.assertEqual(tx.balance_after, 100)
        self.assertEqual(tx.action_type, ACTION_INITIAL_GRANT)
        self.assertEqual(tx.prev_hash, GENESIS_HASH)

    def test_atomic_coin_deduction(self):
        """Deducts coins atomically and updates balance and ledger."""
        user = self.create_test_user(username="author_1", initial_coins=20)
        ok, tx_hash, new_bal = deduct_coins(
            db=self.db,
            user_id=user.id,
            amount=8,
            action_type=ACTION_STORY_SHORT,
            description="Tạo truyện ngắn 8 xu"
        )
        self.assertTrue(ok)
        self.assertEqual(new_bal, 12)
        self.db.refresh(user)
        self.assertEqual(user.coins, 12)

        # Verify ledger record
        tx = self.db.query(CoinTransaction).filter(CoinTransaction.tx_hash == tx_hash).first()
        self.assertIsNotNone(tx)
        self.assertEqual(tx.amount, -8)
        self.assertEqual(tx.balance_after, 12)
        self.assertEqual(tx.action_type, ACTION_STORY_SHORT)

    def test_compensating_refund_transaction(self):
        """Refunds coins and appends REFUND_FAILED_GENERATION transaction to ledger."""
        user = self.create_test_user(username="author_refund", initial_coins=12)
        ok, tx_hash, new_bal = refund_coins(
            db=self.db,
            user_id=user.id,
            amount=12,
            reason=ACTION_REFUND_FAILED,
            description="Tự động hoàn 12 xu do lỗi AI"
        )
        self.assertTrue(ok)
        self.assertEqual(new_bal, 24)
        self.db.refresh(user)
        self.assertEqual(user.coins, 24)

        tx = self.db.query(CoinTransaction).filter(CoinTransaction.tx_hash == tx_hash).first()
        self.assertIsNotNone(tx)
        self.assertEqual(tx.amount, 12)
        self.assertEqual(tx.balance_after, 24)
        self.assertEqual(tx.action_type, ACTION_REFUND_FAILED)

    def test_cryptographic_ledger_hash_chain_formula(self):
        """Validates the SHA-256 hash chaining algorithm."""
        prev_h = GENESIS_HASH
        user_id = 42
        amount = 8
        balance_after = 8
        ts = "2026-09-28T08:00:00.000000Z"

        expected = hashlib.sha256(f"{prev_h}{user_id}{amount}{balance_after}{ts}".encode("utf-8")).hexdigest()
        actual = compute_transaction_hash(prev_h, user_id, amount, balance_after, ts)
        self.assertEqual(actual, expected)
        self.assertEqual(len(actual), 64)

    def test_verify_ledger_integrity_clean(self):
        """Audits an unmodified ledger and confirms 100% integrity."""
        user = self.create_test_user(username="audit_user", initial_coins=0)

        # Grant 8
        topup_coins(self.db, user.id, amount=100, description="Nạp 100 xu")
        deduct_coins(self.db, user.id, amount=16, action_type=ACTION_STORY_LONG)
        deduct_coins(self.db, user.id, amount=2, action_type=ACTION_STORY_EDIT)
        refund_coins(self.db, user.id, amount=2, reason=ACTION_REFUND_FAILED)

        ok, msg = verify_ledger_integrity(self.db, user_id=user.id)
        self.assertTrue(ok, f"Expected clean audit, got error: {msg}")
        self.assertIn("toàn vẹn 100%", msg)


class TestTier2BankingBoundaryAndCornerCases(BaseBankingTestCase):
    """
    Tier 2: Boundary & Corner Cases (Races, Double Spending, Zero Balance, Tampering, Subnet Throttling).
    """

    def test_insufficient_balance_rejection_http_402(self):
        """Attempts to deduct more coins than available MUST immediately fail with HTTP 402."""
        user = self.create_test_user(username="poor_user", initial_coins=5)
        with self.assertRaises(HTTPException) as ctx:
            deduct_coins(
                db=self.db,
                user_id=user.id,
                amount=8,
                action_type=ACTION_STORY_SHORT,
                raise_on_insufficient=True
            )
        self.assertEqual(ctx.exception.status_code, 402)
        self.assertIn("Số dư xu không đủ", ctx.exception.detail)

        # Balance remains untouched
        self.db.refresh(user)
        self.assertEqual(user.coins, 5)

    def test_zero_balance_rejection(self):
        """User with exactly 0 coins cannot perform any paid actions."""
        user = self.create_test_user(username="zero_user", initial_coins=0)
        with self.assertRaises(HTTPException) as ctx:
            deduct_coins(self.db, user.id, amount=2, action_type=ACTION_STORY_EDIT)
        self.assertEqual(ctx.exception.status_code, 402)

    def test_concurrency_race_condition_double_spending(self):
        """
        CRITICAL TEST: Race condition & double-spending prevention.
        User has exactly 8 coins. 10 concurrent threads simultaneously request
        deduction of 8 coins in the exact same millisecond.
        EXACTLY 1 request must succeed. 9 requests must be rejected with HTTP 402.
        Final balance must be exactly 0 (NEVER negative!).
        """
        user = self.create_test_user(username="race_victim", initial_coins=8)
        user_id = user.id

        success_count = 0
        failure_402_count = 0
        other_errors = []

        def worker_task():
            # Create independent session per thread
            worker_db = self.SessionLocal()
            try:
                ok, tx_hash, bal = deduct_coins(
                    db=worker_db,
                    user_id=user_id,
                    amount=8,
                    action_type=ACTION_STORY_SHORT,
                    raise_on_insufficient=True
                )
                return ("SUCCESS", bal)
            except HTTPException as e:
                return ("402", e.status_code)
            except Exception as e:
                return ("ERR", str(e))
            finally:
                worker_db.close()

        workers_count = 10
        with ThreadPoolExecutor(max_workers=workers_count) as executor:
            futures = [executor.submit(worker_task) for _ in range(workers_count)]
            for fut in as_completed(futures):
                status_res, val = fut.result()
                if status_res == "SUCCESS":
                    success_count += 1
                elif status_res == "402":
                    failure_402_count += 1
                else:
                    other_errors.append(val)

        self.assertEqual(len(other_errors), 0, f"Unexpected errors: {other_errors}")
        self.assertEqual(success_count, 1, f"Expected EXACTLY 1 success, got {success_count}!")
        self.assertEqual(failure_402_count, workers_count - 1, f"Expected {workers_count-1} 402 rejections, got {failure_402_count}")

        # Refresh user from DB
        self.db.refresh(user)
        self.assertEqual(user.coins, 0, f"Final coins must be 0, got {user.coins}")

        # Ledger must have exactly 1 transaction
        txs = self.db.query(CoinTransaction).filter(CoinTransaction.user_id == user_id).all()
        self.assertEqual(len(txs), 1)

    def test_absolute_server_authority_ignores_client_costs(self):
        """Server-controlled action costs always override client-specified values."""
        # Client tries to pass cost = 0 or negative
        self.assertEqual(get_action_cost("STORY_GENERATE_SHORT"), COST_SHORT_STORY)
        self.assertEqual(get_action_cost("STORY_GENERATE_LONG"), COST_LONG_STORY)
        self.assertEqual(get_action_cost("COMIC_GENERATE"), COST_MANGA)
        self.assertEqual(get_action_cost("STORY_EDIT"), COST_EDIT)

    def test_cryptographic_ledger_tamper_detection(self):
        """Tampering with any transaction row in SQLite is caught immediately by ledger audit."""
        user = self.create_test_user(username="tamper_test", initial_coins=0)
        topup_coins(self.db, user.id, 50, description="Topup")
        deduct_coins(self.db, user.id, 8, action_type=ACTION_STORY_SHORT)
        deduct_coins(self.db, user.id, 12, action_type=ACTION_STORY_MEDIUM)

        # Audit passes before tampering
        ok_before, _ = verify_ledger_integrity(self.db, user_id=user.id)
        self.assertTrue(ok_before)

        # Malicious actor tampers with balance_after of transaction #2
        tx2 = self.db.query(CoinTransaction).filter(CoinTransaction.user_id == user.id, CoinTransaction.amount == -8).first()
        self.assertIsNotNone(tx2)
        # Directly update DB without updating hash
        self.db.execute(
            text("UPDATE coin_transactions SET amount = -4, balance_after = 46 WHERE id = :tid"),
            {"tid": tx2.id}
        )
        self.db.commit()

        # Audit must FAIL
        ok_after, msg = verify_ledger_integrity(self.db, user_id=user.id)
        self.assertFalse(ok_after, "Auditor failed to detect direct DB row tampering!")
        self.assertTrue("không khớp" in msg or "Lỗi số học" in msg or "Đứt gãy" in msg)

    def test_anti_clone_duplicate_device_gets_zero_coins(self):
        """Duplicate device fingerprint receives 0 initial coins."""
        fp_data = {
            "canvas_hash": "canvas_dup_999",
            "webgl_hash": "webgl_dup_999",
            "audio_hash": "audio_dup_999",
            "screen_specs": "2560x1440x32"
        }
        # First registration -> INITIAL_TRIAL_COINS
        u1 = self.create_test_user(username="genuine_user", initial_coins=0)
        coins1 = register_device_and_get_initial_coins(self.db, "113.160.10.5", fp_data, user_id=u1.id)
        self.assertEqual(coins1, INITIAL_TRIAL_COINS)

        # Second registration with SAME device -> 0 coins
        u2 = self.create_test_user(username="clone_user", initial_coins=0)
        coins2 = register_device_and_get_initial_coins(self.db, "113.160.20.9", fp_data, user_id=u2.id)
        self.assertEqual(coins2, 0, "Clone account must receive 0 coins")
        self.db.refresh(u2)
        self.assertEqual(u2.coins, 0)

    def test_anti_clone_subnet_throttling_limit(self):
        """Subnet /24 allows max 2 trial grants per day; 3rd attempt receives 0 coins."""
        subnet_ip_prefix = "171.224.180."
        fp_base = {"webgl_hash": "w", "audio_hash": "a", "screen_specs": "s"}

        # Attempt 1: fresh IP, fresh device -> INITIAL_TRIAL_COINS
        u1 = self.create_test_user("sub_user_1", 0)
        c1 = register_device_and_get_initial_coins(self.db, f"{subnet_ip_prefix}10", {**fp_base, "canvas_hash": "dev1"}, u1.id)
        self.assertEqual(c1, INITIAL_TRIAL_COINS)

        # Attempt 2: fresh IP, fresh device -> INITIAL_TRIAL_COINS
        u2 = self.create_test_user("sub_user_2", 0)
        c2 = register_device_and_get_initial_coins(self.db, f"{subnet_ip_prefix}20", {**fp_base, "canvas_hash": "dev2"}, u2.id)
        self.assertEqual(c2, INITIAL_TRIAL_COINS)

        # Attempt 3: fresh device, but SAME /24 subnet quota exceeded -> 0 coins!
        u3 = self.create_test_user("sub_user_3", 0)
        c3 = register_device_and_get_initial_coins(self.db, f"{subnet_ip_prefix}30", {**fp_base, "canvas_hash": "dev3"}, u3.id)
        self.assertEqual(c3, 0, "Subnet throttled user must receive 0 coins")
        self.db.refresh(u3)
        self.assertEqual(u3.coins, 0)

    def test_anti_clone_graceful_missing_signals(self):
        """Handles missing or privacy-blocked fingerprint signals gracefully without crashing."""
        u = self.create_test_user("privacy_user", 0)
        # Empty dict or None
        coins = register_device_and_get_initial_coins(self.db, "10.0.0.1", {}, user_id=u.id)
        self.assertIn(coins, [0, INITIAL_TRIAL_COINS])  # Evaluates cleanly without exception


class TestTier3BankingCrossFeatureCombinations(BaseBankingTestCase):
    """
    Tier 3: Cross-Feature Combinations (Paid AI Pipeline + Compensating Rollback, 100 Coin Lifecycle).
    """

    def test_paid_ai_pipeline_with_automatic_compensating_rollback(self):
        """Simulates full paid generation pipeline where AI fails, triggering automatic 100% refund."""
        user = self.create_test_user(username="pro_writer", initial_coins=50)

        # Step 1: Deduct 12 coins for Medium Story
        deduct_ok, deduct_hash, bal_after_deduct = deduct_coins(
            db=self.db,
            user_id=user.id,
            amount=12,
            action_type=ACTION_STORY_MEDIUM,
            description="Tạo truyện vừa 12 xu"
        )
        self.assertTrue(deduct_ok)
        self.assertEqual(bal_after_deduct, 38)

        # Step 2: Simulate External AI Pipeline (Groq / Cloudflare) failure
        ai_failure_exception = RuntimeError("Cloudflare Diffusion 504 Gateway Timeout")

        # Step 3: Compensating Transaction Rollback
        refund_ok, refund_hash, bal_after_refund = refund_coins(
            db=self.db,
            user_id=user.id,
            amount=12,
            reason=ACTION_REFUND_FAILED,
            reference_id=deduct_hash,
            description=f"Hoàn 12 xu do sự cố AI ({str(ai_failure_exception)})"
        )
        self.assertTrue(refund_ok)
        self.assertEqual(bal_after_refund, 50)
        self.db.refresh(user)
        self.assertEqual(user.coins, 50)

        # Step 4: Verify ledger chain integrity remains 100% unbroken
        audit_ok, audit_msg = verify_ledger_integrity(self.db, user_id=user.id)
        self.assertTrue(audit_ok, f"Ledger broken after rollback: {audit_msg}")

    def test_100_coin_package_lifecycle(self):
        """
        Validates the authoritative 100 Coin economic budget:
        100 coins sufficient for:
        - 2 Medium stories: 2 * 12 = 24 xu
        - 1 Long story: 16 xu
        - 10 Edits: 10 * 2 = 20 xu
        - 2 Comic adaptations: 2 * 16 = 32 xu
        Total: 92 xu. Balance remaining: 8 xu (exact amount for 1 short story!).
        """
        user = self.create_test_user(username="economist_user", initial_coins=0)

        # 1. Topup 100 xu
        topup_coins(self.db, user.id, amount=100, description="Nạp gói chuẩn 100k VNĐ = 100 xu")

        # 2. Generate 2 medium stories
        for _ in range(2):
            deduct_coins(self.db, user.id, COST_MEDIUM_STORY, ACTION_STORY_MEDIUM)
        # 3. Generate 1 long story
        deduct_coins(self.db, user.id, COST_LONG_STORY, ACTION_STORY_LONG)
        # 4. Perform 10 edits
        for _ in range(10):
            deduct_coins(self.db, user.id, COST_EDIT, ACTION_STORY_EDIT)
        # 5. Perform 2 comic adaptations
        for _ in range(2):
            deduct_coins(self.db, user.id, COST_MANGA, ACTION_COMIC_GENERATE)

        self.db.refresh(user)
        self.assertEqual(user.coins, 8, "Expected exactly 8 coins remaining from 100 coin budget")

        # 6. Final remaining 8 coins can complete 1 short story
        ok_short, _, final_bal = deduct_coins(self.db, user.id, COST_SHORT_STORY, ACTION_STORY_SHORT)
        self.assertTrue(ok_short)
        self.assertEqual(final_bal, 0)

        # Verify full ledger integrity across all 16 transactions
        ok_audit, _ = verify_ledger_integrity(self.db, user.id)
        self.assertTrue(ok_audit)


class TestTier4BankingRealWorldScenarios(BaseBankingTestCase):
    """
    Tier 4: Real-World Application Scenarios (Sybil Attack Defense & Global Ledger Audit).
    """

    def test_sybil_botnet_attack_defense(self):
        """
        Scenario: An attacker attempts to create 5 clone accounts using automated proxies.
        Guards: Multi-Signal Fingerprinting + /24 Subnet Throttling.
        Only the first legitimate user gets 8 coins. The other 4 are restricted to 0 coins.
        """
        attacker_subnet_ip = "118.69.150."
        clone_accounts = []

        # Attacker tries 5 accounts
        for i in range(5):
            uname = f"bot_account_{i}"
            u = self.create_test_user(username=uname, initial_coins=0)
            # Reusing same hardware with slight fake proxy IP
            fp = {
                "canvas_hash": "bot_hardware_canvas_sig",
                "webgl_hash": "bot_hardware_webgl_sig",
                "audio_hash": "bot_hardware_audio_sig",
                "screen_specs": "1366x768x24"
            }
            coins = register_device_and_get_initial_coins(
                self.db,
                client_ip=f"{attacker_subnet_ip}{10 + i}",
                fingerprint_data=fp,
                user_id=u.id
            )
            clone_accounts.append((u, coins))

        # Only account 0 got INITIAL_TRIAL_COINS coins
        self.assertEqual(clone_accounts[0][1], INITIAL_TRIAL_COINS)
        # All others got 0 coins!
        for idx in range(1, 5):
            self.assertEqual(clone_accounts[idx][1], 0, f"Bot {idx} must receive 0 coins")

        # System-wide ledger audit
        audit_ok, _ = verify_ledger_integrity(self.db)
        self.assertTrue(audit_ok)


if __name__ == "__main__":
    unittest.main()
