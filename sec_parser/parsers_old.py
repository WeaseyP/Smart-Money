import xml.etree.ElementTree as ET
import json
import re

def parse_13f_filing(file_content):
    """
    Parses the raw content of a 13F-HR or 13F-NT filing.

    Args:
        file_content (str): A string containing the full content of the filing file,
                            which may be wrapped in HTML.

    Returns:
        list: A list of dictionaries, where each dictionary represents a holding
              and is structured to match the Quarterly_Holdings table schema.
              Returns an empty list if parsing fails.
    """
    holdings = []
    
    try:
        # This regex correctly isolates the <informationTable> block.
        info_table_match = re.search(
            r'<((?:\w+:)?informationTable)[^>]*>.*?</\1>',
            file_content, 
            re.DOTALL | re.IGNORECASE
        )

        if not info_table_match:
            print("Warning: Could not find the <informationTable> XML block in the document.")
            return []

        xml_block = f"<root>{info_table_match.group(0)}</root>"
        xml_block = xml_block.replace('&', '&amp;')

        root = ET.fromstring(xml_block)

        info_table_elem = root.find('.//{*}informationTable')
        
        if info_table_elem is None:
            print("Warning: Failed to find <informationTable> after isolating XML block.")
            return []

        for holding_elem in info_table_elem:
            if 'infoTable' not in holding_elem.tag:
                continue

            holding_data = {}
            
            # --- CORRECTED HELPER FUNCTION ---
            # This version manually iterates to find tags, avoiding unsupported XPath.
            def find_text(parent, tag_name):
                if parent is None:
                    return None
                # Iterate through all descendants of the parent element
                for child in parent.iter():
                    # The tag name includes the namespace in {..} braces, so we split it off.
                    local_tag = child.tag.split('}')[-1]
                    if local_tag == tag_name:
                        return child.text.strip() if child.text is not None else None
                return None # Return None if the tag wasn't found

            # Find the direct parent of sshPrnamt and sshPrnamtType
            shrs_or_prn_amt_elem = None
            for elem in holding_elem.iter():
                 if elem.tag.endswith('shrsOrPrnAmt'):
                     shrs_or_prn_amt_elem = elem
                     break

            # Extract data using the corrected helper
            holding_data['name_of_issuer'] = find_text(holding_elem, 'nameOfIssuer')
            holding_data['cusip'] = find_text(holding_elem, 'cusip')
            value_str = find_text(holding_elem, 'value')
            shares_str = find_text(shrs_or_prn_amt_elem, 'sshPrnamt')
            share_type_str = find_text(shrs_or_prn_amt_elem, 'sshPrnamtType')

            if value_str:
                holding_data['value'] = int(value_str.replace(',', '')) * 1000
            if shares_str:
                holding_data['shares'] = int(shares_str.replace(',', ''))
            if share_type_str:
                holding_data['share_type'] = share_type_str

            if holding_data.get('cusip') and holding_data.get('shares'):
                holdings.append(holding_data)

    except ET.ParseError as e:
        print(f"XML Parse Error after cleaning: {e}")
        return []
    except Exception as e:
        print(f"An unexpected error occurred during parsing: {e}")
        # For debugging, you might want to print the full traceback
        # import traceback
        # traceback.print_exc()
        return []
        
    return holdings

def parse_form4_filing(xml_content):
    """
    (Placeholder) Parses the raw XML content of a Form 4 filing.
    """
    print("Form 4 parser not yet implemented.")
    return {}