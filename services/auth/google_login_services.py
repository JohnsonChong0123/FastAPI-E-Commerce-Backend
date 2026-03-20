from models.user_model import User
from core.jwt import create_access_token, create_refresh_token
from services.google.google_auth import verify_google_token
from exceptions.auth_exceptions import (
    InvalidGoogleTokenError,
    AuthProviderMismatchError
)

def login_with_google(db, token):

    google_user = verify_google_token(token)

    if not google_user:
        raise InvalidGoogleTokenError()

    email = google_user["email"]
    name = google_user.get("name", "")

    user = db.query(User).filter(User.email == email).first()

    if user and user.provider != "google":
        raise AuthProviderMismatchError()

    if not user:
        user = User(
            email=email,
            first_name=name.split(" ")[0],
            last_name=" ".join(name.split(" ")[1:]),
            password_hash=None,
            image_url=google_user.get("picture"),
            provider="google",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    print(f"User {user.first_name} logged in with Google")
    print(f"Google user info: {user.last_name}")

    return {
        "access_token": create_access_token(user.id),
        "refresh_token": create_refresh_token(user.id),
        "provider": user.provider,
        "user": user
    }