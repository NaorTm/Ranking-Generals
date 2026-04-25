# Upgrade Pass 3 Confidence Report

Snapshot reviewed: `outputs_improved_2026-04-24_upgrade_pass3_confidence`

Status: confidence and uncertainty pass only. `hierarchical_trust_v2` remains the headline model and is not replaced here.

## Methodology

Bootstrap method: battle-level resampling with replacement. Each iteration samples the retained `battle_id` universe with replacement, includes all commander rows attached to sampled battles, recomputes model scores and ranks, and records rank/score distributions.

- Bootstrap iterations: `200`
- Random seed: `20260424`
- Sampled battle IDs per iteration: `12377`
- Runtime seconds: `142.071`
- Models included: `hierarchical_trust_v2, hierarchical_weighted, baseline_conservative, battle_only_baseline, hierarchical_trust_v2_high_level_capped, hierarchical_trust_v2_eligibility_filtered`

The intervals are empirical model uncertainty under current data and scoring assumptions. They are not absolute historical truth.

## Top 25 With Confidence Intervals

| headline_rank | commander_name | tier | stability_category | rank_interval_80 | rank_interval_90 | rank_band_width_80 | confidence_category | recommended_interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Alexander Suvorov | Tier A, robust elite | very_stable | 1-9 | 1-13 | 8.1 | narrow | Robust elite: exact rank is still not historical truth, but elite-band placement is strongly supported. |
| 2 | Maurice, Prince of Orange | Tier D, strong but narrow-category performer | very_stable | 1-23 | 1-32 | 22.0 | moderate | Rank band is reasonably constrained under current model assumptions. |
| 3 | Napoleon Bonaparte | Tier A, robust elite | very_stable | 1-8 | 1-11 | 7.0 | narrow | Robust elite: exact rank is still not historical truth, but elite-band placement is strongly supported. |
| 4 | Subutai | Tier A, robust elite | very_stable | 1-38 | 1-71 | 37.2 | wide | High-ranking but confidence-limited: emphasize tier and interval over exact rank. |
| 5 | Sébastien Le Prestre, Marquis of Vauban | Tier D, strong but narrow-category performer | very_stable | 8-60 | 7-98 | 52.0 | wide | High-ranking but confidence-limited: emphasize tier and interval over exact rank. |
| 6 | Jean Lannes | Tier A, robust elite | very_stable | 2-9 | 2-10 | 7.0 | narrow | Robust elite: exact rank is still not historical truth, but elite-band placement is strongly supported. |
| 7 | Louis-Nicolas Davout | Tier A, robust elite | very_stable | 7-43 | 6-66 | 36.2 | wide | High-ranking but confidence-limited: emphasize tier and interval over exact rank. |
| 8 | Douglas MacArthur | Tier A, robust elite | stable | 14-100 | 12-116 | 86.1 | wide | High-ranking but confidence-limited: emphasize tier and interval over exact rank. |
| 9 | Charles XIV John | Tier A, robust elite | very_stable | 10-52 | 9-85 | 42.3 | wide | High-ranking but confidence-limited: emphasize tier and interval over exact rank. |
| 10 | Ivan Paskevich | Tier B, elite but model-sensitive | stable | 7-201 | 4-490 | 194.2 | very_wide | High-ranking but confidence-limited: emphasize tier and interval over exact rank. |
| 11 | Louis XIV | Tier D, strong but narrow-category performer | stable | 14-102 | 10-149 | 88.0 | wide | High-ranking but confidence-limited: emphasize tier and interval over exact rank. |
| 12 | Henri de La Tour d'Auvergne, Viscount of Turenne | Tier A, robust elite | stable | 9-87 | 7-108 | 78.1 | wide | High-ranking but confidence-limited: emphasize tier and interval over exact rank. |
| 13 | Mehmed II | Tier D, strong but narrow-category performer | stable | 2-45 | 1-65 | 43.1 | wide | High-ranking but confidence-limited: emphasize tier and interval over exact rank. |
| 14 | Belisarius | Tier D, strong but narrow-category performer | stable | 4-81 | 2-127 | 77.2 | wide | High-ranking but confidence-limited: emphasize tier and interval over exact rank. |
| 15 | Louis-Gabriel Suchet | Tier A, robust elite | very_stable | 9-95 | 8-132 | 86.0 | wide | High-ranking but confidence-limited: emphasize tier and interval over exact rank. |
| 16 | André Masséna | Tier A, robust elite | stable | 6-48 | 5-68 | 42.3 | wide | High-ranking but confidence-limited: emphasize tier and interval over exact rank. |
| 17 | Alexander Farnese, Duke of Parma | Tier D, strong but narrow-category performer | very_stable | 8-36 | 7-47 | 28.0 | moderate | Rank band is reasonably constrained under current model assumptions. |
| 18 | Khalid ibn al-Walid | Tier A, robust elite | very_stable | 3-7 | 2-8 | 4.0 | narrow | Robust elite: exact rank is still not historical truth, but elite-band placement is strongly supported. |
| 19 | Genghis Khan | Tier D, strong but narrow-category performer | moderately_stable | 7-111 | 6-160 | 104.2 | very_wide | High-ranking but confidence-limited: emphasize tier and interval over exact rank. |
| 20 | Hubert Gough | Tier A, robust elite | stable | 19-139 | 15-167 | 120.5 | very_wide | High-ranking but confidence-limited: emphasize tier and interval over exact rank. |
| 21 | Bernard Montgomery | Tier B, elite but model-sensitive | stable | 25-133 | 21-182 | 108.3 | very_wide | High-ranking but confidence-limited: emphasize tier and interval over exact rank. |
| 22 | Maharaja Ranjit Singh | Tier B, elite but model-sensitive | moderately_stable | 30-394 | 19-469 | 364.5 | very_wide | High-ranking but confidence-limited: emphasize tier and interval over exact rank. |
| 23 | Alexander the Great | Tier D, strong but narrow-category performer | stable | 31-220 | 25-278 | 189.1 | very_wide | High-ranking but confidence-limited: emphasize tier and interval over exact rank. |
| 24 | Winfield Scott | Tier B, elite but model-sensitive | moderately_stable | 31-325 | 24-403 | 294.0 | very_wide | High-ranking but confidence-limited: emphasize tier and interval over exact rank. |
| 25 | Hannibal | Tier A, robust elite | stable | 39-181 | 31-219 | 142.2 | very_wide | High-ranking but confidence-limited: emphasize tier and interval over exact rank. |

