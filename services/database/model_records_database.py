"""
Database service for tracking Hugging Face model records
Tracks which models have been seen before to identify new trending models
"""

import os
import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ModelRecordsDatabase:
    """Database for tracking model records"""

    def __init__(self, db_path: str = None):
        """
        Initialize database connection

        Args:
            db_path: Path to SQLite database file (defaults to data/model_records.db)
        """
        if db_path is None:
            # Default to data directory
            data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
            os.makedirs(data_dir, exist_ok=True)
            db_path = os.path.join(data_dir, 'model_records.db')

        self.db_path = db_path
        self.connection = None
        self._connect()
        self._initialize_tables()

    def _connect(self):
        """Establish database connection"""
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row
            logger.info(f"Connected to database: {self.db_path}")
        except sqlite3.Error as e:
            logger.error(f"Error connecting to database: {e}")
            raise

    def _initialize_tables(self):
        """Create tables if they don't exist"""
        try:
            cursor = self.connection.cursor()

            # Create model_records table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS model_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    full_name TEXT NOT NULL,
                    first_seen TIMESTAMP NOT NULL,
                    last_seen TIMESTAMP,
                    view_count INTEGER DEFAULT 1,
                    UNIQUE(full_name)
                )
            """)

            # Create index on full_name for faster lookups
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_full_name
                ON model_records(full_name)
            """)

            self.connection.commit()
            logger.info("Database tables initialized")

        except sqlite3.Error as e:
            logger.error(f"Error initializing tables: {e}")
            raise

    def create_record(self, full_name: str, timestamp: datetime) -> bool:
        """
        Create a new model record

        Args:
            full_name: Full model name (e.g., "username/model-name")
            timestamp: Timestamp when model was first seen

        Returns:
            True if record was created, False if it already exists
        """
        try:
            cursor = self.connection.cursor()

            # Try to insert new record
            cursor.execute("""
                INSERT OR IGNORE INTO model_records (full_name, first_seen, last_seen, view_count)
                VALUES (?, ?, ?, 1)
            """, (full_name, timestamp, timestamp))

            self.connection.commit()

            # Check if row was inserted
            if cursor.rowcount > 0:
                logger.info(f"Created new record for model: {full_name}")
                return True
            else:
                logger.debug(f"Record already exists for model: {full_name}")
                return False

        except sqlite3.Error as e:
            logger.error(f"Error creating record for {full_name}: {e}")
            return False

    def read_records_by_name(self, full_name: str) -> List[Dict[str, Any]]:
        """
        Read records by model name

        Args:
            full_name: Full model name

        Returns:
            List of matching records (typically 0 or 1)
        """
        try:
            cursor = self.connection.cursor()

            cursor.execute("""
                SELECT id, full_name, first_seen, last_seen, view_count
                FROM model_records
                WHERE full_name = ?
            """, (full_name,))

            rows = cursor.fetchall()

            records = []
            for row in rows:
                records.append({
                    "id": row["id"],
                    "full_name": row["full_name"],
                    "first_seen": row["first_seen"],
                    "last_seen": row["last_seen"],
                    "view_count": row["view_count"]
                })

            return records

        except sqlite3.Error as e:
            logger.error(f"Error reading records for {full_name}: {e}")
            return []

    def update_last_seen(self, full_name: str, timestamp: datetime) -> bool:
        """
        Update last_seen timestamp and increment view count

        Args:
            full_name: Full model name
            timestamp: New timestamp

        Returns:
            True if update was successful
        """
        try:
            cursor = self.connection.cursor()

            cursor.execute("""
                UPDATE model_records
                SET last_seen = ?, view_count = view_count + 1
                WHERE full_name = ?
            """, (timestamp, full_name))

            self.connection.commit()

            if cursor.rowcount > 0:
                logger.info(f"Updated last_seen for model: {full_name}")
                return True
            else:
                logger.warning(f"No record found to update for: {full_name}")
                return False

        except sqlite3.Error as e:
            logger.error(f"Error updating record for {full_name}: {e}")
            return False

    def get_all_records(self, limit: int = None) -> List[Dict[str, Any]]:
        """
        Get all model records

        Args:
            limit: Maximum number of records to return

        Returns:
            List of all records
        """
        try:
            cursor = self.connection.cursor()

            query = """
                SELECT id, full_name, first_seen, last_seen, view_count
                FROM model_records
                ORDER BY last_seen DESC
            """

            if limit:
                query += f" LIMIT {limit}"

            cursor.execute(query)
            rows = cursor.fetchall()

            records = []
            for row in rows:
                records.append({
                    "id": row["id"],
                    "full_name": row["full_name"],
                    "first_seen": row["first_seen"],
                    "last_seen": row["last_seen"],
                    "view_count": row["view_count"]
                })

            return records

        except sqlite3.Error as e:
            logger.error(f"Error reading all records: {e}")
            return []

    def delete_record(self, full_name: str) -> bool:
        """
        Delete a model record

        Args:
            full_name: Full model name

        Returns:
            True if deletion was successful
        """
        try:
            cursor = self.connection.cursor()

            cursor.execute("""
                DELETE FROM model_records
                WHERE full_name = ?
            """, (full_name,))

            self.connection.commit()

            if cursor.rowcount > 0:
                logger.info(f"Deleted record for model: {full_name}")
                return True
            else:
                logger.warning(f"No record found to delete: {full_name}")
                return False

        except sqlite3.Error as e:
            logger.error(f"Error deleting record for {full_name}: {e}")
            return False

    def close_connection(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")


if __name__ == "__main__":
    # Test the database
    import logging
    logging.basicConfig(level=logging.INFO)

    db = ModelRecordsDatabase()

    # Test creating records
    print("\n=== Testing ModelRecordsDatabase ===\n")

    db.create_record("test/model-1", datetime.utcnow())
    db.create_record("test/model-2", datetime.utcnow())

    # Test reading records
    records = db.read_records_by_name("test/model-1")
    print(f"Found {len(records)} record(s) for 'test/model-1'")
    for record in records:
        print(f"  - {record}")

    # Test getting all records
    all_records = db.get_all_records(limit=10)
    print(f"\nAll records (limit 10): {len(all_records)}")
    for record in all_records:
        print(f"  - {record['full_name']} (viewed {record['view_count']} times)")

    # Clean up
    db.delete_record("test/model-1")
    db.delete_record("test/model-2")

    db.close_connection()
    print("\n=== Test complete ===\n")
