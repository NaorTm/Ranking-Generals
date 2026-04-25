# Final Upgraded System Assessment

Snapshot: `outputs_improved_2026-04-24_upgrade_pass5_release_candidate`

Parent snapshot: `outputs_improved_2026-04-24_upgrade_pass4_role_curated`

## Headline Recommendation

The recommended scoring backbone remains `hierarchical_trust_v2`, because it is the most mature trust-first model and preserves the validated scoring fixes from the authoritative lineage. The recommended public-facing headline view should no longer be a plain exact-rank table. It should lead with the tiered synthesis view in `RANKING_RESULTS_SYNTHESIS_TIERED.csv`, using `hierarchical_trust_v2` rank as one field inside a broader interpretation layer.

Compared views:

- `hierarchical_trust_v2`: best current scoring backbone.
- `hierarchical_trust_v2_high_level_capped`: sensitivity check for broad-page dependence.
- `hierarchical_trust_v2_eligibility_filtered`: sensitivity check for nominal/political/staff exclusions.
- `hierarchical_trust_v2_role_weighted`: sensitivity check for direct command responsibility.
- Confidence-adjusted tiers: best public interpretation layer for uncertainty and exact-rank humility.

## Current Robust Elite Core

Alexander Suvorov, Maurice, Prince of Orange, Napoleon Bonaparte, Jean Lannes, Alexander Farnese, Duke of Parma, Khalid ibn al-Walid

These commanders remain strong after model stability, high-level capping, eligibility filtering, bootstrap confidence, and role-weighting checks. Their exact adjacent order should still be interpreted through confidence intervals.

## Top 25 Synthesis Comparison

| headline_rank | commander_name | rank_interval_80 | stability_category | high_level_capped_rank | eligibility_filtered_rank | role_weighted_rank | synthesis_tier | recommended_interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Alexander Suvorov | 1-9 | very_stable | 1 | 1.0 | 1 | Tier A, robust elite | Robust elite placement is defensible; exact adjacent rank should still be read through confidence bands. |
| 2 | Maurice, Prince of Orange | 1-23 | very_stable | 2 | 2.0 | 3 | Tier A, robust elite | Robust elite placement is defensible; exact adjacent rank should still be read through confidence bands. |
| 3 | Napoleon Bonaparte | 1-8 | very_stable | 3 | 3.0 | 2 | Tier A, robust elite | Robust elite placement is defensible; exact adjacent rank should still be read through confidence bands. |
| 4 | Subutai | 1-38 | very_stable | 4 | 4.0 | 11 | Tier B, elite but qualified | High placement is qualified by wide bootstrap interval. |
| 5 | Sébastien Le Prestre, Marquis of Vauban | 8-60 | very_stable | 5 | 5.0 | 23 | Tier D, category-specific strength | High placement is qualified by wide bootstrap interval, best read as siege engineer or specialist. |
| 6 | Jean Lannes | 2-9 | very_stable | 6 | 6.0 | 9 | Tier A, robust elite | Robust elite placement is defensible; exact adjacent rank should still be read through confidence bands. |
| 7 | Louis-Nicolas Davout | 7-43 | very_stable | 7 | 7.0 | 10 | Tier B, elite but qualified | High placement is qualified by wide bootstrap interval. |
| 8 | Douglas MacArthur | 14-100 | stable | 8 | 8.0 | 41 | Tier D, category-specific strength | High placement is qualified by wide bootstrap interval, large role-weighted movement, best read as coalition commander. |
| 9 | Charles XIV John | 10-52 | very_stable | 9 | 9.0 | 43 | Tier D, category-specific strength | High placement is qualified by wide bootstrap interval, large role-weighted movement, best read as coalition commander. |
| 10 | Ivan Paskevich | 7-201 | stable | 10 | 10.0 | 4 | Tier C, high performer with evidence caveats | High placement is qualified by wide bootstrap interval. |
| 11 | Louis XIV | 14-102 | stable | 11 | 11.0 | 987 | Tier F, not suitable for headline comparison | Not suitable for direct headline comparison without stronger source-backed command-role curation. |
| 12 | Henri de La Tour d'Auvergne, Viscount of Turenne | 9-87 | stable | 12 | 12.0 | 12 | Tier B, elite but qualified | High placement is qualified by wide bootstrap interval. |
| 13 | Mehmed II | 2-45 | stable | 13 | 13.0 | 22 | Tier B, elite but qualified | High placement is qualified by wide bootstrap interval. |
| 14 | Belisarius | 4-81 | stable | 14 | 14.0 | 36 | Tier B, elite but qualified | High placement is qualified by wide bootstrap interval, large role-weighted movement. |
| 15 | Louis-Gabriel Suchet | 9-95 | very_stable | 15 | 15.0 | 20 | Tier B, elite but qualified | High placement is qualified by wide bootstrap interval. |
| 16 | André Masséna | 6-48 | stable | 16 | 16.0 | 32 | Tier B, elite but qualified | High placement is qualified by wide bootstrap interval. |
| 17 | Alexander Farnese, Duke of Parma | 8-36 | very_stable | 17 | 17.0 | 14 | Tier A, robust elite | Robust elite placement is defensible; exact adjacent rank should still be read through confidence bands. |
| 18 | Khalid ibn al-Walid | 3-7 | very_stable | 18 | 18.0 | 17 | Tier A, robust elite | Robust elite placement is defensible; exact adjacent rank should still be read through confidence bands. |
| 19 | Genghis Khan | 7-111 | moderately_stable | 19 | 19.0 | 5 | Tier C, high performer with evidence caveats | High placement is qualified by wide bootstrap interval. |
| 20 | Hubert Gough | 19-139 | stable | 20 | 20.0 | 13 | Tier C, high performer with evidence caveats | High placement is qualified by wide bootstrap interval. |
| 21 | Bernard Montgomery | 25-133 | stable | 113 | 21.0 | 19 | Tier C, high performer with evidence caveats | High placement is qualified by wide bootstrap interval, high broad-page dependency. |
| 22 | Maharaja Ranjit Singh | 30-394 | moderately_stable | 21 | 22.0 | 53 | Tier C, high performer with evidence caveats | High placement is qualified by wide bootstrap interval, large role-weighted movement. |
| 23 | Alexander the Great | 31-220 | stable | 22 | 23.0 | 35 | Tier C, high performer with evidence caveats | High placement is qualified by wide bootstrap interval. |
| 24 | Winfield Scott | 31-325 | moderately_stable | 23 | 24.0 | 45 | Tier C, high performer with evidence caveats | High placement is qualified by wide bootstrap interval, large role-weighted movement. |
| 25 | Hannibal | 39-181 | stable | 24 | 25.0 | 15 | Tier C, high performer with evidence caveats | High placement is qualified by wide bootstrap interval. |

