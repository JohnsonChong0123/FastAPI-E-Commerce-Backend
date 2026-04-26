# tests/schemas/product/test_product_details_response.py
import pytest
from unittest.mock import MagicMock
from pydantic import ValidationError
from schemas.product.product_details_response import ProductDetailsResponse


# ==============================================================================
# HELPERS
# ==============================================================================

def make_product_data(**overrides):
    """Helper — builds valid ProductDetailsResponse data."""
    data = {
        "id": "v1|123456|0",
        "title": "Wireless Headphones",
        "description": "High quality wireless headphones with ANC.",
        "price": 99.99,
        "image_url": "https://example.com/img.jpg",
        "additional_images": ["https://example.com/img1.jpg", "https://example.com/img2.jpg"]
    }
    data.update(overrides)
    return data


# ==============================================================================
# Valid Data Tests
# ==============================================================================

class TestProductDetailsResponseValidData:

    def test_valid_full_data(self):
        """All fields provided with valid data passes."""
        data = ProductDetailsResponse(**make_product_data())
        assert data.id == "v1|123456|0"
        assert data.title == "Wireless Headphones"
        assert data.description == "High quality wireless headphones with ANC."
        assert data.price == 99.99
        assert data.image_url == "https://example.com/img.jpg"
        assert data.additional_images == ["https://example.com/img1.jpg", "https://example.com/img2.jpg"]

    def test_image_url_defaults_to_none(self):
        """image_url defaults to None when not provided."""
        data = ProductDetailsResponse(**make_product_data(image_url=None))
        assert data.image_url is None

    def test_valid_without_image_url(self):
        """ProductDetailsResponse is valid without image_url."""
        product_data = make_product_data()
        del product_data["image_url"]
        data = ProductDetailsResponse(**product_data)
        assert data.image_url is None

    def test_valid_without_additional_images(self):
        """ProductDetailsResponse is valid without additional_images."""
        product_data = make_product_data()
        del product_data["additional_images"]
        data = ProductDetailsResponse(**product_data)
        assert data.additional_images is None

    def test_price_coerces_int_to_float(self):
        """Integer price is coerced to float."""
        data = ProductDetailsResponse(**make_product_data(price=100))
        assert isinstance(data.price, float)
        assert data.price == 100.0

    def test_empty_description_is_valid(self):
        """Empty string description is accepted."""
        data = ProductDetailsResponse(**make_product_data(description=""))
        assert data.description == ""


# ==============================================================================
# Required Fields Tests
# ==============================================================================

class TestProductDetailsResponseRequiredFields:

    def test_missing_id_raises_error(self):
        """Missing id raises ValidationError."""
        product_data = make_product_data()
        del product_data["id"]
        with pytest.raises(ValidationError):
            ProductDetailsResponse(**product_data)

    def test_missing_title_raises_error(self):
        """Missing title raises ValidationError."""
        product_data = make_product_data()
        del product_data["title"]
        with pytest.raises(ValidationError):
            ProductDetailsResponse(**product_data)

    def test_missing_description_raises_error(self):
        """Missing description raises ValidationError."""
        product_data = make_product_data()
        del product_data["description"]
        with pytest.raises(ValidationError):
            ProductDetailsResponse(**product_data)

    def test_missing_price_raises_error(self):
        """Missing price raises ValidationError."""
        product_data = make_product_data()
        del product_data["price"]
        with pytest.raises(ValidationError):
            ProductDetailsResponse(**product_data)

    def test_invalid_price_raises_error(self):
        """Non-numeric price raises ValidationError."""
        with pytest.raises(ValidationError):
            ProductDetailsResponse(**make_product_data(price="free"))

    def test_negative_price_is_accepted(self):
        """
        Negative price currently passes — documents behaviour.
        Consider adding Field(ge=0) constraint.
        """
        data = ProductDetailsResponse(**make_product_data(price=-10.0))
        assert data.price == -10.0

    def test_empty_payload_raises_error(self):
        """Empty payload raises ValidationError for all required fields."""
        with pytest.raises(ValidationError) as exc_info:
            ProductDetailsResponse()
        errors = exc_info.value.errors()
        missing = {e["loc"][0] for e in errors if e["type"] == "missing"}
        assert "id" in missing
        assert "title" in missing
        assert "description" in missing
        assert "price" in missing


# ==============================================================================
# ORM Mapping Tests
# ==============================================================================

class TestProductDetailsResponseOrmMapping:

    def test_from_orm_object(self):
        """ProductDetailsResponse maps correctly from ORM-like object."""
        mock_product = MagicMock()
        mock_product.id = "v1|123456|0"
        mock_product.title = "Wireless Headphones"
        mock_product.description = "Great headphones."
        mock_product.price = 99.99
        mock_product.image_url = "https://example.com/img.jpg"
        mock_product.additional_images = ["https://example.com/img1.jpg", "https://example.com/img2.jpg"]

        data = ProductDetailsResponse.model_validate(mock_product)
        assert data.id == "v1|123456|0"
        assert data.description == "Great headphones."
        assert data.additional_images == ["https://example.com/img1.jpg", "https://example.com/img2.jpg"]

    def test_from_orm_with_none_image_url(self):
        """Maps correctly when image_url is None."""
        mock_product = MagicMock()
        mock_product.id = "v1|123456|0"
        mock_product.title = "Wireless Headphones"
        mock_product.description = "Great headphones."
        mock_product.price = 99.99
        mock_product.image_url = None
        mock_product.additional_images = None

        data = ProductDetailsResponse.model_validate(mock_product)
        assert data.image_url is None
        assert data.additional_images is None


# ==============================================================================
# Comparison vs ProductSummaryResponse
# ==============================================================================

class TestProductDetailsVsSummary:

    def test_description_is_required_unlike_summary(self):
        """description is required in Details but absent in Summary."""
        product_data = make_product_data()
        del product_data["description"]
        with pytest.raises(ValidationError):
            ProductDetailsResponse(**product_data)

    def test_no_original_price_field(self):
        """ProductDetailsResponse has no original_price field."""
        data = ProductDetailsResponse(**make_product_data())
        assert not hasattr(data, "original_price")