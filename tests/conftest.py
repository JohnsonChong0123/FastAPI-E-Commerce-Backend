# tests/conftest.py
import os

import bcrypt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.security import hash_password
from main import app
from database import get_db
from models.base import Base
from core.config import settings
from models.user_model import User

TEST_DATABASE_URL = settings.TEST_DATABASE_URL

engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Create all tables before tests, drop after."""
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)
    
@pytest.fixture(scope="function")
def db_session():
    """Transactional session — rolls back after each test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    if transaction.is_active:
        transaction.rollback()
    connection.close()

@pytest.fixture(scope="function")
def client(db_session):
    """Test client with DB override."""
    def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
    
@pytest.fixture
def registered_user(db_session):
    """Creates a real user with Argon2 hashed password."""
    user = User(
        first_name="John",
        last_name="Doe",
        email="john@example.com",
        password_hash=hash_password("Secret1234!"),
        provider="email"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def legacy_user(db_session):
    """Creates a user with a legacy Bcrypt hashed password."""
    legacy_hash = bcrypt.hashpw(
        "Secret1234!".encode(), bcrypt.gensalt()
    ).decode()
    user = User(
        first_name="Jane",
        last_name="Doe",
        email="jane@example.com",
        password_hash=legacy_hash,
        provider="email"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user