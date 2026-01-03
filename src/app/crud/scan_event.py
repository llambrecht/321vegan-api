from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.crud.base import CRUDRepository
from app.models.scan_event import ScanEvent


class ScanEventCRUDRepository(CRUDRepository):
    def get_by_ean(self, db: Session, ean: str, limit: int = 100) -> list[ScanEvent]:
        """
        Get scan events by EAN.

        Parameters:
            db (Session): The database session.
            ean (str): The EAN of the product.
            limit (int): Maximum number of results to return.

        Returns:
            list[ScanEvent]: List of scan events for the given EAN.
        """
        return db.query(self._model).filter(
            self._model.ean == ean
        ).order_by(self._model.date_created.desc()).limit(limit).all()
    
    def get_by_user(self, db: Session, user_id: int, limit: int = 100) -> list[ScanEvent]:
        """
        Get scan events by user.

        Parameters:
            db (Session): The database session.
            user_id (int): The user ID.
            limit (int): Maximum number of results to return.

        Returns:
            list[ScanEvent]: List of scan events for the given user.
        """
        return db.query(self._model).filter(
            self._model.user_id == user_id
        ).order_by(self._model.date_created.desc()).limit(limit).all()
    
    def get_user_scan_summary(self, db: Session, user_id: int) -> list[dict]:
        """
        Get aggregated scan statistics for a user.
        Returns EANs with their scan counts.

        Parameters:
            db (Session): The database session.
            user_id (int): The user ID.

        Returns:
            list[dict]: List of {ean: str, scan_count: int} ordered by scan count desc.
        """
        result = db.query(
            self._model.ean,
            func.count(self._model.id).label('scan_count')
        ).filter(
            self._model.user_id == user_id
        ).group_by(
            self._model.ean
        ).order_by(
            func.count(self._model.id).desc()
        ).all()
        
        return [{"ean": row.ean, "scan_count": row.scan_count} for row in result]


scan_event_crud = ScanEventCRUDRepository(model=ScanEvent)
