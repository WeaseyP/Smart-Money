import os
import re
import shutil
from pathlib import Path

def main():
    """
    Reads the parser_issues.log file, extracts the paths of problematic filings,
    and copies them into a 'parser_error' directory for easier review.
    """
    log_file = Path('../parser_issues.log')
    source_root = Path('sampled_filings')
    dest_root = Path('parser_error')
    
    if not log_file.exists():
        print(f"Error: Log file not found at '{log_file}'. Please run the main parser first.")
        return

    # Ensure the destination directory exists
    dest_root.mkdir(exist_ok=True)
    
    print(f"Reading log file: {log_file}")
    
    # Regex to extract the relative file path from a log line
    path_regex = re.compile(r'file: (.*)$')
    
    copied_files = set()

    with open(log_file, 'r') as f:
        for line in f:
            match = path_regex.search(line)
            if match:
                relative_path_str = match.group(1).strip()
                # Handle both Windows and Linux paths that might be in the log
                relative_path = Path(relative_path_str.replace('\\', '/'))
                
                source_path = source_root / relative_path
                
                # The relative path includes CIK and Form Type, so we build the dest path
                dest_path = dest_root / relative_path
                
                if source_path in copied_files:
                    continue

                if source_path.exists():
                    # Create the parent directories in the destination
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    print(f"Copying '{source_path}' to '{dest_path}'")
                    shutil.copy(source_path, dest_path)
                    copied_files.add(source_path)
                else:
                    print(f"Warning: Source file not found: '{source_path}'")

    print(f"\nDone. Copied {len(copied_files)} unique files to the '{dest_root}' directory.")

if __name__ == '__main__':
    main()
