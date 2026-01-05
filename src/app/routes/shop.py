from typing import List, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.routes.dependencies import get_current_active_user, get_pagination_params, get_sort_by_params, RoleChecker
from app.crud.shop import shop_crud
from app.database.db import get_db
from app.log import get_logger
from app.models import Shop, User
from app.schemas.shop import ShopCreate, ShopOut, ShopUpdate, ShopOutPaginated, ShopFilters

log = get_logger(__name__)

router = APIRouter(dependencies=[Depends(get_current_active_user)])


@router.get(
    "/", response_model=List[Optional[ShopOut]], status_code=status.HTTP_200_OK
)
def fetch_all_shops(db: Session = Depends(get_db)) -> List[Optional[ShopOut]]:
    """
    Fetch all shops.

    Parameters:
        db (Session): The database session.

    Returns:
        List[Optional[ShopOut]]: The list of shops fetched from the database.
    """
    return shop_crud.get_all(db)


@router.get(
    "/search", response_model=Optional[ShopOutPaginated], status_code=status.HTTP_200_OK
)
def fetch_paginated_shops(
    filter_params: ShopFilters = Depends(),
    db: Session = Depends(get_db),
    pagination_params: Tuple[int, int] = Depends(get_pagination_params),
    orderby_params: Tuple[str, bool] = Depends(get_sort_by_params),
) -> Optional[ShopOutPaginated]:
    """
    Fetch many shops with pagination and filters.

    Parameters:
        filter_params (ShopFilters): Filter parameters (name, city, country, shop_type, ean__in).
        db (Session): The database session.
        pagination_params (Tuple[int, int]): The pagination parameters (skip, limit).
        orderby_params (Tuple[str, bool]): The order by parameters (sortby, descending).

    Returns:
        ShopOutPaginated: The list of shops with pagination data.
    """
    page, size = pagination_params
    sortby, descending = orderby_params
    filters = filter_params.model_dump(exclude_none=True)
    shops, total = shop_crud.get_many(
        db, 
        skip=page, 
        limit=size, 
        order_by=sortby, 
        descending=descending,
        filters=filters
    )
    pages = (total + size - 1) // size
    return {
        "items": shops,
        "total": total,
        "page": page,
        "size": size,
        "pages": pages
    }


@router.get(
    "/{id}",
    response_model=Optional[ShopOut],
    status_code=status.HTTP_200_OK,
)
def fetch_shop_by_id(
    id: int, db: Session = Depends(get_db)
) -> ShopOut:
    """
    Fetches a shop by its ID.

    Parameters:
        id (int): The ID of the shop.
        db (Session): The database session.

    Returns:
        ShopOut: The shop fetched from the database.
    """
    shop = shop_crud.get_by_id(db, id)
    if shop is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Shop not found"
        )
    return shop


@router.post(
    "/", response_model=ShopOut, status_code=status.HTTP_201_CREATED
)
def create_shop(
    shop_in: ShopCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker(["admin"]))
) -> ShopOut:
    """
    Create a new shop.

    Parameters:
        shop_in (ShopCreate): The shop data.
        db (Session): The database session.
        current_user (User): The current authenticated user.

    Returns:
        ShopOut: The created shop.
    """
    try:
        shop = shop_crud.create(db, shop_in)
        log.info(f"Shop created: {shop.name} (ID: {shop.id})")
        return shop
    except IntegrityError as e:
        db.rollback()
        log.error(f"Error creating shop: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Shop with this OSM ID already exists"
        )


@router.put(
    "/{id}",
    response_model=ShopOut,
    status_code=status.HTTP_200_OK,
)
def update_shop(
    id: int,
    shop_in: ShopUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker(["admin"]))
) -> ShopOut:
    """
    Update a shop.

    Parameters:
        id (int): The ID of the shop.
        shop_in (ShopUpdate): The updated shop data.
        db (Session): The database session.
        current_user (User): The current authenticated user.

    Returns:
        ShopOut: The updated shop.
    """
    shop = shop_crud.get_by_id(db, id)
    if shop is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Shop not found"
        )
    
    try:
        updated_shop = shop_crud.update(db, shop, shop_in)
        log.info(f"Shop updated: {updated_shop.name} (ID: {updated_shop.id})")
        return updated_shop
    except IntegrityError as e:
        db.rollback()
        log.error(f"Error updating shop: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error updating shop"
        )


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_shop(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker(["admin"]))
) -> None:
    """
    Delete a shop.

    Parameters:
        id (int): The ID of the shop.
        db (Session): The database session.
        current_user (User): The current authenticated user.
    """
    shop = shop_crud.get_by_id(db, id)
    if shop is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Shop not found"
        )
    
    shop_crud.delete(db, shop)
    log.info(f"Shop deleted: ID {id}")
