from typing import Annotated, List, Optional, Tuple

from fastapi import APIRouter, Request, Body, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.routes.dependencies import get_current_active_user, get_current_superuser, get_pagination_params, get_sort_by_params, RoleChecker
from app.crud import brand_crud
from app.database.db import get_db
from app.log import get_logger
from app.models import Brand, User
from app.schemas.brand import BrandCreate, BrandOut, BrandUpdate, BrandOutPaginated, BrandFilters

log = get_logger(__name__)

router = APIRouter(dependencies=[Depends(get_current_active_user)])


@router.get(
    "/", response_model=List[Optional[BrandOut]], status_code=status.HTTP_200_OK
)
def fetch_all_brands(db: Session = Depends(get_db)) -> List[Optional[BrandOut]]:
    """
    Fetch all brands.

    This function fetches all brands from the
    database.

    Parameters:
        db (Session): The database session.

    Returns:
        BrandOut: The list of brands fetched from the database.
    """
    
    return brand_crud.get_all(db)


@router.get(
    "/search", response_model=Optional[BrandOutPaginated], status_code=status.HTTP_200_OK
)
def fetch_paginated_brands(
    db: Session = Depends(get_db),
    pagination_params: Tuple[int, int] = Depends(get_pagination_params),
    orderby_params: Tuple[str, bool] = Depends(get_sort_by_params),
    filter_params: BrandFilters = Depends()
) -> Optional[BrandOutPaginated]:
    """
    Fetch many brands.

    This function fetches all brands from the
    database based on the pagination parameters.

    Parameters:
        db (Session): The database session.
        pagination_params (Tuple[int, int]): The pagination parameters (skip, limit).
        orderby_params (Tuple[str, bool]): The order by parameters (sortby, descending).

    Returns:
        BrandOutPaginated: The list of brands fetched from the database with pagination datas.
    """
    page, size = pagination_params
    sortby, descending = orderby_params
    brands, total = brand_crud.get_many(
        db, 
        skip=page, 
        limit=size, 
        order_by=sortby, 
        descending=descending, 
        **filter_params.model_dump(exclude_none=True)
    )
    pages = (total + size - 1) // size
    return {
        "items": brands,
        "total": total,
        "page": page,
        "size": size,
        "pages": pages
    }


@router.get(
    "/{id}",
    response_model=Optional[BrandOut],
    status_code=status.HTTP_200_OK,
)
def fetch_brand_by_id(
    id: int, db: Session = Depends(get_db)
) -> BrandOut:
    """
    Fetches a brand by its ID.

    Parameters:
        id (int): The ID of the brand.
        db (Session): The database session.

    Returns:
        BrandOut: The fetched brand.

    Raises:
        HTTPException: If the brand is not found.
    """
    brand = brand_crud.get_one(db, Brand.id == id)
    if brand is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Brand with id {id} not found",
        )
    return brand


@router.post(
    "/",
    response_model=BrandOut,
    status_code=status.HTTP_201_CREATED,
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
    dependencies=[Depends(RoleChecker(["contributor", "admin"]))]
)
def create_brand(
    brand_create: Annotated[
        BrandCreate,
        Body(
            examples=[
                {
                    "name": "Brand name",
                    "parent_id": 1,
                }
            ]
        ),
    ],
    db: Session = Depends(get_db),
):
    """
    Create a brand.

    Parameters:
        brand_create (BrandCreate): The brand data to be created.
        db (Session, optional): The database session.
            Defaults to Depends(get_db).


    Returns:
        BrandOut: The created brand.

    Raises:
        HTTPException: If a brand with same ean provided exists.
        HTTPException: If there is an error creating
            the brand in the database.
    """
    try:
        brand = brand_crud.create(
            db, brand_create
        )
    except IntegrityError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Brand with name {brand_create.name} already exists",
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Couldn't create brand. Error: {str(e)}",
        ) from e 
    return brand


@router.put(
    "/{id}",
    response_model=BrandOut,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(RoleChecker(["contributor", "admin"]))]
)
def update_brand(
    id: int,
    brand_update: BrandUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a brand by its ID.

    Parameters:
        id (int): The ID of the brand to be updated.
        brand_update (BrandUpdate): The updated brand data.
        db (Session, optional): The database session.
            Defaults to Depends(get_db).

    Returns:
        BrandOut: The updated brand.

    Raises:
        HTTPException: If the brand does not exist or
            the user does not have enough permissions.
        HTTPException: If there is an error updating
            the brand in the database.
    """
    brand = brand_crud.get_one(db, Brand.id == id)
    if brand is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Brand with id {id} not found",
        )

    try:
        brand = brand_crud.update(db, brand, brand_update)
    except Exception as e:  
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Couldn't update brand with id {id}. Error: {str(e)}",
        ) from e  
    return brand


@router.delete("/{id}", response_model=dict, status_code=status.HTTP_200_OK, dependencies=[Depends(RoleChecker(["admin"]))])
def delete_brand(
    id: int,
    db: Session = Depends(get_db),
):
    """
    Deletes a brand by its ID.

    Parameters:
        id (int): The ID of the brand to delete.
        db (Session): The database session.

    Returns:
        dict: A dictionary containing the detail that
            the brand with the given ID was deleted.

    Raises:
        HTTPException: If the brand with the given ID is not found.
        HTTPException: If the user does not have enough
            permissions to delete the brand.
        HTTPException: If there is an error while
            deleting the brand from the database.
    """
    brand = brand_crud.get_one(db, Brand.id == id)
    if brand is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Brand with id {id} not found. Cannot delete.",
        )
    try:
        brand_crud.delete(db, brand)
    except Exception as e:  
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Couldn't delete brand with id {id}. Error: {str(e)}",
        ) from e  

    return {"detail": f"Brand with id {id} deleted."}