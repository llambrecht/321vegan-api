from typing import Annotated, List, Optional, Tuple

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.routes.dependencies import get_current_active_user, get_pagination_params, get_sort_by_params, RoleChecker
from app.crud import additive_crud
from app.database.db import get_db
from app.log import get_logger
from app.models.additive import Additive
from app.schemas.additive import AdditiveCreate, AdditiveOut, AdditiveUpdate, AdditiveOutPaginated, AdditiveFilters

log = get_logger(__name__)

router = APIRouter(dependencies=[Depends(get_current_active_user)])


@router.get(
    "/", response_model=List[Optional[AdditiveOut]], status_code=status.HTTP_200_OK
)
def fetch_all_additives(db: Session = Depends(get_db)) -> List[Optional[AdditiveOut]]:
    """
    Fetch all additives.
    """
    additives = additive_crud.get_all(db)
    return additives


@router.get(
    "/search", response_model=Optional[AdditiveOutPaginated], status_code=status.HTTP_200_OK
)
def fetch_paginated_additives(
    db: Session = Depends(get_db),
    pagination_params: Tuple[int, int] = Depends(get_pagination_params),
    orderby_params: Tuple[str, bool] = Depends(get_sort_by_params),
    filter_params: AdditiveFilters = Depends()
) -> Optional[AdditiveOutPaginated]:
    """
    Fetch many additives.

    This function fetches all additives from the
    database based on the pagination parameters.

    Parameters:
        db (Session): The database session.
        pagination_params (Tuple[int, int]): The pagination parameters (skip, limit).
        orderby_params (Tuple[str, bool]): The order by parameters (sortby, descending).

    Returns:
        Optional[AdditiveOutPaginated]: The list of additive fetched from the database with pagination datas.
    """
    page, size = pagination_params
    sortby, descending = orderby_params
    additives, total = additive_crud.get_many(
        db,
        skip=page,
        limit=size,
        order_by=sortby,
        descending=descending,
        **filter_params.model_dump(exclude_none=True)
    )
    pages = (total + size - 1) // size
    return {
        "items": additives,
        "total": total,
        "page": page,
        "size": size,
        "pages": pages
    }


@router.get(
    "/{id}",
    response_model=Optional[AdditiveOut],
    status_code=status.HTTP_200_OK,
)
def fetch_additive_by_id(
    id: int, db: Session = Depends(get_db)
) -> AdditiveOut:
    """
    Fetches a additive by its ID.

    Parameters:
        id (int): The ID of the additive.
        db (Session): The database session.

    Returns:
        AdditiveOut: The fetched additive.

    Raises:
        HTTPException: If the additive is not found.
    """
    additive = additive_crud.get_one(db, Additive.id == id)
    if additive is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Additive with id {id} not found",
        )
    return additive


@router.post(
    "/",
    response_model=AdditiveOut,
    status_code=status.HTTP_201_CREATED,
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
)
def create_additive(
    additive_create: Annotated[
        AdditiveCreate,
        Body(
            examples=[
                {
                    "e_number": "E200",
                    "name": "Sorbic acid",
                    "description": "D'origine végétale",
                    "status": "VEGAN",
                    "source": "https://en.wikipedia.org/wiki/Sorbic_acid"
                }
            ]
        ),
    ],
    db: Session = Depends(get_db),
):
    """
    Create an additive.
    """
    try:
        additive = additive_crud.create(db, additive_create)
    except IntegrityError as e:
        error_message = str(e.orig)
        if "unique constraint" in error_message.lower() and "e_number" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Additive with e-number {additive_create.e_number} already exists",
            ) from e
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Data integrity error: {error_message}",
            ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Couldn't create additive. Error: {str(e)}",
        ) from e
    return additive


@router.put(
    "/{id}",
    response_model=AdditiveOut,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(RoleChecker(["contributor", "admin"]))]
)
def update_additive(
    id: int,
    additive_update: AdditiveUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a additive by its ID.

    Parameters:
        id (int): The ID of the additive to be updated.
        additive_update (AdditiveUpdate): The updated additive data.
        db (Session, optional): The database session.
            Defaults to Depends(get_db).

    Returns:
        AdditiveOut: The updated additive.

    Raises:
        HTTPException: If the additive does not exist or
            the user does not have enough permissions.
        HTTPException: If there is an error updating
            the additive in the database.
    """
    additive = additive_crud.get_one(db, Additive.id == id)
    if additive is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"additive with id {id} not found",
        )

    try:
        additive = additive_crud.update(db, additive, additive_update)
    except IntegrityError as e:
        error_message = str(e.orig)
        if "unique constraint" in error_message.lower() and "e_number" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Additive with e-number {additive_update.e_number} already exists",
            ) from e
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Data integrity error: {error_message}",
            ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Couldn't update additive with id {id}. Error: {str(e)}",
        ) from e
    return additive


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(RoleChecker(["contributor", "admin"]))])
def delete_additive(
    id: int,
    db: Session = Depends(get_db)
):
    """
    Deletes a additive by its ID.

    Parameters:
        id (int): The ID of the additive to delete.
        db (Session): The database session.

    Returns:
        dict: A dictionary containing the detail that
            the additive with the given ID was deleted.

    Raises:
        HTTPException: If the additive with the given ID is not found.
        HTTPException: If the user does not have enough
            permissions to delete the additive.
        HTTPException: If there is an error while
            deleting the additive from the database.
    """
    additive = additive_crud.get_one(db, Additive.id == id)
    if additive is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Additive with id {id} not found. Cannot delete.",
        )

    try:
        additive_crud.delete(db, additive)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Couldn't delete additive with id {id}. Error: {str(e)}",
        ) from e
