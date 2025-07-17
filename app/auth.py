from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID, uuid4

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from passlib.context import CryptContext
from sqlmodel import Session, select

from app.api.v1.models import APIKey, RefreshToken, User
from app.dependencies.db import get_db
from app.dependencies.settings import get_settings
from app.exceptions.auth import InvalidCredentialsException
from app.utils.crud import get_user_by_id

ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7
settings = get_settings()
SECRET_KEY = settings.secret_key
ALGORITHM = settings.encryption_algo

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(db: Session, user_id: UUID) -> str:
    raw_token = str(uuid4())  # Generate random token
    token_hash = pwd_context.hash(raw_token)
    expires_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    refresh_token = RefreshToken(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=expires_at,
    )
    db.add(refresh_token)
    db.commit()

    return raw_token


def verify_token(token: str) -> dict | None:
    try:
        decoded_token_data = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # Check if the token has expired
        if decoded_token_data["exp"] < int(datetime.now(timezone.utc).timestamp()):
            return {"status": "expired"}
        return {"status": "valid", "data": decoded_token_data}
    except jwt.ExpiredSignatureError:
        return {"status": "expired"}
    except jwt.JWTError:
        return None


def verify_refresh_token(db: Session, token: str) -> UUID:
    statement = select(RefreshToken).where(
        RefreshToken.expires_at > datetime.now(timezone.utc),
    )
    refresh_token = db.exec(statement).first()
    if not refresh_token or not pwd_context.verify(token, refresh_token.token_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
    return refresh_token.user_id


def revoke_refresh_token(db: Session, token: str) -> None:
    statement = select(RefreshToken).where(
        RefreshToken.expires_at > datetime.now(timezone.utc)
    )
    refresh_token = db.exec(statement).first()
    if refresh_token and pwd_context.verify(token, refresh_token.token_hash):
        db.delete(refresh_token)
        db.commit()


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    token_data = verify_token(token)
    if token_data is None or token_data["status"] != "valid":
        raise InvalidCredentialsException("Invalid or expired token")
    user_id = token_data["data"].get("sub")
    if user_id is None:
        raise InvalidCredentialsException("Token does not contain user ID")
    user_id = UUID(user_id)
    user = get_user_by_id(db, user_id)
    if user is None:
        raise InvalidCredentialsException("User does not exist")
    return user


async def validate_api_key(api_key: str = Header(...), db: Session = Depends(get_db)):
    key_record = db.exec(
        select(APIKey).where(APIKey.key == api_key, APIKey.is_active)
    ).first()
    if not key_record or (
        key_record.expires_at and key_record.expires_at < datetime.now(timezone.utc)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired API key",
        )
    return key_record
