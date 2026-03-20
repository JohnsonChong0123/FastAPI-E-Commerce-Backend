# tests/schemas/test_auth_schemas.py
import uuid
import pytest
from unittest.mock import MagicMock
from pydantic import ValidationError
from schemas.auth.login_request import LoginRequest

class TestLoginRequest:

    def test_valid_data(self):
        data = LoginRequest(
            email="john@example.com",
            password="Secret1234!"
        )
        assert data.email == "john@example.com"
        assert data.password == "Secret1234!"

    def test_invalid_email_raises_error(self):
        with pytest.raises(ValidationError):
            LoginRequest(email="not-an-email", password="Secret1234!")

    def test_missing_email_raises_error(self):
        with pytest.raises(ValidationError):
            LoginRequest(password="Secret1234!")

    def test_missing_password_raises_error(self):
        with pytest.raises(ValidationError):
            LoginRequest(email="john@example.com")

    def test_email_normalized_to_lowercase(self):
        data = LoginRequest(
            email="JOHN@EXAMPLE.COM",
            password="Secret1234!"
        )
        assert data.email == "john@example.com"

    def test_empty_password_raises_error(self):
        with pytest.raises(ValidationError):
            LoginRequest(email="john@example.com", password="")