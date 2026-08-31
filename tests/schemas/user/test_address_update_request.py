# tests/schemas/user/test_address_update_request.py
import pytest
from pydantic import ValidationError
from schemas.user.address_update_request import AddressUpdateRequest


class TestAddressUpdateRequest:

    def test_valid_data(self):
        data = AddressUpdateRequest(
            user_address="123 Main St, City, Country",
            user_latitude=40.7128,
            user_longitude=-74.0060
        )
        assert data.user_address == "123 Main St, City, Country"
        assert data.user_latitude == 40.7128
        assert data.user_longitude == -74.0060

    def test_missing_user_address_raises_error(self):
        with pytest.raises(ValidationError):
            AddressUpdateRequest(
                user_latitude=40.7128,
                user_longitude=-74.0060
            )

    def test_missing_user_latitude_raises_error(self):
        with pytest.raises(ValidationError):
            AddressUpdateRequest(
                user_address="123 Main St, City, Country",
                user_longitude=-74.0060
            )

    def test_missing_user_longitude_raises_error(self):
        with pytest.raises(ValidationError):
            AddressUpdateRequest(
                user_address="123 Main St, City, Country",
                user_latitude=40.7128
            )

    def test_invalid_latitude_type_raises_error(self):
        with pytest.raises(ValidationError):
            AddressUpdateRequest(
                user_address="123 Main St, City, Country",
                user_latitude="invalid",
                user_longitude=-74.0060
            )

    def test_invalid_longitude_type_raises_error(self):
        with pytest.raises(ValidationError):
            AddressUpdateRequest(
                user_address="123 Main St, City, Country",
                user_latitude=40.7128,
                user_longitude="invalid"
            )

    def test_negative_latitude_valid(self):
        data = AddressUpdateRequest(
            user_address="123 Main St, City, Country",
            user_latitude=-33.8688,
            user_longitude=151.2093
        )
        assert data.user_latitude == -33.8688

    def test_negative_longitude_valid(self):
        data = AddressUpdateRequest(
            user_address="123 Main St, City, Country",
            user_latitude=40.7128,
            user_longitude=-74.0060
        )
        assert data.user_longitude == -74.0060

    def test_zero_coordinates_valid(self):
        data = AddressUpdateRequest(
            user_address="123 Main St, City, Country",
            user_latitude=0.0,
            user_longitude=0.0
        )
        assert data.user_latitude == 0.0
        assert data.user_longitude == 0.0