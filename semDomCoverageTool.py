import xml.etree.ElementTree as ET
import csv
import sys
import re
from collections import defaultdict
from typing import Dict, Any, Set, List, Tuple

def parse_ln_code(ln_code: str) -> str:
    """
    Extract domain number from LN code for matching against the CSV mapping.
    Converts '89.32' to '89', keeps '92a' as '92A', keeps '10' as '10'.
    
    Args:
        ln_code: Format like '89.32', '92a', or '89'
        
    Returns:
        Base domain number with optional letter (e.g., '89', '92A', '10')
    """
    if '.' in ln_code:
        return ln_code.split('.')[0]
    
    return ln_code.upper()

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
            reader = csv.DictReader(f)
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

def extract_ln_data_from_xml(xml_file: str) -> List[Tuple[str, str, str]]:
    """
    Extracts the LN code, word, and reference from all <w> elements in the XML.
    
    Args:
        xml_file: Path to the XML file
        
    Returns:
        A list of tuples: [(full_ln_code, word, reference), ...]
    """
    xml_data = []
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
    except FileNotFoundError:
        print(f"Error: XML file not found at '{xml_file}'")
        sys.exit(1)
    except ET.ParseError as e:
        print(f"Error parsing XML file at '{xml_file}': {e}")
        sys.exit(1)

    # Search for all <w> elements anywhere in the document
    for word_element in root.findall('.//w'):
        # Extract data from attributes and text content
        ln_code_full = word_element.get('ln', '').strip()
        word = word_element.text.strip() if word_element.text else ""
        reference = word_element.get('ref', '').strip()

        # If any essential piece of data is missing, skip the element
        if ln_code_full and word and reference:
            # Handle potential multiple LN codes in one 'ln' attribute (e.g., "89.32 92.1")
            for code in ln_code_full.split():
                if code.strip():
                    xml_data.append((code.strip(), word, reference))

    return xml_data

def output_results_to_csv(aggregated_data: Dict[str, Any], output_filename: str = 'semantic_domains_coverage.csv'):
    """
    Writes the aggregated semantic domain data, including word/reference lists, to a CSV file.
    """
    
    print(f"\nWriting results to {output_filename}...")
    
    fieldnames = [
        'SemDom', 
        'SemDom_Name', 
        'Total_Ln_Decimal_Codes',
        'Total_Unique_Words',
        'Total_Unique_References',
        'Ln_Decimal_Codes_Mapped',
        'Associated_Words_With_Refs'
    ]
    
    try:
        with open(output_filename, 'w', newline='', encoding='utf-8') as outfile:
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()
            
            # Write rows, sorted by Semantic Domain code
            for sem_dom in sorted(aggregated_data.keys()):
                data = aggregated_data[sem_dom]
                
                # Format word-reference pairs
                word_refs_list = []
                for word in sorted(data['WordToRefs'].keys()):
                    refs = sorted(data['WordToRefs'][word])
                    refs_str = "; ".join(refs)
                    word_refs_list.append(f"{word} ({refs_str})")
                
                words_with_refs_str = "|".join(word_refs_list)
                ln_codes_str = ", ".join(sorted(list(data['Ln_Decimal_Codes'])))
                
                row = {
                    'SemDom': sem_dom,
                    # Note: SemDom_Name is a set in aggregation, use the first one found or join them
                    'SemDom_Name': next(iter(data['SemDom_Name'])) if data['SemDom_Name'] else '',
                    'Total_Ln_Decimal_Codes': len(data['Ln_Decimal_Codes']),
                    'Total_Unique_Words': len(data['WordToRefs']),
                    'Total_Unique_References': len(data['AllReferences']),
                    'Ln_Decimal_Codes_Mapped': ln_codes_str,
                    'Associated_Words_With_Refs': words_with_refs_str
                }
                writer.writerow(row)
                
        print(f"\n**Success!** Enhanced analysis saved to {output_filename}.")
    
    except Exception as e:
        print(f"\nFatal Error during CSV writing: {e}")
        sys.exit(1)


def main():
    if len(sys.argv) != 3:
        print("Usage: python script.py <ln_mapping_csv_file> <annotated_xml_file>")
        print("Example: python script.py louw_nida_mapping.csv your_file.xml")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    xml_file = sys.argv[2]
    
    print("=" * 70)
    print(" Louw-Nida/Semantic Domain Enhanced Analysis")
    print("=" * 70)
    
    try:
        # 1. Load the LN -> SemDom mapping from the CSV
        print("Loading LN mapping from CSV...")
        ln_mapping = load_ln_mapping(csv_file)
        print(f"Loaded {len(ln_mapping)} base LN codes from CSV.")
        
        # 2. Extract detailed data (LN code, word, ref) from XML
        print("Extracting word and reference data from XML...")
        xml_ln_data = extract_ln_data_from_xml(xml_file)
        print(f"Found {len(xml_ln_data)} LN-annotated words in XML.")
        
        # 3. Aggregate data by Semantic Domain (SemDom)
        aggregated_data = defaultdict(lambda: {
            'SemDom_Name': set(),
            'Ln_Decimal_Codes': set(),
            'WordToRefs': defaultdict(set),  # word -> set of references
            'AllReferences': set()
        })
        unmatched_codes = set()

        for full_ln_code, word, reference in xml_ln_data:
            base_ln_code = parse_ln_code(full_ln_code)

            if base_ln_code in ln_mapping:
                csv_info = ln_mapping[base_ln_code]
                
                # SemDom and SemDom_Name can be ';' separated, so we split them
                sem_doms = csv_info['SemDom'].split(';')
                sem_dom_names = csv_info['SemDom_Name'].split(';')

                # Iterate through all mapped semantic domains
                for sem_dom, sem_dom_name in zip(sem_doms, sem_dom_names):
                    sem_dom = sem_dom.strip()
                    sem_dom_name = sem_dom_name.strip()

                    # Aggregate data
                    aggregated_data[sem_dom]['SemDom_Name'].add(sem_dom_name)
                    aggregated_data[sem_dom]['Ln_Decimal_Codes'].add(full_ln_code)
                    aggregated_data[sem_dom]['WordToRefs'][word].add(reference)
                    aggregated_data[sem_dom]['AllReferences'].add(reference)
            else:
                unmatched_codes.add(f"{full_ln_code} (Base: {base_ln_code})")
                
        print(f"Aggregated data for {len(aggregated_data)} unique Semantic Domains.")

        # 4. Output the results to the new CSV file
        output_results_to_csv(aggregated_data)
        
        # 5. Report Unmatched Codes
        if unmatched_codes:
            print("\n" + "=" * 70)
            print(f"WARNING: {len(unmatched_codes)} UNMATCHED LN CODES FOUND")
            print("These codes were in the XML but had no match in the CSV mapping.")
            print("=" * 70)
            # Only print a few to keep console clean
            for i, code in enumerate(sorted(unmatched_codes)):
                if i < 10:
                    print(f"  - {code}")
            if len(unmatched_codes) > 10:
                print(f"  ...and {len(unmatched_codes) - 10} more.")
        
    except Exception as e:
        print(f"\nAn unexpected error occurred during processing: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()