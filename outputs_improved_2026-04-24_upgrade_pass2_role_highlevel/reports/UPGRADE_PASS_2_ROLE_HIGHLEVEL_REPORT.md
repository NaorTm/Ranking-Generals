# Upgrade Pass 2 Commander Eligibility And High-Level Page Control Report

Snapshot reviewed: `outputs_improved_2026-04-24_upgrade_pass2_role_highlevel`

Status: sensitivity and audit pass only. `hierarchical_trust_v2` remains the headline model and is not replaced here.

## Summary

- Ranked commanders reviewed: `1067`
- Top-100 commanders with broad-page share above 40%: `12`
- Ranked commanders with 100% broad-page dependency: `18`
- High-ranked commanders with weak battle/siege support: `2`
- Recommended headline exclusions from this pass: `7`
- New sensitivity outputs: `RANKING_RESULTS_HIERARCHICAL_TRUST_V2_HIGH_LEVEL_CAPPED.csv`, `RANKING_RESULTS_HIERARCHICAL_TRUST_V2_ELIGIBILITY_FILTERED.csv`, `RANKING_RESULTS_PASS2_SENSITIVITY.csv`

## Method

Broad-page contribution is computed from `derived_scoring/page_type_score_contributions.csv`. Broad pages include operation, campaign, war/conflict, invasion, conquest, uprising/revolt, and broad-conflict style page types where present. Siege support is estimated from strict engagement titles containing `siege` because most siege events are currently encoded as `battle_article`.

The high-level capped model is a sensitivity view. It caps broad-page dominance at 40% by reducing score contribution when high-level pages dominate the existing trust-v2 score. Cases with 100% broad-page contribution receive zero capped score until battle/siege or verified operational evidence is added.

## Top 100 Commanders With Broad-Page Share Above 40%

| rank_hierarchical_trust_v2 | commander_name | tier | stability_category | known_outcome_count | engagement_count | broad_page_contribution_share | battle_siege_page_contribution_share | strict_eligibility | recommended_action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 21 | Bernard Montgomery | Tier B, elite but model-sensitive | stable | 12 | 19 | 48.9% | 51.1% | eligible_field_commander | add_high_level_page_caveat |
| 36 | Dwight D. Eisenhower | Tier C, high performer with evidence caveats | model_sensitive | 9 | 13 | 54.2% | 45.8% | eligible_field_commander | add_high_level_page_caveat |
| 43 | Fyodor Tolbukhin | Tier B, elite but model-sensitive | moderately_stable | 11 | 13 | 54.7% | 45.3% | eligible_field_commander | add_high_level_page_caveat |
| 44 | Nikolai Vatutin | Tier B, elite but model-sensitive | moderately_stable | 12 | 13 | 47.2% | 52.8% | eligible_field_commander | add_high_level_page_caveat |
| 45 | Rodion Malinovsky | Tier C, high performer with evidence caveats | model_sensitive | 13 | 16 | 56.2% | 43.8% | eligible_field_commander | add_high_level_page_caveat |
| 47 | Konstantin Rokossovsky | Tier C, high performer with evidence caveats | model_sensitive | 17 | 17 | 46.1% | 53.9% | eligible_field_commander | add_high_level_page_caveat |
| 50 | Fedor von Bock | Tier B, elite but model-sensitive | stable | 13 | 18 | 43.7% | 56.3% | eligible_field_commander | add_high_level_page_caveat |
| 59 | Aleksandr Vasilevsky | Tier C, high performer with evidence caveats | model_sensitive | 9 | 9 | 56.4% | 43.6% | ambiguous_requires_review | add_high_level_page_caveat |
| 67 | George S. Patton | Tier C, high performer with evidence caveats | model_sensitive | 10 | 11 | 48.8% | 51.2% | eligible_field_commander | add_high_level_page_caveat |
| 72 | Kirill Meretskov | Tier C, high performer with evidence caveats | model_sensitive | 10 | 13 | 50.9% | 49.1% | ambiguous_requires_review | add_high_level_page_caveat |
| 82 | Joseph Stalin | Tier C, high performer with evidence caveats | model_sensitive | 10 | 17 | 48.2% | 51.8% | eligible_field_commander | add_high_level_page_caveat |
| 85 | Ivan Bagramyan | Tier C, high performer with evidence caveats | model_sensitive | 10 | 11 | 71.3% | 28.7% | eligible_operational_commander | add_high_level_page_caveat |

## All Ranked Commanders With 100% Broad-Page Dependency

