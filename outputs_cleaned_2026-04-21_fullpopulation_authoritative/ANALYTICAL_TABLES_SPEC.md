# Analytical Tables Spec

All derived scoring tables live under [derived_scoring](C:/Users/gameo/OneDrive/Desktop/test/outputs_cleaned_2026-04-11_globaltrust_authoritative/derived_scoring).

## Table Notes

- `engagement_eligibility.csv`: 13,492 rows, one per page.
- `commander_identity_bridge.csv`: 30,897 rows, one per analytic commander identity.
- `commander_engagements_annotated.csv`: 60,395 rows, one per commander-page pair after dedupe.
- `commander_outcome_profile.csv`: 30,897 rows.
- `commander_page_type_profile.csv`: 30,897 rows.
- `commander_era_profile.csv`: 30,897 rows.
- `commander_opponent_profile.csv`: 60,359 rows.
- `commander_ranking_features.csv`: 30,897 rows.

## New Audit Columns

- `scoring_result_raw`
- `scoring_result_type`
- `scoring_result_source`

These make the scoring-stage outcome correction path auditable without rewriting source provenance.
