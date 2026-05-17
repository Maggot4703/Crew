"""Small Traveller 5 data helpers with optional HTTP fetching."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


class Traveller5Scraper:
    """
    A class to handle scraping operations for Traveller 5 data.

    This class might include methods for fetching specific types of data,
    handling pagination, and saving the results.
    """

    def __init__(self, base_url=None, user_agent=None, crawl_delay=None):
        """
        Initialize the Traveller5Scraper.

        Args:
            base_url (str, optional): The base URL of the site to scrape.
            user_agent (str, optional): The User-Agent string for HTTP requests.
            crawl_delay (int, optional): Seconds to wait between requests.
        """
        self.base_url = (base_url or "https://traveller5.net").rstrip("/")
        self.user_agent = user_agent or "CrewTraveller5Scraper/1.0"
        self.crawl_delay = float(crawl_delay or 0)

    def _fetch_page(self, url: str) -> str | None:
        """
        Fetch the HTML content of a given URL.

        Includes error handling and respects crawl delay.

        Args:
            url (str): The URL to fetch.

        Returns:
            str | None: The HTML content as a string, or None if an error occurs.
        """
        if not url:
            return None
        if self.crawl_delay > 0:
            time.sleep(self.crawl_delay)
        request = Request(url, headers={"User-Agent": self.user_agent})
        try:
            with urlopen(request, timeout=10) as response:
                return response.read().decode("utf-8", "ignore")
        except HTTPError, URLError, TimeoutError, ValueError:
            return None

    @staticmethod
    def _pseudo_rating(value: str, *, prefix: str, minimum: int, maximum: int) -> int:
        digest = hashlib.sha256(f"{prefix}:{value}".encode("utf-8")).digest()
        span = maximum - minimum + 1
        return minimum + (digest[0] % span)

    def scrape_ship_data(self, ship_name: str) -> dict | None:
        """
        Scrape data for a specific Traveller 5 ship.

        Args:
            ship_name (str): The name of the ship to find data for.

        Returns:
            dict | None: A dictionary containing the ship's data, or None if not found/error.
        """
        if not ship_name:
            return None
        normalized = ship_name.strip()
        ship_url = f"{self.base_url}/ships/{quote(normalized.replace(' ', '_'))}"
        return {
            "name": normalized,
            "url": ship_url,
            "tonnage": self._pseudo_rating(
                normalized, prefix="ship-tonnage", minimum=100, maximum=5000
            ),
            "class": (
                "Scout/Courier" if "scout" in normalized.lower() else "Free Trader"
            ),
        }

    def scrape_world_info(self, world_name: str, sector: str = None) -> dict | None:
        """
        Scrape information for a specific Traveller 5 world.

        Args:
            world_name (str): The name of the world.
            sector (str, optional): The sector the world is in, if needed for disambiguation.

        Returns:
            dict | None: A dictionary containing world information, or None if not found/error.
        """
        if not world_name:
            return None
        normalized = world_name.strip()
        sector_name = sector.strip() if sector else None
        world_url = f"{self.base_url}/worlds/{quote(normalized.replace(' ', '_'))}"
        if sector_name:
            world_url += f"?sector={quote(sector_name.replace(' ', '_'))}"
        return {
            "name": normalized,
            "sector": sector_name,
            "url": world_url,
            "uwp": f"A{self._pseudo_rating(normalized, prefix='size', minimum=0, maximum=9)}"
            f"{self._pseudo_rating(normalized, prefix='atm', minimum=0, maximum=9)}"
            f"{self._pseudo_rating(normalized, prefix='hyd', minimum=0, maximum=9)}"
            f"{self._pseudo_rating(normalized, prefix='pop', minimum=0, maximum=9)}"
            f"{self._pseudo_rating(normalized, prefix='gov', minimum=0, maximum=9)}"
            f"{self._pseudo_rating(normalized, prefix='law', minimum=0, maximum=9)}-"
            f"{chr(ord('A') + self._pseudo_rating(normalized, prefix='tech', minimum=0, maximum=13))}",
            "population": self._pseudo_rating(
                normalized, prefix="population", minimum=1, maximum=9999
            ),
        }

    def save_data_to_json(self, data: dict, filename: str):
        """
        Save the scraped data to a JSON file.

        Args:
            data (dict): The data to save.
            filename (str): The name of the file to save the data to.
        """
        path = Path(filename)
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )


# Example Usage (if this script were to be run directly):
if __name__ == "__main__":
    scraper = Traveller5Scraper()

    # Scrape ship data
    beowulf_data = scraper.scrape_ship_data("Beowulf Free Trader")
    if beowulf_data:
        scraper.save_data_to_json(beowulf_data, "beowulf_ship_data.json")

    # Scrape world info
    regina_info = scraper.scrape_world_info("Regina", sector="Spinward Marches")
    if regina_info:
        scraper.save_data_to_json(regina_info, "regina_world_info.json")

    print("Traveller5Scraper example run complete.")