| rank_hierarchical_trust_v2 | commander_name | known_outcome_count | engagement_count | broad_page_contribution_share | battle_siege_page_contribution_share | provisional_role_category | strict_eligibility | exclude_from_headline_ranking | recommended_action | rationale |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 195 | Abu Mohammad al-Julani | 5 | 19 | 100.0% | 0.0% | ambiguous_or_hybrid_political_military_leader | ambiguous_requires_review | False | role_review_before_headline_use | Hybrid insurgent/political-military leader with no battle/siege contribution in this snapshot; keep only as caveated operational sensitivity until role evidence is curated. |
| 216 | Hulusi Akar | 5 | 13 | 100.0% | 0.0% | modern_officeholder_or_staff_leader | staff_or_planning_only | True | exclude_from_headline_ranking | Modern chief/minister profile represented only through high-level pages; not enough field-command evidence for headline ranking. |
| 292 | Lê Duẩn | 4 | 12 | 100.0% | 0.0% | political_leader | political_or_nominal_only | True | exclude_from_headline_ranking | Political leadership case with 100% broad-page dependency; exclude from headline commander ranking unless direct command evidence is added. |
| 354 | Ghiath Dalla | 3 | 8 | 100.0% | 0.0% | modern_operational_commander_uncurated | ambiguous_requires_review | False | role_review_before_headline_use | Modern commander represented only by operation pages; requires role verification before headline use. |
| 453 | Ashfaq Parvez Kayani | 4 | 8 | 100.0% | 0.0% | modern_officeholder_or_staff_leader | staff_or_planning_only | True | exclude_from_headline_ranking | Army-chief/staff-office profile with no battle/siege support in this snapshot; exclude from headline ranking unless field command is verified. |
| 463 | Phạm Văn Đồng | 3 | 7 | 100.0% | 0.0% | political_leader | political_or_nominal_only | True | exclude_from_headline_ranking | Political leadership case with 100% broad-page dependency; exclude from headline commander ranking. |
| 559 | Đỗ Cao Trí | 4 | 8 | 100.0% | 0.0% | genuine_military_commander_operational | eligible_operational_commander | False | role_review_before_headline_use | Military commander profile, but current support is entirely high-level; keep as operational sensitivity with caveat. |
| 660 | Jonas Savimbi | 3 | 6 | 100.0% | 0.0% | ambiguous_or_hybrid_political_military_leader | ambiguous_requires_review | False | role_review_before_headline_use | Political-military insurgent leader represented only by broad pages; requires role and event-level verification. |
| 827 | Leonid Brezhnev | 3 | 5 | 100.0% | 0.0% | political_leader | political_or_nominal_only | True | exclude_from_headline_ranking | Political head-of-state profile with no battle/siege command support; exclude from headline ranking. |
| 892 | Mikhail Frunze | 4 | 7 | 100.0% | 0.0% | genuine_military_commander_and_theorist | eligible_operational_commander | False | role_review_before_headline_use | Military commander/theorist profile, but this snapshot supports him only through high-level pages; keep as caveated operational sensitivity. |
| 906 | Hakimullah Mehsud | 3 | 5 | 100.0% | 0.0% | ambiguous_or_hybrid_political_military_leader | ambiguous_requires_review | False | role_review_before_headline_use | Militant leader represented only by operation pages; requires command-role verification. |
| 931 | Hjalmar Siilasvuo | 3 | 5 | 100.0% | 0.0% | genuine_military_commander_operational | eligible_operational_commander | False | role_review_before_headline_use | Genuine military commander, but current score is operation/war-page only; keep as caveated operational sensitivity. |
| 935 | Qianlong Emperor | 3 | 5 | 100.0% | 0.0% | monarch_or_political_leader | political_or_nominal_only | True | exclude_from_headline_ranking | Monarch profile with 100% broad-page dependency; exclude from headline ranking unless direct field command is verified. |
| 978 | Italo Gariboldi | 5 | 7 | 100.0% | 0.0% | genuine_military_commander_operational | eligible_operational_commander | False | role_review_before_headline_use | Military commander profile, but current evidence is high-level only; keep as caveated operational sensitivity. |
| 1001 | Lothar Rendulic | 7 | 9 | 100.0% | 0.0% | genuine_military_commander_operational | eligible_operational_commander | False | role_review_before_headline_use | Military commander profile, but current contribution is entirely high-level; keep as caveated operational sensitivity. |
| 1034 | Maria Theresa | 4 | 5 | 100.0% | 0.0% | monarch_or_political_leader | political_or_nominal_only | True | exclude_from_headline_ranking | Political/monarchical leadership case with no battle/siege command support; exclude from headline ranking. |
| 1058 | Gusztáv Jány | 4 | 6 | 100.0% | 0.0% | genuine_military_commander_operational | eligible_operational_commander | False | role_review_before_headline_use | Military commander profile, but current support is high-level only; keep as caveated operational sensitivity. |
| 1063 | Karl-Adolf Hollidt | 4 | 5 | 100.0% | 0.0% | genuine_military_commander_operational | eligible_operational_commander | False | role_review_before_headline_use | Military commander profile, but current support is operation-page only; keep as caveated operational sensitivity. |

## High-Ranked Commanders With Weak Battle/Siege Support

