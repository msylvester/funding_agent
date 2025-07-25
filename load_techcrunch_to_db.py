#!/usr/bin/env python3
"""
Script to load TechCrunch funding data from JSON file into MongoDB database.

This script reads the techcrunch_minimal.json file and loads all company
funding records into the MongoDB 'funded' database using the database.py layer.
"""

import json
import os
import sys
from typing import List, Dict, Any
from database import FundingDatabase, load_json_to_database

def load_techcrunch_data(json_file: str = 'techcrunch_minimal.json', 
                        connection_string: str = None) -> int:
    """
    Load TechCrunch funding data from JSON file into MongoDB database.
    
    Args:
        json_file: Path to the JSON file containing TechCrunch data
        connection_string: MongoDB connection string (optional)
        
    Returns:
        Number of records successfully loaded
    """
    
    # Check if the JSON file exists
    if not os.path.exists(json_file):
        raise FileNotFoundError(f"JSON file '{json_file}' not found. Please ensure the file exists.")
    
    # Initialize database connection
    print(f"Connecting to MongoDB database 'funded'...")
    try:
        db = FundingDatabase(connection_string)
        print("✅ Successfully connected to database")
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        return 0
    
    # Load and validate JSON data
    print(f"Loading data from '{json_file}'...")
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            print(f"❌ Expected a list of companies, got {type(data)}")
            return 0
        
        print(f"✅ Found {len(data)} companies in JSON file")
        
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON format: {e}")
        return 0
    except Exception as e:
        print(f"❌ Error reading JSON file: {e}")
        return 0
    
    # Validate and prepare data for database insertion
    valid_companies = []
    invalid_count = 0
    
    for i, company in enumerate(data):
        if validate_company_data(company):
            # Ensure required fields are present
            if 'source' not in company:
                company['source'] = 'TechCrunch'
            valid_companies.append(company)
        else:
            invalid_count += 1
            print(f"⚠️  Skipping invalid company record {i+1}: {company.get('company_name', 'Unknown')}")
    
    print(f"✅ {len(valid_companies)} valid companies ready for insertion")
    if invalid_count > 0:
        print(f"⚠️  {invalid_count} invalid records skipped")
    
    # Insert data into database
    if valid_companies:
        try:
            print("Inserting companies into database...")
            inserted_ids = db.bulk_insert_companies(valid_companies)
            print(f"✅ Successfully inserted {len(inserted_ids)} companies into database")
            
            # Display some statistics
            stats = db.get_statistics()
            print(f"\nDatabase Statistics:")
            print(f"  Total companies: {stats['total_companies']}")
            print(f"  Recent companies: {stats['recent_companies']}")
            
            return len(inserted_ids)
            
        except Exception as e:
            print(f"❌ Error inserting data into database: {e}")
            return 0
        finally:
            db.close_connection()
    else:
        print("❌ No valid companies to insert")
        db.close_connection()
        return 0

def validate_company_data(company: Dict[str, Any]) -> bool:
    """
    Validate that a company record has the minimum required fields.
    
    Args:
        company: Company data dictionary
        
    Returns:
        True if valid, False otherwise
    """
    # Check for required field: company_name
    if not company.get('company_name'):
        return False
    
    # Company name should be a non-empty string
    if not isinstance(company['company_name'], str) or not company['company_name'].strip():
        return False
    
    return True

def print_sample_data(json_file: str = 'techcrunch_minimal.json', limit: int = 3):
    """
    Print a sample of the data that will be loaded.
    
    Args:
        json_file: Path to the JSON file
        limit: Number of sample records to display
    """
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"\nSample data from '{json_file}':")
        print("=" * 50)
        
        for i, company in enumerate(data[:limit]):
            print(f"\nCompany {i+1}:")
            print(f"  Name: {company.get('company_name', 'N/A')}")
            print(f"  Funding: {company.get('funding_amount', 'N/A')}")
            print(f"  Series: {company.get('series', 'N/A')}")
            print(f"  Date: {company.get('date', 'N/A')}")
            print(f"  Source: {company.get('source', 'N/A')}")
        
        if len(data) > limit:
            print(f"\n... and {len(data) - limit} more companies")
            
    except Exception as e:
        print(f"Error reading sample data: {e}")

def main():
    """Main function to run the data loading process."""
    
    print("TechCrunch Data Loader for MongoDB")
    print("=" * 40)
    
    # Check command line arguments
    json_file = 'techcrunch_minimal.json'
    if len(sys.argv) > 1:
        json_file = sys.argv[1]
    
    # Print sample data first
    if os.path.exists(json_file):
        print_sample_data(json_file)
        
        # Ask for confirmation
        response = input(f"\nProceed with loading data from '{json_file}' into MongoDB? (y/N): ")
        if response.lower() not in ['y', 'yes']:
            print("Operation cancelled.")
            return
    
    # Load the data
    try:
        count = load_techcrunch_data(json_file)
        if count > 0:
            print(f"\n🎉 Successfully loaded {count} companies into the 'funded' database!")
        else:
            print("\n❌ No companies were loaded.")
            
    except Exception as e:
        print(f"\n❌ Error during data loading: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
