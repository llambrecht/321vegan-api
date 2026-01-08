from typing import Annotated, List, Optional, Tuple

from fastapi import APIRouter, Body, Depends, HTTPException, status, Query, File, UploadFile
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.routes.dependencies import get_current_active_user, get_current_active_user_or_client, get_pagination_params, get_sort_by_params, RoleChecker
from app.crud import interesting_product_crud, product_category_crud
from app.database.db import get_db
from app.log import get_logger
from app.models import InterestingProduct, User
from app.models.interesting_product import InterestingProductType
from app.schemas.interesting_product import InterestingProductCreate, InterestingProductOut, InterestingProductUpdate, InterestingProductOutPaginated, InterestingProductFilters

log = get_logger(__name__)

router = APIRouter()


@router.get(
    "/", response_model=List[Optional[InterestingProductOut]], status_code=status.HTTP_200_OK
)
def fetch_all_interesting_products(
    db: Session = Depends(get_db),
    current_user_or_client = Depends(get_current_active_user_or_client)
) -> List[Optional[InterestingProductOut]]:
    """
    Fetch all interesting products.

    This function fetches all interesting products from the database.

    Parameters:
        db (Session): The database session.

    Returns:
        List[Optional[InterestingProductOut]]: The list of interesting products fetched from the database.
    """
    return interesting_product_crud.get_all(db)


@router.get(
    "/search", response_model=Optional[InterestingProductOutPaginated], status_code=status.HTTP_200_OK
)
def fetch_paginated_interesting_products(
    db: Session = Depends(get_db),
    pagination_params: Tuple[int, int] = Depends(get_pagination_params),
    orderby_params: Tuple[str, bool] = Depends(get_sort_by_params),
    filter_params: InterestingProductFilters = Depends(),
    current_user_or_client = Depends(get_current_active_user_or_client)
) -> Optional[InterestingProductOutPaginated]:
    """
    Fetch many interesting products with pagination and filters.

    Parameters:
        db (Session): The database session.
        pagination_params (Tuple[int, int]): The pagination parameters (skip, limit).
        orderby_params (Tuple[str, bool]): The order by parameters (sortby, descending).
        filter_params (InterestingProductFilters): Optional filters (ean, type, category_id).

    Returns:
        InterestingProductOutPaginated: The list of interesting products with pagination data.
    """
    page, size = pagination_params
    sortby, descending = orderby_params
    products, total = interesting_product_crud.get_many(
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
    "/ean/{ean}",
    response_model=Optional[InterestingProductOut],
    status_code=status.HTTP_200_OK,
)
def fetch_interesting_product_by_ean(
    ean: str,
    db: Session = Depends(get_db),
    current_user_or_client = Depends(get_current_active_user_or_client)
) -> InterestingProductOut:
    """
    Fetches an interesting product by its EAN.

    Parameters:
        ean (str): The EAN of the product.
        db (Session): The database session.

    Returns:
        InterestingProductOut: The fetched interesting product.

    Raises:
        HTTPException: If the interesting product is not found.
    """
    product = interesting_product_crud.get_by_ean(db, ean)
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Interesting product with EAN {ean} not found",
        )
    return product


@router.get(
    "/{id}",
    response_model=Optional[InterestingProductOut],
    status_code=status.HTTP_200_OK,
)
def fetch_interesting_product_by_id(
    id: int,
    db: Session = Depends(get_db),
    current_user_or_client = Depends(get_current_active_user_or_client)
) -> InterestingProductOut:
    """
    Fetches an interesting product by its ID.

    Parameters:
        id (int): The ID of the interesting product.
        db (Session): The database session.

    Returns:
        InterestingProductOut: The fetched interesting product.

    Raises:
        HTTPException: If the interesting product is not found.
    """
    product = interesting_product_crud.get_one(db, InterestingProduct.id == id)
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Interesting product with id {id} not found",
        )
    return product


@router.post(
    "/",
    response_model=InterestingProductOut,
    status_code=status.HTTP_201_CREATED,
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
    dependencies=[Depends(RoleChecker(["contributor", "admin"]))]
)
def create_interesting_product(
    product_create: Annotated[
        InterestingProductCreate,
        Body(
            examples=[
                {
                    "ean": "1234567890123",
                    "type": "popular",
                    "category_id": 1
                }
            ]
        ),
    ],
    db: Session = Depends(get_db),
    active_user: User = Depends(get_current_active_user),
):
    """
    Create an interesting product.

    Parameters:
        product_create (InterestingProductCreate): The interesting product data to be created.
        db (Session): The database session.
        active_user (User): The current active user.

    Returns:
        InterestingProductOut: The created interesting product.

    Raises:
        HTTPException: If the category does not exist.
        HTTPException: If there is an error creating the product.
    """
    try:
        # Check if category exists
        category = product_category_crud.get_one(db, id=product_create.category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category with id {product_create.category_id} does not exist",
            )
        
        product = interesting_product_crud.create(db, product_create)
    except HTTPException:
        raise
    except IntegrityError as e:
        error_message = str(e.orig)
        if "foreign key constraint" in error_message.lower() and "category_id" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category with id {product_create.category_id} does not exist",
            ) from e
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Data integrity error: {error_message}",
            ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Couldn't create interesting product. Error: {str(e)}",
        ) from e 
    return product


