from lxml import etree, html
import re
from typing import List, Dict, Any, Optional
import logging

# --- Helper Functions ---
def _clean_value(value: Optional[str]) -> Optional[str]:
    if not value: return None
    return re.sub(r'[$,]', '', value).strip()

# --- 13F-HR Parser ---

def _parse_13f_text_table(table_text: str) -> List[Dict[str, Any]]:
    """
    Parses a pre-formatted text table by dynamically determining column positions
    from the header, making it robust to spacing variations and multi-line headers.
    """
    holdings = []
    lines = table_text.strip().split('\n')

    # --- Header Detection Logic ---
    header_block = []
    data_start_index = -1
    in_header = False
    for i, line in enumerate(lines):
        upper_line = line.upper()
        is_header_keyword_line = any(kw in upper_line for kw in ['CUSIP', 'VALUE', 'ISSUER', 'SHARES', 'VOTING AUTHORITY'])
        
        if is_header_keyword_line and len(upper_line) < 200:
            header_block.append(line)
            in_header = True
        elif in_header:
            if '---' in line or re.search(r'^[<A-Z0-9]', line.strip()) or not line.strip():
                data_start_index = i
                break
    
    if not header_block:
        logging.warning("Text table parser failed: Header block not found.")
        return []

    if data_start_index == -1:
        data_start_index = len(header_block)

    # --- Column Position Calculation ---
    cusip_line_str = next((l for l in header_block if 'CUSIP' in l.upper()), header_block[-1])
    value_line_str = next((l for l in header_block if 'VALUE' in l.upper()), header_block[-1])
    shares_line_str = next((l for l in header_block if re.search('SHARES|SHRS|PRN AMT', l.upper())), cusip_line_str)

    cusip_match = re.search(r'\bCUSIP\b', cusip_line_str, re.I)
    value_match = re.search(r'\bVALUE\b', value_line_str, re.I)
    shares_match = re.search(r'SHARES/|SHARES|SHRS\s+OR\s+PRN\s+AMT|PRN\s+AMT|SHRSORPRNAMT|SH\b', shares_line_str, re.I)

    if not all([cusip_match, value_match, shares_match]):
        logging.warning(f"Text table parser failed: Essential columns not found in header. CUSIP:{bool(cusip_match)}, VALUE:{bool(value_match)}, SHARES:{bool(shares_match)}.")
        return []

    pos = {
        'nameOfIssuer_end': cusip_match.start(),
        'cusip_start': cusip_match.start(),
        'cusip_end': value_match.start(),
        'value_start': value_match.start(),
        'value_end': shares_match.start(),
        'shares_start': shares_match.start(),
    }

    next_col_match = re.search(r'\b(SH|PUT|CALL|INVESTMENT|DISCRETION|SOLE)\b', cusip_line_str[pos['shares_start']+1:], re.I)
    if next_col_match:
        pos['shares_end'] = pos['shares_start'] + next_col_match.start()
    else:
        pos['shares_end'] = pos['shares_start'] + 15

    if data_start_index < len(lines) and '---' in lines[data_start_index]:
        data_start_index += 1

    # --- Data Line Parsing ---
    for line in lines[data_start_index:]:
        if len(line.strip()) < 20 or '---' in line or re.fullmatch(r'<[A-Z]>', line.strip()):
            continue

        name_of_issuer = line[:pos['nameOfIssuer_end']].strip()
        cusip = line[pos['cusip_start']:pos['cusip_end']].strip()
        value = line[pos['value_start']:pos['value_end']].strip()
        shares = line[pos['shares_start']:pos['shares_end']].strip()

        if not name_of_issuer or not re.match(r'^[A-Z0-9]{8,9}$', cusip, re.I):
            logging.warning(f"Skipping row due to invalid data. Raw line: '{line.strip()}'")
            continue

        holding = {
            'nameOfIssuer': name_of_issuer,
            'cusip': cusip,
            'value': _clean_value(value),
            'sshPrnamt': _clean_value(shares),
        }
        holdings.append(holding)

    return holdings

