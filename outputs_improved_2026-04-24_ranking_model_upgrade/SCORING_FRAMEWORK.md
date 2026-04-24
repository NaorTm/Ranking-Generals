# Scoring Framework

Authoritative upgrade snapshot: `outputs_improved_2026-04-24_ranking_model_upgrade`

Parent lineage: `outputs_cleaned_2026-04-21_fullpopulation_authoritative`

## Analytic Unit

The main analytic unit is `analytic_commander_id x battle_id` after identity bridging, commander verification, outcome overrides, non-person exclusion, and strict eligibility filtering.

## Headline Model

The headline model remains `hierarchical_trust_v2`. It is the conservative trust-first view that combines outcome performance with sustained scale, scope, temporal span, centrality, higher-level-page guardrails, and evidence controls.

`hierarchical_full_credit` remains diagnostic only and must not be presented as the headline model.

## Corrected Scoring Order

Commander verification overrides and outcome overrides are applied before split-credit and page-weight fields are computed. Unknown outcomes receive zero split outcome credit and do not dilute known-outcome same-side split denominators.

## New Interpretation Layer

The upgraded snapshot adds:

- model stability across active ranking variants
- deterministic commander tiers
- page-type score contribution breakdowns
- high-ranked commander audit flags
- dashboard-visible tier, stability, contribution, and audit metadata

## Tier Logic

Tier assignment combines trust-first rank, stability, known-outcome evidence, page-type dependency, and category concentration. Tier A means robust elite within this model; Tier D means strong but category-specific; Tier E means historically important but scoring-sensitive.

Top-100 tier distribution:

| Tier | Top-100 Count |
| --- | --- |
| Tier C, high performer with evidence caveats | 42 |
| Tier D, strong but narrow-category performer | 26 |
| Tier B, elite but model-sensitive | 19 |
| Tier A, robust elite | 13 |

## Interpretation Rule

The ranking should be interpreted as an evidence-weighted model output, not as a final historical verdict. Tiers and confidence bands are more meaningful than exact adjacent rank differences.
