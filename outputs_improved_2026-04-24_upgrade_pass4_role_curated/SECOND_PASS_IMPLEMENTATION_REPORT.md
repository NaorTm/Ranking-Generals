# Second Pass Implementation Report

## Snapshot Lineage

- starting snapshot: `outputs_cleaned_2026-04-10_rankfix_authoritative`
- superseding second-pass snapshot: `outputs_cleaned_2026-04-10_secondpass_authoritative`

The old snapshot is preserved unchanged. This pass created a new superseding analytics snapshot because the fixes affected scoring logic, ranking behavior, interpretive outputs, and the dashboard bundle.

## Code Files Changed

- `build_scoring_framework_package.py`
- `build_ranking_package.py`
- `generate_second_pass_reports.py`

Rebuilt but not code-modified in this pass:

- `build_interpretive_layer.py`
- `build_ranking_dashboard.py`
- `qa_dashboard_snapshot.py`

## Fixes Implemented

### Confirmed bug fixes

1. Anti-target outcome inference:
   - extended `anti-*` target extraction to shorter targets
   - searched both belligerent labels and commander-side raw text for the loser target
   - added coalition aliases such as `allied powers`, `allied forces`, and `anti spartan`

2. Coalition/allied side inference:
   - added direct coalition-label matching
   - added coalition-strength heuristics
   - preserved conservative `unknown` outcomes when the page stayed genuinely ambiguous

3. Unknown-outcome denominator fix:
   - `outcome_factor_split` now becomes zero whenever `outcome_category = unknown`

### Design fixes

4. Split-credit defeat dilution:
   - changed same-side outcome split from `1 / n` to `1 / sqrt(n)`

5. Hierarchical temporal inflation:
   - hierarchical temporal scoring now uses `active_span_years_nonwar` when available

6. Hierarchical guardrail:
   - reduced higher-level reward weight from `0.10` to `0.06`
   - added a small evidence component at `0.04` using known-outcome share

### Data safeguards in the scoring layer

7. Title-year correction:
   - when parsed year is wildly inconsistent with an event title year, the scoring layer now uses the title year

8. Non-person commander exclusion:
   - excluded `Manner of death` from the scoring layer without rewriting the authoritative commander snapshot

## Validation

- total annotated commander rows changed versus the prior snapshot: `1,979`
- anti/coaltition-pattern rows changed: `795`
- title-year override rows now active: `31` across `6` pages
- excluded non-person commander rows at scoring time: `61`
- excluded non-person master identities at scoring time: `0`
- unknown annotated rows in rebuilt package: `32,340`
- unknown rows still contributing non-zero split outcome factor: `0`

## Rebuilt Outputs

- derived scoring tables in `outputs_cleaned_2026-04-10_secondpass_authoritative\derived_scoring`
- ranking outputs: `RANKING_RESULTS_*.csv`, `RANKING_BUILD_METRICS.json`, `TOP_COMMANDERS_SUMMARY.csv`, `TOP_COMMANDERS_PROFILES.md`
- interpretive outputs: `BEST_SUPPORTED_TOP_TIER_MEMO.md`, `TOP_TIER_CLASSIFICATION.csv`, `MODEL_SENSITIVITY_AUDIT.csv`, `ERA_ELITE_SHORTLIST.csv`
- dashboard bundle in `outputs_cleaned_2026-04-10_secondpass_authoritative\dashboard`
- dashboard QA summary: `dashboard_qa_summary.json`

## Before/After Cohort Counts

| model | old_rows | new_rows |
| --- | ---: | ---: |
| baseline_conservative | 664 | 683 |
| battle_only_baseline | 2,197 | 2,217 |
| hierarchical_weighted | 1,230 | 1,286 |
| hierarchical_full_credit | 1,230 | 1,286 |
| hierarchical_equal_split | 1,230 | 1,286 |
| hierarchical_broader_eligibility | 1,289 | 1,353 |

## Leader Checks

- baseline leader: `Alexander Suvorov` -> `Alexander Suvorov`
- hierarchical leader: `Suleiman the Magnificent` -> `Suleiman the Magnificent`
- `Qasem Soleimani` hierarchical rank: `4 -> 13.0`
- `Nelson A. Miles` hierarchical rank: `9 -> 16.0`

## Residual Caveats

- This pass did not rewrite the battle or commander source layers.
- Some coalition/allied pages remain unresolved because their result text is still too generic or citation-polluted to assign safely.
- Those residual unknowns are now bounded and auditable rather than silently mis-scored.