## High-Ranked Commanders Requiring Caveats

Subutai, Sébastien Le Prestre, Marquis of Vauban, Louis-Nicolas Davout, Douglas MacArthur, Charles XIV John, Ivan Paskevich, Louis XIV, Henri de La Tour d'Auvergne, Viscount of Turenne, Mehmed II, Belisarius, Louis-Gabriel Suchet, André Masséna, Genghis Khan, Hubert Gough, Bernard Montgomery, Maharaja Ranjit Singh, Alexander the Great, Winfield Scott, Hannibal, Enver Pasha, Baybars, Peng Dehuai, Frederick the Great, Heinz Guderian, Charles-Pierre Augereau, Takeda Shingen, Hari Singh Nalwa, Aurangzeb, Ögedei Khan, Dwight D. Eisenhower

## Not Direct Field-Command Comparisons

Sébastien Le Prestre, Marquis of Vauban, Douglas MacArthur, Charles XIV John, Dwight D. Eisenhower, Joseph Stalin

These are best read as category-specific, coalition/theater, siege/engineering, naval, staff/planning, or institutional cases where direct field-command comparison is not the right claim.

## Exact Rank Interpretation

Exact ranks are most meaningful when the commander has a narrow or moderate bootstrap interval, high model stability, low broad-page share, no eligibility exclusion, and minimal role-weighted movement. Exact ranks should be treated only as tier placement when intervals are wide, broad-page share is high, role-weighted movement is large, or role class is category-specific.

## Specific Commander Notes

