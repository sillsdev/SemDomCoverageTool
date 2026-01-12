import csv
import sys
from collections import defaultdict
from typing import Dict, List, Set, Tuple

from utils import remove_accents, normalize_reference

def parse_refs_to_set(refs_str: str) -> Set[str]:
    """
    Parse a semicolon-separated reference string into a normalized set.
    Filters out empty strings from normalization.
    
    Args:
        refs_str: String like "Luk 1:1; Luk 1:3" or "LUK 19:2!6; LUK 19:8!3"
        
    Returns:
        Set of normalized individual references
    """
    refs_set = set()
    if refs_str:
        for ref in refs_str.split('; '):
            normalized_ref = normalize_reference(ref)
            if normalized_ref:  # Only add non-empty normalized references
                refs_set.add(normalized_ref)
    return refs_set

def load_key_terms(csv_file: str, verbose: bool = False) -> Dict[str, List[Dict[str, str]]]:
    """
    Load the biblical key terms from luk_terms.csv.
    Multiple key terms can have the same Greek word but different glosses and references.
    
    Args:
        csv_file: Path to the luk_terms.csv file
        verbose: If True, print debug info
        
    Returns:
        Dictionary mapping Term (normalized) to list of {Gloss, Refs_set}
    """
    key_terms = defaultdict(list)
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            if not all(field in reader.fieldnames for field in ['Term', 'Gloss', 'Refs']):
                print("Error: Key terms CSV must contain 'Term', 'Gloss', and 'Refs' columns.")
                print(f"Found columns: {reader.fieldnames}")
                sys.exit(1)
            
            for row in reader:
                term = row['Term'].strip()
                gloss = row['Gloss'].strip()
                refs_str = row['Refs'].strip()
                
                # Parse and normalize references into a set
                refs_set = parse_refs_to_set(refs_str)
                
                # Normalize term by removing accents for accent-insensitive matching
                term_normalized = remove_accents(term)
                
                if verbose:
                    print(f"DEBUG: {term} (normalized: {term_normalized})")
                    print(f"  Raw refs_str: '{refs_str}'")
                    print(f"  Parsed refs_set: {refs_set}")
                
                key_terms[term_normalized].append({
                    'Gloss': gloss,
                    'Refs': refs_set
                })
    except FileNotFoundError:
        print(f"Error: Key terms CSV file not found at '{csv_file}'")
        sys.exit(1)
    
    return dict(key_terms)

def load_word_sem_dom_analysis(csv_file: str) -> List[Dict[str, str]]:
    """
    Load the word/semantic domain analysis CSV file.
    
    Args:
        csv_file: Path to the word_sem_dom_analysis.csv file (produced by wordSemDomAnalysisTool.py)
        
    Returns:
        List of dictionaries with word/semantic domain analysis data
    """
    rows = []
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            if not all(field in reader.fieldnames for field in ['Greek_Word', 'Greek_Forms', 'Refs']):
                print("Error: Word/domain analysis CSV must contain 'Greek_Word', 'Greek_Forms', and 'Refs' columns.")
                sys.exit(1)
            
            for row in reader:
                rows.append(row)
    except FileNotFoundError:
        print(f"Error: Word/domain analysis CSV file not found at '{csv_file}'")
        sys.exit(1)
    
    return rows

