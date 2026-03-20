# tests/routes/test_auth_route.py

from unittest.mock import patch

from tests.services.auth.test_google_services import PATCH_PATH
from tests.services.google.test_google_auth import MOCK_GOOGLE_USER_INFO

class TestRegisterRoute:

    VALID_PAYLOAD = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john@example.com",
        "password": "Secret1234!"
    }
    
    def test_register_returns_success_message(self, client):
        """Test that a successful registration returns the expected success message."""
        response = client.post("/auth/register", json=self.VALID_PAYLOAD)
        assert response.status_code == 200
        assert response.json() == {"message": "User registered successfully"}

    def test_register_duplicate_email_returns_409(self, client):
        """Test that registering with an email that already exists returns a 409 status code."""
        client.post("/auth/register", json=self.VALID_PAYLOAD)
        response = client.post("/auth/register", json=self.VALID_PAYLOAD)
        assert response.status_code == 409

    def test_register_missing_email_returns_422(self, client):
        """Test that missing the email field in the registration payload returns a 422 status code."""
        payload = {**self.VALID_PAYLOAD}
        del payload["email"]
        response = client.post("/auth/register", json=payload)
        assert response.status_code == 422

    def test_register_invalid_email_returns_422(self, client):
        """Test that providing an invalid email in the registration payload returns a 422 status code."""
        payload = {**self.VALID_PAYLOAD, "email": "not-an-email"}
        response = client.post("/auth/register", json=payload)
        assert response.status_code == 422

    def test_register_weak_password_returns_422(self, client):
        """Test that providing a weak password in the registration payload returns a 422 status code."""
        payload = {**self.VALID_PAYLOAD, "password": "weak"}
        response = client.post("/auth/register", json=payload)
        assert response.status_code == 422
        
class TestLoginRoute:

    def test_login_success_returns_200(self, client, registered_user):
        response = client.post("/auth/login", json={
            "email": "john@example.com",
            "password": "Secret1234!"
        })
        assert response.status_code == 200

    def test_login_returns_correct_schema(self, client, registered_user):
        response = client.post("/auth/login", json={
            "email": "john@example.com",
            "password": "Secret1234!"
        })
        body = response.json()
        assert "access_token" in body
        assert "refresh_token" in body
        assert "provider" in body
        assert "user" in body
        assert body["token_type"] == "bearer"

    def test_login_wrong_password_returns_401(self, client, registered_user):
        response = client.post("/auth/login", json={
            "email": "john@example.com",
            "password": "WrongPass99!"
        })
        assert response.status_code == 401

    def test_login_unknown_email_returns_401(self, client):
        response = client.post("/auth/login", json={
            "email": "nobody@example.com",
            "password": "Secret1234!"
        })
        assert response.status_code == 401

    def test_login_invalid_email_format_returns_422(self, client):
        response = client.post("/auth/login", json={
            "email": "not-an-email",
            "password": "Secret1234!"
        })
        assert response.status_code == 422
        


class TestGoogleLoginRoute:
    # -------------------------------------------------------------------------
    # Happy Path
    # -------------------------------------------------------------------------

    def test_valid_token_returns_200(self, client, mock_google_user):
        """Valid Google token returns 200."""
        with patch(PATCH_PATH) as mock_verify:
            mock_verify.return_value = mock_google_user
            response = client.post(
                "/auth/google",
                json={"id_token": "valid.google.token"}
            )
            assert response.status_code == 200

    def test_response_contains_access_token(self, client, mock_google_user):
        """Response body contains access_token."""
        with patch(PATCH_PATH) as mock_verify:
            mock_verify.return_value = mock_google_user
            response = client.post(
                "/auth/google",
                json={"id_token": "valid.google.token"}
            )
            assert "access_token" in response.json()

    def test_response_contains_refresh_token(self, client, mock_google_user):
        """Response body contains refresh_token."""
        with patch(PATCH_PATH) as mock_verify:
            mock_verify.return_value = mock_google_user
            response = client.post(
                "/auth/google",
                json={"id_token": "valid.google.token"}
            )
            assert "refresh_token" in response.json()

    def test_response_contains_correct_provider(self, client, mock_google_user):
        """Response provider is 'google'."""
        with patch(PATCH_PATH) as mock_verify:
            mock_verify.return_value = mock_google_user
            response = client.post(
                "/auth/google",
                json={"id_token": "valid.google.token"}
            )
            assert response.json()["provider"] == "google"

    def test_response_user_is_serialized_correctly(self, client, mock_google_user):
        """User field is serialized via UserResponse."""
        with patch(PATCH_PATH) as mock_verify:
            mock_verify.return_value = mock_google_user
            response = client.post(
                "/auth/google",
                json={"id_token": "valid.google.token"}
            )
            user = response.json()["user"]
            assert user["email"] == "john@gmail.com"
            assert user["first_name"] == "John"
            assert user["last_name"] == "Doe"

    def test_response_user_has_no_password_hash(self, client, mock_google_user):
        """Serialized user does not expose password_hash."""
        with patch(PATCH_PATH) as mock_verify:
            mock_verify.return_value = mock_google_user
            response = client.post(
                "/auth/google",
                json={"id_token": "valid.google.token"}
            )
            user = response.json()["user"]
            assert "password_hash" not in user

    def test_response_matches_login_response_schema(self, client, mock_google_user):
        """Response shape matches LoginResponse schema."""
        with patch(PATCH_PATH) as mock_verify:
            mock_verify.return_value = mock_google_user
            response = client.post(
                "/auth/google",
                json={"id_token": "valid.google.token"}
            )
            body = response.json()
            assert "access_token" in body
            assert "refresh_token" in body
            assert "provider" in body
            assert "user" in body

    # -------------------------------------------------------------------------
    # Error Path
    # -------------------------------------------------------------------------

    def test_invalid_token_returns_401(self, client,):
        """Invalid Google token returns 401."""
        with patch(PATCH_PATH) as mock_verify:
            mock_verify.return_value = None
            response = client.post(
                "/auth/google",
                json={"id_token": "invalid.token"}
            )
            assert response.status_code == 401

    def test_provider_mismatch_returns_409(self, client, existing_local_user):
        """Existing local user trying Google login returns 409."""
        with patch(PATCH_PATH) as mock_verify:
            mock_verify.return_value = MOCK_GOOGLE_USER_INFO
            response = client.post(
                "/auth/google",
                json={"id_token": "valid.token"}
            )
            assert response.status_code == 409

    # -------------------------------------------------------------------------
    # Validation
    # -------------------------------------------------------------------------

    def test_missing_id_token_returns_422(self, client):
        """Missing id_token field returns 422."""
        response = client.post("/auth/google", json={})
        assert response.status_code == 422

    def test_empty_id_token_returns_422(self, client):
        """Empty id_token string returns 422."""
        response = client.post("/auth/google", json={"id_token": ""})
        assert response.status_code == 422