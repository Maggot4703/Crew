"""
traveller_agent.py
Unified interface for querying Traveller data from Travellermap API and Traveller Wiki.
"""

from typing import Any, Dict, Optional

from traveller_wiki_api import TravellerWikiAPI
from travellermap_api import TravellermapAPI


class TravellerAgent:
    def __init__(self):
        self.map_api = TravellermapAPI()
        self.wiki_api = TravellerWikiAPI()

    def get_world_info(
        self, world: str, sector: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Retrieve world info from Travellermap API and summary from Wiki.
        Args:
            world (str): World name.
            sector (str, optional): Sector name.
        Returns:
            dict: Combined info from both sources.
        """
        result = {"world": world, "sector": sector}
        map_data = self.map_api.get_world_info(world, sector)
        if map_data:
            result["map_data"] = map_data
        wiki_summary = self.wiki_api.get_page_summary(world)
        if wiki_summary:
            result["wiki_summary"] = wiki_summary
        return result

    def get_sector_info(self, sector: str) -> Dict[str, Any]:
        """
        Retrieve sector info from Travellermap API.
        Args:
            sector (str): Sector name.
        Returns:
            dict: Sector data.
        """
        return self.map_api.get_sector_info(sector) or {}

    def search_wiki(self, query: str) -> Dict[str, Any]:
        """
        Search the Traveller Wiki for a term.
        Args:
            query (str): Search term.
        Returns:
            dict: Search results.
        """
        return self.wiki_api.search(query) or {}
