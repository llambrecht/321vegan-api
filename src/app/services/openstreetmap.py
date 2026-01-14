import httpx
from typing import Optional, Dict, Any
from app.log import get_logger

log = get_logger(__name__)


class OpenStreetMapService:
    """Service to interact with OpenStreetMap Overpass API."""
    
    OVERPASS_API_URL = "https://overpass.kumi.systems/api/interpreter"
    TIMEOUT = 20.0  # seconds
    
    @staticmethod
    async def find_nearby_shop(latitude: float, longitude: float, radius_meters: int = 100) -> Optional[Dict[str, Any]]:
        """
        Find a nearby shop using OpenStreetMap Overpass API.
        
        Parameters:
            latitude (float): The latitude to search around.
            longitude (float): The longitude to search around.
            radius_meters (int): The search radius in meters (default 50).
            
        Returns:
            Optional[Dict[str, Any]]: Shop data from OSM, or None if not found.
        """
        
        query = f"[out:json][timeout:3600];(node(around:{radius_meters},{latitude},{longitude})[\"shop\"~\"^(supermarket|convenience|greengrocer|food)$\"];way(around:{radius_meters},{latitude},{longitude})[\"shop\"~\"^(supermarket|convenience|greengrocer|food)$\"];);out center;"
        
        try:
            async with httpx.AsyncClient(timeout=OpenStreetMapService.TIMEOUT) as client:
                response = await client.post(
                    OpenStreetMapService.OVERPASS_API_URL,
                    headers={"User-Agent": "321vegan-api/1.0 (contact@321vegan.fr)"},
                    data={"data": query}
                )
                response.raise_for_status()
                
                data = response.json()
                elements = data.get("elements", [])
                
                if not elements:
                    return None
                
                shop = OpenStreetMapService._find_closest_shop(elements, latitude, longitude)
                
                parsed_shop = OpenStreetMapService._parse_osm_shop(shop)
                
                # Validate that we have coordinates
                if not parsed_shop.get("latitude") or not parsed_shop.get("longitude"):
                    log.error(f"Shop from OSM has no valid coordinates: {shop.get('id')}")
                    return None
                
                return parsed_shop
                
        except httpx.HTTPError as e:
            log.error(f"Error calling Overpass API: {e}")
            return None
        except Exception as e:
            log.error(f"Unexpected error in find_nearby_shop: {e}")
            return None
    
    @staticmethod
    def _find_closest_shop(shops: list, target_lat: float, target_lon: float) -> Dict[str, Any]:
        """
        Find the closest shop from a list based on distance.
        
        Parameters:
            shops (list): List of shop elements from OSM.
            target_lat (float): Target latitude.
            target_lon (float): Target longitude.
            
        Returns:
            Dict[str, Any]: The closest shop.
        """
        import math
        
        def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
            """Calculate the great circle distance in meters between two points."""
            R = 6371000  # Earth radius in meters
            
            phi1 = math.radians(lat1)
            phi2 = math.radians(lat2)
            delta_phi = math.radians(lat2 - lat1)
            delta_lambda = math.radians(lon2 - lon1)
            
            a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
            
            return R * c
        
        def get_shop_coords(shop: Dict[str, Any]) -> tuple:
            """Extract coordinates from shop data."""
            if "lat" in shop and "lon" in shop:
                return shop["lat"], shop["lon"]
            elif "center" in shop:
                return shop["center"]["lat"], shop["center"]["lon"]
            return None, None
        
        closest_shop = None
        min_distance = float('inf')
        
        for shop in shops:
            lat, lon = get_shop_coords(shop)
            if lat is None or lon is None:
                continue
            
            distance = haversine_distance(target_lat, target_lon, lat, lon)
            if distance < min_distance:
                min_distance = distance
                closest_shop = shop
        
        return closest_shop if closest_shop else shops[0]
    
    @staticmethod
    def _parse_osm_shop(shop_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse OSM shop data into our shop format.
        
        Parameters:
            shop_data (Dict[str, Any]): Raw shop data from OSM.
            
        Returns:
            Dict[str, Any]: Parsed shop data.
        """
        tags = shop_data.get("tags", {})
        
        # Get coordinates (handle center for ways/relations)
        if "lat" in shop_data and "lon" in shop_data:
            lat = shop_data["lat"]
            lon = shop_data["lon"]
        elif "center" in shop_data:
            lat = shop_data["center"]["lat"]
            lon = shop_data["center"]["lon"]
        else:
            lat = None
            lon = None
        
        # Build address from OSM tags
        address_parts = []
        if "addr:housenumber" in tags:
            address_parts.append(tags["addr:housenumber"])
        if "addr:street" in tags:
            address_parts.append(tags["addr:street"])
        address = " ".join(address_parts) if address_parts else None
        
        name = tags.get("name") or tags.get("brand") or tags.get("name:fr") or tags.get("name:en") or "Magasin inconnu"
        return {
            "name": name,
            "latitude": lat,
            "longitude": lon,
            "address": address,
            "city": tags.get("addr:city"),
            "country": tags.get("addr:country"),
            "osm_id": str(shop_data.get("id")),
            "osm_type": shop_data.get("type"),  # node, way, or relation
            "shop_type": tags.get("shop", "supermarket"),
        }


osm_service = OpenStreetMapService()
