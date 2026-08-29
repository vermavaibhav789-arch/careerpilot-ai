import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.auth import create_access_token, get_current_user, hash_password, verify_password
from app.db import get_db
from app.models.db_models import User
from app.models.schemas import (
    ForgotPasswordRequest,
    MessageResponse,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserResponse,
)
from app.rate_limit import rate_limit
from app.services import email_client

router = APIRouter(prefix="/api/auth", tags=["auth"])

VERIFICATION_TOKEN_HOURS = 24
RESET_TOKEN_HOURS = 1


@router.post("/register", response_model=TokenResponse, dependencies=[Depends(rate_limit(10, 60))])
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == req.email).first()
    if existing is not None:
        raise HTTPException(
            status_code=400, detail="An account with this email already exists."
        )

    verification_token = secrets.token_urlsafe(32)
    user = User(
        email=req.email,
        hashed_password=hash_password(req.password),
        verification_token=verification_token,
        verification_token_expires=datetime.now(timezone.utc)
        + timedelta(hours=VERIFICATION_TOKEN_HOURS),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    email_client.send_verification_email(user.email, verification_token)

    token = create_access_token(user.id, user.token_version)
    return TokenResponse(access_token=token, email=user.email)


@router.post("/login", response_model=TokenResponse, dependencies=[Depends(rate_limit(10, 60))])
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # OAuth2PasswordRequestForm names the field "username" - we treat it as
    # the email. This is what gets us the free "Authorize" button in the
    # /docs UI, which is worth the slightly odd field name.
    user = db.query(User).filter(User.email == form_data.username).first()
    if user is None or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password.")

    token = create_access_token(user.id, user.token_version)
    return TokenResponse(access_token=token, email=user.email)


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return UserResponse(id=current_user.id, email=current_user.email)


@router.post("/logout-everywhere", response_model=MessageResponse)
def logout_everywhere(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    Invalidate every token issued for this account, including the one used
    to call this endpoint - the current session ends too, same as any other.
    """
    current_user.token_version += 1
    db.add(current_user)
    db.commit()
    return MessageResponse(message="Logged out of all sessions.")


@router.get("/verify-email", response_model=MessageResponse)
def verify_email(token: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.verification_token == token).first()
    if user is None:
        raise HTTPException(status_code=400, detail="Invalid or already-used verification link.")

    expires = user.verification_token_expires
    if expires is not None and expires.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="This verification link has expired.")

    user.email_verified = True
    user.verification_token = None
    user.verification_token_expires = None
    db.add(user)
    db.commit()
    return MessageResponse(message="Email verified.")


@router.post("/resend-verification", response_model=MessageResponse)
def resend_verification(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    if current_user.email_verified:
        return MessageResponse(message="Already verified.")

    token = secrets.token_urlsafe(32)
    current_user.verification_token = token
    current_user.verification_token_expires = datetime.now(timezone.utc) + timedelta(
        hours=VERIFICATION_TOKEN_HOURS
    )
    db.add(current_user)
    db.commit()

    email_client.send_verification_email(current_user.email, token)
    return MessageResponse(message="Verification email sent.")


@router.post(
    "/forgot-password", response_model=MessageResponse, dependencies=[Depends(rate_limit(5, 60))]
)
def forgot_password(req: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()

    # Always return the same response whether or not the email exists -
    # otherwise this endpoint becomes a way to check who has an account.
    generic_response = MessageResponse(
        message="If an account exists for that email, a reset link has been sent."
    )
    if user is None:
        return generic_response

    token = secrets.token_urlsafe(32)
    user.reset_token = token
    user.reset_token_expires = datetime.now(timezone.utc) + timedelta(hours=RESET_TOKEN_HOURS)
    db.add(user)
    db.commit()

    email_client.send_password_reset_email(user.email, token)
    return generic_response


@router.post("/reset-password", response_model=MessageResponse)
def reset_password(req: ResetPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.reset_token == req.token).first()
    if user is None:
        raise HTTPException(status_code=400, detail="Invalid or already-used reset link.")

    expires = user.reset_token_expires
    if expires is not None and expires.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="This reset link has expired.")

    user.hashed_password = hash_password(req.new_password)
    user.reset_token = None
    user.reset_token_expires = None
    # A password reset should also kill any sessions started with the old
    # password - e.g. on a device that stole/guessed it.
    user.token_version += 1
    db.add(user)
    db.commit()

    return MessageResponse(message="Password reset. Please log in with your new password.")
