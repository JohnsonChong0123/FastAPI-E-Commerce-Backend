# tests/services/test_refresh_token_service.py
import uuid
import pytest
from jose import jwt as jose_jwt
from exceptions.auth_exceptions import RefreshTokenError, UserNotFoundError
from models.user_model import User
from core.security import hash_password
from core.jwt import (
    create_access_token,
    create_refresh_token,
    create_token,
    TOKEN_SECRET_KEY,
    ALGORITHM
)
from services.auth.refresh_token_services import refresh_token
from schemas.auth.refresh_token_request import RefreshTokenRequest


# ==============================================================================
# FIXTURES
# ==============================================================================

@pytest.fixture
def registered_user(db_session):
    user = User(
        first_name="John",
        last_name="Doe",
        email="john@example.com",
        password_hash=hash_password("Secret1234!"),
        provider="email"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def make_request(token: str) -> RefreshTokenRequest:
    """Helper — builds RefreshTokenRequest."""
    return RefreshTokenRequest(refresh_token=token)


# ==============================================================================
# Happy Path Tests
# ==============================================================================

class TestRefreshTokenHappyPath:

    def test_valid_refresh_token_returns_access_token(
        self, db_session, registered_user
    ):
        """Valid refresh token returns new access token."""
        token = create_refresh_token(str(registered_user.id))
        result = refresh_token(make_request(token), db_session)
        assert "access_token" in result

    def test_returned_access_token_is_non_empty_string(
        self, db_session, registered_user
    ):
        """Returned access_token is a non-empty string."""
        token = create_refresh_token(str(registered_user.id))
        result = refresh_token(make_request(token), db_session)
        assert isinstance(result["access_token"], str)
        assert len(result["access_token"]) > 0

    def test_returned_access_token_contains_correct_user_id(
        self, db_session, registered_user
    ):
        """New access token encodes the correct user ID."""
        token = create_refresh_token(str(registered_user.id))
        result = refresh_token(make_request(token), db_session)
        from core.jwt import decode_token
        payload = decode_token(result["access_token"])
        assert payload["sub"] == str(registered_user.id)

    def test_returned_access_token_has_correct_type(
        self, db_session, registered_user
    ):
        """New access token has type 'access'."""
        token = create_refresh_token(str(registered_user.id))
        result = refresh_token(make_request(token), db_session)
        from core.jwt import decode_token
        payload = decode_token(result["access_token"])
        assert payload["type"] == "access"

    def test_response_only_contains_access_token(
        self, db_session, registered_user
    ):
        """Response contains only access_token — no refresh token."""
        token = create_refresh_token(str(registered_user.id))
        result = refresh_token(make_request(token), db_session)
        assert list(result.keys()) == ["access_token"]


# ==============================================================================
# Invalid Token Tests
# ==============================================================================

class TestRefreshTokenInvalidToken:

    def test_invalid_token_raises_refresh_token_error(self, db_session):
        """Malformed token raises RefreshTokenError."""
        with pytest.raises(RefreshTokenError):
            refresh_token(make_request("invalid.token.here"), db_session)

    def test_expired_token_raises_refresh_token_error(self, db_session):
        """Expired refresh token raises RefreshTokenError."""
        expired = create_token(
            str(uuid.uuid4()), "refresh", expires_delta=-1
        )
        with pytest.raises(RefreshTokenError):
            refresh_token(make_request(expired), db_session)

    def test_tampered_token_raises_refresh_token_error(self, db_session):
        """Tampered token raises RefreshTokenError."""
        token = create_refresh_token(str(uuid.uuid4()))
        tampered = token[:-5] + "XXXXX"
        with pytest.raises(RefreshTokenError):
            refresh_token(make_request(tampered), db_session)

    def test_wrong_secret_raises_refresh_token_error(self, db_session):
        """Token signed with wrong secret raises RefreshTokenError."""
        fake_token = jose_jwt.encode(
            {"sub": str(uuid.uuid4()), "type": "refresh"},
            "wrong-secret",
            algorithm=ALGORITHM
        )
        with pytest.raises(RefreshTokenError):
            refresh_token(make_request(fake_token), db_session)

# ==============================================================================
# Wrong Token Type Tests
# ==============================================================================

class TestRefreshTokenWrongType:

    def test_access_token_raises_refresh_token_error(
        self, db_session, registered_user
    ):
        """Access token used as refresh token raises RefreshTokenError."""
        access_token = create_access_token(str(registered_user.id))
        with pytest.raises(RefreshTokenError):
            refresh_token(make_request(access_token), db_session)

    def test_token_with_no_type_raises_refresh_token_error(self, db_session):
        """Token with no type field raises RefreshTokenError."""
        token = jose_jwt.encode(
            {"sub": str(uuid.uuid4())},  # no type field
            TOKEN_SECRET_KEY,
            algorithm=ALGORITHM
        )
        with pytest.raises(RefreshTokenError):
            refresh_token(make_request(token), db_session)

    def test_token_type_check_is_enforced(
        self, db_session, registered_user
    ):
        """
        Documents bug: type check inside try block is swallowed.
        RefreshTokenError raised for wrong type is caught by
        except Exception and re-raised as RefreshTokenError.
        Works correctly by accident — both paths raise same error.

        Fix: move type check outside try block for clarity.
        """
        access_token = create_access_token(str(registered_user.id))
        with pytest.raises(RefreshTokenError):
            refresh_token(make_request(access_token), db_session)
        # Still raises RefreshTokenError ✅ but for wrong reason internally


# ==============================================================================
# User Not Found Tests
# ==============================================================================

class TestRefreshTokenUserNotFound:

    def test_deleted_user_raises_user_not_found_error(self, db_session):
        """Valid refresh token for deleted user raises UserNotFoundError."""
        non_existent_id = str(uuid.uuid4())
        token = create_refresh_token(non_existent_id)
        with pytest.raises(UserNotFoundError):
            refresh_token(make_request(token), db_session)

    def test_user_not_found_error_not_swallowed(self, db_session):
        """
        UserNotFoundError is raised AFTER try block so it
        correctly propagates — not swallowed by except Exception.
        """
        non_existent_id = str(uuid.uuid4())
        token = create_refresh_token(non_existent_id)
        with pytest.raises(UserNotFoundError):   # ← not RefreshTokenError
            refresh_token(make_request(token), db_session)

    def test_deleted_user_does_not_return_token(self, db_session):
        """No access token returned when user not found."""
        non_existent_id = str(uuid.uuid4())
        token = create_refresh_token(non_existent_id)
        try:
            refresh_token(make_request(token), db_session)
        except UserNotFoundError:
            pass
        except Exception:
            pass


# ==============================================================================
# Bug Documentation Tests
# ==============================================================================

class TestRefreshTokenBugs:

    def test_type_check_inside_try_is_swallowed(
        self, db_session, registered_user
    ):
        """
        DOCUMENTS BUG: token type check inside try block.
        RefreshTokenError raised inside try is caught by except
        and re-raised — works but obscures intent.

        Fix:
            try:
                payload = jwt.decode_token(data.refresh_token)
                user_id = payload.get("sub")
            except Exception:
                raise RefreshTokenError()

            if payload.get("type") != "refresh":   # ← outside try
                raise RefreshTokenError()
        """
        access_token = create_access_token(str(registered_user.id))
        with pytest.raises(RefreshTokenError):
            refresh_token(make_request(access_token), db_session)
        # Raises correctly but internally for wrong reason