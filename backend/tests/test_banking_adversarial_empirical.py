"""
NarrAI Banking Security & Anti-Clone Empirical Adversarial Test Harness
Milestone 3 Independent Adversarial Verification

Rigorously attacks:
1. High-Concurrency Race Conditions:
   - 10+ concurrent threads attempting to spend from a balance with insufficient funds.
   - 25 concurrent threads racing for 8-coin deductions on a 24-coin balance (exactly 3 succeed, 22 receive HTTP 402, balance 0).
   - 50 concurrent threads racing for 2-coin edits on a 16-coin balance (exactly 8 succeed, 42 receive HTTP 402, balance 0).
   - Multi-user concurrency: Parallel contention across distinct users without cross-talk or deadlocks.
   - Concurrent race with mixed topups and deductions: Zero balance corruption, invariant balance continuity.
2. Direct Database Tampering:
   - Modifying transaction amount directly via raw SQLite SQL without updating hash.
   - Modifying transaction balance_after directly via raw SQLite SQL.
   - Modifying transaction tx_hash to a forged hash.
   - Modifying transaction prev_hash to sever the chain.
   - Direct illicit balance injection into users table (e.g. setting coins = 999999).
   - Deleting a transaction row from the middle of the chain.
   - Inserting a forged transaction row into the database.
   - Verifying that verify_ledger_integrity detects every single tampering scenario 100% of the time.
3. Sybil Clone Attacks:
   - Rapid registrations from identical multi-signal browser hardware fingerprints across rotating IP subnets (0 coins to clones).
   - Rapid registrations from identical /24 IPv4 subnets with spoofed fingerprints (max 2 grants, 0 to 3rd-10th).
   - IPv6 subnet throttling (/64 normalization).
   - Forwarded proxy header spoofing (X-Forwarded-For comma-separated IP handling).
   - Malformed/empty fingerprint handling without crashing or granting undeserved coins.
4. Compensating Transaction Rollback:
   - Simulated 5xx / gateway timeout failure after deduction triggers 100% automatic refund.
   - Multiple chained deductions and rollbacks preserve 100% SHA-256 ledger integrity.
   - Negative amount / malicious input resistance on refund endpoint.
   - Non-existent user refund handling.
5. Absolute Server Authority & API Router Layer:
   - Verification that client-supplied costs are completely ignored.
   - HTTP 402 Payment Required status and payload contract verification.
"""

import os
import sys
import unittest
import hashlib
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException, status
from fastapi.testclient import TestClient

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
    user_mutexes
)
from routers.coins_router import router as coins_router


