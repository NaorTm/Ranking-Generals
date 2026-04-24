# Scoring Framework

## Scope

This scoring layer is synchronized to `outputs_cleaned_2026-04-21_fullpopulation_authoritative`.

It supersedes stale scoring references from earlier snapshots. The framework is conservative: it treats unresolved outcomes as missing evidence, applies verified row-level exclusions before model weights, and uses trust tiers before exact rank interpretation.

## Authoritative Inputs

- `battles_clean.csv`
- `battle_commanders.csv`
- `commanders_master.csv`
- `verification/verified_commander_ranking_eligibility.csv`
- `verification/verified_outcome_overrides.csv`
- `derived_scoring/scoring_excluded_commander_rows.csv`

## Core Rules

- The analytic unit is one validated `analytic_commander_id x battle_id` row.
- Non-person commander rows are excluded before scoring.
- Commander verification overrides are applied before page weights and split-credit fields are computed.
- Outcome overrides are applied before split outcome credit is computed.
- Unknown outcomes do not receive outcome credit and do not dilute known-outcome same-side split denominators.
- Same-side known-outcome credit uses `1 / sqrt(known_same_side_count)`.
- `hierarchical_trust_v2` is the headline trust-first model; `hierarchical_weighted`, `baseline_conservative`, and `battle_only_baseline` are sensitivity views.
- `hierarchical_full_credit` remains diagnostic only.

## Current Scale

- retained pages: `13,492`
- raw commander rows: `60,903`
- commander rows entering scoring after exclusion: `60,690`
- excluded non-person/scoring rows: `213`
- commander master rows: `30,783`
- identity bridge rows: `30,953`
- annotated commander-engagement rows: `60,512`
- strict known-outcome rows: `26,364`
- default conservative ranking cohort: `781`

## Current Ranking Cohorts

- `baseline_conservative`: `781`
- `battle_only_baseline`: `2,389`
- `hierarchical_trust_v2`: `1,067`
- `hierarchical_weighted`: `1,067`
- `hierarchical_equal_split`: `1,067`
- `hierarchical_broader_eligibility`: `1,321`
- `hierarchical_full_credit`: `1,067`

## Validation State

- unique retained `battle_id`: true
- unique identity bridge `analytic_commander_id`: true
- unique annotated `analytic_commander_id x battle_id`: true
- literal `"nan"` leakage in core CSVs: none found
- non-person leakage in model validation: none found
- dashboard QA: pass

## Bottom Line

The current scoring layer is structurally consistent after the split-credit and verification-order fixes. Remaining limitations are methodological and evidentiary: unresolved outcomes remain unresolved, higher-level pages remain interpretation-sensitive, and exact adjacent ranks should not be over-read.
