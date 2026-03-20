# tests/services/test_google_login_service.py
import pytest
from unittest.mock import patch
from exceptions.auth_exceptions import (
    InvalidGoogleTokenError,
    AuthProviderMismatchError
)
from models.user_model import User
from core.security import hash_password
from core.jwt import decode_token
from services.auth.google_login_services import login_with_google

# ==============================================================================
# FIXTURES
# ==============================================================================

PATCH_PATH = "services.auth.google_login_services.verify_google_token"

# ==============================================================================
# Invalid Token Tests
# ==============================================================================

class TestInvalidToken:

    def test_invalid_token_raises_error(self, db_session):
        """None return from verify raises InvalidGoogleTokenError."""
        with patch(PATCH_PATH) as mock_verify:
            mock_verify.return_value = None
            with pytest.raises(InvalidGoogleTokenError):
                login_with_google(db_session, "invalid.token")

    def test_invalid_token_does_not_create_user(self, db_session):
        """No user is created when token is invalid."""
        with patch(PATCH_PATH) as mock_verify:
            mock_verify.return_value = None
            try:
                login_with_google(db_session, "invalid.token")
            except InvalidGoogleTokenError:
                pass
            assert db_session.query(User).count() == 0


# ==============================================================================
# New User Creation Tests
# ==============================================================================

class TestNewUserCreation:

    def test_new_user_is_created_in_db(self, db_session, mock_google_user):
        """New user is saved to DB on first Google login."""
        with patch(PATCH_PATH) as mock_verify:
            mock_verify.return_value = mock_google_user
            login_with_google(db_session, "valid.token")
            user = db_session.query(User).filter_by(email="john@gmail.com").first()
            assert user is not None

    def test_new_user_has_correct_fields(self, db_session, mock_google_user):
        """New user fields are populated from Google user info."""
        with patch(PATCH_PATH) as mock_verify:
            mock_verify.return_value = mock_google_user
            login_with_google(db_session, "valid.token")
            user = db_session.query(User).filter_by(email="john@gmail.com").first()
            assert user.first_name == "John"
            assert user.last_name == "Doe"
            assert user.email == "john@gmail.com"
            assert user.provider == "google"
            assert user.image_url == "https://picture.url"

    def test_new_google_user_has_no_password_hash(self, db_session, mock_google_user):
        """Google users have no password hash."""
        with patch(PATCH_PATH) as mock_verify:
            mock_verify.return_value = mock_google_user
            login_with_google(db_session, "valid.token")
            user = db_session.query(User).filter_by(email="john@gmail.com").first()
            assert user.password_hash is None


# ==============================================================================
# Name Parsing Tests
# ==============================================================================

class TestNameParsing:

    def test_full_name_splits_correctly(self, db_session):
        """'John Doe' splits into first='John', last='Doe'."""
        with patch(PATCH_PATH) as mock_verify:
            mock_verify.return_value = {
                "email": "john@gmail.com",
                "name": "John Doe",
                "picture": "https://picture.url"
            }
            login_with_google(db_session, "valid.token")
            user = db_session.query(User).filter_by(email="john@gmail.com").first()
            assert user.first_name == "John"
            assert user.last_name == "Doe"

    def test_single_name_has_empty_last_name(self, db_session):
        """Single name results in empty last name."""
        with patch(PATCH_PATH) as mock_verify:
            mock_verify.return_value = {
                "email": "john@gmail.com",
                "name": "John",
                "picture": "https://picture.url"
            }
            login_with_google(db_session, "valid.token")
            user = db_session.query(User).filter_by(email="john@gmail.com").first()
            assert user.first_name == "John"
            assert user.last_name == ""

    def test_missing_name_defaults_to_empty(self, db_session):
        """Missing name field results in empty first and last name."""
        with patch(PATCH_PATH) as mock_verify:
            mock_verify.return_value = {
                "email": "john@gmail.com",
                "picture": "https://picture.url"
            }
            login_with_google(db_session, "valid.token")
            user = db_session.query(User).filter_by(email="john@gmail.com").first()
            assert user.first_name == ""
            assert user.last_name == ""

    def test_three_part_name_splits_correctly(self, db_session):
        """'John Van Doe' splits into first='John', last='Van Doe'."""
        with patch(PATCH_PATH) as mock_verify:
            mock_verify.return_value = {
                "email": "john@gmail.com",
                "name": "John Van Doe",
                "picture": "https://picture.url"
            }
            login_with_google(db_session, "valid.token")
            user = db_session.query(User).filter_by(email="john@gmail.com").first()
            assert user.first_name == "John"
            assert user.last_name == "Van Doe"


