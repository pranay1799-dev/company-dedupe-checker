import pandas as pd
import re
from rapidfuzz import process, fuzz
from tqdm import tqdm
import sys
import os
import time

# Settings
COMMON_SUFFIXES = [
    'private limited', 'pvt ltd', 'pvt. ltd.', 'pvt. ltd', 'pvt ltd.', 'pvt.', 'pvt',
    'llp', 'inc', 'corporation', 'limited', 'ltd.', 'ltd', 'co', 'company', 
    'group', 'holdings', 'international', 'enterprises', 'solutions', 
    'services', 'corp', 'incorporated'
]
COMMON_REMOVE_WORDS = ['india', 'INDIA']
SIMILARITY_THRESHOLD = 90  # % match
BATCH_SIZE = 1000  # Process prospects in batches

def normalize_name(name):
    """Normalize company names for comparison."""
    if not isinstance(name, str):
        return ''
        
    # Convert to lowercase
    name = name.lower()
    
    # Remove content within brackets (and the brackets themselves)
    name = re.sub(r'\([^)]*\)', '', name)  # Remove (text)
    name = re.sub(r'\[[^\]]*\]', '', name)  # Remove [text]
    name = re.sub(r'\{[^}]*\}', '', name)  # Remove {text}
    
    # Remove specific words like "India"
    for word in COMMON_REMOVE_WORDS:
        pattern = r'\b' + re.escape(word.lower()) + r'\b'
        name = re.sub(pattern, '', name)
    
    # Remove common suffixes - ensuring exact matches
    for suffix in COMMON_SUFFIXES:
        pattern = r'\b' + re.escape(suffix) + r'\b'
        name = re.sub(pattern, '', name)
    
    # Remove special characters and normalize spaces
    name = re.sub(r'[^a-z0-9 ]', '', name)
    name = re.sub(r'\s+', ' ', name)
    
    return name.strip()

def get_ngrams(name, n=2):
    """Generate n-grams from name for initial filtering."""
    if len(name) < n:
        return {name}
    return {name[i:i+n] for i in range(len(name) - n + 1)}

def create_ngram_index(names, n=2):
    """Create ngram index for faster initial filtering."""
    index = {}
    for name_tuple in names:
        name, norm_name = name_tuple
        if not norm_name:
            continue
        
        # Generate ngrams
        ngrams = get_ngrams(norm_name, n)
        
        # Add to index
        for ngram in ngrams:
            if ngram not in index:
                index[ngram] = []
            index[ngram].append(name_tuple)
    
    return index

def find_candidates(norm_prospect, ngram_index, n=2):
    """Find candidate matches using ngram index."""
    candidates = set()
    if not norm_prospect:
        return candidates
    
    # Get prospect ngrams
    prospect_ngrams = get_ngrams(norm_prospect, n)
    
    # Find names that share at least one ngram
    for ngram in prospect_ngrams:
        if ngram in ngram_index:
            for candidate in ngram_index[ngram]:
                candidates.add(candidate)
    
    return candidates

def process_batch(batch, sf_normalized_dict, ngram_index):
    """Process a batch of prospects."""
    batch_matches = []
    
    for prospect in batch:
        norm_prospect = normalize_name(prospect)
        if not norm_prospect:
            continue
        
        # Get candidates using ngram filtering
        candidates = find_candidates(norm_prospect, ngram_index)
        
        # Check similarity only for candidates
        for existing_name, norm_existing in candidates:
            score = fuzz.ratio(norm_prospect, norm_existing)
            if score >= SIMILARITY_THRESHOLD:
                batch_matches.append({
                    'Prospect': prospect,
                    'Matched Salesforce Entry': existing_name,
                    'Similarity %': score,
                    'Normalized Prospect': norm_prospect,
                    'Normalized Salesforce': norm_existing
                })
    
    return batch_matches

