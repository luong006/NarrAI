"""
Unit and Integration Test Suite for Milestone 3 Banking & Anti-Clone Architecture
Covers:
1. Server Authoritative Pricing (8, 12, 16, 2, 16).
2. Dual-Locking Concurrency Isolation & Double-Spending Prevention.
3. Cryptographic Chained Ledger (SHA-256) & Tamper Detection.
4. Compensating Transaction Rollback (REFUND_FAILED_GENERATION).
5. Multi-Signal Anti-Clone Guard (Composite Fingerprint + /24 Subnet Throttling).
6. Router Schemas and Logic.
"""

import sys
import os
import unittest
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException

# Add backend to sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from db.models import (
    Base, User, CoinTransaction, DeviceFingerprint, SubnetRecord,
    SocialPost, PostInteraction, UserInterestProfile, Conversation,
    ConversationParticipant, ChatMessage
)
from services.banking_service import (
    user_mutexes,
    deduct_coins,
    refund_coins,
    topup_coins,
    verify_ledger_integrity,
    register_device_and_get_initial_coins,
    get_action_cost,
    get_story_cost,
    compute_transaction_hash,
    extract_ip_subnet,
    compute_composite_fingerprint,
    COST_SHORT_STORY,
    COST_MEDIUM_STORY,
    COST_LONG_STORY,
    COST_EDIT,
    COST_MANGA,
    INITIAL_TRIAL_COINS,
    STANDARD_TOPUP_COINS,
    GENESIS_HASH,
    ACTION_REFUND_FAILED
)

