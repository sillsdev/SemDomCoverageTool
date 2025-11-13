# SemDomToLouwNida

Process and scripts to map Louw/Nida semantic domain–tagged Biblical Greek/Hebrew texts to SIL Global’s Semantic Domains (semdom.org), and to analyze the domains needed to cover specified scripture.

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

## Expected input formats
- Semantic Domains XML
  - Each domain should include (English preferred):
    - Abbreviation: `.//Abbreviation/AUni[@ws='en']`
    - Name: `.//Name/AUni[@ws='en']`
    - LouwNidaCodes: `.//LouwNidaCodes/Uni` (semicolon-separated if multiple)
  - The script recursively traverses subdomains.

- LN-tagged text XML
  - Tokens are `<w>` elements anywhere in the document, with attributes:
    - `ln`: an LN code like `89.32`, `92a`, or multiple codes separated by space.
    - `ref`: a human-readable reference (e.g., verse or location).
  - Example minimal shape: `<w ln="89.32" ref="Luk 1:1">...</w>`

## Typical workflow
1) Produce mapping (once per Semantic Domains XML source)
   - `python louwNidaMapper.py SemanticDomains.xml LouwNidaToSemDom.csv`

2) Inspect mapping quality (optional)
   - `python codeAnalysis.py LouwNidaToSemDom.csv`

3) Generate coverage from LN-tagged text
   - `python semDomCoverageTool.py LouwNidaToSemDom.csv 03-luke.xml`
   - Output: `semantic_domains_coverage.csv` (you can rename/move as desired).

## Repository notes
- Sample data files (if present):
  - `03-luke.xml` — example LN-tagged text.
  - `LouwNidaToSemDom.csv` — example mapping.
  - `luke_semantic_domains_coverage.csv` / `semantic_domains_coverage.txt` — example outputs.
- Dependencies: Python 3.x; standard library only (no third-party packages required).

## Licensing
- Code: MIT License (see `LICENSE`).
- Semantic Domains content: The Semantic Domains list and descriptions are maintained by SIL International at https://semdom.org and are licensed under Creative Commons Attribution-ShareAlike (CC BY-SA 4.0). If you use or redistribute that content, follow their license terms.

## Acknowledgments
- The Luke data in this repository was derived from the MACULA Greek project: https://github.com/Clear-Bible/macula-greek and is licensed per: https://github.com/Clear-Bible/macula-greek/blob/main/LICENSE.md

