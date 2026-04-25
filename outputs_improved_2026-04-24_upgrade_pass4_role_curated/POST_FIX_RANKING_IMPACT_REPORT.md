# Post Fix Ranking Impact Report

## Scope

This report compares the old authoritative ranking package in `outputs_cleaned_2026-04-10_authoritative` with the corrected ranking package in `outputs_cleaned_2026-04-10_rankfix_authoritative`.

## Cohort Impact

- conservative baseline cohort: `519` -> `664` (+145)
- battle-only baseline cohort: `1,970` -> `2,197` (+227)
- hierarchical weighted cohort: `1,009` -> `1,230` (+221)
- broader-eligibility hierarchical cohort: `1,056` -> `1,289` (+233)
- ranked commanders shown in dashboard data: `2,127` -> `2,370` (+243)

This cohort growth is expected: once many previously-unknown outcomes became valid outcomes, more commanders cleared battle/outcome gates.

## Charles XII Of Sweden

### Rank Impact

- `baseline_conservative`: `1` -> `17`
- `battle_only_baseline`: `2` -> `33`
- `hierarchical_weighted`: `88` -> `199`
- `hierarchical_full_credit`: `113` -> `268`
- `hierarchical_equal_split`: `79` -> `198`
- `hierarchical_broader_eligibility`: `98` -> `213`

### Outcome Profile Impact

- known outcomes: `19` -> `21`
- outcome summary: `V=17; D=2; N=0; U=3` -> `V=15; D=6; N=0; U=1`
- page-type exposure: `B=21; O=0; C=0; W=1`

### Interpretation

Charles XII was previously being flattered by a mix of wrong victories, unresolved defeats, and too-harsh linear split dilution on crowded pages. After the fixes:

- four important Charles rows moved in the historically expected direction
- his defeat count rose from `2` to `6`
- his baseline and battle-only placements stopped looking like obvious headline winners
- he remains a strong battle-dominant commander, but he is now clearly model-sensitive rather than baseline-proof

## Model-Level Impact

### Conservative Baseline

- old leader: `Charles XII of Sweden`
- new leader: `Alexander Suvorov`
- old top 5: `Charles XII of Sweden`, `Khalid ibn al-Walid`, `Alexander Suvorov`, `Belisarius`, and `Takeda Shingen`
- new top 5: `Alexander Suvorov`, `Alexander Farnese, Duke of Parma`, `Khalid ibn al-Walid`, `Sébastien Le Prestre, Marquis of Vauban`, and `Takeda Shingen`

Judgment:

- This model improved materially because the Charles XII anomaly is gone.
- It is still battle-specialist heavy and should still be treated as a diagnostic battle-performance view, not a final all-time headline ranking.

### Battle-Only Baseline

- old leader: `Khalid ibn al-Walid`
- new leader: `Khalid ibn al-Walid`
- old top 5: `Khalid ibn al-Walid`, `Charles XII of Sweden`, `Alexander Suvorov`, `Takeda Shingen`, and `Belisarius`
- new top 5: `Khalid ibn al-Walid`, `Jean Lannes`, `Takeda Shingen`, `Alexander Suvorov`, and `Saladin`

Judgment:

- This model remains intentionally narrow and still rewards battle-specialist profiles very aggressively.
- It is useful as a stress test, but not as the single best answer to the overall research question.

### Hierarchical Weighted

- old leader: `Suleiman the Magnificent`
- new leader: `Suleiman the Magnificent`
- old top 5: `Suleiman the Magnificent`, `Alexander Suvorov`, `Ibrahim Pasha of Egypt`, `Napoleon Bonaparte`, and `Abbas the Great`
- new top 5: `Suleiman the Magnificent`, `Alexander Suvorov`, `Napoleon Bonaparte`, `Qasem Soleimani`, and `Louis XIV`

Judgment:

- This remains the most trustworthy single ranking view in the package.
- It still needs interpretive caution because some historically suspicious higher-level beneficiaries remain high, especially `Qasem Soleimani` and `Nelson A. Miles`.

### Full-Credit / Equal-Split / Broader-Eligibility Views

- `hierarchical_full_credit` remains the least trustworthy model because it is still the most exposed to attribution inflation.
- `hierarchical_equal_split` is safer than full-credit, but still sensitive to page structure and higher-level exposure.
- `hierarchical_broader_eligibility` is useful for exploratory stress-testing, not for the headline conclusion layer.

## Interpretive Layer Impact

Robust-elite additions:

- `Henri de La Tour d'Auvergne, Viscount of Turenne`
- `Jean Victor Marie Moreau`
- `Napoleon Bonaparte`
- `Subutai`

Robust-elite removals:

- `Frederick Henry, Prince of Orange`
- `Georgy Zhukov`

This is a real interpretive shift. The corrected system now leans more toward commanders whose records survive both stronger defeat treatment and the repaired outcome inference.

## Historically Suspicious Results That Still Remain

| display_name | interpretive_group | best_rank | worst_rank | dominant_sensitivity_driver | interpretive_reason |
| --- | --- | --- | --- | --- | --- |
| Qasem Soleimani | caution_likely_artifact | 4.0 | 265.0 | higher_level_page_dependency | Higher-level war/campaign/operation pages are doing substantial work. Battle-only restrictions cause a severe collapse. |
| Nelson A. Miles | caution_likely_artifact | 6.0 | 858.0 | higher_level_page_dependency | Higher-level war/campaign/operation pages are doing substantial work. Battle-only restrictions cause a severe collapse. |

Bottom line on residual plausibility issues:

- `Qasem Soleimani` remains a caution case even after the fixes; his very high hierarchical placement is still driven by higher-level exposure.
- `Nelson A. Miles` remains a caution case for the same reason.
- `Charles XII of Sweden` is no longer the obvious red flag he was before, but his profile is still highly model-sensitive and battle-dominant.

## Dashboard Synchronization

- dashboard snapshot label: `outputs_cleaned_2026-04-10_rankfix_authoritative`
- baseline leader alignment: `Alexander Suvorov`
- hierarchical leader alignment: `Suleiman the Magnificent`
- all dashboard QA checks passed: `True`
- console errors: `0`
- page errors: `0`

## Updated Trust Judgment

- `hierarchical_weighted` remains the most trustworthy single model.
- `baseline_conservative` is now materially better and no longer obviously broken by Charles XII, but it is still not a final all-time model.
- `battle_only_baseline` remains a useful battle-performance stress test.
- `hierarchical_full_credit` still needs revision before it should be trusted as a headline table.

## Final Judgment

The ranking system is more historically and methodologically sound than the previous authoritative package. The Charles XII anomaly was real, and it was driven by both a logic bug and design behavior. That issue is now materially corrected. The package is still not free of interpretive tension, but the remaining problems are now mostly model- and coverage-related caution cases, not the specific scoring defects identified in the audit.
