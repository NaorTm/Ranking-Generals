# Scoring Framework

Snapshot: `outputs_improved_2026-04-24_upgrade_pass5_release_candidate`

## Pipeline

1. Base data cleaning creates retained battle/event rows, commander rows, and master commander identities.
2. Verification overrides are applied before page weights and split-credit fields are computed.
3. Non-person commander rows are excluded before scoring.
4. Outcome overrides are applied before split outcome credit is computed.
5. Unknown same-side rows do not dilute known-outcome split-credit denominators.
6. Page-type weighting separates battles, sieges, operations, campaigns, wars, and broad conflicts.
7. `hierarchical_trust_v2` remains the headline scoring backbone.
8. Model stability compares ranks across active sensitivity models.
9. Audit flags identify broad-page, coalition, evidence, split-credit, outcome-override, and identity risks.
10. High-level capping checks whether broad pages dominate the score.
11. Eligibility filtering checks nominal/political/staff exclusions from headline comparison.
12. Bootstrap confidence estimates empirical rank uncertainty.
13. Role weighting checks whether command responsibility is direct, coalition/theater, siege/engineering, naval, staff/planning, nominal/political, or unclear.
14. Synthesis tiers combine rank, score, stability, confidence, role, eligibility, broad-page dependency, known evidence, and audit flags.

## Interpretation Rule

The ranking should be interpreted as an evidence-weighted model output, not as a final historical verdict. Tiers and confidence bands are more meaningful than exact adjacent rank differences.

## Current Public View

Use `RANKING_RESULTS_SYNTHESIS_TIERED.csv`. It preserves exact `hierarchical_trust_v2` rank but makes caveats first-class.
