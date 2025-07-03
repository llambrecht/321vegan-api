from datetime import timedelta
from typing import Any, Dict, Optional

from fastapi import APIRouter, Cookie, Response, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app import security
from app.exceptions import _get_credential_exception
from app.config import settings
from app.models import User
from app.routes.dependencies import get_token, get_current_active_user, get_current_user
from app.crud import user_crud
from app.database import get_db
from app.schemas.auth import Token, TokenPayload

router = APIRouter()


@router.post("/login", response_model=Token, status_code=status.HTTP_200_OK)
def login_for_access_token(
    response: Response,
    db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()
) -> Dict[str, Any]:
    """
    Endpoint for user login. Authenticates the user using the provided
    email and password.

    Parameters:
        - response (Response): The Http response.
        - db (Session): The database session.
        - form_data (OAuth2PasswordRequestForm): The form data
        containing the username and password.

    Returns:
        - Dict[str, Any]: A dictionary containing the access token and token type.
    
    Raises:
        HTTPException: If the user with the provided username and password is not found in the database.
        HTTPException: If the user is inactive.
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
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token = security.create_access_token(
        subject=user.id, expires_delta=refresh_token_expires
    )
    max_age = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    response.set_cookie(
        key="refresh_token", value=refresh_token, httponly=True, secure=True, samesite="lax", max_age=max_age
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/refresh", response_model=Token, status_code=status.HTTP_200_OK)
def user_refresh(db: Session = Depends(get_db), refresh_token: Optional[str] = Cookie(None, alias="refresh_token")) -> Dict[str, Any]:
    """
    Endpoint for user refresh token. Authenticates the user from refresh_token HttpOnly cookie.

    Parameters:
        - db (Session): The database session.
        - refresh_token (Cookie): The cookie containing the refresh_token.

    Returns:
        - Dict[str, Any]: A dictionary containing the access token and token type.
    
    Raises:
        HTTPException: If the refresh_token is not provided
        HTTPException: If the refresh_token is invalid
        HTTPException: If the user with the token sub is not found in the database.
        HTTPException: If the user is inactive.
    """
    if not refresh_token:
        raise _get_credential_exception(
            details="Refresh token not found",
        )
    token_data = security.verify_token(refresh_token)
    if not token_data:
        raise _get_credential_exception(
            details="Invalid refresh token",
        )
    user = user_crud.get_one(db, User.id == token_data.sub)
    if not user:
        raise _get_credential_exception(
            details="User not found",
        )
    if not user_crud.is_active_user(user):
        raise _get_credential_exception(
            details="Inactive user",
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        subject=user.id, expires_delta=access_token_expires
    )
    return {"access_token": access_token,  "token_type": "bearer"}


@router.get("/logout", status_code=status.HTTP_200_OK)
def user_logout(response: Response, token: TokenPayload = Depends(get_token), refresh_token: Optional[str] = Cookie(None, alias="refresh_token")):
    """
    Endpoint for user logout. Authenticates the user from refresh_token HttpOnly cookie.

    Parameters:
        - response (Response): Http Response.
        - refresh_token (Cookie): The cookie containing the refresh_token.

    Returns:
        - Dict[str, str]: A dictionary containing the confirmation user successfully logged out.
    
    Raises:
        HTTPException: If the refresh_token is not provided
        HTTPException: If the refresh_token is invalid
    """
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found",
        )

    token_data = security.verify_token(refresh_token)
    if not token_data:
        raise _get_credential_exception(
            details="Invalid refresh token",
        )
    response.delete_cookie(key="refresh_token")
    # TODO revoke access token for better security
    return {"detail": "Access token has been successfully revoked"}
