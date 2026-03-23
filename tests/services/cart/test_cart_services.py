# tests/services/cart/test_cart_services.py
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from exceptions.product_exceptions import ProductNotFoundError
from models.cart_model import Cart
from models.cart_item_model import CartItem
from models.user_model import User
from core.security import hash_password
from services.cart.cart_services import add_to_cart
from schemas.cart.cart_create import CartItemCreate


PATCH_PATH = "services.cart.cart_services.fetch_single_product"

MOCK_EBAY_PRODUCT = {
    "itemId": "v1|123456|0",
    "title": "Wireless Headphones",
    "price": {"value": "99.99", "currency": "USD"},
    "image": {"imageUrl": "https://example.com/img.jpg"}
}


# ==============================================================================
# FIXTURES
# ==============================================================================
@pytest.fixture
def user_cart(db_session, registered_user):
    """Creates a cart for the registered user."""
    cart = Cart(user_id=registered_user.id)
    db_session.add(cart)
    db_session.commit()
    db_session.refresh(cart)
    return cart


@pytest.fixture
def valid_payload():
    """Valid CartItemCreate payload."""
    return CartItemCreate(
        product_id="v1|123456|0",
        quantity=1
    )


# ==============================================================================
# Product Not Found Tests
# ==============================================================================

class TestAddToCartProductNotFound:

    @pytest.mark.asyncio
    async def test_product_not_found_raises_error(
        self, db_session, registered_user, valid_payload
    ):
        """None from fetch_single_product raises ProductNotFoundError."""
        with patch(PATCH_PATH, new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = None
            with pytest.raises(ProductNotFoundError):
                await add_to_cart(db_session, registered_user, valid_payload)

    @pytest.mark.asyncio
    async def test_product_not_found_does_not_create_cart(
        self, db_session, registered_user, valid_payload
    ):
        """No cart is created when product is not found."""
        with patch(PATCH_PATH, new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = None
            try:
                await add_to_cart(db_session, registered_user, valid_payload)
            except ProductNotFoundError:
                pass
            cart = db_session.query(Cart).filter_by(
                user_id=registered_user.id
            ).first()
            assert cart is None

    @pytest.mark.asyncio
    async def test_product_not_found_does_not_create_cart_item(
        self, db_session, registered_user, valid_payload
    ):
        """No CartItem is created when product is not found."""
        with patch(PATCH_PATH, new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = None
            try:
                await add_to_cart(db_session, registered_user, valid_payload)
            except ProductNotFoundError:
                pass
            count = db_session.query(CartItem).count()
            assert count == 0


# ==============================================================================
# Cart Creation Tests
# ==============================================================================

class TestAddToCartCreation:

    @pytest.mark.asyncio
    async def test_creates_cart_when_none_exists(
        self, db_session, registered_user, valid_payload
    ):
        """New cart is created for user with no existing cart."""
        with patch(PATCH_PATH, new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = MOCK_EBAY_PRODUCT
            await add_to_cart(db_session, registered_user, valid_payload)
            cart = db_session.query(Cart).filter_by(
                user_id=registered_user.id
            ).first()
            assert cart is not None

    @pytest.mark.asyncio
    async def test_does_not_create_duplicate_cart(
        self, db_session, registered_user, user_cart, valid_payload
    ):
        """Existing cart is reused — no duplicate created."""
        with patch(PATCH_PATH, new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = MOCK_EBAY_PRODUCT
            await add_to_cart(db_session, registered_user, valid_payload)
            count = db_session.query(Cart).filter_by(
                user_id=registered_user.id
            ).count()
            assert count == 1

    @pytest.mark.asyncio
    async def test_adds_item_to_new_cart(
        self, db_session, registered_user, valid_payload
    ):
        """CartItem is added when cart is newly created."""
        with patch(PATCH_PATH, new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = MOCK_EBAY_PRODUCT
            await add_to_cart(db_session, registered_user, valid_payload)
            cart = db_session.query(Cart).filter_by(
                user_id=registered_user.id
            ).first()
            items = db_session.query(CartItem).filter_by(
                cart_id=cart.id
            ).all()
            assert len(items) == 1
            assert items[0].product_id == "v1|123456|0"

    @pytest.mark.asyncio
    async def test_adds_item_with_correct_quantity(
        self, db_session, registered_user, valid_payload
    ):
        """CartItem is created with the correct quantity."""
        with patch(PATCH_PATH, new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = MOCK_EBAY_PRODUCT
            await add_to_cart(db_session, registered_user, valid_payload)
            cart = db_session.query(Cart).filter_by(
                user_id=registered_user.id
            ).first()
            item = db_session.query(CartItem).filter_by(
                cart_id=cart.id
            ).first()
            assert item.quantity == 1


# ==============================================================================
# Existing Cart Tests
# ==============================================================================

class TestAddToCartExistingCart:

    @pytest.mark.asyncio
    async def test_adds_new_item_to_existing_cart(
        self, db_session, registered_user, user_cart, valid_payload
    ):
        """New item is added to existing cart."""
        with patch(PATCH_PATH, new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = MOCK_EBAY_PRODUCT
            await add_to_cart(db_session, registered_user, valid_payload)
            items = db_session.query(CartItem).filter_by(
                cart_id=user_cart.id
            ).all()
            assert len(items) == 1
            assert items[0].product_id == "v1|123456|0"

    @pytest.mark.asyncio
    async def test_multiple_different_items_in_cart(
        self, db_session, registered_user, user_cart
    ):
        """Multiple different items can exist in same cart."""
        with patch(PATCH_PATH, new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = MOCK_EBAY_PRODUCT

            payload1 = CartItemCreate(product_id="v1|111|0", quantity=1)
            payload2 = CartItemCreate(product_id="v1|222|0", quantity=2)

            await add_to_cart(db_session, registered_user, payload1)
            await add_to_cart(db_session, registered_user, payload2)

            items = db_session.query(CartItem).filter_by(
                cart_id=user_cart.id
            ).all()
            assert len(items) == 2


# ==============================================================================
# Quantity Increment Tests
# ==============================================================================

class TestAddToCartQuantityIncrement:

    @pytest.mark.asyncio
    async def test_same_item_increments_quantity(
        self, db_session, registered_user, user_cart
    ):
        """Adding same item twice increments quantity."""
        with patch(PATCH_PATH, new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = MOCK_EBAY_PRODUCT

            payload = CartItemCreate(product_id="v1|123456|0", quantity=2)
            await add_to_cart(db_session, registered_user, payload)
            await add_to_cart(db_session, registered_user, payload)

            item = db_session.query(CartItem).filter_by(
                cart_id=user_cart.id,
                product_id="v1|123456|0"
            ).first()
            assert item.quantity == 4   # 2 + 2

    @pytest.mark.asyncio
    async def test_quantity_increments_correctly(
        self, db_session, registered_user, user_cart
    ):
        """Different quantities increment correctly."""
        with patch(PATCH_PATH, new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = MOCK_EBAY_PRODUCT

            payload1 = CartItemCreate(product_id="v1|123456|0", quantity=1)
            payload2 = CartItemCreate(product_id="v1|123456|0", quantity=3)

            await add_to_cart(db_session, registered_user, payload1)
            await add_to_cart(db_session, registered_user, payload2)

            item = db_session.query(CartItem).filter_by(
                cart_id=user_cart.id,
                product_id="v1|123456|0"
            ).first()
            assert item.quantity == 4   # 1 + 3

    @pytest.mark.asyncio
    async def test_same_item_does_not_create_duplicate_cart_item(
        self, db_session, registered_user, user_cart
    ):
        """Adding same item twice creates one CartItem, not two."""
        with patch(PATCH_PATH, new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = MOCK_EBAY_PRODUCT

            payload = CartItemCreate(product_id="v1|123456|0", quantity=1)
            await add_to_cart(db_session, registered_user, payload)
            await add_to_cart(db_session, registered_user, payload)

            count = db_session.query(CartItem).filter_by(
                cart_id=user_cart.id,
                product_id="v1|123456|0"
            ).count()
            assert count == 1


# ==============================================================================
# Return Value Tests
# ==============================================================================

class TestAddToCartReturnValue:

    @pytest.mark.asyncio
    async def test_returns_success_message(
        self, db_session, registered_user, valid_payload
    ):
        """Service returns correct success message."""
        with patch(PATCH_PATH, new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = MOCK_EBAY_PRODUCT
            result = await add_to_cart(
                db_session, registered_user, valid_payload
            )
            assert result == {"message": "Added to cart successfully"}

    @pytest.mark.asyncio
    async def test_returns_success_message_for_existing_item(
        self, db_session, registered_user, user_cart
    ):
        """Returns success message even when incrementing existing item."""
        with patch(PATCH_PATH, new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = MOCK_EBAY_PRODUCT
            payload = CartItemCreate(product_id="v1|123456|0", quantity=1)
            await add_to_cart(db_session, registered_user, payload)
            result = await add_to_cart(db_session, registered_user, payload)
            assert result == {"message": "Added to cart successfully"}