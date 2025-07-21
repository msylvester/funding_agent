#!/usr/bin/env python3
"""
Script to merge funding_data_augmented.json into funding_data.json
Handles duplicates by checking company_name and url fields
"""

import json
from typing import List, Dict, Set

def load_json_file(filepath: str) -> List[Dict]:
    """Load JSON file and return as list"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"File {filepath} not found")
        return []
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from {filepath}: {e}")
        return []

def save_json_file(data: List[Dict], filepath: str):
    """Save data to JSON file"""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def create_duplicate_key(item: Dict) -> str:
    """Create a key for duplicate detection based on company_name and url"""
    company = item.get('company_name', '').strip().lower()
    url = item.get('url', '').strip()
    return f"{company}|{url}"

def merge_funding_data():
    """Merge augmented data into main funding data"""
    
    # Load both files
    print("Loading funding_data.json...")
    main_data = load_json_file('funding_data.json')
    
    print("Loading funding_data_augmented.json...")
    augmented_data = load_json_file('funding_data_augmented.json')
    
    if not augmented_data:
        print("No augmented data found or file is empty")
        return
    
    # Create set of existing items to avoid duplicates
    existing_keys: Set[str] = set()
    for item in main_data:
        key = create_duplicate_key(item)
        existing_keys.add(key)
    
    # Track new items added
    new_items = []
    
    # Add new items from augmented data
    for item in augmented_data:
        key = create_duplicate_key(item)
        if key not in existing_keys:
            new_items.append(item)
            existing_keys.add(key)
    
    # Combine data
    combined_data = main_data + new_items
    
    # Save merged data
    save_json_file(combined_data, 'funding_data.json')
    
    print(f"Merge completed:")
    print(f"  Original items: {len(main_data)}")
    print(f"  Augmented items available: {len(augmented_data)}")
    print(f"  New items added: {len(new_items)}")
    print(f"  Total items after merge: {len(combined_data)}")

if __name__ == "__main__":
    merge_funding_data()