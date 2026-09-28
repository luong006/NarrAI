"""
Unit & Integration Test Suite for backend_integration_gen2:
1. Router Mounts in backend/main.py (coins, social, messenger)
2. Coin deductions and compensating rollback (REFUND_FAILED_GENERATION) in story generation & edit endpoints
3. Device fingerprint registration & initial trial coins in /api/register
4. Regex hardening in backend/services/ontology.py (re.DOTALL & \\s+)
"""

import os
import sys
import unittest
import json
from unittest.mock import patch, MagicMock

# Ensure backend root is on sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

from db.models import Base, User, Story, CoinTransaction, DeviceFingerprint, SubnetRecord
from main import app, get_db
from services.ontology import (
    NarrativeMode,
    HistoricalGroundingGatekeeper,
    SmartSelectiveLanguageFilter,
    VIETNAMESE_HISTORICAL_CANON,
    TRANSLATION_CLICHE_BANLIST,
)
from services.banking_service import (
    COST_SHORT_STORY,
    COST_MEDIUM_STORY,
    COST_LONG_STORY,
    COST_EDIT,
    COST_MANGA,
    ACTION_REFUND_FAILED,
    ACTION_INITIAL_GRANT,
    user_mutexes,
    verify_ledger_integrity,
)


class TestBackendIntegrationGen2(unittest.TestCase):
    def setUp(self):
        # Create in-memory database with StaticPool for thread-safe dependency injection
        self.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool
        )
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.db = self.SessionLocal()
        user_mutexes.reset()

        # Override dependency
        def override_get_db():
            db = self.SessionLocal()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.clear()
        self.db.close()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()
        user_mutexes.reset()

    # --------------------------------------------------------------------------
    # 1. ROUTER MOUNTS VERIFICATION
    # --------------------------------------------------------------------------
    def test_routers_mounted_in_fastapi_app(self):
        """Verify coins, social, and messenger routers are mounted with correct route prefixes."""
        routes = list(app.openapi().get("paths", {}).keys())
        
        # Coins router
        self.assertIn("/api/coins/balance", routes)
        self.assertIn("/api/coins/transactions", routes)
        self.assertIn("/api/coins/claim-trial", routes)
        self.assertIn("/api/coins/topup", routes)
        self.assertIn("/api/coins/deduct", routes)
        self.assertIn("/api/coins/refund", routes)

        # Social router
        self.assertIn("/api/social/feed", routes)
        self.assertIn("/api/social/publish", routes)
        self.assertIn("/api/social/interact", routes)

        # Messenger router
        self.assertIn("/api/messenger/users", routes)
        self.assertIn("/api/messenger/conversations", routes)
        self.assertIn("/api/messenger/unread-count", routes)

    # --------------------------------------------------------------------------
    # 2. ONTOLOGY REGEX HARDENING
    # --------------------------------------------------------------------------
    def test_historical_gatekeeper_catches_multiline_evasion(self):
        """
        Verify that HistoricalGroundingGatekeeper with re.DOTALL detects
        historical distortion payloads that contain newline '\\n' breaks.
        """
        multiline_payload = "Trần Hưng Đạo\nbại trận Bạch Đằng và đầu hàng quân Nguyên."
        is_valid, violations = HistoricalGroundingGatekeeper.validate_historical_invariants(
            multiline_payload, mode=NarrativeMode.CHINH_SU
        )
        self.assertFalse(is_valid, "Gatekeeper must reject multiline historical distortion!")
        self.assertTrue(any("Trần Hưng Đạo" in v for v in violations))

    def test_historical_gatekeeper_catches_battle_distortion_multiline(self):
        """Verify battle distortion regex matches across line breaks."""
        multiline_battle = "Trận Bạch Đằng\nquân ta thua to và Đại Việt thất bại."
        is_valid, violations = HistoricalGroundingGatekeeper.validate_historical_invariants(
            multiline_battle, mode=NarrativeMode.CHINH_SU
        )
        self.assertFalse(is_valid)
        self.assertTrue(any("Bạch Đằng" in v for v in violations))

    def test_translation_cliches_match_whitespace_variations(self):
        """Verify that \\s+ in TRANSLATION_CLICHE_BANLIST matches multi-space and tab variations."""
        test_samples = [
            "Dáng vẻ tiêu  sái đứng trước hiên nhà.",       # Double space
            "Nụ cười tà   mị của hắn khiến người run rẩy.", # Triple space
            "Ánh mắt lãnh\tkhốc nhìn thẳng kẻ địch.",       # Tab character
            "Bản\n  tọa quyết định xuất sơn.",             # Newline + spaces
        ]
        for sample in test_samples:
            is_clean, violations = SmartSelectiveLanguageFilter.validate_smart_language_compliance(
                sample, genre="Văn học hiện đại", narrative_mode=NarrativeMode.HU_CAU_TU_DO
            )
            self.assertFalse(is_clean, f"Expected whitespace variation to be caught: {sample}")
            self.assertTrue(len(violations) > 0)

    # --------------------------------------------------------------------------
    # 3. REGISTRATION WITH DEVICE FINGERPRINTING & TRIAL COINS
    # --------------------------------------------------------------------------
    def test_registration_with_fingerprint_grants_trial_coins(self):
        """Fresh registration with fingerprint should grant 8 trial coins."""
        payload = {
            "username": "fresh_user_01",
            "password": "Password123!",
            "full_name": "Người Dùng Mới",
            "fingerprint": {
                "canvas_hash": "canvas_test_hash_001",
                "webgl_hash": "webgl_test_hash_001",
                "audio_hash": "audio_test_hash_001",
                "screen_specs": "1920x1080x24"
            }
        }
        res = self.client.post("/api/register", json=payload, headers={"x-forwarded-for": "113.160.10.10"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data.get("status"), "success")
        self.assertEqual(data.get("coins"), 8)
        self.assertEqual(data.get("coins_granted"), 8)

        # Verify transaction logged
        user_in_db = self.db.query(User).filter_by(username="fresh_user_01").first()
        self.assertIsNotNone(user_in_db)
        self.assertEqual(user_in_db.coins, 8)

        tx = self.db.query(CoinTransaction).filter_by(user_id=user_in_db.id).first()
        self.assertIsNotNone(tx)
        self.assertEqual(tx.action_type, ACTION_INITIAL_GRANT)
        self.assertEqual(tx.amount, 8)

    def test_registration_clone_device_receives_zero_coins(self):
        """Duplicate device fingerprint should receive 0 initial coins."""
        fp = {
            "canvas_hash": "canvas_clone_hash",
            "webgl_hash": "webgl_clone_hash",
            "audio_hash": "audio_clone_hash",
            "screen_specs": "1920x1080x24"
        }
        # First registration
        r1 = self.client.post(
            "/api/register",
            json={"username": "genuine_acc", "password": "Password123!", "fingerprint": fp},
            headers={"x-forwarded-for": "113.160.11.1"}
        )
        self.assertEqual(r1.status_code, 200)
        self.assertEqual(r1.json().get("coins"), 8)

        # Second registration with identical fingerprint from different IP
        r2 = self.client.post(
            "/api/register",
            json={"username": "clone_acc", "password": "Password123!", "fingerprint": fp},
            headers={"x-forwarded-for": "113.160.99.99"}
        )
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r2.json().get("coins"), 0)
        self.assertEqual(r2.json().get("coins_granted"), 0)

    # --------------------------------------------------------------------------
    # 4. COIN DEDUCTIONS & COMPENSATING ROLLBACK IN EDIT & COMIC ENDPOINTS
    # --------------------------------------------------------------------------
    def test_edit_text_insufficient_coins_returns_402(self):
        """Edit text endpoint requires 2 coins; 0 coins returns HTTP 402."""
        from auth import create_access_token, get_password_hash
        user = User(username="poor_editor", password_hash=get_password_hash("Pass123!"), coins=0)
        self.db.add(user)
        self.db.commit()
        token = create_access_token({"sub": "poor_editor"})

        res = self.client.post(
            "/api/edit-text",
            json={"original_text": "Đoạn văn cần sửa", "instruction": "Sửa hay hơn"},
            headers={"Authorization": f"Bearer {token}"}
        )
        self.assertEqual(res.status_code, 402)
        self.assertIn("Số dư xu không đủ", res.json().get("detail", ""))

    def test_edit_text_deducts_coins_on_success(self):
        """Edit text endpoint deducts 2 coins on successful revision."""
        from auth import create_access_token, get_password_hash
        user = User(username="rich_editor", password_hash=get_password_hash("Pass123!"), coins=10)
        self.db.add(user)
        self.db.commit()
        token = create_access_token({"sub": "rich_editor"})

        with patch("agents.editor_agent.EditorAgent.edit_text", return_value="Văn bản đã sửa cực hay"):
            res = self.client.post(
                "/api/edit-text",
                json={"original_text": "Văn bản cũ", "instruction": "Chỉnh sửa"},
                headers={"Authorization": f"Bearer {token}"}
            )
            self.assertEqual(res.status_code, 200)
            self.assertEqual(res.json().get("status"), "success")

        # Refresh user balance
        self.db.refresh(user)
        self.assertEqual(user.coins, 8)

    def test_edit_text_compensating_rollback_on_agent_failure(self):
        """When EditorAgent throws an unexpected exception, 100% of deducted coins are refunded."""
        from auth import create_access_token, get_password_hash
        user = User(username="failing_editor", password_hash=get_password_hash("Pass123!"), coins=10)
        self.db.add(user)
        self.db.commit()
        token = create_access_token({"sub": "failing_editor"})

        with patch("agents.editor_agent.EditorAgent.edit_text", side_effect=RuntimeError("Groq 503 Service Unavailable")):
            res = self.client.post(
                "/api/edit-text",
                json={"original_text": "Văn bản cũ", "instruction": "Chỉnh sửa"},
                headers={"Authorization": f"Bearer {token}"}
            )
            self.assertEqual(res.status_code, 200)
            self.assertEqual(res.json().get("status"), "error")

        # Balance must be fully restored to 10
        self.db.refresh(user)
        self.assertEqual(user.coins, 10)

        # Transactions must show deduction then REFUND_FAILED_GENERATION
        txs = self.db.query(CoinTransaction).filter_by(user_id=user.id).order_by(CoinTransaction.id.asc()).all()
        self.assertEqual(len(txs), 2)
        self.assertEqual(txs[0].amount, -2)
        self.assertEqual(txs[1].amount, 2)
        self.assertEqual(txs[1].action_type, ACTION_REFUND_FAILED)

        # Cryptographic ledger audit must pass cleanly
        audit_ok, audit_msg = verify_ledger_integrity(self.db, user_id=user.id)
        self.assertTrue(audit_ok, f"Ledger broken after rollback: {audit_msg}")

    def test_comic_generate_deducts_16_coins_and_rolls_back_on_failure(self):
        """Comic generation deducts 16 coins and triggers compensating rollback if director fails."""
        from auth import create_access_token, get_password_hash
        user = User(username="manga_creator", password_hash=get_password_hash("Pass123!"), coins=20)
        self.db.add(user)
        self.db.commit()
        story = Story(user_id=user.id, refined_prompt="Manga prompt", story_content="Nội dung truyện rất dài...")
        self.db.add(story)
        self.db.commit()
        token = create_access_token({"sub": "manga_creator"})

        with patch("agents.comic_agent.ComicDirectorAgent.generate_comic_script", side_effect=Exception("Diffusion API Error")):
            res = self.client.post(
                "/api/comic/generate",
                json={"story_id": story.id, "story_text": story.story_content},
                headers={"Authorization": f"Bearer {token}"}
            )
            self.assertEqual(res.status_code, 200)
            self.assertEqual(res.json().get("status"), "error")

        # Coins restored to 20
        self.db.refresh(user)
        self.assertEqual(user.coins, 20)

        # Cryptographic ledger audit passes
        audit_ok, audit_msg = verify_ledger_integrity(self.db, user_id=user.id)
        self.assertTrue(audit_ok, f"Ledger broken: {audit_msg}")


if __name__ == "__main__":
    unittest.main()
