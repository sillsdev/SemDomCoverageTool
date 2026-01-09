"""
Common utility functions used across word analysis scripts.
"""

import re
import unicodedata
from typing import Dict, Optional, Tuple

#################################################################
## Greek text utilities

def remove_accents(text: str) -> str:
    """
    Remove accents from Greek text for accent-insensitive matching.
    Uses NFD decomposition to separate base characters from combining marks.
    
    Args:
        text: Greek text with possible accents
        
    Returns:
        Text with accents removed
    """
    # NFD decomposition: separate base characters from combining marks
    nfd = unicodedata.normalize('NFD', text)
    # Filter out combining marks (category Mn = Mark, nonspacing)
    return ''.join(char for char in nfd if unicodedata.category(char) != 'Mn')

def clean_term_id(term_id: str) -> str:
    """
    When extracting terms from `BiblicalTerms.xml`, remove "-#" or "(DC)" suffix from term ID.
    
    Args:
        term_id: The raw term ID
        
    Returns:
        Cleaned term ID
    """
    # Remove (DC) suffix
    term_id = re.sub(r'\(DC\)$', '', term_id)
    # Remove -# suffix (one or more digits after a dash)
    term_id = re.sub(r'-\d+$', '', term_id)
    return term_id.strip()

#################################################################
## Domain utilities

def convert_domain_to_ln(domain_code: str) -> str:
    """
    Convert a domain code to LN format.
    - 3 digits: remove leading zeros (e.g., "089" -> "89")
    - 6 digits: first 3 digits (remove leading zeros) + last 3 digits as letter
      (001->A, 002->B, ..., 026->Z, 027->A', 028->B', ..., 052->Z', 053->A", etc.)
    
    Args:
        domain_code: "089" or "089017"
        
    Returns:
        LN code like "89" or "89Q"
    """
    if len(domain_code) == 3:
        return str(int(domain_code))
    elif len(domain_code) == 6:
        base = str(int(domain_code[:3]))
        suffix_num = int(domain_code[3:])
        
        if suffix_num == 0:
            return base
        
        # Convert suffix to letter format
        # 001-026: A-Z, 027-052: A'-Z', 053-078: A"-Z"
        letter_index = (suffix_num - 1) % 26
        prime_count = (suffix_num - 1) // 26
        
        letter = chr(ord('A') + letter_index)
        if prime_count == 0:
            primes = ''
        elif prime_count == 1:
            primes = "'"
        elif prime_count == 2:
            primes = '"'
        else:
            # Unexpected prime count (> 2), beyond standard LN notation
            print(f"WARNING: Domain code {domain_code} has unexpected suffix {suffix_num} (prime_count={prime_count})")
            primes = ''
        
        return base + letter + primes
    else:
        # Unexpected format, return as-is
        return domain_code

#################################################################
## Bible reference utilities

def normalize_reference(ref: str) -> str:
    """
    Normalize a reference to Book Chapter:Verse format, ignoring word positions.
    
    Args:
        ref: Reference string like "LUK 1:3" or "LUK 1:3!6" (word position after !)
        
    Returns:
        Normalized reference like "luk 1:3" (lowercase, no word position)
    """
    # Remove word position if present (everything after !)
    ref = ref.split('!')[0].strip()
    
    # Extract Book Chapter:Verse using regex
    match = re.match(r'([A-Za-z0-9]+)\s+(\d+):(\d+)', ref)
    if match:
        book, chapter, verse = match.groups()
        return f"{book.lower()} {chapter}:{verse}"
    
    return ""

# Bible book number to abbreviation mapping
# 3-digit 1-based indexing: 001-039 = OT, 040-066 = NT
# Codes from libpalaso: SIL.Scripture.SilBooks.Codes_3Letter
# https://github.com/sillsdev/libpalaso/blob/v16.2.0/SIL.Scripture/BCVRef.cs#L35
BOOK_NUMBERS: Dict[str, str] = {
    '001': 'Gen', '002': 'Exo', '003': 'Lev', '004': 'Num', '005': 'Deu',
    '006': 'Jos', '007': 'Jdg', '008': 'Rut', '009': '1Sa', '010': '2Sa',
    '011': '1Ki', '012': '2Ki', '013': '1Ch', '014': '2Ch', '015': 'Ezr',
    '016': 'Neh', '017': 'Est', '018': 'Job', '019': 'Psa', '020': 'Pro',
    '021': 'Ecc', '022': 'Sng', '023': 'Isa', '024': 'Jer', '025': 'Lam',
    '026': 'Ezk', '027': 'Dan', '028': 'Hos', '029': 'Jol', '030': 'Amo',
    '031': 'Oba', '032': 'Jon', '033': 'Mic', '034': 'Nam', '035': 'Hab',
    '036': 'Zep', '037': 'Hag', '038': 'Zec', '039': 'Mal',
    '040': 'Mat', '041': 'Mrk', '042': 'Luk', '043': 'Jhn', '044': 'Act',
    '045': 'Rom', '046': '1Co', '047': '2Co', '048': 'Gal', '049': 'Eph',
    '050': 'Php', '051': 'Col', '052': '1Th', '053': '2Th', '054': '1Ti',
    '055': '2Ti', '056': 'Tit', '057': 'Phm', '058': 'Heb', '059': 'Jas',
    '060': '1Pe', '061': '2Pe', '062': '1Jn', '063': '2Jn', '064': '3Jn',
    '065': 'Jud', '066': 'Rev',
}

# Reverse mapping for book name to number
BOOK_NAMES: Dict[str, str] = {v.lower(): k for k, v in BOOK_NUMBERS.items()}

def parse_verse_reference(verse_code: str) -> Optional[Tuple[str, str, str, str]]:
    """
    Parse a <Verse> reference from `BiblicalTerms.xml`.
    Convert numeric reference format BBBCCCVVVWWWWW to (book_abbr, chapter, verse, word).
    Book: 3 digits, Chapter: 3 digits, Verse: 3 digits, Word: 5 digits.
    
    Args:
        verse_code: Numeric code like '04203000300000'
        
    Returns:
        Tuple of (book_abbr, chapter, verse, word_position) or None if invalid
    """
    if len(verse_code) < 11:
        return None
    
    book_num = verse_code[0:3]
    chapter = verse_code[3:6]
    verse = verse_code[6:9]
    word = verse_code[9:14]
    
    if book_num not in BOOK_NUMBERS:
        return None
    
    book_abbr = BOOK_NUMBERS[book_num]
    
    # Remove leading zeros
    chapter = str(int(chapter))
    verse = str(int(verse))
    word = str(int(word))
    
    return (book_abbr, chapter, verse, word)
