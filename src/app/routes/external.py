from typing import Annotated, List, Optional, Tuple

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.routes.dependencies import get_current_active_client
from app.crud import product_crud
from app.database.db import get_db
from app.log import get_logger
from app.models import Product

from app.schemas.product import ProductCreate, ProductOut

log = get_logger(__name__)

router = APIRouter(dependencies=[Depends(get_current_active_client)])

@router.post(
    "/products/",
    response_model=ProductOut,
    status_code=status.HTTP_201_CREATED,
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
)
def create_product(
    product_create: Annotated[
        ProductCreate,
        Body(
            examples=[
                {
                    "ean": "1234567890",
                }
            ]
        ),
    ],
    db: Session = Depends(get_db),
):
    """
    Create a product from api key auth.

    Parameters:
        product_create (ProductCreate): The product data to be created.
        db (Session, optional): The database session.
            Defaults to Depends(get_db).

    Returns:
        ProductOut: The created product.

    Raises:
        HTTPException: If a product with same ean provided exists.
        HTTPException: If there is an error creating
            the product in the database.
    """
    try:
        product = product_crud.create(
            db, product_create
        )
    except IntegrityError as e:
        error_message = str(e.orig)
        if "unique constraint" in error_message.lower() and "ean" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Product with EAN {product_create.ean} already exists",
            ) from e
        elif "foreign key constraint" in error_message.lower() and "brand_id" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Brand with id {product_create.brand_id} does not exist",
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
