import pandas as pd
from typing import List, Dict, Any, Optional
import json
from datetime import datetime

def to_int(value: Optional[str]) -> Optional[int]:
    """Safely convert a string to an integer, returning None on failure."""
    if value is None or value == '':
        return None
    try:
        # Remove commas and decimals before converting
        return int(str(value).replace(',', '').split('.')[0])
    except (ValueError, TypeError):
        return None

def to_float(value: Optional[str]) -> Optional[float]:
    """Safely convert a string to a float, returning None on failure."""
    if value is None or value == '':
        return None
    try:
        return float(str(value).replace(',', ''))
    except (ValueError, TypeError):
        return None

def to_date(value: Optional[str]) -> Optional[pd.Timestamp]:
    """Safely convert a string to a pandas Timestamp, returning None on failure."""
    if not value:
        return None
    try:
        # pd.to_datetime is very flexible with formats
        return pd.to_datetime(value)
    except (ValueError, TypeError):
        return None

def create_insider_relation(record: Dict[str, Any]) -> str:
    """Create a descriptive string for the insider's relationship."""
    relations = []
    if record.get('is_director'):
        relations.append("Director")
    if record.get('is_officer'):
        title = record.get('officer_title', 'Officer')
        relations.append(title if title else "Officer")
    if record.get('is_ten_percent_owner'):
        relations.append("10% Owner")
    return ', '.join(relations) if relations else "N/A"

def normalize_13f_data(raw_data: List[Dict[str, Any]], metadata: Dict[str, Any]) -> pd.DataFrame:
    """
    Cleans and normalizes a list of dictionaries from a 13F parser
    and aligns it with the Quarterly_Holdings schema.
    """
    if not raw_data:
        return pd.DataFrame()

    processed_data = []
    for record in raw_data:
        value_x1000 = to_int(record.get('value'))
        
        processed_record = {
            'fund_cik': metadata.get('cik'),
            'report_date': to_date(metadata.get('report_date')),
            'filing_date': to_date(metadata.get('filing_date')),
            'cusip': record.get('cusip'),
            'company_name': record.get('nameOfIssuer'),
            'shares': to_int(record.get('sshPrnamt')),
            'value_usd': value_x1000 * 1000 if value_x1000 is not None else None,
            'raw_json': json.dumps(record)
        }
        processed_data.append(processed_record)
        
    return pd.DataFrame(processed_data)

def normalize_form4_data(raw_data: List[Dict[str, Any]], metadata: Dict[str, Any], accession_no: str) -> pd.DataFrame:
    """
    Cleans and normalizes a list of dictionaries from a Form 4 parser
    and aligns it with the Insider_Transactions schema.
    """
    if not raw_data:
        return pd.DataFrame()

    processed_data = []
    for record in raw_data:
        processed_record = {
            'accession_no': accession_no,
            'issuer_cik': record.get('issuer_cik'),
            'issuer_ticker': record.get('issuer_ticker'),
            'insider_cik': metadata.get('cik'), # The CIK from the directory is the insider's
            'insider_name': record.get('reporting_owner_name'),
            'insider_relation': create_insider_relation(record),
            'filing_date': to_date(metadata.get('filing_date')),
            'transaction_date': to_date(record.get('transaction_date')),
            'transaction_code': record.get('transaction_code'),
            'shares': to_int(record.get('shares_transacted')),
            'price_per_share': to_float(record.get('price_per_share')),
            'shares_owned_after': to_int(record.get('shares_owned_after')),
            'raw_json': json.dumps({k: v for k, v in record.items() if not isinstance(v, bool)})
        }
        processed_data.append(processed_record)

    return pd.DataFrame(processed_data)

if __name__ == '__main__':
    # Example usage with updated function signatures and dummy data
    print("--- Testing 13F Data Normalization ---")
    sample_13f = [{'nameOfIssuer': 'TESTCO', 'cusip': '123456789', 'value': '1,500', 'sshPrnamt': '100'}]
    meta_13f = {'cik': '0001234567', 'report_date': '2025-03-31', 'filing_date': '2025-04-15'}
    df_13f = normalize_13f_data(sample_13f, meta_13f)
    print(df_13f)

    print("\n--- Testing Form 4 Data Normalization ---")
    sample_f4 = [{
        'issuer_cik': '111', 'issuer_ticker': 'TCKR', 'reporting_owner_name': 'Insider',
        'is_director': True, 'is_officer': False, 'officer_title': '', 'transaction_date': '2025-01-01', 
        'transaction_code': 'P', 'shares_transacted': '200', 'price_per_share': '123.45', 'shares_owned_after': '1000'
    }]
    meta_f4 = {'cik': '222', 'filing_date': '2025-01-02'}
    df_f4 = normalize_form4_data(sample_f4, meta_f4, '0001-23-456789')
    print(df_f4)
