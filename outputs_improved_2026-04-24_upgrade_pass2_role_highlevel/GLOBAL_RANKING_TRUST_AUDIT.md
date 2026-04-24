# Global Ranking Trust Audit

This pass audited the full commander population in `outputs_cleaned_2026-04-10_secondpass_authoritative` and rebuilt the affected analytics in `outputs_cleaned_2026-04-11_globaltrust_authoritative`.

## Issue Families

- Confirmed global bug fixed: citation-fused result strings. Scope fixed: `322` pages, `1,546` commander rows, `1,254` commanders.
- Confirmed global data-quality fix: ranked non-person leakage. Scope fixed: `76` excluded commander rows across `59` battles.
- Residual coalition/allied ambiguity: `1,342` commander rows on `283` pages.
- Residual generic one-sided result strings: `4,520` commander rows on `445` page-level occurrences.
- Residual hierarchical structural risk: `29` ranked commanders, including `4` in the top 100.

## Judgment

- Remaining problems are now mostly bounded ambiguity classes plus one still-open hierarchical design tradeoff.
- The system is globally more trustworthy than the second-pass snapshot.
