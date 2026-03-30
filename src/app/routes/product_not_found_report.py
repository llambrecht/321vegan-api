from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.routes.dependencies import get_current_active_user
from app.crud.shop import shop_crud
from app.crud.product_not_found_report import product_not_found_report_crud
from app.database.db import get_db
from app.log import get_logger
from app.models import User
from app.schemas.product_not_found_report import ProductNotFoundReportCreate, ProductNotFoundReportOut

log = get_logger(__name__)

router = APIRouter(dependencies=[Depends(get_current_active_user)])


@router.post(
    "/",
    response_model=ProductNotFoundReportOut,
    status_code=status.HTTP_201_CREATED,
)
def report_product_not_found(
    report_in: ProductNotFoundReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ProductNotFoundReportOut:
    """
    Report that a product was not found at a shop.

    Limited to one report per user per (shop, ean) per day.

    Parameters:
        report_in (ProductNotFoundReportCreate): The report data (ean, shop_id).
        db (Session): The database session.
        current_user (User): The current authenticated user.

    Returns:
        ProductNotFoundReportOut: The created report.
    """
    shop = shop_crud.get_by_id(db, report_in.shop_id)
    if shop is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Shop not found"
        )

    if product_not_found_report_crud.has_reported_today(
        db, report_in.ean, report_in.shop_id, current_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already reported this product as not found at this shop today",
        )

    report_in.user_id = current_user.id
    report = product_not_found_report_crud.create(db, report_in)
    log.info(
        f"Product not found reported: EAN {report_in.ean} "
        f"at shop {report_in.shop_id} by user {current_user.id}"
    )
    return report