def enrich_word_analysis(word_rows: List[Dict[str, str]], key_terms: Dict[str, List[Dict[str, str]]], verbose: bool = False) -> Tuple[List[Dict[str, str]], int, int]:
    """
    Enrich word/domain analysis with key term information.
    For each row, find all key terms matching the Greek_Word.
    If only one matches, use it. If multiple match, pick the one with overlapping refs.
    
    Args:
        word_rows: List of word/domain analysis rows
        key_terms: Dictionary mapping term to list of {Gloss, Refs}
        verbose: If True, print term matches
        
    Returns:
        Tuple of (enriched_rows list, match_count, term_match_no_ref_count)
    """
    enriched_rows = []
    match_count = 0
    term_match_no_ref_count = 0
    
    for row in word_rows:
        greek_word = row['Greek_Word'].strip() # Already normalized
        word_refs_str = row['Refs'].strip()
        word_refs_set = parse_refs_to_set(word_refs_str)
        
        # Check if there's a matching key term (with accent-insensitive comparison)
        meaning = "unknown"
        is_key_term = "no"
        
        if greek_word in key_terms:
            term_entries = key_terms[greek_word]
            
            # If only one key term entry, use it
            if len(term_entries) == 1:
                meaning = term_entries[0]['Gloss']
                is_key_term = "yes"
                match_count += 1
                
                if verbose:
                    print(f"  + {greek_word} → {meaning} (single match)")
            else:
                # Multiple entries - find one with overlapping references
                matched_entry = None
                for entry in term_entries:
                    if word_refs_set & entry['Refs']:  # Set intersection
                        matched_entry = entry
                        break
                
                if matched_entry:
                    meaning = matched_entry['Gloss']
                    is_key_term = "yes"
                    match_count += 1
                    
                    if verbose:
                        print(f"  + {greek_word} → {meaning} (matched by refs)")
                else:
                    # Found term(s) but no overlapping references
                    term_match_no_ref_count += 1
                    if verbose:
                        print(f"  ~ {greek_word} ({len(term_entries)} terms found but no overlapping refs)")
        
        # Create enriched row with new columns after Greek_Forms
        enriched_row = {
            'Greek_Word': row['Greek_Word'],
            'Greek_Forms': row['Greek_Forms'],
            'Meaning': meaning,
            'Is_Key_Term': is_key_term
        }
        
        # Add remaining columns from original row
        for key, value in row.items():
            if key not in ['Greek_Word', 'Greek_Forms']:
                enriched_row[key] = value
        
        enriched_rows.append(enriched_row)
    
    return enriched_rows, match_count, term_match_no_ref_count

def output_results_to_csv(enriched_rows: List[Dict[str, str]], output_filename: str = 'word_analysis.csv'):
    """
    Write enriched word analysis to a tab-separated CSV file.
    
    Args:
        enriched_rows: List of enriched row dictionaries
        output_filename: Output CSV filename
    """
    if not enriched_rows:
        print("Warning: No data to write.")
        return
    
    print(f"\nWriting results to {output_filename}...")
    
    # Use the first row to determine field names in order
    fieldnames = list(enriched_rows[0].keys())
    
    try:
        with open(output_filename, 'w', newline='', encoding='utf-8') as outfile:
            writer = csv.DictWriter(outfile, fieldnames=fieldnames, delimiter='\t', quoting=csv.QUOTE_MINIMAL)
            writer.writeheader()
            
            for row in enriched_rows:
                writer.writerow(row)
        
        print(f"\n**Success!** Enriched word analysis saved to {output_filename}.")
    
    except Exception as e:
        print(f"\nFatal Error during CSV writing: {e}")
        sys.exit(1)


def main():
    verbose = False
    
    # Check for --verbose flag
    if '--verbose' in sys.argv:
        verbose = True
        sys.argv.remove('--verbose')
    
    if len(sys.argv) != 3:
        print("Usage: python wordAnalysisTool.py [--verbose] <key_terms.csv> <word_sem_dom_analysis.csv>")
        print("Example: python wordAnalysisTool.py luk_terms.csv word_sem_dom_analysis.csv")
        print("         python wordAnalysisTool.py --verbose luk_terms.csv word_sem_dom_analysis.csv")
        sys.exit(1)
    
    key_terms_file = sys.argv[1]
    word_domain_file = sys.argv[2]
    
    print("=" * 70)
    print(" Word Analysis with Key Terms")
    if verbose:
        print(" (Verbose Mode)")
    print("=" * 70)
    
    try:
        # 1. Load key terms
        print("Loading key terms from CSV...")
        key_terms = load_key_terms(key_terms_file, verbose)
        print(f"Loaded {len(key_terms)} unique key terms.")
        
        # 2. Load word/domain analysis
        print("Loading word/domain analysis CSV...")
        word_rows = load_word_sem_dom_analysis(word_domain_file)
        print(f"Loaded {len(word_rows)} word/domain analysis rows.")
        
        # 3. Enrich with key term information
        if verbose:
            print("\nTerm Matches:")
        else:
            print("Enriching with key term data...")
        enriched_rows, match_count, term_match_no_ref_count = enrich_word_analysis(word_rows, key_terms, verbose)
        
        # 4. Output the results
        output_results_to_csv(enriched_rows)
        
        # 5. Report results
        print(f"\n**Match Summary:**")
        print(f"  - Key term matches: {match_count}")
        print(f"  - Terms with multiple matches and no common references: {term_match_no_ref_count}")
        print(f"  - Total word instances analyzed: {len(enriched_rows)}")
        
    except Exception as e:
        print(f"\nAn unexpected error occurred during processing: {e}")
        import traceback
        print("\nFull traceback:")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
