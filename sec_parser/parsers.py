from lxml import etree
import re

def parse_form4_xml(xml_content: str) -> list[dict]:
    """
    Parses the XML content of a Form 4 filing.
    """
    try:
        # Remove namespaces for easier parsing
        xml_content = re.sub(r'\sxmlns="[^"]+"', '', xml_content, count=1)
        root = etree.fromstring(xml_content.encode('utf-8'))
    except etree.XMLSyntaxError as e:
        raise ValueError(f"Failed to parse Form 4 XML: {e}")

    transactions = []
    
    # Common data (issuer and owner)
    issuer_cik = root.findtext('.//issuer/issuerCik', default='').strip()
    issuer_name = root.findtext('.//issuer/issuerName', default='').strip()
    issuer_ticker = root.findtext('.//issuer/issuerTradingSymbol', default='').strip()
    
    owner_cik = root.findtext('.//reportingOwner/reportingOwnerId/rptOwnerCik', default='').strip()
    owner_name = root.findtext('.//reportingOwner/reportingOwnerId/rptOwnerName', default='').strip()
    
    # Extract relationship details
    relationship_node = root.find('.//reportingOwner/reportingOwnerRelationship')
    is_director = relationship_node.findtext('isDirector', default='0').strip() == '1'
    is_officer = relationship_node.findtext('isOfficer', default='0').strip() == '1'
    is_ten_percent_owner = relationship_node.findtext('isTenPercentOwner', default='0').strip() == '1'
    officer_title = relationship_node.findtext('officerTitle', default='').strip()

    # Process non-derivative transactions
    for transaction in root.findall('.//nonDerivativeTransaction'):
        data = {
            'issuer_cik': issuer_cik,
            'issuer_name': issuer_name,
            'issuer_ticker': issuer_ticker,
            'reporting_owner_cik': owner_cik,
            'reporting_owner_name': owner_name,
            'is_director': is_director,
            'is_officer': is_officer,
            'is_ten_percent_owner': is_ten_percent_owner,
            'officer_title': officer_title,
            'transaction_date': transaction.findtext('.//transactionDate/value', default='').strip(),
            'transaction_code': transaction.findtext('.//transactionCoding/transactionCode', default='').strip(),
            'shares_transacted': transaction.findtext('.//transactionAmounts/transactionShares/value', default='').strip(),
            'price_per_share': transaction.findtext('.//transactionAmounts/transactionPricePerShare/value', default='').strip(),
            'acquired_disposed_code': transaction.findtext('.//transactionAmounts/transactionAcquiredDisposedCode/value', default='').strip(),
            'shares_owned_after': transaction.findtext('.//postTransactionAmounts/sharesOwnedFollowingTransaction/value', default='').strip(),
        }
        transactions.append(data)
        
    return transactions

def parse_13f_xml(xml_content: str) -> list[dict]:
    """
    Parses the XML content of a modern Form 13F filing (form13fInfoTable.xml).
    """
    try:
        xml_content = re.sub(r'\sxmlns="[^"]+"', '', xml_content, count=1)
        root = etree.fromstring(xml_content.encode('utf-8'))
    except etree.XMLSyntaxError as e:
        raise ValueError(f"Failed to parse 13F XML: {e}")

    holdings = []
    for info_table in root.findall('.//infoTable'):
        data = {
            'name_of_issuer': info_table.findtext('nameOfIssuer', default='').strip(),
            'title_of_class': info_table.findtext('titleOfClass', default='').strip(),
            'cusip': info_table.findtext('cusip', default='').strip(),
            'value_x1000': info_table.findtext('value', default='').strip(),
            'shrs_or_prn_amt': info_table.findtext('.//shrsOrPrnAmt/sshPrnamt', default='').strip(),
            'sh_prn_type': info_table.findtext('.//shrsOrPrnAmt/sshPrnamtType', default='').strip(),
            'investment_discretion': info_table.findtext('investmentDiscretion', default='').strip(),
            'voting_auth_sole': info_table.findtext('.//votingAuthority/Sole', default='').strip(),
            'voting_auth_shared': info_table.findtext('.//votingAuthority/Shared', default='').strip(),
            'voting_auth_none': info_table.findtext('.//votingAuthority/None', default='').strip(),
        }
        holdings.append(data)
        
    return holdings

def parse_13f_text(text_content: str) -> list[dict]:
    """
    Parses the text content of a legacy Form 13F filing.
    """
    holdings = []
    # Regex to find the start of the table data, looking for the header row.
    table_header_regex = re.compile(r'NAME OF ISSUER\s+TITLE OF CLASS\s+CUSIP')
    lines = text_content.splitlines()

    table_started = False
    for line in lines:
        if table_header_regex.search(line):
            table_started = True
            continue
        
        if table_started:
            # Skip the separator line(s)
            if '---' in line:
                continue
            # Stop at the end of the table
            if '</TABLE>' in line or not line.strip():
                break
            
            # Ensure the line has enough characters to avoid IndexError
            if len(line) >= 116:
                holding = {
                    'name_of_issuer': line[0:25].strip(),
                    'title_of_class': line[25:37].strip(),
                    'cusip': line[37:49].strip(),
                    'value_x1000': line[49:58].strip(),
                    'shrs_or_prn_amt': line[58:67].strip(),
                    'sh_prn_type': line[67:70].strip(),
                    'put_call': line[70:74].strip(),
                    'investment_discretion': line[74:83].strip(),
                    'other_manager': line[83:89].strip(),
                    'voting_auth_sole': line[89:98].strip(),
                    'voting_auth_shared': line[98:107].strip(),
                    'voting_auth_none': line[107:116].strip(),
                }
                holdings.append(holding)
    return holdings

if __name__ == '__main__':
    # This block is for testing the parsers directly with the sample files.
    # It will not run when main.py imports this module.
    import json

    print("--- Testing Modern 13F XML Parser ---")
    with open('sample_modern_13f.xml', 'r') as f:
        xml_13f_content = f.read()
    parsed_13f_xml = parse_13f_xml(xml_13f_content)
    print(json.dumps(parsed_13f_xml, indent=2))

    print("\n--- Testing Legacy 13F Text Parser ---")
    with open('sample_legacy_13f.txt', 'r') as f:
        text_13f_content = f.read()
    parsed_13f_text = parse_13f_text(text_13f_content)
    print(json.dumps(parsed_13f_text, indent=2))

    print("\n--- Testing Form 4 XML Parser ---")
    with open('sample_form4.xml', 'r') as f:
        xml_4_content = f.read()
    parsed_form4 = parse_form4_xml(xml_4_content)
    print(json.dumps(parsed_form4, indent=2))