def load_dataframe(file_path, column_name):
    """Load a dataframe from either CSV or Excel file and validate the required column exists."""
    try:
        # Determine file type by extension
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.csv':
            # Try different encodings for CSV
            try:
                df = pd.read_csv(file_path, encoding='utf-8')
            except UnicodeDecodeError:
                try:
                    df = pd.read_csv(file_path, encoding='latin1')
                except UnicodeDecodeError:
                    df = pd.read_csv(file_path, encoding='cp1252')
        elif file_ext in ['.xlsx', '.xls']:
            df = pd.read_excel(file_path)
        else:
            print(f"Error: Unsupported file format: {file_ext}")
            sys.exit(1)
            
        if column_name not in df.columns:
            print(f"Error: Column '{column_name}' not found in {file_path}")
            print(f"Available columns: {', '.join(df.columns)}")
            sys.exit(1)
        return df
    except Exception as e:
        print(f"Error loading {file_path}: {str(e)}")
        sys.exit(1)

# Main
if __name__ == "__main__":
    start_time = time.time()
    
    # File paths
    prospects_path = r"C:\Users\Luna\Desktop\Deplicate_Check\prospects.CSV"
    salesforce_path = r"C:\Users\Luna\Desktop\Deplicate_Check\salesforce_data.xlsx"
    output_path = r"C:\Users\Luna\Desktop\Deplicate_Check\possible_duplicates.csv"
    
    # Column names
    prospect_col = "Company Name"
    sf_col = "Company Name"
    
    # Validate file paths
    for path in [prospects_path, salesforce_path]:
        if not os.path.exists(path):
            print(f"Error: File not found: {path}")
            sys.exit(1)
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    print(f"Loading data files...")
    
    # Load files
    prospects_df = load_dataframe(prospects_path, prospect_col)
    sf_df = load_dataframe(salesforce_path, sf_col)
    
    # Get lists of company names
    prospects_list = prospects_df[prospect_col].dropna().tolist()
    sf_list = sf_df[sf_col].dropna().tolist()
    
    print(f"Loaded {len(prospects_list)} prospects and {len(sf_list)} Salesforce entries")
    
    # Test normalization on a few examples
    print("\nNormalization test examples:")
    test_examples = [
        "Amace Solutions Pvt. Ltd.",
        "Example Company (India) Ltd.",
        "Test Corp [Division] Pvt. Ltd.",
        "ABC {Department} Services INDIA",
        "XYZ Pvt Ltd."
    ]
    for example in test_examples:
        normalized = normalize_name(example)
        print(f"Original: '{example}' → Normalized: '{normalized}'")
    print()  # Empty line after examples
    
    # Pre-normalize Salesforce entries and create tuples
    print("Normalizing Salesforce entries...")
    sf_tuples = [(name, normalize_name(name)) for name in tqdm(sf_list)]
    sf_tuples = [t for t in sf_tuples if t[1]]  # Remove empty normalizations
    
    # Create ngram index for faster matching
    print("Creating search index...")
    ngram_index = create_ngram_index(sf_tuples)
    
    # Process in batches
    matches = []
    batches = [prospects_list[i:i+BATCH_SIZE] for i in range(0, len(prospects_list), BATCH_SIZE)]
    
    print(f"Finding potential duplicates (threshold: {SIMILARITY_THRESHOLD}%)...")
    for i, batch in enumerate(batches):
        print(f"Processing batch {i+1}/{len(batches)} ({len(batch)} prospects)...")
        batch_matches = process_batch(batch, dict(sf_tuples), ngram_index)
        matches.extend(batch_matches)
        print(f"Found {len(batch_matches)} matches in this batch, {len(matches)} total so far")
    
    # Output results
    if matches:
        matches_df = pd.DataFrame(matches)
        matches_df.sort_values('Similarity %', ascending=False, inplace=True)
        matches_df.to_csv(output_path, index=False)
        print(f"✅ Found {len(matches)} potential duplicates. Results saved to '{output_path}'")
    else:
        print("No potential duplicates found!")