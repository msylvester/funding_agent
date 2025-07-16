import json
from pathlib import Path

def combine_funding_data():
    """Combine final_scrape.json with funding_data.json and overwrite funding_data.json"""
    
    combined_data = []
    
    # Load existing funding_data.json
    try:
        with open('funding_data.json', 'r', encoding='utf-8') as f:
            funding_data = json.load(f)
        combined_data.extend(funding_data)
        print(f"Loaded {len(funding_data)} records from funding_data.json")
    except FileNotFoundError:
        print("funding_data.json not found - starting with empty dataset")
    except Exception as e:
        print(f"Error loading funding_data.json: {e}")
        return False
    
    # Load final_scrape.json
    try:
        with open('final_scrape.json', 'r', encoding='utf-8') as f:
            scrape_data = json.load(f)
        combined_data.extend(scrape_data)
        print(f"Loaded {len(scrape_data)} records from final_scrape.json")
    except FileNotFoundError:
        print("final_scrape.json not found")
        return False
    except Exception as e:
        print(f"Error loading final_scrape.json: {e}")
        return False
    
    # Remove duplicates based on URL
    seen_urls = set()
    unique_data = []
    
    for item in combined_data:
        url = item.get('url', '')
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique_data.append(item)
        elif not url:  # Keep items without URLs
            unique_data.append(item)
    
    print(f"Removed {len(combined_data) - len(unique_data)} duplicate records")
    print(f"Final dataset contains {len(unique_data)} unique records")
    
    # Write combined data back to funding_data.json
    try:
        with open('funding_data.json', 'w', encoding='utf-8') as f:
            json.dump(unique_data, f, indent=2, ensure_ascii=False)
        print("Successfully updated funding_data.json with combined data")
        return True
    except Exception as e:
        print(f"Error writing to funding_data.json: {e}")
        return False

def main():
    print("Combining funding data sources...")
    success = combine_funding_data()
    
    if success:
        print("Data combination completed successfully!")
    else:
        print("Data combination failed!")

if __name__ == "__main__":
    main()
