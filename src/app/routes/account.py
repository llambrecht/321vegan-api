from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.routes.dependencies import get_current_active_user
from app.crud import user_crud
from app.database.db import get_db
from app.log import get_logger
from app.models import User
from app.schemas.user import UserOut, UserUpdateOwn
from app.security import get_password_hash

log = get_logger(__name__)


router = APIRouter()


@router.get("/", response_model=UserOut, status_code=status.HTTP_200_OK)
def fetch_current_active_user(user: User = Depends(get_current_active_user)):
    """
    Fetches the current active user from the database.

    Parameters:
        user (User, optional): The current active user.

    Returns:
        UserOut: The user object fetched from the database.

    Raises:
        HTTPException: If the current active user is not found.
    """
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Current active user not found",
        )
    return user


@router.put("/", response_model=UserOut, status_code=status.HTTP_200_OK)
def update_current_active_user(
    user_update: UserUpdateOwn,
    db: Session = Depends(get_db),
    active_user: User = Depends(get_current_active_user),
):
    """
    Update a current active user.

    Parameters:
        user_update (UserUpdateOwn): The updated user information.
        db (Session, optional): The database session. Defaults to Depends(get_db).
        active_user (User, optional): The current active user.

    Returns:
        UserOut: The updated user information.

    Raises:
        HTTPException: If the user is not found.
        HTTPException: If there is an error updating the user.
    """
    
    if active_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Current active user not found. Cannot update.",
        )
    try:
        dict_user_update = user_update.model_dump(
            exclude_unset=True
        )  # exclude_unset=True -
        # do not update fields with None
        if 'password' in dict_user_update:
            dict_user_update['password'] = get_password_hash(user_update.password)
        user_in = UserUpdateOwn(
            **dict_user_update
        )
        user = user_crud.update(db, active_user, user_in)
    except IntegrityError as e:
        error_message = str(e.orig)
        if "unique constraint" in error_message.lower() and "nickname" in error_message.lower(): 
            raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"User with NICKNAME {user_in.nickname} already exists",
                ) from e   
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Data integrity error: {error_message}",
            ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Couldn't update current active user. Error: {str(e)}",
        ) from e
    return user