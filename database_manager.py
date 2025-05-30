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
            cursor.execute('''
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
            ''')
            
            # Groups table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS groups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    members TEXT, -- JSON array of member IDs
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            self.connection.commit()
            logging.info("Database initialized successfully")
            
        except Exception as e:
            logging.error(f"Error initializing database: {e}")
            raise
    
    def add_crew_member(self, member_data: Dict[str, Any]) -> int:
        """Add a new crew member.
        
        Args:
            member_data: Dictionary containing member information
            
        Returns:
            ID of the newly created member
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                INSERT INTO crew_members 
                (name, rank, department, primary_skill, secondary_skill, experience)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                member_data.get('name', ''),
                member_data.get('rank', ''),
                member_data.get('department', ''),
                member_data.get('primary_skill', ''),
                member_data.get('secondary_skill', ''),
                member_data.get('experience', 0)
            ))
            
            self.connection.commit()
            member_id = cursor.lastrowid
            logging.info(f"Added crew member: {member_data.get('name', 'Unknown')}")
            return member_id
            
        except Exception as e:
            logging.error(f"Error adding crew member: {e}")
            raise
    
    def get_all_crew_members(self) -> List[Dict[str, Any]]:
        """Get all crew members.
        
        Returns:
            List of crew member dictionaries
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute('SELECT * FROM crew_members ORDER BY name')
            rows = cursor.fetchall()
            
            return [dict(row) for row in rows]
            
        except Exception as e:
            logging.error(f"Error fetching crew members: {e}")
            return []
    
    def create_group(self, name: str, description: str = "", member_ids: List[int] = None) -> int:
        """Create a new group.
        
        Args:
            name: Group name
            description: Group description
            member_ids: List of member IDs to include
            
        Returns:
            ID of the newly created group
        """
        try:
            if member_ids is None:
                member_ids = []
                
            cursor = self.connection.cursor()
            cursor.execute('''
                INSERT INTO groups (name, description, members)
                VALUES (?, ?, ?)
            ''', (name, description, json.dumps(member_ids)))
            
            self.connection.commit()
            group_id = cursor.lastrowid
            logging.info(f"Created group: {name}")
            return group_id
            
        except Exception as e:
            logging.error(f"Error creating group: {e}")
            raise
    
    def get_all_groups(self) -> List[Dict[str, Any]]:
        """Get all groups.
        
        Returns:
            List of group dictionaries
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute('SELECT * FROM groups ORDER BY name')
            rows = cursor.fetchall()
            
            groups = []
            for row in rows:
                group = dict(row)
                group['members'] = json.loads(group['members'])
                groups.append(group)
                
            return groups
            
        except Exception as e:
            logging.error(f"Error fetching groups: {e}")
            return []
    
    def close(self) -> None:
        """Close database connection."""
        if self.connection:
            self.connection.close()
            logging.info("Database connection closed")
