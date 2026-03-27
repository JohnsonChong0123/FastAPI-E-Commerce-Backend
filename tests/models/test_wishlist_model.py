# tests/models/test_wishlist_model.py
import uuid
import pytest
from sqlalchemy.exc import IntegrityError
from models.wishlist_model import Wishlist
from models.user_model import User
from core.security import hash_password
from tests.conftest import db_session


# ==============================================================================
# FIXTURES
# ==============================================================================

def make_user(db_session, email="john@example.com"):
    """Helper — creates and persists a user."""
    user = User(
        first_name="John",
        last_name="Doe",
        email=email,
        password_hash=hash_password("Secret1234!"),
        provider="email"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


# ==============================================================================
# Unit Tests (No DB)
# ==============================================================================

class TestWishlistModelInstantiation:

    def test_basic_instantiation(self):
        """Wishlist can be instantiated with required fields."""
        wishlist = Wishlist(
            user_id=uuid.uuid4(),
            product_id="v1|123456|0"
        )
        assert wishlist.product_id == "v1|123456|0"

    def test_uuid_auto_generated(self):
        """Wishlist ID is auto-generated as a valid UUID."""
        wishlist = Wishlist(
            user_id=uuid.uuid4(),
            product_id="v1|123456|0"
        )
        assert wishlist.id is not None
        assert isinstance(wishlist.id, uuid.UUID)

    def test_uuid_unique_per_instance(self):
        """Each Wishlist instance gets a different UUID."""
        wishlist1 = Wishlist(user_id=uuid.uuid4(), product_id="v1|111|0")
        wishlist2 = Wishlist(user_id=uuid.uuid4(), product_id="v1|222|0")
        assert wishlist1.id != wishlist2.id

    def test_tablename(self):
        """Model maps to correct table name."""
        assert Wishlist.__tablename__ == "wishlists"


# ==============================================================================
# Integration Tests (With DB)
# ==============================================================================

class TestWishlistModelConstraints:

    def test_wishlist_persists_to_db(self, db_session):
        """Wishlist entry is saved and retrieved from DB."""
        user = make_user(db_session)
        wishlist = Wishlist(
            user_id=user.id,
            product_id="v1|123456|0"
        )
        db_session.add(wishlist)
        db_session.commit()

        fetched = db_session.query(Wishlist).filter_by(
            user_id=user.id
        ).first()
        assert fetched is not None
        assert fetched.product_id == "v1|123456|0"

    def test_user_id_cannot_be_null(self, db_session):
        """Wishlist without user_id raises IntegrityError."""
        wishlist = Wishlist(product_id="v1|123456|0")
        db_session.add(wishlist)
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_product_id_cannot_be_null(self, db_session):
        """Wishlist without product_id raises IntegrityError."""
        user = make_user(db_session)
        wishlist = Wishlist(user_id=user.id)
        db_session.add(wishlist)
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_user_id_must_reference_existing_user(self, db_session):
        """Wishlist with non-existent user_id raises IntegrityError."""
        wishlist = Wishlist(
            user_id=uuid.uuid4(),
            product_id="v1|123456|0"
        )
        db_session.add(wishlist)
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_different_users_can_wishlist_same_product(self, db_session):
        """Different users can wishlist the same product."""
        user1 = make_user(db_session, email="john@example.com")
        user2 = make_user(db_session, email="jane@example.com")

        wishlist1 = Wishlist(user_id=user1.id, product_id="v1|123456|0")
        wishlist2 = Wishlist(user_id=user2.id, product_id="v1|123456|0")
        db_session.add_all([wishlist1, wishlist2])
        db_session.commit()

        count = db_session.query(Wishlist).filter_by(
            product_id="v1|123456|0"
        ).count()
        assert count == 2


# ==============================================================================
# Relationship Tests
# ==============================================================================

class TestWishlistModelRelationships:

    def test_wishlist_belongs_to_user(self, db_session):
        """Wishlist.user returns the correct User object."""
        user = make_user(db_session)
        wishlist = Wishlist(user_id=user.id, product_id="v1|123456|0")
        db_session.add(wishlist)
        db_session.commit()
        db_session.refresh(wishlist)
        assert wishlist.user.email == "john@example.com"

    def test_user_wishlist_relationship_populated(self, db_session):
        """User.wishlist returns the correct Wishlist entries."""
        user = make_user(db_session)
        wishlist = Wishlist(user_id=user.id, product_id="v1|123456|0")
        db_session.add(wishlist)
        db_session.commit()
        db_session.refresh(user)
        assert len(user.wishlist) == 1
        assert user.wishlist[0].product_id == "v1|123456|0"

    def test_deleting_user_cascades_to_wishlist(self, db_session):
        """Deleting a user removes their wishlist entries."""
        user = make_user(db_session)
        wishlist = Wishlist(user_id=user.id, product_id="v1|123456|0")
        db_session.add(wishlist)
        db_session.commit()
        wishlist_id = wishlist.id

        db_session.delete(user)
        db_session.commit()

        deleted = db_session.query(Wishlist).filter_by(
            id=wishlist_id
        ).first()
        assert deleted is None

    def test_deleting_wishlist_does_not_delete_user(self, db_session):
        """Deleting a wishlist entry does not delete the user."""
        user = make_user(db_session)
        wishlist = Wishlist(user_id=user.id, product_id="v1|123456|0")
        db_session.add(wishlist)
        db_session.commit()

        db_session.delete(wishlist)
        db_session.commit()

        user_check = db_session.query(User).filter_by(
            id=user.id
        ).first()
        assert user_check is not None