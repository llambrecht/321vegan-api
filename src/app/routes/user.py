from typing import Annotated, List, Optional, Tuple

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.routes.dependencies import get_current_superuser, get_pagination_params, get_sort_by_params, RoleChecker, get_current_active_user_or_client, get_admin_or_client
from app.crud import user_crud
from app.database.db import get_db
from app.log import get_logger
from app.models import User
from app.schemas.user import UserCreate, UserOutPaginated, UserOut, UserUpdate, UserFilters, UserUpdateOwn, UserPatch
from app.security import get_password_hash

log = get_logger(__name__)


router = APIRouter()


@router.get(
    "/", response_model=List[Optional[UserOut]], status_code=status.HTTP_200_OK, dependencies=[Depends(RoleChecker(["admin"]))]
)
def fetch_all_users(
    db: Session = Depends(get_db),
):
    """
    Fetches all users.

    Parameters:
        db (Session): The database session.
    
    Returns:
        List[Optional[UserOut]]: A list of user objects,
            or None if there are no users.

    Raises:
        HTTPException: If the user does not have enough
            permissions to access to this endpoint.
    """
    
    return user_crud.get_all(db)


@router.get(
    "/search", response_model=Optional[UserOutPaginated], status_code=status.HTTP_200_OK, dependencies=[Depends(RoleChecker(["admin"]))]
)
def fetch_paginated_users(
    db: Session = Depends(get_db), pagination_params: Tuple[int, int] = Depends(get_pagination_params),
    orderby_params: Tuple[str, bool] = Depends(get_sort_by_params),
    filter_params: UserFilters = Depends()
) -> Optional[UserOutPaginated]:
    """
    Fetches all users with pagination.

    Parameters:
        db (Session): The database session.
        pagination_params (Tuple[int, int]): The pagination parameters (skip, limit).
        orderby_params (Tuple[str, bool]): The order by parameters (sortby, descending).

    Returns:
        Optional[UserOutPaginated]: A list of user objects,
            or None if there are no users.

    Raises:
        HTTPException: If the user does not have enough
            permissions to access to this endpoint.
    """
    
    page, size = pagination_params
    sortby, descending = orderby_params
    users, total = user_crud.get_many(
        db, 
        skip=page, 
        limit=size, 
        order_by=sortby, 
        descending=descending,
        **filter_params.model_dump(exclude_none=True)
    )
    pages = (total + size - 1) // size
    return {
        "items": users,
        "total": total,
        "page": page,
        "size": size,
        "pages": pages
    }


@router.get("/{id}", response_model=UserOut, status_code=status.HTTP_200_OK, dependencies=[Depends(RoleChecker(["admin"]))])
def fetch_user_by_id(id: int, db: Session = Depends(get_db)):
    """
    Fetches a user by their ID from the database.

    Parameters:
        id (int): The ID of the user to fetch.
        db (Session): The database session.

    Returns:
        UserOut: The user object fetched from the database.

    Raises:
        HTTPException: If the user does not have enough
            permissions to access to this endpoint.
        HTTPException: If the user with the specified ID is not found in the database.
    """
    user = user_crud.get_one(db, User.id == id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with {id} not found",
        )
    return user


@router.get("/email/{email}", response_model=UserOut, status_code=status.HTTP_200_OK, dependencies=[Depends(RoleChecker(["admin"]))])
def fetch_user_by_email(email: str, db: Session = Depends(get_db)):
    """
    Fetches a user from the database based on the provided email.

    Parameters:
        email (str): The email address of the user.
        db (Session, optional): The database session.
        Defaults to the result of calling `get_db`.

    Returns:
        UserOut: The user object fetched from the database.

    Raises:
        HTTPException: If no user is found with the provided email,
            an HTTP 404 Not Found exception is raised.
        HTTPException: If the user does not have enough
            permissions to access to this endpoint.
    """
    user = user_crud.get_user_by_email(db, email=email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"User with {email} not found"
        )
    return user


