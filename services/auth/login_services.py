# services/auth/login_services.py
from core.jwt import create_access_token, create_refresh_token
from models.user_model import User
from core.security import hash_password, needs_upgrade
from core.security import verify_password
from exceptions.auth_exceptions import InvalidCredentialsError

def login(db, data):
    user = db.query(User).filter(User.email == data.email).first()

    if not user or not verify_password(data.password, user.password_hash):
        raise InvalidCredentialsError()
    
    # Check if the password hash needs to be upgraded (e.g., from Bcrypt to Argon2) and update it if necessary.
    if needs_upgrade(user.password_hash):
        user.password_hash = hash_password(data.password)
        db.add(user)
        db.commit()

    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "provider": user.provider,
        "user": user
    }