from datetime import timedelta
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app import security
from app.config import settings
from app.models import User
from app.routes.dependencies import get_token, get_current_user
from app.crud import user_crud
from app.database import get_db
from app.schemas.auth import Token, TokenPayload

router = APIRouter()


@router.post("/login", response_model=Token, status_code=status.HTTP_200_OK)
def login_for_access_token(
    db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()
) -> Dict[str, Any]:
    """
    Endpoint for user login. Authenticates the user using the provided
    email and password.

    Parameters:
        - db (Session): The database session.
        - form_data (OAuth2PasswordRequestForm): The form data
        containing the username and password.

    Returns:
        - Dict[str, Any]: A dictionary containing the access token and token type.
    """
    user = user_crud.authenticate_user(
        db, email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password",
        )
    if not user_crud.is_active_user(user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        subject=user.id, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/logout", status_code=status.HTTP_200_OK)
def user_logout(token: TokenPayload = Depends(get_token), current_user: User = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Current user not found",
        )
    # TODO revoke token for better security
    return {"detail": "Access token has been revoked"}
