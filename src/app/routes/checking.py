from typing import Annotated, List, Optional, Tuple

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.routes.dependencies import get_current_active_user, get_pagination_params, get_sort_by_params, RoleChecker
from app.crud import checking_crud
from app.database.db import get_db
from app.log import get_logger
from app.models import Checking, User
from app.schemas.checking import CheckingCreate, CheckingOut, CheckingUpdate, CheckingOutPaginated, CheckingFilters

log = get_logger(__name__)

router = APIRouter(dependencies=[Depends(get_current_active_user)])


@router.get(
    "/", response_model=List[Optional[CheckingOut]], status_code=status.HTTP_200_OK
)
def fetch_all_checkings(db: Session = Depends(get_db)) -> List[Optional[CheckingOut]]:
    """
    Fetch all checkings.

    This function fetches all checkings from the
    database.

    Parameters:
        db (Session): The database session.

    Returns:
        List[Optional[CheckingOut]]: The list of checkings fetched from the database.
    """
    
    return checking_crud.get_all(db)


@router.get(
    "/search", response_model=Optional[CheckingOutPaginated], status_code=status.HTTP_200_OK
)
def fetch_paginated_checkings(
    db: Session = Depends(get_db),
    pagination_params: Tuple[int, int] = Depends(get_pagination_params),
    orderby_params: Tuple[str, bool] = Depends(get_sort_by_params),
    filter_params: CheckingFilters = Depends()
) -> Optional[CheckingOutPaginated]:
    """
    Fetch many checkings.

    This function fetches all checkings from the
    database based on the pagination parameters.

    Parameters:
        db (Session): The database session.
        pagination_params (Tuple[int, int]): The pagination parameters (skip, limit).
        orderby_params (Tuple[str, bool]): The order by parameters (sortby, descending).

    Returns:
        CheckingOutPaginated: The list of checkings fetched from the database with pagination datas.
    """
    page, size = pagination_params
    sortby, descending = orderby_params
    checkings, total = checking_crud.get_many(
        db, 
        skip=page, 
        limit=size, 
        order_by=sortby, 
        descending=descending, 
        **filter_params.model_dump(exclude_none=True)
    )
    pages = (total + size - 1) // size
    return {
        "items": checkings,
        "total": total,
        "page": page,
        "size": size,
        "pages": pages
    }


@router.get(
    "/{id}",
    response_model=Optional[CheckingOut],
    status_code=status.HTTP_200_OK,
)
def fetch_checking_by_id(
    id: int, db: Session = Depends(get_db)
) -> CheckingOut:
    """
    Fetches a checking by its ID.

    Parameters:
        id (int): The ID of the checking.
        db (Session): The database session.

    Returns:
        CheckingOut: The fetched checking.

    Raises:
        HTTPException: If the checking is not found.
    """
    checking = checking_crud.get_one(db, Checking.id == id)
    if checking is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Checking with id {id} not found",
        )
    return checking


@router.post(
    "/",
    response_model=CheckingOut,
    status_code=status.HTTP_201_CREATED,
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
    dependencies=[Depends(RoleChecker(["contributor", "admin"]))]
)
def create_checking(
    checking_create: Annotated[
        CheckingCreate,
        Body(
            examples=[
                {
                    "product_id": 1,
                }
            ]
        ),
    ],
    db: Session = Depends(get_db),
    active_user: User = Depends(get_current_active_user),
):
    """
    Create a checking.

    Parameters:
        checking_create (CheckingCreate): The checking data to be created.
        db (Session, optional): The database session.
            Defaults to Depends(get_db).
        active_user (User, optional): The current active user.


    Returns:
        CheckingOut: The created checking.

    Raises:
        HTTPException: If the user is not found or
            the user does not have enough permissions.
        HTTPException: If a product provided does not exists.
        HTTPException: If there is an error creating
            the checking in the database.
    """
    try:
        dict_checking_create = checking_create.model_dump()
        dict_checking_create['user_id'] = str(active_user.id)
        checking_in = CheckingCreate(
            **dict_checking_create,
        )
        checking = checking_crud.create(
            db, checking_in
        )
    except IntegrityError as e:
        error_message = str(e.orig)
        if "foreign key constraint" in error_message.lower() and "product_id" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product with id {checking_in.product_id} does not exist",
            ) from e
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Data integrity error: {error_message}",
            ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Couldn't create checking. Error: {str(e)}",
        ) from e 
    return checking


@router.put(
    "/{id}",
    response_model=CheckingOut,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(RoleChecker(["contributor", "admin"]))]
)
def update_checking(
    id: int,
    checking_update: CheckingUpdate,
    db: Session = Depends(get_db),
    active_user: User = Depends(get_current_active_user),
):
    """
    Update a checking by its ID.

    Parameters:
        id (int): The ID of the checking to be updated.
        checking_update (CheckingUpdate): The updated checking data.
        db (Session, optional): The database session.
            Defaults to Depends(get_db).
        active_user (User, optional): The current active user.

    Returns:
        CheckingOut: The updated checking.

    Raises:
        HTTPException: If the checking does not exist or
            the user does not have enough permissions.
        HTTPException: If there is an error updating
            the checking in the database.
    """
    checking = checking_crud.get_one(db, Checking.id == id)
    if checking is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Checking with id {id} not found",
        )
    if checking.user_id != active_user.id and not active_user.is_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user does not have enough privileges",
        )
    try:
        checking = checking_crud.update(db, checking, checking_update)
    except IntegrityError as e:
        error_message = str(e.orig)
        if "foreign key constraint" in error_message.lower() and "product_id" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product with id {checking_update.product_id} does not exist",
            ) from e
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Data integrity error: {error_message}",
            ) from e
    except Exception as e:  
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Couldn't update checking with id {id}. Error: {str(e)}",
        ) from e  
    return checking


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(RoleChecker(["contributor", "admin"]))])
def delete_checking(
    id: int,
    db: Session = Depends(get_db),
    active_user: User = Depends(get_current_active_user),
):
    """
    Deletes a checking by its ID.

    Parameters:
        id (int): The ID of the checking to delete.
        db (Session): The database session.
        active_user (User, optional): The current active user.

    Returns:
        dict: A dictionary containing the detail that
            the checking with the given ID was deleted.

    Raises:
        HTTPException: If the checking with the given ID is not found.
        HTTPException: If the user does not have enough
            permissions to delete the checking.
        HTTPException: If there is an error while
            deleting the checking from the database.
    """
    checking = checking_crud.get_one(db, Checking.id == id)
    if checking is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Checking with id {id} not found. Cannot delete.",
        )
    if checking.user_id != active_user.id and not active_user.is_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user does not have enough privileges",
        )
    try:
        checking_crud.delete(db, checking)
    except Exception as e:  
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Couldn't delete checking with id {id}. Error: {str(e)}",
        ) from e