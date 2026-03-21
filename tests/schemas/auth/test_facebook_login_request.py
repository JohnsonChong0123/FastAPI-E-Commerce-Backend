# tests/schemas/auth/test_facebook_login_request.py
import pytest
from pydantic import ValidationError
from schemas.auth.facebook_login_request import FacebookLoginRequest


class TestFacebookLoginRequest:

    def test_valid_access_token(self):
        """Valid access_token string passes."""
        data = FacebookLoginRequest(access_token="valid.facebook.token")
        assert data.access_token == "valid.facebook.token"

    def test_missing_access_token_raises_error(self):
        """Omitting access_token raises ValidationError."""
        with pytest.raises(ValidationError):
            FacebookLoginRequest()

    def test_empty_access_token_raises_error(self):
        """Empty string access_token raises ValidationError."""
        with pytest.raises(ValidationError):
            FacebookLoginRequest(access_token="")