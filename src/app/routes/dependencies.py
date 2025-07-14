from typing import Tuple, List

from fastapi import HTTPException, Depends, Query, status, Security
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader

from jose import jwt

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.config import settings
from app.crud import user_crud, apiclient_crud
from app.database import get_db
from app.exceptions import _get_credential_exception
from app.models import User, Base, ApiClient
from app.schemas.auth import TokenPayload, ApiKeyPayload


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
x_api_key = APIKeyHeader(name="x-api-key", auto_error=False)

def get_pagination_params(
    page: int = Query(1, ge=1), page_size: int = Query(5, ge=1, le=100)
) -> Tuple[int, int]:
    """
    Get the pagination parameters.

    Parameters:
        page (int): The number of items to skip. Defaults to 1.
        page_size (int): The maximum number of items to return. Defaults to 5.

    Returns:
        Tuple[int, int]: A tuple containing the page and size values.
    """
    page = (page - 1) * page_size
    size = page_size
    return page, size


def get_sort_by_params(sortby: str = Query('created_at'), direction: str = Query('desc')) -> Tuple[str, bool]:
    """
    Get the order by parameters.

    Parameters:
        sortby (str): The field name to order by. Defaults to None.
        direction (str): The direction to order by. Defaults to asc.

    Returns:
        Tuple[str, bool]: A tuple containing the sortby and descending values.
    """
    descending = direction == 'desc'
    return sortby, descending


def get_token(token: str = Depends(oauth2_scheme)) -> TokenPayload:
    """
    Retrieve the token payload from the provided JWT token.

    Parameters:
        token (str, optional): The JWT token. Defaults to the value returned by the `oauth2_scheme` dependency.

    Returns:
        TokenPayload: The decoded token payload.

    Raises:
        HTTPException: If there is an error decoding the token or validating the payload.
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (jwt.JWTError, ValidationError) as e:
        raise _get_credential_exception(status_code=status.HTTP_401_UNAUTHORIZED) from e
    return token_data


def get_current_user(
    db: Session = Depends(get_db), token: TokenPayload = Depends(get_token)
) -> User:
    """
    Retrieves the current user based on the provided database session and authentication token.

    Parameters:
        db (Session): The database session to use for querying the user information.
        token (TokenPayload): The authentication token containing the user's identification.

    Returns:
        User: The user object representing the current authenticated user.

    Raises:
        HTTPException: If the user is not found in the database.
    """
    user = user_crud.get_one(db, User.id == token.sub)
    if user is None:
        raise _get_credential_exception(
            status_code=status.HTTP_404_NOT_FOUND, details="User not found"
        )
    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Returns the current active user.

    Parameters:
        current_user (User, optional): The current user.

    Returns:
        User: The current active user.

    Raises:
        HTTPException: If the user is not active

    """
    if not user_crud.is_active_user(current_user):
        raise _get_credential_exception(
            status_code=status.HTTP_400_BAD_REQUEST,
            details="Inactive user",
        )
    return current_user


def get_current_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    """Returns the current superuser (admin).

    Parameters:
        current_user (User, optional): The current user.

    Returns:
        User: The current superuser.

    Raises:
        HTTPException: If the current user is not a super user (admin).

    """
    if not user_crud.is_super_user(current_user):
        raise _get_credential_exception(
            status_code=status.HTTP_403_FORBIDDEN,
            details="The user does not have enough privileges",
        )
    return current_user


def get_api_key(api_key: str = Security(x_api_key)) -> str:
    """
    Retrieve the api key from the provided key.

    Parameters:
        api_key (str, optional): The API key. Defaults to the value returned by the `x_api_key` dependency.

    Returns:
        str: The api key payload.

    Raises:
        HTTPException: If there is an error retrieving the api key or validating the payload.
    """
    try:
        if not api_key:
            raise _get_credential_exception(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing or invalid API key"
            )
        key_data = ApiKeyPayload(**{"api_key": api_key})
    except Exception as e:
        raise _get_credential_exception(status_code=status.HTTP_401_UNAUTHORIZED) from e
    return key_data


def get_current_client(
    db: Session = Depends(get_db), api_key: ApiKeyPayload = Depends(get_api_key)
) -> ApiClient:
    """
    Retrieves the current client based on the provided database session and authentication api key.

    Parameters:
        db (Session): The database session to use for querying the client information.
        api_key (ApiKeyPayload): The authentication key containing the client's identification.

    Returns:
        ApicLient: The ApicLient object representing the current authenticated ApicLient.

    Raises:
        HTTPException: If the api client is not found in the database.
    """
    client = apiclient_crud.get_one(db, ApiClient.api_key == api_key.api_key)
    if client is None:
        raise _get_credential_exception(
            status_code=status.HTTP_404_NOT_FOUND, details="Client not found"
        )
    return client


def get_current_active_client(
    current_client: ApiClient = Depends(get_current_client),
) -> ApiClient:
    """Returns the current active api client.

    Parameters:
        current_client (ApiClient, optional): The current api client.

    Returns:
        ApiClient: The current active api client.

    Raises:
        HTTPException: If the api client is not active

    """
    if not apiclient_crud.is_active_client(current_client):
        raise _get_credential_exception(
            status_code=status.HTTP_400_BAD_REQUEST,
            details="Inactive client",
        )
    return current_client


class RoleChecker:
    """
    Checker for routes role based access.
    
    Parameters:
            allowed_roles (List[str]): The required roles to access to the endpoint.

    Raises:
            HTTPException: If the current user does not have enough privileges 
            to access to the requested endpoint.
    """

    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, user: User = Depends(get_current_active_user)):  
        """
        Checks if the current user has access to endpoint.

        Parameters:
            user (User, optional): The current active user.

        Raises:
            HTTPException: If the current user does not have enough privileges 
            to access to the requested endpoint.
        """
        if user.role not in self.allowed_roles:
            raise _get_credential_exception(
                status_code=status.HTTP_403_FORBIDDEN,
                details="The user does not have enough privileges",
            )