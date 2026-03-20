# core/jwt.py
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError, ExpiredSignatureError
from core.config import settings
from exceptions.auth_exceptions import InvalidTokenError, TokenExpiredError

TOKEN_SECRET_KEY = settings.TOKEN_SECRET_KEY
ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7


def create_token(user_id: str, token_type: str, expires_delta: int):
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_delta)
    payload = {
        "sub": str(user_id),
        "type": token_type,
        "exp": expire
    }
    return jwt.encode(payload, TOKEN_SECRET_KEY, algorithm=ALGORITHM)


def create_access_token(user_id: str):
    return create_token(user_id, "access", ACCESS_TOKEN_EXPIRE_MINUTES)


def create_refresh_token(user_id: str):
    return create_token(user_id, "refresh", REFRESH_TOKEN_EXPIRE_MINUTES)


def decode_token(token: str):
    try:
        payload = jwt.decode(token, TOKEN_SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except ExpiredSignatureError:
        raise TokenExpiredError()
    except JWTError:
        raise InvalidTokenError()