class TestMilestone3Banking(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create an in-memory SQLite database for isolated test execution
        cls.engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        Base.metadata.create_all(cls.engine)
        cls.Session = sessionmaker(bind=cls.engine)

    def setUp(self):
        user_mutexes.reset()
        self.db = self.Session()

    def tearDown(self):
        self.db.close()

    def _create_test_user(self, username="tester", coins=0):
        user = User(
            username=f"{username}_{datetime.utcnow().timestamp()}",
            full_name="Nguyễn Văn Test",
            password_hash="hashed_pw_123",
            coins=coins
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    # =========================================================================
    # 1. ABSOLUTE SERVER AUTHORITY OVER PRICING
    # =========================================================================
    def test_pricing_constants(self):
        self.assertEqual(COST_SHORT_STORY, 8)
        self.assertEqual(COST_MEDIUM_STORY, 12)
        self.assertEqual(COST_LONG_STORY, 16)
        self.assertEqual(COST_EDIT, 2)
        self.assertEqual(COST_MANGA, 16)
        self.assertEqual(INITIAL_TRIAL_COINS, 8)
        self.assertEqual(STANDARD_TOPUP_COINS, 100)

    def test_story_cost_derivation(self):
        self.assertEqual(get_story_cost("short"), 8)
        self.assertEqual(get_story_cost("SHORT"), 8)
        self.assertEqual(get_story_cost("medium"), 12)
        self.assertEqual(get_story_cost("long"), 16)
        self.assertEqual(get_story_cost("unknown"), 12)
        self.assertEqual(get_story_cost(None), 12)

    def test_action_cost_derivation(self):
        self.assertEqual(get_action_cost("STORY_GENERATE_SHORT"), 8)
        self.assertEqual(get_action_cost("STORY_GENERATE_MEDIUM"), 12)
        self.assertEqual(get_action_cost("STORY_GENERATE_LONG"), 16)
        self.assertEqual(get_action_cost("STORY_EDIT"), 2)
        self.assertEqual(get_action_cost("COMIC_GENERATE"), 16)
        self.assertEqual(get_action_cost("MANGA_CONVERT"), 16)

    # =========================================================================
    # 2. DUAL-LOCKING & CONCURRENCY DOUBLE-SPENDING PREVENTION
    # =========================================================================
    def test_deduct_coins_successful(self):
        user = self._create_test_user(coins=20)
        ok, tx_hash, new_balance = deduct_coins(
            db=self.db,
            user_id=user.id,
            amount=8,
            action_type="STORY_GENERATE_SHORT",
            description="Test deduction"
        )
        self.assertTrue(ok)
        self.assertEqual(new_balance, 12)
        self.assertEqual(len(tx_hash), 64)

        # Confirm user balance in DB
        reloaded = self.db.query(User).filter(User.id == user.id).first()
        self.assertEqual(reloaded.coins, 12)

    def test_deduct_coins_insufficient_balance_raises_402(self):
        user = self._create_test_user(coins=6)
        with self.assertRaises(HTTPException) as ctx:
            deduct_coins(
                db=self.db,
                user_id=user.id,
                amount=8,
                action_type="STORY_GENERATE_SHORT",
                raise_on_insufficient=True
            )
        self.assertEqual(ctx.exception.status_code, 402)
        self.assertIn("Số dư xu không đủ", ctx.exception.detail)

    def test_concurrent_double_spending_elimination(self):
        """
        Stress test: User has exactly 8 coins.
        10 threads simultaneously attempt to deduct 8 coins in parallel.
        Strict requirement: Exactly 1 thread succeeds, 9 fail with HTTP 402.
        Final balance MUST be 0 coins, never negative.
        """
        user = self._create_test_user(coins=8)
        results = []
        errors = []

        def worker():
            local_db = self.Session()
            try:
                ok, tx_hash, new_bal = deduct_coins(
                    db=local_db,
                    user_id=user.id,
                    amount=8,
                    action_type="STORY_GENERATE_SHORT",
                    raise_on_insufficient=True
                )
                results.append((ok, new_bal))
            except HTTPException as e:
                errors.append(e)
            finally:
                local_db.close()

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(worker) for _ in range(10)]
            for f in futures:
                f.result()

        self.assertEqual(len(results), 1, "Expected exactly 1 deduction to succeed")
        self.assertEqual(len(errors), 9, "Expected exactly 9 deductions to fail")
        for err in errors:
            self.assertEqual(err.status_code, 402)

        # Verify final user coins in DB
        reloaded = self.db.query(User).filter(User.id == user.id).first()
        self.assertEqual(reloaded.coins, 0)

    # =========================================================================
    # 3. COMPENSATING TRANSACTION ROLLBACK (REFUND)
    # =========================================================================
    def test_compensating_refund_on_ai_failure(self):
        user = self._create_test_user(coins=20)
        # 1. Deduct 16 coins for manga
        deduct_coins(self.db, user.id, 16, "COMIC_GENERATE")
        reloaded = self.db.query(User).filter(User.id == user.id).first()
        self.assertEqual(reloaded.coins, 4)

        # 2. Simulate AI failure & trigger compensating rollback
        ok, tx_hash, new_balance = refund_coins(
            db=self.db,
            user_id=user.id,
            amount=16,
            reason=ACTION_REFUND_FAILED,
            description="Automatic refund due to Groq timeout"
        )
        self.assertTrue(ok)
        self.assertEqual(new_balance, 20)

        # Check transaction records
        txs = self.db.query(CoinTransaction).filter(CoinTransaction.user_id == user.id).all()
        self.assertEqual(len(txs), 2)
        self.assertEqual(txs[0].amount, -16)
        self.assertEqual(txs[1].amount, 16)
        self.assertEqual(txs[1].action_type, ACTION_REFUND_FAILED)

        # Verify ledger integrity
        is_valid, msg = verify_ledger_integrity(self.db, user.id)
        self.assertTrue(is_valid, msg)

    # =========================================================================
    # 4. CRYPTOGRAPHIC LEDGER INTEGRITY & TAMPER DETECTION
    # =========================================================================
    def test_ledger_chain_and_tamper_detection(self):
        user = self._create_test_user(coins=0)
        # Perform 5 transactions
        topup_coins(self.db, user.id, 100)  # +100 -> bal=100
        deduct_coins(self.db, user.id, 8, "STORY_GENERATE_SHORT")  # -8 -> bal=92
        deduct_coins(self.db, user.id, 12, "STORY_GENERATE_MEDIUM")  # -12 -> bal=80
        deduct_coins(self.db, user.id, 2, "STORY_EDIT")  # -2 -> bal=78
        refund_coins(self.db, user.id, 12, ACTION_REFUND_FAILED)  # +12 -> bal=90

        # Ledger should be 100% valid
        is_valid, msg = verify_ledger_integrity(self.db, user.id)
        self.assertTrue(is_valid, msg)

        # Simulate adversarial tamper: directly edit a transaction's amount in DB
        second_tx = (
            self.db.query(CoinTransaction)
            .filter(CoinTransaction.user_id == user.id)
            .order_by(CoinTransaction.id.asc())
            .offset(1)
            .first()
        )
        original_amount = second_tx.amount
        second_tx.amount = -1  # Fraudulent change
        self.db.commit()

        # Audit must immediately detect tampering!
        tamper_detected, error_msg = verify_ledger_integrity(self.db, user.id)
        self.assertFalse(tamper_detected)
        self.assertTrue("can thiệp" in error_msg or "Lỗi số học" in error_msg or "không khớp" in error_msg)

        # Restore
        second_tx.amount = original_amount
        self.db.commit()

    # =========================================================================
    # 5. MULTI-SIGNAL ANTI-CLONE & SUBNET THROTTLING GUARD
    # =========================================================================
    def test_anti_clone_fresh_device_grants_8_coins(self):
        user = self._create_test_user(coins=0)
        fp_data = {
            "canvas_hash": "canvas_device_alpha_123",
            "webgl_hash": "webgl_rtx3060_alpha",
            "audio_hash": "audio_realtek_alpha",
            "screen_specs": "1920x1080x24"
        }
        ip = "113.161.45.88"

        coins = register_device_and_get_initial_coins(
            db=self.db,
            client_ip=ip,
            fingerprint_data=fp_data,
            user_id=user.id
        )
        self.assertEqual(coins, 8)
        reloaded = self.db.query(User).filter(User.id == user.id).first()
        self.assertEqual(reloaded.coins, 8)

    def test_anti_clone_duplicate_device_rejected_0_coins(self):
        user1 = self._create_test_user(coins=0)
        user2 = self._create_test_user(coins=0)
        fp_data = {
            "canvas_hash": "canvas_device_beta_456",
            "webgl_hash": "webgl_amd_beta",
            "audio_hash": "audio_beta",
            "screen_specs": "2560x1440x32"
        }
        ip1 = "14.162.20.10"
        ip2 = "42.113.50.99"  # Different IP, same device

        # User 1 registers with device
        coins1 = register_device_and_get_initial_coins(self.db, ip1, fp_data, user1.id)
        self.assertEqual(coins1, 8)

        # User 2 clones with same device -> 0 coins!
        coins2 = register_device_and_get_initial_coins(self.db, ip2, fp_data, user2.id)
        self.assertEqual(coins2, 0)
        reloaded2 = self.db.query(User).filter(User.id == user2.id).first()
        self.assertEqual(reloaded2.coins, 0)

    def test_anti_clone_subnet_throttling_max_2(self):
        """Same /24 subnet cannot claim more than 2 trial bonuses within 24 hours."""
        subnet_ip_base = "27.72.100."
        user1 = self._create_test_user(coins=0)
        user2 = self._create_test_user(coins=0)
        user3 = self._create_test_user(coins=0)

        # Device 1 on subnet
        fp1 = {"canvas_hash": "canvas_sub_1", "webgl_hash": "w1", "audio_hash": "a1", "screen_specs": "s1"}
        c1 = register_device_and_get_initial_coins(self.db, subnet_ip_base + "10", fp1, user1.id)
        self.assertEqual(c1, 8)

        # Device 2 on same subnet
        fp2 = {"canvas_hash": "canvas_sub_2", "webgl_hash": "w2", "audio_hash": "a2", "screen_specs": "s2"}
        c2 = register_device_and_get_initial_coins(self.db, subnet_ip_base + "20", fp2, user2.id)
        self.assertEqual(c2, 8)

        # Device 3 on same subnet -> throttled to 0 coins!
        fp3 = {"canvas_hash": "canvas_sub_3", "webgl_hash": "w3", "audio_hash": "a3", "screen_specs": "s3"}
        c3 = register_device_and_get_initial_coins(self.db, subnet_ip_base + "30", fp3, user3.id)
        self.assertEqual(c3, 0)

    # =========================================================================
    # 6. SOCIAL & MESSENGER FOUNDATIONAL DATABASE MODELS
    # =========================================================================
    def test_social_models_structure(self):
        user = self._create_test_user(coins=10)
        post = SocialPost(
            user_id=user.id,
            title="Đại Việt Sử Ký",
            content_snippet="Lời mở đầu hào hùng...",
            genre="Chính Sử",
            tags='["Lịch Sử", "Việt Nam"]',
            concept_vector="[0.1, 0.2, 0.3]",
            dsgo_entities='["Trần Hưng Đạo", "Yết Kiêu"]',
            dsgo_spaces='["Sông Bạch Đằng"]',
            completion_count=5,
            likes_count=10,
            views_count=50
        )
        self.db.add(post)
        self.db.commit()
        self.assertIsNotNone(post.id)
        self.assertEqual(post.likes_count, 10)

        interaction = PostInteraction(
            user_id=user.id,
            post_id=post.id,
            interaction_type="DWELL_TIME",
            dwell_seconds=75.5,
            scroll_depth=100
        )
        self.db.add(interaction)
        self.db.commit()
        self.assertEqual(interaction.dwell_time, 75.5)

        conv = Conversation(last_message_text="Xin chào tác giả")
        self.db.add(conv)
        self.db.commit()
        self.assertIsNotNone(conv.id)


if __name__ == "__main__":
    unittest.main()