def _parse_13f_xml_infotable(xml_content: str) -> List[Dict[str, Any]]:
    """Parses the modern form13fInfoTable.xml format."""
    try:
        clean_xml = re.sub(r'\sxmlns="[^"]+"', '', xml_content, count=1)
        root = etree.fromstring(clean_xml.encode('utf-8'))
    except etree.XMLSyntaxError: return []

    holdings = []
    for info_table in root.findall('.//infoTable'):
        data = {
            'nameOfIssuer': info_table.findtext('nameOfIssuer'),
            'cusip': info_table.findtext('cusip'),
            'value': _clean_value(info_table.findtext('value')),
            'sshPrnamt': _clean_value(info_table.findtext('.//shrsOrPrnAmt/sshPrnamt')),
            'sshPrnamtType': info_table.findtext('.//shrsOrPrnAmt/sshPrnamtType'),
        }
        holdings.append({k: v.strip() if isinstance(v, str) else v for k, v in data.items()})
    return holdings

def parse_13f_hr(content: str, file_path_str: str) -> Optional[List[Dict[str, Any]]]:
    """
    Dispatches 13F-HR parsing based on content.
    Returns a list of holdings, an empty list if no holdings are found,
    or None if the file is identified as a cover page without a data table.
    """
    stripped_content = content.strip()
    # Check for XML declaration or root element of an information table
    if stripped_content.startswith('<?xml') or stripped_content.lower().startswith('<informationtable'):
        return _parse_13f_xml_infotable(content)

    # Attempt to parse as HTML and find a text-based table
    try:
        root = html.fromstring(content.encode('utf-8'))
        for element in root.xpath('//table | //pre'):
            text = element.text_content()
            if 'CUSIP' in text.upper() and 'VALUE' in text.upper():
                return _parse_13f_text_table(text)
    except etree.XMLSyntaxError:
        # Fallback for content that isn't valid HTML.
        # Use regex to find the table text, as the document may be malformed.
        table_match = re.search(r'<TABLE>([\s\S]*?)<\/TABLE>', content, re.I)
        if table_match:
            table_text = table_match.group(1)
            if 'CUSIP' in table_text.upper() and 'VALUE' in table_text.upper():
                return _parse_13f_text_table(table_text)
        # If no <TABLE> tag, try a broader search on the whole content
        elif 'CUSIP' in content.upper() and 'VALUE' in content.upper():
            return _parse_13f_text_table(content)

    # If no holdings table is found, check if it's just a cover page
    upper_content = content.upper()
    if 'FORM 13F COVER PAGE' in upper_content or 'FORM 13F SUMMARY PAGE' in upper_content:
        return None  # Signal that this is a cover page, not a parsing failure

    return []  # Return empty list if it's not a cover page but has no data

# --- Form 4 Parser ---

def parse_form4(content: str) -> List[Dict[str, Any]]:
    """Parses a Form 4 or 4/A filing."""
    try:
        root = html.fromstring(content.encode('utf-8'))
    except etree.XMLSyntaxError: return []

    if root.xpath('.//nonderivativetransaction'):
        transactions = []
        base_info = {'issuer_ticker': root.findtext('.//issuer/issuertradingsymbol')}
        for tx in root.findall('.//nonDerivativeTransaction'):
            data = base_info.copy()
            data.update({
                'security_title': tx.findtext('.//securitytitle/value'),
                'transaction_date': tx.findtext('.//transactiondate/value'),
                'transaction_code': tx.findtext('.//transactioncoding/transactioncode'),
                'shares_transacted': _clean_value(tx.findtext('.//transactionamounts/transactionshares/value')),
                'price_per_share': _clean_value(tx.findtext('.//transactionamounts/transactionpricepershare/value')),
                'shares_owned_after': _clean_value(tx.findtext('.//posttransactionamounts/sharesownedfollowingtransaction/value')),
            })
            transactions.append(data)
        return transactions

    transactions = []
    issuer_ticker_match = re.search(r'Ticker or Trading Symbol.*\[\s*(.*?)\s*\]', content)
    issuer_ticker = issuer_ticker_match.group(1) if issuer_ticker_match else None
    table1 = root.xpath('//table[.//b[contains(text(), "Table I - Non-Derivative")]]')
    if table1:
        for row in table1[0].xpath('.//tr[count(td) > 7]'):
            cells = row.xpath('.//td')
            transactions.append({
                'issuer_ticker': issuer_ticker,
                'security_title': cells[0].text_content().strip(),
                'transaction_date': cells[1].text_content().strip(),
                'transaction_code': cells[3].text_content().strip(),
                'shares_transacted': _clean_value(cells[5].text_content()),
                'price_per_share': _clean_value(cells[7].text_content()),
                'shares_owned_after': _clean_value(cells[8].text_content()),
            })
    return transactions
