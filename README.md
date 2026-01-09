# SemDomCoverageTool

Process and scripts to map Louw/Nida semantic domain–tagged Biblical Greek/Hebrew texts to SIL Global’s Semantic Domains ([semdom.org](https://semdom.org/)), and to analyze the domains needed to cover specified scripture.

## Overview

This project provides a reproducible workflow to:

- Derive a mapping between Louw/Nida (LN) domain codes and Semantic Domains from a Semantic Domains XML file.
- Use that mapping to summarize semantic-domain coverage of an LN-tagged text.
- Perform simple sanity checks on the mapping.

## Scripts

- codeAnalysis.py

  - Purpose: Analyze a mapping CSV to report which LN base codes are present and how many subdomains exist per LN code number (1–93).
  - Input: LouwNidaToSemDom.csv (see below).
  - Output: Console report (counts, missing numbers, summary stats).
  - Run: `python codeAnalysis.py LouwNidaToSemDom.csv`

- louwNidaMapper.py

  - Purpose: Parse a Semantic Domains XML file and create a CSV that maps LN base codes to Semantic Domain abbreviations and names.
  - Input: Semantic Domains XML (with Abbreviation/Name in English and LouwNidaCodes under each domain).
  - Output: LouwNidaToSemDom.csv with columns: `LouwNida_Code, SemDom, SemDom_Name`.
  - Run: `python louwNidaMapper.py <SemanticDomains.xml> LouwNidaToSemDom.csv`

- semDomCoverageTool.py

  - Purpose: Compute Semantic Domain coverage over an LN-tagged text.
  - Inputs:
    - Mapping CSV (e.g., LouwNidaToSemDom.csv) produced by louwNidaMapper.py.
    - Annotated text XML where tokens are marked with LN codes.
  - Output: semantic_domains_coverage.csv containing, per Semantic Domain:
    - SemDom, SemDom_Name
    - Total_Ln_Decimal_Codes
    - Total_Unique_Words
    - Total_Unique_References
    - Ln_Decimal_Codes_Mapped
    - Associated_Words_With_Refs (pipe-separated list like `lemma (Ref1; Ref2)`)
  - Run: `python semDomCoverageTool.py LouwNidaToSemDom.csv <AnnotatedText.xml>`

- wordLouwNidaAnalysisTool.py

  - Purpose: Analyze word usage by Louw/Nida domain code in an annotated Greek text. Converts domain codes (from `domain` attribute) to LN format.
  - Input: Annotated text XML where tokens (`<w>` elements) are marked with domain codes (numeric 3-digit or 6-digit format).
  - Output: word_louw_nida_analysis.csv containing, per (word, LN code) pair:
    - Greek_Word (without accents)
    - Greek_Forms (with accents, semicolon-separated)
    - Ln_Domain (LN code in format like "89", "89Q", "23C", etc.; semicolon-separated if multiple domains)
    - Total_Unique_References
    - Refs (semicolon-separated list of all references with word positions, e.g., "LUK 1:5!44; LUK 1:55!16")
  - Note: Converts domain codes (e.g., "089" → "89", "089017" → "89Q"). Same word with different LN codes produces separate rows; same word with same LN code across multiple locations produces one row with all references.
  - Run: `python wordLouwNidaAnalysisTool.py <AnnotatedText.xml>`

- wordSemDomAnalysisTool.py

  - Purpose: Enrich word/LN analysis with semantic domain information by mapping LN codes to semantic domains.
  - Inputs:
    - word_louw_nida_analysis.csv produced by wordLouwNidaAnalysisTool.py.
    - Mapping CSV (e.g., LouwNidaToSemDom.csv) produced by louwNidaMapper.py.
  - Output: word_sem_dom_analysis.csv containing all columns from word_louw_nida_analysis.csv, minus Ln_Domain, plus:
    - SemDom (semantic domain code; semicolon-separated if multiple LN domains map to different semantic domains)
    - SemDom_Name (semantic domain name; semicolon-separated if multiple)
  - Note: For semicolon-separated LN codes (e.g., "23C;58D"), looks up each code independently and joins the results. Includes fallback matching (strips letters/primes if code not found).
  - Run: `python wordSemDomAnalysisTool.py word_louw_nida_analysis.csv LouwNidaToSemDom.csv`

- biblicalTermsAnalysisTool.py

  - Purpose: Extract biblical terms (from BiblicalTerms.xml) that appear in a specified book of the Bible.
  - Inputs:
    - BiblicalTerms.xml containing biblical term definitions and verse references.
    - Book abbreviation (e.g., Luk, Mat, Rom).
  - Output: `<book>_terms.csv` containing, per term found in that book:
    - Term_Id (original term with optional -# and (DC) suffixes)
    - Term (cleaned term ID)
    - Gloss
    - Domain
    - Refs (semicolon-separated list of references in the target book, formatted as `BOOK CHAPTER:VERSE!WORDPOS`, e.g., `LUK 1:5!44; LUK 1:55!16`)
  - Run: `python biblicalTermsAnalysisTool.py BiblicalTerms.xml <book>`

- wordAnalysisTool.py

  - Purpose: Match Greek words to key terms.
  - Inputs:
    - `<book>_terms.csv` (e.g., luk_terms.csv) produced by biblicalTermsAnalysisTool.py, containing biblical key terms with glosses and references.
    - word_sem_domain_analysis.csv produced by wordSemDomAnalysisTool.py, containing words with semantic domain info.
  - Output: word_analysis.csv containing all columns from word_sem_dom_analysis.csv plus (inserted after Greek_Word):
    - Meaning (gloss from matching key term, or "unknown")
    - Is_Key_Term ("yes" if word matches a key term, "no" otherwise)
  - Matching Logic:
    - Uses accent-insensitive matching (e.g., "Δαυίδ" and "Δαυὶδ" match the same term).
    - Multiple key terms can share the same Greek word with different glosses/references.
    - If only one key term matches a Greek word, uses it automatically.
    - If multiple key terms match, selects the one with overlapping references (ignoring word positions).
  - Run: `python wordAnalysisTool.py <book>_terms.csv word_sem_dom_analysis.csv`
  - Optional: `python wordAnalysisTool.py --verbose <book>_terms.csv word_sem_dom_analysis.csv` (prints detailed matching info)

## Expected input formats

- Semantic Domains XML

  - Each domain should include (English preferred):
    - Abbreviation: `.//Abbreviation/AUni[@ws='en']`
    - Name: `.//Name/AUni[@ws='en']`
    - LouwNidaCodes: `.//LouwNidaCodes/Uni` (semicolon-separated if multiple)
  - The script recursively traverses subdomains.

- LN-domain-coded text XML

  - Tokens are `<w>` elements anywhere in the document with:
    - `domain` attribute with numeric domain codes (3-digit like `089` or 6-digit like `089017`); space-separated if multiple.
    - `ref`: a human-readable reference (e.g., verse or location, optionally with word position like `LUK 1:1!5`).
  - Example:
    - `<w domain="089017" ref="LUK 1:1!5">word</w>`

## Typical workflow

1. Produce mapping (once per Semantic Domains XML source)

   - `python louwNidaMapper.py SemanticDomains.xml LouwNidaToSemDom.csv`

2. Inspect mapping quality (optional)

   - `python codeAnalysis.py LouwNidaToSemDom.csv`

### ... by semantic domain

3. Generate coverage from LN-tagged text

   - `python semDomCoverageTool.py LouwNidaToSemDom.csv 03-luke.xml`
   - Output: `semantic_domains_coverage.csv` (you can rename/move as desired).

### ... by Greek term

3. Analyze word usage by Louw-Nida code

   - `python wordLouwNidaAnalysisTool.py 03-luke.xml`
   - Output: `word_louw_nida_analysis.csv` (you can rename/move as desired).

4. Enrich word analysis with semantic domain data

   - `python wordSemDomAnalysisTool.py word_louw_nida_analysis.csv LouwNidaToSemDom.csv`
   - Output: `word_sem_dom_analysis.csv` (you can rename/move as desired).

5. Extract biblical terms for a specific book

   - `python biblicalTermsAnalysisTool.py BiblicalTerms.xml Luk`
   - Output: `luk_terms.csv` (you can rename/move as desired).

6. Enrich word analysis with biblical key term meanings

   - `python wordAnalysisTool.py luk_terms.csv word_sem_dom_analysis.csv`
   - Output: `word_analysis.csv` (you can rename/move as desired).
   - Add `--verbose` flag for detailed matching diagnostics.

## Repository notes

- Sample data files (if present):
  - `03-luke.xml` — data from [Clear-Bible/macula-greek](https://github.com/Clear-Bible/macula-greek)
  - `BiblicalTerms.xml` — key Biblical terms, the authoritative list for Paratext.
  - `LouwNidaToSemDom.csv` — Mapping generated from best current FieldWorks semantic domain data.
  - `luke_semantic_domains_coverage.csv` — results of the output of the semDomCoverageTool for the Luke xml.
- Dependencies: Python 3.x; standard library only (no third-party packages required).

## Licensing

- Code: MIT License (see `LICENSE`).
- Semantic Domains content: The Semantic Domains list and descriptions are maintained by SIL Global at [semdom.org](https://semdom.org/) and are licensed under Creative Commons Attribution-ShareAlike (CC BY-SA 4.0). If you use or redistribute that content, follow their license terms.

## Acknowledgments

- The Luke data in this repository was derived from the [MACULA Greek](https://github.com/Clear-Bible/macula-greek) project and is licensed per: https://github.com/Clear-Bible/macula-greek/blob/main/LICENSE.md
