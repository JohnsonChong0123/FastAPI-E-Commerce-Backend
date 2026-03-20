# tests/services/google/test_google_auth.py
import pytest
from unittest.mock import patch, MagicMock
from core.config import settings
from services.google.google_auth import verify_google_token


MOCK_GOOGLE_USER_INFO = {
    "sub": "google-user-123",
    "email": "john@gmail.com",
    "given_name": "John",
    "family_name": "Doe",
    "picture": "https://picture.url",
    "email_verified": True
}

class TestVerifyGoogleToken:

    def test_valid_token_returns_user_info(self):
        """Valid token returns user info dict from Google."""
        with patch("services.google.google_auth.id_token.verify_oauth2_token") as mock_verify:
            mock_verify.return_value = MOCK_GOOGLE_USER_INFO
            result = verify_google_token("valid.google.token")
            assert result is not None
            assert result["email"] == "john@gmail.com"
            assert result["sub"] == "google-user-123"

    def test_valid_token_returns_full_user_info(self):
        """Valid token returns all expected fields."""
        with patch("services.google.google_auth.id_token.verify_oauth2_token") as mock_verify:
            mock_verify.return_value = MOCK_GOOGLE_USER_INFO
            result = verify_google_token("valid.google.token")
            assert "sub" in result
            assert "email" in result
            assert "given_name" in result
            assert "family_name" in result
            assert "picture" in result

    def test_invalid_token_returns_none(self):
        """Invalid token raises ValueError — returns None."""
        with patch("services.google.google_auth.id_token.verify_oauth2_token") as mock_verify:
            mock_verify.side_effect = ValueError("Invalid token")
            result = verify_google_token("invalid.token")
            assert result is None

    def test_expired_token_returns_none(self):
        """Expired token raises ValueError — returns None."""
        with patch("services.google.google_auth.id_token.verify_oauth2_token") as mock_verify:
            mock_verify.side_effect = ValueError("Token expired")
            result = verify_google_token("expired.token")
            assert result is None

    def test_wrong_audience_returns_none(self):
        """Token with wrong client ID returns None."""
        with patch("services.google.google_auth.id_token.verify_oauth2_token") as mock_verify:
            mock_verify.side_effect = ValueError("Wrong audience")
            result = verify_google_token("wrong.audience.token")
            assert result is None

    def test_network_error_returns_none(self):
        """Network failure returns None instead of crashing."""
        with patch("services.google.google_auth.id_token.verify_oauth2_token") as mock_verify:
            mock_verify.side_effect = Exception("Network error")
            result = verify_google_token("some.token")
            assert result is None

    def test_verify_called_with_correct_token(self):
        """Token is passed correctly to Google's verify function."""
        with patch("services.google.google_auth.id_token.verify_oauth2_token") as mock_verify:
            mock_verify.return_value = MOCK_GOOGLE_USER_INFO
            verify_google_token("my.specific.token")
            call_args = mock_verify.call_args
            assert call_args[0][0] == "my.specific.token"

    def test_verify_called_with_correct_client_id(self):
        """Google Client ID from settings is passed correctly."""
        with patch("services.google.google_auth.id_token.verify_oauth2_token") as mock_verify:
            mock_verify.return_value = MOCK_GOOGLE_USER_INFO
            verify_google_token("some.token")
            call_args = mock_verify.call_args
            assert call_args[0][2] == settings.GOOGLE_CLIENT_ID

    def test_empty_token_returns_none(self):
        """Empty token string returns None."""
        with patch("services.google.google_auth.id_token.verify_oauth2_token") as mock_verify:
            mock_verify.side_effect = ValueError("Empty token")
            result = verify_google_token("")
            assert result is None