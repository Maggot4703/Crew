import unittest
import pandas as pd
from database_manager import DatabaseManager
from pathlib import Path

class TestDatabaseManager(unittest.TestCase):
    def setUp(self):
        """Initialize test database"""
        self.db = DatabaseManager("test_db.db")
        self.db.__enter__()  # Start context manager
        
    def tearDown(self):
        """Clean up test database"""
        if hasattr(self, 'db'):
            self.db.__exit__(None, None, None)  # Close context manager
        Path("test_db.db").unlink(missing_ok=True)
        Path("cleanup_test.db").unlink(missing_ok=True)  # Clean up test cleanup file

    def test_database_connection(self):
        """Test database connection is established"""
        self.assertIsNotNone(self.db.conn)
        
    def test_load_csv_files(self):
        """Test loading CSV files into database"""
        # Create test directory and files
        Path("data").mkdir(exist_ok=True)
        test_data = pd.DataFrame({
            'ID': [1, 2],
            'Name': ['Test1', 'Test2']
        })
        test_data.to_csv("data/test.csv", index=False)
        
        # Test loading
        self.db.load_csv_files()
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        self.assertIn(('test',), tables)
        
    def test_link_tables(self):
        """Test linking tables with and without matching IDs"""
        # Create test data
        crew_data = pd.DataFrame({
            'ID': [1, 2, 3],
            'Name': ['John', 'Jane', 'Bob']
        })
        links_data = pd.DataFrame({
            'ID': [1, 2, 4],
            'Link': ['A', 'B', 'C']
        })
        
        # Save to database
        crew_data.to_sql('crew', self.db.conn, if_exists='replace', index=False)
        links_data.to_sql('links', self.db.conn, if_exists='replace', index=False)
        
        # Test linking
        result = self.db.link_tables('crew', 'links')
        
        # Verify results
        self.assertEqual(len(result), 3)  # All crew entries preserved
        self.assertTrue(result['Link'].notna().all())  # No null links
        self.assertEqual(len(result[result['Link'].notna()]), 2)  # Two matched links
        
    def test_invalid_table_link(self):
        """Test linking non-existent tables"""
        with self.assertRaises(ValueError):
            self.db.link_tables('nonexistent', 'missing')

    def test_cleanup(self):
        """Test database cleanup"""
        test_path = Path("cleanup_test.db")
        test_path.unlink(missing_ok=True)  # Ensure clean state
            
        test_db = DatabaseManager("cleanup_test.db")
        with test_db:  # Use context manager properly
            self.assertTrue(test_path.exists())  # Verify db exists
        
        # Verify db is removed after context manager exits
        self.assertFalse(test_path.exists())

if __name__ == '__main__':
    unittest.main(verbosity=2)