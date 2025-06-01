"""
Database Manager for Crew Management Application
==============================================

Handles data persistence, crew data storage, and group management.
"""

import json
import logging
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Setup logger for this module
logger = logging.getLogger(__name__)


class DatabaseManager:
    """Database manager for crew data persistence."""

    def __init__(self, db_file: str = "crew_data.db"):
        """Initialize database manager.

        Args:
            db_file: Database file name
        """
        self.db_file = Path(db_file)
        self.connection: Optional[sqlite3.Connection] = None
        self.init_database()

    def init_database(self) -> None:
        """Initialize database tables."""
        try:
            self.connection = sqlite3.connect(self.db_file)
            self.connection.row_factory = sqlite3.Row

            # Create tables
            cursor = self.connection.cursor()

            # Crew members table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS crew_members (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    rank TEXT,
                    department TEXT,
                    primary_skill TEXT,
                    secondary_skill TEXT,
                    experience INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )
            # Example: Create groups table (assuming it's needed based on get_all_groups, create_group)
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS groups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS group_members (
                    group_id INTEGER,
                    member_id INTEGER,
                    PRIMARY KEY (group_id, member_id),
                    FOREIGN KEY (group_id) REFERENCES groups (id) ON DELETE CASCADE,
                    FOREIGN KEY (member_id) REFERENCES crew_members (id) ON DELETE CASCADE
                )
                """
            )
            self.connection.commit()  # Commit table creation
        except sqlite3.Error as e:
            logger.error(f"Database initialization error: {e}")
            # Potentially re-raise or handle more gracefully
        except Exception as e:  # General fallback
            logger.error(f"An unexpected error occurred during database initialization: {e}")

    def add_crew_member(self, member_data: Dict[str, Any]) -> Optional[int]:
        """Add a new crew member.

        Args:
            member_data: Dictionary containing member information

        Returns:
            ID of the newly created member, or None if an error occurred.
        """
        if not self.connection:
            logger.error("Database connection is not available.")
            return None
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                """
                INSERT INTO crew_members (name, rank, department, primary_skill, secondary_skill, experience)
                VALUES (:name, :rank, :department, :primary_skill, :secondary_skill, :experience)
                """,
                member_data,
            )
            self.connection.commit()
            logger.info(f"Added crew member: {member_data.get('name')}")
            return cursor.lastrowid
        except sqlite3.Error as e:
            logger.error(f"Error adding crew member {member_data.get('name')}: {e}")
            return None
        except Exception as e:  # General fallback
            logger.error(f"An unexpected error occurred while adding crew member: {e}")
            return None

    def get_all_crew_members(self) -> List[Dict[str, Any]]:
        """Get all crew members.

        Returns:
            List of crew member dictionaries
        """
        if not self.connection:
            logger.error("Database connection is not available.")
            return []
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM crew_members")
            members = [dict(row) for row in cursor.fetchall()]
            return members
        except sqlite3.Error as e:
            logger.error(f"Error fetching all crew members: {e}")
            return []
        except Exception as e:  # General fallback
            logger.error(f"An unexpected error occurred while fetching all crew members: {e}")
            return []

    def create_group(
        self, name: str, description: str = "", member_ids: Optional[List[int]] = None
    ) -> Optional[int]:
        """Create a new group and optionally add members.

        Args:
            name: Group name
            description: Group description
            member_ids: List of member IDs to include in the group

        Returns:
            ID of the newly created group, or None if an error occurred.
        """
        if not self.connection:
            logger.error("Database connection is not available.")
            return None
        try:
            cursor = self.connection.cursor()
            cursor.execute(
                "INSERT INTO groups (name, description) VALUES (?, ?)",
                (name, description),
            )
            group_id = cursor.lastrowid
            if group_id and member_ids:
                for member_id in member_ids:
                    cursor.execute(
                        "INSERT INTO group_members (group_id, member_id) VALUES (?, ?)",
                        (group_id, member_id),
                    )
            self.connection.commit()
            logger.info(f"Created group '{name}' with ID: {group_id}")
            return group_id
        except sqlite3.IntegrityError as e:  # e.g., UNIQUE constraint failed for group name
            logger.error(f"Error creating group '{name}'. It might already exist: {e}")
            self.connection.rollback()  # Rollback if partial changes occurred
            return None
        except sqlite3.Error as e:
            logger.error(f"Error creating group '{name}': {e}")
            self.connection.rollback()
            return None
        except Exception as e:  # General fallback
            logger.error(f"An unexpected error occurred while creating group '{name}': {e}")
            if self.connection:  # Check if connection exists before rollback
                self.connection.rollback()
            return None

    def get_all_groups(self) -> List[Dict[str, Any]]:
        """Get all groups, including their members.

        Returns:
            List of group dictionaries, each potentially with a 'members' key.
        """
        if not self.connection:
            logger.error("Database connection is not available.")
            return []
        try:
            cursor = self.connection.cursor()
            # Get all groups
            cursor.execute("SELECT id, name, description FROM groups")
            groups_raw = cursor.fetchall()

            groups_list = []
            for group_row in groups_raw:
                group_dict = dict(group_row)
                # Get members for each group
                cursor.execute(
                    """
                    SELECT cm.id, cm.name, cm.rank 
                    FROM crew_members cm
                    JOIN group_members gm ON cm.id = gm.member_id
                    WHERE gm.group_id = ?
                    """,
                    (group_dict["id"],),
                )
                members = [dict(row) for row in cursor.fetchall()]
                group_dict["members"] = members
                groups_list.append(group_dict)
            return groups_list
        except sqlite3.Error as e:
            logger.error(f"Error fetching all groups: {e}")
            return []
        except Exception as e:  # General fallback
            logger.error(f"An unexpected error occurred while fetching all groups: {e}")
            return []

    def close(self) -> None:
        """Close database connection."""
        if self.connection:
            try:
                self.connection.close()
                logger.info("Database connection closed.")
            except sqlite3.Error as e:
                logger.error(f"Error closing database connection: {e}")
            except Exception as e:  # General fallback
                logger.error(f"An unexpected error occurred while closing the database connection: {e}")
            finally:
                self.connection = None
