# Upgrade Pass 1 Review Report

Snapshot reviewed: `outputs_improved_2026-04-24_ranking_model_upgrade`

Status: review and diagnosis only. No ranking outputs were changed by this report.

## Executive Summary

Upgrade Pass 1 materially improves interpretability. The snapshot now explains high ranks with deterministic tiers, cross-model stability, page-type contribution shares, and high-rank audit flags. It still should not be treated as the final historical model because role attribution, bootstrap confidence bands, opponent/difficulty adjustments, and category-specific rankings remain future work.

## 1. Top 25 `hierarchical_trust_v2` Commanders

| Rank | Commander | Tier | Stability | Known rows | Engagement rows | Broad share | Battle/Siege share | Main audit flags | Interpretation note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Alexander Suvorov | Tier A, robust elite | very_stable | 18 | 20 | 0.0% | battle 100.0%; siege rows 10.0% | coalition_credit_heavy, split_credit_sensitive | robust; battle-heavy; exact rank should be read through tier and stability metadata. |
| 2 | Maurice, Prince of Orange | Tier D, strong but narrow-category performer | very_stable | 35 | 38 | 0.0% | battle 100.0%; siege rows 81.6% | siege_engineering_specialist | qualified; siege-heavy; exact rank should be read through tier and stability metadata. |
| 3 | Napoleon Bonaparte | Tier A, robust elite | very_stable | 60 | 67 | 0.0% | battle 100.0%; siege rows 6.0% | coalition_credit_heavy, split_credit_sensitive | robust; battle-heavy; exact rank should be read through tier and stability metadata. |
| 4 | Subutai | Tier A, robust elite | very_stable | 16 | 16 | 4.9% | battle 95.1%; siege rows 25.0% | coalition_credit_heavy, split_credit_sensitive | robust; battle-heavy; exact rank should be read through tier and stability metadata. |
| 5 | Sébastien Le Prestre, Marquis of Vauban | Tier D, strong but narrow-category performer | very_stable | 13 | 16 | 0.0% | battle 100.0%; siege rows 68.8% | siege_engineering_specialist, split_credit_sensitive | qualified; siege-heavy; exact rank should be read through tier and stability metadata. |
| 6 | Jean Lannes | Tier A, robust elite | very_stable | 27 | 28 | 1.4% | battle 98.6%; siege rows 7.1% | coalition_credit_heavy, split_credit_sensitive | robust; battle-heavy; exact rank should be read through tier and stability metadata. |
| 7 | Louis-Nicolas Davout | Tier A, robust elite | very_stable | 20 | 25 | 2.7% | battle 97.3%; siege rows 4.0% | coalition_credit_heavy, split_credit_sensitive | robust; battle-heavy; exact rank should be read through tier and stability metadata. |
| 8 | Douglas MacArthur | Tier A, robust elite | stable | 20 | 22 | 6.6% | battle 93.4%; siege rows 0.0% | large_model_rank_variance, coalition_credit_heavy, split_credit_sensitive | qualified; battle-heavy; exact rank should be read through tier and stability metadata. |
| 9 | Charles XIV John | Tier A, robust elite | very_stable | 16 | 21 | 3.3% | battle 96.7%; siege rows 4.8% | coalition_credit_heavy, split_credit_sensitive | robust; battle-heavy; exact rank should be read through tier and stability metadata. |
| 10 | Ivan Paskevich | Tier B, elite but model-sensitive | stable | 9 | 9 | 5.8% | battle 94.2%; siege rows 0.0% | large_model_rank_variance, coalition_credit_heavy, split_credit_sensitive | qualified; battle-heavy; exact rank should be read through tier and stability metadata. |
| 11 | Louis XIV | Tier D, strong but narrow-category performer | stable | 11 | 15 | 7.7% | battle 92.3%; siege rows 46.7% | siege_engineering_specialist, split_credit_sensitive | qualified; siege-heavy; exact rank should be read through tier and stability metadata. |
| 12 | Henri de La Tour d'Auvergne, Viscount of Turenne | Tier A, robust elite | stable | 15 | 20 | 0.0% | battle 100.0%; siege rows 25.0% | none | robust; battle-heavy; exact rank should be read through tier and stability metadata. |
| 13 | Mehmed II | Tier D, strong but narrow-category performer | stable | 21 | 23 | 1.8% | battle 98.2%; siege rows 52.2% | siege_engineering_specialist, split_credit_sensitive | qualified; siege-heavy; exact rank should be read through tier and stability metadata. |
| 14 | Belisarius | Tier D, strong but narrow-category performer | stable | 18 | 18 | 2.2% | battle 97.8%; siege rows 44.4% | coalition_credit_heavy, siege_engineering_specialist, split_credit_sensitive | qualified; siege-heavy; exact rank should be read through tier and stability metadata. |
| 15 | Louis-Gabriel Suchet | Tier A, robust elite | very_stable | 19 | 21 | 0.6% | battle 99.4%; siege rows 33.3% | split_credit_sensitive | robust; battle-heavy; exact rank should be read through tier and stability metadata. |
| 16 | André Masséna | Tier A, robust elite | stable | 37 | 43 | 0.8% | battle 99.2%; siege rows 14.0% | coalition_credit_heavy, split_credit_sensitive | robust; battle-heavy; exact rank should be read through tier and stability metadata. |
| 17 | Alexander Farnese, Duke of Parma | Tier D, strong but narrow-category performer | very_stable | 18 | 20 | 0.0% | battle 100.0%; siege rows 65.0% | siege_engineering_specialist | qualified; siege-heavy; exact rank should be read through tier and stability metadata. |
| 18 | Khalid ibn al-Walid | Tier A, robust elite | very_stable | 39 | 41 | 0.0% | battle 100.0%; siege rows 14.6% | split_credit_sensitive | robust; battle-heavy; exact rank should be read through tier and stability metadata. |
| 19 | Genghis Khan | Tier D, strong but narrow-category performer | moderately_stable | 15 | 15 | 4.4% | battle 95.6%; siege rows 46.7% | high_rank_low_battle_only_score, large_model_rank_variance, coalition_credit_heavy, siege_engineering_specialist + | qualified; siege-heavy; exact rank should be read through tier and stability metadata. |
| 20 | Hubert Gough | Tier A, robust elite | stable | 17 | 22 | 5.3% | battle 94.7%; siege rows 0.0% | large_model_rank_variance | qualified; battle-heavy; exact rank should be read through tier and stability metadata. |
| 21 | Bernard Montgomery | Tier B, elite but model-sensitive | stable | 12 | 19 | 48.9% | battle 51.1%; siege rows 5.3% | high_rank_many_high_level_pages, large_model_rank_variance, split_credit_sensitive | qualified; broad-page-sensitive; exact rank should be read through tier and stability metadata. |
| 22 | Maharaja Ranjit Singh | Tier B, elite but model-sensitive | moderately_stable | 9 | 11 | 12.4% | battle 87.6%; siege rows 9.1% | high_rank_low_battle_only_score, large_model_rank_variance, split_credit_sensitive | qualified; battle-heavy; exact rank should be read through tier and stability metadata. |
| 23 | Alexander the Great | Tier D, strong but narrow-category performer | stable | 11 | 18 | 1.1% | battle 98.9%; siege rows 38.9% | siege_engineering_specialist | qualified; siege-heavy; exact rank should be read through tier and stability metadata. |
| 24 | Winfield Scott | Tier B, elite but model-sensitive | moderately_stable | 8 | 12 | 2.6% | battle 97.4%; siege rows 8.3% | large_model_rank_variance, split_credit_sensitive | qualified; battle-heavy; exact rank should be read through tier and stability metadata. |
| 25 | Hannibal | Tier A, robust elite | stable | 18 | 27 | 2.5% | battle 97.5%; siege rows 11.1% | outcome_override_sensitive | robust; battle-heavy; exact rank should be read through tier and stability metadata. |

