import pandas as pd
from pathlib import Path
import traceback
import logging

# Import the new modules
from .processor import FileProcessor
from . import parsers
from . import utils

def main():
    """
    Main function to walk the sampled_filings directory, parse all filings,
    and return two aggregated DataFrames.
    """
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        filename='parser_issues.log',
        filemode='w' # Overwrite the log file each time
    )
    
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 200)

    # Changed path to point to the sample filings for testing
    root_path = Path("./sec_parser/parser_error")

    if not root_path.exists():
        print(f"Error: Directory not found at '{root_path.resolve()}'")
        logging.critical(f"Root directory not found at '{root_path.resolve()}'")
        return

    all_holdings = []
    all_transactions = []

    print(f"Starting processing of directory: {root_path.resolve()}")
    logging.info(f"Starting processing of directory: {root_path.resolve()}")

    filing_files = [p for p in root_path.rglob('*') if p.is_file()]

    for file_path in filing_files:
        if file_path.suffix.lower() not in ['.xml', '.txt']:
            continue
            
        accession_no = file_path.stem
        print(f"\nProcessing file: {file_path.relative_to(root_path)}")

        try:
            processor = FileProcessor(file_path)
            filing_type = processor.filing_type
            metadata = processor.metadata

            print(f"  - Detected Type: {filing_type}")
            
            raw_data = []
            df = pd.DataFrame()

            if filing_type == "13F-HR":
                raw_data = parsers.parse_13f_hr(processor.content, str(file_path))
                
                # The parser returns None for cover pages without data tables.
                if raw_data is None:
                    print(f"    - Skipped 13F-HR cover page (no data table found).")
                    continue
                
                if not raw_data:
                    logging.warning(f"Parsed 0 holdings from 13F-HR file: {file_path.relative_to(root_path)}")

                df = utils.normalize_13f_data(raw_data, metadata)
                if not df.empty:
                    all_holdings.append(df)
                print(f"    - Parsed as 13F-HR. Found {len(df)} holdings.")
            
            elif filing_type in ["4", "4/A"]:
                raw_data = parsers.parse_form4(processor.content)
                df = utils.normalize_form4_data(raw_data, metadata, accession_no)
                if not df.empty:
                    all_transactions.append(df)
                print(f"    - Parsed as {filing_type}. Found {len(df)} transactions.")

            elif filing_type == "13F-NT":
                print(f"    - Skipped 13F-NT (Notice) filing.")

            else:
                logging.warning(f"Unknown or unhandled filing type '{filing_type}' for file: {file_path.relative_to(root_path)}")
                print(f"    - WARNING: Unknown or unhandled filing type '{filing_type}'.")

        except Exception as e:
            print(f"    - ERROR processing {file_path.name}: {e}")
            logging.error(f"Failed to process {file_path.relative_to(root_path)}", exc_info=True)

    # --- Aggregate and display final results ---
    final_holdings_df = pd.DataFrame()
    if all_holdings:
        final_holdings_df = pd.concat(all_holdings, ignore_index=True)
    
    final_transactions_df = pd.DataFrame()
    if all_transactions:
        final_transactions_df = pd.concat(all_transactions, ignore_index=True)

    print("\n\n" + "="*80)
    print("                      AGGREGATED QUARTERLY HOLDINGS (13F-HR)")
    print("="*80)
    if not final_holdings_df.empty:
        print(final_holdings_df.head())
    else:
        print("No 13F-HR holdings data found.")

    print("\n\n" + "="*80)
    print("                      AGGREGATED INSIDER TRANSACTIONS (FORM 4, 4/A)")
    print("="*80)
    if not final_transactions_df.empty:
        print(final_transactions_df.head())
    else:
        print("No Form 4/4A transaction data found.")

    print(f"\nProcessing complete. Check 'parser_issues.log' for any warnings or errors.")


if __name__ == '__main__':
    main()
