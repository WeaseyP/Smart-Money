import pandas as pd
from pathlib import Path
import re

# Import the modules from the sec_parser package
from . import parsers
from . import utils

def find_filing_file(filing_path: Path):
    """
    Finds the primary filing document within a filing directory.
    - For 13F, prefers form13fInfoTable.xml, falls back to the first .txt file.
    - For Form 4, finds the first .xml file.
    """
    # Check for modern 13F XML file
    modern_13f_xml = filing_path / "form13fInfoTable.xml"
    if modern_13f_xml.exists():
        return modern_13f_xml, "13F-HR-XML"

    # Check for legacy 13F text file
    try:
        legacy_13f_txt = next(filing_path.glob('*.txt'))
        return legacy_13f_txt, "13F-HR-TXT"
    except StopIteration:
        pass

    # Check for Form 4 XML file
    try:
        form4_xml = next(filing_path.glob('*.xml'))
        return form4_xml, "4"
    except StopIteration:
        pass

    return None, None


def main():
    """
    Main function to walk the raw_filings directory, parse all filings,
    and return two aggregated DataFrames.
    """
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 200)

    # The user will run this from their Downloads folder.
    # The script will look for './raw_filings' relative to the current working directory.
    root_path = Path("./sec_parser/raw_filings")

    if not root_path.exists():
        print(f"Error: Directory not found at '{root_path.resolve()}'")
        print("Please ensure you are running this script from your Downloads folder and the 'raw_filings' directory exists.")
        return

    all_holdings = []
    all_transactions = []

    print(f"Starting processing of directory: {root_path.resolve()}")

    # Iterate through each CIK directory
    for cik_path in root_path.iterdir():
        if not cik_path.is_dir():
            continue
        
        cik = cik_path.name
        print(f"\nProcessing CIK: {cik}")

        # Iterate through each filing directory within the CIK folder
        for filing_path in cik_path.iterdir():
            if not filing_path.is_dir():
                continue

            accession_no = filing_path.name
            print(f"  Parsing filing: {accession_no}")

            file_to_parse, file_type = find_filing_file(filing_path)

            if not file_to_parse:
                print(f"    - No suitable .xml or .txt file found in {filing_path}")
                continue

            try:
                content = file_to_parse.read_text(encoding='utf-8')
                raw_data = []
                df = pd.DataFrame()

                if file_type == "13F-HR-XML":
                    raw_data = parsers.parse_13f_xml(content)
                    df = utils.normalize_13f_data(raw_data, fund_cik=cik)
                    all_holdings.append(df)
                    print(f"    - Parsed as Modern 13F. Found {len(df)} holdings.")
                
                elif file_type == "13F-HR-TXT":
                    raw_data = parsers.parse_13f_text(content)
                    df = utils.normalize_13f_data(raw_data, fund_cik=cik)
                    all_holdings.append(df)
                    print(f"    - Parsed as Legacy 13F. Found {len(df)} holdings.")

                elif file_type == "4":
                    raw_data = parsers.parse_form4_xml(content)
                    # Use filing_path.name as a proxy for accession_no
                    df = utils.normalize_form4_data(raw_data, accession_no=accession_no)
                    all_transactions.append(df)
                    print(f"    - Parsed as Form 4. Found {len(df)} transactions.")
            
            except Exception as e:
                print(f"    - ERROR parsing {file_to_parse}: {e}")

    # --- Aggregate and display final results ---
    final_holdings_df = pd.DataFrame()
    if all_holdings:
        final_holdings_df = pd.concat(all_holdings, ignore_index=True)
    
    final_transactions_df = pd.DataFrame()
    if all_transactions:
        final_transactions_df = pd.concat(all_transactions, ignore_index=True)

    print("\n\n" + "="*80)
    print("                      AGGREGATED QUARTERLY HOLDINGS (13F)")
    print("="*80)
    if not final_holdings_df.empty:
        print(final_holdings_df)
    else:
        print("No 13F holdings data found.")

    print("\n\n" + "="*80)
    print("                      AGGREGATED INSIDER TRANSACTIONS (FORM 4)")
    print("="*80)
    if not final_transactions_df.empty:
        print(final_transactions_df)
    else:
        print("No Form 4 transaction data found.")


if __name__ == '__main__':
    main()