## 2. Top 20 Most Stable Commanders Across Models

| Rank | Commander | Stability | Score | Median rank | Rank stddev | Top-25 models |
| --- | --- | --- | --- | --- | --- | --- |
| 3 | Napoleon Bonaparte | very_stable | 99.0 | 3 | 1.4 | 6 |
| 1 | Alexander Suvorov | very_stable | 98.8 | 1 | 1.4 | 6 |
| 5 | Sébastien Le Prestre, Marquis of Vauban | very_stable | 98.0 | 7 | 2.4 | 6 |
| 2 | Maurice, Prince of Orange | very_stable | 95.6 | 5.5 | 3.9 | 6 |
| 7 | Louis-Nicolas Davout | very_stable | 92.2 | 8.5 | 5.5 | 6 |
| 6 | Jean Lannes | very_stable | 92.0 | 7.5 | 5.5 | 6 |
| 9 | Charles XIV John | very_stable | 90.4 | 12 | 2.6 | 6 |
| 4 | Subutai | very_stable | 89.8 | 4 | 9.2 | 5 |
| 15 | Louis-Gabriel Suchet | very_stable | 87.1 | 13.5 | 8.4 | 5 |
| 17 | Alexander Farnese, Duke of Parma | very_stable | 86.3 | 15.5 | 8.1 | 5 |
| 18 | Khalid ibn al-Walid | very_stable | 84.4 | 18 | 10.3 | 5 |
| 11 | Louis XIV | stable | 81.5 | 13.5 | 13.6 | 4 |
| 10 | Ivan Paskevich | stable | 80.8 | 8.5 | 23.0 | 4 |
| 12 | Henri de La Tour d'Auvergne, Viscount of Turenne | stable | 80.6 | 18.5 | 11.9 | 4 |
| 16 | André Masséna | stable | 80.0 | 25.5 | 8.5 | 3 |
| 27 | Baybars | stable | 79.6 | 25.5 | 12.5 | 3 |
| 13 | Mehmed II | stable | 78.5 | 21.5 | 13.7 | 3 |
| 14 | Belisarius | stable | 78.2 | 19 | 13.6 | 4 |
| 25 | Hannibal | stable | 77.1 | 26.5 | 12.9 | 3 |
| 41 | Stanisław Żółkiewski | stable | 77.1 | 25 | 11.3 | 3 |

