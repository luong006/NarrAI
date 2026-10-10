import os
import sys
import unittest
from unittest.mock import MagicMock

# Ensure backend directory is in sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

os.environ.setdefault("SECRET_KEY", "test-secret-key-for-bank-auth-tests-2026")

from auth import validate_bank_password, LoginRateLimiter
from db.models import User, Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException


class TestBankPasswordValidation(unittest.TestCase):
    """
    Unit tests for bank-grade password complexity validator.
    Rules:
    - Length >= 8
    - At least 1 uppercase (A-Z)
    - At least 1 lowercase (a-z)
    - At least 1 digit (0-9)
    - At least 1 special character (!@#$%^&*...)
    - No whitespace allowed
    """

    def test_valid_passwords(self):
        valid_samples = [
            "StrongPass123!",
            "CyberP@ssw0rd99#",
            "V13tN@m2026$",
            "AlphaBeta123!",
            "A1b2C3d4@#$%",
            "MangaNarrAI_2026!",
        ]
        for pwd in valid_samples:
            is_valid, err_vi, err_en = validate_bank_password(pwd)
            self.assertTrue(is_valid, f"Expected '{pwd}' to be valid, but got: {err_vi} / {err_en}")
            self.assertEqual(err_vi, "")
            self.assertEqual(err_en, "")

    def test_short_passwords(self):
        short_samples = ["", "A1!", "Short1!", "P@ss1", "Ab1!"]
        for pwd in short_samples:
            is_valid, err_vi, err_en = validate_bank_password(pwd)
            self.assertFalse(is_valid, f"Expected '{pwd}' to fail length check")
            self.assertIn("tối thiểu 8 ký tự", err_vi)
            self.assertIn("at least 8 characters", err_en)

    def test_none_password(self):
        is_valid, err_vi, err_en = validate_bank_password(None)
        self.assertFalse(is_valid)
        self.assertIn("tối thiểu 8 ký tự", err_vi)

    def test_missing_uppercase(self):
        pwd = "lowercase123!@"
        is_valid, err_vi, err_en = validate_bank_password(pwd)
        self.assertFalse(is_valid)
        self.assertIn("chữ in hoa", err_vi)
        self.assertIn("uppercase", err_en)

    def test_missing_lowercase(self):
        pwd = "UPPERCASE123!@"
        is_valid, err_vi, err_en = validate_bank_password(pwd)
        self.assertFalse(is_valid)
        self.assertIn("chữ thường", err_vi)
        self.assertIn("lowercase", err_en)

    def test_missing_digit(self):
        pwd = "NoDigitsHere!@#"
        is_valid, err_vi, err_en = validate_bank_password(pwd)
        self.assertFalse(is_valid)
        self.assertIn("chữ số", err_vi)
        self.assertIn("digit", err_en)

    def test_missing_special_char(self):
        pwd = "NoSpecialChar123"
        is_valid, err_vi, err_en = validate_bank_password(pwd)
        self.assertFalse(is_valid)
        self.assertIn("ký tự đặc biệt", err_vi)
        self.assertIn("special character", err_en)

    def test_whitespace_prohibited(self):
        whitespace_samples = [
            "Space In Pass123!",
            " Leading123!@",
            "Trailing123!@ ",
            "Tab\tPass123!@",
            "New\nLine123!@",
        ]
        for pwd in whitespace_samples:
            is_valid, err_vi, err_en = validate_bank_password(pwd)
            self.assertFalse(is_valid, f"Expected '{pwd}' to fail whitespace check")
            self.assertIn("khoảng trắng", err_vi)
            self.assertIn("whitespace", err_en)


