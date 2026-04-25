# Upgrade Release Notes

Snapshot: `outputs_improved_2026-04-24_ranking_model_upgrade`

Implemented in this upgrade pass:

- Created a new working snapshot from `outputs_cleaned_2026-04-21_fullpopulation_authoritative`.
- Added `compute_model_stability.py` and generated `derived_scoring/commander_model_stability.csv`.
- Added `assign_commander_tiers.py` and generated `derived_scoring/commander_tiers.csv`.
- Added `build_page_type_contribution_report.py` and generated `derived_scoring/page_type_score_contributions.csv`.
- Added `audit_high_ranked_commanders.py` and generated `audits/high_ranked_commander_flags.csv`.
- Updated dashboard build data to include upgrade metadata.
- Updated dashboard UI to show tier, stability, page contribution mix, and audit-flag counts.
- Extended snapshot integrity audit with `--require-upgrade-files`.

Not yet implemented in this pass:

- bootstrap confidence bands
- manually curated command-role classification
- opponent-strength and force-ratio difficulty models
- era-normalized and region-normalized leaderboards
- multidimensional tactical, operational, siege, strategic, and institutional rankings

Those components should be added as later sensitivity views before replacing the current headline model.
