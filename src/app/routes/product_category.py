from typing import Annotated, List, Optional, Tuple

from fastapi import APIRouter, Body, Depends, HTTPException, UploadFile, status, File
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.routes.dependencies import get_current_active_user, get_pagination_params, get_sort_by_params, RoleChecker
from app.crud import product_category_crud
from app.database.db import get_db
from app.log import get_logger
from app.models import ProductCategory, User
from app.schemas.product_category import ProductCategoryCreate, ProductCategoryOut, ProductCategoryUpdate, ProductCategoryOutPaginated, ProductCategoryFilters

log = get_logger(__name__)

router = APIRouter(dependencies=[Depends(get_current_active_user)])


@router.get(
    "/", response_model=List[Optional[ProductCategoryOut]], status_code=status.HTTP_200_OK
)
def fetch_all_product_categories(db: Session = Depends(get_db)) -> List[Optional[ProductCategoryOut]]:
    """
    Fetch all product categories.

    This function fetches all product categories from the database.

    Parameters:
        db (Session): The database session.

    Returns:
        List[Optional[ProductCategoryOut]]: The list of product categories fetched from the database.
    """
    return product_category_crud.get_all(db)


@router.get(
    "/search", response_model=Optional[ProductCategoryOutPaginated], status_code=status.HTTP_200_OK
)
def fetch_paginated_product_categories(
    db: Session = Depends(get_db),
    pagination_params: Tuple[int, int] = Depends(get_pagination_params),
    orderby_params: Tuple[str, bool] = Depends(get_sort_by_params),
    filter_params: ProductCategoryFilters = Depends()
) -> Optional[ProductCategoryOutPaginated]:
    """
    Fetch many product categories with pagination.

    Parameters:
        db (Session): The database session.
        pagination_params (Tuple[int, int]): The pagination parameters (skip, limit).
        orderby_params (Tuple[str, bool]): The order by parameters (sortby, descending).

    Returns:
        ProductCategoryOutPaginated: The list of product categories with pagination data.
    """
    page, size = pagination_params
    sortby, descending = orderby_params
    categories, total = product_category_crud.get_many(
        db,
        skip=page,
        limit=size,
        order_by=sortby,
        descending=descending,
        **filter_params.model_dump(exclude_none=True)
    )
    pages = (total + size - 1) // size
    return {
        "items": categories,
        "total": total,
        "page": page,
        "size": size,
        "pages": pages
    }


@router.get(
    "/root", response_model=List[Optional[ProductCategoryOut]], status_code=status.HTTP_200_OK
)
def fetch_root_categories(db: Session = Depends(get_db)) -> List[Optional[ProductCategoryOut]]:
    """
    Fetch all root categories (categories without parent).

    Parameters:
        db (Session): The database session.

    Returns:
        List[Optional[ProductCategoryOut]]: The list of root categories.
    """
    return product_category_crud.get_root_categories(db)


@router.get(
    "/{id}",
    response_model=Optional[ProductCategoryOut],
    status_code=status.HTTP_200_OK,
)
def fetch_product_category_by_id(
    id: int, db: Session = Depends(get_db)
) -> ProductCategoryOut:
    """
    Fetches a product category by its ID.

    Parameters:
        id (int): The ID of the product category.
        db (Session): The database session.

    Returns:
        ProductCategoryOut: The fetched product category.

    Raises:
        HTTPException: If the product category is not found.
    """
    category = product_category_crud.get_one(db, ProductCategory.id == id)
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product category with id {id} not found",
        )
    return category


@router.get(
    "/{id}/children",
    response_model=List[Optional[ProductCategoryOut]],
    status_code=status.HTTP_200_OK,
)
def fetch_category_children(
    id: int, db: Session = Depends(get_db)
) -> List[Optional[ProductCategoryOut]]:
    """
    Fetches all child categories of a given category.

    Parameters:
        id (int): The ID of the parent category.
        db (Session): The database session.

    Returns:
        List[Optional[ProductCategoryOut]]: The list of child categories.

    Raises:
        HTTPException: If the parent category is not found.
    """
    parent = product_category_crud.get_one(db, ProductCategory.id == id)
    if parent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product category with id {id} not found",
        )
    return product_category_crud.get_children(db, id)


