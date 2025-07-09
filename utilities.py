import os
import httpx
from typing import Optional, Tuple, List, Dict

async def geocode_location(location:str) -> Optional[Tuple[float, float]]:
    """
    Convert a location name to latitude and longitude by supplying it to the Nominatim geocoding service.
    
    Args:
        location (str): The name of the location to geocode.
    
    Returns:
        Optional[Tuple[float, float]]: A tuple containing latitude and longitude if successful, None otherwise.
    """
    base_url = "https://nominatim.openstreetmap.org/search"

    params = {
        "q": location,
        "format": "json",
    }
    
    headers = {
        "User-Agent": "ma-beach-agent/1.0"
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(base_url, params=params, headers=headers)
        response.raise_for_status()  # Raise an error for bad responses
        data = response.json()
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"])
        return None

async def get_tide_times(lat: float, lon: float) -> Optional[Dict[str, List]]:
    """
    Acquire tide times for a given latitude and longitude using the Marea API.
    
    Args:
        lat (float): Latitude of the location.
        lon (float): Longitude of the location.
    
    Returns:
        Optional[Dict[str, List]]: A dictionary containing tide times and heights if successful, None otherwise.
    """
    url = f"https://api.marea.ooo/v2/tides?duration=1440&interval=60&latitude={lat}&longitude={lon}&model=FES2014&datum=MSL"
    
    headers = {
        "User-Agent": "ma-beach-agent/1.0",
        "x-marea-api-token": os.environ["MAREA_API_TOKEN"] if "MAREA_API_TOKEN" in os.environ else None
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # Raise an error for bad responses
        data = response.json()
        if data and "extremes" in data and "heights" in data:
            return data
        return None