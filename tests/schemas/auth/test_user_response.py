# tests/schemas/test_auth_schemas.py
import uuid
import pytest
from unittest.mock import MagicMock
from pydantic import ValidationError
from schemas.auth.user_response import UserResponse
    
class TestUserResponse:

    def test_valid_full_data(self):
        data = UserResponse(
            id=uuid.uuid4(),
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            phone="0123456789",
            image_url="https://example.com/avatar.jpg",
            wallet=100.0,
            address="123 Main St",
            longitude=101.6869,
            latitude=3.1390
        )
        assert data.first_name == "John"
        assert data.email == "john@example.com"

    def test_optional_fields_default_to_none(self):
        data = UserResponse(
            id=uuid.uuid4(),
            first_name="John",
            last_name="Doe",
            email="john@example.com"
        )
        assert data.phone is None
        assert data.image_url is None
        assert data.wallet is None
        assert data.address is None
        assert data.longitude is None
        assert data.latitude is None

    def test_missing_id_raises_error(self):
        with pytest.raises(ValidationError):
            UserResponse(
                first_name="John",
                last_name="Doe",
                email="john@example.com"
            )

    def test_missing_first_name_raises_error(self):
        with pytest.raises(ValidationError):
            UserResponse(
                id=uuid.uuid4(),
                last_name="Doe",
                email="john@example.com"
            )

    def test_missing_last_name_raises_error(self):
        with pytest.raises(ValidationError):
            UserResponse(
                id=uuid.uuid4(),
                first_name="John",
                email="john@example.com"
            )

    def test_from_orm_object(self):
        """UserResponse can be built directly from an ORM model instance."""
        mock_user = MagicMock()
        mock_user.id = uuid.uuid4()
        mock_user.first_name = "John"
        mock_user.last_name = "Doe"
        mock_user.email = "john@example.com"
        mock_user.phone = None
        mock_user.image_url = None
        mock_user.wallet = None
        mock_user.address = None
        mock_user.longitude = None
        mock_user.latitude = None

        data = UserResponse.model_validate(mock_user)
        assert data.first_name == "John"
        assert data.email == "john@example.com"