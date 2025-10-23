from datetime import timedelta
from typing import Any, Dict, Optional

from fastapi import APIRouter, Cookie, Response, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app import security
from app.exceptions import _get_credential_exception
from app.config import settings
from app.models import User
from app.routes.dependencies import get_token
from app.crud import user_crud
from app.database import get_db
from app.schemas.auth import Token, TokenPayload, PasswordResetRequest, PasswordResetConfirm
from app.services.email import email_service

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


@router.post("/password-reset/request", status_code=status.HTTP_200_OK)
def request_password_reset(
    request: PasswordResetRequest,
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """
    Request a password reset for a user.

    Parameters:
        request (PasswordResetRequest): The password reset request containing the email.
        db (Session): The database session.

    Returns:
        Dict[str, str]: A confirmation message.
    
    Note:
        This endpoint always returns success for security reasons, 
        even if the email doesn't exist in the database.
    """
    user = user_crud.get_user_by_email(db, request.email)
    
    if user and user_crud.is_active_user(user):
        reset_token = user_crud.create_password_reset_token(db, request.email)
        
        if reset_token:
            email_sent = email_service.send_password_reset_email(
                email=user.email,
                reset_token=reset_token,
                user_nickname=user.nickname
            )
            
            if not email_sent:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to send reset email. Please try again later."
                )
    
    return {
        "detail": "If the email exists in our system, you will receive password reset instructions."
    }


@router.post("/password-reset/confirm", status_code=status.HTTP_200_OK)
def confirm_password_reset(
    request: PasswordResetConfirm,
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """
    Confirm a password reset using a reset token.

    Parameters:
        request (PasswordResetConfirm): The password reset confirmation containing token and new password.
        db (Session): The database session.

    Returns:
        Dict[str, str]: A confirmation message.
    
    Raises:
        HTTPException: If the reset token is invalid or expired.
        HTTPException: If the new password doesn't meet security requirements.
    """
    # Validate password strength
    is_valid, error_messages = security.validate_password_strength(request.new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"errors": error_messages}
        )
    
    user = user_crud.reset_password(db, request.token, request.new_password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token."
        )
    
    return {"detail": "Password has been reset successfully. You can now log in with your new password."}


@router.post("/password-reset/verify-token", status_code=status.HTTP_200_OK)
def verify_reset_token(
    token: str,
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """
    Verify if a password reset token is valid.

    Parameters:
        token (str): The reset token to verify.
        db (Session): The database session.

    Returns:
        Dict[str, str]: A confirmation message.
    
    Raises:
        HTTPException: If the reset token is invalid or expired.
    """
    user = user_crud.verify_reset_token(db, token)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token."
        )
    
    return {"detail": "Reset token is valid.", "email": user.email}
