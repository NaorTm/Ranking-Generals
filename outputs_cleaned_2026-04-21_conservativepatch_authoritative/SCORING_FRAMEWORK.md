# Scoring Framework

## Scope

This scoring layer is synchronized to `outputs_cleaned_2026-04-11_globaltrust_authoritative` and supersedes `outputs_cleaned_2026-04-10_secondpass_authoritative` for downstream ranking work.

## Authoritative Inputs

- [battles_clean.csv](C:/Users/gameo/OneDrive/Desktop/test/outputs_cleaned_2026-04-11_globaltrust_authoritative/battles_clean.csv)
- [battle_commanders.csv](C:/Users/gameo/OneDrive/Desktop/test/outputs_cleaned_2026-04-11_globaltrust_authoritative/battle_commanders.csv)
- [commanders_master.csv](C:/Users/gameo/OneDrive/Desktop/test/outputs_cleaned_2026-04-11_globaltrust_authoritative/commanders_master.csv)
- [scoring_excluded_commander_rows.csv](C:/Users/gameo/OneDrive/Desktop/test/outputs_cleaned_2026-04-11_globaltrust_authoritative/derived_scoring/scoring_excluded_commander_rows.csv)

## Core Rules

- The analytic unit is one validated `analytic_commander_id x battle_id` row.
- Unknown outcomes remain missing evidence in split-credit models, not denominator-weighted zeros.
- Same-side outcome credit keeps the inherited `sqrt_same_side_split` rule.
- This pass adds scoring-only sanitization for citation-fused page result text and excludes the last audited non-person identity leak.

## Current Scale

- retained pages: `13,492`
- commander rows entering scoring after exclusion: `60,572`
- commander master rows entering scoring: `30,722`
- identity bridge rows: `30,897`
- annotated commander-engagement rows: `60,395`
- strict known-outcome rows: `27,720`
- default conservative ranking cohort: `709`

## Bottom Line

The scoring layer in `outputs_cleaned_2026-04-11_globaltrust_authoritative` is the current authoritative foundation for ranking rebuilds.
