from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db, get_user_by_email
from app.core.security import create_access_token, get_current_user

router = APIRouter(tags=["auth"])


class LoginPayload(BaseModel):
    email: str = Field(..., min_length=3)
    password: str = Field(..., min_length=4)


@router.post("/login")
async def login(payload: LoginPayload, db: Session = Depends(get_db)):
    user = get_user_by_email(db, payload.email)
    if not user or user.password != payload.password:
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
async def me(current_user=Depends(get_current_user)):
    return {
        "id": current_user.public_id,
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role,
    }
