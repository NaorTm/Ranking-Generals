# Upgrade Pass 3 Confidence Report

Snapshot reviewed: `outputs_improved_2026-04-24_upgrade_pass3_confidence`

Status: confidence and uncertainty pass only. `hierarchical_trust_v2` remains the headline model and is not replaced here.

## Methodology

Bootstrap method: battle-level resampling with replacement. Each iteration samples the retained `battle_id` universe with replacement, includes all commander rows attached to sampled battles, recomputes model scores and ranks, and records rank/score distributions.

- Bootstrap iterations: `200`
- Random seed: `20260424`
- Sampled battle IDs per iteration: `12377`
- Runtime seconds: `366.791`
- Models included: `hierarchical_trust_v2, hierarchical_weighted, baseline_conservative, battle_only_baseline, hierarchical_trust_v2_high_level_capped, hierarchical_trust_v2_eligibility_filtered`

The intervals are empirical model uncertainty under current data and scoring assumptions. They are not absolute historical truth.

## Top 25 With Confidence Intervals

| headline_rank | commander_name | tier | stability_category | rank_interval_80 | rank_interval_90 | rank_band_width_80 | confidence_category | recommended_interpretation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Alexander Suvorov | Tier A, robust elite | very_stable | 1-9 | 1-14 | 8.0 | narrow | Robust elite: exact rank is still not historical truth, but elite-band placement is strongly supported. |
| 2 | Maurice, Prince of Orange | Tier D, strong but narrow-category performer | very_stable | 2-36 | 1-46 | 34.0 | wide | High-ranking but confidence-limited: emphasize tier and interval over exact rank. |
| 3 | Napoleon Bonaparte | Tier A, robust elite | very_stable | 2-23 | 1-26 | 21.0 | moderate | Robust elite: exact rank is still not historical truth, but elite-band placement is strongly supported. |
| 4 | Subutai | Tier A, robust elite | very_stable | 3-62 | 2-89 | 59.2 | wide | High-ranking but confidence-limited: emphasize tier and interval over exact rank. |
| 5 | Sébastien Le Prestre, Marquis of Vauban | Tier D, strong but narrow-category performer | very_stable | 3-32 | 2-59 | 29.0 | moderate | Rank band is reasonably constrained under current model assumptions. |
| 6 | Jean Lannes | Tier A, robust elite | very_stable | 4-13 | 4-15 | 9.0 | narrow | Robust elite: exact rank is still not historical truth, but elite-band placement is strongly supported. |
| 7 | Louis-Nicolas Davout | Tier A, robust elite | very_stable | 3-33 | 3-58 | 30.2 | wide | High-ranking but confidence-limited: emphasize tier and interval over exact rank. |
| 8 | Douglas MacArthur | Tier A, robust elite | stable | 4-72 | 2-89 | 68.4 | wide | High-ranking but confidence-limited: emphasize tier and interval over exact rank. |
| 9 | Charles XIV John | Tier A, robust elite | very_stable | 6-32 | 4-57 | 26.2 | moderate | Robust elite: exact rank is still not historical truth, but elite-band placement is strongly supported. |
| 10 | Ivan Paskevich | Tier B, elite but model-sensitive | stable | 2-199 | 1-384 | 197.0 | very_wide | High-ranking but confidence-limited: emphasize tier and interval over exact rank. |
| 11 | Louis XIV | Tier D, strong but narrow-category performer | stable | 5-60 | 4-110 | 55.1 | wide | High-ranking but confidence-limited: emphasize tier and interval over exact rank. |
| 12 | Henri de La Tour d'Auvergne, Viscount of Turenne | Tier A, robust elite | stable | 4-77 | 3-93 | 73.1 | wide | High-ranking but confidence-limited: emphasize tier and interval over exact rank. |
| 13 | Mehmed II | Tier D, strong but narrow-category performer | stable | 3-84 | 2-110 | 81.2 | wide | High-ranking but confidence-limited: emphasize tier and interval over exact rank. |
| 14 | Belisarius | Tier D, strong but narrow-category performer | stable | 4-76 | 3-118 | 72.0 | wide | High-ranking but confidence-limited: emphasize tier and interval over exact rank. |
| 15 | Louis-Gabriel Suchet | Tier A, robust elite | very_stable | 9-78 | 6-100 | 69.2 | wide | High-ranking but confidence-limited: emphasize tier and interval over exact rank. |
| 16 | André Masséna | Tier A, robust elite | stable | 6-63 | 5-79 | 57.1 | wide | High-ranking but confidence-limited: emphasize tier and interval over exact rank. |
| 17 | Alexander Farnese, Duke of Parma | Tier D, strong but narrow-category performer | very_stable | 13-57 | 11-68 | 44.1 | wide | High-ranking but confidence-limited: emphasize tier and interval over exact rank. |
| 18 | Khalid ibn al-Walid | Tier A, robust elite | very_stable | 7-31 | 6-33 | 24.0 | moderate | Robust elite: exact rank is still not historical truth, but elite-band placement is strongly supported. |
| 19 | Genghis Khan | Tier D, strong but narrow-category performer | moderately_stable | 3-106 | 2-162 | 103.3 | very_wide | High-ranking but confidence-limited: emphasize tier and interval over exact rank. |
| 20 | Hubert Gough | Tier A, robust elite | stable | 10-109 | 6-142 | 99.1 | wide | High-ranking but confidence-limited: emphasize tier and interval over exact rank. |
| 21 | Bernard Montgomery | Tier B, elite but model-sensitive | stable | 15-103 | 14-140 | 88.2 | wide | High-ranking but confidence-limited: emphasize tier and interval over exact rank. |
| 22 | Maharaja Ranjit Singh | Tier B, elite but model-sensitive | moderately_stable | 8-264 | 3-317 | 256.4 | very_wide | High-ranking but confidence-limited: emphasize tier and interval over exact rank. |
| 23 | Alexander the Great | Tier D, strong but narrow-category performer | stable | 16-140 | 8-174 | 124.2 | very_wide | High-ranking but confidence-limited: emphasize tier and interval over exact rank. |
| 24 | Winfield Scott | Tier B, elite but model-sensitive | moderately_stable | 6-222 | 3-274 | 216.0 | very_wide | High-ranking but confidence-limited: emphasize tier and interval over exact rank. |
| 25 | Hannibal | Tier A, robust elite | stable | 12-106 | 11-139 | 94.0 | wide | High-ranking but confidence-limited: emphasize tier and interval over exact rank. |

