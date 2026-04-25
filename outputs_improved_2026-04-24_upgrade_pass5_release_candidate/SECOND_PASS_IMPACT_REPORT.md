# Second Pass Impact Report

## Top-Level Outcome

This second pass materially improved the trustworthiness of the rebuilt analytics stack without changing the headline leaders:

- baseline leader stayed `Alexander Suvorov`
- battle-only leader stayed `Khalid ibn al-Walid`
- hierarchical leader stayed `Suleiman the Magnificent`

What changed was the composition of the upper hierarchical table.

## Hierarchical Top Table Before vs After

| display_name | old_rank | new_rank |
| --- | --- | --- |
| Suleiman the Magnificent | 1 | 1 |
| Alexander Suvorov | 2 | 2 |
| Napoleon Bonaparte | 3 | 3 |
| Louis XIV | 5 | 4 |
| Louis-Nicolas Davout | 10 | 5 |
| Subutai |  | 6 |
| Babur |  | 7 |
| Emperor Taizong of Tang |  | 8 |
| Charles XIV John |  | 9 |
| Flavius Aetius |  | 10 |
| Henri de La Tour d'Auvergne, Viscount of Turenne | 11 | 11 |
| Jean Lannes |  | 12 |
| Qasem Soleimani | 4 |  |
| Jean Victor Marie Moreau | 6 |  |
| Mustafa Kemal Atatürk | 7 |  |
| Aleksandr Vasilevsky | 8 |  |
| Nelson A. Miles | 9 |  |
| Abbas the Great | 12 |  |

## Suspicious Case Movement

| display_name | old_hier_rank | new_hier_rank | old_best_rank | new_best_rank | stability_label |
| --- | --- | --- | --- | --- | --- |
| Qasem Soleimani | 4 | 13 | 4 | 12 | highly_model_sensitive |
| Nelson A. Miles | 9 | 16 | 6 | 7 | highly_model_sensitive |
| Charles XII of Sweden | 199 | 118 | 17 | 16 | highly_model_sensitive |
| Jean Victor Marie Moreau | 6 | 25 | 5 | 15 | model_sensitive |
| Aleksandr Vasilevsky | 8 | 33 | 7 | 29 | highly_model_sensitive |

Key interpretation:

- `Qasem Soleimani` moved from `#4` to `#13` in hierarchical_weighted.
- `Nelson A. Miles` moved from `#9` to `#16`.
- `Jean Victor Marie Moreau` moved from `#6` to `#25`.
- `Aleksandr Vasilevsky` moved from `#8` to `#33`.
- `Charles XII of Sweden` actually rose inside hierarchical views after the year-correction pass, but he remains far from the top and is no longer a headline anomaly.

## Cohort Size Impact

- baseline_conservative: `664 -> 683`
- battle_only_baseline: `2,197 -> 2,217`
- hierarchical_weighted: `1,230 -> 1,286`
- hierarchical_broader_eligibility: `1,289 -> 1,353`

The net cohort expansion came from outcome-resolution improvements and year corrections. The scoring-layer exclusion of the non-person `Manner of death` rows was more than offset by rows that became cleanly eligible after the second-pass fixes.

## Residual Caution Cases In The Current Hierarchical Top 25

| rank | display_name | interpretive_group | caution_flags |
| --- | --- | --- | --- |
| 10 | Flavius Aetius | caution_likely_artifact |  |
| 13 | Qasem Soleimani | caution_likely_artifact |  |
| 16 | Nelson A. Miles | caution_likely_artifact | higher_level_dependent |
| 18 | Stepa Stepanović | caution_likely_artifact |  |
| 19 | Živojin Mišić | caution_likely_artifact |  |
| 21 | Petar Bojović | caution_likely_artifact | higher_level_dependent |

## Trust Judgment After The Second Pass

- `hierarchical_weighted` remains the most trustworthy single model.
- Its trust level improved in this pass because the known residual bug class no longer explains the most suspicious first-pass leaders.
- `baseline_conservative` is better than before but still battle-specialist heavy.
- `hierarchical_full_credit` remains the weakest model because it still over-rewards higher-level page accumulation.

## Remaining Concerns

- Some coalition/allied pages are still unresolved and continue to affect scope and centrality even though they no longer distort outcome means.
- `Qasem Soleimani` and `Nelson A. Miles` remain caution cases rather than robust elite outcomes.
- `Flavius Aetius` and a few other top-25 names remain historically arguable but lower-confidence because of sparse or uneven source coverage.

## Dashboard Synchronization

- dashboard snapshot label: `outputs_cleaned_2026-04-10_secondpass_authoritative`
- expected ranked commanders in dashboard: `2,422`
- baseline leader match: `Alexander Suvorov`
- hierarchical leader match: `Suleiman the Magnificent`
- all dashboard checks passed: `True`

## Bottom Line

The second pass did not prove the ranking system perfect, but it moved the remaining issues into the acceptable category: explicitly documented, bounded, and no longer obviously driving the top-level conclusions. The current hierarchy is materially more trustworthy than the first rank-fix snapshot, with `hierarchical_weighted` still the best current single model.
