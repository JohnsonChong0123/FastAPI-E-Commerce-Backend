# tests/core/test_security.py
import pytest
import bcrypt
from core.security import hash_password, verify_password, needs_upgrade


class TestHashPassword:

    def test_hash_password_returns_string(self):
        """hash_password returns a non-empty string."""
        result = hash_password("Secret1234!")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_hash_is_not_plaintext(self):
        """Hashed password is never equal to the plaintext input."""
        result = hash_password("Secret1234!")
        assert result != "Secret1234!"

    def test_hash_uses_argon2_by_default(self):
        """New hashes always use Argon2 as the primary algorithm."""
        result = hash_password("Secret1234!")
        assert result.startswith("$argon2")

    def test_same_password_produces_different_hashes(self):
        """Same password hashed twice produces different hashes (random salt)."""
        hash1 = hash_password("Secret1234!")
        hash2 = hash_password("Secret1234!")
        assert hash1 != hash2

    def test_empty_password_raises_error(self):
        """Empty password should raise ValueError."""
        with pytest.raises(ValueError):
            hash_password("")


class TestVerifyPassword:

    def test_verify_correct_password_returns_true(self):
        """Correct password verifies successfully against its hash."""
        hashed = hash_password("Secret1234!")
        assert verify_password("Secret1234!", hashed) is True

    def test_verify_wrong_password_returns_false(self):
        """Wrong password fails verification."""
        hashed = hash_password("Secret1234!")
        assert verify_password("WrongPass99!", hashed) is False

    def test_verify_invalid_hash_returns_false(self):
        """Corrupted or invalid hash returns False instead of raising."""
        assert verify_password("Secret1234!", "not-a-valid-hash") is False

    def test_verify_empty_password_returns_false(self):
        """Empty password input returns False."""
        hashed = hash_password("Secret1234!")
        assert verify_password("", hashed) is False

    def test_verify_legacy_bcrypt_hash(self):
        """Correct password verifies successfully against legacy Bcrypt hash."""
        legacy_hash = bcrypt.hashpw(
            "Secret1234!".encode(), bcrypt.gensalt()
        ).decode()
        assert verify_password("Secret1234!", legacy_hash) is True

    def test_verify_wrong_password_against_bcrypt_returns_false(self):
        """Wrong password fails against legacy Bcrypt hash."""
        legacy_hash = bcrypt.hashpw(
            "Secret1234!".encode(), bcrypt.gensalt()
        ).decode()
        assert verify_password("WrongPass99!", legacy_hash) is False


class TestNeedsUpgrade:

    def test_argon2_hash_does_not_need_upgrade(self):
        """Fresh Argon2 hash should not need upgrading."""
        argon2_hash = hash_password("Secret1234!")
        assert needs_upgrade(argon2_hash) is False

    def test_bcrypt_hash_needs_upgrade(self):
        """Legacy Bcrypt hash should be flagged for upgrade."""
        legacy_hash = bcrypt.hashpw(
            "Secret1234!".encode(), bcrypt.gensalt()
        ).decode()
        assert needs_upgrade(legacy_hash) is True