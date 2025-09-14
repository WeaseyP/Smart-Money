from lxml import etree, html
import re
from typing import List, Dict, Any, Optional

# --- Helper Functions ---
def _clean_value(value: Optional[str]) -> Optional[str]:
    if not value: return None
    return re.sub(r'[$,]', '', value).strip()

# --- 13F-HR Parser ---

def _parse_13f_text_table(table_text: str) -> List[Dict[str, Any]]:
    """Parses a pre-formatted text table using a CUSIP-anchored regex."""
    holdings = []
    lines = table_text.strip().split('\n')
    
    separator_index = -1
    for i, line in enumerate(lines):
        if '----' in line and 'CUSIP' in lines[i-1]:
            separator_index = i
            break
    if separator_index == -1: return []

    # Regex to find a CUSIP and capture the text before and after.
    # CUSIPs are 9 chars, but can sometimes be 8 in older filings.
    cusip_regex = re.compile(r'\b([A-Z0-9]{8,9})\b')
    
    for line in lines[separator_index + 1:]:
        if not line.strip() or '<' in line or '---' in line: continue

        match = cusip_regex.search(line)
        if not match: continue
            
        cusip = match.group(1)
        # The issuer/title is everything before the CUSIP.
        issuer_and_title = line[:match.start()].strip()
        # The rest of the data is after the CUSIP.
        other_cols_str = line[match.end():].strip()
        
        # Split the remaining columns by multiple spaces.
        other_cols = re.split(r'\s{2,}', other_cols_str)
        
        # We expect at least value and shares.
        if len(other_cols) < 2: continue
            
        holding = {
            'nameOfIssuer': issuer_and_title,
            'cusip': cusip,
            'value': _clean_value(other_cols[0]),
            'sshPrnamt': _clean_value(other_cols[1]),
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

def parse_13f_hr(content: str, file_path_str: str) -> List[Dict[str, Any]]:
    """Dispatches 13F-HR parsing to the correct function based on content."""
    if content.strip().startswith('<?xml'):
        return _parse_13f_xml_infotable(content)
    
    try:
        root = html.fromstring(content.encode('utf-8'))
        for element in root.xpath('//table | //pre'):
            text = element.text_content()
            if 'CUSIP' in text.upper() and 'VALUE' in text.upper():
                return _parse_13f_text_table(text)
    except etree.XMLSyntaxError:
        if 'CUSIP' in content.upper() and 'VALUE' in content.upper():
            return _parse_13f_text_table(content)
    return []

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
