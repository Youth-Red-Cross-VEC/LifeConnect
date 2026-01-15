import httpx
import re
from typing import List, Optional
import logging

from app.config import Settings

logger = logging.getLogger(__name__)


class DistanceService:
    """
    Service for calculating distances using Google Maps API.
    
    Used to sort donors by proximity to hospital.
    """

    def __init__(self, settings: Settings):
        self.api_key = settings.GOOGLE_MAPS_API_KEY
        self.base_url = settings.GOOGLE_MAPS_BASE_URL

    async def get_distance(
        self, start_location: str, end_location: str
    ) -> Optional[float]:
        """
        Calculate distance between two locations in kilometers.
        
        Args:
            start_location: Origin address
            end_location: Destination address
            
        Returns:
            Distance in km, or None on failure
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.base_url,
                    params={
                        "origins": start_location,
                        "destinations": end_location,
                        "key": self.api_key,
                    },
                    timeout=10.0,
                )

                if response.status_code != 200:
                    logger.warning(f"Google Maps API returned {response.status_code}")
                    return None

                data = response.json()

                if data.get("status") != "OK":
                    logger.warning(f"Google Maps API status: {data.get('status')}")
                    return None

                rows = data.get("rows", [])
                if not rows or not rows[0].get("elements"):
                    return None

                element = rows[0]["elements"][0]
                if element.get("status") != "OK":
                    return None

                distance_text = element.get("distance", {}).get("text", "")
                # Extract numeric value from "5.3 km" format
                match = re.findall(r"[\d.]+", distance_text)
                if match:
                    return float(match[0])

                return None

        except Exception as e:
            logger.error(f"Error calculating distance: {e}")
            return None

    async def sort_donors_by_distance(
        self,
        donors: List[dict],
        target_address: str,
    ) -> List[dict]:
        """
        Sort donors by distance from target address.
        
        Args:
            donors: List of donor dicts with 'address' field
            target_address: Hospital/target address
            
        Returns:
            Donors sorted by distance (closest first)
        """
        for donor in donors:
            donor_address = donor.get("address", "")
            distance = await self.get_distance(target_address, donor_address)
            donor["distance"] = distance if distance is not None else float("inf")

        return sorted(donors, key=lambda x: x.get("distance", float("inf")))

    async def get_nearby_donors(
        self,
        donors: List[dict],
        target_address: str,
        max_distance_km: float = 50.0,
    ) -> List[dict]:
        """
        Filter and sort donors within a maximum distance.
        
        Args:
            donors: List of donor dicts with 'address' field
            target_address: Hospital/target address
            max_distance_km: Maximum distance in kilometers
            
        Returns:
            Nearby donors sorted by distance
        """
        sorted_donors = await self.sort_donors_by_distance(donors, target_address)
        return [
            d for d in sorted_donors
            if d.get("distance", float("inf")) <= max_distance_km
        ]
