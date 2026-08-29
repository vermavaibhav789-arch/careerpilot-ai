"""
Auth: password hashing, JWT issuing/verification, and the FastAPI
dependency that protected routes use to identify the current user.

Password hashing uses bcrypt directly rather than through passlib - passlib
hasn't kept pace with recent bcrypt releases and its bcrypt backend has had
version-detection issues, so calling bcrypt directly is both simpler and
more reliable.
"""

from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.models.db_models import User

settings = get_settings()

# tokenUrl just tells FastAPI's auto-generated docs where to send the
# "Authorize" button's login request - it doesn't affect how tokens from
# elsewhere are validated.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


def create_access_token(user_id: str, token_version: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    payload = {"sub": user_id, "tv": token_version, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


_CREDENTIALS_ERROR = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials.",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    """FastAPI dependency: every protected route takes `current_user: User =
    Depends(get_current_user)` and gets a guaranteed-valid, guaranteed-real
    user - invalid/expired/tampered/revoked tokens never reach the route."""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        user_id = payload.get("sub")
        token_version = payload.get("tv")
        if user_id is None or token_version is None:
            raise _CREDENTIALS_ERROR
    except jwt.PyJWTError:
        raise _CREDENTIALS_ERROR

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise _CREDENTIALS_ERROR

    # Revocation check: if the user has logged out everywhere or reset their
    # password since this token was issued, token_version has moved on and
    # this token - even though it's a validly-signed, unexpired JWT - is
    # treated as revoked.
    if token_version != user.token_version:
        raise _CREDENTIALS_ERROR

    return user
