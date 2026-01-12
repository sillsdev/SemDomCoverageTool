import xml.etree.ElementTree as ET
import csv
import sys
from typing import Dict, List

from utils import BOOK_NUMBERS, BOOK_NAMES, clean_term_id, parse_verse_reference


def load_biblical_terms(xml_file: str) -> List[Dict]:
    """
    Load all biblical terms from the XML file.
    
    Args:
        xml_file: Path to BiblicalTerms.xml
        
    Returns:
        List of dictionaries with term information
    """
    terms = []
    
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
    except FileNotFoundError:
        print(f"Error: XML file not found at '{xml_file}'")
        sys.exit(1)
    except ET.ParseError as e:
        print(f"Error parsing XML file at '{xml_file}': {e}")
        sys.exit(1)
    
    for term_elem in root.findall('.//Term'):
        term_id = term_elem.get('Id', '')
        
        # Extract elements
        gloss_elem = term_elem.find('Gloss')
        domain_elem = term_elem.find('Domain')
        references_elem = term_elem.find('References')
        
        gloss = gloss_elem.text if gloss_elem is not None else ''
        domain = domain_elem.text if domain_elem is not None else ''
        
        # Extract verse references
        verses = []
        if references_elem is not None:
            for verse_elem in references_elem.findall('Verse'):
                if verse_elem.text:
                    verses.append(verse_elem.text.strip())
        
        terms.append({
            'Term_Id': term_id,
            'Gloss': gloss,
            'Domain': domain,
            'Verses': verses
        })
    
    return terms


def filter_and_format_terms(terms: List[Dict], book_name: str) -> List[Dict]:
    """
    Filter terms by book and format the output.
    
    Args:
        terms: List of term dictionaries
        book_name: Book name/abbreviation (case-insensitive)
        
    Returns:
        List of formatted term dictionaries with filtered references
    """
    book_name_lower = book_name.lower()
    print(f"DEBUG: Looking for book: '{book_name}' (lowercase: '{book_name_lower}')")
    
    # Try to find matching book
    book_num = None
    if book_name_lower in BOOK_NAMES:
        book_num = BOOK_NAMES[book_name_lower]
        print(f"DEBUG: Found book by exact match in BOOK_NAMES: {book_name_lower} -> {book_num}")
    elif book_name_lower.replace('á', 'a').replace('é', 'e') in BOOK_NAMES:
        book_num = BOOK_NAMES[book_name_lower.replace('á', 'a').replace('é', 'e')]
        print(f"DEBUG: Found book by accent-removed match: {book_name_lower} -> {book_num}")
    else:
        print(f"Error: Unknown book '{book_name}'")
        print(f"Available books: {', '.join(sorted(BOOK_NAMES.keys()))}")
        sys.exit(1)
    
    # Get the target book abbreviation from the number
    target_book_abbr = BOOK_NUMBERS[book_num]
    print(f"DEBUG: Target book abbreviation: {target_book_abbr} (book number: {book_num})")
    
    result_terms = []
    
    for term in terms:
        filtered_refs = []
        
        for verse_code in term['Verses']:
            parsed = parse_verse_reference(verse_code)
            if parsed:
                found_book_abbr, chapter, verse, word = parsed
                if found_book_abbr == target_book_abbr:
                    filtered_refs.append(f"{found_book_abbr.upper()} {chapter}:{verse}!{word}")
        
        # Only include if there are references in this book
        if filtered_refs:
            result_terms.append({
                'Term_Id': term['Term_Id'],
                'Term': clean_term_id(term['Term_Id']),
                'Gloss': term['Gloss'],
                'Domain': term['Domain'],
                'Refs': "; ".join(filtered_refs)
            })
    
    return result_terms


def output_results_to_csv(terms: List[Dict], book_name: str, output_filename: str = None):
    """
    Write filtered terms to a tab-separated CSV file.
    
    Args:
        terms: List of formatted term dictionaries
        book_name: Book name (for default output filename)
        output_filename: Output CSV filename (optional)
    """
    if output_filename is None:
        output_filename = f"{book_name.lower()}_terms.csv"
    
    print(f"\nWriting results to {output_filename}...")
    
    fieldnames = ['Term_Id', 'Term', 'Gloss', 'Domain', 'Refs']
    
    try:
        with open(output_filename, 'w', newline='', encoding='utf-8') as outfile:
            writer = csv.DictWriter(outfile, fieldnames=fieldnames, delimiter='\t', quoting=csv.QUOTE_MINIMAL)
            writer.writeheader()
            
            for term in terms:
                writer.writerow(term)
        
        print(f"\n**Success!** {len(terms)} terms found in {book_name}. Results saved to {output_filename}.")
    
    except Exception as e:
        print(f"\nFatal Error during CSV writing: {e}")
        sys.exit(1)


def main():
    if len(sys.argv) != 3:
        print("Usage: python biblicalTermsAnalysisTool.py <BiblicalTerms.xml> <book>")
        print("Example: python biblicalTermsAnalysisTool.py BiblicalTerms.xml luk")
        sys.exit(1)
    
    xml_file = sys.argv[1]
    book_name = sys.argv[2]
    
    print("=" * 70)
    print(" Biblical Terms Analysis by Book")
    print("=" * 70)
    
    try:
        # 1. Load all biblical terms
        print("Loading biblical terms from XML...")
        terms = load_biblical_terms(xml_file)
        print(f"Loaded {len(terms)} terms from XML.")
        
        # 2. Filter by book and format references
        print(f"Filtering terms for {book_name}...")
        filtered_terms = filter_and_format_terms(terms, book_name)
        print(f"DEBUG: Successfully filtered {len(filtered_terms)} terms for {book_name}")
        
        # 3. Output to CSV
        output_results_to_csv(filtered_terms, book_name)
        
    except Exception as e:
        print(f"\nAn unexpected error occurred during processing: {e}")
        import traceback
        print("\nFull traceback:")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
