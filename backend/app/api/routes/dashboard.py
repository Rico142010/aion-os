from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db, get_user_by_email
from app.core.security import create_access_token, get_current_user, hash_password, verify_password
from app.models import User

router = APIRouter(tags=["auth"])


class RegisterPayload(BaseModel):
    name: str = Field(..., min_length=2)
    email: str = Field(..., min_length=3)
    password: str = Field(..., min_length=6)


class LoginPayload(BaseModel):
    email: str = Field(..., min_length=3)
    password: str = Field(..., min_length=6)


@router.post("/register")
async def register(payload: RegisterPayload, db: Session = Depends(get_db)):
    if get_user_by_email(db, payload.email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El usuario ya existe")

    user = User(
        public_id=f"u-{db.query(User).count() + 1:03d}",
        name=payload.name,
        email=payload.email,
        password=hash_password(payload.password),
        role="user",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.email)
    return {
        "token": token,
        "user": {
            "id": user.public_id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
        },
    }


@router.post("/login")
async def login(payload: LoginPayload, db: Session = Depends(get_db)):
    user = get_user_by_email(db, payload.email)
    if not user or not verify_password(payload.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales incorrectas")

    token = create_access_token(user.email)
    return {
        "token": token,
        "user": {
            "id": user.public_id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
        },
    }


@router.get("/me")
async def me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.public_id,
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role,
    }
