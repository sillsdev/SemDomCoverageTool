import xml.etree.ElementTree as ET
import csv
import sys
from collections import defaultdict
from typing import List, Tuple, Dict, Any

from utils import convert_domain_to_ln

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
        domain_codes = word_element.get('domain', '').strip()
        word = word_element.text.strip() if word_element.text else ""
        reference = word_element.get('ref', '').strip()

        # If any essential piece of data is missing, skip the element
        if domain_codes and word and reference:
            # Handle potential multiple domain codes in one 'domain' attribute (e.g., "089017 092001")
            ln_dom = ";".join([convert_domain_to_ln(dom.strip()) for dom in domain_codes.split() if dom.strip()])
            xml_data.append((ln_dom, word, reference))

    return xml_data

def output_results_to_csv(aggregated_data: Dict[Tuple[str, str], Any], output_filename: str = 'word_louw_nida_analysis.csv'):
    """
    Writes the aggregated word/LN code data to a tab-separated CSV file.
    
    Args:
        aggregated_data: Dictionary with (word, ln_code) tuples as keys
        output_filename: Output CSV filename
    """
    
    print(f"\nWriting results to {output_filename}...")
    
    fieldnames = [
        'Greek_Word',
        'Ln_Domain',
        'Total_Unique_References',
        'Refs'
    ]
    
    try:
        with open(output_filename, 'w', newline='', encoding='utf-8') as outfile:
            writer = csv.DictWriter(outfile, fieldnames=fieldnames, delimiter='\t', quoting=csv.QUOTE_MINIMAL)
            writer.writeheader()
            
            # Write rows, sorted by word and then by LN code
            for (word, ln_code) in sorted(aggregated_data.keys()):
                refs = sorted(list(aggregated_data[(word, ln_code)]))
                
                row = {
                    'Greek_Word': word,
                    'Ln_Domain': ln_code,
                    'Total_Unique_References': len(refs),
                    'Refs': "; ".join(refs)
                }
                writer.writerow(row)
                
        print(f"\n**Success!** Word-LN analysis saved to {output_filename}.")
    
    except Exception as e:
        print(f"\nFatal Error during CSV writing: {e}")
        sys.exit(1)


def main():
    if len(sys.argv) != 2:
        print("Usage: python wordLouwNidaAnalysisTool.py <annotated_xml_file>")
        print("Example: python wordLouwNidaAnalysisTool.py your_file.xml")
        sys.exit(1)
    
    xml_file = sys.argv[1]
    
    print("=" * 70)
    print(" Word/LN Code Analysis")
    print("=" * 70)
    
    try:
        # 1. Extract data (word, LN code, reference) from XML
        print("Extracting word and reference data from XML...")
        xml_ln_data = extract_ln_data_from_xml(xml_file)
        print(f"Found {len(xml_ln_data)} LN-annotated words in XML.")
        
        # 2. Aggregate data by (word, LN code) pair
        aggregated_data = defaultdict(set)  # (word, ln_code) -> set of references
        
        for ln_code, word, reference in xml_ln_data:
            aggregated_data[(word, ln_code)].add(reference)
                
        print(f"Aggregated data for {len(aggregated_data)} unique (word, LN code) pairs.")

        # 3. Output the results to the new CSV file
        output_results_to_csv(aggregated_data)
        
    except Exception as e:
        print(f"\nAn unexpected error occurred during processing: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
