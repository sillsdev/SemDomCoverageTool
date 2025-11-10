import xml.etree.ElementTree as ET
import csv
from collections import defaultdict

def parse_semantic_domains(xml_file, output_csv):
    """
    Parse semantic domains XML and create CSV mapping LouwNida codes to semantic domains.
    
    Args:
        xml_file: Path to input XML file
        output_csv: Path to output CSV file
    """
    # Parse XML
    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    # Dictionary to aggregate domains by LouwNida code
    # Structure: {code: {"abbreviations": set(), "names": set()}}
    louwNida_map = defaultdict(lambda: {"abbreviations": set(), "names": set()})
    
    def process_domain(domain_element):
        """Recursively process a semantic domain element."""
        # Extract English abbreviation
        abbr_elem = domain_element.find(".//Abbreviation/AUni[@ws='en']")
        abbr = abbr_elem.text if abbr_elem is not None else ""
        
        # Extract English name
        name_elem = domain_element.find(".//Name/AUni[@ws='en']")
        name = name_elem.text if name_elem is not None else ""
        
        # Extract LouwNida codes
        louwNida_elem = domain_element.find(".//LouwNidaCodes/Uni")
        
        if louwNida_elem is not None and louwNida_elem.text:
            # Split by semicolon and process each code
            codes = louwNida_elem.text.split(';')
            for code in codes:
                code = code.strip()
                if code:  # Only process non-empty codes
                    louwNida_map[code]["abbreviations"].add(abbr)
                    louwNida_map[code]["names"].add(name)
        
        # Recursively process sub-domains
        sub_possibilities = domain_element.find(".//SubPossibilities")
        if sub_possibilities is not None:
            for sub_domain in sub_possibilities.findall(".//ownseq[@class='CmSemanticDomain']"):
                process_domain(sub_domain)
    
    # Find all top-level semantic domains
    possibilities = root.find(".//Possibilities")
    if possibilities is not None:
        for domain in possibilities.findall(".//ownseq[@class='CmSemanticDomain']"):
            process_domain(domain)
    
    # Write to CSV
    with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile, quoting=csv.QUOTE_ALL)
        
        # Write header
        writer.writerow(['LouwNida_Code', 'SemDom', 'SemDom_Name'])
        
        # Sort codes for consistent output
        for code in sorted(louwNida_map.keys()):
            data = louwNida_map[code]
            
            # Join unique domains with semicolons (sorted for consistency)
            semdom = ';'.join(sorted(data["abbreviations"]))
            semdom_name = ';'.join(sorted(data["names"]))
            
            writer.writerow([code, semdom, semdom_name])
    
    print(f"Successfully created {output_csv}")
    print(f"Total LouwNida codes processed: {len(louwNida_map)}")

# Example usage
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 3:
        print("Usage: python louwNidaMapper.py <input_xml_file> <output_csv_file>")
        sys.exit(1)
    
    xml_file = sys.argv[1]
    output_csv = sys.argv[2]
    
    parse_semantic_domains(xml_file, output_csv)
