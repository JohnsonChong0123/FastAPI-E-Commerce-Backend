# tests/services/test_wishlist_services.py
import pytest
from unittest.mock import patch, AsyncMock
from sqlalchemy import select
from exceptions.product_exceptions import ProductNotFoundError
from exceptions.wishlist_exceptions import WishlistNotFoundError
from models.wishlist_model import Wishlist
from models.user_model import User
from core.security import hash_password
from services.wishlist.wishlist_services import (
    add_to_wishlist,
    get_wishlist,
    remove_wishlist,
    clear_wishlist,
)
from schemas.wishlist.wishlist_create import WishlistCreate


PATCH_PATH = "services.wishlist.wishlist_services.fetch_single_product"

MOCK_EBAY_PRODUCT = {
    "itemId": "v1|123456|0",
    "title": "Wireless Headphones",
    "price": {"value": "99.99"},
    "image": {"imageUrl": "https://example.com/img.jpg"}
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
def second_user(db_session):
    user = User(
        first_name="Jane",
        last_name="Doe",
        email="jane@example.com",
        password_hash=hash_password("Secret1234!"),
        provider="email"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def wishlist_item(db_session, registered_user):
    """Single wishlist item for registered user."""
    item = Wishlist(
        user_id=registered_user.id,
        product_id="v1|123456|0"
    )
    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)
    return item


@pytest.fixture
def wishlist_with_multiple_items(db_session, registered_user):
    """Multiple wishlist items for registered user."""
    items = [
        Wishlist(user_id=registered_user.id, product_id="v1|123456|0"),
        Wishlist(user_id=registered_user.id, product_id="v1|222|0"),
        Wishlist(user_id=registered_user.id, product_id="v1|333|0"),
    ]
    db_session.add_all(items)
    db_session.commit()
    return items


@pytest.fixture
def valid_payload():
    return WishlistCreate(product_id="v1|123456|0")


# ==============================================================================
# add_to_wishlist Tests
# ==============================================================================

class TestAddToWishlist:

    @pytest.mark.asyncio
    async def test_product_not_found_raises_error(
        self, db_session, registered_user, valid_payload
    ):
        """None from fetch_single_product raises ProductNotFoundError."""
        with patch(PATCH_PATH, new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = None
            with pytest.raises(ProductNotFoundError):
                await add_to_wishlist(db_session, registered_user, valid_payload)

    @pytest.mark.asyncio
    async def test_product_not_found_does_not_create_entry(
        self, db_session, registered_user, valid_payload
    ):
        """No wishlist entry created when product not found."""
        with patch(PATCH_PATH, new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = None
            try:
                await add_to_wishlist(
                    db_session, registered_user, valid_payload
                )
            except ProductNotFoundError:
                pass
            count = db_session.query(Wishlist).count()
            assert count == 0

    @pytest.mark.asyncio
    async def test_adds_new_item_to_wishlist(
        self, db_session, registered_user, valid_payload
    ):
        """New item is added to wishlist."""
        with patch(PATCH_PATH, new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = MOCK_EBAY_PRODUCT
            await add_to_wishlist(db_session, registered_user, valid_payload)
            db_session.commit()

            item = db_session.query(Wishlist).filter_by(
                user_id=registered_user.id,
                product_id="v1|123456|0"
            ).first()
            assert item is not None

    @pytest.mark.asyncio
    async def test_returns_success_message(
        self, db_session, registered_user, valid_payload
    ):
        """Returns correct success message."""
        with patch(PATCH_PATH, new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = MOCK_EBAY_PRODUCT
            result = await add_to_wishlist(
                db_session, registered_user, valid_payload
            )
            assert result == {"message": "Added to wishlist successfully"}

    @pytest.mark.asyncio
    async def test_does_not_duplicate_existing_item(
        self, db_session, registered_user, wishlist_item, valid_payload
    ):
        """Adding same product twice does not create duplicate."""
        with patch(PATCH_PATH, new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = MOCK_EBAY_PRODUCT
            await add_to_wishlist(db_session, registered_user, valid_payload)
            await add_to_wishlist(db_session, registered_user, valid_payload)
            db_session.commit()

            count = db_session.query(Wishlist).filter_by(
                user_id=registered_user.id,
                product_id="v1|123456|0"
            ).count()
            assert count == 1

    @pytest.mark.asyncio
    async def test_returns_success_even_if_already_in_wishlist(
        self, db_session, registered_user, wishlist_item, valid_payload
    ):
        """Returns success message even if item already wishlisted."""
        with patch(PATCH_PATH, new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = MOCK_EBAY_PRODUCT
            result = await add_to_wishlist(
                db_session, registered_user, valid_payload
            )
            assert result == {"message": "Added to wishlist successfully"}


# ==============================================================================
# get_wishlist Tests
# ==============================================================================

class TestGetWishlist:

    @pytest.mark.asyncio
    async def test_empty_wishlist_returns_empty_list(
        self, db_session, registered_user
    ):
        """
        Empty wishlist currently returns a dict — should return [].
        Documents the inconsistency gap.
        """
        result = await get_wishlist(db_session, registered_user)
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_returns_enriched_items(
        self, db_session, registered_user, wishlist_item
    ):
        """Returns items enriched with eBay product data."""
        with patch(PATCH_PATH, new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = MOCK_EBAY_PRODUCT
            result = await get_wishlist(db_session, registered_user)
            assert len(result) == 1
            assert result[0]["product_id"] == "v1|123456|0"
            assert result[0]["name"] == "Wireless Headphones"
            assert result[0]["price"] == 99.99

    @pytest.mark.asyncio
    async def test_returns_correct_item_fields(
        self, db_session, registered_user, wishlist_item
    ):
        """Each item contains all required fields."""
        with patch(PATCH_PATH, new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = MOCK_EBAY_PRODUCT
            result = await get_wishlist(db_session, registered_user)
            item = result[0]
            assert "id" in item
            assert "product_id" in item
            assert "name" in item
            assert "price" in item
            assert "image_url" in item

    @pytest.mark.asyncio
    async def test_skips_items_with_missing_ebay_product(
        self, db_session, registered_user, wishlist_with_multiple_items
    ):
        """Items with no eBay product are skipped."""
        with patch(PATCH_PATH, new_callable=AsyncMock) as mock_fetch:
            mock_fetch.side_effect = [
                MOCK_EBAY_PRODUCT,
                None,             # second product not found
                MOCK_EBAY_PRODUCT_2
            ]
            result = await get_wishlist(db_session, registered_user)
            assert len(result) == 2

    @pytest.mark.asyncio
    async def test_fetch_called_for_each_item(
        self, db_session, registered_user, wishlist_with_multiple_items
    ):
        """fetch_single_product called once per wishlist item."""
        with patch(PATCH_PATH, new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = MOCK_EBAY_PRODUCT
            await get_wishlist(db_session, registered_user)
            assert mock_fetch.call_count == 3

    @pytest.mark.asyncio
    async def test_all_products_missing_returns_empty_list(
        self, db_session, registered_user, wishlist_with_multiple_items
    ):
        """All products missing returns empty list."""
        with patch(PATCH_PATH, new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = None
            result = await get_wishlist(db_session, registered_user)
            assert result == []


# ==============================================================================
# remove_wishlist Tests
# ==============================================================================

class TestRemoveWishlist:

    def test_item_not_found_raises_error(
        self, db_session, registered_user
    ):
        """Missing wishlist item raises WishlistNotFoundError."""
        with pytest.raises(WishlistNotFoundError):
            remove_wishlist(
                db_session, registered_user, "v1|nonexistent|0"
            )

    def test_removes_item_from_db(
        self, db_session, registered_user, wishlist_item
    ):
        """Item is deleted from DB."""
        remove_wishlist(db_session, registered_user, "v1|123456|0")
        db_session.commit()

        deleted = db_session.query(Wishlist).filter_by(
            user_id=registered_user.id,
            product_id="v1|123456|0"
        ).first()
        assert deleted is None

    def test_returns_success_message(
        self, db_session, registered_user, wishlist_item
    ):
        """Returns correct success message."""
        result = remove_wishlist(
            db_session, registered_user, "v1|123456|0"
        )
        assert result == {"message": "Wishlist removed successfully"}

    def test_only_removes_target_item(
        self, db_session, registered_user, wishlist_with_multiple_items
    ):
        """Only target item removed, others remain."""
        remove_wishlist(db_session, registered_user, "v1|222|0")
        db_session.commit()

        remaining = db_session.query(Wishlist).filter_by(
            user_id=registered_user.id
        ).all()
        assert len(remaining) == 2
        product_ids = {w.product_id for w in remaining}
        assert "v1|111|0" not in product_ids

    def test_does_not_affect_other_users_wishlist(
        self, db_session, registered_user, second_user, wishlist_item
    ):
        """Removing item only affects correct user's wishlist."""
        second_item = Wishlist(
            user_id=second_user.id,
            product_id="v1|123456|0"
        )
        db_session.add(second_item)
        db_session.commit()

        remove_wishlist(db_session, registered_user, "v1|123456|0")
        db_session.commit()

        second_check = db_session.query(Wishlist).filter_by(
            user_id=second_user.id,
            product_id="v1|123456|0"
        ).first()
        assert second_check is not None


# ==============================================================================
# clear_wishlist Tests
# ==============================================================================

class TestClearWishlist:

    def test_no_wishlist_raises_error(
        self, db_session, registered_user
    ):
        """User with no wishlist entries raises WishlistNotFoundError."""
        with pytest.raises(WishlistNotFoundError):
            clear_wishlist(db_session, registered_user)

    def test_returns_success_message(
        self, db_session, registered_user, wishlist_item
    ):
        """Returns correct success message."""
        result = clear_wishlist(db_session, registered_user)
        assert result == {"message": "Wishlist cleared successfully"}

    def test_clears_only_one_item_bug(
        self, db_session, registered_user, wishlist_with_multiple_items
    ):
        clear_wishlist(db_session, registered_user)
        db_session.commit()

        remaining = db_session.query(Wishlist).filter_by(
            user_id=registered_user.id
        ).all()
        assert len(remaining) == 0   

    def test_only_clears_correct_users_wishlist(
        self, db_session, registered_user, second_user, wishlist_item
    ):
        """Only target user's wishlist is cleared."""
        second_item = Wishlist(
            user_id=second_user.id,
            product_id="v1|123456|0"
        )
        db_session.add(second_item)
        db_session.commit()

        clear_wishlist(db_session, registered_user)
        db_session.commit()

        second_check = db_session.query(Wishlist).filter_by(
            user_id=second_user.id
        ).first()
        assert second_check is not None