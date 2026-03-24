# tests/schemas/cart/test_cart_response.py
import uuid
import pytest
from unittest.mock import MagicMock
from pydantic import ValidationError
from schemas.cart.cart_response import CartItemResponse, CartResponse


# ==============================================================================
# HELPERS
# ==============================================================================

def make_cart_item_data(**overrides):
    """Helper — builds valid CartItemResponse data."""
    data = {
        "product_id": "v1|123456|0",
        "name": "Wireless Headphones",
        "price": 99.99,
        "quantity": 2,
        "image_url": "https://example.com/img.jpg"
    }
    data.update(overrides)
    return data


def make_cart_data(**overrides):
    """Helper — builds valid CartResponse data."""
    data = {
        "id": uuid.uuid4(),
        "items": [make_cart_item_data()],
        "cart_total": 199.98
    }
    data.update(overrides)
    return data


# ==============================================================================
# CartItemResponse Tests
# ==============================================================================

class TestCartItemResponse:

    # -------------------------------------------------------------------------
    # Valid Data Tests
    # -------------------------------------------------------------------------

    def test_valid_full_data(self):
        """All fields provided with valid data passes."""
        data = CartItemResponse(**make_cart_item_data())
        assert data.product_id == "v1|123456|0"
        assert data.name == "Wireless Headphones"
        assert data.price == 99.99
        assert data.quantity == 2
        assert data.image_url == "https://example.com/img.jpg"

    def test_image_url_defaults_to_none(self):
        """image_url defaults to None when not provided."""
        data = CartItemResponse(**make_cart_item_data(image_url=None))
        assert data.image_url is None

    def test_valid_without_image_url(self):
        """CartItemResponse is valid without image_url."""
        item_data = make_cart_item_data()
        del item_data["image_url"]
        data = CartItemResponse(**item_data)
        assert data.image_url is None

    def test_price_coerces_int_to_float(self):
        """Integer price is coerced to float."""
        data = CartItemResponse(**make_cart_item_data(price=100))
        assert isinstance(data.price, float)
        assert data.price == 100.0

    # -------------------------------------------------------------------------
    # Required Fields Tests
    # -------------------------------------------------------------------------

    def test_missing_product_id_raises_error(self):
        """Missing product_id raises ValidationError."""
        item_data = make_cart_item_data()
        del item_data["product_id"]
        with pytest.raises(ValidationError):
            CartItemResponse(**item_data)

    def test_missing_name_raises_error(self):
        """Missing name raises ValidationError."""
        item_data = make_cart_item_data()
        del item_data["name"]
        with pytest.raises(ValidationError):
            CartItemResponse(**item_data)

    def test_missing_price_raises_error(self):
        """Missing price raises ValidationError."""
        item_data = make_cart_item_data()
        del item_data["price"]
        with pytest.raises(ValidationError):
            CartItemResponse(**item_data)

    def test_missing_quantity_raises_error(self):
        """Missing quantity raises ValidationError."""
        item_data = make_cart_item_data()
        del item_data["quantity"]
        with pytest.raises(ValidationError):
            CartItemResponse(**item_data)

    def test_invalid_price_raises_error(self):
        """Non-numeric price raises ValidationError."""
        with pytest.raises(ValidationError):
            CartItemResponse(**make_cart_item_data(price="not-a-price"))

    def test_invalid_quantity_raises_error(self):
        """Non-integer quantity raises ValidationError."""
        with pytest.raises(ValidationError):
            CartItemResponse(**make_cart_item_data(quantity="two"))

    # -------------------------------------------------------------------------
    # ORM Mapping Tests
    # -------------------------------------------------------------------------

    def test_from_orm_object(self):
        """CartItemResponse maps correctly from ORM object."""
        mock_item = MagicMock()
        mock_item.product_id = "v1|123456|0"
        mock_item.name = "Wireless Headphones"
        mock_item.price = 99.99
        mock_item.quantity = 2
        mock_item.image_url = "https://example.com/img.jpg"

        data = CartItemResponse.model_validate(mock_item)
        assert data.product_id == "v1|123456|0"
        assert data.quantity == 2

    def test_from_orm_object_with_none_image(self):
        """CartItemResponse maps correctly when image_url is None."""
        mock_item = MagicMock()
        mock_item.product_id = "v1|123456|0"
        mock_item.name = "Wireless Headphones"
        mock_item.price = 99.99
        mock_item.quantity = 2
        mock_item.image_url = None

        data = CartItemResponse.model_validate(mock_item)
        assert data.image_url is None


# ==============================================================================
# CartResponse Tests
# ==============================================================================