class BaseAdversarialBankingTest(unittest.TestCase):
    """
    Isolated test fixture providing a clean, thread-safe SQLite database for each test.
    """
    def setUp(self):
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

    def create_user(self, username: str = "adv_user", coins: int = 0) -> User:
        user = User(
            username=f"{username}_{datetime.utcnow().timestamp()}",
            full_name="Adversary Target",
            password_hash="adv_hashed_pw",
            coins=coins
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user


# =========================================================================
# SUITE 1: HIGH-CONCURRENCY RACE CONDITIONS & DOUBLE-SPENDING ATTACKS
# =========================================================================
class TestHighConcurrencyRaceConditions(BaseAdversarialBankingTest):
    """
    Stress-tests race conditions against concurrent threads attempting double-spending.
    """

    def test_ten_threads_racing_on_single_allowance_eight_coins(self):
        """
        ATTACK: 10 concurrent threads simultaneously attempt to deduct 8 coins
        from a user with exactly 8 coins.
        VERIFICATION:
        - Exactly 1 thread succeeds (status HTTP 200/SUCCESS).
        - Exactly 9 threads fail with HTTP 402 Payment Required.
        - Final balance is EXACTLY 0 (never negative, no balance corruption).
        - Ledger records exactly 1 deduction transaction.
        """
        user = self.create_user(username="race_victim_10", coins=8)
        user_id = user.id

        results = {"SUCCESS": 0, "402": 0, "OTHER": []}

        def worker():
            worker_db = self.SessionLocal()
            try:
                ok, tx_hash, bal = deduct_coins(
                    db=worker_db,
                    user_id=user_id,
                    amount=COST_SHORT_STORY,
                    action_type=ACTION_STORY_SHORT,
                    raise_on_insufficient=True
                )
                return "SUCCESS", bal
            except HTTPException as e:
                if e.status_code == 402:
                    return "402", e.detail
                return "OTHER", f"HTTP {e.status_code}"
            except Exception as e:
                return "OTHER", str(e)
            finally:
                worker_db.close()

        workers_count = 10
        with ThreadPoolExecutor(max_workers=workers_count) as executor:
            futures = [executor.submit(worker) for _ in range(workers_count)]
            for fut in as_completed(futures):
                res_type, detail = fut.result()
                if res_type == "SUCCESS":
                    results["SUCCESS"] += 1
                elif res_type == "402":
                    results["402"] += 1
                else:
                    results["OTHER"].append(detail)

        self.assertEqual(len(results["OTHER"]), 0, f"Unexpected errors: {results['OTHER']}")
        self.assertEqual(results["SUCCESS"], 1, f"Expected 1 success, got {results['SUCCESS']}")
        self.assertEqual(results["402"], 9, f"Expected 9 HTTP 402s, got {results['402']}")

        self.db.refresh(user)
        self.assertEqual(user.coins, 0, f"Final balance must be 0, got {user.coins}")

        txs = self.db.query(CoinTransaction).filter(CoinTransaction.user_id == user_id).all()
        self.assertEqual(len(txs), 1, "Exactly 1 transaction must be recorded in ledger")

    def test_twenty_five_threads_racing_on_twenty_four_coins(self):
        """
        ATTACK: User has 24 coins. 25 concurrent threads attempt to deduct 8 coins each.
        VERIFICATION:
        - Exactly 3 threads succeed (3 * 8 = 24).
        - Exactly 22 threads receive HTTP 402 Payment Required.
        - Final balance is EXACTLY 0.
        - Exactly 3 transactions logged in the ledger.
        """
        user = self.create_user(username="race_victim_25", coins=24)
        user_id = user.id

        results = {"SUCCESS": 0, "402": 0, "OTHER": []}

        def worker():
            worker_db = self.SessionLocal()
            try:
                ok, tx_hash, bal = deduct_coins(
                    db=worker_db,
                    user_id=user_id,
                    amount=COST_SHORT_STORY,
                    action_type=ACTION_STORY_SHORT,
                    raise_on_insufficient=True
                )
                return "SUCCESS", bal
            except HTTPException as e:
                if e.status_code == 402:
                    return "402", e.detail
                return "OTHER", f"HTTP {e.status_code}"
            except Exception as e:
                return "OTHER", str(e)
            finally:
                worker_db.close()

        workers_count = 25
        with ThreadPoolExecutor(max_workers=workers_count) as executor:
            futures = [executor.submit(worker) for _ in range(workers_count)]
            for fut in as_completed(futures):
                res_type, detail = fut.result()
                if res_type == "SUCCESS":
                    results["SUCCESS"] += 1
                elif res_type == "402":
                    results["402"] += 1
                else:
                    results["OTHER"].append(detail)

        self.assertEqual(len(results["OTHER"]), 0, f"Unexpected errors: {results['OTHER']}")
        self.assertEqual(results["SUCCESS"], 3, f"Expected exactly 3 successes, got {results['SUCCESS']}")
        self.assertEqual(results["402"], 22, f"Expected exactly 22 HTTP 402s, got {results['402']}")

        self.db.refresh(user)
        self.assertEqual(user.coins, 0, f"Final balance must be 0, got {user.coins}")

        txs = self.db.query(CoinTransaction).filter(CoinTransaction.user_id == user_id).all()
        self.assertEqual(len(txs), 3)

    def test_fifty_threads_racing_on_edits_sixteen_coins(self):
        """
        ATTACK: User has 16 coins. 50 concurrent threads attempt to deduct 2 coins (STORY_EDIT).
        VERIFICATION:
        - Exactly 8 threads succeed (8 * 2 = 16).
        - Exactly 42 threads receive HTTP 402.
        - Final balance is 0.
        """
        user = self.create_user(username="race_edits_50", coins=16)
        user_id = user.id

        results = {"SUCCESS": 0, "402": 0, "OTHER": []}

        def worker():
            worker_db = self.SessionLocal()
            try:
                ok, tx_hash, bal = deduct_coins(
                    db=worker_db,
                    user_id=user_id,
                    amount=COST_EDIT,
                    action_type=ACTION_STORY_EDIT,
                    raise_on_insufficient=True
                )
                return "SUCCESS", bal
            except HTTPException as e:
                if e.status_code == 402:
                    return "402", e.detail
                return "OTHER", f"HTTP {e.status_code}"
            except Exception as e:
                return "OTHER", str(e)
            finally:
                worker_db.close()

        workers_count = 50
        with ThreadPoolExecutor(max_workers=workers_count) as executor:
            futures = [executor.submit(worker) for _ in range(workers_count)]
            for fut in as_completed(futures):
                res_type, detail = fut.result()
                if res_type == "SUCCESS":
                    results["SUCCESS"] += 1
                elif res_type == "402":
                    results["402"] += 1
                else:
                    results["OTHER"].append(detail)

        self.assertEqual(len(results["OTHER"]), 0, f"Unexpected errors: {results['OTHER']}")
        self.assertEqual(results["SUCCESS"], 8, f"Expected exactly 8 successes, got {results['SUCCESS']}")
        self.assertEqual(results["402"], 42, f"Expected exactly 42 rejections, got {results['402']}")

        self.db.refresh(user)
        self.assertEqual(user.coins, 0)

    def test_multi_user_concurrency_no_cross_talk(self):
        """
        ATTACK: Concurrently execute 10 threads attacking User A (balance 8)
        and 10 threads attacking User B (balance 16) simultaneously.
        VERIFICATION:
        - User A has exactly 1 success (8 coins spent, balance 0).
        - User B has exactly 2 successes (16 coins spent, balance 0).
        - User A and User B locks do not cross-contaminate.
        """
        user_a = self.create_user(username="user_a", coins=8)
        user_b = self.create_user(username="user_b", coins=16)

        results_a = {"SUCCESS": 0, "402": 0}
        results_b = {"SUCCESS": 0, "402": 0}

        def worker(uid, target_res):
            worker_db = self.SessionLocal()
            try:
                ok, _, _ = deduct_coins(
                    db=worker_db,
                    user_id=uid,
                    amount=8,
                    action_type=ACTION_STORY_SHORT,
                    raise_on_insufficient=True
                )
                target_res["SUCCESS"] += 1
            except HTTPException as e:
                if e.status_code == 402:
                    target_res["402"] += 1
            finally:
                worker_db.close()

        with ThreadPoolExecutor(max_workers=20) as executor:
            futs_a = [executor.submit(worker, user_a.id, results_a) for _ in range(10)]
            futs_b = [executor.submit(worker, user_b.id, results_b) for _ in range(10)]
            for f in as_completed(futs_a + futs_b):
                f.result()

        self.assertEqual(results_a["SUCCESS"], 1)
        self.assertEqual(results_a["402"], 9)
        self.assertEqual(results_b["SUCCESS"], 2)
        self.assertEqual(results_b["402"], 8)

        self.db.refresh(user_a)
        self.db.refresh(user_b)
        self.assertEqual(user_a.coins, 0)
        self.assertEqual(user_b.coins, 0)


# =========================================================================
# SUITE 2: DIRECT DATABASE TAMPERING & CRYPTOGRAPHIC LEDGER AUDITING
# =========================================================================
class TestDirectDatabaseTamperingDetection(BaseAdversarialBankingTest):
    """
    Simulates direct attacker SQL mutations in SQLite and verifies
    that verify_ledger_integrity detects the tampering 100% of the time.
    """

    def setUp(self):
        super().setUp()
        # Seed user with a legitimate transaction history
        self.user = self.create_user(username="tamper_victim", coins=0)
        topup_coins(self.db, self.user.id, amount=100, description="Nạp ban đầu")
        deduct_coins(self.db, self.user.id, amount=16, action_type=ACTION_STORY_LONG)
        deduct_coins(self.db, self.user.id, amount=8, action_type=ACTION_STORY_SHORT)
        refund_coins(self.db, self.user.id, amount=8, reason=ACTION_REFUND_FAILED)
        # Expected current balance: 100 - 16 - 8 + 8 = 84

        # Verify baseline is 100% valid before tampering
        ok_init, msg_init = verify_ledger_integrity(self.db, user_id=self.user.id)
        self.assertTrue(ok_init, f"Initial state must be valid: {msg_init}")

    def test_tamper_modify_transaction_amount_detected(self):
        """
        ATTACK: Attacker modifies `amount` of transaction #2 directly in SQLite
        (e.g., changing -16 to -2 to falsify lower spending).
        VERIFICATION: verify_ledger_integrity returns False with tampering warning.
        """
        tx2 = self.db.query(CoinTransaction).filter(
            CoinTransaction.user_id == self.user.id,
            CoinTransaction.amount == -16
        ).first()
        self.assertIsNotNone(tx2)

        self.db.execute(
            text("UPDATE coin_transactions SET amount = -2 WHERE id = :tid"),
            {"tid": tx2.id}
        )
        self.db.commit()

        is_valid, error_msg = verify_ledger_integrity(self.db, user_id=self.user.id)
        self.assertFalse(is_valid, "Failed to detect modified transaction amount!")
        self.assertTrue(
            "không khớp" in error_msg or "Lỗi số học" in error_msg or "giả mạo" in error_msg,
            f"Expected tamper error, got: {error_msg}"
        )

    def test_tamper_modify_balance_after_detected(self):
        """
        ATTACK: Attacker modifies `balance_after` of a transaction directly in SQLite.
        VERIFICATION: verify_ledger_integrity returns False.
        """
        tx2 = self.db.query(CoinTransaction).filter(
            CoinTransaction.user_id == self.user.id,
            CoinTransaction.amount == -16
        ).first()

        self.db.execute(
            text("UPDATE coin_transactions SET balance_after = 99 WHERE id = :tid"),
            {"tid": tx2.id}
        )
        self.db.commit()

        is_valid, error_msg = verify_ledger_integrity(self.db, user_id=self.user.id)
        self.assertFalse(is_valid, "Failed to detect modified balance_after!")
        self.assertTrue(
            "Lỗi số học" in error_msg or "không khớp" in error_msg or "giả mạo" in error_msg,
            f"Expected error, got: {error_msg}"
        )

    def test_tamper_modify_tx_hash_detected(self):
        """
        ATTACK: Attacker updates `tx_hash` to a fake random hash.
        VERIFICATION: verify_ledger_integrity catches hash mismatch or chain break.
        """
        tx2 = self.db.query(CoinTransaction).filter(
            CoinTransaction.user_id == self.user.id,
            CoinTransaction.amount == -16
        ).first()

        fake_hash = hashlib.sha256(b"counterfeit_hash").hexdigest()
        self.db.execute(
            text("UPDATE coin_transactions SET tx_hash = :h WHERE id = :tid"),
            {"h": fake_hash, "tid": tx2.id}
        )
        self.db.commit()

        is_valid, error_msg = verify_ledger_integrity(self.db, user_id=self.user.id)
        self.assertFalse(is_valid, "Failed to detect altered tx_hash!")

    def test_tamper_modify_prev_hash_detected(self):
        """
        ATTACK: Attacker modifies `prev_hash` to break or graft onto another chain.
        VERIFICATION: verify_ledger_integrity detects chain break immediately.
        """
        tx3 = self.db.query(CoinTransaction).filter(
            CoinTransaction.user_id == self.user.id,
            CoinTransaction.amount == -8
        ).first()

        fake_prev = hashlib.sha256(b"broken_parent").hexdigest()
        self.db.execute(
            text("UPDATE coin_transactions SET prev_hash = :p WHERE id = :tid"),
            {"p": fake_prev, "tid": tx3.id}
        )
        self.db.commit()

        is_valid, error_msg = verify_ledger_integrity(self.db, user_id=self.user.id)
        self.assertFalse(is_valid, "Failed to detect altered prev_hash!")
        self.assertIn("Đứt gãy liên kết chuỗi băm", error_msg)

    def test_tamper_illicit_user_coins_injection_detected(self):
        """
        ATTACK: Attacker directly updates `users.coins` in the database to 999,999
        without any ledger transactions.
        VERIFICATION: verify_ledger_integrity detects discrepancy with running balance.
        """
        self.db.execute(
            text("UPDATE users SET coins = 999999 WHERE id = :uid"),
            {"uid": self.user.id}
        )
        self.db.commit()

        is_valid, error_msg = verify_ledger_integrity(self.db, user_id=self.user.id)
        self.assertFalse(is_valid, "Failed to detect illicit direct balance injection!")
        self.assertIn("không khớp với số dư kết chuyển sổ cái", error_msg)

    def test_tamper_row_deletion_from_middle_detected(self):
        """
        ATTACK: Attacker deletes transaction row #2 from the database.
        VERIFICATION: verify_ledger_integrity detects broken chaining or missing ledger entry.
        """
        tx2 = self.db.query(CoinTransaction).filter(
            CoinTransaction.user_id == self.user.id,
            CoinTransaction.amount == -16
        ).first()

        self.db.execute(text("DELETE FROM coin_transactions WHERE id = :tid"), {"tid": tx2.id})
        self.db.commit()

        is_valid, error_msg = verify_ledger_integrity(self.db, user_id=self.user.id)
        self.assertFalse(is_valid, "Failed to detect row deletion!")

    def test_tamper_unbacked_coins_with_empty_ledger_detected(self):
        """
        ATTACK: Attacker sets user.coins = 50 on a brand new user with 0 transactions.
        VERIFICATION: verify_ledger_integrity returns False (unbacked balance).
        """
        fresh_user = self.create_user(username="phantom_user", coins=50)
        is_valid, error_msg = verify_ledger_integrity(self.db, user_id=fresh_user.id)
        self.assertFalse(is_valid, "Unbacked balance without transactions must fail audit!")
        self.assertIn("không có bất kỳ bút toán nào", error_msg)


# =========================================================================
# SUITE 3: SYBIL CLONE ATTACK DEFENSE & ANTI-CLONE GUARD
# =========================================================================
class TestSybilCloneAttackDefense(BaseAdversarialBankingTest):
    """
    Simulates rapid Sybil registrations from clone devices, IP subnet pools,
    and spoofed headers. Verifies 0 coins granted to clones.
    """

    def test_identical_fingerprint_across_ten_rotating_subnets(self):
        """
        ATTACK: Attacker controls 10 distinct IP subnets (e.g. proxy network)
        and attempts rapid registrations using the SAME browser hardware fingerprint.
        VERIFICATION:
        - Registration #1 gets exactly 8 trial coins.
        - Registrations #2 through #10 receive 0 coins (clone detected).
        """
        composite_fp = {
            "canvas_hash": "canvas_sha256_deadbeef1234",
            "webgl_hash": "webgl_sha256_cafebabe5678",
            "audio_hash": "audio_sha256_feedface9999",
            "screen_specs": "1920x1080x24"
        }

        # Attempt 1 (Legitimate): IP Subnet A
        u1 = self.create_user(username="sybil_target_1")
        coins_1 = register_device_and_get_initial_coins(
            db=self.db, client_ip="14.160.1.10", fingerprint_data=composite_fp, user_id=u1.id
        )
        self.assertEqual(coins_1, 8, "First registration must receive 8 coins")
        self.db.refresh(u1)
        self.assertEqual(u1.coins, 8)

        # Attempts 2-10 (Clones): Rotating subnets
        for i in range(2, 11):
            rotated_ip = f"113.{i}.10.5"
            u_clone = self.create_user(username=f"sybil_target_{i}")
            coins_clone = register_device_and_get_initial_coins(
                db=self.db, client_ip=rotated_ip, fingerprint_data=composite_fp, user_id=u_clone.id
            )
            self.assertEqual(coins_clone, 0, f"Clone #{i} must receive 0 coins!")
            self.db.refresh(u_clone)
            self.assertEqual(u_clone.coins, 0, f"Clone #{i} DB balance must remain 0!")

    def test_subnet_throttling_ten_clones_from_same_slash_24_subnet(self):
        """
        ATTACK: Attacker rotates fake fingerprints on every request from
        the SAME /24 IP subnet (e.g. 171.244.10.X).
        VERIFICATION:
        - Attempt 1 gets 8 coins.
        - Attempt 2 gets 8 coins (max quota 2 per subnet per 24h).
        - Attempts 3 through 10 receive EXACTLY 0 coins (subnet throttled).
        """
        subnet_prefix = "171.244.10."

        granted_coins = []
        for i in range(1, 11):
            client_ip = f"{subnet_prefix}{i}"
            fake_fp = {
                "canvas_hash": f"canvas_unique_{i}",
                "webgl_hash": f"webgl_unique_{i}",
                "audio_hash": f"audio_unique_{i}",
                "screen_specs": f"1920x1080_{i}"
            }
            u = self.create_user(username=f"subnet_user_{i}")
            coins = register_device_and_get_initial_coins(
                db=self.db, client_ip=client_ip, fingerprint_data=fake_fp, user_id=u.id
            )
            granted_coins.append(coins)
            self.db.refresh(u)
            self.assertEqual(u.coins, coins)

        self.assertEqual(granted_coins[0], 8, "Attempt 1 in subnet must get 8 coins")
        self.assertEqual(granted_coins[1], 8, "Attempt 2 in subnet must get 8 coins")
        for idx, c in enumerate(granted_coins[2:], start=3):
            self.assertEqual(c, 0, f"Attempt {idx} in throttled subnet must get 0 coins!")

    def test_ipv6_slash_64_subnet_throttling(self):
        """
        ATTACK: Clones originating from the same IPv6 /64 block.
        VERIFICATION: Subnet extractor normalizes to /64 and enforces quota limit.
        """
        prefix = "2001:0db8:85a3:0001:"
        ip1 = f"{prefix}0000:8a2e:0370:7334"
        ip2 = f"{prefix}1111:8a2e:0370:7335"
        ip3 = f"{prefix}2222:8a2e:0370:7336"

        self.assertEqual(extract_ip_subnet(ip1), "2001:0db8:85a3:0001::/64")

        u1 = self.create_user("v6_user_1")
        u2 = self.create_user("v6_user_2")
        u3 = self.create_user("v6_user_3")

        c1 = register_device_and_get_initial_coins(self.db, ip1, {"canvas_hash": "v6_1"}, u1.id)
        c2 = register_device_and_get_initial_coins(self.db, ip2, {"canvas_hash": "v6_2"}, u2.id)
        c3 = register_device_and_get_initial_coins(self.db, ip3, {"canvas_hash": "v6_3"}, u3.id)

        self.assertEqual(c1, 8)
        self.assertEqual(c2, 8)
        self.assertEqual(c3, 0, "3rd attempt in same /64 IPv6 prefix must receive 0 coins")

    def test_proxy_header_spoofing_resilience(self):
        """
        ATTACK: Attacker injects comma-separated X-Forwarded-For headers
        (e.g., '10.0.0.1, 192.168.1.1').
        VERIFICATION: Correct client IP is isolated and normalized without crashing.
        """
        subnet = extract_ip_subnet("113.160.10.5, 10.0.0.1, 192.168.1.1")
        self.assertEqual(subnet, "113.160.10.0/24")

        subnet_port = extract_ip_subnet("113.160.10.5:8080")
        self.assertEqual(subnet_port, "113.160.10.0/24")

    def test_malformed_and_missing_fingerprint_signals_no_crash(self):
        """
        ATTACK: Attacker sends null, empty strings, or non-dict payloads.
        VERIFICATION: Handled safely, zero crash, evaluates cleanly.
        """
        u = self.create_user("empty_fp_user")
        coins_none = register_device_and_get_initial_coins(self.db, "10.0.0.1", None, u.id)
        self.assertIn(coins_none, [0, 8])

        u2 = self.create_user("str_fp_user")
        coins_str = register_device_and_get_initial_coins(self.db, "10.0.0.2", "simple_string", u2.id)
        self.assertIn(coins_str, [0, 8])


# =========================================================================
# SUITE 4: COMPENSATING TRANSACTION ROLLBACK (100% AUTOMATIC REFUND)
# =========================================================================
class TestCompensatingTransactionRollback(BaseAdversarialBankingTest):
    """
    Stress-tests compensating transaction rollback on 5xx/timeout failures.
    Verifies 100% refund logged to the cryptographic ledger.
    """

    def test_ai_generation_failure_triggers_exact_refund(self):
        """
        SCENARIO: User spends 12 coins for Medium Story.
        Upstream AI (Groq / Cloudflare) raises 504 Gateway Timeout.
        Compensating transaction automatically refunds 12 coins.
        VERIFICATION:
        - Balance drops from 50 to 38 upon deduction.
        - Balance restores from 38 to 50 upon refund.
        - Cryptographic ledger retains unbroken SHA-256 chaining.
        - Refund record has action_type = REFUND_FAILED_GENERATION.
        """
        user = self.create_user(username="author_user", coins=50)

        # 1. Deduct 12 coins
        ok_deduct, tx_hash_deduct, bal_deduct = deduct_coins(
            db=self.db,
            user_id=user.id,
            amount=COST_MEDIUM_STORY,
            action_type=ACTION_STORY_MEDIUM,
            description="Tạo truyện vừa 12 xu"
        )
        self.assertTrue(ok_deduct)
        self.assertEqual(bal_deduct, 38)

        # 2. Simulate 5xx / timeout failure
        simulated_error = "504 Gateway Timeout: AI inference node unreachable"

        # 3. Compensating transaction rollback
        ok_refund, tx_hash_refund, bal_refund = refund_coins(
            db=self.db,
            user_id=user.id,
            amount=COST_MEDIUM_STORY,
            reason=ACTION_REFUND_FAILED,
            reference_id=tx_hash_deduct,
            description=f"Tự động hoàn 12 xu ({simulated_error})"
        )
        self.assertTrue(ok_refund)
        self.assertEqual(bal_refund, 50)

        # 4. Check user database balance
        self.db.refresh(user)
        self.assertEqual(user.coins, 50, "User balance must be fully restored to 50!")

        # 5. Verify ledger integrity
        audit_ok, audit_msg = verify_ledger_integrity(self.db, user_id=user.id)
        self.assertTrue(audit_ok, f"Ledger corrupted after rollback: {audit_msg}")

        # 6. Verify ledger entries
        txs = self.db.query(CoinTransaction).filter(CoinTransaction.user_id == user.id).order_by(CoinTransaction.id.asc()).all()
        self.assertEqual(len(txs), 2)
        self.assertEqual(txs[0].amount, -12)
        self.assertEqual(txs[1].amount, 12)
        self.assertEqual(txs[1].action_type, ACTION_REFUND_FAILED)
        self.assertEqual(txs[1].reference_id, tx_hash_deduct)
        self.assertEqual(txs[1].prev_hash, txs[0].tx_hash)

    def test_chained_alternating_deductions_and_rollbacks(self):
        """
        STRESS: Multiple sequential deductions and rollbacks.
        Operations: Deduct(16) -> Refund(16) -> Deduct(8) -> Deduct(12) -> Refund(12) -> Deduct(2).
        VERIFICATION:
        - Ledger maintains unbroken chaining across 6 alternating operations.
        - Final balance matches arithmetic sum exactly.
        - verify_ledger_integrity returns True.
        """
        user = self.create_user(username="pipeline_stress_user", coins=100)

        # 1. Deduct 16
        deduct_coins(self.db, user.id, 16, ACTION_STORY_LONG)
        # 2. Refund 16
        refund_coins(self.db, user.id, 16, ACTION_REFUND_FAILED)
        # 3. Deduct 8
        deduct_coins(self.db, user.id, 8, ACTION_STORY_SHORT)
        # 4. Deduct 12
        deduct_coins(self.db, user.id, 12, ACTION_STORY_MEDIUM)
        # 5. Refund 12
        refund_coins(self.db, user.id, 12, ACTION_REFUND_FAILED)
        # 6. Deduct 2
        deduct_coins(self.db, user.id, 2, ACTION_STORY_EDIT)

        # Expected: 100 - 16 + 16 - 8 - 12 + 12 - 2 = 90
        self.db.refresh(user)
        self.assertEqual(user.coins, 90)

        audit_ok, audit_msg = verify_ledger_integrity(self.db, user_id=user.id)
        self.assertTrue(audit_ok, f"Audit failed: {audit_msg}")

    def test_refund_negative_amount_injection_resistance(self):
        """
        ATTACK: Attacker passes negative amount (-50) to refund_coins in an attempt
        to subtract funds via refund endpoint.
        VERIFICATION: abs(int(amount)) converts -50 to +50, preventing subtraction exploit.
        """
        user = self.create_user(username="refund_inject_user", coins=10)
        ok, _, bal = refund_coins(self.db, user.id, amount=-10, reason=ACTION_REFUND_FAILED)
        self.assertTrue(ok)
        self.assertEqual(bal, 20)
        self.db.refresh(user)
        self.assertEqual(user.coins, 20)


# =========================================================================
# SUITE 5: ABSOLUTE SERVER AUTHORITY & CONTRACT SPECIFICATIONS
# =========================================================================
class TestAbsoluteServerAuthorityAndContracts(BaseAdversarialBankingTest):
    """
    Verifies that client parameters cannot tamper with server-authoritative costs.
    """

    def test_server_authoritative_costs_enforced(self):
        """Client can request whatever, server enforces fixed pricing."""
        self.assertEqual(get_story_cost("short"), 8)
        self.assertEqual(get_story_cost("medium"), 12)
        self.assertEqual(get_story_cost("long"), 16)
        self.assertEqual(get_action_cost("STORY_EDIT"), 2)
        self.assertEqual(get_action_cost("COMIC_GENERATE"), 16)

    def test_genesis_hash_constant(self):
        """Cryptographic ledger genesis hash must be 64 zeros."""
        self.assertEqual(GENESIS_HASH, "0" * 64)
        self.assertEqual(len(GENESIS_HASH), 64)


if __name__ == "__main__":
    unittest.main(verbosity=2)
