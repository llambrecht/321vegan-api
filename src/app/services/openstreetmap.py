import random
import httpx
from typing import Dict, Any, List
from app.log import get_logger

log = get_logger(__name__)


class OpenStreetMapService:
    """Service to interact with OpenStreetMap Overpass API."""

    OVERPASS_API_URLS = [
        "https://overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter",
        "https://overpass.private.coffee/api/interpreter",
    ]
    OVERPASS_QUERY_TIMEOUT = 25  # seconds, server-side timeout
    TIMEOUT = 45.0  # seconds, HTTP client timeout

    @staticmethod
    async def find_nearby_shops(latitude: float, longitude: float, radius_meters: int = 100) -> List[Dict[str, Any]]:
        """
        Find all nearby shops using OpenStreetMap Overpass API, sorted by distance (closest first).

        Parameters:
            latitude (float): The latitude to search around.
            longitude (float): The longitude to search around.
            radius_meters (int): The search radius in meters (default 100).

        Returns:
            List[Dict[str, Any]]: List of shop data from OSM sorted by distance, or empty list if none found.
        """

        query = f"[out:json][timeout:{OpenStreetMapService.OVERPASS_QUERY_TIMEOUT}];(node(around:{radius_meters},{latitude},{longitude})[\"shop\"~\"^(supermarket|convenience|greengrocer|food|department_store|garden_centre)$\"];way(around:{radius_meters},{latitude},{longitude})[\"shop\"~\"^(supermarket|convenience|greengrocer|food|department_store|garden_centre)$\"];);out center;"

        # Shuffle to distribute load across endpoints rather than always trying the first one
        urls = OpenStreetMapService.OVERPASS_API_URLS.copy()
        random.shuffle(urls)

        last_error = None
        for url in urls:
            try:
                async with httpx.AsyncClient(timeout=OpenStreetMapService.TIMEOUT) as client:
                    response = await client.post(
                        url,
                        headers={"User-Agent": "321vegan-api/1.0 (contact@321vegan.fr)"},
                        data={"data": query}
                    )
                    response.raise_for_status()

                    data = response.json()
                    elements = data.get("elements", [])

                    if not elements:
                        return []

                    sorted_shops = OpenStreetMapService._sort_shops_by_distance(elements, latitude, longitude)

                    parsed_shops = []
                    for shop in sorted_shops:
                        parsed = OpenStreetMapService._parse_osm_shop(shop)
                        if parsed.get("latitude") and parsed.get("longitude"):
                            parsed_shops.append(parsed)
                        else:
                            log.warning(f"Shop from OSM has no valid coordinates: {shop.get('id')}")

                    return parsed_shops

            except httpx.HTTPError as e:
                last_error = e
                log.warning(f"Overpass API failed ({url}): {type(e).__name__}: {e}")
                continue
            except Exception as e:
                last_error = e
                log.warning(f"Overpass API failed ({url}): {type(e).__name__}: {e}")
                continue

        log.error(f"All Overpass API endpoints failed. Last error: {type(last_error).__name__}: {last_error}")
        return []
    
    @staticmethod
    def _sort_shops_by_distance(shops: list, target_lat: float, target_lon: float) -> List[Dict[str, Any]]:
        """
        Sort shops by distance from the target coordinates (closest first).

        Parameters:
            shops (list): List of shop elements from OSM.
            target_lat (float): Target latitude.
            target_lon (float): Target longitude.

        Returns:
            List[Dict[str, Any]]: Shops sorted by distance (closest first).
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

        shops_with_distance = []
        for shop in shops:
            lat, lon = get_shop_coords(shop)
            if lat is None or lon is None:
                continue
            distance = haversine_distance(target_lat, target_lon, lat, lon)
            shops_with_distance.append((distance, shop))

        shops_with_distance.sort(key=lambda x: x[0])
        return [shop for _, shop in shops_with_distance]
    
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