High-ranked here means current trust-v2 rank 150 or better. Weak battle/siege support means less than 35% battle/siege contribution.

| rank_hierarchical_trust_v2 | commander_name | known_outcome_count | engagement_count | broad_page_contribution_share | battle_siege_page_contribution_share | strict_eligibility | recommended_action | rationale |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 85 | Ivan Bagramyan | 10 | 11 | 71.3% | 28.7% | eligible_operational_commander | add_high_level_page_caveat | Mostly high-level operational evidence; keep only as caveated sensitivity until event-level support improves. |
| 125 | Suhayl al-Hasan | 9 | 26 | 81.3% | 18.7% | eligible_operational_commander | add_high_level_page_caveat | Mostly high-level operational evidence; keep only as caveated sensitivity until event-level support improves. |

## Largest Drops Under High-Level Page Cap

Positive movement means the commander drops after the high-level page cap is applied.

| rank | rank_high_level_capped | rank_change_vs_hierarchical_trust_v2 | commander_name | broad_page_contribution_share | strict_eligibility | recommended_action |
| --- | --- | --- | --- | --- | --- | --- |
| 125 | 996 | 871 | Suhayl al-Hasan | 81.3% | eligible_operational_commander | add_high_level_page_caveat |
| 195 | 1050 | 855 | Abu Mohammad al-Julani | 100.0% | ambiguous_requires_review | role_review_before_headline_use |
| 216 | 1051 | 835 | Hulusi Akar | 100.0% | staff_or_planning_only | exclude_from_headline_ranking |
| 243 | 1012 | 769 | Ivan Chernyakhovsky | 80.8% | eligible_operational_commander | add_high_level_page_caveat |
| 292 | 1052 | 760 | Lê Duẩn | 100.0% | political_or_nominal_only | exclude_from_headline_ranking |
| 85 | 789 | 704 | Ivan Bagramyan | 71.3% | eligible_operational_commander | add_high_level_page_caveat |
| 354 | 1053 | 699 | Ghiath Dalla | 100.0% | ambiguous_requires_review | role_review_before_headline_use |
| 279 | 962 | 683 | Marc Mitscher | 74.7% | eligible_operational_commander | add_high_level_page_caveat |
| 302 | 914 | 612 | James Somerville | 69.9% | ambiguous_requires_review | add_high_level_page_caveat |
| 453 | 1054 | 601 | Ashfaq Parvez Kayani | 100.0% | staff_or_planning_only | exclude_from_headline_ranking |
| 463 | 1055 | 592 | Phạm Văn Đồng | 100.0% | political_or_nominal_only | exclude_from_headline_ranking |
| 559 | 1056 | 497 | Đỗ Cao Trí | 100.0% | eligible_operational_commander | role_review_before_headline_use |
| 516 | 994 | 478 | Georg-Hans Reinhardt | 72.3% | eligible_operational_commander | add_high_level_page_caveat |
| 511 | 936 | 425 | Trần Văn Trà | 66.4% | ambiguous_requires_review | add_high_level_page_caveat |
| 534 | 952 | 418 | Valerian Frolov | 67.0% | ambiguous_requires_review | add_high_level_page_caveat |
| 660 | 1057 | 397 | Jonas Savimbi | 100.0% | ambiguous_requires_review | role_review_before_headline_use |
| 505 | 900 | 395 | Abu Bakr al-Baghdadi | 63.1% | eligible_field_commander | add_high_level_page_caveat |
| 373 | 758 | 385 | Miles Dempsey | 59.0% | ambiguous_requires_review | add_high_level_page_caveat |
| 392 | 764 | 372 | Andrey Yeryomenko | 58.3% | ambiguous_requires_review | add_high_level_page_caveat |
| 617 | 979 | 362 | Harry Crerar | 67.6% | ambiguous_requires_review | add_high_level_page_caveat |
| 383 | 714 | 331 | Erich von Manstein | 56.5% | eligible_field_commander | add_high_level_page_caveat |
| 410 | 717 | 307 | Adolf Hitler | 55.5% | ambiguous_requires_review | add_high_level_page_caveat |
| 730 | 1024 | 294 | Noor Wali Mehsud | 71.6% | eligible_operational_commander | add_high_level_page_caveat |
| 738 | 1021 | 283 | Dmitry Lelyushenko | 71.0% | eligible_operational_commander | add_high_level_page_caveat |
| 156 | 435 | 279 | Asif Ali Zardari | 55.8% | ambiguous_requires_review | add_high_level_page_caveat |

## Recommended Actions

- Exclude political or nominal-only leaders from headline ranking unless direct field, naval, siege, or verified operational command evidence is added.
- Keep genuine military commanders with high-level-only support only in operational sensitivity views until role and event-level evidence is curated.
- Add caveats to any top-100 commander whose broad-page share exceeds 40%.
- Do not promote the capped or eligibility-filtered outputs to headline status until role classification is manually reviewed.
