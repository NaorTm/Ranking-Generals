# Commander Ranking Framework Release Candidate

Current release-candidate snapshot: `outputs_improved_2026-04-24_upgrade_pass5_release_candidate`

Parent snapshot: `outputs_improved_2026-04-24_upgrade_pass4_role_curated`

This project provides a conservative, auditable, evidence-weighted ranking framework for historical commanders. The ranking is not a final historical verdict. It is a structured model of available evidence, designed to expose uncertainty rather than hide it.

## Recommended Interpretation

Use `RANKING_RESULTS_SYNTHESIS_TIERED.csv` as the public-facing interpretation table. `hierarchical_trust_v2` remains the scoring backbone, but exact rank should be interpreted through synthesis tiers, confidence intervals, role weighting, high-level page sensitivity, and audit flags.

## Why Tiers Matter

Adjacent exact ranks are often less meaningful than tier placement. Tiers distinguish robust elite commanders from high performers whose placement depends on role attribution, broad pages, sparse evidence, or model sensitivity.

## Confidence Bands

Bootstrap confidence bands estimate empirical model uncertainty under current data and scoring assumptions. They are not absolute historical truth. Wide intervals mean exact rank should not be over-read.

## Role Weighting

Role weighting distinguishes overall command, principal field command, coalition/theater command, siege/engineering, naval command, staff/planning, nominal political leadership, and unclear roles. It is currently a sensitivity layer, not a replacement headline model.

## High-Level Page Capping

High-level capped sensitivity checks whether broad war, campaign, conquest, invasion, uprising, or broad-conflict pages dominate a commander's score.

## Known Limitations

- Wikipedia/source-density bias by era and region.
- Commander role ambiguity.
- Coalition credit ambiguity.
- Outcome ambiguity and disputed results.
- Uneven data coverage for ancient and non-European cases.
- Bootstrap uncertainty measures model/data uncertainty, not historical truth.

## Reproduce Validation

```powershell
python -m compileall .\build_upgrade_pass5_release_candidate.py .\build_ranking_dashboard.py .\audit_snapshot_integrity.py .\qa_dashboard_snapshot.py .\generate_ranking_validation_v2.py
python .\generate_ranking_validation_v2.py --snapshot-dir .\outputs_improved_2026-04-24_upgrade_pass5_release_candidate
python .\qa_dashboard_snapshot.py --snapshot-dir .\outputs_improved_2026-04-24_upgrade_pass5_release_candidate --port 8772
python .\audit_snapshot_integrity.py --snapshot-dir .\outputs_improved_2026-04-24_upgrade_pass5_release_candidate --require-upgrade-files --require-confidence-files --require-role-files --require-synthesis-files
```

## Major Reports

- `FINAL_UPGRADED_SYSTEM_ASSESSMENT.md`
- `ROBUST_ELITE_CORE.md`
- `CAVEATED_HIGH_RANKED_COMMANDERS.md`
- `RELEASE_CANDIDATE_CHECKLIST.md`
- `reports/UPGRADE_PASS_4_ROLE_CLASSIFICATION_REPORT.md`
- `reports/UPGRADE_PASS_3_CONFIDENCE_REPORT.md`
