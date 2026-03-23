# tests/models/test_cart_item_model.py
import uuid
import pytest
from sqlalchemy.exc import IntegrityError
from models.cart_model import Cart
from models.cart_item_model import CartItem
from models.user_model import User
from core.security import hash_password


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


# ==============================================================================
# Unit Tests (No DB)
# ==============================================================================

class TestCartItemModelInstantiation:

    def test_cart_item_instantiation(self):
        """CartItem can be instantiated with required fields."""
        item = CartItem(
            cart_id=uuid.uuid4(),
            product_id="ebay-item-001"
        )
        assert item.product_id == "ebay-item-001"

    def test_quantity_defaults_to_one(self):
        """Quantity defaults to 1 when not provided."""
        item = CartItem(
            cart_id=uuid.uuid4(),
            product_id="ebay-item-001"
        )
        assert item.quantity == 1

    def test_quantity_can_be_set(self):
        """Quantity can be set to any positive integer."""
        item = CartItem(
            cart_id=uuid.uuid4(),
            product_id="ebay-item-001",
            quantity=5
        )
        assert item.quantity == 5

    def test_tablename(self):
        """Model maps to correct table name."""
        assert CartItem.__tablename__ == "cart_items"

    def test_id_is_integer_type(self):
        """
        Documents that id is Integer, not UUID.
        Inconsistent with Cart and User — consider UUID for consistency.
        """
        from sqlalchemy import Integer
        id_col = CartItem.__table__.columns["id"]
        assert isinstance(id_col.type, Integer)


# ==============================================================================
# Integration Tests (With DB)
# ==============================================================================

class TestCartItemModelConstraints:

    def test_cart_item_persists_to_db(self, db_session, user_cart):
        """CartItem is saved and retrieved from DB correctly."""
        item = CartItem(
            cart_id=user_cart.id,
            product_id="ebay-item-001",
            quantity=2
        )
        db_session.add(item)
        db_session.commit()

        fetched = db_session.query(CartItem).filter_by(
            cart_id=user_cart.id
        ).first()
        assert fetched is not None
        assert fetched.product_id == "ebay-item-001"
        assert fetched.quantity == 2

    def test_cart_id_cannot_be_null(self, db_session):
        """CartItem without cart_id raises IntegrityError."""
        item = CartItem(product_id="ebay-item-001")
        db_session.add(item)
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_product_id_cannot_be_null(self, db_session, user_cart):
        """CartItem without product_id raises IntegrityError."""
        item = CartItem(cart_id=user_cart.id)
        db_session.add(item)
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_cart_id_must_reference_existing_cart(self, db_session):
        """CartItem with non-existent cart_id raises IntegrityError."""
        item = CartItem(
            cart_id=uuid.uuid4(),
            product_id="ebay-item-001"
        )
        db_session.add(item)
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_quantity_defaults_to_one_in_db(self, db_session, user_cart):
        """Quantity defaults to 1 in DB when not provided."""
        item = CartItem(
            cart_id=user_cart.id,
            product_id="ebay-item-001"
        )
        db_session.add(item)
        db_session.commit()
        db_session.refresh(item)
        assert item.quantity == 1

    def test_id_is_auto_incremented(self, db_session, user_cart):
        """ID is auto-incremented integer."""
        item1 = CartItem(cart_id=user_cart.id, product_id="ebay-item-001")
        item2 = CartItem(cart_id=user_cart.id, product_id="ebay-item-002")
        db_session.add_all([item1, item2])
        db_session.commit()
        db_session.refresh(item1)
        db_session.refresh(item2)
        assert item2.id > item1.id

    def test_same_cart_can_have_multiple_items(self, db_session, user_cart):
        """One cart can have multiple cart items."""
        item1 = CartItem(cart_id=user_cart.id, product_id="ebay-item-001")
        item2 = CartItem(cart_id=user_cart.id, product_id="ebay-item-002")
        item3 = CartItem(cart_id=user_cart.id, product_id="ebay-item-003")
        db_session.add_all([item1, item2, item3])
        db_session.commit()

        count = db_session.query(CartItem).filter_by(
            cart_id=user_cart.id
        ).count()
        assert count == 3


# ==============================================================================
# Relationship Tests
# ==============================================================================

class TestCartItemModelRelationships:

    def test_cart_item_belongs_to_cart(self, db_session, user_cart):
        """CartItem.cart returns the correct Cart object."""
        item = CartItem(
            cart_id=user_cart.id,
            product_id="ebay-item-001"
        )
        db_session.add(item)
        db_session.commit()
        db_session.refresh(item)
        assert item.cart.id == user_cart.id

    def test_cart_items_relationship_populated(self, db_session, user_cart):
        """Cart.items returns all CartItems for that cart."""
        item1 = CartItem(cart_id=user_cart.id, product_id="ebay-item-001")
        item2 = CartItem(cart_id=user_cart.id, product_id="ebay-item-002")
        db_session.add_all([item1, item2])
        db_session.commit()
        db_session.refresh(user_cart)
        assert len(user_cart.items) == 2

    def test_deleting_cart_cascades_to_items(self, db_session, user_cart):
        """Deleting a cart removes all its CartItems."""
        item1 = CartItem(cart_id=user_cart.id, product_id="ebay-item-001")
        item2 = CartItem(cart_id=user_cart.id, product_id="ebay-item-002")
        db_session.add_all([item1, item2])
        db_session.commit()

        db_session.delete(user_cart)
        db_session.commit()

        remaining = db_session.query(CartItem).filter_by(
            cart_id=user_cart.id
        ).all()
        assert remaining == []

    def test_deleting_user_cascades_to_cart_and_items(
        self, db_session, registered_user, user_cart
    ):
        """Deleting user cascades through cart to cart items."""
        item = CartItem(
            cart_id=user_cart.id,
            product_id="ebay-item-001"
        )
        db_session.add(item)
        db_session.commit()
        item_id = item.id

        db_session.delete(registered_user)
        db_session.commit()

        deleted_item = db_session.query(CartItem).filter_by(
            id=item_id
        ).first()
        assert deleted_item is None