## Commanders Whose Exact Rank Is Stable

| headline_rank | commander_name | rank_interval_80 | rank_band_width_80 | confidence_category | tier |
| --- | --- | --- | --- | --- | --- |
| 1 | Alexander Suvorov | 1-9 | 8.1 | narrow | Tier A, robust elite |
| 3 | Napoleon Bonaparte | 1-8 | 7.0 | narrow | Tier A, robust elite |
| 6 | Jean Lannes | 2-9 | 7.0 | narrow | Tier A, robust elite |
| 18 | Khalid ibn al-Walid | 3-7 | 4.0 | narrow | Tier A, robust elite |

## Commanders Whose Exact Rank Is Fragile

| headline_rank | commander_name | rank_interval_80 | rank_band_width_80 | confidence_category | tier | recommended_interpretation |
| --- | --- | --- | --- | --- | --- | --- |
| 66 | Petar Bojović | 53-541 | 488.3 | very_wide | Tier C, high performer with evidence caveats | Wide uncertainty: use tier and sensitivity context rather than exact adjacent rank. |
| 93 | Zubayr ibn al-Awwam | 38-523 | 485.1 | very_wide | Tier C, high performer with evidence caveats | Wide uncertainty: use tier and sensitivity context rather than exact adjacent rank. |
| 90 | Yamagata Aritomo | 35-483 | 448.0 | very_wide | Tier C, high performer with evidence caveats | Wide uncertainty: use tier and sensitivity context rather than exact adjacent rank. |
| 87 | Carl Gustaf Wrangel | 35-464 | 428.6 | very_wide | Tier C, high performer with evidence caveats | Wide uncertainty: use tier and sensitivity context rather than exact adjacent rank. |
| 95 | Date Masamune | 29-428 | 399.1 | very_wide | Tier D, strong but narrow-category performer | Wide uncertainty: use tier and sensitivity context rather than exact adjacent rank. |
| 70 | Ernst Gideon von Laudon | 33-425 | 392.3 | very_wide | Tier C, high performer with evidence caveats | Wide uncertainty: use tier and sensitivity context rather than exact adjacent rank. |
| 91 | Ambrogio Spinola | 35-425 | 390.2 | very_wide | Tier D, strong but narrow-category performer | Wide uncertainty: use tier and sensitivity context rather than exact adjacent rank. |
| 71 | Živojin Mišić | 52-425 | 372.9 | very_wide | Tier C, high performer with evidence caveats | Wide uncertainty: use tier and sensitivity context rather than exact adjacent rank. |
| 22 | Maharaja Ranjit Singh | 30-394 | 364.5 | very_wide | Tier B, elite but model-sensitive | High-ranking but confidence-limited: emphasize tier and interval over exact rank. |
| 96 | Lennart Torstensson | 103-460 | 356.6 | very_wide | Tier C, high performer with evidence caveats | Wide uncertainty: use tier and sensitivity context rather than exact adjacent rank. |
| 97 | Honda Tadakatsu | 49-393 | 344.4 | very_wide | Tier C, high performer with evidence caveats | Wide uncertainty: use tier and sensitivity context rather than exact adjacent rank. |
| 81 | Bertrand du Guesclin | 35-376 | 341.5 | very_wide | Tier C, high performer with evidence caveats | Wide uncertainty: use tier and sensitivity context rather than exact adjacent rank. |
| 28 | Peng Dehuai | 68-408 | 340.1 | very_wide | Tier B, elite but model-sensitive | Wide uncertainty: use tier and sensitivity context rather than exact adjacent rank. |
| 59 | Aleksandr Vasilevsky | 49-388 | 338.7 | very_wide | Tier C, high performer with evidence caveats | Wide uncertainty: use tier and sensitivity context rather than exact adjacent rank. |
| 77 | Babur | 32-365 | 333.2 | very_wide | Tier D, strong but narrow-category performer | Wide uncertainty: use tier and sensitivity context rather than exact adjacent rank. |
| 68 | Ahmad Shah Durrani | 23-346 | 323.4 | very_wide | Tier C, high performer with evidence caveats | Wide uncertainty: use tier and sensitivity context rather than exact adjacent rank. |
| 52 | Ōyama Iwao | 24-334 | 310.7 | very_wide | Tier C, high performer with evidence caveats | Wide uncertainty: use tier and sensitivity context rather than exact adjacent rank. |
| 69 | François-Henri de Montmorency, duc de Luxembourg | 63-373 | 310.0 | very_wide | Tier C, high performer with evidence caveats | Wide uncertainty: use tier and sensitivity context rather than exact adjacent rank. |
| 33 | Hari Singh Nalwa | 36-341 | 305.0 | very_wide | Tier B, elite but model-sensitive | Wide uncertainty: use tier and sensitivity context rather than exact adjacent rank. |
| 100 | Skanderbeg | 45-342 | 297.6 | very_wide | Tier C, high performer with evidence caveats | Wide uncertainty: use tier and sensitivity context rather than exact adjacent rank. |

