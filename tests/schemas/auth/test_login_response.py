# tests/schemas/test_auth_schemas.py
import uuid
import pytest
from pydantic import ValidationError
from schemas.auth.login_response import LoginResponse
from schemas.auth.user_response import UserResponse

@pytest.fixture
def valid_user_response():
    return UserResponse(
        id=uuid.uuid4(),
        first_name="John",
        last_name="Doe",
        email="john@example.com"
    )

class TestLoginResponse:
    def test_valid_full_data(self, valid_user_response):
        data = LoginResponse(
            access_token="access.jwt.token",
            refresh_token="refresh.jwt.token",
            provider="email",
            user=valid_user_response
        )
        assert data.access_token == "access.jwt.token"
        assert data.refresh_token == "refresh.jwt.token"
        assert data.provider == "email"

    def test_token_type_defaults_to_bearer(self, valid_user_response):
        data = LoginResponse(
            access_token="access.jwt.token",
            refresh_token="refresh.jwt.token",
            provider="email",
            user=valid_user_response
        )
        assert data.token_type == "bearer"

    def test_missing_access_token_raises_error(self, valid_user_response):
        with pytest.raises(ValidationError):
            LoginResponse(
                refresh_token="refresh.jwt.token",
                provider="email",
                user=valid_user_response
            )

    def test_missing_refresh_token_raises_error(self, valid_user_response):
        with pytest.raises(ValidationError):
            LoginResponse(
                access_token="access.jwt.token",
                provider="email",
                user=valid_user_response
            )

    def test_missing_provider_raises_error(self, valid_user_response):
        with pytest.raises(ValidationError):
            LoginResponse(
                access_token="access.jwt.token",
                refresh_token="refresh.jwt.token",
                user=valid_user_response
            )

    def test_missing_user_raises_error(self):
        with pytest.raises(ValidationError):
            LoginResponse(
                access_token="access.jwt.token",
                refresh_token="refresh.jwt.token",
                provider="email"
            )

    def test_user_field_is_nested_user_response(self, valid_user_response):
        data = LoginResponse(
            access_token="access.jwt.token",
            refresh_token="refresh.jwt.token",
            provider="email",
            user=valid_user_response
        )
        assert isinstance(data.user, UserResponse)
        assert data.user.email == "john@example.com"