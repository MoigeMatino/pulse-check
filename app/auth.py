from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from passlib.context import CryptContext
from sqlmodel import Session

from app.api.v1.models import User
from app.dependencies.db import get_db
from app.dependencies.settings import get_settings
from app.exceptions.auth import InvalidCredentialsException
from app.utils.crud import get_user_by_id

ACCESS_TOKEN_EXPIRE_MINUTES = 30
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
