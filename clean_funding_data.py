import json

def is_valid_entry(entry):
    # Check required keys exist
    required_keys = [
        'source', 'title', 'url', 'date', 'scraped_at', 
        'company_name', 'funding_amount', 'valuation',
        'series', 'founded_year', 'total_funding', 'investors', 
        'description', 'is_recent', 'is_unicorn', 
        'unicorn_month', 'unicorn_year'
    ]
    if not all(key in entry for key in required_keys):
        return False

    company_name_words = entry['company_name'].split()
    # if the company name is more than 3 words or is found within the title, consider it malformed
    if len(company_name_words) > 3 or entry['company_name'] in entry.get('title', ''):
        return False

    return True

def clean_data(input_file, output_file):
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    cleaned_data = [entry for entry in data if is_valid_entry(entry)]
    
    with open(output_file, 'w') as f:
        json.dump(cleaned_data, f, indent=2)

if __name__ == '__main__':
    clean_data('funding_data_augmented.json', 'funding_data_augmented_cleaned.json')
