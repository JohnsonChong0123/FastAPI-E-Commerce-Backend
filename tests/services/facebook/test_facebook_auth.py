# tests/services/facebook/test_facebook_auth.py
import pytest
from unittest.mock import patch, MagicMock
from services.facebook.facebook_auth import verify_facebook_token

MOCK_FACEBOOK_USER_INFO = {
    "id": "fb-123",
    "name": "John Doe",
    "email": "john@gmail.com"
}

PATCH_PATH = "services.facebook.facebook_auth.requests.get"


class TestVerifyFacebookToken:

    # -------------------------------------------------------------------------
    # Happy Path
    # -------------------------------------------------------------------------

    def test_valid_token_returns_user_info(self):
        """Valid token returns user info dict from Facebook."""
        with patch(PATCH_PATH) as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = MOCK_FACEBOOK_USER_INFO
            result = verify_facebook_token("valid.facebook.token")
            assert result is not None
            assert result["email"] == "john@gmail.com"
            assert result["id"] == "fb-123"
            assert result["name"] == "John Doe"

    def test_correct_url_is_called(self):
        """Correct Facebook Graph API URL is used."""
        with patch(PATCH_PATH) as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = MOCK_FACEBOOK_USER_INFO
            verify_facebook_token("valid.token")
            call_args = mock_get.call_args
            assert call_args[0][0] == "https://graph.facebook.com/me"

    def test_correct_params_are_sent(self):
        """Token and required fields are sent as query params."""
        with patch(PATCH_PATH) as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = MOCK_FACEBOOK_USER_INFO
            verify_facebook_token("my.specific.token")
            params = mock_get.call_args[1]["params"]
            assert params["access_token"] == "my.specific.token"
            assert "id" in params["fields"]
            assert "name" in params["fields"]
            assert "email" in params["fields"]

    # -------------------------------------------------------------------------
    # Error Path
    # -------------------------------------------------------------------------

    def test_401_response_returns_none(self):
        """Unauthorized response returns None."""
        with patch(PATCH_PATH) as mock_get:
            mock_get.return_value.status_code = 401
            result = verify_facebook_token("invalid.token")
            assert result is None

    def test_400_response_returns_none(self):
        """Bad request response returns None."""
        with patch(PATCH_PATH) as mock_get:
            mock_get.return_value.status_code = 400
            result = verify_facebook_token("bad.token")
            assert result is None

    def test_500_response_returns_none(self):
        """Server error response returns None."""
        with patch(PATCH_PATH) as mock_get:
            mock_get.return_value.status_code = 500
            result = verify_facebook_token("some.token")
            assert result is None

    def test_network_error_returns_none(self):
        """Network failure returns None instead of crashing."""
        with patch(PATCH_PATH) as mock_get:
            mock_get.side_effect = Exception("Network error")
            result = verify_facebook_token("some.token")
            assert result is None

    def test_facebook_error_body_returns_none(self):
        """Facebook error body with status 200 returns None."""
        with patch(PATCH_PATH) as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {
                "error": {
                    "message": "Invalid OAuth access token",
                    "code": 190
                }
            }
            result = verify_facebook_token("expired.token")
            assert result is None

    def test_empty_token_returns_none(self):
        """Empty token string returns None."""
        with patch(PATCH_PATH) as mock_get:
            mock_get.return_value.status_code = 401
            result = verify_facebook_token("")
            assert result is None