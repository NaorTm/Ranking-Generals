# Ranking Generals

Release candidate: `v2026.04.24-upgraded-tiered-rc`

Current public snapshot: `outputs_improved_2026-04-24_upgrade_pass5_release_candidate`

This repository publishes a conservative, auditable, evidence-weighted commander ranking framework. The release-candidate view is tiered and confidence-aware: exact ranks are available, but the correct first reading is through synthesis tiers, confidence bands, stability, role sensitivity, high-level-page sensitivity, and audit flags.

## Recommended Public View

Start with:

- `outputs_improved_2026-04-24_upgrade_pass5_release_candidate/RANKING_RESULTS_SYNTHESIS_TIERED.csv`
- `outputs_improved_2026-04-24_upgrade_pass5_release_candidate/FINAL_UPGRADED_SYSTEM_ASSESSMENT.md`
- `outputs_improved_2026-04-24_upgrade_pass5_release_candidate/ROBUST_ELITE_CORE.md`
- `outputs_improved_2026-04-24_upgrade_pass5_release_candidate/CAVEATED_HIGH_RANKED_COMMANDERS.md`

`hierarchical_trust_v2` remains the scoring backbone. The public interpretation should lead with `RANKING_RESULTS_SYNTHESIS_TIERED.csv`, not a rigid top-10 list.

## How To Interpret This Release

The strongest claim:

This is a conservative, auditable, evidence-weighted commander ranking framework.

What should not be claimed:

This is not a final mathematical proof of the greatest commanders in history.

Correct interpretation:

Use the tiered synthesis layer first, then consult exact ranks and model-specific outputs.

## Why Tiers Matter

Adjacent exact ranks can be less meaningful than tier placement. The upgraded framework separates:

- robust elite commanders
- elite but qualified commanders
- high performers with evidence caveats
- category-specific strengths
- historically important but model-sensitive cases
- commanders not suitable for direct headline comparison

## What The Upgrade Added

- Pass 1: model stability, interpretive tiers, page-type diagnostics, high-ranked audit flags.
- Pass 2: stricter eligibility audit, high-level page capped sensitivity, broad-page dependency checks.
- Pass 3: bootstrap confidence bands, rank uncertainty, confidence-adjusted tiers.
- Pass 4: curated command-role classification, role contribution shares, role-weighted sensitivity ranking.
- Pass 5: consolidated release-candidate synthesis, robust elite core, caveated high-ranked report, release metadata.

## Current Snapshot Lineage

Parent lineage starts from:

- `outputs_cleaned_2026-04-21_fullpopulation_authoritative`

Release candidate:

- `outputs_improved_2026-04-24_upgrade_pass5_release_candidate`

## Dashboard

GitHub Pages dashboard:

`https://naortm.github.io/Ranking-Generals/`

Run locally:

```powershell
cd .\outputs_improved_2026-04-24_upgrade_pass5_release_candidate\dashboard
python -m http.server 8000
```

Then open `http://127.0.0.1:8000`.

## Validation

Run the release-candidate validation suite:

```powershell
python -m compileall .\build_upgrade_pass5_release_candidate.py .\build_ranking_dashboard.py .\audit_snapshot_integrity.py .\qa_dashboard_snapshot.py .\generate_ranking_validation_v2.py
python .\generate_ranking_validation_v2.py --snapshot-dir .\outputs_improved_2026-04-24_upgrade_pass5_release_candidate
python .\qa_dashboard_snapshot.py --snapshot-dir .\outputs_improved_2026-04-24_upgrade_pass5_release_candidate --port 8772
python .\audit_snapshot_integrity.py --snapshot-dir .\outputs_improved_2026-04-24_upgrade_pass5_release_candidate --require-upgrade-files --require-confidence-files --require-role-files --require-synthesis-files
```

Expected status:

- Python compile: passed
- Ranking validation: passed
- Strict integrity audit: `PASS`, `0` failed checks
- Dashboard QA: passed, `0` console/page errors
- Large-file check: passed, no tracked files above 50 MB

## Key Files

- `outputs_improved_2026-04-24_upgrade_pass5_release_candidate/FINAL_UPGRADED_SYSTEM_ASSESSMENT.md`
- `outputs_improved_2026-04-24_upgrade_pass5_release_candidate/RANKING_RESULTS_SYNTHESIS_TIERED.csv`
- `outputs_improved_2026-04-24_upgrade_pass5_release_candidate/ROBUST_ELITE_CORE.md`
- `outputs_improved_2026-04-24_upgrade_pass5_release_candidate/CAVEATED_HIGH_RANKED_COMMANDERS.md`
- `outputs_improved_2026-04-24_upgrade_pass5_release_candidate/SCORING_FRAMEWORK.md`
- `outputs_improved_2026-04-24_upgrade_pass5_release_candidate/METHODOLOGICAL_LIMITATIONS.md`
- `outputs_improved_2026-04-24_upgrade_pass5_release_candidate/MODEL_SENSITIVE_CASES.md`

## Future Research Passes

Do not treat this release candidate as the final historical model. Next research passes should focus on source-backed manual role curation, opponent strength, battle difficulty, evidence-quality scoring, and category-specific ranking views.