## 3. Top 20 Most Model-Sensitive Commanders Across Models

These are ranked by cross-model rank standard deviation, not by historical importance.

| Trust rank | Commander | Stability | Best rank | Worst rank | Rank stddev | Rank IQR | Main flags |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 392 | Andrey Yeryomenko | model_sensitive | #392 | #2217 | 707.2 | 103.0 | none |
| 302 | James Somerville | model_sensitive | #264 | #1828 | 605.3 | 97.0 | none |
| 560 | Abu Ibrahim al-Hashimi al-Qurashi | model_sensitive | #560 | #2221 | 582.7 | 200.0 | none |
| 746 | Nobutake Kondō | model_sensitive | #746 | #2210 | 582.2 | 12.0 | none |
| 264 | Võ Nguyên Giáp | model_sensitive | #264 | #1844 | 580.3 | 99.0 | none |
| 511 | Trần Văn Trà | model_sensitive | #511 | #2120 | 574.3 | 180.0 | none |
| 619 | Abu Ayyub al-Masri | model_sensitive | #619 | #2235 | 568.9 | 193.0 | none |
| 941 | Najib ad-Dawlah | model_sensitive | #908 | #2329 | 549.1 | 129.0 | none |
| 909 | Mikhail Tukhachevsky | model_sensitive | #909 | #2336 | 535.1 | 231.0 | none |
| 903 | Hans-Valentin Hube | model_sensitive | #903 | #2333 | 532.6 | 232.0 | none |
| 678 | Hoàng Văn Thái | model_sensitive | #678 | #2062 | 531.6 | 153.0 | none |
| 981 | Thomas Gage | model_sensitive | #921 | #2306 | 529.2 | 240.0 | none |
| 226 | Saddam Hussein | model_sensitive | #226 | #1853 | 523.8 | 172.2 | none |
| 900 | Jean d'Estrées, Count of Estrées | model_sensitive | #900 | #2260 | 517.5 | 228.0 | none |
| 372 | Fu Zuoyi | model_sensitive | #372 | #1965 | 515.5 | 91.0 | none |
| 954 | Osman Digna | model_sensitive | #879 | #2262 | 514.8 | 272.0 | none |
| 794 | Wehib Pasha | model_sensitive | #762 | #2207 | 509.8 | 98.2 | none |
| 260 | Velupillai Prabhakaran | model_sensitive | #260 | #1819 | 508.6 | 109.2 | none |
| 1055 | Christian V of Denmark | model_sensitive | #1028 | #2344 | 504.0 | 258.0 | none |
| 681 | Sigismund, Holy Roman Emperor | model_sensitive | #663 | #2143 | 503.2 | 266.5 | none |

