# tests/auth/test_facebook_login_service.py
import pytest
from unittest.mock import patch
from exceptions.auth_exceptions import (
    InvalidFacebookTokenError,
    AuthProviderMismatchError
)
from models.user_model import User
from core.security import hash_password
from core.jwt import decode_token
from services.auth.facebook_login_services import login_with_facebook


# ==============================================================================
# FIXTURES
# ==============================================================================

@pytest.fixture
def mock_facebook_user():
    """Standard mock Facebook user with email."""
    return {
        "id": "fb-123",
        "name": "John Doe",
        "email": "john@gmail.com"
    }

@pytest.fixture
def mock_facebook_user_no_email():
    """Facebook user without email (privacy settings)."""
    return {
        "id": "fb-456",
        "name": "John Doe"
        # no email field
    }

@pytest.fixture
def existing_facebook_user(db_session):
    """User already registered via Facebook."""
    user = User(
        first_name="John",
        last_name="Doe",
        email="john@gmail.com",
        password_hash=None,
        provider="facebook"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def existing_local_user(db_session):
    """User already registered via local email/password."""
    user = User(
        first_name="John",
        last_name="Doe",
        email="john@gmail.com",
        password_hash=hash_password("Secret1234!"),
        provider="local"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def existing_google_user(db_session):
    """User already registered via Google."""
    user = User(
        first_name="John",
        last_name="Doe",
        email="john@gmail.com",
        password_hash=None,
        provider="google"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


PATCH_PATH = "services.auth.facebook_login_services.verify_facebook_token"


# ==============================================================================
# Invalid Token Tests
# ==============================================================================

class TestInvalidToken:

    def test_invalid_token_raises_error(self, db_session):
        """None return from verify raises InvalidFacebookTokenError."""
        with patch(PATCH_PATH) as mock_verify:
            mock_verify.return_value = None
            with pytest.raises(InvalidFacebookTokenError):
                login_with_facebook(db_session, "invalid.token")

    def test_invalid_token_does_not_create_user(self, db_session):
        """No user is created when token is invalid."""
        with patch(PATCH_PATH) as mock_verify:
            mock_verify.return_value = None
            try:
                login_with_facebook(db_session, "invalid.token")
            except InvalidFacebookTokenError:
                pass
            assert db_session.query(User).count() == 0


# ==============================================================================
# New User Creation Tests
# ==============================================================================

class TestNewUserCreation:

    def test_new_user_created_with_email(self, db_session, mock_facebook_user):
        """New user is saved to DB on first Facebook login."""
        with patch(PATCH_PATH) as mock_verify:
            mock_verify.return_value = mock_facebook_user
            login_with_facebook(db_session, "valid.token")
            user = db_session.query(User).filter_by(
                email="john@gmail.com"
            ).first()
            assert user is not None

    def test_new_user_has_correct_fields(self, db_session, mock_facebook_user):
        """New user fields are populated from Facebook user info."""
        with patch(PATCH_PATH) as mock_verify:
            mock_verify.return_value = mock_facebook_user
            login_with_facebook(db_session, "valid.token")
            user = db_session.query(User).filter_by(
                email="john@gmail.com"
            ).first()
            assert user.first_name == "John"
            assert user.last_name == "Doe"
            assert user.email == "john@gmail.com"
            assert user.provider == "facebook"

    def test_new_facebook_user_has_no_password_hash(
        self, db_session, mock_facebook_user
    ):
        """Facebook users are created without a password hash."""
        with patch(PATCH_PATH) as mock_verify:
            mock_verify.return_value = mock_facebook_user
            login_with_facebook(db_session, "valid.token")
            user = db_session.query(User).filter_by(
                email="john@gmail.com"
            ).first()
            assert user.password_hash is None

    def test_new_user_without_email_raises_or_handles_gracefully(
        self, db_session, mock_facebook_user_no_email
    ):
        """
        Facebook user without email — currently creates user with
        email=None which may violate DB constraints.
        This test documents the current behaviour and flags the bug.
        """
        with patch(PATCH_PATH) as mock_verify:
            mock_verify.return_value = mock_facebook_user_no_email
            # Should raise an error — email=None violates NOT NULL constraint
            with pytest.raises(Exception):
                login_with_facebook(db_session, "valid.token")


# ==============================================================================
# Name Parsing Tests
# ==============================================================================

class TestNameParsing:

    def test_full_name_splits_correctly(self, db_session):
        """'John Doe' → first='John', last='Doe'."""
        with patch(PATCH_PATH) as mock_verify:
            mock_verify.return_value = {
                "id": "fb-123",
                "email": "john@gmail.com",
                "name": "John Doe"
            }
            login_with_facebook(db_session, "valid.token")
            user = db_session.query(User).filter_by(
                email="john@gmail.com"
            ).first()
            assert user.first_name == "John"
            assert user.last_name == "Doe"

    def test_single_name_has_empty_last_name(self, db_session):
        """'John' → first='John', last=''."""
        with patch(PATCH_PATH) as mock_verify:
            mock_verify.return_value = {
                "id": "fb-123",
                "email": "john@gmail.com",
                "name": "John"
            }
            login_with_facebook(db_session, "valid.token")
            user = db_session.query(User).filter_by(
                email="john@gmail.com"
            ).first()
            assert user.first_name == "John"
            assert user.last_name == ""

    def test_three_part_name_splits_correctly(self, db_session):
        """'John Van Doe' → first='John', last='Van Doe'."""
        with patch(PATCH_PATH) as mock_verify:
            mock_verify.return_value = {
                "id": "fb-123",
                "email": "john@gmail.com",
                "name": "John Van Doe"
            }
            login_with_facebook(db_session, "valid.token")
            user = db_session.query(User).filter_by(
                email="john@gmail.com"
            ).first()
            assert user.first_name == "John"
            assert user.last_name == "Van Doe"

    def test_missing_name_defaults_to_empty(self, db_session):
        """Missing name field → first='', last=''."""
        with patch(PATCH_PATH) as mock_verify:
            mock_verify.return_value = {
                "id": "fb-123",
                "email": "john@gmail.com"
                # no name field
            }
            login_with_facebook(db_session, "valid.token")
            user = db_session.query(User).filter_by(
                email="john@gmail.com"
            ).first()
            assert user.first_name == ""
            assert user.last_name == ""


# ==============================================================================
# Existing User Tests
# ==============================================================================

class TestExistingUser:

    def test_existing_facebook_user_not_duplicated(
        self, db_session, existing_facebook_user, mock_facebook_user
    ):
        """Logging in twice does not create duplicate users."""
        with patch(PATCH_PATH) as mock_verify:
            mock_verify.return_value = mock_facebook_user
            login_with_facebook(db_session, "valid.token")
            count = db_session.query(User).filter_by(
                email="john@gmail.com"
            ).count()
            assert count == 1

    def test_local_user_raises_provider_mismatch(
        self, db_session, existing_local_user, mock_facebook_user
    ):
        """Local user trying Facebook login raises AuthProviderMismatchError."""
        with patch(PATCH_PATH) as mock_verify:
            mock_verify.return_value = mock_facebook_user
            with pytest.raises(AuthProviderMismatchError):
                login_with_facebook(db_session, "valid.token")

    def test_google_user_raises_provider_mismatch(
        self, db_session, existing_google_user, mock_facebook_user
    ):
        """Google user trying Facebook login raises AuthProviderMismatchError."""
        with patch(PATCH_PATH) as mock_verify:
            mock_verify.return_value = mock_facebook_user
            with pytest.raises(AuthProviderMismatchError):
                login_with_facebook(db_session, "valid.token")

    def test_provider_mismatch_does_not_modify_user(
        self, db_session, existing_local_user, mock_facebook_user
    ):
        """Provider mismatch leaves existing user completely unchanged."""
        with patch(PATCH_PATH) as mock_verify:
            mock_verify.return_value = mock_facebook_user
            try:
                login_with_facebook(db_session, "valid.token")
            except AuthProviderMismatchError:
                pass
            db_session.refresh(existing_local_user)
            assert existing_local_user.provider == "local"
            assert existing_local_user.password_hash is not None


# ==============================================================================
# Token Generation Tests
# ==============================================================================

class TestTokenGeneration:

    def test_returns_access_and_refresh_tokens(
        self, db_session, mock_facebook_user
    ):
        """Response contains both access and refresh tokens."""
        with patch(PATCH_PATH) as mock_verify:
            mock_verify.return_value = mock_facebook_user
            result = login_with_facebook(db_session, "valid.token")
            assert "access_token" in result
            assert "refresh_token" in result

    def test_returns_correct_provider(self, db_session, mock_facebook_user):
        """Response provider is 'facebook'."""
        with patch(PATCH_PATH) as mock_verify:
            mock_verify.return_value = mock_facebook_user
            result = login_with_facebook(db_session, "valid.token")
            assert result["provider"] == "facebook"

    def test_returns_user_object(self, db_session, mock_facebook_user):
        """Response contains the correct user object."""
        with patch(PATCH_PATH) as mock_verify:
            mock_verify.return_value = mock_facebook_user
            result = login_with_facebook(db_session, "valid.token")
            assert result["user"].email == "john@gmail.com"

    def test_tokens_contain_correct_user_id(
        self, db_session, mock_facebook_user
    ):
        """Both tokens encode the correct user ID."""
        with patch(PATCH_PATH) as mock_verify:
            mock_verify.return_value = mock_facebook_user
            result = login_with_facebook(db_session, "valid.token")
            user = db_session.query(User).filter_by(
                email="john@gmail.com"
            ).first()
            access_payload = decode_token(result["access_token"])
            refresh_payload = decode_token(result["refresh_token"])
            assert access_payload["sub"] == str(user.id)
            assert refresh_payload["sub"] == str(user.id)

    def test_existing_facebook_user_gets_fresh_tokens(
        self, db_session, existing_facebook_user, mock_facebook_user
    ):
        """Existing Facebook user gets fresh tokens on every login."""
        with patch(PATCH_PATH) as mock_verify:
            mock_verify.return_value = mock_facebook_user
            result = login_with_facebook(db_session, "valid.token")
            assert "access_token" in result
            assert "refresh_token" in result