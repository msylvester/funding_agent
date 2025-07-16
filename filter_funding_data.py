import json
import sys
from pathlib import Path

def has_company_and_funding(item):
    """Check if an item has both company_name and funding_amount specified"""
    company_name = item.get('company_name', 'Not specified')
    funding_amount = item.get('funding_amount', 'Not specified')
    
    # Both fields must be present and not "Not specified"
    return (company_name != 'Not specified' and 
            funding_amount != 'Not specified' and
            company_name.strip() != '' and
            funding_amount.strip() != '')

def filter_funding_data(input_file='scraped_one.json', output_file='final_scrape.json'):
    """Filter JSON data to only include items with company name and valuation"""
    try:
        # Check if input file exists
        if not Path(input_file).exists():
            print(f"Error: Input file '{input_file}' not found.")
            return False
        
        # Read the input JSON file
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"Loaded {len(data)} items from {input_file}")
        
        # Filter items that have both company name and funding amount
        filtered_data = [item for item in data if has_company_and_funding(item)]
        
        print(f"Found {len(filtered_data)} items with both company name and funding amount")
        
        # Write filtered data to output file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(filtered_data, f, indent=2, ensure_ascii=False)
        
        print(f"Filtered data saved to {output_file}")
        
        # Print summary of filtered items
        if filtered_data:
            print("\nFiltered companies:")
            for item in filtered_data:
                company = item.get('company_name', 'Unknown')
                funding = item.get('funding_amount', 'Unknown')
                valuation = item.get('valuation', 'Not specified')
                print(f"  - {company}: {funding} funding, {valuation} valuation")
        
        return True
        
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {input_file}: {e}")
        return False
    except Exception as e:
        print(f"Error processing files: {e}")
        return False

def main():
    """Main function to run the filtering process"""
    input_file = 'scraped_one.json'
    output_file = 'final_scrape.json'
    
    # Allow command line arguments for custom file paths
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    
    print(f"Filtering funding data from {input_file} to {output_file}")
    success = filter_funding_data(input_file, output_file)
    
    if success:
        print("Filtering completed successfully!")
    else:
        print("Filtering failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