@router.put(
    "/{id}",
    response_model=InterestingProductOut,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(RoleChecker(["contributor", "admin"]))]
)
def update_interesting_product(
    id: int,
    product_update: InterestingProductUpdate,
    db: Session = Depends(get_db),
    active_user: User = Depends(get_current_active_user),
):
    """
    Update an interesting product by its ID.

    Parameters:
        id (int): The ID of the interesting product to be updated.
        product_update (InterestingProductUpdate): The updated product data.
        db (Session): The database session.
        active_user (User): The current active user.

    Returns:
        InterestingProductOut: The updated interesting product.

    Raises:
        HTTPException: If the interesting product does not exist.
        HTTPException: If there is an error updating the product.
    """
    product = interesting_product_crud.get_one(db, InterestingProduct.id == id)
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Interesting product with id {id} not found",
        )
    
    try:
        # Check if category exists if being updated
        if product_update.category_id:
            category = product_category_crud.get_one(db, id=product_update.category_id)
            if not category:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Category with id {product_update.category_id} does not exist",
                )
        
        product = interesting_product_crud.update(db, product, product_update)
    except HTTPException:
        raise
    except IntegrityError as e:
        error_message = str(e.orig)
        if "foreign key constraint" in error_message.lower() and "category_id" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category with id {product_update.category_id} does not exist",
            ) from e
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Data integrity error: {error_message}",
            ) from e
    except Exception as e:  
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Couldn't update interesting product with id {id}. Error: {str(e)}",
        ) from e  
    return product


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(RoleChecker(["contributor", "admin"]))])
def delete_interesting_product(
    id: int,
    db: Session = Depends(get_db),
    active_user: User = Depends(get_current_active_user),
):
    """
    Deletes an interesting product by its ID.

    Parameters:
        id (int): The ID of the interesting product to delete.
        db (Session): The database session.
        active_user (User): The current active user.

    Raises:
        HTTPException: If the interesting product is not found.
        HTTPException: If there is an error while deleting the product.
    """
    product = interesting_product_crud.get_one(db, InterestingProduct.id == id)
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Interesting product with id {id} not found. Cannot delete.",
        )
    try:
        interesting_product_crud.delete(db, product)
    except Exception as e:  
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Couldn't delete interesting product with id {id}. Error: {str(e)}",
        ) from e


@router.post("/{product_id}/upload-image", response_model=InterestingProductOut, status_code=status.HTTP_200_OK, dependencies=[Depends(RoleChecker(["contributor", "admin"]))])
def upload_interesting_product_image(
    *,
    db: Session = Depends(get_db),
    product_id: int,
    file: UploadFile = File(..., description="Image du produit (JPG, PNG, WebP max 5MB)")
):
    """
    Upload an image for an interesting product.

    - **product_id**: ID of the interesting product
    - **file**: Image file (JPG, PNG, WebP, max 5MB)

    The file will be saved in `/uploads/interesting_products/` and the path will be updated in the database.
    """
    from app.services.file_service import file_service

    # Check if the product exists
    product = interesting_product_crud.get_one(db, InterestingProduct.id == product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Interesting product with id {product_id} not found"
        )
    
    try:
        # Save the file and get the path
        image_path = file_service.save_interesting_product_image(product_id, file)

        # Update the product with the new image path
        product_update = InterestingProductUpdate(image=image_path)
        updated_product = interesting_product_crud.update(db, product, product_update)
        
        return updated_product
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading image: {str(e)}"
        ) from e


@router.delete("/{product_id}/image", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(RoleChecker(["contributor", "admin"]))])
def delete_interesting_product_image(
    *,
    db: Session = Depends(get_db),
    product_id: int
):
    """
    Delete the image of an interesting product.

    - **product_id**: ID of the interesting product
    """
    from app.services.file_service import file_service

    # Check if the product exists
    product = interesting_product_crud.get_one(db, InterestingProduct.id == product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Interesting product with id {product_id} not found"
        )
    
    try:
        # Delete the physical file if it exists
        if product.image:
            file_service.delete_interesting_product_image(product.image)

        # Update the product to remove the image path
        product_update = InterestingProductUpdate(image=None)
        interesting_product_crud.update(db, product, product_update)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting image: {str(e)}"
        ) from e