class TestCartResponse:

    # -------------------------------------------------------------------------
    # Valid Data Tests
    # -------------------------------------------------------------------------

    def test_valid_full_data(self):
        """All fields provided with valid data passes."""
        data = CartResponse(**make_cart_data())
        assert isinstance(data.id, uuid.UUID)
        assert len(data.items) == 1
        assert data.cart_total == 199.98

    def test_empty_items_list_is_valid(self):
        """Cart with no items is valid."""
        data = CartResponse(**make_cart_data(items=[], cart_total=0.0))
        assert data.items == []
        assert data.cart_total == 0.0

    def test_multiple_items_in_cart(self):
        """Cart with multiple items is valid."""
        data = CartResponse(**make_cart_data(
            items=[
                make_cart_item_data(product_id="v1|111|0"),
                make_cart_item_data(product_id="v1|222|0"),
                make_cart_item_data(product_id="v1|333|0")
            ],
            cart_total=299.97
        ))
        assert len(data.items) == 3

    def test_items_are_cart_item_response_instances(self):
        """Each item in items list is a CartItemResponse instance."""
        data = CartResponse(**make_cart_data())
        for item in data.items:
            assert isinstance(item, CartItemResponse)

    def test_cart_total_coerces_int_to_float(self):
        """Integer cart_total is coerced to float."""
        data = CartResponse(**make_cart_data(cart_total=100))
        assert isinstance(data.cart_total, float)

    # -------------------------------------------------------------------------
    # Required Fields Tests
    # -------------------------------------------------------------------------

    def test_missing_id_raises_error(self):
        """Missing id raises ValidationError."""
        cart_data = make_cart_data()
        del cart_data["id"]
        with pytest.raises(ValidationError):
            CartResponse(**cart_data)

    def test_missing_items_raises_error(self):
        """Missing items raises ValidationError."""
        cart_data = make_cart_data()
        del cart_data["items"]
        with pytest.raises(ValidationError):
            CartResponse(**cart_data)

    def test_missing_cart_total_raises_error(self):
        """Missing cart_total raises ValidationError."""
        cart_data = make_cart_data()
        del cart_data["cart_total"]
        with pytest.raises(ValidationError):
            CartResponse(**cart_data)

    def test_invalid_id_format_raises_error(self):
        """Non-UUID id raises ValidationError."""
        with pytest.raises(ValidationError):
            CartResponse(**make_cart_data(id="not-a-uuid"))

    def test_invalid_cart_total_raises_error(self):
        """Non-numeric cart_total raises ValidationError."""
        with pytest.raises(ValidationError):
            CartResponse(**make_cart_data(cart_total="free"))

    # -------------------------------------------------------------------------
    # ORM Mapping Tests
    # -------------------------------------------------------------------------

    def test_from_orm_object(self):
        """CartResponse maps correctly from ORM object."""
        mock_item = MagicMock()
        mock_item.product_id = "v1|123456|0"
        mock_item.name = "Wireless Headphones"
        mock_item.price = 99.99
        mock_item.quantity = 2
        mock_item.image_url = None

        mock_cart = MagicMock()
        mock_cart.id = uuid.uuid4()
        mock_cart.items = [mock_item]
        mock_cart.cart_total = 99.99

        data = CartResponse.model_validate(mock_cart)
        assert isinstance(data.id, uuid.UUID)
        assert len(data.items) == 1
        assert data.cart_total == 99.99

    def test_from_orm_object_empty_cart(self):
        """CartResponse maps correctly from ORM object with no items."""
        mock_cart = MagicMock()
        mock_cart.id = uuid.uuid4()
        mock_cart.items = []
        mock_cart.cart_total = 0.0

        data = CartResponse.model_validate(mock_cart)
        assert data.items == []
        assert data.cart_total == 0.0


# ==============================================================================
# Gap Documentation Tests
# ==============================================================================

class TestCartSchemaGaps:

    def test_cart_item_name_not_in_cart_item_model(self):
        """
        Documents gap: CartItemResponse has a 'name' field
        but CartItem model has no 'name' column.
        Name must come from eBay API — not stored in DB.
        Serialization from ORM object will fail unless
        name is manually populated before returning response.
        """
        from models.cart_item_model import CartItem
        columns = [c.key for c in CartItem.__table__.columns]
        assert "name" not in columns   # ← documents the gap

    def test_cart_response_cart_total_not_in_cart_model(self):
        """
        Documents gap: CartResponse has a 'cart_total' field
        but Cart model has no 'cart_total' column.
        Total must be computed — not stored in DB.
        Serialization from ORM object will fail unless
        cart_total is computed before returning response.
        """
        from models.cart_model import Cart
        columns = [c.key for c in Cart.__table__.columns]
        assert "cart_total" not in columns   # ← documents the gap