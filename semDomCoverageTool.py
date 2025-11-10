import xml.etree.ElementTree as ET
import csv
from collections import defaultdict

def parse_ln_code(ln_code):
    """
    Extract domain number from LN code for matching.
    Converts '89.32' to '89', keeps '92a' as '92A', keeps '10' as '10'.
    
    Args:
        ln_code: Format like '89.32', '92a', or '89'
    
    Returns:
        Domain number with optional letter (e.g., '89', '92A', '10')
    """
    # If it has a dot, take everything before it
    if '.' in ln_code:
        return ln_code.split('.')[0]
    
    # Otherwise, just uppercase it (keeps letters if present)
    return ln_code.upper()

def load_ln_mapping(csv_file):
    """
    Load the LN code to semantic domain mapping from CSV.
    Extracts the LN code from the beginning of the LouwNida_Code field.
    
    Args:
        csv_file: Path to the CSV file
    
    Returns:
        Dictionary mapping LN letter codes to semantic domain info
    """
    ln_map = {}
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            full_code = row['LouwNida_Code']
            sem_dom = row['SemDom']
            sem_dom_name = row['SemDom_Name']
            
            # Extract just the code at the beginning (e.g., "1", "10A", "10B")
            # by taking everything before the first space
            ln_code = full_code.split()[0] if ' ' in full_code else full_code
            
            ln_map[ln_code] = {
                'SemDom': sem_dom,
                'SemDom_Name': sem_dom_name
            }
    
    return ln_map

def extract_ln_from_xml(xml_file):
    """
    Extract all unique 'ln' attributes from XML file.
    Handles space-separated multiple codes (e.g., "89.93 92.1").
    
    Args:
        xml_file: Path to the XML file
    
    Returns:
        Set of unique ln decimal codes
    """
    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    unique_ln = set()
    
    for elem in root.iter():
        ln_value = elem.get('ln')
        if ln_value is not None:
            # Split by spaces to handle multiple codes
            codes = ln_value.split()
            for code in codes:
                unique_ln.add(code.strip())
    
    return unique_ln

def main():
    import sys
    
    # Check for command line arguments
    if len(sys.argv) != 3:
        print("Usage: python script.py <csv_file> <xml_file>")
        print("Example: python script.py louw_nida_mapping.csv your_file.xml")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    xml_file = sys.argv[2]
    
    try:
        print("Loading LN mapping from CSV...")
        ln_mapping = load_ln_mapping(csv_file)
        print(f"Loaded {len(ln_mapping)} LN codes from CSV\n")
        
        print("Extracting LN codes from XML...")
        xml_ln_codes = extract_ln_from_xml(xml_file)
        print(f"Found {len(xml_ln_codes)} unique LN codes in XML\n")
        
        # Convert decimal codes to letter codes and find matching domains
        semantic_domains = defaultdict(set)
        unmatched_codes = []
        
        for decimal_code in sorted(xml_ln_codes):
            letter_code = parse_ln_code(decimal_code)
            
            if letter_code in ln_mapping:
                info = ln_mapping[letter_code]
                # Store by SemDom code
                sem_doms = info['SemDom'].split(';')
                sem_dom_names = info['SemDom_Name'].split(';')
                for sem_dom, sem_dom_name in zip(sem_doms, sem_dom_names):
                    semantic_domains[sem_dom].add(sem_dom_name)
            else:
                unmatched_codes.append(f"{decimal_code} -> {letter_code}")
        
        # Print results
        print("=" * 70)
        print("SEMANTIC DOMAINS COVERED")
        print("=" * 70)
        
        for sem_dom in sorted(semantic_domains.keys()):
            names = ', '.join(sorted(semantic_domains[sem_dom]))
            print(f"{sem_dom}: {names}")
        
        print(f"\nTotal unique semantic domains: {len(semantic_domains)}")
        
        # Print unmatched codes if any
        if unmatched_codes:
            print("\n" + "=" * 70)
            print("UNMATCHED LN CODES")
            print("=" * 70)
            for code in unmatched_codes:
                print(code)
        
        # Save to file
        output_file = 'semantic_domains_coverage.txt'
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("SEMANTIC DOMAINS COVERED\n")
            f.write("=" * 70 + "\n\n")
            for sem_dom in sorted(semantic_domains.keys()):
                names = ', '.join(sorted(semantic_domains[sem_dom]))
                f.write(f"{sem_dom}: {names}\n")
            f.write(f"\nTotal unique semantic domains: {len(semantic_domains)}\n")
            
            if unmatched_codes:
                f.write("\n" + "=" * 70 + "\n")
                f.write("UNMATCHED LN CODES\n")
                f.write("=" * 70 + "\n\n")
                for code in unmatched_codes:
                    f.write(code + "\n")
        
        print(f"\nResults saved to {output_file}")
        
    except FileNotFoundError as e:
        print(f"Error: File not found - {e}")
    except ET.ParseError as e:
        print(f"Error parsing XML: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()