@router.post(
    "/",
    response_model=ProductCategoryOut,
    status_code=status.HTTP_201_CREATED,
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
    dependencies=[Depends(RoleChecker(["contributor", "admin"]))]
)
def create_product_category(
    category_create: Annotated[
        ProductCategoryCreate,
        Body(
            examples=[
                {
                    "name": "Beverages",
                    "parent_category_id": None,
                    "image": "https://example.com/beverages.jpg"
                }
            ]
        ),
    ],
    db: Session = Depends(get_db),
    active_user: User = Depends(get_current_active_user),
):
    """
    Create a product category.

    Parameters:
        category_create (ProductCategoryCreate): The product category data to be created.
        db (Session): The database session.
        active_user (User): The current active user.

    Returns:
        ProductCategoryOut: The created product category.

    Raises:
        HTTPException: If the parent category does not exist.
        HTTPException: If a category with the same name already exists.
        HTTPException: If there is an error creating the category.
    """

    try:
        category = product_category_crud.create(
            db, category_create
        )
    except IntegrityError as e:
        error_message = str(e.orig)
        if "unique constraint" in error_message.lower() and "name" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Product category with name {category_create.name} already exists",
            ) from e
        elif "foreign key constraint" in error_message.lower() and "parent_category_id" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product category with id {category_create.parent_category_id} does not exist",
            ) from e
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Data integrity error: {error_message}",
            ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Couldn't create product category. Error: {str(e)}",
        ) from e
    return category


@router.put(
    "/{id}",
    response_model=ProductCategoryOut,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(RoleChecker(["contributor", "admin"]))]
)
def update_product_category(
    id: int,
    category_update: ProductCategoryUpdate,
    db: Session = Depends(get_db),
    active_user: User = Depends(get_current_active_user),
):
    """
    Update a product category by its ID.

    Parameters:
        id (int): The ID of the product category to be updated.
        category_update (ProductCategoryUpdate): The updated category data.
        db (Session): The database session.
        active_user (User): The current active user.

    Returns:
        ProductCategoryOut: The updated product category.

    Raises:
        HTTPException: If the product category does not exist.
        HTTPException: If there is an error updating the category.
    """
    category = product_category_crud.get_one(db, ProductCategory.id == id)
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product category with id {id} not found",
        )

    try:
        # Check if parent category exists if provided
        if category_update.parent_category_id:
            parent = product_category_crud.get_one(
                db, ProductCategory.id == category_update.parent_category_id)
            if not parent:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Parent category with id {category_update.parent_category_id} does not exist",
                )

            # Prevent circular reference
            if category_update.parent_category_id == id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="A category cannot be its own parent",
                )

        # Check if new name already exists (if name is being updated)
        if category_update.name and category_update.name != category.name:
            existing = product_category_crud.get_by_name(
                db, category_update.name)
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Product category with name '{category_update.name}' already exists",
                )

        category = product_category_crud.update(db, category, category_update)
    except HTTPException:
        raise
    except IntegrityError as e:
        error_message = str(e.orig)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Data integrity error: {error_message}",
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Couldn't update product category with id {id}. Error: {str(e)}",
        ) from e
    return category


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(RoleChecker(["contributor", "admin"]))])
def delete_product_category(
    id: int,
    db: Session = Depends(get_db),
    active_user: User = Depends(get_current_active_user),
):
    """
    Deletes a product category by its ID.

    Parameters:
        id (int): The ID of the product category to delete.
        db (Session): The database session.
        active_user (User): The current active user.

    Raises:
        HTTPException: If the product category is not found.
        HTTPException: If there is an error while deleting the category.
    """
    category = product_category_crud.get_one(db, ProductCategory.id == id)
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product category with id {id} not found. Cannot delete.",
        )
    if category.nb_interesting_products > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Product category with name {category.name} currently used by at least one product",
        )
    try:
        product_category_crud.delete(db, category)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Couldn't delete product category with id {id}. Error: {str(e)}",
        ) from e

@router.post("/{category_id}/upload-image", response_model=ProductCategoryOut, status_code=status.HTTP_200_OK, dependencies=[Depends(RoleChecker(["contributor", "admin"]))])
def upload_product_category_image(
    *,
    db: Session = Depends(get_db),
    category_id: int,
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
    category = product_category_crud.get_one(db, ProductCategory.id == category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product category with id {category_id} not found"
        )
    
    try:
        # Save the file and get the path
        image_path = file_service.save_product_category_image(category_id, file)

        # Update the product with the new image path
        category_update = ProductCategoryUpdate(image=image_path)
        updated_category = product_category_crud.update(db, category, category_update)
        
        return updated_category
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading image: {str(e)}"
        ) from e