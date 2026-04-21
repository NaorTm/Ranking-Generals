# Global Correction Pass Report

## Snapshot Lineage

- starting analytics snapshot: `outputs_cleaned_2026-04-10_secondpass_authoritative`
- superseding analytics snapshot: `outputs_cleaned_2026-04-11_globaltrust_authoritative`

## Logic Changed

- `build_scoring_framework_package.py`: added scoring-only result-text sanitization and fallback outcome normalization.
- `build_scoring_framework_package.py`: extended explicit non-person exclusion to remove `Al-Masdar News` from scoring and ranking inputs.
- No ranking-formula rewrite was applied in this pass; the model layer was rebuilt on top of the corrected scoring outputs.

## Rebuilt Outputs

- [commander_engagements_annotated.csv](C:/Users/gameo/OneDrive/Desktop/test/outputs_cleaned_2026-04-11_globaltrust_authoritative/derived_scoring/commander_engagements_annotated.csv)
- [RANKING_RESULTS_BASELINE.csv](C:/Users/gameo/OneDrive/Desktop/test/outputs_cleaned_2026-04-11_globaltrust_authoritative/RANKING_RESULTS_BASELINE.csv)
- [RANKING_RESULTS_HIERARCHICAL.csv](C:/Users/gameo/OneDrive/Desktop/test/outputs_cleaned_2026-04-11_globaltrust_authoritative/RANKING_RESULTS_HIERARCHICAL.csv)
- [RANKING_RESULTS_SENSITIVITY.csv](C:/Users/gameo/OneDrive/Desktop/test/outputs_cleaned_2026-04-11_globaltrust_authoritative/RANKING_RESULTS_SENSITIVITY.csv)
- [TOP_TIER_CLASSIFICATION.csv](C:/Users/gameo/OneDrive/Desktop/test/outputs_cleaned_2026-04-11_globaltrust_authoritative/TOP_TIER_CLASSIFICATION.csv)
- [MODEL_SENSITIVITY_AUDIT.csv](C:/Users/gameo/OneDrive/Desktop/test/outputs_cleaned_2026-04-11_globaltrust_authoritative/MODEL_SENSITIVITY_AUDIT.csv)
- [dashboard_data.js](C:/Users/gameo/OneDrive/Desktop/test/outputs_cleaned_2026-04-11_globaltrust_authoritative/dashboard/dashboard_data.js)
- [dashboard_qa_summary.json](C:/Users/gameo/OneDrive/Desktop/test/outputs_cleaned_2026-04-11_globaltrust_authoritative/dashboard_qa_summary.json)

## Not Rebuilt

- The battle and commander base CSVs were not re-extracted or replaced in this pass.