## 4. Top 20 High-Level Page Dependency Cases

Broad share includes operation, campaign, war/conflict, invasion, conquest, uprising/revolt, and broad-conflict-style page types where present. In this snapshot the concrete high-level page types are primarily operation, campaign, and war/conflict articles.

| Trust rank | Commander | Broad share | Battle share | Tier | Stability | Main flags |
| --- | --- | --- | --- | --- | --- | --- |
| 195 | Abu Mohammad al-Julani | 100.0% | 0.0% | Tier E, historically important but scoring-sensitive | model_sensitive | none |
| 216 | Hulusi Akar | 100.0% | 0.0% | Tier E, historically important but scoring-sensitive | model_sensitive | none |
| 292 | Lê Duẩn | 100.0% | 0.0% | Tier E, historically important but scoring-sensitive | model_sensitive | none |
| 354 | Ghiath Dalla | 100.0% | 0.0% | Unclassified | model_sensitive | none |
| 453 | Ashfaq Parvez Kayani | 100.0% | 0.0% | Unclassified | model_sensitive | none |
| 463 | Phạm Văn Đồng | 100.0% | 0.0% | Tier E, historically important but scoring-sensitive | model_sensitive | none |
| 559 | Đỗ Cao Trí | 100.0% | 0.0% | Tier E, historically important but scoring-sensitive | model_sensitive | none |
| 660 | Jonas Savimbi | 100.0% | 0.0% | Tier E, historically important but scoring-sensitive | model_sensitive | none |
| 827 | Leonid Brezhnev | 100.0% | 0.0% | Tier E, historically important but scoring-sensitive | model_sensitive | none |
| 892 | Mikhail Frunze | 100.0% | 0.0% | Tier E, historically important but scoring-sensitive | model_sensitive | none |
| 906 | Hakimullah Mehsud | 100.0% | 0.0% | Unclassified | model_sensitive | none |
| 931 | Hjalmar Siilasvuo | 100.0% | 0.0% | Unclassified | model_sensitive | none |
| 935 | Qianlong Emperor | 100.0% | 0.0% | Tier E, historically important but scoring-sensitive | model_sensitive | none |
| 978 | Italo Gariboldi | 100.0% | 0.0% | Unclassified | model_sensitive | none |
| 1001 | Lothar Rendulic | 100.0% | 0.0% | Tier E, historically important but scoring-sensitive | model_sensitive | none |
| 1034 | Maria Theresa | 100.0% | 0.0% | Tier E, historically important but scoring-sensitive | model_sensitive | none |
| 1058 | Gusztáv Jány | 100.0% | 0.0% | Unclassified | model_sensitive | none |
| 1063 | Karl-Adolf Hollidt | 100.0% | 0.0% | Unclassified | model_sensitive | none |
| 1039 | Kurt von Tippelskirch | 84.3% | 15.7% | Unclassified | model_sensitive | none |
| 1051 | Walter Weiß | 83.9% | 16.1% | Unclassified | model_sensitive | none |

## 5. Top 20 Largest Rank Movers Across Requested Models

Models compared: `hierarchical_trust_v2`, `hierarchical_weighted`, `baseline_conservative`, `battle_only_baseline`, `hierarchical_equal_split`, and `hierarchical_broader_eligibility`.

