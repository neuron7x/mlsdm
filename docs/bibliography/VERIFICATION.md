# Verification and Curation Protocol

This document defines the verification and curation protocol for bibliographic references in this repository.

## Inclusion Criteria

Each reference MUST satisfy ALL of the following requirements:

### Required Metadata
- **Title**: Complete, unabbreviated title
- **Authors**: At least first author with full name
- **Year**: 4-digit publication year
- **Venue**: Journal, conference, or publisher name

### Stable Identifier (at least one required)
- **DOI**: Digital Object Identifier (preferred for published works)
- **arXiv ID**: For preprints (format: YYMM.NNNNN)
- **Official URL**: Canonical URL from official issuer (NIST, ISO, IEEE, ACM, USENIX)

### URL Requirements
- All URLs must use HTTPS
- URLs must be stable (publisher, doi.org, arxiv.org, official bodies)
- No personal blogs, temporary links, or example.com domains

## Recency Policy

- **Preferred**: Publications from the last 5-10 years
- **Exceptions**: Foundational works (e.g., Hebb 1949, Hopfield 1982)
- **Justification**: Classic references must be explicitly noted in context

## Disallowed Sources

The following sources are NOT permitted:
- Personal blogs or unreviewed websites
- Preprints without arXiv or institutional repository
- Sources with non-stable URLs
- References without DOI, arXiv ID, or official canonical URL
- Placeholder or example entries (example.com, TODO, TBD)

## Verification Procedure

### Before Adding a Reference

1. **Verify DOI resolves**: Navigate to `https://doi.org/<DOI>` and confirm it loads
2. **Verify arXiv exists**: Navigate to `https://arxiv.org/abs/<ID>` and confirm paper exists
3. **Verify metadata matches**: Title, authors, and year in BibTeX match the source
4. **Cross-check with Scholar**: Search Google Scholar or PubMed to confirm publication details

### Official Source Verification

- **NIST**: Must link to nvlpubs.nist.gov
- **ISO**: Must link to iso.org
- **IEEE**: Must link to standards.ieee.org or doi.org
- **USENIX**: Must link to usenix.org
- **ACM**: Must link to dl.acm.org or doi.org

## File Consistency Requirements

### BibTeX and APA 7 Synchronization

- `REFERENCES.bib` and `REFERENCES_APA7.md` must contain the same set of references
- Each APA entry includes a BibTeX key comment: `<!-- key: bibkey -->`
- CI validates 1:1 mapping between files

### Entry Format

**BibTeX (`REFERENCES.bib`)**:
```bibtex
@article{author2024_shorttitle,
  author    = {LastName, FirstName and ...},
  title     = {Full Title Here},
  journal   = {Journal Name},
  year      = {2024},
  volume    = {X},
  pages     = {Y--Z},
  doi       = {10.xxxx/xxxxx}
}
```

**APA 7 (`REFERENCES_APA7.md`)**:
```markdown
<!-- key: author2024_shorttitle -->
LastName, F., & OtherAuthor, O. (2024). Full Title Here. *Journal Name, X*, Y-Z. https://doi.org/10.xxxx/xxxxx
```

## CI Enforcement

The CI workflow (`citation-integrity.yml`) enforces:

1. **Schema validation**: `cffconvert --validate -i CITATION.cff`
2. **BibTeX parsing**: All entries must parse without errors
3. **Unique keys**: No duplicate BibTeX keys allowed
4. **Required fields**: title, year, author, and at least one identifier
5. **Year format**: Must be 4 digits (1900-2099)
6. **DOI format**: Basic regex validation (10.XXXX/...)
7. **URL protocol**: Must be HTTPS
8. **Forbidden content**: No TODO, example.com, or placeholder text
9. **Unicode safety**: No bidirectional control characters (Trojan Source prevention)
10. **BibTeX-APA mapping**: 1:1 correspondence via key comments

## Update Workflow

### Adding a New Reference

1. Find the authoritative source and verify all metadata
2. Add BibTeX entry to `docs/bibliography/REFERENCES.bib`:
   - Use key format: `author_year_shorttitle`
   - Include all required fields
   - Add DOI, eprint, or official URL
3. Add corresponding APA 7 entry to `docs/bibliography/REFERENCES_APA7.md`:
   - Include HTML comment with BibTeX key: `<!-- key: author_year_shorttitle -->`
   - Follow APA 7 format exactly
4. Run local validation:
   ```bash
   python scripts/validate_bibliography.py
   cffconvert --validate -i CITATION.cff
   ```
5. Open PR; CI blocks invalid metadata

### Reviewer Checklist

When reviewing bibliography changes, verify:

- [ ] BibTeX entry parses correctly
- [ ] All required fields present (title, author, year)
- [ ] Year is 4 digits and plausible
- [ ] At least one stable identifier (DOI/arXiv/official URL)
- [ ] URLs use HTTPS protocol
- [ ] DOI resolves at doi.org (manual check)
- [ ] arXiv ID exists at arxiv.org (manual check)
- [ ] Corresponding APA entry exists with matching key comment
- [ ] APA entry follows APA 7 format
- [ ] No placeholder text (TODO, example.com, TBD)
- [ ] No bidirectional Unicode control characters
- [ ] Source is from allowed category (peer-reviewed, standards body, established preprint)

## Maintenance

- **Quarterly review**: Check for DOI/URL rot (broken links)
- **Version updates**: When software version changes, update CITATION.cff and CITATION.bib
- **New releases**: Ensure date-released in CITATION.cff matches actual release date
