# tests/schemas/auth/test_google_login_request.py
import pytest
from pydantic import ValidationError
from schemas.auth.google_login_request import GoogleLoginRequest


class TestGoogleLoginRequest:

    def test_valid_id_token(self):
        """Valid id_token string passes."""
        data = GoogleLoginRequest(id_token="valid.google.jwt.token")
        assert data.id_token == "valid.google.jwt.token"

    def test_missing_id_token_raises_error(self):
        """Omitting id_token raises ValidationError."""
        with pytest.raises(ValidationError):
            GoogleLoginRequest()

    def test_empty_id_token_raises_error(self):
        """Empty string id_token should raise ValidationError."""
        with pytest.raises(ValidationError):
            GoogleLoginRequest(id_token="")