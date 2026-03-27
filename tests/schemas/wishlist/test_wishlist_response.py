# tests/schemas/wishlist/test_wishlist_response.py
import uuid
import pytest
from unittest.mock import MagicMock
from pydantic import ValidationError
from schemas.wishlist.wishlist_response import WishlistResponse


# ==============================================================================
# HELPERS
# ==============================================================================

def make_wishlist_data(**overrides):
    """Helper — builds valid WishlistResponse data."""
    data = {
        "id": uuid.uuid4(),
        "product_id": "v1|123456|0",
        "name": "Wireless Headphones",
        "price": 99.99,
        "image_url": "https://example.com/img.jpg"
    }
    data.update(overrides)
    return data


# ==============================================================================
# Valid Data Tests
# ==============================================================================

class TestWishlistResponseValidData:

    def test_valid_full_data(self):
        """All fields provided with valid data passes."""
        data = WishlistResponse(**make_wishlist_data())
        assert isinstance(data.id, uuid.UUID)
        assert data.product_id == "v1|123456|0"
        assert data.name == "Wireless Headphones"
        assert data.price == 99.99
        assert data.image_url == "https://example.com/img.jpg"

    def test_image_url_defaults_to_none(self):
        """image_url defaults to None when not provided."""
        data = WishlistResponse(**make_wishlist_data(image_url=None))
        assert data.image_url is None

    def test_valid_without_image_url(self):
        """WishlistResponse is valid without image_url."""
        wishlist_data = make_wishlist_data()
        del wishlist_data["image_url"]
        data = WishlistResponse(**wishlist_data)
        assert data.image_url is None

    def test_price_coerces_int_to_float(self):
        """Integer price is coerced to float."""
        data = WishlistResponse(**make_wishlist_data(price=100))
        assert isinstance(data.price, float)
        assert data.price == 100.0


# ==============================================================================
# Required Fields Tests
# ==============================================================================

class TestWishlistResponseRequiredFields:

    def test_missing_id_raises_error(self):
        """Missing id raises ValidationError."""
        wishlist_data = make_wishlist_data()
        del wishlist_data["id"]
        with pytest.raises(ValidationError):
            WishlistResponse(**wishlist_data)

    def test_missing_product_id_raises_error(self):
        """Missing product_id raises ValidationError."""
        wishlist_data = make_wishlist_data()
        del wishlist_data["product_id"]
        with pytest.raises(ValidationError):
            WishlistResponse(**wishlist_data)

    def test_missing_name_raises_error(self):
        """Missing name raises ValidationError."""
        wishlist_data = make_wishlist_data()
        del wishlist_data["name"]
        with pytest.raises(ValidationError):
            WishlistResponse(**wishlist_data)

    def test_missing_price_raises_error(self):
        """Missing price raises ValidationError."""
        wishlist_data = make_wishlist_data()
        del wishlist_data["price"]
        with pytest.raises(ValidationError):
            WishlistResponse(**wishlist_data)

    def test_invalid_id_format_raises_error(self):
        """Non-UUID id raises ValidationError."""
        with pytest.raises(ValidationError):
            WishlistResponse(**make_wishlist_data(id="not-a-uuid"))

    def test_invalid_price_raises_error(self):
        """Non-numeric price raises ValidationError."""
        with pytest.raises(ValidationError):
            WishlistResponse(**make_wishlist_data(price="free"))

    def test_empty_payload_raises_error(self):
        """Empty payload raises ValidationError for all required fields."""
        with pytest.raises(ValidationError) as exc_info:
            WishlistResponse()
        errors = exc_info.value.errors()
        missing = {e["loc"][0] for e in errors if e["type"] == "missing"}
        assert "id" in missing
        assert "product_id" in missing
        assert "name" in missing
        assert "price" in missing


# ==============================================================================
# ORM Mapping Tests
# ==============================================================================

class TestWishlistResponseOrmMapping:

    def test_from_orm_object(self):
        """WishlistResponse maps correctly from ORM-like object."""
        mock_wishlist = MagicMock()
        mock_wishlist.id = uuid.uuid4()
        mock_wishlist.product_id = "v1|123456|0"
        mock_wishlist.name = "Wireless Headphones"
        mock_wishlist.price = 99.99
        mock_wishlist.image_url = "https://example.com/img.jpg"

        data = WishlistResponse.model_validate(mock_wishlist)
        assert data.product_id == "v1|123456|0"
        assert data.name == "Wireless Headphones"

    def test_from_orm_with_none_image_url(self):
        """Maps correctly when image_url is None."""
        mock_wishlist = MagicMock()
        mock_wishlist.id = uuid.uuid4()
        mock_wishlist.product_id = "v1|123456|0"
        mock_wishlist.name = "Wireless Headphones"
        mock_wishlist.price = 99.99
        mock_wishlist.image_url = None

        data = WishlistResponse.model_validate(mock_wishlist)
        assert data.image_url is None


# ==============================================================================
# Gap Documentation Tests
# ==============================================================================

class TestWishlistResponseGaps:

    def test_name_not_in_wishlist_model(self):
        """
        Documents gap: WishlistResponse has 'name' and 'price'
        but Wishlist model only stores 'product_id'.
        name + price must be fetched from eBay API and
        manually populated before returning response —
        same pattern as CartItemResponse.
        """
        from models.wishlist_model import Wishlist
        columns = [c.key for c in Wishlist.__table__.columns]
        assert "name" not in columns
        assert "price" not in columns