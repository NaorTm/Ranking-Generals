# Ranking Dashboard Technical Note

This dashboard is wired directly to the authoritative snapshot in `outputs_cleaned_2026-04-21_fullpopulation_authoritative`.

Primary source tables:

- `derived_scoring/commander_ranking_features.csv`
- `derived_scoring/commander_outcome_profile.csv`
- `derived_scoring/commander_page_type_profile.csv`
- `derived_scoring/commander_era_profile.csv`
- `RANKING_RESULTS_BASELINE.csv`
- `RANKING_RESULTS_BATTLE_ONLY.csv`
- `RANKING_RESULTS_HIERARCHICAL_TRUST_V2.csv`
- `RANKING_RESULTS_HIERARCHICAL.csv`
- `RANKING_RESULTS_SENSITIVITY.csv`
- `TOP_COMMANDERS_SUMMARY.csv`
- `TOP_TIER_CLASSIFICATION.csv`
- `ERA_ELITE_SHORTLIST.csv`
- `MODEL_SENSITIVITY_AUDIT.csv`

Build process:

1. `build_ranking_dashboard.py` reads the ranking and scoring CSVs from the authoritative snapshot.
2. It joins those tables on `analytic_commander_id` and `canonical_wikipedia_url`.
3. It emits one consolidated browser dataset at `dashboard/dashboard_data.js`.
4. The static dashboard in `dashboard/index.html` reads that in-browser dataset and renders all views client-side.

What is included in the browser dataset:

- one commander record per ranked commander appearing in `RANKING_RESULTS_SENSITIVITY.csv`
- model ranks and normalized scores across six ranking variants, with `hierarchical_trust_v2` as the headline trust-first view
- engagement, conflict, outcome, page-type, and era profile metrics
- robustness classification from `TOP_TIER_CLASSIFICATION.csv`
- era shortlist rows from `ERA_ELITE_SHORTLIST.csv`
- focused audit rows from `MODEL_SENSITIVITY_AUDIT.csv`

Runtime characteristics:

- no backend is required
- the dashboard is fully static and can be opened locally
- charts are rendered client-side with the bundled `plotly.min.js`

Current commander universe in the dashboard: `2541`
