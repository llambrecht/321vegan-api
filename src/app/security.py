from datetime import datetime, timedelta
from typing import Any, Union
from pydantic import ValidationError
from jose import jwt, JWTError
from app.config import settings
from app.schemas.auth import TokenPayload
import secrets
import string
import re

# hack for passlib new bcrypt incompatibility
import bcrypt
bcrypt.__about__ = bcrypt
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(
    subject: Union[str, Any], expires_delta: timedelta = None
) -> str:
    """
    Creates an access token.

    Parameters:
        subject (Union[str, Any]): The subject for which the access token is created.
        expires_delta (timedelta, optional): The expiration time for the access token. Defaults to None.

    Returns:
        str: The encoded access token.
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt

def verify_token(token: str) -> TokenPayload | None:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        sub = payload.get("sub")
        if not sub:
            return None
        token_data = TokenPayload(**payload)
    except (jwt.JWTError, ValidationError) as e:
        return None
    return token_data

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify if a plain password matches a hashed password.

    Parameters:
        plain_password (str): The plain password to be verified.
        hashed_password (str): The hashed password to compare with.

    Returns:
        bool: True if the plain password matches the hashed password, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    Generate the hash value of a password.

    Parameters:
        password (str): The password to be hashed.

    Returns:
        str: The hash value of the password.
    """
    return pwd_context.hash(password)

def generate_api_key(length: int = 32) -> str:
    """
    Generates a cryptographically strong random numbers string.

    Parameters:
        length (int): The length of the generated string.

    Returns:
        str: The generated value of the key.
    """
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def generate_reset_token() -> str:
    """
    Generate a secure reset token for password reset.

    Returns:
        str: A secure random token for password reset.
    """
    return secrets.token_urlsafe(32)


def create_reset_token(user_id: int) -> str:
    """
    Create a password reset token for a user.

    Parameters:
        user_id (int): The user ID to create the token for.

    Returns:
        str: The encoded reset token.
    """
    expire = datetime.utcnow() + timedelta(hours=settings.RESET_TOKEN_EXPIRE_HOURS)
    to_encode = {
        "exp": expire,
        "sub": str(user_id),
        "type": "password_reset"
    }
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def verify_reset_token(token: str) -> TokenPayload | None:
    """
    Verify a password reset token.

    Parameters:
        token (str): The reset token to verify.

    Returns:
        TokenPayload | None: The token payload if valid, None otherwise.
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        sub = payload.get("sub")
        token_type = payload.get("type")
        
        if not sub or token_type != "password_reset":
            return None
            
        token_data = TokenPayload(**payload)
    except (jwt.JWTError, ValidationError) as e:
        return None
    return token_data


import re

def validate_password_strength(password: str) -> tuple[bool, list[str]]:
    """
    Validate password strength.

    Parameters:
        password (str): The password to validate.

    Returns:
        tuple[bool, list[str]]: A tuple containing (is_valid, error_messages).
    """
    errors = []

    if len(password) < 8:
        errors.append("Password must be at least 8 characters long")
    if len(password) > 100:
        errors.append("Password must be less than 100 characters long")
    if not re.search(r"[a-z]", password):
        errors.append("Password must contain at least one lowercase letter")
    if not re.search(r"[A-Z]", password):
        errors.append("Password must contain at least one uppercase letter")
    if not re.search(r"\d", password):
        errors.append("Password must contain at least one number")
    if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]", password):
        errors.append("Password must contain at least one special character")

    return len(errors) == 0, errors
