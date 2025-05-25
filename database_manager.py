"""
Manages database interactions for the application.

This module provides an abstraction layer for database operations,
including connecting to the database, executing queries (CRUD operations),
and managing transactions. It aims to decouple the rest of the application
from the specific database technology being used.
"""

import logging
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd

from errors import DatabaseError


class DatabaseManager:
    """
    A class to manage database connections and operations.

    Attributes:
        db_path (str): The path to the SQLite database file.
        connection (sqlite3.Connection): The active database connection.
        cursor (sqlite3.Cursor): The database cursor for executing queries.
    """

    SCHEMA_VERSION = "1.0"

    def __init__(self, db_path="crew_data.db"):
        """
        Initialize the DatabaseManager and connect to the database.

        Args:
            db_path (str): The path to the SQLite database file.
                           Defaults to 'crew_data.db'.
        """
        self.db_name = db_path
        self.conn = None
        self.setup_logging()
        self.validation_rules = {}

    def setup_logging(self) -> None:
        """Configure logging for database operations"""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            filename="database.log",
        )
        self.logger = logging.getLogger("DatabaseManager")

    def __enter__(self):
        """Context manager entry"""
        try:
            self.conn = sqlite3.connect(self.db_name)
            self.conn.row_factory = sqlite3.Row
            self._initialize_database()
            return self
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            raise DatabaseError(f"Database initialization failed: {e}")

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if self.conn:
            try:
                if exc_type:
                    self.conn.rollback()
                else:
                    self.conn.commit()
            finally:
                self.conn.close()
                # Ensure database file is removed
                Path(self.db_name).unlink(missing_ok=True)

    def load_data(
        self, filename: str
    ) -> Tuple[List[str], List[Any], Dict[str, List[Any]]]:
        """Load data from CSV file with error handling and validation"""
        try:
            if not Path(filename).exists():
                raise DatabaseError(f"File not found: {filename}")

            data = pd.read_csv(filename)
            headers = list(data.columns)
            rows = data.values.tolist()

            # Validate data
            errors = self.validate_data("crew", data)
            if errors:
                self.logger.warning(f"Data validation warnings: {errors}")

            # Group data by relevant columns (e.g., by role, squad, etc.)
            groups = {}
            if "Role" in data.columns:
                for role in data["Role"].unique():
                    if pd.notna(role):
                        groups[role] = data[data["Role"] == role].values.tolist()

            return headers, rows, groups

        except Exception as e:
            self.logger.error(f"Failed to load data from {filename}: {e}")
            raise DatabaseError(f"Failed to load data: {e}")

    def save_data(self, filename: str, headers: list, data: list) -> bool:
        """Save data to CSV file"""
        try:
            df = pd.DataFrame(data, columns=headers)
            df.to_csv(filename, index=False)
            return True
        except Exception as e:
            logging.error(f"Error saving data: {e}")
            return False

    def export_data(self, filename: str, headers: list, data: list) -> bool:
        """Export data to Excel file"""
        try:
            df = pd.DataFrame(data, columns=headers)
            df.to_excel(filename, index=False)
            return True
        except Exception as e:
            logging.error(f"Error exporting data: {e}")
            return False

    def add_validation_rule(
        self, table: str, column: str, rule_type: str, rule_value: Any
    ) -> None:
        """Add a validation rule for a specific column"""
        if table not in self.validation_rules:
            self.validation_rules[table] = {}
        if column not in self.validation_rules[table]:
            self.validation_rules[table][column] = []

        self.validation_rules[table][column].append(
            {"type": rule_type, "value": rule_value}
        )

    def validate_data(self, table: str, data: pd.DataFrame) -> List[str]:
        """Validate data against defined rules"""
        errors = []
        if table in self.validation_rules:
            for column, rules in self.validation_rules[table].items():
                if column in data.columns:
                    for rule in rules:
                        if rule["type"] == "not_null":
                            null_values = data[column].isnull()
                            if null_values.any():
                                errors.append(f"Column {column} contains null values")
                        elif rule["type"] == "unique":
                            duplicates = data[column].duplicated()
                            if duplicates.any():
                                errors.append(
                                    f"Column {column} contains duplicate values"
                                )
                        elif rule["type"] == "range":
                            min_val, max_val = rule["value"]
                            out_of_range = (data[column] < min_val) | (
                                data[column] > max_val
                            )
                            if out_of_range.any():
                                errors.append(
                                    f"Column {column} contains values outside range [{min_val}, {max_val}]"
                                )
        return errors

    def _initialize_database(self) -> None:
        """Initialize database schema and version control"""
        try:
            cursor = self.conn.cursor()

            # Create schema_version table if it doesn't exist
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_version (
                    version TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Check current schema version
            cursor.execute(
                "SELECT version FROM schema_version ORDER BY created_at DESC LIMIT 1"
            )
            result = cursor.fetchone()

            if not result:
                # First time initialization
                cursor.execute(
                    "INSERT INTO schema_version (version) VALUES (?)",
                    (self.SCHEMA_VERSION,),
                )
                self._create_initial_schema()
            elif result[0] != self.SCHEMA_VERSION:
                # Schema needs migration
                self._migrate_schema(result[0])

            self.conn.commit()

        except Exception as e:
            self.logger.error(f"Database initialization failed: {e}")
            raise DatabaseError(f"Database initialization failed: {e}")

    def _create_initial_schema(self) -> None:
        """Create initial database schema"""
        try:
            cursor = self.conn.cursor()

            # Create tables
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS crew (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    role TEXT,
                    squad TEXT,
                    primary_skill TEXT,
                    secondary_skill TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_crew_name ON crew(name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_crew_role ON crew(role)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_crew_squad ON crew(squad)")

            self.conn.commit()

        except Exception as e:
            self.logger.error(f"Failed to create initial schema: {e}")
            raise DatabaseError(f"Failed to create initial schema: {e}")

    def _migrate_schema(self, current_version: str) -> None:
        """Migrate database schema to latest version"""
        try:
            cursor = self.conn.cursor()

            # Add any necessary schema migrations here
            if current_version == "1.0":
                pass  # No migrations needed yet

            # Update schema version
            cursor.execute(
                "INSERT INTO schema_version (version) VALUES (?)",
                (self.SCHEMA_VERSION,),
            )
            self.conn.commit()

        except Exception as e:
            self.logger.error(f"Schema migration failed: {e}")
            raise DatabaseError(f"Schema migration failed: {e}")


# Add default validation rules
def setup_default_validation():
    db = DatabaseManager()
    with db:
        db.add_validation_rule("crew", "name", "not_null", True)
        db.add_validation_rule("crew", "name", "unique", True)
        db.add_validation_rule("crew", "role", "not_null", True)
