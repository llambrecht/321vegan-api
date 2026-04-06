from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from app.crud.base import CRUDRepository
from app.models.product_not_found_report import ProductNotFoundReport


class ProductNotFoundReportCRUDRepository(CRUDRepository):
    def has_reported_today(self, db: Session, ean: str, shop_id: int, user_id: int) -> bool:
        """
        Check if a user already reported this product as not found at this shop today.

        Parameters:
            db (Session): The database session.
            ean (str): The product EAN.
            shop_id (int): The shop ID.
            user_id (int): The user ID.

        Returns:
            bool: True if a report already exists for today.
        """
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        return db.query(self._model).filter(
            self._model.ean == ean,
            self._model.shop_id == shop_id,
            self._model.user_id == user_id,
            self._model.created_at >= today_start,
        ).first() is not None

    def get_reports_for_shop(self, db: Session, shop_id: int) -> List[ProductNotFoundReport]:
        """
        Get all not-found reports for a shop.

        Parameters:
            db (Session): The database session.
            shop_id (int): The shop ID.

        Returns:
            List[ProductNotFoundReport]: All reports for the shop.
        """
        return db.query(self._model).filter(
            self._model.shop_id == shop_id
        ).all()

    def get_reports_for_shop_ean(
        self, db: Session, shop_id: int, ean: str, after: Optional[datetime] = None
    ) -> List[ProductNotFoundReport]:
        """
        Get not-found reports for a specific product at a shop, optionally after a date.

        Parameters:
            db (Session): The database session.
            shop_id (int): The shop ID.
            ean (str): The product EAN.
            after (Optional[datetime]): Only return reports after this date.

        Returns:
            List[ProductNotFoundReport]: Matching reports.
        """
        query = db.query(self._model).filter(
            self._model.shop_id == shop_id,
            self._model.ean == ean,
        )
        if after:
            query = query.filter(self._model.created_at > after)
        return query.all()


product_not_found_report_crud = ProductNotFoundReportCRUDRepository(model=ProductNotFoundReport)
