import os
import json
import requests
import time
import shutil

def download_filings():
    """
    Reads extracted CIK JSON files, finds 13F and Form 4 filings,
    and downloads the raw data files, filtering for modern filings.
    """
    # --- CONFIGURATION ---
    fund_data_dir = 'fund_data'
    output_dir = 'raw_filings'
    # Filter to ignore any filings before this year.
    # Set to 2004 to capture the modern HTML/XML era.
    MIN_FILING_YEAR = 2004 
    
    headers = {'User-Agent': 'YourAppName/1.0 (your.email@example.com)'}

    if not os.path.exists(fund_data_dir):
        print(f"Error: Directory '{fund_data_dir}' not found.")
        return

    if os.path.exists(output_dir):
        print(f"Removing old '{output_dir}' directory...")
        shutil.rmtree(output_dir)
    
    os.makedirs(output_dir)
    print(f"Created new '{output_dir}' directory.")

    json_files = [f for f in os.listdir(fund_data_dir) if f.endswith('.json')]

    for json_file in json_files:
        cik = json_file.replace('CIK', '').replace('.json', '')
        print(f"\nProcessing filings for CIK: {cik}")

        with open(os.path.join(fund_data_dir, json_file), 'r') as f:
            data = json.load(f)

        # --- Extract Filing Metadata ---
        filings = data.get('filings', {}).get('recent', {})
        accession_numbers = filings.get('accessionNumber', [])
        form_types = filings.get('form', [])
        primary_documents = filings.get('primaryDocument', [])
        filing_dates = filings.get('filingDate', []) 

        for i, form_type in enumerate(form_types):
            # --- DATE FILTER ---
            try:
                filing_year = int(filing_dates[i].split('-')[0])
                if filing_year < MIN_FILING_YEAR:
                    continue # Skip this filing if it's too old
            except (ValueError, IndexError):
                continue # Skip if date is malformed

            if form_type in ['13F-HR', '13F-NT', '4', '4/A']:
                accession_number = accession_numbers[i]
                primary_document = primary_documents[i]
                accession_no_dashes = accession_number.replace('-', '')

                form_dir_name = form_type.replace('/', '_A')
                output_path = os.path.join(output_dir, cik, form_dir_name)
                os.makedirs(output_path, exist_ok=True)
                
                save_path = os.path.join(output_path, f"{accession_number}.xml")

                if os.path.exists(save_path):
                    continue

                filing_url_base = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_no_dashes}/"
                
                downloaded = False
                
                def make_request(url, retry_count=3, backoff_factor=0.5):
                    for attempt in range(retry_count):
                        try:
                            time.sleep(0.2) 
                            res = requests.get(url, headers=headers, timeout=10)
                            if res.status_code == 200:
                                return res
                            if 400 <= res.status_code < 500:
                                return res
                        except requests.exceptions.RequestException:
                            if attempt < retry_count - 1:
                                time.sleep(backoff_factor * (2 ** attempt))
                            else:
                                print(f"   [!] Final attempt failed for {url}.")
                                return None
                    return None

                if form_type in ['13F-HR', '13F-NT']:
                    potential_filenames = ['form13fInfoTable.xml', 'infotable.xml']
                    for filename in potential_filenames:
                        res = make_request(filing_url_base + filename)
                        if res and res.status_code == 200:
                            with open(save_path, 'w', encoding='utf-8') as f_out:
                                f_out.write(res.text)
                            print(f"   Downloaded {filename} for {accession_number}")
                            downloaded = True
                            break
                
                if not downloaded:
                    res = make_request(filing_url_base + primary_document)
                    if res and res.status_code == 200:
                        with open(save_path, 'w', encoding='utf-8') as f_out:
                            f_out.write(res.text)
                        print(f"   Downloaded primary doc for {accession_number}")

if __name__ == "__main__":
    download_filings()