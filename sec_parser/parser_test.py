from parsers_old import parse_13f_filing
import os
import json

# --- INSTRUCTIONS ---
# 1. Go to your `raw_filings` directory.
# 2. Find a CIK folder, then a 13F-HR or 13F-NT folder inside it.
# 3. Copy the full filename of one of the XML files (e.g., "0000921895-17-002661.xml").
# 4. Paste that filename and its CIK folder name into the variables below.

# --- CONFIGURATION ---
TEST_CIK = '0001720792' # <-- PASTE THE CIK FOLDER NAME HERE
TEST_FORM_TYPE = '13F-HR' # <-- PASTE THE FORM TYPE FOLDER NAME HERE
TEST_FILENAME = '0000919574-18-003527.xml' # <-- PASTE THE FILENAME HERE 

def run_test():
    """Reads a sample file and tests the parser function."""
    
    file_path = os.path.join('raw_filings', TEST_CIK, TEST_FORM_TYPE, TEST_FILENAME)
    
    print(f"Attempting to parse file: {file_path}")

    if not os.path.exists(file_path):
        print("\nERROR: File not found!")
        print("Please make sure the TEST_CIK, TEST_FORM_TYPE, and TEST_FILENAME variables are set correctly.")
        return

    # Read the raw content of the file that errors in your browser
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Pass the content to our new parser function
    holdings_data = parse_13f_filing(content)

    if not holdings_data:
        print("\nParsing failed or returned no data. The parser may need adjustments for this file's format.")
    else:
        print(f"\nSuccessfully parsed {len(holdings_data)} holdings from the file!")
        print("Here are the first 5 entries:")
        
        # Pretty-print the first 5 results
        for holding in holdings_data[:5]:
            print(json.dumps(holding, indent=2))

if __name__ == "__main__":
    run_test()