# ==============================================================================
# Existing User Tests
# ==============================================================================

class TestExistingUser:

    def test_existing_google_user_not_duplicated(
        self, db_session, existing_google_user, mock_google_user
    ):
        """Logging in twice does not create duplicate users."""
        with patch(PATCH_PATH) as mock_verify:
            mock_verify.return_value = mock_google_user
            login_with_google(db_session, "valid.token")
            count = db_session.query(User).filter_by(email="john@gmail.com").count()
            assert count == 1

    def test_local_user_raises_provider_mismatch(
        self, db_session, existing_local_user, mock_google_user
    ):
        """Local user trying Google login raises AuthProviderMismatchError."""
        with patch(PATCH_PATH) as mock_verify:
            mock_verify.return_value = mock_google_user
            with pytest.raises(AuthProviderMismatchError):
                login_with_google(db_session, "valid.token")

    def test_provider_mismatch_does_not_modify_user(
        self, db_session, existing_local_user, mock_google_user
    ):
        """Provider mismatch leaves existing user unchanged."""
        with patch(PATCH_PATH) as mock_verify:
            mock_verify.return_value = mock_google_user
            try:
                login_with_google(db_session, "valid.token")
            except AuthProviderMismatchError:
                pass
            db_session.refresh(existing_local_user)
            assert existing_local_user.provider == "email"


# ==============================================================================
# Token Generation Tests
# ==============================================================================

class TestTokenGeneration:

    def test_returns_access_and_refresh_tokens(self, db_session, mock_google_user):
        """Response contains both access and refresh tokens."""
        with patch(PATCH_PATH) as mock_verify:
            mock_verify.return_value = mock_google_user
            result = login_with_google(db_session, "valid.token")
            assert "access_token" in result
            assert "refresh_token" in result

    def test_returns_correct_provider(self, db_session, mock_google_user):
        """Response provider is 'google'."""
        with patch(PATCH_PATH) as mock_verify:
            mock_verify.return_value = mock_google_user
            result = login_with_google(db_session, "valid.token")
            assert result["provider"] == "google"

    def test_returns_user_object(self, db_session, mock_google_user):
        """Response contains the correct user object."""
        with patch(PATCH_PATH) as mock_verify:
            mock_verify.return_value = mock_google_user
            result = login_with_google(db_session, "valid.token")
            assert result["user"].email == "john@gmail.com"

    def test_tokens_contain_correct_user_id(self, db_session, mock_google_user):
        """Both tokens encode the correct user ID."""
        with patch(PATCH_PATH) as mock_verify:
            mock_verify.return_value = mock_google_user
            result = login_with_google(db_session, "valid.token")
            user = db_session.query(User).filter_by(email="john@gmail.com").first()
            access_payload = decode_token(result["access_token"])
            refresh_payload = decode_token(result["refresh_token"])
            assert access_payload["sub"] == str(user.id)
            assert refresh_payload["sub"] == str(user.id)

    def test_existing_google_user_gets_valid_tokens(
        self, db_session, existing_google_user, mock_google_user
    ):
        """Existing Google user still gets fresh tokens on login."""
        with patch(PATCH_PATH) as mock_verify:
            mock_verify.return_value = mock_google_user
            result = login_with_google(db_session, "valid.token")
            assert "access_token" in result
            assert "refresh_token" in result                 