class TestLoginRateLimiter(unittest.TestCase):
    """
    Unit tests for LoginRateLimiter brute-force defense.
    - 5 failed attempts trigger 60s lockout (HTTP 429)
    - Successful login resets the counter
    - Case-insensitive on username and strips whitespace
    """

    def setUp(self):
        self.limiter = LoginRateLimiter(max_failures=5, lockout_seconds=60, window_seconds=300)

    def test_rate_limiter_lockout_after_5_failures(self):
        ip = "192.168.1.100"
        user = "testuser"

        # Attempts 1 to 4 should not trigger lockout
        for i in range(1, 5):
            locked, rem = self.limiter.record_failure(ip, user)
            self.assertFalse(locked, f"Attempt {i} should not lock user out")
            self.assertEqual(rem, 0)
            is_l, _ = self.limiter.is_locked(ip, user)
            self.assertFalse(is_l)

        # 5th attempt must trigger lockout
        locked, rem = self.limiter.record_failure(ip, user)
        self.assertTrue(locked, "5th failed attempt must trigger lockout")
        self.assertGreater(rem, 0)
        self.assertLessEqual(rem, 60)

        # is_locked should now be True
        is_l, rem2 = self.limiter.is_locked(ip, user)
        self.assertTrue(is_l)
        self.assertGreater(rem2, 0)

        # check_rate_limit must raise HTTPException(429)
        with self.assertRaises(HTTPException) as cm:
            self.limiter.check_rate_limit(ip, user)
        self.assertEqual(cm.exception.status_code, 429)
        self.assertIn("Đăng nhập thất bại quá nhiều lần", cm.exception.detail)
        self.assertIn("Too many failed login attempts", cm.exception.detail)

    def test_rate_limiter_reset_on_success(self):
        ip = "10.0.0.1"
        user = "alice"

        # Record 4 failures
        for _ in range(4):
            self.limiter.record_failure(ip, user)

        # Successful login clears failures
        self.limiter.record_success(ip, user)

        # Another 4 failures should still not lock because counter was reset
        for i in range(4):
            locked, _ = self.limiter.record_failure(ip, user)
            self.assertFalse(locked)

    def test_different_users_and_ips_isolated(self):
        self.limiter.record_failure("1.1.1.1", "bob")
        self.limiter.record_failure("1.1.1.1", "bob")
        self.limiter.record_failure("1.1.1.1", "bob")
        self.limiter.record_failure("1.1.1.1", "bob")
        locked_bob, _ = self.limiter.record_failure("1.1.1.1", "bob")
        self.assertTrue(locked_bob)

        # Charlie from same IP should not be locked
        is_charlie_locked, _ = self.limiter.is_locked("1.1.1.1", "charlie")
        self.assertFalse(is_charlie_locked)

        # Bob from different IP should not be locked
        is_bob_other_ip_locked, _ = self.limiter.is_locked("2.2.2.2", "bob")
        self.assertFalse(is_bob_other_ip_locked)


class TestUserModelAndDatabase(unittest.TestCase):
    """
    Verifies User model schema includes full_name and saves correctly.
    """

    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def test_user_full_name_storage(self):
        db = self.Session()
        user = User(
            username="nguyenvana",
            full_name="Nguyễn Văn A",
            password_hash="fake_hash_123"
        )
        db.add(user)
        db.commit()

        saved = db.query(User).filter(User.username == "nguyenvana").first()
        self.assertIsNotNone(saved)
        self.assertEqual(saved.full_name, "Nguyễn Văn A")
        self.assertEqual(saved.username, "nguyenvana")
        db.close()

    def test_user_full_name_default(self):
        db = self.Session()
        user = User(
            username="user_no_name",
            password_hash="fake_hash_456"
        )
        db.add(user)
        db.commit()

        saved = db.query(User).filter(User.username == "user_no_name").first()
        self.assertIsNotNone(saved)
        # Default or empty string
        self.assertIn(saved.full_name, ["", None])
        # Display fallback
        display_name = saved.full_name or saved.username
        self.assertEqual(display_name, "user_no_name")
        db.close()


if __name__ == "__main__":
    unittest.main()
