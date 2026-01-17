from typing import Annotated, List, Optional, Tuple

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.routes.dependencies import get_current_active_user, get_pagination_params, get_sort_by_params, RoleChecker
from app.crud import household_cleaner_crud
from app.database.db import get_db
from app.log import get_logger
from app.models.household_cleaner import HouseholdCleaner
from app.schemas.household_cleaner import HouseholdCleanerCreate, HouseholdCleanerOut, HouseholdCleanerUpdate, HouseholdCleanerOutPaginated, HouseholdCleanerFilters

log = get_logger(__name__)

router = APIRouter(dependencies=[Depends(get_current_active_user)])


@router.get(
    "/", response_model=List[Optional[HouseholdCleanerOut]], status_code=status.HTTP_200_OK
)
def fetch_all_household_cleaners(db: Session = Depends(get_db)) -> List[Optional[HouseholdCleanerOut]]:
    """
    Fetch all household_cleaners.
    """
    household_cleaners = household_cleaner_crud.get_all(db)
    return household_cleaners


@router.post(
    "/",
    response_model=HouseholdCleanerOut,
    status_code=status.HTTP_201_CREATED,
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
)
def create_household_cleaner(
    household_cleaner_create: Annotated[
        HouseholdCleanerCreate,
        Body(
            examples=[
                {
                    "brand_name": "Ecover",
                    "is_vegan": False,
                    "is_cruelty_free": True,
                    "description": "Most products are vegan but not all.",
                    "source": "https://mysource/"
                }
            ]
        ),
    ],
    db: Session = Depends(get_db),
):
    """
    Create a household cleaner.
    """
    try:
        household_cleaner = household_cleaner_crud.create(
            db, household_cleaner_create)
    except IntegrityError as e:
        error_message = str(e.orig)
        if "unique constraint" in error_message.lower() and "brand_name" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"HouseholdCleaner with brand name {household_cleaner_create.brand_name} already exists",
            ) from e
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Data integrity error: {error_message}",
            ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Couldn't create household cleaner. Error: {str(e)}",
        ) from e
    return household_cleaner


@router.get(
    "/search", response_model=Optional[HouseholdCleanerOutPaginated], status_code=status.HTTP_200_OK
)
def fetch_paginated_household_cleaners(
    db: Session = Depends(get_db),
    pagination_params: Tuple[int, int] = Depends(get_pagination_params),
    orderby_params: Tuple[str, bool] = Depends(get_sort_by_params),
    filter_params: HouseholdCleanerFilters = Depends()
) -> Optional[HouseholdCleanerOutPaginated]:
    """
    Fetch many household cleaners.

    This function fetches all household cleaners from the
    database based on the pagination parameters.

    Parameters:
        db (Session): The database session.
        pagination_params (Tuple[int, int]): The pagination parameters (skip, limit).
        orderby_params (Tuple[str, bool]): The order by parameters (sortby, descending).

    Returns:
        Optional[HouseholdCleanerOutPaginated]: The list of household cleaner fetched from the database with pagination datas.
    """
    page, size = pagination_params
    sortby, descending = orderby_params
    household_cleaners, total = household_cleaner_crud.get_many(
        db,
        skip=page,
        limit=size,
        order_by=sortby,
        descending=descending,
        **filter_params.model_dump(exclude_none=True)
    )
    pages = (total + size - 1) // size
    return {
        "items": household_cleaners,
        "total": total,
        "page": page,
        "size": size,
        "pages": pages
    }


@router.get(
    "/{id}",
    response_model=Optional[HouseholdCleanerOut],
    status_code=status.HTTP_200_OK,
)
def fetch_household_cleaner_by_id(
    id: int, db: Session = Depends(get_db)
) -> HouseholdCleanerOut:
    """
    Fetches a household cleaner by its ID.

    Parameters:
        id (int): The ID of the household cleaner.
        db (Session): The database session.

    Returns:
        HouseholdCleanerOut: The fetched household cleaner.

    Raises:
        HTTPException: If the household cleaner is not found.
    """
    household_cleaner = household_cleaner_crud.get_one(
        db, HouseholdCleaner.id == id)
    if household_cleaner is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"HouseholdCleaner with id {id} not found",
        )
    return household_cleaner


@router.put(
    "/{id}",
    response_model=HouseholdCleanerOut,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(RoleChecker(["contributor", "admin"]))]
)
def update_household_cleaner(
    id: int,
    household_cleaner_update: HouseholdCleanerUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a household cleaner by its ID.

    Parameters:
        id (int): The ID of the household cleaner to be updated.
        household_cleaner_update (HouseholdCleanerUpdate): The updated household cleaner data.
        db (Session, optional): The database session.
            Defaults to Depends(get_db).

    Returns:
        HouseholdCleanerOut: The updated household cleaner.

    Raises:
        HTTPException: If the household cleaner does not exist or
            the user does not have enough permissions.
        HTTPException: If there is an error updating
            the household cleaner in the database.
    """
    household_cleaner = household_cleaner_crud.get_one(
        db, HouseholdCleaner.id == id)
    if household_cleaner is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"household cleaner with id {id} not found",
        )

    try:
        household_cleaner = household_cleaner_crud.update(
            db, household_cleaner, household_cleaner_update)
    except IntegrityError as e:
        error_message = str(e.orig)
        if "unique constraint" in error_message.lower() and "brand_name" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"HouseholdCleaner with brand name {household_cleaner_update.brand_name} already exists",
            ) from e
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Data integrity error: {error_message}",
            ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Couldn't update household cleaner with id {id}. Error: {str(e)}",
        ) from e
    return household_cleaner


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(RoleChecker(["contributor", "admin"]))])
def delete_household_cleaner(
    id: int,
    db: Session = Depends(get_db)
):
    """
    Deletes a household cleaner by its ID.

    Parameters:
        id (int): The ID of the household cleaner to delete.
        db (Session): The database session.

    Returns:
        dict: A dictionary containing the detail that
            the household cleaner with the given ID was deleted.

    Raises:
        HTTPException: If the household cleaner with the given ID is not found.
        HTTPException: If the user does not have enough
            permissions to delete the household cleaner.
        HTTPException: If there is an error while
            deleting the household cleaner from the database.
    """
    household_cleaner = household_cleaner_crud.get_one(
        db, HouseholdCleaner.id == id)
    if household_cleaner is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"HouseholdCleaner with id {id} not found. Cannot delete.",
        )

    try:
        household_cleaner_crud.delete(db, household_cleaner)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Couldn't delete household cleaner with id {id}. Error: {str(e)}",
        ) from e
