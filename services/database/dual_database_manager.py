"""
Dual Database Manager - Syncs writes to both local MongoDB and hosted MongoDB Atlas

This module provides a DualDatabaseManager class that coordinates database operations
between a local MongoDB instance and a hosted MongoDB Atlas instance. It ensures
strict consistency by implementing rollback mechanisms when Atlas writes fail.

Usage:
    from services.database.dual_database_manager import DualDatabaseManager

    db = DualDatabaseManager()
    company_id = db.create_company(company_data)
    db.close_connections()
"""

import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from bson import ObjectId

from services.database.database import FundingDatabase

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DualDatabaseManager:
    """
    Manages dual-write operations to both local and hosted MongoDB databases.

    This class wraps two FundingDatabase instances (local and Atlas) and ensures
    that all write operations are synchronized between them. If an Atlas write
    fails, the local write is rolled back to maintain consistency.
    """

    def __init__(
        self,
        local_uri: str = None,
        local_db_name: str = 'funded_backup_20251105_121856',
        local_collection_name: str = 'companies',
        atlas_uri: str = None,
        atlas_db_name: str = 'companies',
        atlas_collection_name: str = 'funded_companies'
    ):
        """
        Initialize dual database manager with local and Atlas connections.

        Args:
            local_uri: Local MongoDB connection string (default: from env MONGODB_URI)
            local_db_name: Local database name
            local_collection_name: Local collection name
            atlas_uri: Atlas MongoDB connection string (default: from env MONGODB_ATLAS_URI)
            atlas_db_name: Atlas database name
            atlas_collection_name: Atlas collection name

        Raises:
            Exception: If either database connection fails
        """
        # Get URIs from environment if not provided
        if local_uri is None:
            local_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')

        if atlas_uri is None:
            atlas_uri = os.getenv('MONGODB_ATLAS_URI')
            if not atlas_uri:
                raise Exception(
                    "MONGODB_ATLAS_URI environment variable not set. "
                    "Please add it to your .env file."
                )

        # Initialize local database connection
        try:
            self.local_db = FundingDatabase(
                connection_string=local_uri,
                db_name=local_db_name,
                collection_name=local_collection_name
            )
            logger.info(f"Connected to local database: {local_db_name}.{local_collection_name}")
        except Exception as e:
            raise Exception(f"Failed to connect to local database: {e}")

        # Initialize Atlas database connection
        try:
            self.atlas_db = FundingDatabase(
                connection_string=atlas_uri,
                db_name=atlas_db_name,
                collection_name=atlas_collection_name
            )
            logger.info(f"Connected to Atlas database: {atlas_db_name}.{atlas_collection_name}")
        except Exception as e:
            self.local_db.close_connection()
            raise Exception(f"Failed to connect to Atlas database: {e}")

        # Store collection names for reference
        self.local_collection_name = local_collection_name
        self.atlas_collection_name = atlas_collection_name

    def create_company(self, company_data: Dict[str, Any]) -> str:
        """
        Create a company record in both local and Atlas databases.

        This method writes to the local database first, then to Atlas.
        If the Atlas write fails, the local write is rolled back.

        Args:
            company_data: Dictionary containing company funding information

        Returns:
            str: The ObjectId of the local document as string

        Raises:
            Exception: If write to either database fails
        """
        local_id = None

        try:
            # Step 1: Write to local database
            local_id = self.local_db.create_company(company_data.copy())
            logger.info(f"Created company in local database: {local_id}")

            # Step 2: Write to Atlas database
            try:
                atlas_id = self.atlas_db.create_company(company_data.copy())
                logger.info(f"Created company in Atlas database: {atlas_id}")

                # Success - return local ID
                return local_id

            except Exception as atlas_error:
                # Atlas write failed - rollback local write
                logger.error(f"Atlas write failed: {atlas_error}")

                try:
                    self.local_db.delete_company(local_id)
                    logger.info(f"Rolled back local write: {local_id}")
                except Exception as rollback_error:
                    logger.critical(
                        f"ROLLBACK FAILED! Local record {local_id} exists but Atlas write failed. "
                        f"Manual cleanup required. Rollback error: {rollback_error}"
                    )

                raise Exception(
                    f"Failed to write to Atlas database (local write rolled back): {atlas_error}"
                )

        except Exception as e:
            # If error happened before Atlas write, just raise
            if local_id is None:
                raise Exception(f"Failed to create company: {e}")
            # Otherwise, error was already handled above
            raise

    def update_company(self, company_id: str, update_data: Dict[str, Any]) -> bool:
        """
        Update a company record in both local and Atlas databases.

        Uses company_id to find the local record, then uses URL to find
        the corresponding Atlas record (since ObjectIds differ).

        Args:
            company_id: Local ObjectId as string
            update_data: Dictionary containing fields to update

        Returns:
            bool: True if update was successful in both databases

        Raises:
            Exception: If update fails in either database
        """
        # First, get the company URL from local database
        local_company = self.local_db.read_company(company_id)
        if not local_company:
            raise Exception(f"Company {company_id} not found in local database")

        company_url = local_company.get('url')
        if not company_url:
            raise Exception(f"Company {company_id} has no URL field - cannot sync to Atlas")

        # Track if local update succeeded
        local_updated = False
        original_local_data = None

        try:
            # Store original data for potential rollback
            original_local_data = local_company.copy()

            # Step 1: Update local database
            local_updated = self.local_db.update_company(company_id, update_data.copy())
            if not local_updated:
                logger.warning(f"Local update for {company_id} did not modify any records")
                return False

            logger.info(f"Updated company in local database: {company_id}")

            # Step 2: Find and update Atlas record by URL
            try:
                # Find Atlas record by URL
                atlas_companies = self.atlas_db.collection.find({'url': company_url})
                atlas_company = None
                for company in atlas_companies:
                    atlas_company = company
                    break

                if not atlas_company:
                    raise Exception(f"Company with URL {company_url} not found in Atlas")

                atlas_id = str(atlas_company['_id'])

                # Update Atlas record
                atlas_updated = self.atlas_db.update_company(atlas_id, update_data.copy())

                if atlas_updated:
                    logger.info(f"Updated company in Atlas database: {atlas_id}")
                    return True
                else:
                    raise Exception("Atlas update did not modify any records")

            except Exception as atlas_error:
                # Atlas update failed - rollback local update
                logger.error(f"Atlas update failed: {atlas_error}")

                try:
                    # Restore original data (remove timestamps that were added)
                    restore_data = {k: v for k, v in original_local_data.items()
                                  if k not in ['_id', 'created_at']}
                    self.local_db.update_company(company_id, restore_data)
                    logger.info(f"Rolled back local update: {company_id}")
                except Exception as rollback_error:
                    logger.critical(
                        f"ROLLBACK FAILED! Local record {company_id} modified but Atlas update failed. "
                        f"Manual cleanup required. Rollback error: {rollback_error}"
                    )

                raise Exception(
                    f"Failed to update Atlas database (local update rolled back): {atlas_error}"
                )

        except Exception as e:
            # If error happened before local update, just raise
            if not local_updated:
                raise Exception(f"Failed to update company: {e}")
            # Otherwise, error was already handled above
            raise

    def delete_company(self, company_id: str) -> bool:
        """
        Delete a company record from both local and Atlas databases.

        Uses company_id to delete from local, then uses URL to find and
        delete the corresponding Atlas record.

        Args:
            company_id: Local ObjectId as string

        Returns:
            bool: True if deletion was successful in both databases

        Raises:
            Exception: If deletion fails in either database
        """
        # First, get the company data (we need the URL)
        local_company = self.local_db.read_company(company_id)
        if not local_company:
            raise Exception(f"Company {company_id} not found in local database")

        company_url = local_company.get('url')
        if not company_url:
            raise Exception(f"Company {company_id} has no URL field - cannot sync deletion to Atlas")

        # Save company data for potential rollback
        company_data_backup = local_company.copy()
        company_data_backup.pop('_id', None)  # Remove local _id for recreation

        local_deleted = False

        try:
            # Step 1: Delete from local database
            local_deleted = self.local_db.delete_company(company_id)
            if not local_deleted:
                logger.warning(f"Local delete for {company_id} did not remove any records")
                return False

            logger.info(f"Deleted company from local database: {company_id}")

            # Step 2: Find and delete from Atlas by URL
            try:
                # Find Atlas record by URL
                atlas_companies = self.atlas_db.collection.find({'url': company_url})
                atlas_company = None
                for company in atlas_companies:
                    atlas_company = company
                    break

                if not atlas_company:
                    raise Exception(f"Company with URL {company_url} not found in Atlas")

                atlas_id = str(atlas_company['_id'])

                # Delete Atlas record
                atlas_deleted = self.atlas_db.delete_company(atlas_id)

                if atlas_deleted:
                    logger.info(f"Deleted company from Atlas database: {atlas_id}")
                    return True
                else:
                    raise Exception("Atlas delete did not remove any records")

            except Exception as atlas_error:
                # Atlas delete failed - restore local record
                logger.error(f"Atlas delete failed: {atlas_error}")

                try:
                    restored_id = self.local_db.create_company(company_data_backup)
                    logger.info(f"Restored local record after failed Atlas delete: {restored_id}")
                except Exception as rollback_error:
                    logger.critical(
                        f"ROLLBACK FAILED! Local record {company_id} deleted but Atlas delete failed. "
                        f"Manual recovery required. Company data: {company_data_backup}. "
                        f"Rollback error: {rollback_error}"
                    )

                raise Exception(
                    f"Failed to delete from Atlas database (local delete rolled back): {atlas_error}"
                )

        except Exception as e:
            # If error happened before local delete, just raise
            if not local_deleted:
                raise Exception(f"Failed to delete company: {e}")
            # Otherwise, error was already handled above
            raise

    def bulk_insert_companies(self, companies_data: List[Dict[str, Any]]) -> List[str]:
        """
        Bulk insert company records to both local and Atlas databases.

        Args:
            companies_data: List of company data dictionaries

        Returns:
            List[str]: List of local ObjectIds as strings

        Raises:
            Exception: If bulk insert fails in either database
        """
        local_ids = []

        try:
            # Step 1: Bulk insert to local database
            local_ids = self.local_db.bulk_insert_companies([c.copy() for c in companies_data])
            logger.info(f"Bulk inserted {len(local_ids)} companies to local database")

            # Step 2: Bulk insert to Atlas database
            try:
                atlas_ids = self.atlas_db.bulk_insert_companies([c.copy() for c in companies_data])
                logger.info(f"Bulk inserted {len(atlas_ids)} companies to Atlas database")

                return local_ids

            except Exception as atlas_error:
                # Atlas bulk insert failed - rollback local inserts
                logger.error(f"Atlas bulk insert failed: {atlas_error}")

                try:
                    for local_id in local_ids:
                        self.local_db.delete_company(local_id)
                    logger.info(f"Rolled back {len(local_ids)} local inserts")
                except Exception as rollback_error:
                    logger.critical(
                        f"ROLLBACK FAILED! {len(local_ids)} local records created but Atlas bulk insert failed. "
                        f"Manual cleanup required. IDs: {local_ids}. Rollback error: {rollback_error}"
                    )

                raise Exception(
                    f"Failed to bulk insert to Atlas database (local inserts rolled back): {atlas_error}"
                )

        except Exception as e:
            # If error happened before local insert, just raise
            if not local_ids:
                raise Exception(f"Failed to bulk insert companies: {e}")
            # Otherwise, error was already handled above
            raise

    # Read operations - delegate to local database only
    # (Reads don't need to be dual since data should be identical)

    def read_company(self, company_id: str) -> Optional[Dict[str, Any]]:
        """Read a company record by ID from local database"""
        return self.local_db.read_company(company_id)

    def read_companies_by_name(self, company_name: str) -> List[Dict[str, Any]]:
        """Read all funding records for a specific company from local database"""
        return self.local_db.read_companies_by_name(company_name)

    def read_all_companies(self, limit: int = 1000, skip: int = 0) -> List[Dict[str, Any]]:
        """Read all company records with pagination from local database"""
        return self.local_db.read_all_companies(limit, skip)

    def search_companies(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Full-text search across company records from local database"""
        return self.local_db.search_companies(query, limit)

    def filter_companies(self, filters: Dict[str, Any], limit: int = 100) -> List[Dict[str, Any]]:
        """Filter companies based on specific criteria from local database"""
        return self.local_db.filter_companies(filters, limit)

    def get_companies_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get companies funded within a specific date range from local database"""
        return self.local_db.get_companies_by_date_range(start_date, end_date)

    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics from local database"""
        return self.local_db.get_statistics()

    def close_connections(self):
        """Close both local and Atlas database connections"""
        self.local_db.close_connection()
        self.atlas_db.close_connection()
        logger.info("Closed both database connections")


# Example usage
if __name__ == "__main__":
    # Initialize dual database manager
    db = DualDatabaseManager()

    # Example: Create a company
    try:
        test_company = {
            'company_name': 'Test Company',
            'source': 'Test',
            'url': 'https://example.com/test-' + str(datetime.now().timestamp()),
            'funding_amount': '$1M',
            'series': 'Seed'
        }

        company_id = db.create_company(test_company)
        print(f"Created company with ID: {company_id}")

        # Read it back
        company = db.read_company(company_id)
        print(f"Retrieved company: {company['company_name']}")

        # Update it
        db.update_company(company_id, {'funding_amount': '$2M'})
        print(f"Updated company funding amount")

        # Delete it
        db.delete_company(company_id)
        print(f"Deleted company")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close_connections()
