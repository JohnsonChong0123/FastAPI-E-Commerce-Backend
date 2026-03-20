# tests/routes/test_auth_route.py

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