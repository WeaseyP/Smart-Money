import shutil
from pathlib import Path

# --- CONFIGURATION ---
# This path should be correct, looking for 'raw_filings' inside 'sec_parser'.
ROOT_PATH = Path("./raw_filings")
DEST_PATH = Path("./sampled_filings")

# --- SCRIPT LOGIC ---

def main():
    """Main function to find, sample, and copy individual filing files."""
    if not ROOT_PATH.exists():
        print(f"Error: Source directory not found at '{ROOT_PATH.resolve()}'")
        print("Please ensure you are running this script from the 'sec_parser' directory.")
        return

    if DEST_PATH.exists():
        print(f"Removing existing destination directory: {DEST_PATH}")
        shutil.rmtree(DEST_PATH)
    DEST_PATH.mkdir(parents=True)
    print(f"Created new destination directory: {DEST_PATH}")

    total_copied = 0
    print("\nStarting dynamic sampling process...")

    # Level 1: Iterate through CIK folders
    for cik_path in sorted(ROOT_PATH.iterdir()):
        if not cik_path.is_dir():
            continue
        print(f"\nProcessing CIK: {cik_path.name}")

        # Level 2: Iterate through form type folders (e.g., '4', '13F-HR')
        for form_path in sorted(cik_path.iterdir()):
            if not form_path.is_dir():
                continue

            # Get a list of all individual FILES inside the form type folder
            files = sorted([p for p in form_path.iterdir() if p.is_file()])
            num_files = len(files)
            
            if num_files == 0:
                continue

            print(f"-> Found Form Type '{form_path.name}' with {num_files} files.")
            
            files_to_copy = set()

            # Apply sampling logic based on the number of files
            if num_files > 10:
                files_to_copy.add(files[0])             # First file
                files_to_copy.add(files[num_files // 2])  # Middle file
                files_to_copy.add(files[-1])            # Last file
            elif num_files > 5:
                files_to_copy.add(files[0])             # First file
                files_to_copy.add(files[-1])            # Last file
            else: # 5 or fewer files
                files_to_copy.add(files[-1])            # Last file

            # Copy the selected individual files
            for file_to_copy in sorted(list(files_to_copy)):
                print(f"  > Copying sample file: {file_to_copy.name}")
                
                dest_file_path = DEST_PATH / file_to_copy.relative_to(ROOT_PATH)
                dest_file_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Use shutil.copy2 for single files
                shutil.copy2(file_to_copy, dest_file_path)
                total_copied += 1
    
    print("\n" + "="*50)
    print("Sampling Complete!")
    print(f"Total files copied: {total_copied}")
    print(f"Samples saved to: {DEST_PATH.resolve()}")
    print("="*50)

if __name__ == "__main__":
    main()