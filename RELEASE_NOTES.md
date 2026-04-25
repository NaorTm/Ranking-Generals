# v2026.04.24-upgraded-tiered-rc

Title: Upgraded Tiered Commander Ranking Framework, Release Candidate

Release-candidate snapshot:

`outputs_improved_2026-04-24_upgrade_pass5_release_candidate`

## Summary

This release candidate preserves `hierarchical_trust_v2` as the scoring backbone, but changes the recommended public interpretation from a rigid exact-rank list to a tiered synthesis layer.

Recommended public table:

`RANKING_RESULTS_SYNTHESIS_TIERED.csv`

Exact adjacent ranks should not be over-read. Tiers, confidence bands, stability, role sensitivity, high-level-page sensitivity, and audit flags are the primary interpretive layer.

## Parent Lineage

The upgrade lineage starts from:

`outputs_cleaned_2026-04-21_fullpopulation_authoritative`

Release-candidate lineage:

1. `outputs_improved_2026-04-24_ranking_model_upgrade`
2. `outputs_improved_2026-04-24_upgrade_pass2_role_highlevel`
3. `outputs_improved_2026-04-24_upgrade_pass3_confidence`
4. `outputs_improved_2026-04-24_upgrade_pass4_role_curated`
5. `outputs_improved_2026-04-24_upgrade_pass5_release_candidate`

## Upgrade Passes

Upgrade Pass 1 added model stability, interpretive tiers, page-type diagnostics, and high-ranked commander audit flags.

Upgrade Pass 2 added stricter commander eligibility auditing, high-level page capped sensitivity, and broad-page dependency checks.

Upgrade Pass 3 added bootstrap confidence bands, rank uncertainty estimates, and confidence-adjusted tiers.

Upgrade Pass 4 added curated command-role sensitivity, role contribution shares, and a role-weighted ranking sensitivity output.

Upgrade Pass 5 added the final tiered synthesis table, robust elite core report, caveated high-ranked commander report, release-candidate assessment, dashboard release metadata, and public-facing documentation.

## How To Interpret This Release

The strongest claim:

This is a conservative, auditable, evidence-weighted commander ranking framework.

What should not be claimed:

This is not a final mathematical proof of the greatest commanders in history.

Correct interpretation:

Use the tiered synthesis layer first, then consult exact ranks and model-specific outputs.

## Validation Status

- Python compile: passed
- Ranking validation: passed
- Strict integrity audit: `PASS`, `0` failed checks
- Dashboard QA: passed, `0` console/page errors
- Large-file check: passed, no tracked files above 50 MB

## Future Work

Opponent strength, battle difficulty, evidence-quality scoring, and multidimensional category rankings are intentionally deferred to future research passes after this release candidate is preserved.
