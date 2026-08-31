# tests/routes/test_user_route.py
import pytest
from unittest.mock import patch, MagicMock
from core.jwt import create_access_token, create_refresh_token
from models.user_model import User
from core.security import hash_password
from main import app
from database import get_db


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


# ==============================================================================
# Update Address Route Tests
# ==============================================================================

ADDRESS_PAYLOAD = {
    "user_address": "123 Main St, City, Country",
    "user_latitude": 40.7128,
    "user_longitude": -74.0060,
}


class TestUpdateMyAddressRoute:

    def test_valid_payload_returns_200(self, client, registered_user):
        """Valid address payload returns 200."""
        response = client.put(
            "/user/me/address",
            json=ADDRESS_PAYLOAD,
            headers=auth_header(registered_user.id)
        )
        assert response.status_code == 200

    def test_returns_success_message(self, client, registered_user):
        """Response contains the success message."""
        response = client.put(
            "/user/me/address",
            json=ADDRESS_PAYLOAD,
            headers=auth_header(registered_user.id)
        )
        body = response.json()
        assert body["message"] == "Address updated successfully"

    def test_persists_address_to_db(self, client, registered_user, db_session):
        """Updated address/lat/long are persisted to the database."""
        client.put(
            "/user/me/address",
            json=ADDRESS_PAYLOAD,
            headers=auth_header(registered_user.id)
        )

        db_session.expire_all()
        refreshed = db_session.get(User, registered_user.id)
        assert refreshed.address == ADDRESS_PAYLOAD["user_address"]
        assert refreshed.latitude == ADDRESS_PAYLOAD["user_latitude"]
        assert refreshed.longitude == ADDRESS_PAYLOAD["user_longitude"]

    def test_commit_called_once_on_success(self, client, registered_user):
        """DB commit is called once when the update succeeds."""
        mock_db = MagicMock()

        def override_get_db():
            yield mock_db

        app.dependency_overrides[get_db] = override_get_db
        try:
            client.put(
                "/user/me/address",
                json=ADDRESS_PAYLOAD,
                headers=auth_header(registered_user.id)
            )
            mock_db.commit.assert_called_once()
        finally:
            app.dependency_overrides.clear()

    def test_invalid_body_returns_422(self, client, registered_user):
        """Missing required fields returns 422."""
        response = client.put(
            "/user/me/address",
            json={"user_address": "123 Main St"},
            headers=auth_header(registered_user.id)
        )
        assert response.status_code == 422

    # -------------------------------------------------------------------------
    # Auth Failure Tests
    # -------------------------------------------------------------------------

    def test_no_token_returns_401(self, client):
        """Missing Authorization header returns 401."""
        response = client.put(
            "/user/me/address",
            json=ADDRESS_PAYLOAD
        )
        assert response.status_code == 401

    def test_invalid_token_returns_401(self, client):
        """Invalid token returns 401."""
        response = client.put(
            "/user/me/address",
            json=ADDRESS_PAYLOAD,
            headers={"Authorization": "Bearer invalid.token.here"}
        )
        assert response.status_code == 401

    def test_refresh_token_returns_401(self, client, registered_user):
        """Refresh token used instead of access token returns 401."""
        refresh_token = create_refresh_token(str(registered_user.id))
        response = client.put(
            "/user/me/address",
            json=ADDRESS_PAYLOAD,
            headers={"Authorization": f"Bearer {refresh_token}"}
        )
        assert response.status_code == 401


# ==============================================================================
# Get Location Route Tests
# ==============================================================================

class TestGetMyLocationRoute:

    def test_returns_200(self, client, registered_user):
        """Valid access token returns 200."""
        response = client.get(
            "/user/me/location",
            headers=auth_header(registered_user.id)
        )
        assert response.status_code == 200

    def test_returns_expected_fields(self, client, registered_user):
        """Response contains latitude, longitude and address fields."""
        response = client.get(
            "/user/me/location",
            headers=auth_header(registered_user.id)
        )
        body = response.json()
        assert "latitude" in body
        assert "longitude" in body
        assert "address" in body

    def test_missing_location_defaults_to_zero_and_unset(
        self, client, registered_user
    ):
        """When lat/long are unset, defaults to 0.0/0.0 and 'Location not set'."""
        response = client.get(
            "/user/me/location",
            headers=auth_header(registered_user.id)
        )
        body = response.json()
        assert body["latitude"] == 0.0
        assert body["longitude"] == 0.0
        assert body["address"] == "Location not set"

    def test_returns_stored_location(self, client, db_session):
        """Returns the user's persisted lat/long/address when set."""
        user = User(
            first_name="Jane",
            last_name="Doe",
            email="jane-loc@example.com",
            password_hash=hash_password("Secret1234!"),
            provider="email",
            address="456 Market St, City, Country",
            latitude=37.7749,
            longitude=-122.4194,
        )
        db_session.add(user)
        db_session.commit()

        response = client.get(
            "/user/me/location",
            headers=auth_header(user.id)
        )
        body = response.json()
        assert body["latitude"] == 37.7749
        assert body["longitude"] == -122.4194
        assert body["address"] == "456 Market St, City, Country"

    # -------------------------------------------------------------------------
    # Auth Failure Tests
    # -------------------------------------------------------------------------

    def test_no_token_returns_401(self, client):
        """Missing Authorization header returns 401."""
        response = client.get("/user/me/location")
        assert response.status_code == 401

    def test_invalid_token_returns_401(self, client):
        """Invalid token returns 401."""
        response = client.get(
            "/user/me/location",
            headers={"Authorization": "Bearer invalid.token.here"}
        )
        assert response.status_code == 401

    def test_refresh_token_returns_401(self, client, registered_user):
        """Refresh token used instead of access token returns 401."""
        refresh_token = create_refresh_token(str(registered_user.id))
        response = client.get(
            "/user/me/location",
            headers={"Authorization": f"Bearer {refresh_token}"}
        )
        assert response.status_code == 401