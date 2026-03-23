# tests/models/test_cart_model.py
import uuid
import pytest
from sqlalchemy.exc import IntegrityError
from models.cart_model import Cart
from models.user_model import User
from models.cart_item_model import CartItem
from core.security import hash_password


# ==============================================================================
# FIXTURES
# ==============================================================================
@pytest.fixture
def second_user(db_session):
    """Creates a second user in the test DB."""
    user = User(
        first_name="Jane",
        last_name="Doe",
        email="jane@example.com",
        password_hash=hash_password("Secret1234!"),
        provider="local"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


# ==============================================================================
# Unit Tests (No DB)
# ==============================================================================

class TestCartModelInstantiation:

    def test_cart_instantiation(self):
        """Cart can be instantiated with required fields."""
        cart = Cart(user_id=uuid.uuid4())
        assert cart.user_id is not None

    def test_cart_id_auto_generated(self):
        """Cart ID can be assigned a valid UUID."""
        custom_id = uuid.uuid4()
        cart = Cart(id=custom_id, user_id=uuid.uuid4())
        assert cart.id == custom_id

    def test_cart_uuid_is_unique_per_instance(self):
        """Each Cart instance can hold different UUIDs."""
        id1 = uuid.uuid4()
        id2 = uuid.uuid4()
        cart1 = Cart(id=id1, user_id=uuid.uuid4())
        cart2 = Cart(id=id2, user_id=uuid.uuid4())
        assert cart1.id != cart2.id

    def test_tablename(self):
        """Model maps to correct table name."""
        assert Cart.__tablename__ == "carts"


# ==============================================================================
# Integration Tests (With DB)
# ==============================================================================

class TestCartModelConstraints:

    def test_cart_persists_to_db(self, db_session, registered_user):
        """Cart is saved and retrieved from DB correctly."""
        cart = Cart(user_id=registered_user.id)
        db_session.add(cart)
        db_session.commit()

        fetched = db_session.query(Cart).filter_by(
            user_id=registered_user.id
        ).first()
        assert fetched is not None
        assert fetched.user_id == registered_user.id

    def test_created_at_auto_populated(self, db_session, registered_user):
        """created_at is automatically set by DB on insert."""
        cart = Cart(user_id=registered_user.id)
        db_session.add(cart)
        db_session.commit()
        db_session.refresh(cart)
        assert cart.created_at is not None

    def test_user_id_cannot_be_null(self, db_session):
        """Cart without user_id raises IntegrityError."""
        cart = Cart()
        db_session.add(cart)
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_user_id_must_be_unique(self, db_session, registered_user):
        """One user cannot have two carts."""
        cart1 = Cart(user_id=registered_user.id)
        cart2 = Cart(user_id=registered_user.id)
        db_session.add(cart1)
        db_session.commit()
        db_session.add(cart2)
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_different_users_can_have_separate_carts(
        self, db_session, registered_user, second_user
    ):
        """Each user can have their own cart."""
        cart1 = Cart(user_id=registered_user.id)
        cart2 = Cart(user_id=second_user.id)
        db_session.add_all([cart1, cart2])
        db_session.commit()

        count = db_session.query(Cart).count()
        assert count == 2

    def test_user_id_must_reference_existing_user(self, db_session):
        """Cart with non-existent user_id raises IntegrityError."""
        cart = Cart(user_id=uuid.uuid4())   # non-existent user
        db_session.add(cart)
        with pytest.raises(IntegrityError):
            db_session.commit()


# ==============================================================================
# Relationship Tests
# ==============================================================================

class TestCartModelRelationships:

    def test_cart_belongs_to_user(self, db_session, registered_user):
        """Cart.user returns the correct User object."""
        cart = Cart(user_id=registered_user.id)
        db_session.add(cart)
        db_session.commit()
        db_session.refresh(cart)
        assert cart.user.email == "john@example.com"

    def test_user_has_one_cart(self, db_session, registered_user):
        """User.cart returns the correct Cart (uselist=False)."""
        cart = Cart(user_id=registered_user.id)
        db_session.add(cart)
        db_session.commit()
        db_session.refresh(registered_user)
        assert registered_user.cart is not None
        assert registered_user.cart.id == cart.id

    def test_cart_items_defaults_to_empty_list(self, db_session, registered_user):
        """New cart has no items."""
        cart = Cart(user_id=registered_user.id)
        db_session.add(cart)
        db_session.commit()
        db_session.refresh(cart)
        assert cart.items == []

    def test_deleting_cart_cascades_to_items(self, db_session, registered_user):
        """
        Deleting a cart removes all its items (cascade).
        Full cascade test requires CartItem model — documents
        the expected behaviour for when CartItem is tested.
        """
        cart = Cart(user_id=registered_user.id)
        db_session.add(cart)
        db_session.commit()

        db_session.delete(cart)
        db_session.commit()

        deleted = db_session.query(Cart).filter_by(
            user_id=registered_user.id
        ).first()
        assert deleted is None

    def test_deleting_user_cascades_to_cart(self, db_session, registered_user):
        """Deleting a user removes their cart (User cascade)."""
        cart = Cart(user_id=registered_user.id)
        db_session.add(cart)
        db_session.commit()

        db_session.delete(registered_user)
        db_session.commit()

        deleted = db_session.query(Cart).filter_by(
            user_id=registered_user.id
        ).first()
        assert deleted is None