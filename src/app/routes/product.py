from typing import Annotated, List, Optional, Tuple

from fastapi import APIRouter, Body, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.routes.dependencies import get_current_active_user, get_pagination_params, get_sort_by_params, RoleChecker, get_current_active_user_or_client
from app.crud import product_crud
from app.crud.user import user_crud
from app.database.db import get_db
from app.log import get_logger
from app.models import Product, User
from app.models.product import ProductState

from app.schemas.product import ProductCreate, ProductOut, ProductUpdate, ProductOutPaginated, ProductOutCount, ProductFilters
from app.services.file_service import file_service

log = get_logger(__name__)

router = APIRouter()


@router.get(
    "/", response_model=List[Optional[ProductOut]], status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_active_user)]
)
def fetch_all_products(db: Session = Depends(get_db)) -> List[Optional[ProductOut]]:
    """
    Fetch all products.

    This function fetches all products from the
    database.

    Parameters:
        db (Session): The database session.

    Returns:
        List[Optional[ProductOut]]: The list of products fetched from the database.
    """
    return product_crud.get_all(db)

@router.get(
    "/count", response_model=Optional[ProductOutCount], status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_active_user)]
)
def fetch_count_products(
    db: Session = Depends(get_db),
    filter_params: ProductFilters = Depends(),
) -> Optional[ProductOutCount]:
    """
    Fetch how many products.

    This function fetches total product count from the
    database based on the filters parameters.

    Parameters:
        db (Session): The database session.
        filter_params (ProductFilters): The filters parameters.

    Returns:
        Optional[ProductOutCount]: The total count of products fetched from the database with filter datas.
    """
    total = product_crud.count(
        db,
        **filter_params.model_dump(exclude_none=True)
    )
    return {
        "total": total
    }

@router.get(
    "/search", response_model=Optional[ProductOutPaginated], status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_active_user)]
)
def fetch_paginated_products(
    db: Session = Depends(get_db),
    pagination_params: Tuple[int, int] = Depends(get_pagination_params),
    orderby_params: Tuple[str, bool] = Depends(get_sort_by_params),
    filter_params: ProductFilters = Depends(),
) -> Optional[ProductOutPaginated]:
    """
    Fetch many products.

    This function fetches all products from the
    database based on the pagination parameters.

    Parameters:
        db (Session): The database session.
        pagination_params (Tuple[int, int]): The pagination parameters (skip, limit).
        orderby_params (Tuple[str, bool]): The order by parameters (sortby, descending).

    Returns:
        Optional[ProductOutPaginated]: The list of products fetched from the database with pagination datas.
    """
    page, size = pagination_params
    sortby, descending = orderby_params
    products, total = product_crud.get_many(
        db, 
        skip=page, 
        limit=size, 
        order_by=sortby, 
        descending=descending,
        **filter_params.model_dump(exclude_none=True)
    )
    pages = (total + size - 1) // size
    return {
        "items": products,
        "total": total,
        "page": page,
        "size": size,
        "pages": pages
    }


@router.get(
    "/{id}",
    response_model=Optional[ProductOut],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(get_current_active_user)]
)
def fetch_product_by_id(
    id: int, db: Session = Depends(get_db)
) -> ProductOut:
    """
    Fetches a product by its ID.

    Parameters:
        id (int): The ID of the product.
        db (Session): The database session.

    Returns:
        ProductOut: The fetched product.

    Raises:
        HTTPException: If the product is not found.
    """
    product = product_crud.get_one(db, Product.id == id)
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {id} not found",
        )
    return product


@router.get("/ean/{ean}", response_model=ProductOut, status_code=status.HTTP_200_OK, dependencies=[Depends(get_current_active_user)])
def fetch_product_by_ean(ean: str, db: Session = Depends(get_db)):
    """
    Fetches a product from the database based on the provided ean.

    Parameters:
        ean (str): The ean of the product.
        db (Session, optional): The database session.
        Defaults to the result of calling `get_db`.

    Returns:
        ProductOut: The product object fetched from the database.

    Raises:
        HTTPException: If no product is found with the provided ean,
            an HTTP 404 Not Found exception is raised.
        HTTPException: If the user does not have enough
            permissions to access to this endpoint.
    """
    product = product_crud.get_product_by_ean(db, ean=ean)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Product with ean {ean} not found"
        )
    return product


@router.post(
    "/",
    response_model=ProductOut,
    status_code=status.HTTP_201_CREATED,
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
    dependencies=[Depends(get_current_active_user_or_client)]
)
def create_product(
    ean: str = Form(...),
    name: Optional[str] = Form(None),
    brand_id: Optional[int] = Form(None),
    user_id: Optional[int] = Form(None),
    photo: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    """
    Create a product.

    Parameters:
        ean (str): The EAN of the product.
        name (Optional[str]): The name of the product.
        brand_id (Optional[int]): The brand ID of the product.
        user_id (Optional[int]): The user ID of the user creating the product.
        photo (Optional[UploadFile]): The photo of the product.
        db (Session): The database session.

    Returns:
        ProductOut: The created product.
    """
    if user_id:
        user_crud.increment_products_sent(db, user_id)

    try:
        product_data_dict = {"ean": ean}
        if name:
            product_data_dict["name"] = name
        if brand_id:
            product_data_dict["brand_id"] = brand_id
        if user_id:
            product_data_dict["last_modified_by"] = user_id

        from app.schemas.product import ProductBase
        product_base = ProductBase(**product_data_dict)
        product = product_crud.create(db, product_base)

        if photo:
            photo_path = file_service.save_product_image(product.id, photo)
            product.photo = photo_path
            db.commit()
            db.refresh(product)

    except IntegrityError as e:
        error_message = str(e.orig)
        if "unique constraint" in error_message.lower() and "ean" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Product with EAN {ean} already exists",
            ) from e
        elif "foreign key constraint" in error_message.lower() and "brand_id" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Brand with id {brand_id} does not exist",
            ) from e
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Data integrity error: {error_message}",
            ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Couldn't create product. Error: {str(e)}",
        ) from e
    return product


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(RoleChecker(["contributor", "admin"]))])
def delete_product(
    id: int,
    db: Session = Depends(get_db)
):
    """
    Deletes a product by its ID.

    Parameters:
        id (int): The ID of the product to delete.
        db (Session): The database session.

    Returns:
        dict: A dictionary containing the detail that
            the product with the given ID was deleted.

    Raises:
        HTTPException: If the product with the given ID is not found.
        HTTPException: If the user does not have enough
            permissions to delete the product.
        HTTPException: If there is an error while
            deleting the product from the database.
    """
    product = product_crud.get_one(db, Product.id == id)
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {id} not found. Cannot delete.",
        )

    try:
        product_crud.delete(db, product)
    except Exception as e:  
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Couldn't delete product with id {id}. Error: {str(e)}",
        ) from e  
