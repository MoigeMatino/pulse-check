from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select

from app.api.v1.models import APIKey, User
from app.api.v1.schemas import APIKeyResponse, UserCreate, UserRead
from app.auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
    create_access_token,
    create_refresh_token,
    get_current_user,
    get_password_hash,
    revoke_refresh_token,
    verify_password,
    verify_refresh_token,
)
from app.dependencies.db import get_db
from app.utils.crud import get_user_by_email

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register_user(user: UserCreate, db: Session = Depends(get_db)) -> UserRead:
    user_email = get_user_by_email(db, user.email)
    if user_email:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = get_password_hash(user.password)
    new_user = User(
        email=user.email,
        password_hash=hashed_password,
        slack_webhook=user.slack_webhook,
        phone_number=user.phone_number,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.post("/login")
def login_user(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> dict:
    user = db.exec(select(User).where(User.email == form_data.username)).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(db, user_id=user.id)
    # Set refresh token in HttpOnly cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=int(timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS).total_seconds()),
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/logout")
def logout(
    response: Response,
    refresh_token: str = Cookie(None, alias="refresh_token"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    if refresh_token:
        revoke_refresh_token(db, refresh_token)

    response.delete_cookie(
        key="refresh_token",
        httponly=True,
        secure=True,
        samesite="strict",
    )
    return {"message": "Logged out successfully"}


@router.post("/refresh")
def refresh_token(
    refresh_token: str = Cookie(None, alias="refresh_token"),
    db: Session = Depends(get_db),
):
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing",
        )

    user_id = verify_refresh_token(db, refresh_token)
    access_token = create_access_token(
        data={"sub": str(user_id)},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/api-keys", response_model=APIKeyResponse)
async def generate_api_key(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> APIKeyResponse:
    """
    Generate a new API key for the authenticated user
    """
    # ? Maybe think of hashing this api key in future
    api_key = str(uuid4())  # Generate unique key
    expires_at = datetime.now(timezone.utc) + timedelta(days=365)  # 1-year expiration
    key = APIKey(
        key=api_key,
        owner=user.id,
        is_active=True,
        created_at=datetime.now(timezone.utc),
        expires_at=expires_at,
    )
    db.add(key)
    db.commit()
    db.refresh(key)
    return key
