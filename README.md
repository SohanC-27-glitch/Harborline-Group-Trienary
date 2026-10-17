# Harbourline duplicate-candidate matcher

A small Python 3 script that reads a customer CSV and flags candidate duplicate pairs for human review. It does **not** merge records.

## Run

The input CSV should have these headers:

`Company,Name,Phone,Email,City,Last activity,Notes`

No third-party packages are required.

```bash
python match_customers.py harbourline_customers.csv
```

To choose an output filename:

```bash
python match_customers.py harbourline_customers.csv candidates.csv
```

The output contains source row numbers, names, business units, name similarity, reasons for the flag, and `MANUAL REVIEW` as the decision.

## Matching rules

1. **Normalized phone:** remove punctuation and whitespace; if the digits are 12 characters beginning with `91`, strip that country prefix. Exact normalized phone matches are candidates.
2. **Normalized email:** trim and case-fold; exact non-empty matches are candidates.
3. **Exact normalized name:** punctuation/whitespace normalization; flags for review even if contact details differ (e.g., the two Suresh Rao rows).
4. **Similar name + same city:** name similarity of at least 0.85 plus matching canonical city. Mangalore/Mangaluru are treated as aliases.
5. **Entity-kind guard:** obvious organizations and names ending in “Family” are kept separate from people. This is only a basic safeguard; production data should carry an explicit entity-type field.
6. **Missing values:** blanks do not match blanks and never count as positive evidence.

## Limitations and risks

- Shared/recycled phone numbers and family/company inboxes can create false positives.
- Name spelling variants, initials, transliteration, missing data or different contact details can cause false negatives.
- City aliases are intentionally minimal and must be maintained as a controlled reference list.
- The simple entity classifier is not robust enough for production.
- Row numbers are positional, not stable identifiers; use source IDs in production.
- Similarity scores are evidence for review, not probabilities of identity.

Before any merge, a data steward should verify identity, preserve each business relationship/activity, log the decision, and ensure that the merge is reversible or recoverable. Add unit tests, stable source IDs, an explicit entity type, audit logging, and a reviewed alias list before production use.
