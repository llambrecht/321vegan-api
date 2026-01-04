from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from app.crud.base import CRUDRepository
from app.models.shop import Shop


class ShopCRUDRepository(CRUDRepository):
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
        # Haversine formula to calculate distance
        # Earth radius in meters
        earth_radius = 6371000
        
        # Convert radius to degrees (approximate)
        lat_range = radius_meters / 111320  # 1 degree latitude ≈ 111.32 km
        lon_range = radius_meters / (111320 * func.cos(func.radians(latitude)))
        
        # Find shops in the bounding box first (faster)
        shops = db.query(self._model).filter(
            self._model.latitude.between(latitude - lat_range, latitude + lat_range),
            self._model.longitude.between(longitude - lon_range, longitude + lon_range)
        ).all()
        
        # Calculate exact distance using Haversine formula for shops in bounding box
        for shop in shops:
            dlat = func.radians(shop.latitude - latitude)
            dlon = func.radians(shop.longitude - longitude)
            
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


shop_crud = ShopCRUDRepository(model=Shop)