@router.post("/", response_model=UserOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(get_admin_or_client)])
def create_user(
    user_create: Annotated[
        UserCreate,
        Body(
            examples=[
                {
                    "role": "user",
                    "nickname": "User name",
                    "email": "example@example.com",
                    "password": "12345678",
                    "is_active": True,
                    "vegan_since": "2023-01-01T00:00:00Z",
                    "nb_products_sent": 0
                }
            ]
        ),
    ],
    db: Session = Depends(get_db),
):
    """
    Create a new user.

    Parameters:
        user_create (UserCreate): The user data to be created.
        db (Session): The database session.

    Returns:
        User: The newly created user.

    Raises:
        HTTPException: If a user with the same email already exists in the system.
        HTTPException: If the user is not an admin or the request is not authenticated with a valid API key.
    """
    user = user_crud.get_user_by_email(db, email=user_create.email)
    if user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"The user with this {user_create.email} already exists \
            in the system",
        )
    try:
        dict_user_create = user_create.model_dump()
        dict_user_create['password'] = get_password_hash(user_create.password)
        user_in = UserCreate(
            **dict_user_create,
        )
        user = user_crud.create(db, user_in)
        
    except IntegrityError as e:
        error_message = str(e.orig)
        if "unique constraint" in error_message.lower(): 
            if "email" in error_message.lower():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"User with EMAIL {user_create.email} already exists",
                ) from e
            elif "nickname" in error_message.lower():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"User with NICKNAME {user_create.nickname} already exists",
                ) from e
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Data integrity error: {error_message}",
            ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Couldn't create user. Error: {str(e)}",
        ) from e 
    return user


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(RoleChecker([ "admin"]))])
def delete_user(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
):
    """
    Delete a user by user ID.

    Parameters:
        id (int): The ID of the user to delete.
        db (Session, optional): The database session. Defaults to Depends(get_db).
        current_user (User, optional): The current authenticated superuser.

    Raises:
        HTTPException: If the user is not found or the user tries to delete themselves.
        HTTPException: If there is an error deleting the user.
        HTTPException: If the user does not have enough
            permissions to access to this endpoint.
    Returns:
        None

    """
    user = user_crud.get_one(db, User.id == id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {id} not found. Cannot delete.",
        )

    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot delete yourself",
        )
    try:
        user_crud.delete(db, user)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Couldn't delete user with id {id}. Error: {str(e)}",
        ) from e

@router.put("/{id}", response_model=UserOut, status_code=status.HTTP_200_OK, dependencies=[Depends(RoleChecker(["admin"]))])
def update_user(
    id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
):
    """
    Update a user with the given ID.

    Parameters:
        id (int): The ID of the user to update.
        user_update (UserUpdate): The updated user information.
        db (Session, optional): The database session. Defaults to Depends(get_db).

    Returns:
        UserOut: The updated user information.

    Raises:
        HTTPException: If the user is not found.
        HTTPException: If there is an error updating the user.
        HTTPException: If the user does not have enough
            permissions to access to this endpoint.
    """
    user = user_crud.get_one(db, User.id == id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {id} not found. Cannot update.",
        )
    try:
        user = user_crud.update(db, user, user_update)
    except IntegrityError as e:
        error_message = str(e.orig)
        if "unique constraint" in error_message.lower(): 
            if "email" in error_message.lower():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"User with EMAIL {user_update.email} already exists",
                ) from e
            elif "nickname" in error_message.lower():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"User with NICKNAME {user_update.nickname} already exists",
                ) from e
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Data integrity error: {error_message}",
            ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Couldn't update user with id {id}. Error: {str(e)}",
        ) from e
    return user


@router.patch("/{id}", response_model=UserOut, status_code=status.HTTP_200_OK, dependencies=[Depends(RoleChecker(["admin"]))])
def patch_user(
    id: int,
    user_patch: UserPatch,
    db: Session = Depends(get_db),
):
    """
    Partially update a user with the given ID.
    Only the provided fields will be updated, other fields remain unchanged.

    Parameters:
        id (int): The ID of the user to update.
        user_patch (UserPatch): The fields to update (only provided fields will be updated).
        db (Session, optional): The database session. Defaults to Depends(get_db).

    Returns:
        UserOut: The updated user information.

    Raises:
        HTTPException: If the user is not found.
        HTTPException: If there is an error updating the user.
        HTTPException: If the user does not have enough
            permissions to access to this endpoint.
    """
    user = user_crud.get_one(db, User.id == id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {id} not found. Cannot update.",
        )
    
    # Hash password if it's being updated
    update_data = user_patch.model_dump(exclude_unset=True)
    if "password" in update_data:
        update_data["password"] = get_password_hash(update_data["password"])
        # Create a new UserPatch with the hashed password
        user_patch = UserPatch(**update_data)
    
    try:
        user = user_crud.update(db, user, user_patch)
    except IntegrityError as e:
        error_message = str(e.orig)
        if "unique constraint" in error_message.lower(): 
            if "email" in error_message.lower():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"User with EMAIL {update_data.get('email', '')} already exists",
                ) from e
            elif "nickname" in error_message.lower():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"User with NICKNAME {update_data.get('nickname', '')} already exists",
                ) from e
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Data integrity error: {error_message}",
            ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Couldn't update user with id {id}. Error: {str(e)}",
        ) from e
    return user