## Commanders Whose Exact Rank Is Stable

| headline_rank | commander_name | rank_interval_80 | rank_band_width_80 | confidence_category | tier |
| --- | --- | --- | --- | --- | --- |
| 1 | Alexander Suvorov | 1-9 | 8.0 | narrow | Tier A, robust elite |
| 6 | Jean Lannes | 4-13 | 9.0 | narrow | Tier A, robust elite |

## Commanders Whose Exact Rank Is Fragile

| headline_rank | commander_name | rank_interval_80 | rank_band_width_80 | confidence_category | tier | recommended_interpretation |
| --- | --- | --- | --- | --- | --- | --- |
| 95 | Date Masamune | 28-454 | 426.1 | very_wide | Tier D, strong but narrow-category performer | Wide uncertainty: use tier and sensitivity context rather than exact adjacent rank. |
| 87 | Carl Gustaf Wrangel | 37-456 | 419.1 | very_wide | Tier C, high performer with evidence caveats | Wide uncertainty: use tier and sensitivity context rather than exact adjacent rank. |
| 93 | Zubayr ibn al-Awwam | 30-442 | 411.8 | very_wide | Tier C, high performer with evidence caveats | Wide uncertainty: use tier and sensitivity context rather than exact adjacent rank. |
| 90 | Yamagata Aritomo | 25-412 | 386.5 | very_wide | Tier C, high performer with evidence caveats | Wide uncertainty: use tier and sensitivity context rather than exact adjacent rank. |
| 66 | Petar Bojović | 19-397 | 378.0 | very_wide | Tier C, high performer with evidence caveats | Wide uncertainty: use tier and sensitivity context rather than exact adjacent rank. |
| 91 | Ambrogio Spinola | 29-367 | 338.0 | very_wide | Tier D, strong but narrow-category performer | Wide uncertainty: use tier and sensitivity context rather than exact adjacent rank. |
| 81 | Bertrand du Guesclin | 37-368 | 330.6 | very_wide | Tier C, high performer with evidence caveats | Wide uncertainty: use tier and sensitivity context rather than exact adjacent rank. |
| 59 | Aleksandr Vasilevsky | 31-342 | 310.7 | very_wide | Tier C, high performer with evidence caveats | Wide uncertainty: use tier and sensitivity context rather than exact adjacent rank. |
| 71 | Živojin Mišić | 23-333 | 310.3 | very_wide | Tier C, high performer with evidence caveats | Wide uncertainty: use tier and sensitivity context rather than exact adjacent rank. |
| 96 | Lennart Torstensson | 53-363 | 310.2 | very_wide | Tier C, high performer with evidence caveats | Wide uncertainty: use tier and sensitivity context rather than exact adjacent rank. |
| 68 | Ahmad Shah Durrani | 31-339 | 308.2 | very_wide | Tier C, high performer with evidence caveats | Wide uncertainty: use tier and sensitivity context rather than exact adjacent rank. |
| 97 | Honda Tadakatsu | 36-343 | 307.0 | very_wide | Tier C, high performer with evidence caveats | Wide uncertainty: use tier and sensitivity context rather than exact adjacent rank. |
| 80 | Jassa Singh Ahluwalia | 26-329 | 303.3 | very_wide | Tier C, high performer with evidence caveats | Wide uncertainty: use tier and sensitivity context rather than exact adjacent rank. |
| 70 | Ernst Gideon von Laudon | 17-316 | 299.3 | very_wide | Tier C, high performer with evidence caveats | Wide uncertainty: use tier and sensitivity context rather than exact adjacent rank. |
| 65 | Sayenqueraghta | 33-325 | 292.4 | very_wide | Tier C, high performer with evidence caveats | Wide uncertainty: use tier and sensitivity context rather than exact adjacent rank. |
| 77 | Babur | 27-318 | 291.0 | very_wide | Tier D, strong but narrow-category performer | Wide uncertainty: use tier and sensitivity context rather than exact adjacent rank. |
| 49 | Tolui | 21-301 | 280.0 | very_wide | Tier D, strong but narrow-category performer | Wide uncertainty: use tier and sensitivity context rather than exact adjacent rank. |
| 85 | Ivan Bagramyan | 51-329 | 278.2 | very_wide | Tier C, high performer with evidence caveats | Wide uncertainty: use tier and sensitivity context rather than exact adjacent rank. |
| 63 | Philip the Good | 28-289 | 261.3 | very_wide | Tier D, strong but narrow-category performer | Wide uncertainty: use tier and sensitivity context rather than exact adjacent rank. |
| 52 | Ōyama Iwao | 19-278 | 259.1 | very_wide | Tier C, high performer with evidence caveats | Wide uncertainty: use tier and sensitivity context rather than exact adjacent rank. |