## Tier Stable Despite Rank Uncertainty

| headline_rank | commander_name | confidence_adjusted_tier | rank_interval_80 | confidence_category | confidence_adjusted_tier_reason |
| --- | --- | --- | --- | --- | --- |
| 1 | Alexander Suvorov | Tier A, confidence-supported robust elite | 1-9 | narrow | Elite placement remains supported under bootstrap uncertainty. |
| 2 | Maurice, Prince of Orange | Tier B, confidence-supported elite | 1-23 | moderate | Upper-band placement is supported, but exact rank should be read as an interval. |
| 3 | Napoleon Bonaparte | Tier A, confidence-supported robust elite | 1-8 | narrow | Elite placement remains supported under bootstrap uncertainty. |
| 4 | Subutai | Tier B, confidence-supported elite | 1-38 | wide | Upper-band placement is supported, but exact rank should be read as an interval. |
| 5 | Sébastien Le Prestre, Marquis of Vauban | Tier B, confidence-supported elite | 8-60 | wide | Upper-band placement is supported, but exact rank should be read as an interval. |
| 6 | Jean Lannes | Tier A, confidence-supported robust elite | 2-9 | narrow | Elite placement remains supported under bootstrap uncertainty. |
| 7 | Louis-Nicolas Davout | Tier B, confidence-supported elite | 7-43 | wide | Upper-band placement is supported, but exact rank should be read as an interval. |
| 8 | Douglas MacArthur | Tier B, confidence-supported elite | 14-100 | wide | Upper-band placement is supported, but exact rank should be read as an interval. |
| 9 | Charles XIV John | Tier B, confidence-supported elite | 10-52 | wide | Upper-band placement is supported, but exact rank should be read as an interval. |
| 11 | Louis XIV | Tier B, confidence-supported elite | 14-102 | wide | Upper-band placement is supported, but exact rank should be read as an interval. |
| 12 | Henri de La Tour d'Auvergne, Viscount of Turenne | Tier B, confidence-supported elite | 9-87 | wide | Upper-band placement is supported, but exact rank should be read as an interval. |
| 13 | Mehmed II | Tier B, confidence-supported elite | 2-45 | wide | Upper-band placement is supported, but exact rank should be read as an interval. |
| 14 | Belisarius | Tier B, confidence-supported elite | 4-81 | wide | Upper-band placement is supported, but exact rank should be read as an interval. |
| 15 | Louis-Gabriel Suchet | Tier B, confidence-supported elite | 9-95 | wide | Upper-band placement is supported, but exact rank should be read as an interval. |
| 16 | André Masséna | Tier B, confidence-supported elite | 6-48 | wide | Upper-band placement is supported, but exact rank should be read as an interval. |
| 17 | Alexander Farnese, Duke of Parma | Tier B, confidence-supported elite | 8-36 | moderate | Upper-band placement is supported, but exact rank should be read as an interval. |
| 18 | Khalid ibn al-Walid | Tier A, confidence-supported robust elite | 3-7 | narrow | Elite placement remains supported under bootstrap uncertainty. |
| 32 | Takeda Shingen | Tier B, confidence-supported elite | 18-88 | wide | Upper-band placement is supported, but exact rank should be read as an interval. |

