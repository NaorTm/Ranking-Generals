# Hardening Pass Report

Starting snapshot: `outputs_cleaned_2026-04-11_globaltrust_authoritative`
Superseding snapshot: `outputs_cleaned_2026-04-11_hardening_authoritative`

## What Was Fixed

1. Unsafe generic title-subject outcome inference was removed from `build_scoring_framework_package.py`.
   - The broad `subject_title_match` rule could assign wins to the wrong side on pages such as `Puerto Rico campaign` and `2017 Iraqi?Kurdish conflict`.
   - Final state: `subject_title_match` rows are now `0`.

2. Non-person commander leakage was tightened globally in `build_scoring_framework_package.py`.
   - Added exact-title and pattern-based exclusion for media outlets, agencies, missions, groups, and similar entity pages.
   - Confirmed removed from the ranked population: `Wounded in action`, `Channel NewsAsia`, `Federal Investigation Agency`, `Newsweek`, `Kommersant`, `RBK Group`, `Rudaw Media Network`, `Hafiz Gul Bahadur Group`, `Media Trust`, `Uganda Radio Network`.

3. `hierarchical_full_credit` was formally downgraded to diagnostic-only status in cross-model trust summaries.
   - `build_ranking_package.py` now computes cross-model stability metrics from five trusted models only.
   - `build_ranking_dashboard.py` labels `hierarchical_full_credit` as `diagnostic`.

4. A new hierarchical evidence guardrail was added in `build_ranking_package.py`.
   - Rule: commanders with `known_outcome_count < 8`, `known_outcome_share < 0.50`, and `higher_level_share >= 0.35` receive a mild `0.95` confidence guardrail factor.
   - This is a global model fix for sparse higher-level evidence, not a commander-specific patch.

5. The dashboard bundle was rebuilt and its asset-copy logic was fixed.
   - The copied static assets now rewrite embedded snapshot names correctly.
   - Browser QA passed against the rebuilt bundle.

## What Was Rebuilt

- Scoring layer
- Ranking layer
- Interpretive layer
- Dashboard bundle
- Dashboard QA summary

## Validation

- Dashboard QA all checks passed: `True`
- Baseline dashboard leader matches CSV: `Jean Lannes`
- Hierarchical dashboard leader matches CSV: `Suleiman the Magnificent`
- Console errors: `0`
- Page errors: `0`

## Current Trust Judgment

- `hierarchical_weighted` remains the most trustworthy single model.
- `baseline_conservative` remains useful, but still battle-specialist heavy.
- `hierarchical_full_credit` should be treated as diagnostic only, not as a co-equal trust vote.

## Residual State

- Remaining unresolved coalition/allied ambiguity: `242` commander rows on `69` pages.
- Remaining unresolved bare `Victory` / `Defeat` pages: `4503` commander rows on `445` pages.
- No obvious non-person entries remain in the top 200 of the baseline or hierarchical tables.
