"""
traveller_wiki_api.py
Module for querying the Traveller Wiki (MediaWiki API) for page summaries and content.
"""

from typing import Any, Dict, Optional

import requests

WIKI_API_URL = "https://wiki.travellerrpg.com/api.php"


class TravellerWikiAPI:
    def __init__(self, api_url: str = WIKI_API_URL):
        self.api_url = api_url

    def get_page_summary(self, title: str) -> Optional[str]:
        """
        Get the summary/intro of a wiki page by title.
        Args:
            title (str): Page title (e.g., 'Regina').
        Returns:
            str or None: Extracted summary if found, else None.
        """
        params = {
            "action": "query",
            "prop": "extracts",
            "exintro": True,
            "explaintext": True,
            "titles": title,
            "format": "json",
        }
        try:
            resp = requests.get(self.api_url, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            pages = data.get("query", {}).get("pages", {})
            for page in pages.values():
                extract = page.get("extract")
                if extract:
                    return extract.strip()
            return None
        except Exception as e:
            print(f"TravellerWikiAPI error: {e}")
            return None

    def search(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Search the wiki for a page title.
        Args:
            query (str): Search term.
        Returns:
            dict or None: Search results if found, else None.
        """
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "format": "json",
        }
        try:
            resp = requests.get(self.api_url, params=params, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"TravellerWikiAPI error: {e}")
            return None
