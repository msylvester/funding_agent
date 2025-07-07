import json

def is_valid_entry(entry):
    """
    Returns True if the 'company_name' in entry has four or fewer words,
    otherwise returns False.
    """
    company_name = entry.get('company_name', '')
    word_count = len(company_name.split())
    return word_count <= 4

def clean_data(input_filename: str, output_filename: str):
    """
    Reads the JSON file 'input_filename', filters the entries to remove those where
    the value for 'company_name' is more than four words, and writes the cleaned data
    to 'output_filename'.
    """
    try:
        with open(input_filename, 'r', encoding='utf-8') as file:
            data = json.load(file)
    except Exception as e:
        print(f"Error reading file {input_filename}: {e}")
        return

    # Filter out entries with 'company_name' containing more than four words
    valid_entries = [entry for entry in data if is_valid_entry(entry)]
    print(f"Total entries: {len(data)}")
    print(f"Valid entries: {len(valid_entries)}")

    try:
        with open(output_filename, 'w', encoding='utf-8') as outfile:
            json.dump(valid_entries, outfile, indent=4)
        print(f"Cleaned data written to {output_filename}")
    except Exception as e:
        print(f"Error writing file {output_filename}: {e}")

if __name__ == "__main__":
    input_file = 'funding_data_augmented.json'
    output_file = 'cleaned_funding_data_augmented.json'
    clean_data(input_file, output_file)
