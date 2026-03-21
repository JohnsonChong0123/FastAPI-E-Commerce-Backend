# tests/core/test_exception_handler.py
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from core.exception_handler import register_exceptions
from exceptions.auth_exceptions import (
    AuthProviderMismatchError,
    EmailAlreadyExistsError, 
    InvalidCredentialsError,
    InvalidGoogleTokenError, 
    TokenExpiredError,
    InvalidTokenError,
    InvalidFacebookTokenError
)

@pytest.fixture
def mock_app():
    """Create a mock FastAPI app with registered exception handlers for testing."""
    app = FastAPI()
    register_exceptions(app)
    return app

@pytest.mark.parametrize("exception_class, expected_status, expected_detail", [
    (EmailAlreadyExistsError, 409, "Email already registered"),
    (InvalidCredentialsError, 401, "Invalid email or password"),
    (TokenExpiredError, 401, "Token expired"),
    (InvalidTokenError, 401, "Invalid token"),
    (InvalidGoogleTokenError, 401, "Invalid Google token"),
    (AuthProviderMismatchError, 409, "Account exists with different login method"),
    (InvalidFacebookTokenError, 401, "Invalid Facebook token")
])
def test_exception_handlers_format(mock_app, exception_class, expected_status, expected_detail):
    @mock_app.get("/trigger-error")
    def trigger():
        raise exception_class()

    client = TestClient(mock_app)
    response = client.get("/trigger-error")
    
    assert response.status_code == expected_status
    assert response.json() == {"detail": expected_detail}