# tests/services/cart/test_cart_services.py
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from exceptions.product_exceptions import ProductNotFoundError
from models.cart_model import Cart
from models.cart_item_model import CartItem
from models.user_model import User
from core.security import hash_password
from services.cart.cart_services import add_to_cart, get_cart, remove_cart_item
from schemas.cart.cart_create import CartItemCreate
from sqlalchemy import select
from exceptions.cart_exceptions import CartNotFoundError, CartItemNotFoundError
from services.cart.cart_services import clear_cart

PATCH_PATH = "services.cart.cart_services.fetch_single_product"

MOCK_EBAY_PRODUCT = {
    "itemId": "v1|123456|0",
    "title": "Wireless Headphones",
    "price": {"value": "99.99", "currency": "USD"},
    "image": {"imageUrl": "https://example.com/img.jpg"}
}

MOCK_EBAY_PRODUCT_1 = {
    "itemId": "v1|111|0",
    "title": "Wireless Headphones",
    "price": {"value": "99.99"},
    "image": {"imageUrl": "https://example.com/img1.jpg"}
}

MOCK_EBAY_PRODUCT_2 = {
    "itemId": "v1|222|0",
    "title": "Bluetooth Speaker",
    "price": {"value": "49.99"},
    "image": {"imageUrl": "https://example.com/img2.jpg"}
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
    
@pytest.fixture
def cart_with_item(db_session, user_cart):
    """Cart with one item."""
    item = CartItem(
        cart_id=user_cart.id,
        product_id="v1|123456|0",
        quantity=2
    )
    db_session.add(item)
    db_session.commit()
    db_session.refresh(user_cart)
    return user_cart
    
@pytest.fixture
def cart_with_multiple_items(db_session, user_cart):
    """Cart with multiple items."""
    item1 = CartItem(
        cart_id=user_cart.id,
        product_id="v1|111|0",
        quantity=2
    )
    item2 = CartItem(
        cart_id=user_cart.id,
        product_id="v1|222|0",
        quantity=3
    )
    db_session.add_all([item1, item2])
    db_session.commit()
    db_session.refresh(user_cart)
    return user_cart
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
            
# ==============================================================================
# Empty Cart Tests
# ==============================================================================

class TestGetCartEmpty:

    @pytest.mark.asyncio
    async def test_no_cart_returns_empty_response(
        self, db_session, registered_user
    ):
        """User with no cart returns empty cart response."""
        result = await get_cart(db_session, registered_user)
        assert result["items"] == []
        assert result["cart_total"] == 0

    @pytest.mark.asyncio
    async def test_no_cart_returns_none_id(
        self, db_session, registered_user
    ):
        """User with no cart returns None as id."""
        result = await get_cart(db_session, registered_user)
        assert result["id"] is None

    @pytest.mark.asyncio
    async def test_cart_with_no_items_returns_empty_response(
        self, db_session, registered_user, user_cart
    ):
        """Cart with no items returns empty items list."""
        result = await get_cart(db_session, registered_user)
        assert result["items"] == []
        assert result["cart_total"] == 0

    @pytest.mark.asyncio
    async def test_cart_with_no_items_returns_correct_id(
        self, db_session, registered_user, user_cart
    ):
        """Cart with no items still returns correct cart id."""
        result = await get_cart(db_session, registered_user)
        assert result["id"] == user_cart.id


# ==============================================================================
# Happy Path Tests
# ==============================================================================

class TestGetCartHappyPath:

    @pytest.mark.asyncio
    async def test_returns_all_items(
        self, db_session, registered_user, cart_with_multiple_items
    ):
        """Returns all items when all products found."""
        with patch(PATCH_PATH, new_callable=AsyncMock) as mock_fetch:
            mock_fetch.side_effect = [
                MOCK_EBAY_PRODUCT_1,
                MOCK_EBAY_PRODUCT_2
            ]
            result = await get_cart(db_session, registered_user)
            assert len(result["items"]) == 2

    @pytest.mark.asyncio
    async def test_returns_correct_item_fields(
        self, db_session, registered_user, cart_with_multiple_items
    ):
        """Each item contains correct fields from eBay product."""
        with patch(PATCH_PATH, new_callable=AsyncMock) as mock_fetch:
            mock_fetch.side_effect = [
                MOCK_EBAY_PRODUCT_1,
                MOCK_EBAY_PRODUCT_2
            ]
            result = await get_cart(db_session, registered_user)
            first_item = result["items"][0]
            assert first_item["product_id"] == "v1|111|0"
            assert first_item["name"] == "Wireless Headphones"
            assert first_item["price"] == 99.99
            assert first_item["quantity"] == 2
            assert first_item["image_url"] == "https://example.com/img1.jpg"

    @pytest.mark.asyncio
    async def test_returns_correct_cart_id(
        self, db_session, registered_user, cart_with_multiple_items
    ):
        """Returns correct cart UUID."""
        with patch(PATCH_PATH, new_callable=AsyncMock) as mock_fetch:
            mock_fetch.side_effect = [
                MOCK_EBAY_PRODUCT_1,
                MOCK_EBAY_PRODUCT_2
            ]
            result = await get_cart(db_session, registered_user)
            assert result["id"] == cart_with_multiple_items.id


# ==============================================================================
# Cart Total Calculation Tests
# ==============================================================================

class TestGetCartTotal:

    @pytest.mark.asyncio
    async def test_cart_total_calculated_correctly(
        self, db_session, registered_user, cart_with_multiple_items
    ):
        """
        cart_total = sum(price * quantity) per item.
        item1: 99.99 * 2 = 199.98
        item2: 49.99 * 3 = 149.97
        total: 199.98 + 149.97 = 349.95
        """
        with patch(PATCH_PATH, new_callable=AsyncMock) as mock_fetch:
            mock_fetch.side_effect = [
                MOCK_EBAY_PRODUCT_1,
                MOCK_EBAY_PRODUCT_2
            ]
            result = await get_cart(db_session, registered_user)
            assert round(result["cart_total"], 2) == 349.95

    @pytest.mark.asyncio
    async def test_cart_total_single_item(
        self, db_session, registered_user, user_cart
    ):
        """cart_total for single item = price * quantity."""
        item = CartItem(
            cart_id=user_cart.id,
            product_id="v1|111|0",
            quantity=3
        )
        db_session.add(item)
        db_session.commit()

        with patch(PATCH_PATH, new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = MOCK_EBAY_PRODUCT_1
            result = await get_cart(db_session, registered_user)
            assert round(result["cart_total"], 2) == round(99.99 * 3, 2)

    @pytest.mark.asyncio
    async def test_cart_total_zero_when_no_items(
        self, db_session, registered_user
    ):
        """cart_total is 0 when no items."""
        result = await get_cart(db_session, registered_user)
        assert result["cart_total"] == 0


# ==============================================================================
# Missing Product Tests
# ==============================================================================

class TestGetCartMissingProducts:

    @pytest.mark.asyncio
    async def test_skips_item_when_product_not_found(
        self, db_session, registered_user, cart_with_multiple_items
    ):
        """Items with no eBay product are skipped."""
        with patch(PATCH_PATH, new_callable=AsyncMock) as mock_fetch:
            mock_fetch.side_effect = [
                MOCK_EBAY_PRODUCT_1,
                None    # second product not found
            ]
            result = await get_cart(db_session, registered_user)
            assert len(result["items"]) == 1
            assert result["items"][0]["product_id"] == "v1|111|0"

    @pytest.mark.asyncio
    async def test_cart_total_excludes_missing_products(
        self, db_session, registered_user, cart_with_multiple_items
    ):
        """cart_total only includes items with found products."""
        with patch(PATCH_PATH, new_callable=AsyncMock) as mock_fetch:
            mock_fetch.side_effect = [
                MOCK_EBAY_PRODUCT_1,
                None    # second product not found
            ]
            result = await get_cart(db_session, registered_user)
            # Only item1: 99.99 * 2 = 199.98
            assert round(result["cart_total"], 2) == 199.98

    @pytest.mark.asyncio
    async def test_all_products_missing_returns_empty_items(
        self, db_session, registered_user, cart_with_multiple_items
    ):
        """All products missing returns empty items list."""
        with patch(PATCH_PATH, new_callable=AsyncMock) as mock_fetch:
            mock_fetch.side_effect = [None, None]
            result = await get_cart(db_session, registered_user)
            assert result["items"] == []
            assert result["cart_total"] == 0


# ==============================================================================
# Parallel Fetch Tests
# ==============================================================================

class TestGetCartParallelFetch:

    @pytest.mark.asyncio
    async def test_fetch_called_for_each_item(
        self, db_session, registered_user, cart_with_multiple_items
    ):
        """fetch_single_product called once per cart item."""
        with patch(PATCH_PATH, new_callable=AsyncMock) as mock_fetch:
            mock_fetch.side_effect = [
                MOCK_EBAY_PRODUCT_1,
                MOCK_EBAY_PRODUCT_2
            ]
            await get_cart(db_session, registered_user)
            assert mock_fetch.call_count == 2

    @pytest.mark.asyncio
    async def test_fetch_called_with_correct_product_ids(
        self, db_session, registered_user, cart_with_multiple_items
    ):
        """fetch_single_product called with correct product IDs."""
        with patch(PATCH_PATH, new_callable=AsyncMock) as mock_fetch:
            mock_fetch.side_effect = [
                MOCK_EBAY_PRODUCT_1,
                MOCK_EBAY_PRODUCT_2
            ]
            await get_cart(db_session, registered_user)
            called_ids = {
                call[0][0] for call in mock_fetch.call_args_list
            }
            assert "v1|111|0" in called_ids
            assert "v1|222|0" in called_ids

    @pytest.mark.asyncio
    async def test_no_fetch_called_for_empty_cart(
        self, db_session, registered_user
    ):
        """fetch_single_product not called when cart is empty."""
        with patch(PATCH_PATH, new_callable=AsyncMock) as mock_fetch:
            await get_cart(db_session, registered_user)
            mock_fetch.assert_not_called()
            
# ==============================================================================
# Cart Not Found Tests
# ==============================================================================

class TestRemoveCartItemNoCart:

    def test_no_cart_raises_cart_not_found_error(
        self, db_session, registered_user
    ):
        """User with no cart raises CartNotFoundError."""
        with pytest.raises(CartNotFoundError):
            remove_cart_item(db_session, registered_user, "v1|123456|0")

    def test_no_cart_does_not_delete_anything(
        self, db_session, registered_user
    ):
        """No deletion happens when cart doesn't exist."""
        try:
            remove_cart_item(db_session, registered_user, "v1|123456|0")
        except CartNotFoundError:
            pass
        count = db_session.query(CartItem).count()
        assert count == 0


# ==============================================================================
# Cart Item Not Found Tests
# ==============================================================================

class TestRemoveCartItemNotFound:

    def test_missing_item_raises_cart_item_not_found_error(
        self, db_session, registered_user, user_cart
    ):
        """Cart exists but item not in cart raises CartItemNotFoundError."""
        with pytest.raises(CartItemNotFoundError):
            remove_cart_item(
                db_session, registered_user, "v1|nonexistent|0"
            )

    def test_wrong_product_id_raises_cart_item_not_found_error(
        self, db_session, registered_user, cart_with_item
    ):
        """Correct cart but wrong product_id raises CartItemNotFoundError."""
        with pytest.raises(CartItemNotFoundError):
            remove_cart_item(
                db_session, registered_user, "v1|wrong|0"
            )

    def test_missing_item_does_not_delete_other_items(
        self, db_session, registered_user, cart_with_multiple_items
    ):
        """Other items unaffected when target item not found."""
        try:
            remove_cart_item(
                db_session, registered_user, "v1|nonexistent|0"
            )
        except CartItemNotFoundError:
            pass
        count = db_session.query(CartItem).filter_by(
            cart_id=cart_with_multiple_items.id
        ).count()
        assert count == 2


# ==============================================================================
# Successful Removal Tests
# ==============================================================================

class TestRemoveCartItemSuccess:

    def test_removes_item_from_db(
        self, db_session, registered_user, cart_with_item
    ):
        """Item is deleted from DB on successful removal."""
        remove_cart_item(db_session, registered_user, "v1|123456|0")
        db_session.commit()

        deleted = db_session.execute(
            select(CartItem).where(
                CartItem.cart_id == cart_with_item.id,
                CartItem.product_id == "v1|123456|0"
            )
        ).scalar_one_or_none()
        assert deleted is None

    def test_returns_success_message(
        self, db_session, registered_user, cart_with_item
    ):
        """Returns correct success message on removal."""
        result = remove_cart_item(
            db_session, registered_user, "v1|123456|0"
        )
        assert result == {"message": "Item removed successfully"}

    def test_only_removes_target_item(
        self, db_session, registered_user, cart_with_multiple_items
    ):
        """Only the target item is removed, others remain."""
        remove_cart_item(
            db_session, registered_user, "v1|111|0"
        )
        db_session.commit()

        remaining = db_session.query(CartItem).filter_by(
            cart_id=cart_with_multiple_items.id
        ).all()
        assert len(remaining) == 1
        assert remaining[0].product_id == "v1|222|0"

    def test_cart_is_not_deleted_after_item_removal(
        self, db_session, registered_user, cart_with_item
    ):
        """Removing item does not delete the cart itself."""
        remove_cart_item(
            db_session, registered_user, "v1|123456|0"
        )
        db_session.commit()

        cart = db_session.query(Cart).filter_by(
            user_id=registered_user.id
        ).first()
        assert cart is not None

    def test_removing_all_items_leaves_empty_cart(
        self, db_session, registered_user, cart_with_item
    ):
        """Removing the last item leaves an empty cart."""
        remove_cart_item(
            db_session, registered_user, "v1|123456|0"
        )
        db_session.commit()

        items = db_session.query(CartItem).filter_by(
            cart_id=cart_with_item.id
        ).all()
        assert items == []

    def test_same_product_in_different_users_cart_unaffected(
        self, db_session, registered_user, cart_with_item
    ):
        """Removing item only affects the correct user's cart."""
        # Create second user with same product in their cart
        second_user = User(
            first_name="Jane",
            last_name="Doe",
            email="jane@example.com",
            password_hash=hash_password("Secret1234!"),
            provider="local"
        )
        db_session.add(second_user)
        db_session.commit()

        second_cart = Cart(user_id=second_user.id)
        db_session.add(second_cart)
        db_session.commit()

        second_item = CartItem(
            cart_id=second_cart.id,
            product_id="v1|123456|0",   # same product
            quantity=1
        )
        db_session.add(second_item)
        db_session.commit()

        # Remove from first user's cart only
        remove_cart_item(
            db_session, registered_user, "v1|123456|0"
        )
        db_session.commit()

        # Second user's item unaffected
        second_item_check = db_session.query(CartItem).filter_by(
            cart_id=second_cart.id,
            product_id="v1|123456|0"
        ).first()
        assert second_item_check is not None
        
# ==============================================================================
# Cart Not Found Tests
# ==============================================================================

class TestClearCartNotFound:

    def test_no_cart_raises_cart_not_found_error(
        self, db_session, registered_user
    ):
        """User with no cart raises CartNotFoundError."""
        with pytest.raises(CartNotFoundError):
            clear_cart(db_session, registered_user)

    def test_no_cart_does_not_delete_anything(
        self, db_session, registered_user
    ):
        """No deletion happens when cart doesn't exist."""
        try:
            clear_cart(db_session, registered_user)
        except CartNotFoundError:
            pass
        count = db_session.query(CartItem).count()
        assert count == 0


# ==============================================================================
# Successful Clear Tests
# ==============================================================================

class TestClearCartSuccess:

    def test_clears_all_items_from_cart(
        self, db_session, registered_user, cart_with_multiple_items
    ):
        """All items are removed from cart."""
        clear_cart(db_session, registered_user)
        db_session.commit()

        remaining = db_session.query(CartItem).filter_by(
            cart_id=cart_with_multiple_items.id
        ).all()
        assert remaining == []

    def test_returns_success_message(
        self, db_session, registered_user, cart_with_multiple_items
    ):
        """Returns correct success message."""
        result = clear_cart(db_session, registered_user)
        assert result == {"message": "Cart cleared successfully"}

    def test_cart_itself_not_deleted(
        self, db_session, registered_user, cart_with_multiple_items
    ):
        """Cart record remains after clearing items."""
        clear_cart(db_session, registered_user)
        db_session.commit()

        cart = db_session.query(Cart).filter_by(
            user_id=registered_user.id
        ).first()
        assert cart is not None

    def test_empty_cart_clears_successfully(
        self, db_session, registered_user, user_cart
    ):
        """Clearing an already empty cart returns success."""
        result = clear_cart(db_session, registered_user)
        assert result == {"message": "Cart cleared successfully"}

    def test_empty_cart_remains_empty(
        self, db_session, registered_user, user_cart
    ):
        """Clearing an empty cart leaves it empty."""
        clear_cart(db_session, registered_user)
        db_session.commit()

        items = db_session.query(CartItem).filter_by(
            cart_id=user_cart.id
        ).all()
        assert items == []

    def test_only_clears_correct_users_cart(
        self, db_session, registered_user, cart_with_multiple_items
    ):
        """Only the target user's cart is cleared."""
        # Create second user with their own cart and items
        second_user = User(
            first_name="Jane",
            last_name="Doe",
            email="jane@example.com",
            password_hash=hash_password("Secret1234!"),
            provider="local"
        )
        db_session.add(second_user)
        db_session.commit()

        second_cart = Cart(user_id=second_user.id)
        db_session.add(second_cart)
        db_session.commit()

        second_item = CartItem(
            cart_id=second_cart.id,
            product_id="v1|111|0",
            quantity=1
        )
        db_session.add(second_item)
        db_session.commit()

        # Clear first user's cart only
        clear_cart(db_session, registered_user)
        db_session.commit()

        # Second user's items unaffected
        second_items = db_session.query(CartItem).filter_by(
            cart_id=second_cart.id
        ).all()
        assert len(second_items) == 1

    def test_clears_all_items_not_just_first(
        self, db_session, registered_user, cart_with_multiple_items
    ):
        """All 3 items are removed, not just the first one."""
        count_before = db_session.query(CartItem).filter_by(
            cart_id=cart_with_multiple_items.id
        ).count()
        assert count_before == 2

        clear_cart(db_session, registered_user)
        db_session.commit()

        count_after = db_session.query(CartItem).filter_by(
            cart_id=cart_with_multiple_items.id
        ).count()
        assert count_after == 0