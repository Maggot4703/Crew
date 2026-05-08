"""Simple story-search helpers for in-memory, JSON, and CSV sources."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


class StorySearch:
    """
    A class to perform searches for stories based on various criteria.

    Attributes:
        # connection: Database connection object (if using a DB).
        # story_data: In-memory representation of stories (if not using a DB).
    """

    def __init__(self, data_source=None):
        """
        Initialize the StorySearch engine.

        Args:
            data_source (str, optional): Path to the data source (e.g., database file)
                                         or an existing data structure.
        """
        self.story_data = self._load_stories(data_source)

    def _load_stories(self, data_source):
        """
        Load story data from the specified source.

        This is an internal method that would handle reading from a file,
        connecting to a database, or processing an in-memory structure.

        Args:
            data_source: The source of the story data.

        Returns:
            A structured representation of the stories (e.g., list of dicts).
        """
        if data_source is None:
            return []

        if isinstance(data_source, list):
            return [self._normalize_story(item) for item in data_source]

        if isinstance(data_source, dict):
            stories = data_source.get("stories", [])
            return [self._normalize_story(item) for item in stories]

        if isinstance(data_source, (str, Path)):
            path = Path(data_source)
            if not path.exists():
                return []
            if path.suffix.lower() == ".json":
                loaded = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    loaded = loaded.get("stories", [])
                if isinstance(loaded, list):
                    return [self._normalize_story(item) for item in loaded]
                return []
            if path.suffix.lower() == ".csv":
                with path.open("r", encoding="utf-8", newline="") as handle:
                    return [
                        self._normalize_story(row) for row in csv.DictReader(handle)
                    ]
        return []

    def _normalize_story(self, story: Any) -> dict[str, Any]:
        if not isinstance(story, dict):
            return {
                "title": str(story),
                "text": str(story),
                "characters": [],
                "themes": [],
            }

        normalized = dict(story)
        normalized.setdefault("title", "")
        normalized.setdefault("text", "")
        normalized["characters"] = self._normalize_list_field(
            normalized.get("characters", [])
        )
        normalized["themes"] = self._normalize_list_field(normalized.get("themes", []))
        return normalized

    @staticmethod
    def _normalize_list_field(value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return [str(item) for item in value]
        if isinstance(value, str):
            return [part.strip() for part in value.split(",") if part.strip()]
        return [str(value)]

    @staticmethod
    def _normalize_query(value: Any) -> str:
        if value is None:
            return ""
        return str(value).strip().lower()

    def find_by_keyword(self, keyword: str) -> list:
        """
        Find stories containing a specific keyword.

        Args:
            keyword (str): The keyword to search for.

        Returns:
            list: A list of stories (or story identifiers) matching the keyword.
        """
        query = self._normalize_query(keyword)
        if not query:
            return []
        return [
            story
            for story in self.story_data
            if query in story.get("text", "").lower()
            or query in story.get("title", "").lower()
        ]

    def find_by_character(self, character_name: str) -> list:
        """
        Find stories featuring a specific character.

        Args:
            character_name (str): The name of the character.

        Returns:
            list: A list of stories (or story identifiers) featuring the character.
        """
        query = self._normalize_query(character_name)
        if not query:
            return []
        return [
            story
            for story in self.story_data
            if any(query == character.lower() for character in story.get("characters", []))
        ]

    def find_by_theme(self, theme: str) -> list:
        """
        Find stories related to a specific theme.

        Args:
            theme (str): The theme to search for.

        Returns:
            list: A list of stories (or story identifiers) matching the theme.
        """
        query = self._normalize_query(theme)
        if not query:
            return []
        return [
            story
            for story in self.story_data
            if any(query == item.lower() for item in story.get("themes", []))
        ]


# Example Usage (if this script were to be run directly):
if __name__ == "__main__":
    # Assuming you have a data source, e.g., 'data/story_collection.csv'
    search_engine = StorySearch()

    keyword_stories = search_engine.find_by_keyword("dragon")
    print(f"Stories about dragons: {keyword_stories}")

    character_stories = search_engine.find_by_character("Gandalf")
    print(f"Stories featuring Gandalf: {character_stories}")

    theme_stories = search_engine.find_by_theme("adventure")
    print(f"Adventure stories: {theme_stories}")
