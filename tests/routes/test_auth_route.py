# tests/routes/test_auth_route.py

class TestRegisterRoute:

    VALID_PAYLOAD = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john@example.com",
        "password": "Secret1234!"
    }

    def test_register_success_returns_200(self, client):
        """Test that a valid registration returns a 200 status code."""
        response = client.post("/auth/register", json=self.VALID_PAYLOAD)
        assert response.status_code == 200

    def test_register_returns_success_message(self, client):
        """Test that a successful registration returns the expected success message."""
        response = client.post("/auth/register", json=self.VALID_PAYLOAD)
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