| Movement | Commander | Trust rank | Hierarchical | Baseline | Battle-only | Equal split | Broader eligibility | Main flags |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1825 | Andrey Yeryomenko | #392 | #464 | NA | #2217 | #529 | #426 | none |
| 1661 | Abu Ibrahim al-Hashimi al-Qurashi | #560 | #828 | NA | #2221 | #835 | #1028 | none |
| 1627 | Saddam Hussein | #226 | #493 | #687 | #1853 | #493 | #600 | none |
| 1616 | Abu Ayyub al-Masri | #619 | #862 | NA | #2235 | #888 | #1055 | none |
| 1609 | Trần Văn Trà | #511 | #723 | NA | #2120 | #736 | #903 | none |
| 1593 | Fu Zuoyi | #372 | #618 | #718 | #1965 | #663 | #721 | none |
| 1580 | Võ Nguyên Giáp | #264 | #410 | NA | #1844 | #446 | #509 | none |
| 1564 | James Somerville | #302 | #310 | NA | #1828 | #264 | #399 | none |
| 1559 | Velupillai Prabhakaran | #260 | #506 | #574 | #1819 | #487 | #610 | none |
| 1525 | Albert Kesselring | #443 | #814 | #592 | #1968 | #890 | #913 | none |
| 1510 | Max von Gallwitz | #461 | #856 | #535 | #1971 | #904 | #1015 | none |
| 1503 | Erich Ludendorff | #384 | #783 | #518 | #1887 | #791 | #904 | none |
| 1489 | Daulat Rao Sindhia | #684 | #943 | #651 | #2140 | #942 | #1192 | none |
| 1484 | Chiang Kai-shek | #188 | #408 | #635 | #1672 | #509 | #256 | none |
| 1484 | Cevat Çobanlı | #351 | #685 | #569 | #1835 | #713 | #689 | none |
| 1481 | Hitoshi Imamura | #479 | #813 | #657 | #1960 | #832 | #1006 | none |
| 1480 | Sigismund, Holy Roman Emperor | #681 | #892 | #663 | #2143 | #935 | #1022 | none |
| 1478 | Zamorin | #444 | #645 | #677 | #1922 | #568 | #841 | none |
| 1465 | Levin August von Bennigsen | #310 | #635 | #469 | #1775 | #722 | #825 | none |
| 1464 | Nobutake Kondō | #746 | #750 | NA | #2210 | #762 | #760 | none |

## 6. Focused Audit Notes For Current Top Ten

### Alexander Suvorov

- Rank and tier: `#1`, `Tier A, robust elite`, stability `very_stable` with score `98.8`.
- Why high: `hierarchical_trust_v2` rewards the commander's known-outcome record, scale/breadth, and cross-model support; this commander has `18` known-outcome rows across `20` strict engagement rows.
- Sensitivity: stable enough for tier interpretation; requested-model rank movement is `3` places, with rank stddev `1.4`.
- Page support: battle-supported: battle contribution 100.0%, broad contribution 0.0%, siege-row share 10.0%.
- Audit flags: coalition_credit_heavy, split_credit_sensitive.
- Treatment: `robust`. Read the exact rank through tier, stability, and audit flags rather than as a final historical verdict.
### Maurice, Prince of Orange

- Rank and tier: `#2`, `Tier D, strong but narrow-category performer`, stability `very_stable` with score `95.6`.
- Why high: `hierarchical_trust_v2` rewards the commander's known-outcome record, scale/breadth, and cross-model support; this commander has `35` known-outcome rows across `38` strict engagement rows.
- Sensitivity: stable enough for tier interpretation; requested-model rank movement is `12` places, with rank stddev `3.9`.
- Page support: siege-heavy within battle-page data: battle contribution 100.0%, siege-row share 81.6%, broad contribution 0.0%.
- Audit flags: siege_engineering_specialist.
- Treatment: `qualified`. Read the exact rank through tier, stability, and audit flags rather than as a final historical verdict.
### Napoleon Bonaparte

- Rank and tier: `#3`, `Tier A, robust elite`, stability `very_stable` with score `99.0`.
- Why high: `hierarchical_trust_v2` rewards the commander's known-outcome record, scale/breadth, and cross-model support; this commander has `60` known-outcome rows across `67` strict engagement rows.
- Sensitivity: stable enough for tier interpretation; requested-model rank movement is `4` places, with rank stddev `1.4`.
- Page support: battle-supported: battle contribution 100.0%, broad contribution 0.0%, siege-row share 6.0%.
- Audit flags: coalition_credit_heavy, split_credit_sensitive.
- Treatment: `robust`. Read the exact rank through tier, stability, and audit flags rather than as a final historical verdict.
### Subutai

