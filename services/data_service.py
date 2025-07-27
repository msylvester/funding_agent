"""
Data service layer for handling database operations
"""
from services.database import FundingDatabase
from typing import List, Dict, Any
import streamlit as st

class DataService:
    def __init__(self):
        self.db = FundingDatabase()
    
    def ingest_data(self) -> Dict[str, Any]:
        """
        Handle data ingestion - query MongoDB and return results
        """
        try:
            # Get statistics about current data
            stats = self.db.get_statistics()
            
            # Get recent companies (last 10)
            recent_companies = self.db.read_all_companies(limit=10)
            
            return {
                'success': True,
                'stats': stats,
                'recent_companies': recent_companies,
                'message': f"Successfully retrieved {len(recent_companies)} recent companies"
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to retrieve data from MongoDB'
            }
    
    def close(self):
        """Close database connection"""
        self.db.close_connection()
