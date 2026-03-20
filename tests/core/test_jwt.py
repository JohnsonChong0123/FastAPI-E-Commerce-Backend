# tests/core/test_jwt.py
import pytest
from datetime import datetime, timezone
from jose import jwt
from core.jwt import (
    create_token,
    create_access_token,
    create_refresh_token,
    decode_token,
    TOKEN_SECRET_KEY,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_MINUTES,
)
from exceptions.auth_exceptions import InvalidTokenError, TokenExpiredError


# ==============================================================================
# create_token Tests
# ==============================================================================

class TestCreateToken:

    def test_returns_non_empty_string(self):
        token = create_token("user-123", "access", ACCESS_TOKEN_EXPIRE_MINUTES)
        assert isinstance(token, str)
        assert len(token) > 0

    def test_payload_contains_correct_sub(self):
        token = create_token("user-123", "access", ACCESS_TOKEN_EXPIRE_MINUTES)
        payload = jwt.decode(token, TOKEN_SECRET_KEY, algorithms=["HS256"])
        assert payload["sub"] == "user-123"

    def test_payload_contains_correct_type(self):
        token = create_token("user-123", "access", ACCESS_TOKEN_EXPIRE_MINUTES)
        payload = jwt.decode(token, TOKEN_SECRET_KEY, algorithms=["HS256"])
        assert payload["type"] == "access"

    def test_payload_contains_expiry(self):
        token = create_token("user-123", "access", ACCESS_TOKEN_EXPIRE_MINUTES)
        payload = jwt.decode(token, TOKEN_SECRET_KEY, algorithms=["HS256"])
        assert "exp" in payload

    def test_expiry_is_in_future(self):
        token = create_token("user-123", "access", ACCESS_TOKEN_EXPIRE_MINUTES)
        payload = jwt.decode(token, TOKEN_SECRET_KEY, algorithms=["HS256"])
        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        assert exp > datetime.now(timezone.utc)

    def test_different_users_produce_different_tokens(self):
        token1 = create_token("user-111", "access", ACCESS_TOKEN_EXPIRE_MINUTES)
        token2 = create_token("user-222", "access", ACCESS_TOKEN_EXPIRE_MINUTES)
        assert token1 != token2


# ==============================================================================
# create_access_token Tests
# ==============================================================================

class TestCreateAccessToken:

    def test_has_correct_type(self):
        token = create_access_token("user-123")
        payload = jwt.decode(token, TOKEN_SECRET_KEY, algorithms=["HS256"])
        assert payload["type"] == "access"

    def test_has_correct_sub(self):
        token = create_access_token("user-123")
        payload = jwt.decode(token, TOKEN_SECRET_KEY, algorithms=["HS256"])
        assert payload["sub"] == "user-123"

    def test_expires_in_60_minutes(self):
        before = datetime.now(timezone.utc)
        token = create_access_token("user-123")
        payload = jwt.decode(token, TOKEN_SECRET_KEY, algorithms=["HS256"])
        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        diff = exp - before
        assert 59 <= diff.seconds // 60 <= 61


# ==============================================================================
# create_refresh_token Tests
# ==============================================================================

class TestCreateRefreshToken:

    def test_has_correct_type(self):
        token = create_refresh_token("user-123")
        payload = jwt.decode(token, TOKEN_SECRET_KEY, algorithms=["HS256"])
        assert payload["type"] == "refresh"

    def test_has_correct_sub(self):
        token = create_refresh_token("user-123")
        payload = jwt.decode(token, TOKEN_SECRET_KEY, algorithms=["HS256"])
        assert payload["sub"] == "user-123"

    def test_expires_in_7_days(self):
        before = datetime.now(timezone.utc)
        token = create_refresh_token("user-123")
        payload = jwt.decode(token, TOKEN_SECRET_KEY, algorithms=["HS256"])
        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        diff = exp - before
        assert 6 <= diff.days <= 7

    def test_refresh_token_lives_longer_than_access_token(self):
        access = create_access_token("user-123")
        refresh = create_refresh_token("user-123")
        access_payload = jwt.decode(access, TOKEN_SECRET_KEY, algorithms=["HS256"])
        refresh_payload = jwt.decode(refresh, TOKEN_SECRET_KEY, algorithms=["HS256"])
        assert refresh_payload["exp"] > access_payload["exp"]


# ==============================================================================
# decode_token Tests
# ==============================================================================

class TestDecodeToken:

    def test_valid_token_returns_correct_payload(self):
        token = create_access_token("user-123")
        payload = decode_token(token)
        assert payload["sub"] == "user-123"
        assert payload["type"] == "access"

    def test_expired_token_raises_token_expired_error(self):
        token = create_token("user-123", "access", expires_delta=-1)
        with pytest.raises(TokenExpiredError):
            decode_token(token)

    def test_invalid_token_raises_invalid_token_error(self):
        with pytest.raises(InvalidTokenError):
            decode_token("this.is.invalid")

    def test_wrong_secret_raises_invalid_token_error(self):
        fake_token = jwt.encode(
            {"sub": "user-123", "type": "access"},
            "wrong-secret",
            algorithm="HS256"
        )
        with pytest.raises(InvalidTokenError):
            decode_token(fake_token)

    def test_tampered_token_raises_invalid_token_error(self):
        token = create_access_token("user-123")
        tampered = token[:-5] + "XXXXX"
        with pytest.raises(InvalidTokenError):
            decode_token(tampered)

    def test_decode_refresh_token_returns_correct_payload(self):
        token = create_refresh_token("user-123")
        payload = decode_token(token)
        assert payload["sub"] == "user-123"
        assert payload["type"] == "refresh"

    def test_empty_token_raises_invalid_token_error(self):
        with pytest.raises(InvalidTokenError):
            decode_token("")