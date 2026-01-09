import csv
import sys
from typing import Dict, List

def load_ln_mapping(csv_file: str) -> Dict[str, Dict[str, str]]:
    """
    Load the LN code to semantic domain mapping from CSV.
    
    Args:
        csv_file: Path to the CSV file
        
    Returns:
        Dictionary mapping base LN codes (e.g., '10A') to semantic domain info
    """
    ln_map = {}
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            # Basic field validation
            if not all(field in reader.fieldnames for field in ['LouwNida_Code', 'SemDom', 'SemDom_Name']):
                print("Error: CSV must contain 'LouwNida_Code', 'SemDom', and 'SemDom_Name' columns.")
                sys.exit(1)

            for row in reader:
                full_code = row['LouwNida_Code'].strip().strip('"')
                
                # Extract just the code at the beginning (e.g., "1", "10A", "10B")
                # by taking everything before the first space
                ln_code = full_code.split()[0] if ' ' in full_code else full_code
                
                ln_map[ln_code] = {
                    'SemDom': row['SemDom'].strip(),
                    'SemDom_Name': row['SemDom_Name'].strip()
                }
    except FileNotFoundError:
        print(f"Error: Mapping CSV file not found at '{csv_file}'")
        sys.exit(1)
        
    return ln_map

def load_word_louw_nida_analysis(csv_file: str) -> List[Dict[str, str]]:
    """
    Load the word/LN analysis CSV file.
    
    Args:
        csv_file: Path to the word_louw_nida_analysis.csv file
        
    Returns:
        List of dictionaries with word/LN analysis data
    """
    rows = []
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            # Basic field validation
            if not all(field in reader.fieldnames for field in ['Greek_Word', 'Ln_Domain', 'Total_Unique_References', 'Refs']):
                print("Error: CSV must contain 'Greek_Word', 'Ln_Domain', 'Total_Unique_References', and 'Refs' columns.")
                sys.exit(1)

            for row in reader:
                rows.append(row)
    except FileNotFoundError:
        print(f"Error: Word/LN analysis CSV file not found at '{csv_file}'")
        sys.exit(1)
        
    return rows

def output_results_to_csv(enriched_data: List[Dict[str, str]], output_filename: str = 'word_sem_dom_analysis.csv'):
    """
    Writes the enriched word/domain data to a tab-separated CSV file.
    
    Args:
        enriched_data: List of dictionaries with enriched word/domain data
        output_filename: Output CSV filename
    """
    
    print(f"\nWriting results to {output_filename}...")
    
    fieldnames = [
        'Greek_Word',
        'Greek_Forms',
        'SemDom',
        'SemDom_Name',
        'Total_Unique_References',
        'Refs'
    ]
    
    try:
        with open(output_filename, 'w', newline='', encoding='utf-8') as outfile:
            writer = csv.DictWriter(outfile, fieldnames=fieldnames, delimiter='\t', quoting=csv.QUOTE_MINIMAL)
            writer.writeheader()
            
            for row in enriched_data:
                writer.writerow(row)
                
        print(f"\n**Success!** Word/domain analysis saved to {output_filename}.")
    
    except Exception as e:
        print(f"\nFatal Error during CSV writing: {e}")
        sys.exit(1)


def main():
    if len(sys.argv) != 3:
        print("Usage: python wordSemDomAnalysisTool.py <word_louw_nida_analysis.csv> <ln_mapping.csv>")
        print("Example: python wordSemDomAnalysisTool.py word_louw_nida_analysis.csv LouwNidaToSemDom.csv")
        sys.exit(1)
    
    word_ln_file = sys.argv[1]
    mapping_file = sys.argv[2]
    
    print("=" * 70)
    print(" Word/Domain Analysis")
    print("=" * 70)
    
    try:
        # 1. Load the LN -> SemDom mapping from the CSV
        print("Loading LN mapping from CSV...")
        ln_mapping = load_ln_mapping(mapping_file)
        print(f"Loaded {len(ln_mapping)} base LN codes from mapping CSV.")
        
        # 2. Load the word/LN analysis CSV
        print("Loading word/LN analysis CSV...")
        word_ln_rows = load_word_louw_nida_analysis(word_ln_file)
        print(f"Loaded {len(word_ln_rows)} word/LN pairs from analysis CSV.")
        
        # 3. Enrich data with semantic domain information
        print("Enriching with semantic domain data...")
        enriched_data = []
        unmatched_codes = set()
        
        for row in word_ln_rows:
            ln_domain = row['Ln_Domain']
            
            # Split semicolon-separated LN codes
            ln_codes = [code.strip() for code in ln_domain.split(';') if code.strip()]
            
            # Look up each LN code and collect results
            sem_doms = []
            sem_dom_names = []
            
            for ln_code in ln_codes:
                csv_info = None
                
                if ln_code in ln_mapping:
                    csv_info = ln_mapping[ln_code]
                else:
                    # If unmatched and has a letter/prime at the end, try without it
                    if ln_code and (ln_code[-1].isalpha() or ln_code[-1] == "'" or ln_code[-1] == '"'):
                        # Strip trailing letters and primes
                        base = ln_code.rstrip("ABCDEFGHIJKLMNOPQRSTUVWXYZ'\"")
                        if base and base in ln_mapping:
                            csv_info = ln_mapping[base]
                
                if csv_info:
                    sem_doms.append(csv_info['SemDom'])
                    sem_dom_names.append(csv_info['SemDom_Name'])
                else:
                    unmatched_codes.add(ln_code)
            
            # Create enriched row
            enriched_row = {
                'Greek_Word': row['Greek_Word'],
                'Greek_Forms': row['Greek_Forms'],
                'SemDom': ';'.join(sem_doms) if sem_doms else '',
                'SemDom_Name': ';'.join(sem_dom_names) if sem_dom_names else '',
                'Total_Unique_References': row['Total_Unique_References'],
                'Refs': row['Refs']
            }
            enriched_data.append(enriched_row)

        # 4. Output the results to the new CSV file
        output_results_to_csv(enriched_data)
        
        # 5. Report Unmatched Codes
        if unmatched_codes:
            print("\n" + "=" * 70)
            print(f"WARNING: {len(unmatched_codes)} UNMATCHED LN CODES FOUND")
            print("These codes were in the word/LN analysis but had no match in the mapping.")
            print("=" * 70)
            for code in sorted(unmatched_codes):
                print(f"  - {code}")
        
    except Exception as e:
        print(f"\nAn unexpected error occurred during processing: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
