# tests/models/test_user_model.py
import uuid
import pytest
from sqlalchemy.exc import IntegrityError
from models.cart_model import Cart
from models.cart_item_model import CartItem
from models.user_model import User


# ==============================================================================
# FIXTURES
# ==============================================================================

@pytest.fixture
def base() -> dict:
    """Minimal valid user payload."""
    return {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john@example.com",
    }


@pytest.fixture
def persisted_user(base, db_session) -> User:
    """A committed User row, ready for DB assertion tests."""
    user = User(**base, password_hash="hashed")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


# ==============================================================================
# INSTANTIATION
# ==============================================================================

class TestUserInstantiation:

    def test_basic_fields(self, base):
        """User can be created with required fields."""
        user = User(**base)
        assert user.first_name == base["first_name"]
        assert user.last_name == base["last_name"]
        assert user.email == base["email"]

    def test_tablename(self):
        """Model maps to the correct table."""
        assert User.__tablename__ == "users"

    @pytest.mark.parametrize("field", [
        "phone", "image_url", "address",
        "latitude", "longitude", "avatar_key", "password_hash",
    ])
    def test_optional_fields_default_to_none(self, base, field):
        """Nullable optional fields default to None."""
        assert getattr(User(**base), field) is None

    def test_all_fields_assignable(self, base):
        """All fields can be assigned without error."""
        user = User(
            **base,
            password_hash="hashed_password",
            phone="0123456789",
            image_url="https://example.com/avatar.jpg",
            wallet=100.00,
            provider="local",
            address="123 Main St",
            latitude=3.1390,
            longitude=101.6869,
            avatar_key="avatar-key-123",
        )
        assert user.phone == "0123456789"
        assert user.wallet == 100.00
        assert user.latitude == 3.1390
        assert user.longitude == 101.6869


# ==============================================================================
# AVATAR PROPERTY
# ==============================================================================

class TestAvatarProperty:

    def test_falls_back_to_gravatar_when_no_image(self, base):
        """If no image_url is set, avatar should return a Gravatar URL."""
        user = User(**base)
        assert "gravatar.com/avatar/" in user.avatar
        assert "d=mp" in user.avatar

    def test_returns_image_url_when_set(self, base):
        """If image_url is set, avatar should return that URL instead of Gravatar."""
        user = User(**base, image_url="https://my-site.com/photo.jpg")
        assert user.avatar == "https://my-site.com/photo.jpg"


# ==============================================================================
# OAUTH
# ==============================================================================

class TestOAuthUser:

    def test_password_hash_nullable_for_oauth_users(self, base):
        """Users created via OAuth providers may not have a password hash."""
        user = User(**base, provider="google", password_hash=None)
        assert user.password_hash is None
        assert user.provider == "google"


# ==============================================================================
# DB — PERSISTENCE & DEFAULTS
# ==============================================================================

class TestUserPersistence:

    def test_user_persists_and_is_retrievable(self, base, db_session):
        """A User can be added to the session, committed, and then queried back."""
        db_session.add(User(**base, password_hash="hashed"))
        db_session.commit()

        fetched = db_session.query(User).filter_by(email=base["email"]).first()
        assert fetched is not None
        assert fetched.first_name == base["first_name"]

    def test_id_is_uuid_after_commit(self, persisted_user):
        """Test that the user's ID is a UUID after being committed to the database."""
        assert isinstance(persisted_user.id, uuid.UUID)

    def test_created_at_auto_populated(self, persisted_user):
        """Test that the created_at timestamp is automatically set upon persistence."""
        assert persisted_user.created_at is not None

    def test_wallet_defaults_to_zero(self, persisted_user):
        """Test that the wallet field defaults to 0 if not explicitly set."""
        assert persisted_user.wallet == 0

    def test_defaults_resolved_after_flush(self, base, db_session):
        """Test that defaults like wallet and provider are set after flushing the session."""
        user = User(**base)
        assert user.id is None

        db_session.add(user)
        db_session.flush()

        assert isinstance(user.id, uuid.UUID)
        assert user.wallet == 0
        assert user.provider == "email"


# ==============================================================================
# DB — CONSTRAINTS
# ==============================================================================

class TestUserConstraints:

    @pytest.mark.parametrize("field", ["first_name", "last_name", "email"])
    def test_required_field_cannot_be_null(self, base, db_session, field):
        """Test that required fields cannot be null in the database."""
        del base[field]
        db_session.add(User(**base))
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_email_must_be_unique(self, base, db_session):
        """Test that the email field must be unique across users."""
        db_session.add(User(**base, password_hash="abc"))
        db_session.commit()

        db_session.add(User(**{**base, "first_name": "Jane"}, password_hash="xyz"))
        with pytest.raises(IntegrityError):
            db_session.commit()
            
# ==============================================================================
# RELATIONSHIPS — CART
# ==============================================================================

class TestUserCartRelationship:

    def test_user_can_have_a_cart(self, db_session, persisted_user):
        """Test that a User can be associated with a Cart and that the relationship is properly set up.""" 
        new_cart = Cart(user_id=persisted_user.id)
        db_session.add(new_cart)
        db_session.commit()
        
        db_session.refresh(persisted_user)
        assert persisted_user.cart is not None
        assert persisted_user.cart.id == new_cart.id
        assert new_cart.user == persisted_user

    def test_cascade_delete_user_removes_cart(self, db_session, persisted_user):
        """When a User is deleted, the associated Cart should also be deleted due to cascade settings."""
        cart = Cart(user=persisted_user)
        db_session.add(cart)
        db_session.commit()
        cart_id = cart.id

        db_session.delete(persisted_user)
        db_session.commit()

        remaining_cart = db_session.query(Cart).filter_by(id=cart_id).first()
        assert remaining_cart is None

    def test_delete_orphan_when_setting_none(self, db_session, persisted_user):
        """Test orphan deletion: when user.cart is set to None, the cart record should be deleted."""
        cart = Cart(user=persisted_user)
        db_session.add(cart)
        db_session.commit()

        persisted_user.cart = None
        db_session.commit()

        assert db_session.query(Cart).count() == 0