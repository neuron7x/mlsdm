# Verification & Curation Protocol

## Inclusion rules (hard)
Each reference MUST:
- Have a stable identifier: DOI OR arXiv ID OR official canonical URL (NIST/ISO/IEEE/USENIX/ACM).
- Provide full metadata: title, authors, year, venue/publisher.

## Recency
- Prefer last 5–10 years, except necessary classics (e.g., Hebb, Hopfield).

## Verification anchors
- DOI must resolve at https://doi.org/<DOI>.
- arXiv must match ID at https://arxiv.org/abs/<ID>.
- Standards must come from official issuer pages:
  - NIST: nvlpubs.nist.gov
  - ISO: iso.org
  - IEEE: standards.ieee.org
  - USENIX: usenix.org

## What CI enforces
- CITATION.cff schema validation (cffconvert).
- BibTeX parsing + minimal required fields + unique keys.
