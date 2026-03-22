# tests/routes/test_user_route.py
import pytest
from unittest.mock import patch, MagicMock
from core.jwt import create_access_token, create_refresh_token
from models.user_model import User
from core.security import hash_password


# ==============================================================================
# FIXTURES
# ==============================================================================
def auth_header(user_id: str) -> dict:
    """Helper — builds Authorization header with access token."""
    token = create_access_token(str(user_id))
    return {"Authorization": f"Bearer {token}"}
# ==============================================================================
# Happy Path Tests
# ==============================================================================

class TestMeRoute:

    def test_valid_token_returns_200(self, client, registered_user):
        """Valid access token returns 200."""
        response = client.get(
            "/user/me",
            headers=auth_header(registered_user.id)
        )
        assert response.status_code == 200

    def test_returns_correct_user_data(self, client, registered_user):
        """Response contains correct user fields."""
        response = client.get(
            "/user/me",
            headers=auth_header(registered_user.id)
        )
        body = response.json()
        assert body["email"] == "john@example.com"
        assert body["first_name"] == "John"
        assert body["last_name"] == "Doe"

    def test_response_matches_user_response_schema(self, client, registered_user):
        """Response shape matches UserResponse schema."""
        response = client.get(
            "/user/me",
            headers=auth_header(registered_user.id)
        )
        body = response.json()
        assert "id" in body
        assert "email" in body
        assert "first_name" in body
        assert "last_name" in body
        assert "phone" in body
        assert "image_url" in body
        assert "wallet" in body

    def test_response_does_not_expose_password_hash(self, client, registered_user):
        """Response never exposes password_hash field."""
        response = client.get(
            "/user/me",
            headers=auth_header(registered_user.id)
        )
        assert "password_hash" not in response.json()

    def test_response_does_not_expose_provider(self, client, registered_user):
        """Response never exposes provider field."""
        response = client.get(
            "/user/me",
            headers=auth_header(registered_user.id)
        )
        assert "provider" not in response.json()

    # -------------------------------------------------------------------------
    # Auth Failure Tests
    # -------------------------------------------------------------------------

    def test_no_token_returns_401(self, client):
        """Missing Authorization header returns 401."""
        response = client.get("/user/me")
        assert response.status_code == 401

    def test_invalid_token_returns_401(self, client):
        """Invalid token returns 401."""
        response = client.get(
            "/user/me",
            headers={"Authorization": "Bearer invalid.token.here"}
        )
        assert response.status_code == 401

    def test_expired_token_returns_401(self, client):
        """Expired token returns 401."""
        from core.jwt import create_token
        expired = create_token(
            "some-user-id", "access", expires_delta=-1
        )
        response = client.get(
            "/user/me",
            headers={"Authorization": f"Bearer {expired}"}
        )
        assert response.status_code == 401

    def test_refresh_token_returns_401(self, client, registered_user):
        """Refresh token used instead of access token returns 401."""
        refresh_token = create_refresh_token(str(registered_user.id))
        response = client.get(
            "/user/me",
            headers={"Authorization": f"Bearer {refresh_token}"}
        )
        assert response.status_code == 401

    def test_malformed_authorization_header_returns_401(self, client):
        """Malformed Authorization header returns 401."""
        response = client.get(
            "/user/me",
            headers={"Authorization": "NotBearer token"}
        )
        assert response.status_code == 401