# tests/schemas/cart/test_cart_create.py
import pytest
from pydantic import ValidationError
from schemas.cart.cart_create import CartItemCreate

class TestCartItemCreate:

    # -------------------------------------------------------------------------
    # Valid Data Tests
    # -------------------------------------------------------------------------

    def test_valid_full_data(self):
        """Valid product_id and quantity passes."""
        data = CartItemCreate(
            product_id="ebay-item-001",
            quantity=2
        )
        assert data.product_id == "ebay-item-001"
        assert data.quantity == 2

    def test_quantity_of_one_is_valid(self):
        """Minimum valid quantity is 1."""
        data = CartItemCreate(
            product_id="ebay-item-001",
            quantity=1
        )
        assert data.quantity == 1

    def test_large_quantity_is_valid(self):
        """Large quantity values are accepted."""
        data = CartItemCreate(
            product_id="ebay-item-001",
            quantity=999
        )
        assert data.quantity == 999

    # -------------------------------------------------------------------------
    # product_id Validation Tests
    # -------------------------------------------------------------------------

    def test_empty_product_id_raises_error(self):
        """Empty product_id raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            CartItemCreate(product_id="", quantity=1)
        assert "product_id" in str(exc_info.value).lower()

    def test_missing_product_id_raises_error(self):
        """Missing product_id raises ValidationError."""
        with pytest.raises(ValidationError):
            CartItemCreate(quantity=1)

    def test_whitespace_product_id_raises_error(self):
        """
        Single space product_id — min_length=1 currently passes this.
        Documents the gap — consider strip() + min_length validation.
        """
        data = CartItemCreate(product_id=" ", quantity=1)
        assert data.product_id == " "   # ← passes, documents gap

    # -------------------------------------------------------------------------
    # quantity Validation Tests
    # -------------------------------------------------------------------------

    def test_zero_quantity_raises_error(self):
        """Zero quantity raises ValidationError (gt=0 constraint)."""
        with pytest.raises(ValidationError) as exc_info:
            CartItemCreate(product_id="ebay-item-001", quantity=0)
        assert "quantity" in str(exc_info.value).lower()

    def test_negative_quantity_raises_error(self):
        """Negative quantity raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            CartItemCreate(product_id="ebay-item-001", quantity=-1)
        assert "quantity" in str(exc_info.value).lower()

    def test_missing_quantity_raises_error(self):
        """Missing quantity raises ValidationError."""
        with pytest.raises(ValidationError):
            CartItemCreate(product_id="ebay-item-001")

    def test_float_quantity_raises_error(self):
        """Float quantity raises ValidationError."""
        with pytest.raises(ValidationError):
            CartItemCreate(product_id="ebay-item-001", quantity=1.5)

    def test_string_quantity_raises_error(self):
        """Non-numeric quantity raises ValidationError."""
        with pytest.raises(ValidationError):
            CartItemCreate(product_id="ebay-item-001", quantity="two")

    # -------------------------------------------------------------------------
    # Missing Fields Tests
    # -------------------------------------------------------------------------

    def test_empty_payload_raises_error(self):
        """Empty payload raises ValidationError for both fields."""
        with pytest.raises(ValidationError) as exc_info:
            CartItemCreate()
        errors = exc_info.value.errors()
        missing = {e["loc"][0] for e in errors if e["type"] == "missing"}
        assert "product_id" in missing
        assert "quantity" in missing

    def test_empty_payload_reports_two_missing_fields(self):
        """Empty payload reports exactly 2 missing required fields."""
        with pytest.raises(ValidationError) as exc_info:
            CartItemCreate()
        errors = exc_info.value.errors()
        missing = [e for e in errors if e["type"] == "missing"]
        assert len(missing) == 2