## Tier Stable Despite Rank Uncertainty

| headline_rank | commander_name | confidence_adjusted_tier | rank_interval_80 | confidence_category | confidence_adjusted_tier_reason |
| --- | --- | --- | --- | --- | --- |
| 1 | Alexander Suvorov | Tier A, confidence-supported robust elite | 1-9 | narrow | Elite placement remains supported under bootstrap uncertainty. |
| 2 | Maurice, Prince of Orange | Tier B, confidence-supported elite | 2-36 | wide | Upper-band placement is supported, but exact rank should be read as an interval. |
| 3 | Napoleon Bonaparte | Tier A, confidence-supported robust elite | 2-23 | moderate | Elite placement remains supported under bootstrap uncertainty. |
| 4 | Subutai | Tier B, confidence-supported elite | 3-62 | wide | Upper-band placement is supported, but exact rank should be read as an interval. |
| 5 | Sébastien Le Prestre, Marquis of Vauban | Tier B, confidence-supported elite | 3-32 | moderate | Upper-band placement is supported, but exact rank should be read as an interval. |
| 6 | Jean Lannes | Tier A, confidence-supported robust elite | 4-13 | narrow | Elite placement remains supported under bootstrap uncertainty. |
| 7 | Louis-Nicolas Davout | Tier B, confidence-supported elite | 3-33 | wide | Upper-band placement is supported, but exact rank should be read as an interval. |
| 8 | Douglas MacArthur | Tier B, confidence-supported elite | 4-72 | wide | Upper-band placement is supported, but exact rank should be read as an interval. |
| 9 | Charles XIV John | Tier A, confidence-supported robust elite | 6-32 | moderate | Elite placement remains supported under bootstrap uncertainty. |
| 11 | Louis XIV | Tier B, confidence-supported elite | 5-60 | wide | Upper-band placement is supported, but exact rank should be read as an interval. |
| 12 | Henri de La Tour d'Auvergne, Viscount of Turenne | Tier B, confidence-supported elite | 4-77 | wide | Upper-band placement is supported, but exact rank should be read as an interval. |
| 13 | Mehmed II | Tier B, confidence-supported elite | 3-84 | wide | Upper-band placement is supported, but exact rank should be read as an interval. |
| 14 | Belisarius | Tier B, confidence-supported elite | 4-76 | wide | Upper-band placement is supported, but exact rank should be read as an interval. |
| 15 | Louis-Gabriel Suchet | Tier B, confidence-supported elite | 9-78 | wide | Upper-band placement is supported, but exact rank should be read as an interval. |
| 16 | André Masséna | Tier B, confidence-supported elite | 6-63 | wide | Upper-band placement is supported, but exact rank should be read as an interval. |
| 17 | Alexander Farnese, Duke of Parma | Tier B, confidence-supported elite | 13-57 | wide | Upper-band placement is supported, but exact rank should be read as an interval. |
| 18 | Khalid ibn al-Walid | Tier A, confidence-supported robust elite | 7-31 | moderate | Elite placement remains supported under bootstrap uncertainty. |
| 20 | Hubert Gough | Tier B, confidence-supported elite | 10-109 | wide | Upper-band placement is supported, but exact rank should be read as an interval. |
| 21 | Bernard Montgomery | Tier B, confidence-supported elite | 15-103 | wide | Upper-band placement is supported, but exact rank should be read as an interval. |
| 25 | Hannibal | Tier B, confidence-supported elite | 12-106 | wide | Upper-band placement is supported, but exact rank should be read as an interval. |

