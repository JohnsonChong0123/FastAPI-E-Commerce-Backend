from models.user_model import User
from services.facebook.facebook_auth import verify_facebook_token
from core.jwt import create_access_token, create_refresh_token
from exceptions.auth_exceptions import (
    InvalidFacebookTokenError,
    AuthProviderMismatchError
)

def login_with_facebook(db, token):
    fb_user = verify_facebook_token(token)

    if not fb_user:
        raise InvalidFacebookTokenError()

    email = fb_user.get("email")
    name = fb_user.get("name", "")
    # facebook_id = fb_user["id"]
    
    if not email:                               
        raise InvalidFacebookTokenError()

    user = None

    if email:
        user = db.query(User).filter(User.email == email).first()

    if user and user.provider != "facebook":
        raise AuthProviderMismatchError()

    if not user:
        names = name.split(" ")
        first_name = names[0]
        last_name = " ".join(names[1:]) if len(names) > 1 else ""

        user = User(
            email=email,
            first_name=first_name,
            last_name=last_name,
            provider="facebook",
            # facebook_id=fb_user["id"]
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    return {
        "access_token": create_access_token(user.id),
        "refresh_token": create_refresh_token(user.id),
        "user": user,
        "provider": user.provider,
    }