## Tier Downgrades Or Caveats

| headline_rank | commander_name | confidence_adjusted_tier | rank_interval_80 | confidence_category | confidence_adjusted_tier_reason |
| --- | --- | --- | --- | --- | --- |
| 10 | Ivan Paskevich | Tier C, high-ranking but confidence-limited | 7-201 | very_wide | High rank has a wide bootstrap interval; emphasize tier over exact rank. |
| 19 | Genghis Khan | Tier C, high-ranking but confidence-limited | 7-111 | very_wide | High rank has a wide bootstrap interval; emphasize tier over exact rank. |
| 20 | Hubert Gough | Tier C, high-ranking but confidence-limited | 19-139 | very_wide | High rank has a wide bootstrap interval; emphasize tier over exact rank. |
| 21 | Bernard Montgomery | Tier C, high-ranking but confidence-limited | 25-133 | very_wide | High rank has a wide bootstrap interval; emphasize tier over exact rank. |
| 22 | Maharaja Ranjit Singh | Tier C, high-ranking but confidence-limited | 30-394 | very_wide | High rank has a wide bootstrap interval; emphasize tier over exact rank. |
| 23 | Alexander the Great | Tier C, high-ranking but confidence-limited | 31-220 | very_wide | High rank has a wide bootstrap interval; emphasize tier over exact rank. |
| 24 | Winfield Scott | Tier C, high-ranking but confidence-limited | 31-325 | very_wide | High rank has a wide bootstrap interval; emphasize tier over exact rank. |
| 25 | Hannibal | Tier C, high-ranking but confidence-limited | 39-181 | very_wide | High rank has a wide bootstrap interval; emphasize tier over exact rank. |
| 26 | Enver Pasha | Tier C, high-ranking but confidence-limited | 44-322 | very_wide | High rank has a wide bootstrap interval; emphasize tier over exact rank. |
| 27 | Baybars | Tier C, high-ranking but confidence-limited | 21-295 | very_wide | High rank has a wide bootstrap interval; emphasize tier over exact rank. |
| 28 | Peng Dehuai | Tier C, high-ranking but confidence-limited | 68-408 | very_wide | High rank has a wide bootstrap interval; emphasize tier over exact rank. |
| 29 | Frederick the Great | Tier C, high-ranking but confidence-limited | 8-100 | wide | High rank has a wide bootstrap interval; emphasize tier over exact rank. |
| 30 | Heinz Guderian | Tier C, high-ranking but confidence-limited | 10-218 | very_wide | High rank has a wide bootstrap interval; emphasize tier over exact rank. |
| 31 | Charles-Pierre Augereau | Tier C, high-ranking but confidence-limited | 9-98 | wide | High rank has a wide bootstrap interval; emphasize tier over exact rank. |
| 33 | Hari Singh Nalwa | Tier C, high-ranking but confidence-limited | 36-341 | very_wide | High rank has a wide bootstrap interval; emphasize tier over exact rank. |
| 34 | Aurangzeb | Tier C, high-ranking but confidence-limited | 12-213 | very_wide | High rank has a wide bootstrap interval; emphasize tier over exact rank. |
| 35 | Ögedei Khan | Tier C, high-ranking but confidence-limited | 14-187 | very_wide | High rank has a wide bootstrap interval; emphasize tier over exact rank. |
| 36 | Dwight D. Eisenhower | Tier C, high-ranking but confidence-limited | 54-312 | very_wide | High rank has a wide bootstrap interval; emphasize tier over exact rank. |
| 37 | Katō Kiyomasa | Tier C, high-ranking but confidence-limited | 22-250 | very_wide | High rank has a wide bootstrap interval; emphasize tier over exact rank. |
| 38 | Tokugawa Ieyasu | Tier C, high-ranking but confidence-limited | 9-190 | very_wide | High rank has a wide bootstrap interval; emphasize tier over exact rank. |