## Tier Downgrades Or Caveats

| headline_rank | commander_name | confidence_adjusted_tier | rank_interval_80 | confidence_category | confidence_adjusted_tier_reason |
| --- | --- | --- | --- | --- | --- |
| 10 | Ivan Paskevich | Tier C, high-ranking but confidence-limited | 2-199 | very_wide | High rank has a wide bootstrap interval; emphasize tier over exact rank. |
| 19 | Genghis Khan | Tier C, high-ranking but confidence-limited | 3-106 | very_wide | High rank has a wide bootstrap interval; emphasize tier over exact rank. |
| 22 | Maharaja Ranjit Singh | Tier C, high-ranking but confidence-limited | 8-264 | very_wide | High rank has a wide bootstrap interval; emphasize tier over exact rank. |
| 23 | Alexander the Great | Tier C, high-ranking but confidence-limited | 16-140 | very_wide | High rank has a wide bootstrap interval; emphasize tier over exact rank. |
| 24 | Winfield Scott | Tier C, high-ranking but confidence-limited | 6-222 | very_wide | High rank has a wide bootstrap interval; emphasize tier over exact rank. |
| 26 | Enver Pasha | Tier C, high-ranking but confidence-limited | 11-188 | very_wide | High rank has a wide bootstrap interval; emphasize tier over exact rank. |
| 27 | Baybars | Tier C, high-ranking but confidence-limited | 22-240 | very_wide | High rank has a wide bootstrap interval; emphasize tier over exact rank. |
| 28 | Peng Dehuai | Tier C, high-ranking but confidence-limited | 14-242 | very_wide | High rank has a wide bootstrap interval; emphasize tier over exact rank. |
| 29 | Frederick the Great | Tier C, high-ranking but confidence-limited | 8-105 | wide | High rank has a wide bootstrap interval; emphasize tier over exact rank. |
| 30 | Heinz Guderian | Tier C, high-ranking but confidence-limited | 17-165 | very_wide | High rank has a wide bootstrap interval; emphasize tier over exact rank. |
| 31 | Charles-Pierre Augereau | Tier C, high-ranking but confidence-limited | 9-112 | very_wide | High rank has a wide bootstrap interval; emphasize tier over exact rank. |
| 33 | Hari Singh Nalwa | Tier C, high-ranking but confidence-limited | 11-257 | very_wide | High rank has a wide bootstrap interval; emphasize tier over exact rank. |
| 34 | Aurangzeb | Tier C, high-ranking but confidence-limited | 14-218 | very_wide | High rank has a wide bootstrap interval; emphasize tier over exact rank. |
| 35 | Ögedei Khan | Tier C, high-ranking but confidence-limited | 16-207 | very_wide | High rank has a wide bootstrap interval; emphasize tier over exact rank. |
| 36 | Dwight D. Eisenhower | Tier C, high-ranking but confidence-limited | 15-223 | very_wide | High rank has a wide bootstrap interval; emphasize tier over exact rank. |
| 37 | Katō Kiyomasa | Tier C, high-ranking but confidence-limited | 20-216 | very_wide | High rank has a wide bootstrap interval; emphasize tier over exact rank. |
| 38 | Tokugawa Ieyasu | Tier C, high-ranking but confidence-limited | 9-182 | very_wide | High rank has a wide bootstrap interval; emphasize tier over exact rank. |
| 39 | Georgy Zhukov | Tier C, high-ranking but confidence-limited | 16-113 | wide | High rank has a wide bootstrap interval; emphasize tier over exact rank. |
| 40 | Mikhail Kutuzov | Tier C, high-ranking but confidence-limited | 20-244 | very_wide | High rank has a wide bootstrap interval; emphasize tier over exact rank. |
| 41 | Stanisław Żółkiewski | Tier C, high-ranking but confidence-limited | 31-209 | very_wide | High rank has a wide bootstrap interval; emphasize tier over exact rank. |

