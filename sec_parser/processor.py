from pathlib import Path
import re
from typing import Optional, Dict, Any
from lxml import etree, html
from datetime import datetime

class FileProcessor:
    """
    Processes a single filing to determine its type and extract key metadata.
    """
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.content = self._read_content()
        self.filing_type = self._determine_filing_type()
        self.metadata = self._extract_metadata()

    def _read_content(self) -> str:
        """Reads file content, trying different encodings."""
        try:
            return self.file_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            return self.file_path.read_text(encoding='latin-1')

    def _determine_filing_type(self) -> Optional[str]:
        """
        Determines the filing type by inspecting the file content.
        This is more reliable than trusting file extensions or directory names.
        """
        # The <TYPE> tag is the most reliable indicator.
        type_match = re.search(r'<TYPE>([^<\n]+)', self.content)
        if type_match:
            doc_type = type_match.group(1).strip().upper()
            if '13F-HR' in doc_type: return '13F-HR'
            if '13F-NT' in doc_type: return '13F-NT'
            if '4/A' in doc_type: return '4/A'
            if '4' in doc_type: return '4'
            return doc_type

        # For HTML forms, check which box is checked.
        if re.search(r'\[[Xx]\]\s*13F HOLDINGS REPORT', self.content, re.I): return '13F-HR'
        if re.search(r'\[[Xx]\]\s*13F NOTICE', self.content, re.I): return '13F-NT'
        if re.search(r'[Xx]</span></td>\s*<td.*>13F HOLDINGS REPORT', self.content, re.I): return '13F-HR'
        if re.search(r'[Xx]</span></td>\s*<td.*>13F NOTICE', self.content, re.I): return '13F-NT'

        # Fallback to generic keyword search.
        upper_content = self.content.upper()
        if 'FORM 4/A' in upper_content: return '4/A'
        if 'FORM 4' in upper_content: return '4'
        if '13F NOTICE' in upper_content: return '13F-NT' # Check for NT before HR
        if '13F HOLDINGS REPORT' in upper_content: return '13F-HR'
        if 'FORM 13F-NT' in upper_content: return '13F-NT'
        if 'FORM 13F-HR' in upper_content: return '13F-HR'

        # Fallback for data-only XML files.
        stripped_content = self.content.strip()
        if stripped_content.startswith('<?xml') or stripped_content.lower().startswith('<informationtable'):
            if '<informationTable' in stripped_content or '<infotable' in stripped_content.lower():
                return '13F-HR'

        return None

    def _extract_metadata(self) -> Dict[str, Any]:
        """
        Extracts key metadata from the filing content using a combination of
        regex and structured parsing.
        """
        metadata = {
            'filing_date': self._extract_filing_date(),
            'report_date': self._extract_report_date(),
            'cik': self.file_path.parts[-3] # CIK is in the directory structure
        }
        return metadata

    def _format_date(self, date_str: str, *input_formats: str) -> Optional[str]:
        """Helper to parse and format date strings using multiple formats."""
        for fmt in input_formats:
            try:
                return datetime.strptime(date_str, fmt).strftime('%Y-%m-%d')
            except (ValueError, TypeError):
                continue
        return None

    def _extract_filing_date(self) -> Optional[str]:
        """Extracts the filing date from the document."""
        # Pattern for <ACCEPTANCE-DATETIME> or similar tags
        match = re.search(r'<ACCEPTANCE-DATETIME>(\d{8})', self.content)
        if match:
            return self._format_date(match.group(1), '%Y%m%d')
        
        # Pattern for "FILED AS OF DATE:"
        match = re.search(r'FILED AS OF DATE:\s*(\d{8})', self.content)
        if match:
            return self._format_date(match.group(1), '%Y%m%d')

        # Pattern for "Date of Signing"
        match = re.search(r'Date of Signing:\s*([\d/]+)', self.content, re.I)
        if match:
            return self._format_date(match.group(1).strip(), '%m/%d/%Y', '%m/%d/%y')
            
        # Look for <filingDate> in XML
        try:
            root = html.fromstring(self.content.encode('utf-8'))
            date_val = root.findtext('.//filingdate')
            if date_val:
                return self._format_date(date_val, '%Y-%m-%d', '%m-%d-%Y')
        except etree.XMLSyntaxError:
            pass
            
        return None

    def _extract_report_date(self) -> Optional[str]:
        """Extracts the period of report date, primarily for 13F filings."""
        # Pattern for "Report for the Calendar Year or Quarter Ended:"
        match = re.search(r'Report for the Calendar Year or Quarter Ended:\s*([\d/]+)', self.content, re.I)
        if match:
            return self._format_date(match.group(1).strip(), '%m/%d/%Y', '%m/%d/%y')

        # Look for <periodOfReport> in XML
        try:
            root = html.fromstring(self.content.encode('utf-8'))
            date_val = root.findtext('.//periodofreport')
            if date_val:
                return self._format_date(date_val, '%Y-%m-%d', '%m-%d-%Y')
        except etree.XMLSyntaxError:
            pass

        return None
