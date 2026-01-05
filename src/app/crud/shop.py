from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, distinct
from app.crud.base import CRUDRepository
from app.models.shop import Shop
from app.models.scan_event import ScanEvent


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
            ean_string = filters.pop('ean__in')
            eans = [ean.strip() for ean in ean_string.split(',')]
        
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
            filters=filters,
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
            import math
            a = (math.sin(math.radians(shop.latitude - latitude) / 2) ** 2 +
                 math.cos(math.radians(latitude)) * math.cos(math.radians(shop.latitude)) *
                 math.sin(math.radians(shop.longitude - longitude) / 2) ** 2)
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
            distance = earth_radius * c
            
            if distance <= radius_meters:
                return shop
        
        return None
    
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
