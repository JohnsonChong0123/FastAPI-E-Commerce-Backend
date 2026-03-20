# tests/services/test_login_services.py
import pytest
import bcrypt
from exceptions.auth_exceptions import InvalidCredentialsError
from models.user_model import User
from core.security import hash_password
from core.jwt import decode_token
from services.auth.login_services import login
from schemas.auth.login_request import LoginRequest

# ==============================================================================
# Happy Path Tests
# ==============================================================================

class TestLoginServiceHappyPath:

    def test_login_success_returns_response(self, db_session, registered_user):
        """Valid credentials return a response."""
        data = LoginRequest(email="john@example.com", password="Secret1234!")
        result = login(db_session, data)
        assert result is not None

    def test_login_returns_access_token(self, db_session, registered_user):
        """Response contains a non-empty access token."""
        data = LoginRequest(email="john@example.com", password="Secret1234!")
        result = login(db_session, data)
        assert "access_token" in result
        assert len(result["access_token"]) > 0

    def test_login_returns_refresh_token(self, db_session, registered_user):
        """Response contains a non-empty refresh token."""
        data = LoginRequest(email="john@example.com", password="Secret1234!")
        result = login(db_session, data)
        assert "refresh_token" in result
        assert len(result["refresh_token"]) > 0

    def test_login_returns_correct_provider(self, db_session, registered_user):
        """Response contains the correct provider."""
        data = LoginRequest(email="john@example.com", password="Secret1234!")
        result = login(db_session, data)
        assert result["provider"] == "email"

    def test_login_returns_user_object(self, db_session, registered_user):
        """Response contains the correct user object."""
        data = LoginRequest(email="john@example.com", password="Secret1234!")
        result = login(db_session, data)
        assert result["user"].email == "john@example.com"

    def test_login_access_token_contains_correct_user_id(self, db_session, registered_user):
        """Access token encodes the correct user ID."""
        data = LoginRequest(email="john@example.com", password="Secret1234!")
        result = login(db_session, data)
        payload = decode_token(result["access_token"])
        assert payload["sub"] == str(registered_user.id)

    def test_login_refresh_token_contains_correct_user_id(self, db_session, registered_user):
        """Refresh token encodes the correct user ID."""
        data = LoginRequest(email="john@example.com", password="Secret1234!")
        result = login(db_session, data)
        payload = decode_token(result["refresh_token"])
        assert payload["sub"] == str(registered_user.id)

    def test_login_access_token_has_correct_type(self, db_session, registered_user):
        """Access token payload type is 'access'."""
        data = LoginRequest(email="john@example.com", password="Secret1234!")
        result = login(db_session, data)
        payload = decode_token(result["access_token"])
        assert payload["type"] == "access"

    def test_login_refresh_token_has_correct_type(self, db_session, registered_user):
        """Refresh token payload type is 'refresh'."""
        data = LoginRequest(email="john@example.com", password="Secret1234!")
        result = login(db_session, data)
        payload = decode_token(result["refresh_token"])
        assert payload["type"] == "refresh"


# ==============================================================================
# Error Path Tests
# ==============================================================================

class TestLoginServiceErrorPath:

    def test_user_not_found_raises_invalid_credentials(self, db_session):
        """Non-existent email raises InvalidCredentialsError."""
        data = LoginRequest(email="nobody@example.com", password="Secret1234!")
        with pytest.raises(InvalidCredentialsError):
            login(db_session, data)

    def test_wrong_password_raises_invalid_credentials(self, db_session, registered_user):
        """Wrong password raises InvalidCredentialsError."""
        data = LoginRequest(email="john@example.com", password="WrongPass99!")
        with pytest.raises(InvalidCredentialsError):
            login(db_session, data)

    def test_invalid_email_and_wrong_password_raise_same_error(self, db_session, registered_user):
        """Both wrong email and wrong password raise the same error — no info leak."""
        with pytest.raises(InvalidCredentialsError):
            login(db_session, LoginRequest(
                email="nobody@example.com", password="Secret1234!"
            ))
        with pytest.raises(InvalidCredentialsError):
            login(db_session, LoginRequest(
                email="john@example.com", password="WrongPass99!"
            ))


# ==============================================================================
# Password Upgrade Tests
# ==============================================================================

class TestLoginServicePasswordUpgrade:

    def test_legacy_bcrypt_hash_is_upgraded_on_login(self, db_session, legacy_user):
        """Bcrypt hash is upgraded to Argon2 after successful login."""
        original_hash = legacy_user.password_hash
        data = LoginRequest(email="jane@example.com", password="Secret1234!")
        login(db_session, data)
        db_session.refresh(legacy_user)
        assert legacy_user.password_hash != original_hash
        assert legacy_user.password_hash.startswith("$argon2")

    def test_argon2_hash_is_not_upgraded(self, db_session, registered_user):
        """Argon2 hash is not changed on login — already modern."""
        original_hash = registered_user.password_hash
        data = LoginRequest(email="john@example.com", password="Secret1234!")
        login(db_session, data)
        db_session.refresh(registered_user)
        assert registered_user.password_hash == original_hash

    def test_login_still_succeeds_after_hash_upgrade(self, db_session, legacy_user):
        """Login returns valid tokens even when hash upgrade happens."""
        data = LoginRequest(email="jane@example.com", password="Secret1234!")
        result = login(db_session, data)
        assert "access_token" in result
        assert "refresh_token" in result