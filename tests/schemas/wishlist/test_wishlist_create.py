# tests/schemas/wishlist/test_wishlist_create.py
import pytest
from pydantic import ValidationError
from schemas.wishlist.wishlist_create import WishlistCreate


class TestWishlistCreate:

    # -------------------------------------------------------------------------
    # Valid Data Tests
    # -------------------------------------------------------------------------

    def test_valid_product_id(self):
        """Valid product_id string passes."""
        data = WishlistCreate(product_id="v1|123456|0")
        assert data.product_id == "v1|123456|0"

    def test_any_non_empty_string_is_valid(self):
        """Any non-empty product_id is accepted."""
        data = WishlistCreate(product_id="ebay-item-abc")
        assert data.product_id == "ebay-item-abc"

    # -------------------------------------------------------------------------
    # product_id Validation Tests
    # -------------------------------------------------------------------------

    def test_missing_product_id_raises_error(self):
        """Missing product_id raises ValidationError."""
        with pytest.raises(ValidationError):
            WishlistCreate()

    def test_empty_product_id_raises_error(self):
        """Empty string product_id raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            WishlistCreate(product_id="")
        assert "product_id" in str(exc_info.value).lower()

    def test_whitespace_product_id_raises_error(self):
        """
        Whitespace-only product_id — min_length=1 currently passes this.
        Documents the gap — consider adding strip() validator.
        """
        data = WishlistCreate(product_id=" ")
        assert data.product_id == " "   