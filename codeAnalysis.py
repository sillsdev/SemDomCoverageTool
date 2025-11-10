import csv
import sys
import re
from collections import defaultdict

def analyze_louwNida_codes(csv_file):
    """
    Analyze LouwNida codes from CSV file.
    Reports missing codes and counts subdomains for each code number.
    
    Args:
        csv_file: Path to the CSV file with LouwNida codes
    """
    # Dictionary to store codes by number
    # Structure: {1: ['1A', '1B', ...], 2: ['2A', '2B'], ...}
    codes_by_number = defaultdict(list)
    
    # Read CSV and extract codes
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            code = row['LouwNida_Code'].strip().strip('"')
            
            # Extract the number and optional letter from the code
            # Pattern: "14A Weather" -> number=14, full_code="14A Weather"
            match = re.match(r'^(\d+)([A-Z])?', code)
            if match:
                number = int(match.group(1))
                codes_by_number[number].append(code)
    
    # Analyze results
    print("="*70)
    print("LouwNida Code Analysis")
    print("="*70)
    print()
    
    # Find missing code numbers (1-93)
    all_numbers = set(range(1, 94))
    found_numbers = set(codes_by_number.keys())
    missing_numbers = sorted(all_numbers - found_numbers)
    
    print(f"Total code numbers found: {len(found_numbers)} out of 93")
    print()
    
    if missing_numbers:
        print(f"Missing code numbers ({len(missing_numbers)}):")
        print("  " + ", ".join(map(str, missing_numbers)))
    else:
        print("All 93 code numbers are present!")
    
    print()
    print("="*70)
    print("Subdomain Counts by Code Number")
    print("="*70)
    print()
    print(f"{'Code':<6} {'Count':<7} {'Subdomains'}")
    print("-"*70)
    
    # Display counts for each code number
    for number in sorted(codes_by_number.keys()):
        subdomains = codes_by_number[number]
        count = len(subdomains)
        
        # Extract just the code part (number + letter) for display
        subdomain_codes = []
        for full_code in subdomains:
            match = re.match(r'^(\d+[A-Z]?(?:\')?)', full_code)
            if match:
                subdomain_codes.append(match.group(1))
            else:
                # If no letter, just use the number
                subdomain_codes.append(str(number))
        
        # Remove duplicates and sort
        subdomain_codes = sorted(set(subdomain_codes))
        
        # Display
        subdomain_str = ", ".join(subdomain_codes)
        if len(subdomain_str) > 50:
            subdomain_str = subdomain_str[:47] + "..."
        
        print(f"{number:<6} {count:<7} {subdomain_str}")
    
    print()
    print("="*70)
    print("Summary Statistics")
    print("="*70)
    
    total_codes = sum(len(subdomains) for subdomains in codes_by_number.values())
    avg_subdomains = total_codes / len(codes_by_number) if codes_by_number else 0
    max_subdomains = max((len(subdomains) for subdomains in codes_by_number.values()), default=0)
    max_code = max(codes_by_number.items(), key=lambda x: len(x[1]), default=(None, []))[0]
    
    print(f"Total LouwNida codes: {total_codes}")
    print(f"Average subdomains per code number: {avg_subdomains:.2f}")
    print(f"Maximum subdomains: {max_subdomains} (Code {max_code})")
    print()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python analyze_louwNida.py <csv_file>")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    analyze_louwNida_codes(csv_file)