## Non-Top-10 Commanders Frequently Appearing In Bootstrap Top 10

| original_rank | commander_name | rank_p10 | rank_p90 | top10_bootstrap_count | top10_bootstrap_rate |
| --- | --- | --- | --- | --- | --- |
| 18 | Khalid ibn al-Walid | 3.0 | 7.0 | 196 | 0.98 |
| 13 | Mehmed II | 2.0 | 45.1 | 95 | 0.475 |
| 16 | André Masséna | 6.0 | 48.3 | 74 | 0.37 |
| 51 | Jean Victor Marie Moreau | 5.0 | 58.1 | 55 | 0.275 |
| 14 | Belisarius | 4.0 | 81.2 | 54 | 0.27 |
| 17 | Alexander Farnese, Duke of Parma | 8.0 | 36.0 | 53 | 0.265 |
| 83 | Suleiman the Magnificent | 6.9 | 100.0 | 34 | 0.17 |
| 19 | Genghis Khan | 7.0 | 111.2 | 32 | 0.16 |
| 15 | Louis-Gabriel Suchet | 9.0 | 95.0 | 31 | 0.155 |
| 12 | Henri de La Tour d'Auvergne, Viscount of Turenne | 9.0 | 87.1 | 30 | 0.15 |
| 31 | Charles-Pierre Augereau | 8.8 | 98.1 | 30 | 0.15 |
| 29 | Frederick the Great | 8.0 | 100.2 | 27 | 0.135 |
| 38 | Tokugawa Ieyasu | 9.0 | 190.5 | 24 | 0.12 |
| 30 | Heinz Guderian | 10.0 | 218.1 | 23 | 0.115 |
| 41 | Stanisław Żółkiewski | 10.0 | 161.1 | 22 | 0.11 |
| 54 | Mahmud Pasha Angelović | 10.9 | 146.2 | 20 | 0.1 |
| 62 | Francis Vere | 11.0 | 85.0 | 18 | 0.09 |
| 34 | Aurangzeb | 12.0 | 213.1 | 16 | 0.08 |
| 49 | Tolui | 12.0 | 272.0 | 15 | 0.075 |
| 53 | Amr ibn al-As | 13.0 | 138.1 | 12 | 0.06 |

