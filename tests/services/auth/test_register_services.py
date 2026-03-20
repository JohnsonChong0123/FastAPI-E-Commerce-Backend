# tests/services/test_register_services.py
import pytest
from exceptions.auth_exceptions import EmailAlreadyExistsError
from models.user_model import User
from services.auth.register_services import register
from schemas.auth.register_request import RegisterRequest


class TestRegisterService:

    VALID_DATA = RegisterRequest(
        first_name="John",
        last_name="Doe",
        email="john@example.com",
        password="Secret1234!"
    )

    def test_register_creates_user_in_db(self, db_session):
        """After registration, the user should exist in the database."""
        register(db_session, self.VALID_DATA)
        user = db_session.query(User).filter_by(email="john@example.com").first()
        assert user is not None

    def test_register_saves_correct_fields(self, db_session):
        """Registered user's fields should match the input data (except password which is hashed)."""
        register(db_session, self.VALID_DATA)
        user = db_session.query(User).filter_by(email="john@example.com").first()
        assert user.first_name == "John"
        assert user.last_name == "Doe"
        assert user.email == "john@example.com"

    def test_register_password_is_hashed(self, db_session):
        """Password should not be stored in plaintext; it should be hashed."""
        register(db_session, self.VALID_DATA)
        user = db_session.query(User).filter_by(email="john@example.com").first()
        assert user.password_hash != "Secret1234!"
        assert user.password_hash is not None

    def test_register_assigns_default_avatar(self, db_session):
        """New users should have a default avatar URL based on their email hash."""
        register(db_session, self.VALID_DATA)
        user = db_session.query(User).filter_by(email="john@example.com").first()
        assert "gravatar.com/avatar/" in user.avatar 
        assert user.image_url is None
        
    def test_register_returns_success_message(self, db_session):
        """Service should return a success message upon successful registration."""
        result = register(db_session, self.VALID_DATA)
        assert result == {"message": "User registered successfully"}

    def test_register_duplicate_email_raises_custom_exception(self, db_session):
        """Service raises EmailAlreadyExistsError, NOT HTTPException."""
        register(db_session, self.VALID_DATA)
        with pytest.raises(EmailAlreadyExistsError):
            register(db_session, self.VALID_DATA)

    def test_register_does_not_raise_http_exception(self, db_session):
        """Service layer is independent of FastAPI — no HTTPException raised."""
        from fastapi import HTTPException
        register(db_session, self.VALID_DATA)
        try:
            register(db_session, self.VALID_DATA)
        except HTTPException:
            pytest.fail("Service should not raise HTTPException directly")
        except EmailAlreadyExistsError:
            pass

    def test_register_without_phone_saves_none(self, db_session):
        """If phone is not provided, it should be saved as None in the database."""
        register(db_session, self.VALID_DATA)
        user = db_session.query(User).filter_by(email="john@example.com").first()
        assert user.phone is None

    def test_register_with_phone_saves_correctly(self, db_session):
        """If phone is provided, it should be saved correctly in the database."""
        data = RegisterRequest(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            password="Secret1234!",
            phone="0123456789"
        )
        register(db_session, data)
        user = db_session.query(User).filter_by(email="john@example.com").first()
        assert user.phone == "0123456789"