# services/auth_services.py

from models.user_model import User
from core.security import hash_password
from exceptions.auth_exceptions import EmailAlreadyExistsError

def register(db, data):
    existing = db.query(User).filter(User.email == data.email).first()

    if existing:
        raise EmailAlreadyExistsError()

    user = User(
        first_name=data.first_name,
        last_name=data.last_name,
        email=data.email,
        password_hash=hash_password(data.password),
        phone=data.phone,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return {"message": "User registered successfully"}