## Non-Top-10 Commanders Frequently Appearing In Bootstrap Top 10

| original_rank | commander_name | rank_p10 | rank_p90 | top10_bootstrap_count | top10_bootstrap_rate |
| --- | --- | --- | --- | --- | --- |
| 18 | Khalid ibn al-Walid | 7.0 | 31.0 | 78 | 0.39 |
| 11 | Louis XIV | 5.0 | 60.1 | 68 | 0.34 |
| 13 | Mehmed II | 3.0 | 84.2 | 61 | 0.305 |
| 12 | Henri de La Tour d'Auvergne, Viscount of Turenne | 4.0 | 77.1 | 54 | 0.27 |
| 14 | Belisarius | 4.0 | 76.0 | 53 | 0.265 |
| 19 | Genghis Khan | 3.0 | 106.3 | 53 | 0.265 |
| 16 | André Masséna | 6.0 | 63.1 | 47 | 0.235 |
| 24 | Winfield Scott | 6.0 | 222.0 | 41 | 0.205 |
| 15 | Louis-Gabriel Suchet | 9.0 | 78.2 | 31 | 0.155 |
| 29 | Frederick the Great | 8.0 | 105.0 | 28 | 0.14 |
| 22 | Maharaja Ranjit Singh | 8.0 | 264.4 | 26 | 0.13 |
| 31 | Charles-Pierre Augereau | 9.0 | 112.2 | 25 | 0.125 |
| 20 | Hubert Gough | 9.9 | 109.0 | 23 | 0.115 |
| 38 | Tokugawa Ieyasu | 9.0 | 182.4 | 22 | 0.11 |
| 26 | Enver Pasha | 10.9 | 188.0 | 20 | 0.1 |
| 33 | Hari Singh Nalwa | 11.0 | 257.3 | 19 | 0.095 |
| 23 | Alexander the Great | 15.9 | 140.1 | 14 | 0.07 |
| 34 | Aurangzeb | 14.0 | 218.2 | 13 | 0.065 |
| 36 | Dwight D. Eisenhower | 15.0 | 223.0 | 12 | 0.06 |
| 70 | Ernst Gideon von Laudon | 17.0 | 316.3 | 12 | 0.06 |

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

- `Alexander Suvorov`: exact rank #1, 80% interval `1-9`, 90% interval `1-14`, confidence `narrow`. Robust elite: exact rank is still not historical truth, but elite-band placement is strongly supported.
- `Maurice, Prince of Orange`: exact rank #2, 80% interval `2-36`, 90% interval `1-46`, confidence `wide`. High-ranking but confidence-limited: emphasize tier and interval over exact rank.
- `Napoleon Bonaparte`: exact rank #3, 80% interval `2-23`, 90% interval `1-26`, confidence `moderate`. Robust elite: exact rank is still not historical truth, but elite-band placement is strongly supported.
- `Subutai`: exact rank #4, 80% interval `3-62`, 90% interval `2-89`, confidence `wide`. High-ranking but confidence-limited: emphasize tier and interval over exact rank.
- `Sébastien Le Prestre, Marquis of Vauban`: exact rank #5, 80% interval `3-32`, 90% interval `2-59`, confidence `moderate`. Rank band is reasonably constrained under current model assumptions.
- `Jean Lannes`: exact rank #6, 80% interval `4-13`, 90% interval `4-15`, confidence `narrow`. Robust elite: exact rank is still not historical truth, but elite-band placement is strongly supported.
- `Louis-Nicolas Davout`: exact rank #7, 80% interval `3-33`, 90% interval `3-58`, confidence `wide`. High-ranking but confidence-limited: emphasize tier and interval over exact rank.
- `Douglas MacArthur`: exact rank #8, 80% interval `4-72`, 90% interval `2-89`, confidence `wide`. High-ranking but confidence-limited: emphasize tier and interval over exact rank.
- `Charles XIV John`: exact rank #9, 80% interval `6-32`, 90% interval `4-57`, confidence `moderate`. Robust elite: exact rank is still not historical truth, but elite-band placement is strongly supported.
- `Ivan Paskevich`: exact rank #10, 80% interval `2-199`, 90% interval `1-384`, confidence `very_wide`. High-ranking but confidence-limited: emphasize tier and interval over exact rank.

## Final Interpretation Rule

After Pass 3, every headline placement should distinguish exact rank, confidence band, tier, model sensitivity, and evidence limitations. The ranking is now less brittle because it can say both where a commander ranks and how much precision that rank deserves.
