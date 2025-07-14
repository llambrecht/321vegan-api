from datetime import datetime, timedelta
from typing import Any, Union
from jose import jwt, JWTError
from app.config import settings
from app.schemas.auth import TokenPayload
import secrets
import string

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