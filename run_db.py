#!/usr/bin/env python3
"""
Script to load funding data into MongoDB database and optionally display sample records.

Usage:
    python run_db.py                    # Load data into database
    python run_db.py --show-sample      # Load data and show first 5 records
    python run_db.py -s                 # Short form to show sample
"""

import argparse
import json
import sys
from database import FundingDatabase, load_json_to_database
from typing import List, Dict, Any

def load_data_sources() -> List[str]:
    """
    Get list of available JSON data files to load into database.
    
    Returns:
        List of JSON file paths
    """
    data_files = [
        'funding_data.json',
        'funding_data_complete.json', 
        'final_scrape.json',
        'scraped_one.json'
    ]
    
    # Filter to only existing files
    existing_files = []
    for file_path in data_files:
        try:
            with open(file_path, 'r') as f:
                # Try to load to verify it's valid JSON
                data = json.load(f)
                if data:  # Only include non-empty files
                    existing_files.append(file_path)
                    print(f"✓ Found data file: {file_path} ({len(data) if isinstance(data, list) else 1} records)")
        except (FileNotFoundError, json.JSONDecodeError):
            print(f"⚠ Skipping {file_path}: File not found or invalid JSON")
            continue
    
    return existing_files

def load_all_data_to_database(db: FundingDatabase, data_files: List[str]) -> int:
    """
    Load data from all available JSON files into the database.
    
    Args:
        db: FundingDatabase instance
        data_files: List of JSON file paths to load
        
    Returns:
        Total number of records loaded
    """
    total_loaded = 0
    
    for file_path in data_files:
        try:
            print(f"\n📥 Loading data from {file_path}...")
            count = load_json_to_database(file_path, db)
            total_loaded += count
            print(f"✅ Loaded {count} records from {file_path}")
            
        except Exception as e:
            print(f"❌ Error loading {file_path}: {e}")
            continue
    
    return total_loaded

def print_sample_records(db: FundingDatabase, limit: int = 5):
    """
    Print sample records from the database.
    
    Args:
        db: FundingDatabase instance
        limit: Number of records to display
    """
    try:
        print(f"\n📋 First {limit} records in database:")
        print("=" * 80)
        
        records = db.read_all_companies(limit=limit)
        
        if not records:
            print("No records found in database.")
            return
        
        for i, record in enumerate(records, 1):
            print(f"\n🏢 Record {i}:")
            print(f"   Company: {record.get('company_name', 'N/A')}")
            print(f"   Funding: {record.get('funding_amount', 'N/A')}")
            print(f"   Series: {record.get('series', 'N/A')}")
            print(f"   Source: {record.get('source', 'N/A')}")
            print(f"   Date: {record.get('date', 'N/A')}")
            print(f"   URL: {record.get('url', 'N/A')[:80]}{'...' if len(record.get('url', '')) > 80 else ''}")
            print(f"   ID: {record.get('_id', 'N/A')}")
            
        print("\n" + "=" * 80)
        
    except Exception as e:
        print(f"❌ Error retrieving sample records: {e}")

def print_database_stats(db: FundingDatabase):
    """
    Print database statistics.
    
    Args:
        db: FundingDatabase instance
    """
    try:
        print("\n📊 Database Statistics:")
        print("-" * 40)
        
        stats = db.get_statistics()
        
        print(f"Total Companies: {stats.get('total_companies', 0)}")
        print(f"Recent Companies: {stats.get('recent_companies', 0)}")
        
        # Series breakdown
        series_stats = stats.get('series_breakdown', [])
        if series_stats:
            print("\nFunding Series:")
            for series in series_stats[:5]:  # Top 5 series
                print(f"  {series['_id']}: {series['count']}")
        
        # Source breakdown  
        source_stats = stats.get('source_breakdown', [])
        if source_stats:
            print("\nData Sources:")
            for source in source_stats:
                print(f"  {source['_id']}: {source['count']}")
                
    except Exception as e:
        print(f"❌ Error getting database statistics: {e}")

def main():
    """Main function to handle command line arguments and execute database operations."""
    
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description="Load funding data into MongoDB database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_db.py                    # Load data into database
  python run_db.py --show-sample      # Load data and show first 5 records
  python run_db.py -s                 # Short form to show sample
        """
    )
    
    parser.add_argument(
        '--show-sample', '-s',
        action='store_true',
        help='Display first 5 records after loading data'
    )
    
    parser.add_argument(
        '--stats-only',
        action='store_true', 
        help='Only show database statistics without loading new data'
    )
    
    parser.add_argument(
        '--clear-db',
        action='store_true',
        help='Clear all existing data before loading (use with caution!)'
    )
    
    args = parser.parse_args()
    
    print("🚀 Starting MongoDB Database Operations")
    print("=" * 50)
    
    # Initialize database connection
    try:
        print("🔌 Connecting to MongoDB...")
        db = FundingDatabase()
        print("✅ Connected to MongoDB successfully")
        
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        print("💡 Make sure MongoDB is running and connection string is correct")
        sys.exit(1)
    
    try:
        # Handle stats-only mode
        if args.stats_only:
            print_database_stats(db)
            if args.show_sample:
                print_sample_records(db)
            return
        
        # Handle clear database option
        if args.clear_db:
            response = input("⚠️  Are you sure you want to clear all data? (yes/no): ")
            if response.lower() == 'yes':
                db.collection.delete_many({})
                print("🗑️  Database cleared successfully")
            else:
                print("❌ Database clear cancelled")
                return
        
        # Find available data files
        print("\n🔍 Scanning for data files...")
        data_files = load_data_sources()
        
        if not data_files:
            print("❌ No valid data files found!")
            print("💡 Make sure you have JSON files like funding_data.json, final_scrape.json, etc.")
            return
        
        # Load data into database
        print(f"\n📦 Loading data from {len(data_files)} file(s)...")
        total_loaded = load_all_data_to_database(db, data_files)
        
        print(f"\n🎉 Successfully loaded {total_loaded} total records into database!")
        
        # Show database statistics
        print_database_stats(db)
        
        # Show sample records if requested
        if args.show_sample:
            print_sample_records(db)
        
    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled by user")
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        
    finally:
        # Close database connection
        try:
            db.close_connection()
            print("\n🔌 Database connection closed")
        except:
            pass

if __name__ == "__main__":
    main()
