# tests/schemas/auth/test_refresh_token_request.py
import pytest
from pydantic import ValidationError
from schemas.auth.refresh_token_request import RefreshTokenRequest


class TestRefreshTokenRequest:

    # -------------------------------------------------------------------------
    # Valid Data Tests
    # -------------------------------------------------------------------------

    def test_valid_refresh_token(self):
        """Valid refresh_token string passes."""
        data = RefreshTokenRequest(refresh_token="valid.refresh.token")
        assert data.refresh_token == "valid.refresh.token"

    def test_any_non_empty_string_is_valid(self):
        """Any non-empty string is accepted as refresh_token."""
        data = RefreshTokenRequest(refresh_token="abc123")
        assert data.refresh_token == "abc123"

    # -------------------------------------------------------------------------
    # Validation Tests
    # -------------------------------------------------------------------------

    def test_missing_refresh_token_raises_error(self):
        """Missing refresh_token raises ValidationError."""
        with pytest.raises(ValidationError):
            RefreshTokenRequest()

    def test_empty_refresh_token_raises_error(self):
        """
        Empty string refresh_token — currently passes.
        Documents the gap — add Field(..., min_length=1).
        """
        with pytest.raises(ValidationError):
            RefreshTokenRequest(refresh_token="")   

    def test_whitespace_refresh_token_raises_error(self):
        """
        Whitespace-only refresh_token — currently passes.
        Documents the gap — add strip() validator.
        """
        with pytest.raises(ValidationError):
            RefreshTokenRequest(refresh_token="   ") 