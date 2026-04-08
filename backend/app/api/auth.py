from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_active_user
from app.auth.jwt import create_access_token, create_refresh_token, decode_token
from app.auth.passwords import verify_password
from app.db import get_db
from app.models.models import User
from app.repositories.user_repo import get_user_by_username
from app.schemas.schemas import RefreshRequest, Token, UserWithRoles
from app.services.audit_service import log_action

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> Token:
    user = get_user_by_username(db, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user account"
        )

    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    log_action(
        db=db,
        entity_type="user",
        entity_id=str(user.id),
        action="login",
        actor=user,
        new_value={"username": user.username},
        request=request,
    )
    db.commit()

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )


@router.post("/refresh", response_model=Token)
def refresh_token(
    body: RefreshRequest,
    db: Session = Depends(get_db),
) -> Token:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(body.refresh_token)
        if payload.get("type") != "refresh":
            raise credentials_exception
        user_id: str = payload.get("sub", "")
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise credentials_exception

    new_access = create_access_token(data={"sub": str(user.id)})
    new_refresh = create_refresh_token(data={"sub": str(user.id)})

    return Token(
        access_token=new_access,
        refresh_token=new_refresh,
        token_type="bearer",
    )


@router.get("/me", response_model=UserWithRoles)
def get_me(current_user: User = Depends(get_current_active_user)) -> User:
    return current_user