- Rank and tier: `#4`, `Tier A, robust elite`, stability `very_stable` with score `89.8`.
- Why high: `hierarchical_trust_v2` rewards the commander's known-outcome record, scale/breadth, and cross-model support; this commander has `16` known-outcome rows across `16` strict engagement rows.
- Sensitivity: stable enough for tier interpretation; requested-model rank movement is `25` places, with rank stddev `9.2`.
- Page support: battle-supported: battle contribution 95.1%, broad contribution 4.9%, siege-row share 25.0%.
- Audit flags: coalition_credit_heavy, split_credit_sensitive.
- Treatment: `robust`. Read the exact rank through tier, stability, and audit flags rather than as a final historical verdict.
### Sébastien Le Prestre, Marquis of Vauban

- Rank and tier: `#5`, `Tier D, strong but narrow-category performer`, stability `very_stable` with score `98.0`.
- Why high: `hierarchical_trust_v2` rewards the commander's known-outcome record, scale/breadth, and cross-model support; this commander has `13` known-outcome rows across `16` strict engagement rows.
- Sensitivity: stable enough for tier interpretation; requested-model rank movement is `6` places, with rank stddev `2.4`.
- Page support: siege-heavy within battle-page data: battle contribution 100.0%, siege-row share 68.8%, broad contribution 0.0%.
- Audit flags: siege_engineering_specialist, split_credit_sensitive.
- Treatment: `qualified`. Read the exact rank through tier, stability, and audit flags rather than as a final historical verdict.
### Jean Lannes

- Rank and tier: `#6`, `Tier A, robust elite`, stability `very_stable` with score `92.0`.
- Why high: `hierarchical_trust_v2` rewards the commander's known-outcome record, scale/breadth, and cross-model support; this commander has `27` known-outcome rows across `28` strict engagement rows.
- Sensitivity: stable enough for tier interpretation; requested-model rank movement is `15` places, with rank stddev `5.5`.
- Page support: battle-supported: battle contribution 98.6%, broad contribution 1.4%, siege-row share 7.1%.
- Audit flags: coalition_credit_heavy, split_credit_sensitive.
- Treatment: `robust`. Read the exact rank through tier, stability, and audit flags rather than as a final historical verdict.
### Louis-Nicolas Davout

- Rank and tier: `#7`, `Tier A, robust elite`, stability `very_stable` with score `92.2`.
- Why high: `hierarchical_trust_v2` rewards the commander's known-outcome record, scale/breadth, and cross-model support; this commander has `20` known-outcome rows across `25` strict engagement rows.
- Sensitivity: stable enough for tier interpretation; requested-model rank movement is `14` places, with rank stddev `5.5`.
- Page support: battle-supported: battle contribution 97.3%, broad contribution 2.7%, siege-row share 4.0%.
- Audit flags: coalition_credit_heavy, split_credit_sensitive.
- Treatment: `robust`. Read the exact rank through tier, stability, and audit flags rather than as a final historical verdict.
### Douglas MacArthur

- Rank and tier: `#8`, `Tier A, robust elite`, stability `stable` with score `76.0`.
- Why high: `hierarchical_trust_v2` rewards the commander's known-outcome record, scale/breadth, and cross-model support; this commander has `20` known-outcome rows across `22` strict engagement rows.
- Sensitivity: model-sensitive; requested-model rank movement is `71` places, with rank stddev `24.6`.
- Page support: battle-supported: battle contribution 93.4%, broad contribution 6.6%, siege-row share 0.0%.
- Audit flags: large_model_rank_variance, coalition_credit_heavy, split_credit_sensitive.
- Treatment: `qualified`. Read the exact rank through tier, stability, and audit flags rather than as a final historical verdict.
### Charles XIV John

- Rank and tier: `#9`, `Tier A, robust elite`, stability `very_stable` with score `90.4`.
- Why high: `hierarchical_trust_v2` rewards the commander's known-outcome record, scale/breadth, and cross-model support; this commander has `16` known-outcome rows across `21` strict engagement rows.
- Sensitivity: stable enough for tier interpretation; requested-model rank movement is `7` places, with rank stddev `2.6`.
- Page support: battle-supported: battle contribution 96.7%, broad contribution 3.3%, siege-row share 4.8%.
- Audit flags: coalition_credit_heavy, split_credit_sensitive.
- Treatment: `robust`. Read the exact rank through tier, stability, and audit flags rather than as a final historical verdict.
### Ivan Paskevich