- **Alexander Suvorov**: headline rank 1, role-weighted rank 1, tier `Tier A, robust elite`, 80% CI 1-9, dominant role `overall_commander`. Robust elite placement is defensible; exact adjacent rank should still be read through confidence bands.
- **Maurice, Prince of Orange**: headline rank 2, role-weighted rank 3, tier `Tier A, robust elite`, 80% CI 1-23, dominant role `overall_commander`. Robust elite placement is defensible; exact adjacent rank should still be read through confidence bands.
- **Napoleon Bonaparte**: headline rank 3, role-weighted rank 2, tier `Tier A, robust elite`, 80% CI 1-8, dominant role `overall_commander`. Robust elite placement is defensible; exact adjacent rank should still be read through confidence bands.
- **Subutai**: headline rank 4, role-weighted rank 11, tier `Tier B, elite but qualified`, 80% CI 1-38, dominant role `principal_field_commander`. High placement is qualified by wide bootstrap interval.
- **Sébastien Le Prestre, Marquis of Vauban**: headline rank 5, role-weighted rank 23, tier `Tier D, category-specific strength`, 80% CI 8-60, dominant role `siege_engineer_or_specialist`. High placement is qualified by wide bootstrap interval, best read as siege engineer or specialist.
- **Jean Lannes**: headline rank 6, role-weighted rank 9, tier `Tier A, robust elite`, 80% CI 2-9, dominant role `principal_field_commander`. Robust elite placement is defensible; exact adjacent rank should still be read through confidence bands.
- **Louis-Nicolas Davout**: headline rank 7, role-weighted rank 10, tier `Tier B, elite but qualified`, 80% CI 7-43, dominant role `principal_field_commander`. High placement is qualified by wide bootstrap interval.
- **Douglas MacArthur**: headline rank 8, role-weighted rank 41, tier `Tier D, category-specific strength`, 80% CI 14-100, dominant role `coalition_commander`. High placement is qualified by wide bootstrap interval, large role-weighted movement, best read as coalition commander.
- **Charles XIV John**: headline rank 9, role-weighted rank 43, tier `Tier D, category-specific strength`, 80% CI 10-52, dominant role `coalition_commander`. High placement is qualified by wide bootstrap interval, large role-weighted movement, best read as coalition commander.
- **Ivan Paskevich**: headline rank 10, role-weighted rank 4, tier `Tier C, high performer with evidence caveats`, 80% CI 7-201, dominant role `overall_commander`. High placement is qualified by wide bootstrap interval.
- **Dwight D. Eisenhower**: headline rank 36, role-weighted rank 68, tier `Tier D, category-specific strength`, 80% CI 54-312, dominant role `coalition_commander`. High placement is qualified by wide bootstrap interval, high broad-page dependency, large role-weighted movement, best read as coalition commander.
- **Georgy Zhukov**: headline rank 39, role-weighted rank 7, tier `Tier B, elite but qualified`, 80% CI 15-113, dominant role `overall_commander`. High placement is qualified by wide bootstrap interval, large role-weighted movement.
- **Genghis Khan**: headline rank 19, role-weighted rank 5, tier `Tier C, high performer with evidence caveats`, 80% CI 7-111, dominant role `overall_commander`. High placement is qualified by wide bootstrap interval.
- **Frederick the Great**: headline rank 29, role-weighted rank 6, tier `Tier B, elite but qualified`, 80% CI 8-100, dominant role `overall_commander`. High placement is qualified by wide bootstrap interval, large role-weighted movement.
- **Konstantin Rokossovsky**: headline rank 47, role-weighted rank 8, tier `Tier C, high performer with evidence caveats`, 80% CI 19-175, dominant role `overall_commander`. High placement is qualified by wide bootstrap interval, high broad-page dependency, large role-weighted movement.
- **Hannibal**: headline rank 25, role-weighted rank 15, tier `Tier C, high performer with evidence caveats`, 80% CI 39-181, dominant role `principal_field_commander`. High placement is qualified by wide bootstrap interval.
- **Julius Caesar**: not present as a ranked commander in the current identity bridge; this is a coverage/alias issue, not a model judgment.
- **Alexander the Great**: headline rank 23, role-weighted rank 35, tier `Tier C, high performer with evidence caveats`, 80% CI 31-220, dominant role `principal_field_commander`. High placement is qualified by wide bootstrap interval.
- **Khalid ibn al-Walid**: headline rank 18, role-weighted rank 17, tier `Tier A, robust elite`, 80% CI 3-7, dominant role `principal_field_commander`. Robust elite placement is defensible; exact adjacent rank should still be read through confidence bands.
- **Helmuth von Moltke the Elder**: headline rank 487, role-weighted rank 609, tier `Tier E, historically important but model-sensitive`, 80% CI 313-932, dominant role `wing_or_corps_commander`. High placement is qualified by wide bootstrap interval, large role-weighted movement.
- **Wellington**: not present as a ranked commander in the current identity bridge; this is a coverage/alias issue, not a model judgment.

## Release-Candidate Judgment

1. The upgraded system is ready to publish as a release candidate, not as a final historical verdict.
2. The strongest defensible claim is that the framework identifies a robust elite tier and makes uncertainty/audit caveats visible.
3. The project should not claim that adjacent exact ranks are historically definitive.
4. The robust elite core is the `Tier A, robust elite` group in `RANKING_RESULTS_SYNTHESIS_TIERED.csv`.
5. High-ranked but caveated commanders are listed in `CAVEATED_HIGH_RANKED_COMMANDERS.md`.
6. The next research pass should replace heuristic role labels with source-backed manual curation, then add opponent-strength and battle-difficulty sensitivity only where evidence quality supports it.

Final framing: this is a conservative, auditable, evidence-weighted commander ranking framework. It is strongest when read through tiers, confidence bands, and sensitivity diagnostics, not as a rigid exact-rank list.
