"""Region selection logic for optimal WorkSpace placement.

Requirements:
- 4.1: Geographic location detection
- 4.2: Lowest latency region selection
- 4.3: Region consistency for user
"""

import logging
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
import requests

logger = logging.getLogger(__name__)


@dataclass
class RegionInfo:
    """Information about an AWS region."""
    code: str
    name: str
    latitude: float
    longitude: float


class RegionSelector:
    """Selects optimal AWS region based on user location."""
    
    # AWS WorkSpaces supported regions with approximate coordinates
    SUPPORTED_REGIONS = {
        "us-east-1": RegionInfo("us-east-1", "US East (N. Virginia)", 38.13, -78.45),
        "us-west-2": RegionInfo("us-west-2", "US West (Oregon)", 45.52, -122.68),
        "ca-central-1": RegionInfo("ca-central-1", "Canada (Central)", 45.50, -73.57),
        "eu-west-1": RegionInfo("eu-west-1", "Europe (Ireland)", 53.35, -6.26),
        "eu-west-2": RegionInfo("eu-west-2", "Europe (London)", 51.51, -0.13),
        "eu-central-1": RegionInfo("eu-central-1", "Europe (Frankfurt)", 50.11, 8.68),
        "ap-southeast-1": RegionInfo("ap-southeast-1", "Asia Pacific (Singapore)", 1.35, 103.82),
        "ap-southeast-2": RegionInfo("ap-southeast-2", "Asia Pacific (Sydney)", -33.87, 151.21),
        "ap-northeast-1": RegionInfo("ap-northeast-1", "Asia Pacific (Tokyo)", 35.68, 139.65),
        "ap-northeast-2": RegionInfo("ap-northeast-2", "Asia Pacific (Seoul)", 37.57, 126.98),
        "sa-east-1": RegionInfo("sa-east-1", "South America (São Paulo)", -23.55, -46.63),
    }
    
    def __init__(self, default_region: str = "us-west-2"):
        """Initialize region selector.
        
        Args:
            default_region: Fallback region if detection fails
        """
        self.default_region = default_region
    
    def detect_location_from_ip(self, ip_address: str) -> Optional[Tuple[float, float]]:
        """Detect geographic location from IP address.
        
        Requirements:
        - Validates: Requirements 4.1 (Geographic location detection)
        
        Args:
            ip_address: User's IP address
            
        Returns:
            Tuple of (latitude, longitude) or None if detection fails
        """
        try:
            # Use ip-api.com for geolocation (free tier, no API key required)
            # In production, consider using AWS's own geolocation or a paid service
            response = requests.get(
                f"http://ip-api.com/json/{ip_address}",
                timeout=2
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    lat = data.get("lat")
                    lon = data.get("lon")
                    
                    logger.info(
                        "location_detected",
                        ip=ip_address,
                        latitude=lat,
                        longitude=lon,
                        city=data.get("city"),
                        country=data.get("country")
                    )
                    
                    return (lat, lon)
            
            logger.warning(
                f"location_detection_failed ip={ip_address} status_code={response.status_code}"
            )
            return None
            
        except Exception as e:
            logger.error(
                f"location_detection_error ip={ip_address} error={str(e)}"
            )
            return None
    
    def calculate_distance(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float
    ) -> float:
        """Calculate great circle distance between two points.
        
        Uses Haversine formula to calculate distance in kilometers.
        
        Args:
            lat1: Latitude of first point
            lon1: Longitude of first point
            lat2: Latitude of second point
            lon2: Longitude of second point
            
        Returns:
            Distance in kilometers
        """
        from math import radians, sin, cos, sqrt, atan2
        
        # Earth radius in kilometers
        R = 6371.0
        
        # Convert to radians
        lat1_rad = radians(lat1)
        lon1_rad = radians(lon1)
        lat2_rad = radians(lat2)
        lon2_rad = radians(lon2)
        
        # Haversine formula
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = sin(dlat / 2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2)**2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        
        distance = R * c
        return distance
    
    def select_optimal_region(
        self,
        user_location: Tuple[float, float],
        available_regions: Optional[List[str]] = None
    ) -> str:
        """Select AWS region with lowest latency to user location.
        
        Requirements:
        - Validates: Requirements 4.2 (Lowest latency region selection)
        - Validates: Requirements 4.3 (Region consistency)
        
        Args:
            user_location: Tuple of (latitude, longitude)
            available_regions: Optional list of region codes to consider
            
        Returns:
            AWS region code with lowest latency
        """
        if available_regions is None:
            available_regions = list(self.SUPPORTED_REGIONS.keys())
        
        user_lat, user_lon = user_location
        
        # Calculate distance to each region
        distances: Dict[str, float] = {}
        for region_code in available_regions:
            if region_code not in self.SUPPORTED_REGIONS:
                logger.warning(
                    "unsupported_region",
                    region=region_code
                )
                continue
            
            region_info = self.SUPPORTED_REGIONS[region_code]
            distance = self.calculate_distance(
                user_lat,
                user_lon,
                region_info.latitude,
                region_info.longitude
            )
            distances[region_code] = distance
        
        if not distances:
            logger.warning(
                "no_valid_regions",
                falling_back_to=self.default_region
            )
            return self.default_region
        
        # Select region with minimum distance
        optimal_region = min(distances.items(), key=lambda x: x[1])
        region_code, distance_km = optimal_region
        
        logger.info(
            "optimal_region_selected",
            region=region_code,
            distance_km=round(distance_km, 2),
            user_location={"lat": user_lat, "lon": user_lon}
        )
        
        return region_code
    
    def select_region_for_user(
        self,
        ip_address: str,
        available_regions: Optional[List[str]] = None
    ) -> str:
        """Select optimal region for user based on IP address.
        
        This is the main entry point for region selection.
        
        Requirements:
        - Validates: Requirements 4.1 (Geographic location detection)
        - Validates: Requirements 4.2 (Lowest latency region selection)
        
        Args:
            ip_address: User's IP address
            available_regions: Optional list of region codes to consider
            
        Returns:
            AWS region code
        """
        # Detect user location
        location = self.detect_location_from_ip(ip_address)
        
        if location is None:
            logger.warning(
                f"region_selection_fallback reason=location_detection_failed region={self.default_region}"
            )
            return self.default_region
        
        # Select optimal region
        return self.select_optimal_region(location, available_regions)
    
    def get_region_info(self, region_code: str) -> Optional[RegionInfo]:
        """Get information about a region.
        
        Args:
            region_code: AWS region code
            
        Returns:
            RegionInfo or None if region not supported
        """
        return self.SUPPORTED_REGIONS.get(region_code)
