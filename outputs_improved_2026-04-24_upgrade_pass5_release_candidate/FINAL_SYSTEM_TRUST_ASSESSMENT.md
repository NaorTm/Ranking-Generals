# Final System Trust Assessment

Snapshot: `outputs_improved_2026-04-24_ranking_model_upgrade`

The system is usable as a conservative, auditable ranking framework with a stronger interpretation layer than the parent snapshot.

What is now stronger:

- top commanders have cross-model stability metadata
- top commanders have deterministic tiers
- top commanders have page-type contribution breakdowns
- top commanders have high-rank audit flags
- dashboard data includes tier, stability, audit, and contribution metadata
- strict upgrade integrity checks can be run with `audit_snapshot_integrity.py --require-upgrade-files`

Headline top 10:

| Rank | Commander | Score | Tier | Stability |
| --- | --- | --- | --- | --- |
| 1 | Alexander Suvorov | 91.36 | Tier A, robust elite | very_stable |
| 2 | Maurice, Prince of Orange | 88.55 | Tier D, strong but narrow-category performer | very_stable |
| 3 | Napoleon Bonaparte | 88.42 | Tier A, robust elite | very_stable |
| 4 | Subutai | 88.30 | Tier A, robust elite | very_stable |
| 5 | Sébastien Le Prestre, Marquis of Vauban | 86.81 | Tier D, strong but narrow-category performer | very_stable |
| 6 | Jean Lannes | 86.81 | Tier A, robust elite | very_stable |
| 7 | Louis-Nicolas Davout | 86.67 | Tier A, robust elite | very_stable |
| 8 | Douglas MacArthur | 86.28 | Tier A, robust elite | stable |
| 9 | Charles XIV John | 86.09 | Tier A, robust elite | very_stable |
| 10 | Ivan Paskevich | 86.08 | Tier B, elite but model-sensitive | stable |

Most common top-100 audit flags:

| Flag | Flagged Count |
| --- | --- |
| split_credit_sensitive | 73 |
| large_model_rank_variance | 71 |
| coalition_credit_heavy | 47 |
| siege_engineering_specialist | 26 |
| high_rank_low_battle_only_score | 15 |
| high_rank_many_high_level_pages | 12 |
| outcome_override_sensitive | 12 |
| low_evidence_quality | 11 |
| high_rank_low_known_rows | 7 |
| region_or_era_source_density_risk | 4 |
| nominal_leader_risk | 3 |

Trust judgment:

The model is defensible as an evidence-weighted ranking platform when read tier-first and confidence-first. It should not be presented as a definitive exact ordering of military greatness.
