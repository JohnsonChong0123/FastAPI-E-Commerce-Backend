from core import jwt
from exceptions.auth_exceptions import RefreshTokenError, UserNotFoundError
from models.user_model import User

def refresh_token(data, db):
    try:
        payload = jwt.decode_token(data.refresh_token)

        if payload.get("type") != "refresh":
            raise RefreshTokenError()

        user_id = payload.get("sub")

    except Exception:
        raise RefreshTokenError()

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise UserNotFoundError()

    access_token = jwt.create_access_token(user.id)

    return {
        "access_token": access_token
    }