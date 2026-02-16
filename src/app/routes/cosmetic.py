from typing import Annotated, List, Optional, Tuple

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.routes.dependencies import get_current_active_user, get_pagination_params, get_sort_by_params, RoleChecker
from app.crud.cosmetic import cosmetic_crud
from app.database.db import get_db
from app.log import get_logger
from app.models.cosmetic import Cosmetic
from app.schemas.cosmetic import CosmeticCreate, CosmeticOut, CosmeticUpdate, CosmeticOutPaginated, CosmeticFilters

log = get_logger(__name__)

router = APIRouter(dependencies=[Depends(get_current_active_user)])


@router.get(
    "/", response_model=List[Optional[CosmeticOut]], status_code=status.HTTP_200_OK
)
def fetch_all_cosmetics(db: Session = Depends(get_db)) -> List[Optional[CosmeticOut]]:
    """
    Fetch all cosmetics.
    """
    cosmetics = cosmetic_crud.get_all(db)
    return cosmetics


@router.post(
    "/",
    response_model=CosmeticOut,
    status_code=status.HTTP_201_CREATED,
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
    dependencies=[Depends(RoleChecker(["contributor", "admin"]))]
)
def create_cosmetic(
    cosmetic_create: Annotated[
        CosmeticCreate,
        Body(
            examples=[
                {
                    "brand_name": "Avril",
                    "is_vegan": False,
                    "is_cruelty_free": True,
                    "description": "Most products are vegan but not all."
                }
            ]
        ),
    ],
    db: Session = Depends(get_db),
):
    """
    Create a cosmetic.
    """
    try:
        cosmetic = cosmetic_crud.create(db, cosmetic_create)
    except IntegrityError as e:
        error_message = str(e.orig)
        if "unique constraint" in error_message.lower() and "brand_name" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cosmetic with brand name {cosmetic_create.brand_name} already exists",
            ) from e
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Data integrity error: {error_message}",
            ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Couldn't create cosmetic. Error: {str(e)}",
        ) from e
    return cosmetic


@router.get(
    "/search", response_model=Optional[CosmeticOutPaginated], status_code=status.HTTP_200_OK
)
def fetch_paginated_cosmetics(
    db: Session = Depends(get_db),
    pagination_params: Tuple[int, int] = Depends(get_pagination_params),
    orderby_params: Tuple[str, bool] = Depends(get_sort_by_params),
    filter_params: CosmeticFilters = Depends()
) -> Optional[CosmeticOutPaginated]:
    """
    Fetch many cosmetics.

    This function fetches all cosmetics from the
    database based on the pagination parameters.

    Parameters:
        db (Session): The database session.
        pagination_params (Tuple[int, int]): The pagination parameters (skip, limit).
        orderby_params (Tuple[str, bool]): The order by parameters (sortby, descending).

    Returns:
        Optional[CosmeticOutPaginated]: The list of cosmetic fetched from the database with pagination datas.
    """
    page, size = pagination_params
    sortby, descending = orderby_params
    cosmetics, total = cosmetic_crud.get_many(
        db,
        skip=page,
        limit=size,
        order_by=sortby,
        descending=descending,
        **filter_params.model_dump(exclude_none=True)
    )
    pages = (total + size - 1) // size
    return {
        "items": cosmetics,
        "total": total,
        "page": page,
        "size": size,
        "pages": pages
    }


@router.get(
    "/{id}",
    response_model=Optional[CosmeticOut],
    status_code=status.HTTP_200_OK,
)
def fetch_cosmetic_by_id(
    id: int, db: Session = Depends(get_db)
) -> CosmeticOut:
    """
    Fetches a cosmetic by its ID.

    Parameters:
        id (int): The ID of the cosmetic.
        db (Session): The database session.

    Returns:
        CosmeticOut: The fetched cosmetic.

    Raises:
        HTTPException: If the cosmetic is not found.
    """
    cosmetic = cosmetic_crud.get_one(db, Cosmetic.id == id)
    if cosmetic is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cosmetic with id {id} not found",
        )
    return cosmetic


@router.put(
    "/{id}",
    response_model=CosmeticOut,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(RoleChecker(["contributor", "admin"]))]
)
def update_cosmetic(
    id: int,
    cosmetic_update: CosmeticUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a cosmetic by its ID.

    Parameters:
        id (int): The ID of the cosmetic to be updated.
        cosmetic_update (CosmeticUpdate): The updated cosmetic data.
        db (Session, optional): The database session.
            Defaults to Depends(get_db).

    Returns:
        CosmeticOut: The updated cosmetic.

    Raises:
        HTTPException: If the cosmetic does not exist or
            the user does not have enough permissions.
        HTTPException: If there is an error updating
            the cosmetic in the database.
    """
    cosmetic = cosmetic_crud.get_one(db, Cosmetic.id == id)
    if cosmetic is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"cosmetic with id {id} not found",
        )

    try:
        cosmetic = cosmetic_crud.update(db, cosmetic, cosmetic_update)
    except IntegrityError as e:
        error_message = str(e.orig)
        if "unique constraint" in error_message.lower() and "brand_name" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cosmetic with brand name {cosmetic_update.brand_name} already exists",
            ) from e
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Data integrity error: {error_message}",
            ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Couldn't update cosmetic with id {id}. Error: {str(e)}",
        ) from e
    return cosmetic


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(RoleChecker(["contributor", "admin"]))])
def delete_cosmetic(
    id: int,
    db: Session = Depends(get_db)
):
    """
    Deletes a cosmetic by its ID.

    Parameters:
        id (int): The ID of the cosmetic to delete.
        db (Session): The database session.

    Returns:
        dict: A dictionary containing the detail that
            the cosmetic with the given ID was deleted.

    Raises:
        HTTPException: If the cosmetic with the given ID is not found.
        HTTPException: If the user does not have enough
            permissions to delete the cosmetic.
        HTTPException: If there is an error while
            deleting the cosmetic from the database.
    """
    cosmetic = cosmetic_crud.get_one(db, Cosmetic.id == id)
    if cosmetic is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cosmetic with id {id} not found. Cannot delete.",
        )

    try:
        cosmetic_crud.delete(db, cosmetic)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Couldn't delete cosmetic with id {id}. Error: {str(e)}",
        ) from e
