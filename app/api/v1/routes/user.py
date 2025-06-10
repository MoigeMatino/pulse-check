from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.api.v1.models import User
from app.api.v1.schemas import UserRead, UserUpdate
from app.auth import get_current_user, get_password_hash
from app.dependencies.db import get_db
from app.utils.crud import get_user_by_email

router = APIRouter(prefix="/user", tags=["user"])


@router.get("/me", response_model=UserRead)
def get_user_profile(current_user: User = Depends(get_current_user)) -> UserRead:
    return current_user


@router.patch("/me", response_model=UserRead)
def update_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserRead:
    # check if updated email already exists
    if user_update.email:
        existing_user = get_user_by_email(db, user_update.email)
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

    # Update user fields
    update_data = user_update.model_dump(exclude_unset=True)
    # If password is provided, hash it
    if "password" in update_data:
        update_data["password_hash"] = get_password_hash(update_data.pop("password"))

    for key, value in update_data.items():
        setattr(current_user, key, value)

    db.add(current_user)
    db.commit()
    db.refresh(current_user)

    return current_user