## Specific Top-10 Questions

1. Alexander Suvorov remains within the top elite band under bootstrap uncertainty; use robust elite language rather than treating rank #1 as metaphysical certainty.
2. Napoleon's elite-tier status is more meaningful than exact adjacent placement; the bootstrap interval states how much exact-rank precision is justified.
3. Maurice of Orange, Jean Lannes, and Davout remain elite/upper-band cases, but Maurice should still be described as siege/category-specific where the tier audit says so.
4. Vauban, MacArthur, Charles XIV John, Subutai, and Paskevich should be read through their confidence intervals and Pass 1/2 caveats, especially model sensitivity and category dependence.
5. High exact-rank but wide-interval commanders are listed in the fragile exact-rank table.
6. Non-top-10 commanders with bootstrap top-10 appearances are listed above.
7. Commanders in confidence-supported Tier A should be described as robust elite rather than assigned a hard final exact rank.
8. High-ranking commanders with wide/very-wide intervals should be described as high-ranking but confidence-limited.

Focused top-10 notes:

- `Alexander Suvorov`: exact rank #1, 80% interval `1-9`, 90% interval `1-13`, confidence `narrow`. Robust elite: exact rank is still not historical truth, but elite-band placement is strongly supported.
- `Maurice, Prince of Orange`: exact rank #2, 80% interval `1-23`, 90% interval `1-32`, confidence `moderate`. Rank band is reasonably constrained under current model assumptions.
- `Napoleon Bonaparte`: exact rank #3, 80% interval `1-8`, 90% interval `1-11`, confidence `narrow`. Robust elite: exact rank is still not historical truth, but elite-band placement is strongly supported.
- `Subutai`: exact rank #4, 80% interval `1-38`, 90% interval `1-71`, confidence `wide`. High-ranking but confidence-limited: emphasize tier and interval over exact rank.
- `Sébastien Le Prestre, Marquis of Vauban`: exact rank #5, 80% interval `8-60`, 90% interval `7-98`, confidence `wide`. High-ranking but confidence-limited: emphasize tier and interval over exact rank.
- `Jean Lannes`: exact rank #6, 80% interval `2-9`, 90% interval `2-10`, confidence `narrow`. Robust elite: exact rank is still not historical truth, but elite-band placement is strongly supported.
- `Louis-Nicolas Davout`: exact rank #7, 80% interval `7-43`, 90% interval `6-66`, confidence `wide`. High-ranking but confidence-limited: emphasize tier and interval over exact rank.
- `Douglas MacArthur`: exact rank #8, 80% interval `14-100`, 90% interval `12-116`, confidence `wide`. High-ranking but confidence-limited: emphasize tier and interval over exact rank.
- `Charles XIV John`: exact rank #9, 80% interval `10-52`, 90% interval `9-85`, confidence `wide`. High-ranking but confidence-limited: emphasize tier and interval over exact rank.
- `Ivan Paskevich`: exact rank #10, 80% interval `7-201`, 90% interval `4-490`, confidence `very_wide`. High-ranking but confidence-limited: emphasize tier and interval over exact rank.

## Final Interpretation Rule

After Pass 3, every headline placement should distinguish exact rank, confidence band, tier, model sensitivity, and evidence limitations. The ranking is now less brittle because it can say both where a commander ranks and how much precision that rank deserves.
