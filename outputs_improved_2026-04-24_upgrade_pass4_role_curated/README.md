# Commander Ranking Framework Upgrade Snapshot

Snapshot: `outputs_improved_2026-04-24_ranking_model_upgrade`

Parent snapshot: `outputs_cleaned_2026-04-21_fullpopulation_authoritative`

This snapshot adds an interpretation and audit layer on top of the corrected `hierarchical_trust_v2` ranking. It does not replace the headline model; it makes the output more defensible by attaching tier, stability, page-type dependency, and audit metadata to ranked commanders.

Primary interpretation rule:

Exact adjacent ranks should be treated as weaker than tiers, confidence, stability, and sensitivity movement. The ranking is an evidence-weighted model output, not a final historical verdict.

New upgrade outputs:

- `derived_scoring/commander_model_stability.csv`
- `derived_scoring/commander_tiers.csv`
- `derived_scoring/page_type_score_contributions.csv`
- `audits/high_ranked_commander_flags.csv`
- `METHODOLOGICAL_LIMITATIONS.md`
- `MODEL_SENSITIVE_CASES.md`
- `UPGRADE_RELEASE_NOTES.md`

Headline top 10 with interpretation metadata:

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
