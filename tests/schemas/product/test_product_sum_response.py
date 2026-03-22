# tests/schemas/product/test_product_sum_response.py
import uuid
import pytest
from unittest.mock import MagicMock
from pydantic import ValidationError
from schemas.product.product_sum_response import ProductSummaryResponse


class TestProductSummaryResponse:

    # -------------------------------------------------------------------------
    # Valid Data Tests
    # -------------------------------------------------------------------------

    def test_valid_full_data(self):
        """All fields provided with valid data should pass."""
        data = ProductSummaryResponse(
            id=str(uuid.uuid4()),
            title="Wireless Headphones",
            price=99.99,
            original_price=149.99,
            image_url="https://example.com/image.jpg"
        )
        assert data.title == "Wireless Headphones"
        assert data.price == 99.99
        assert data.original_price == 149.99

    def test_valid_minimal_data(self):
        """Only required fields should pass."""
        data = ProductSummaryResponse(
            id=str(uuid.uuid4()),
            title="Wireless Headphones",
            price=99.99
        )
        assert data.title == "Wireless Headphones"
        assert data.price == 99.99

    # -------------------------------------------------------------------------
    # Optional Fields Tests
    # -------------------------------------------------------------------------

    def test_original_price_defaults_to_none(self):
        """original_price defaults to None when not provided."""
        data = ProductSummaryResponse(
            id=str(uuid.uuid4()),
            title="Wireless Headphones",
            price=99.99
        )
        assert data.original_price is None

    def test_image_url_defaults_to_none(self):
        """image_url defaults to None when not provided."""
        data = ProductSummaryResponse(
            id=str(uuid.uuid4()),
            title="Wireless Headphones",
            price=99.99
        )
        assert data.image_url is None

    # -------------------------------------------------------------------------
    # Required Fields Tests
    # -------------------------------------------------------------------------

    def test_missing_id_raises_error(self):
        """Missing id raises ValidationError."""
        with pytest.raises(ValidationError):
            ProductSummaryResponse(
                title="Wireless Headphones",
                price=99.99
            )

    def test_missing_title_raises_error(self):
        """Missing title raises ValidationError."""
        with pytest.raises(ValidationError):
            ProductSummaryResponse(
                id=str(uuid.uuid4()),
                price=99.99
            )

    def test_missing_price_raises_error(self):
        """Missing price raises ValidationError."""
        with pytest.raises(ValidationError):
            ProductSummaryResponse(
                id=str(uuid.uuid4()),
                title="Wireless Headphones"
            )

    # -------------------------------------------------------------------------
    # Field Type Tests
    # -------------------------------------------------------------------------

    def test_price_must_be_numeric(self):
        """Non-numeric price raises ValidationError."""
        with pytest.raises(ValidationError):
            ProductSummaryResponse(
                id=str(uuid.uuid4()),
                title="Wireless Headphones",
                price="not-a-price"
            )

    def test_price_coerces_int_to_float(self):
        """Integer price is coerced to float."""
        data = ProductSummaryResponse(
            id=str(uuid.uuid4()),
            title="Wireless Headphones",
            price=100
        )
        assert isinstance(data.price, float)
        assert data.price == 100.0

    def test_original_price_must_be_numeric(self):
        """Non-numeric original_price raises ValidationError."""
        with pytest.raises(ValidationError):
            ProductSummaryResponse(
                id=str(uuid.uuid4()),
                title="Wireless Headphones",
                price=99.99,
                original_price="not-a-price"
            )

    def test_price_zero_is_valid(self):
        """Zero price is a valid value."""
        data = ProductSummaryResponse(
            id=str(uuid.uuid4()),
            title="Free Item",
            price=0.0
        )
        assert data.price == 0.0

    def test_negative_price_is_accepted(self):
        """
        Negative price currently passes — documents behaviour.
        Consider adding Field(ge=0) constraint if this is undesirable.
        """
        data = ProductSummaryResponse(
            id=str(uuid.uuid4()),
            title="Wireless Headphones",
            price=-10.0
        )
        assert data.price == -10.0

    # -------------------------------------------------------------------------
    # ORM Mapping Tests
    # -------------------------------------------------------------------------

    def test_from_orm_object(self):
        """ProductSummaryResponse maps correctly from an ORM object."""
        mock_product = MagicMock()
        mock_product.id = str(uuid.uuid4())
        mock_product.title = "Wireless Headphones"
        mock_product.price = 99.99
        mock_product.original_price = 149.99
        mock_product.image_url = "https://example.com/image.jpg"

        data = ProductSummaryResponse.model_validate(mock_product)
        assert data.title == "Wireless Headphones"
        assert data.price == 99.99

    def test_from_orm_object_with_optional_none(self):
        """ORM object with None optional fields maps correctly."""
        mock_product = MagicMock()
        mock_product.id = str(uuid.uuid4())
        mock_product.title = "Wireless Headphones"
        mock_product.price = 99.99
        mock_product.original_price = None
        mock_product.image_url = None

        data = ProductSummaryResponse.model_validate(mock_product)
        assert data.original_price is None
        assert data.image_url is None