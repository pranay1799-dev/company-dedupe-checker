# company-dedupe-checker
Instructions for Running the Company Name Deduplication Tool
Prerequisites

Make sure Python is installed on your computer (version 3.6 or later)
You'll need to install these Python packages:
pip install pandas rapidfuzz tqdm openpyxl


Setup

Save the Python script to a file named duplicate_checker.py
Have your data files ready:

An Excel file with your prospects (containing a "Company Name" column)
An Excel file with your Salesforce data (containing a "Company Name" column)



Steps to Run the Tool

Open the script in a text editor and verify/update these file paths:
python# File paths - update these to match your actual file locations
prospects_path = r"C:\Users\Luna\Desktop\Deplicate_Check\prospects.xlsx"
salesforce_path = r"C:\Users\Luna\Desktop\Deplicate_Check\salesforce_data.xlsx"
output_path = r"C:\Users\Luna\Desktop\Deplicate_Check\possible_duplicates.csv"

Also verify the column names match your data:
python# Column names
prospect_col = "Company Name"  # Column in prospects file with company names
sf_col = "Name"  # Column in Salesforce file with company names

Open Command Prompt or PowerShell and navigate to the folder where you saved the script:
cd C:\path\to\script\folder

Run the script:
python duplicate_checker.py

The script will show progress information as it runs

It first loads both data files
Tests the normalization on some examples
Then processes the data in batches
Finally saves matches to the output file


When complete, check the output CSV file for potential duplicates:

Each row shows a prospect that potentially matches a Salesforce entry
The "Similarity %" column shows how closely they match (90-100%)
Higher percentages indicate more likely duplicates



Customization Options
If needed, you can adjust these settings in the script:

SIMILARITY_THRESHOLD = 90 - Change to require higher/lower match confidence
COMMON_SUFFIXES - Add/remove business suffixes that should be ignored
COMMON_REMOVE_WORDS - Add/remove words that should be completely ignored

Troubleshooting

If you get errors about missing columns, verify the column names in your Excel files
If processing is too slow, try reducing the dataset size or increasing batch size
If you get file not found errors, double-check all file paths
