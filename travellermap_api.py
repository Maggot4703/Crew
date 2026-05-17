"""
travellermap_api.py
Module for querying the Travellermap API for Traveller world and sector data.
"""

from typing import Any, Dict, Optional

import requests

BASE_URL = "https://travellermap.com/api"


class TravellermapAPI:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url

    def get_world_info(
        self, world: str, sector: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Query the Travellermap API for world information.
        Args:
            world (str): Name of the world (e.g., 'Regina').
            sector (str, optional): Name of the sector (e.g., 'Spinward Marches').
        Returns:
            dict or None: World data if found, else None.
        """
        params = {"name": world}
        if sector:
            params["sector"] = sector
        url = f"{self.base_url}/world"
        try:
            resp = requests.get(url, params=params, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"TravellermapAPI error: {e}")
            return None

    def get_sector_info(self, sector: str) -> Optional[Dict[str, Any]]:
        """
        Query the Travellermap API for sector information.
        Args:
            sector (str): Name of the sector.
        Returns:
            dict or None: Sector data if found, else None.
        """
        url = f"{self.base_url}/sec"
        params = {"sector": sector}
        try:
            resp = requests.get(url, params=params, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"TravellermapAPI error: {e}")
            return None

    def get_jumpworlds(
        self, world: str, sector: Optional[str] = None, jump: int = 2
    ) -> Optional[Dict[str, Any]]:
        """
        Query the Travellermap API for worlds within jump range.
        Args:
            world (str): Name of the world.
            sector (str, optional): Name of the sector.
            jump (int): Jump range (default 2).
        Returns:
            dict or None: Jumpworlds data if found, else None.
        """
        params = {"name": world, "jump": jump}
        if sector:
            params["sector"] = sector
        url = f"{self.base_url}/jumpworlds"
        try:
            resp = requests.get(url, params=params, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"TravellermapAPI error: {e}")
            return None
