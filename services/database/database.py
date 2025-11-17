import pymongo
from pymongo import MongoClient
from typing import List, Dict, Optional, Any
from datetime import datetime
import json
import os
from bson import ObjectId

class FundingDatabase:
    def __init__(self, connection_string: str = None, db_name: str = 'funded_backup_20251105_121856'):
        """
        Initialize MongoDB connection for funded companies database

        Args:
            connection_string: MongoDB connection string. If None, uses environment variable MONGODB_URI
            db_name: Database name (default: 'funded')
        """
        if connection_string is None:
            connection_string = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')

        self.client = MongoClient(connection_string)
        self.db = self.client[db_name]
        self.collection = self.db['companies']

        # Create indexes for better query performance
        self._create_indexes()
    
    def _create_indexes(self):
        """Create database indexes for optimized queries"""
        try:
            # Index on company name for fast company lookups
            self.collection.create_index("company_name")
            
            # Index on date for time-based queries
            self.collection.create_index("date")
            
            # Index on funding amount for amount-based queries
            self.collection.create_index("funding_amount")
            
            # Index on series for funding round queries
            self.collection.create_index("series")
            
            # Compound index for common query patterns
            self.collection.create_index([("company_name", 1), ("date", -1)])
            
            # Text index for full-text search
            self.collection.create_index([
                ("title", "text"),
                ("content", "text"),
                ("company_name", "text"),
                ("description", "text")
            ])
            
        except Exception as e:
            print(f"Warning: Could not create indexes: {e}")
    
    def create_company(self, company_data: Dict[str, Any]) -> str:
        """
        Create a new company funding record
        
        Args:
            company_data: Dictionary containing company funding information
            
        Returns:
            str: The ObjectId of the created document as string
        """
        try:
            # Add timestamp for when record was created
            company_data['created_at'] = datetime.utcnow()
            company_data['updated_at'] = datetime.utcnow()
            
            # Validate required fields
            required_fields = ['company_name', 'source']
            for field in required_fields:
                if field not in company_data:
                    raise ValueError(f"Required field '{field}' is missing")
            
            result = self.collection.insert_one(company_data)
            return str(result.inserted_id)
            
        except Exception as e:
            raise Exception(f"Error creating company record: {e}")
    
    def read_company(self, company_id: str) -> Optional[Dict[str, Any]]:
        """
        Read a company record by ID
        
        Args:
            company_id: ObjectId as string
            
        Returns:
            Dict containing company data or None if not found
        """
        try:
            result = self.collection.find_one({"_id": ObjectId(company_id)})
            if result:
                result['_id'] = str(result['_id'])
            return result
            
        except Exception as e:
            raise Exception(f"Error reading company record: {e}")
    
    def read_companies_by_name(self, company_name: str) -> List[Dict[str, Any]]:
        """
        Read all funding records for a specific company
        
        Args:
            company_name: Name of the company
            
        Returns:
            List of company funding records
        """
        try:
            results = list(self.collection.find({"company_name": company_name}))
            for result in results:
                result['_id'] = str(result['_id'])
            return results
            
        except Exception as e:
            raise Exception(f"Error reading company records: {e}")
    
    def read_all_companies(self, limit: int = 1000, skip: int = 0) -> List[Dict[str, Any]]:
        """
        Read all company records with pagination
        
        Args:
            limit: Maximum number of records to return
            skip: Number of records to skip
            
        Returns:
            List of company records
        """
        try:
            results = list(self.collection.find().skip(skip).limit(limit))
            for result in results:
                result['_id'] = str(result['_id'])
            return results
            
        except Exception as e:
            raise Exception(f"Error reading all company records: {e}")
    
    def update_company(self, company_id: str, update_data: Dict[str, Any]) -> bool:
        """
        Update a company record
        
        Args:
            company_id: ObjectId as string
            update_data: Dictionary containing fields to update
            
        Returns:
            bool: True if update was successful
        """
        try:
            # Add timestamp for when record was updated
            update_data['updated_at'] = datetime.utcnow()
            
            result = self.collection.update_one(
                {"_id": ObjectId(company_id)},
                {"$set": update_data}
            )
            return result.modified_count > 0
            
        except Exception as e:
            raise Exception(f"Error updating company record: {e}")
    
    def delete_company(self, company_id: str) -> bool:
        """
        Delete a company record
        
        Args:
            company_id: ObjectId as string
            
        Returns:
            bool: True if deletion was successful
        """
        try:
            result = self.collection.delete_one({"_id": ObjectId(company_id)})
            return result.deleted_count > 0
            
        except Exception as e:
            raise Exception(f"Error deleting company record: {e}")
    
    def search_companies(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Full-text search across company records
        
        Args:
            query: Search query string
            limit: Maximum number of results
            
        Returns:
            List of matching company records
        """
        try:
            results = list(self.collection.find(
                {"$text": {"$search": query}}
            ).limit(limit))
            
            for result in results:
                result['_id'] = str(result['_id'])
            return results
            
        except Exception as e:
            raise Exception(f"Error searching company records: {e}")
    
    def filter_companies(self, filters: Dict[str, Any], limit: int = 100) -> List[Dict[str, Any]]:
        """
        Filter companies based on specific criteria
        
        Args:
            filters: Dictionary of filter criteria
            limit: Maximum number of results
            
        Returns:
            List of filtered company records
        """
        try:
            # Build MongoDB query from filters
            query = {}
            
            if 'company_name' in filters:
                query['company_name'] = {"$regex": filters['company_name'], "$options": "i"}
            
            if 'series' in filters:
                query['series'] = filters['series']
            
            if 'funding_amount_min' in filters:
                # Convert funding amount to numeric for comparison
                query['funding_amount'] = {"$exists": True}
            
            if 'date_from' in filters:
                if 'date' not in query:
                    query['date'] = {}
                query['date']['$gte'] = filters['date_from']
            
            if 'date_to' in filters:
                if 'date' not in query:
                    query['date'] = {}
                query['date']['$lte'] = filters['date_to']
            
            if 'is_recent' in filters:
                query['is_recent'] = filters['is_recent']
            
            results = list(self.collection.find(query).limit(limit))
            for result in results:
                result['_id'] = str(result['_id'])
            return results
            
        except Exception as e:
            raise Exception(f"Error filtering company records: {e}")
    
    def bulk_insert_companies(self, companies_data: List[Dict[str, Any]]) -> List[str]:
        """
        Insert multiple company records at once
        
        Args:
            companies_data: List of company data dictionaries
            
        Returns:
            List of inserted ObjectIds as strings
        """
        try:
            # Add timestamps to all records
            for company in companies_data:
                company['created_at'] = datetime.utcnow()
                company['updated_at'] = datetime.utcnow()
            
            result = self.collection.insert_many(companies_data)
            return [str(id) for id in result.inserted_ids]
            
        except Exception as e:
            raise Exception(f"Error bulk inserting company records: {e}")
    
    def get_companies_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """
        Get companies funded within a specific date range
        
        Args:
            start_date: Start date for filtering
            end_date: End date for filtering
            
        Returns:
            List of company records within date range
        """
        try:
            query = {
                "date": {
                    "$gte": start_date.isoformat(),
                    "$lte": end_date.isoformat()
                }
            }
            
            results = list(self.collection.find(query))
            for result in results:
                result['_id'] = str(result['_id'])
            return results
            
        except Exception as e:
            raise Exception(f"Error getting companies by date range: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get database statistics
        
        Returns:
            Dictionary containing various statistics
        """
        try:
            total_companies = self.collection.count_documents({})
            
            # Count by series
            series_pipeline = [
                {"$group": {"_id": "$series", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]
            series_stats = list(self.collection.aggregate(series_pipeline))
            
            # Count by source
            source_pipeline = [
                {"$group": {"_id": "$source", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]
            source_stats = list(self.collection.aggregate(source_pipeline))
            
            # Recent companies (last 30 days)
            recent_count = self.collection.count_documents({"is_recent": True})
            
            return {
                "total_companies": total_companies,
                "series_breakdown": series_stats,
                "source_breakdown": source_stats,
                "recent_companies": recent_count
            }
            
        except Exception as e:
            raise Exception(f"Error getting statistics: {e}")
    
    def close_connection(self):
        """Close the MongoDB connection"""
        self.client.close()

# Example usage and utility functions
def load_json_to_database(json_file_path: str, db: FundingDatabase) -> int:
    """
    Load data from JSON file into the database
    
    Args:
        json_file_path: Path to the JSON file
        db: FundingDatabase instance
        
    Returns:
        Number of records inserted
    """
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, list):
            inserted_ids = db.bulk_insert_companies(data)
            return len(inserted_ids)
        else:
            # Single record
            db.create_company(data)
            return 1
            
    except Exception as e:
        raise Exception(f"Error loading JSON to database: {e}")

def export_database_to_json(db: FundingDatabase, output_file: str) -> int:
    """
    Export all database records to JSON file
    
    Args:
        db: FundingDatabase instance
        output_file: Output JSON file path
        
    Returns:
        Number of records exported
    """
    try:
        all_companies = db.read_all_companies(limit=10000)  # Adjust limit as needed
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_companies, f, indent=2, ensure_ascii=False, default=str)
        
        return len(all_companies)
        
    except Exception as e:
        raise Exception(f"Error exporting database to JSON: {e}")

# Example usage
if __name__ == "__main__":
    # Initialize database
    db = FundingDatabase()
    
    # Example: Load data from existing JSON file
    try:
        count = load_json_to_database('funding_data.json', db)
        print(f"Loaded {count} records into database")
    except Exception as e:
        print(f"Error loading data: {e}")
    
    # Example: Get statistics
    try:
        stats = db.get_statistics()
        print("Database Statistics:", stats)
    except Exception as e:
        print(f"Error getting statistics: {e}")
    
    # Close connection
    db.close_connection()