- Rank and tier: `#10`, `Tier B, elite but model-sensitive`, stability `stable` with score `80.8`.
- Why high: `hierarchical_trust_v2` rewards the commander's known-outcome record, scale/breadth, and cross-model support; this commander has `9` known-outcome rows across `9` strict engagement rows.
- Sensitivity: model-sensitive; requested-model rank movement is `58` places, with rank stddev `23.0`.
- Page support: battle-supported: battle contribution 94.2%, broad contribution 5.8%, siege-row share 0.0%.
- Audit flags: large_model_rank_variance, coalition_credit_heavy, split_credit_sensitive.
- Treatment: `qualified`. Read the exact rank through tier, stability, and audit flags rather than as a final historical verdict.

## 7. Verification Confirmations

Dashboard and data checks:

- Dashboard metadata snapshot: `outputs_improved_2026-04-24_ranking_model_upgrade`.
- Dashboard headline model: `hierarchical_trust_v2`.
- Dashboard commander count: `2541`; sensitivity CSV rows: `2541`.
- Dashboard first commander: `Alexander Suvorov`; trust CSV first commander: `Alexander Suvorov`.
- Dashboard generated-from includes upgrade files: `derived_scoring/commander_model_stability.csv, derived_scoring/commander_tiers.csv, derived_scoring/page_type_score_contributions.csv, audits/high_ranked_commander_flags.csv`.

Current documentation snapshot references:

| Document | Status |
| --- | --- |
| README.md | references improved snapshot |
| SCORING_FRAMEWORK.md | references improved snapshot |
| FINAL_SYSTEM_TRUST_ASSESSMENT.md | references improved snapshot |
| METHODOLOGICAL_LIMITATIONS.md | references improved snapshot |
| MODEL_SENSITIVE_CASES.md | references improved snapshot |
| UPGRADE_RELEASE_NOTES.md | references improved snapshot |
| dashboard/README.md | references improved snapshot |
| RANKING_DASHBOARD_TECHNICAL_NOTE.md | references improved snapshot |

Integrity and dashboard QA:

- Strict integrity audit status: `PASS`, failed checks `0`.
- Upgrade metadata checks: top-100 stability `True`, tiers `True`, page contributions `True`, audit rows `True`.
- Dashboard data matches ranking output: `True`.
- Diagnostic full-credit is not headline: `True`.
- Dashboard QA status: `True`.
- Dashboard QA console errors: `0`; page errors: `0`.
- Stale historical references: current docs check passes `True`; archived lineage/audit files with older references `21`.

## 8. Final Judgment

Interpretability judgment: the improved snapshot is clearly more interpretable than the previous one because high ranks are no longer presented as only rank/name/score. Each top commander now carries tier, stability, known evidence count, page-type dependency, and audit flags.

Robust elite core in the current top-25 reading: Alexander Suvorov, Napoleon Bonaparte, Subutai, Jean Lannes, Louis-Nicolas Davout, Charles XIV John, Henri de La Tour d'Auvergne, Viscount of Turenne, Louis-Gabriel Suchet, André Masséna, Khalid ibn al-Walid, Hannibal.

High-ranked commanders requiring caveats include: Maurice, Prince of Orange, Sébastien Le Prestre, Marquis of Vauban, Douglas MacArthur, Ivan Paskevich, Louis XIV, Mehmed II, Belisarius, Alexander Farnese, Duke of Parma, Genghis Khan, Hubert Gough, Bernard Montgomery, Maharaja Ranjit Singh, Alexander the Great, Winfield Scott. These caveats are mostly driven by siege/category concentration, coalition or split-credit sensitivity, model-rank variance, or high-level page dependency.

Next highest-priority model upgrades:

1. Add curated command-role classification so nominal, coalition, subordinate, siege-engineering, naval, staff, and field-command roles are not blended.
2. Add bootstrap rank confidence bands to quantify rank intervals instead of relying only on model spread.
3. Add high-level page capped and role-weighted sensitivity models before changing the headline model.
4. Add era/region source-density diagnostics and era-normalized rankings.
5. Add opponent-strength and battle-difficulty models only as documented sensitivity views until coverage is strong.
6. Add separate tactical, operational, siege-engineering, strategic, and institutional rankings before attempting a new overall composite.
