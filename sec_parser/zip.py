import zipfile
import os

# The path to your downloaded submissions file
zip_path = 'submissions.zip'

# The folder where you want to save the extracted JSON files
output_dir = 'fund_data'
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# The list of "smart money" CIKs you are tracking
target_ciks = [
    '0000904495',  
    '0001517137',  
    '0001345471',
    '0001336528',
    '0001351069',
    '0001067983',
    '0001112520',
    '0001571785',
    '0001709323',
    '0001061768',
    '0000807985',
    '0001720792',
    '0000029440',
    '0001325447',
    '0001079114',
    '0001582090',
    '0001159159',
    '0001559771'
    ]

print("Starting to scan the zip archive...")

# Open the zip file for reading
with zipfile.ZipFile(zip_path, 'r') as zf:
    # Get a list of all files in the zip
    all_files = zf.namelist()
    
    # Loop through each target CIK
    for cik in target_ciks:
        # Construct the filename we are looking for
        target_file = f'CIK{cik}.json'
        
        # Check if this file exists in the archive
        if target_file in all_files:
            print(f"Found: {target_file}. Extracting...")
            # Extract just this one file to your output directory
            zf.extract(target_file, path=output_dir)
        else:
            print(f"Warning: Could not find file for CIK {cik}")

print("Extraction complete.")