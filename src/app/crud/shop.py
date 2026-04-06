from typing import Optional, List, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct
from app.crud.base import CRUDRepository
from app.models.shop import Shop
from app.models.scan_event import ScanEvent
from app.models.product_not_found_report import ProductNotFoundReport
import math


class ShopCRUDRepository(CRUDRepository):
    def get_many(
        self, 
        db: Session, 
        *args, 
        skip: int = 0, 
        limit: int = 100, 
        order_by: str = 'created_at', 
        descending: bool = False, 
        filters: dict = None,
        **kwargs
    ) -> Tuple[List[Shop], int]:
        """
        Override get_many to handle eans filter specially.
        
        Parameters:
            db (Session): The database session.
            skip (int): Number of records to skip.
            limit (int): Maximum number of records to retrieve.
            order_by (str): Field name to order by.
            descending (bool): Sort direction.
            filters (dict): Filter parameters.
            
        Returns:
            Tuple[List[Shop], int]: List of shops and total count.
        """
        eans = None
        if filters and 'ean__in' in filters:
            eans = filters.pop('ean__in')

        if eans:
            shop_ids = self.get_shops_by_eans(db, eans)
            if not shop_ids:
                return [], 0
            filters = filters or {}
            filters['id__in'] = shop_ids
        
        return super().get_many(
            db,
            *args,
            skip=skip,
            limit=limit,
            order_by=order_by,
            descending=descending,
            **(filters or {}),
            **kwargs
        )
    
    def find_nearby(
        self, 
        db: Session, 
        latitude: float, 
        longitude: float, 
        radius_meters: int = 20
    ) -> Optional[Shop]:
        """
        Find a shop within a given radius using Haversine formula.
        
        Parameters:
            db (Session): The database session.
            latitude (float): The latitude to search around.
            longitude (float): The longitude to search around.
            radius_meters (int): The search radius in meters (default 20).
            
        Returns:
            Optional[Shop]: The nearest shop within radius, or None.
        """
        # Calculate distance using Haversine formula
        # https://en.wikipedia.org/wiki/Haversine_formula
        earth_radius = 6371000
        
        # Convert radius to degrees (approximate)
        lat_range = radius_meters / 111320 
        lon_range = radius_meters / (111320 * func.cos(func.radians(latitude)))
        
        # Find shops in the bounding box first (faster)
        shops = db.query(self._model).filter(
            self._model.latitude.between(latitude - lat_range, latitude + lat_range),
            self._model.longitude.between(longitude - lon_range, longitude + lon_range)
        ).all()
        
        # Calculate exact distance
        for shop in shops:
            a = (math.sin(math.radians(shop.latitude - latitude) / 2) ** 2 +
                 math.cos(math.radians(latitude)) * math.cos(math.radians(shop.latitude)) *
                 math.sin(math.radians(shop.longitude - longitude) / 2) ** 2)
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
            distance = earth_radius * c
            
            if distance <= radius_meters:
                return shop
        
        return None
    
    def find_all_nearby(
        self,
        db: Session,
        latitude: float,
        longitude: float,
        radius_meters: int = 100
    ) -> List[Shop]:
        """
        Find all shops within a given radius, sorted by distance (closest first).

        Parameters:
            db (Session): The database session.
            latitude (float): The latitude to search around.
            longitude (float): The longitude to search around.
            radius_meters (int): The search radius in meters (default 100).

        Returns:
            List[Shop]: Shops within radius sorted by distance.
        """
        earth_radius = 6371000

        lat_range = radius_meters / 111320
        lon_range = radius_meters / (111320 * func.cos(func.radians(latitude)))

        shops = db.query(self._model).filter(
            self._model.latitude.between(latitude - lat_range, latitude + lat_range),
            self._model.longitude.between(longitude - lon_range, longitude + lon_range)
        ).all()

        shops_with_distance = []
        for shop in shops:
            a = (math.sin(math.radians(shop.latitude - latitude) / 2) ** 2 +
                 math.cos(math.radians(latitude)) * math.cos(math.radians(shop.latitude)) *
                 math.sin(math.radians(shop.longitude - longitude) / 2) ** 2)
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
            distance = earth_radius * c

            if distance <= radius_meters:
                shops_with_distance.append((distance, shop))

        shops_with_distance.sort(key=lambda x: x[0])
        return [shop for _, shop in shops_with_distance]

    def get_by_osm_id(self, db: Session, osm_id: str) -> Optional[Shop]:
        """
        Get a shop by OpenStreetMap ID.
        
        Parameters:
            db (Session): The database session.
            osm_id (str): The OpenStreetMap ID.
            
        Returns:
            Optional[Shop]: The shop with the given OSM ID, or None.
        """
        return db.query(self._model).filter(self._model.osm_id == osm_id).first()
    
    def get_in_bounding_box(
        self,
        db: Session,
        min_lat: float,
        max_lat: float,
        min_lng: float,
        max_lng: float,
        limit: int = 300
    ) -> List[Shop]:
        """
        Get shops within a geographic bounding box.

        Parameters:
            db (Session): The database session.
            min_lat (float): Minimum latitude.
            max_lat (float): Maximum latitude.
            min_lng (float): Minimum longitude.
            max_lng (float): Maximum longitude.
            limit (int): Maximum number of shops to return (default 300).

        Returns:
            List[Shop]: List of shops within the bounding box.
        """
        return db.query(self._model).filter(
            self._model.latitude.between(min_lat, max_lat),
            self._model.longitude.between(min_lng, max_lng)
        ).limit(limit).all()

    def get_shop_scan_summary(self, db: Session, shop_id: int) -> List[dict]:
        """
        Get distinct EANs scanned at a shop with scan count, last scan date,
        not-found report stats, and a computed presence score.

        Only not-found reports that occurred AFTER the last scan for that EAN
        are considered relevant (a scan after a report proves restocking).

        Parameters:
            db (Session): The database session.
            shop_id (int): The shop ID.

        Returns:
            List[dict]: List of dicts with ean, scan_count, last_scanned_at,
                        not_found_count, last_not_found_at, presence_score.
        """
        from sqlalchemy import and_
        from sqlalchemy.dialects.postgresql import array_agg

        # Subquery 1: scan stats per EAN
        scan_subq = (
            db.query(
                ScanEvent.ean,
                func.count(ScanEvent.id).label("scan_count"),
                func.max(ScanEvent.date_created).label("last_scanned_at"),
            )
            .filter(ScanEvent.shop_id == shop_id)
            .group_by(ScanEvent.ean)
            .subquery()
        )

        # Subquery 2: not-found report stats per EAN, only reports after last scan
        report_subq = (
            db.query(
                ProductNotFoundReport.ean,
                func.count(ProductNotFoundReport.id).label("not_found_count"),
                func.max(ProductNotFoundReport.date_created).label("last_not_found_at"),
                array_agg(ProductNotFoundReport.date_created).label("report_dates"),
            )
            .join(
                scan_subq,
                and_(
                    scan_subq.c.ean == ProductNotFoundReport.ean,
                    ProductNotFoundReport.date_created > scan_subq.c.last_scanned_at,
                ),
            )
            .filter(ProductNotFoundReport.shop_id == shop_id)
            .group_by(ProductNotFoundReport.ean)
            .subquery()
        )

        # Join scan stats with report stats
        results = (
            db.query(
                scan_subq.c.ean,
                scan_subq.c.scan_count,
                scan_subq.c.last_scanned_at,
                func.coalesce(report_subq.c.not_found_count, 0).label("not_found_count"),
                report_subq.c.last_not_found_at,
                report_subq.c.report_dates,
            )
            .outerjoin(report_subq, report_subq.c.ean == scan_subq.c.ean)
            .order_by(scan_subq.c.last_scanned_at.desc())
            .all()
        )

        now = datetime.now()
        summaries = []

        for row in results:
            report_dates = [d for d in (row.report_dates or []) if d is not None]

            presence_score = self._compute_presence_score(
                now, row.last_scanned_at, row.scan_count, report_dates,
            )

            summaries.append({
                "ean": row.ean,
                "scan_count": row.scan_count,
                "last_scanned_at": row.last_scanned_at,
                "not_found_count": row.not_found_count,
                "last_not_found_at": row.last_not_found_at,
                "presence_score": round(presence_score, 2),
            })

        return summaries

    @staticmethod
    def _compute_presence_score(
        now: datetime,
        last_scanned_at: datetime,
        scan_count: int,
        report_dates: list[datetime],
    ) -> float:
        """
        Compute a presence score between 0.0 and 1.0.

        - Freshness (60%): decays linearly over 90 days since last scan.
        - Frequency (40%): scan count capped at 10.
        - Penalty: each relevant not-found report subtracts up to 0.2,
          decaying over 30 days.
        """
        days_since_scan = (now - last_scanned_at).total_seconds() / 86400
        freshness = max(0.0, min(1.0, 1.0 - days_since_scan / 90))
        frequency = max(0.0, min(1.0, scan_count / 10))

        penalty = 0.0
        for date in report_dates:
            days_ago = (now - date).total_seconds() / 86400
            penalty += 0.2 * max(0.0, 1.0 - days_ago / 30)

        return max(0.0, min(1.0, freshness * 0.6 + frequency * 0.4 - penalty))

    def get_shops_by_eans(self, db: Session, eans: List[str]) -> List[int]:
        """
        Get shop IDs that have products with the given EAN codes.
        
        Parameters:
            db (Session): The database session.
            eans (List[str]): List of EAN codes to search for.
            
        Returns:
            List[int]: List of shop IDs that have these products.
        """
        shop_ids = db.query(distinct(ScanEvent.shop_id)).filter(
            ScanEvent.shop_id.isnot(None),
            ScanEvent.ean.in_(eans)
        ).all()
        
        return [shop_id[0] for shop_id in shop_ids]


shop_crud = ShopCRUDRepository(model=Shop)
