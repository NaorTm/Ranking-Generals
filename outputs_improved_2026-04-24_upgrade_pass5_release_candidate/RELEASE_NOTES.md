# v2026.04.24-upgraded-tiered-rc

Title: Upgraded Tiered Commander Ranking Framework, Release Candidate

This release candidate preserves `hierarchical_trust_v2` as the scoring backbone while making `RANKING_RESULTS_SYNTHESIS_TIERED.csv` the recommended public interpretation layer.

Exact adjacent ranks should not be over-read. Tiers, confidence bands, stability, role sensitivity, high-level-page sensitivity, and audit flags are the primary interpretive layer.

## Parent Lineage

The upgrade lineage starts from `outputs_cleaned_2026-04-21_fullpopulation_authoritative`.

Release-candidate lineage:

1. `outputs_improved_2026-04-24_ranking_model_upgrade`
2. `outputs_improved_2026-04-24_upgrade_pass2_role_highlevel`
3. `outputs_improved_2026-04-24_upgrade_pass3_confidence`
4. `outputs_improved_2026-04-24_upgrade_pass4_role_curated`
5. `outputs_improved_2026-04-24_upgrade_pass5_release_candidate`

## Upgrade Passes

- Pass 1: stability, tiers, page-type diagnostics, audit flags.
- Pass 2: role/high-level eligibility filtering and capped sensitivity.
- Pass 3: bootstrap confidence bands and rank uncertainty.
- Pass 4: curated command-role sensitivity and role-weighted ranking.
- Pass 5: final tiered synthesis and release-candidate assessment.

## How To Interpret This Release

The strongest claim:

This is a conservative, auditable, evidence-weighted commander ranking framework.

What should not be claimed:

This is not a final mathematical proof of the greatest commanders in history.

Correct interpretation:

Use the tiered synthesis layer first, then consult exact ranks and model-specific outputs.
