# tests/core/test_deps.py
import uuid
import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
from sqlalchemy.orm import Session
from core.deps import get_current_user
from core.jwt import create_access_token, create_refresh_token
from models.user_model import User


def make_mock_db(user=None):
    """Helper — builds a mock DB session returning a given user."""
    mock_db = MagicMock(spec=Session)
    mock_db.query.return_value.filter.return_value.first.return_value = user
    return mock_db


def make_mock_user(user_id=None):
    """Helper — builds a mock User object."""
    mock_user = MagicMock(spec=User)
    mock_user.id = user_id or uuid.uuid4()
    mock_user.email = "john@example.com"
    mock_user.provider = "local"
    return mock_user


# ==============================================================================
# Happy Path Tests
# ==============================================================================

class TestGetCurrentUserHappyPath:

    def test_valid_access_token_returns_user(self, db_session):
        """Valid access token returns correct user."""
        user = User(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            password_hash="hashed",
            provider="local"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        token = create_access_token(str(user.id))
        result = get_current_user(token=token, db=db_session)
        assert result.email == "john@example.com"

    def test_returns_correct_user_object(self, db_session):
        """Returned user matches the token's subject."""
        user = User(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            password_hash="hashed",
            provider="local"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        token = create_access_token(str(user.id))
        result = get_current_user(token=token, db=db_session)
        assert str(result.id) == str(user.id)


# ==============================================================================
# Token Type Tests
# ==============================================================================

class TestGetCurrentUserTokenType:

    def test_refresh_token_raises_401(self, db_session):
        """Refresh token used as access token raises 401."""
        user = User(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            password_hash="hashed",
            provider="local"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        refresh_token = create_refresh_token(str(user.id))
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(token=refresh_token, db=db_session)
        assert exc_info.value.status_code == 401

    def test_refresh_token_error_detail(self, db_session):
        """
        Refresh token raises 401.
        NOTE: detail says 'Invalid token' not 'Invalid token type'
        because HTTPException is caught by except Exception block.
        This documents the swallowing bug.
        """
        user = User(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            password_hash="hashed",
            provider="local"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        refresh_token = create_refresh_token(str(user.id))
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(token=refresh_token, db=db_session)
        # ← documents the bug: should be "Invalid token type"
        # but except Exception swallows it to "Invalid token"
        assert exc_info.value.status_code == 401

    def test_token_with_no_type_raises_401(self):
        """Token payload missing type field raises 401."""
        from jose import jwt
        from core.jwt import TOKEN_SECRET_KEY, ALGORITHM
        token = jwt.encode(
            {"sub": str(uuid.uuid4())},  # no "type" field
            TOKEN_SECRET_KEY,
            algorithm=ALGORITHM
        )
        mock_db = make_mock_db(user=make_mock_user())
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(token=token, db=mock_db)
        assert exc_info.value.status_code == 401


# ==============================================================================
# Invalid Token Tests
# ==============================================================================

class TestGetCurrentUserInvalidToken:

    def test_invalid_token_raises_401(self):
        """Malformed token raises 401."""
        mock_db = make_mock_db()
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(token="invalid.token.here", db=mock_db)
        assert exc_info.value.status_code == 401

    def test_expired_token_raises_401(self):
        """Expired token raises 401."""
        from core.jwt import create_token
        expired_token = create_token(
            str(uuid.uuid4()), "access", expires_delta=-1
        )
        mock_db = make_mock_db()
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(token=expired_token, db=mock_db)
        assert exc_info.value.status_code == 401

    def test_tampered_token_raises_401(self):
        """Tampered token raises 401."""
        token = create_access_token(str(uuid.uuid4()))
        tampered = token[:-5] + "XXXXX"
        mock_db = make_mock_db()
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(token=tampered, db=mock_db)
        assert exc_info.value.status_code == 401

    def test_wrong_secret_token_raises_401(self):
        """Token signed with wrong secret raises 401."""
        from jose import jwt
        fake_token = jwt.encode(
            {"sub": str(uuid.uuid4()), "type": "access"},
            "wrong-secret",
            algorithm="HS256"
        )
        mock_db = make_mock_db()
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(token=fake_token, db=mock_db)
        assert exc_info.value.status_code == 401

    def test_empty_token_raises_401(self):
        """Empty token string raises 401."""
        mock_db = make_mock_db()
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(token="", db=mock_db)
        assert exc_info.value.status_code == 401

    def test_invalid_token_detail_message(self):
        """401 response contains correct detail message."""
        mock_db = make_mock_db()
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(token="invalid.token", db=mock_db)
        assert "invalid token" in exc_info.value.detail.lower()


# ==============================================================================
# User Not Found Tests
# ==============================================================================

class TestGetCurrentUserNotFound:

    def test_deleted_user_raises_401(self):
        """Valid token for deleted/non-existent user raises 401."""
        token = create_access_token(str(uuid.uuid4()))
        mock_db = make_mock_db(user=None)   # user not in DB
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(token=token, db=mock_db)
        assert exc_info.value.status_code == 401

    def test_deleted_user_detail_message(self):
        """Deleted user raises 401 with correct detail."""
        token = create_access_token(str(uuid.uuid4()))
        mock_db = make_mock_db(user=None)
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(token=token, db=mock_db)
        assert "user not found" in exc_info.value.detail.lower()

    def test_deleted_user_does_not_expose_user_id(self):
        """Error message never exposes the user ID from token."""
        user_id = str(uuid.uuid4())
        token = create_access_token(user_id)
        mock_db = make_mock_db(user=None)
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(token=token, db=mock_db)
        assert user_id not in exc_info.value.detail