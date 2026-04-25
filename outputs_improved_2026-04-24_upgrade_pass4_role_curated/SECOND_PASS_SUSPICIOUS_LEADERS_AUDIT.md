# Second Pass Suspicious Leaders Audit

## Scope

This audit starts from `outputs_cleaned_2026-04-10_secondpass_authoritative` and focuses on the leaders that still looked historically questionable after the first rank-fix pass.

The primary questions were:

- Are `Qasem Soleimani` and `Nelson A. Miles` still ranking high because of a residual bug?
- Are any other hierarchical top names still suspicious enough to require special caution?
- Are the remaining high ranks explainable, acceptable, or still likely inflated?


## Qasem Soleimani

Verdict: **questionable but now bounded caution case**

Why this commander still ranks where he does:

His remaining rank is not being driven by residual anti/coaltition bugs. It is driven by a small but very positive known-outcome set, very strong scope exposure (six battles, three operations, two campaigns, two wars), and still-meaningful higher-level exposure. The second pass neutralized the worst inflation by switching temporal scoring to non-war span (16 years used in-model instead of the 99-year war-page span) and by adding an evidence component, which pushed him from #4 to #13 in hierarchical_weighted. He remains caution-worthy because modern proxy-war pages still give him broad exposure with sparse explicit defeat coverage.

Model rank shift from the previous snapshot:

| model | old_rank | new_rank | rank_change |
| --- | --- | --- | --- |
| baseline_conservative |  |  |  |
| battle_only_baseline | 265 | 277 | -12 |
| hierarchical_weighted | 4 | 13 | -9 |
| hierarchical_full_credit | 4 | 12 | -8 |
| hierarchical_equal_split | 8 | 36 | -28 |
| hierarchical_broader_eligibility | 4 | 14 | -10 |

Current driver summary:

| rank_hierarchical | score_hierarchical | interpretive_group | caution_flags | strict_engagements | battle_pages | operation_pages | campaign_pages | war_pages | known_outcomes | known_outcome_share | first_year | last_year | active_span_years | nonwar_span_used_for_model | higher_level_share | component_outcome | component_scope | component_temporal | component_centrality | component_higher_level | component_evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 13 | 84.27 | caution_likely_artifact |  | 13 | 6 | 3 | 2 | 2 | 4 | 0.308 | 1918 | 2017 | 99 | 16 | 0.412 | 90.2 | 97.4 | 66.7 | 83.6 | 94.5 | 4 |

Current counted engagement rows:

| battle_name | page_type | analytic_year | result_raw | outcome_category | outcome_inference_method | same_side_commander_count | known_outcome_flag |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Iranian–Kurdish conflict | war_conflict_article | 1918 |  | unknown | unknown | 14 | 0 |
| Iran–Saudi Arabia proxy war | war_conflict_article | 1979 | The rivalry has drawn comparisons to the dynamics of the Cold War era. | unknown | unknown | 36 | 0 |
| 2001 uprising in Herat | battle_article | 2001 | Northern Alliance victory | victory | inferred_unique_belligerent_match | 7 | 1 |
| Iran–PJAK conflict | war_conflict_article | 2004 | Victory | unknown | unknown | 29 | 0 |
| Battle of Aleppo (2012–2016) | battle_article | 2012 | Victory | unknown | unknown | 11 | 0 |
| Battle of Baiji (2014–2015) | battle_article | 2014 | Victory | unknown | unknown | 5 | 0 |
| Siege of Amirli | battle_article | 2014 | Iraqi and allied victory | victory | inferred_unique_belligerent_match | 4 | 1 |
| Second Battle of Tikrit | battle_article | 2015 | Victory | unknown | unknown | 6 | 0 |
| Siege of Fallujah (2016) | battle_article | 2016 |  | unknown | unknown | 3 | 0 |
| 2017 Abu Kamal offensive | operation_article | 2017 | Decisive Syrian Army and allies victory | decisive_victory | inferred_unique_belligerent_match | 3 | 1 |
| Eastern Syria campaign | campaign_article | 2017 | Decisive Syrian Army and allies victory ISIL militants maintain presence in the desert | decisive_victory | inferred_unique_belligerent_match | 5 | 1 |
| Hama offensive (March–April 2017) | operation_article | 2017 |  | unknown | unknown | 3 | 0 |
| Qalamoun offensive (2017) | operation_article | 2017 | Victory | unknown | unknown | 6 | 0 |
| Syrian Desert campaign (May–July 2017) | campaign_article | 2017 |  | unknown | unknown | 2 | 0 |

No unresolved coalition/allied rows remain for this commander.



## Nelson A. Miles

Verdict: **still inflated enough to remain a caution case**

Why this commander still ranks where he does:

His rank is not a parsing bug. It is a war/campaign-heavy profile built from repeated United States victory pages: three battles, two campaigns, six wars, and six known outcomes out of eleven strict engagements. The second pass reduced his rank from #9 to #16 by weakening higher-level reward and by making evidence coverage matter more, but his dossier is still thinner at the battle layer than a top-20 all-history placement would normally warrant.

Model rank shift from the previous snapshot:

| model | old_rank | new_rank | rank_change |
| --- | --- | --- | --- |
| baseline_conservative |  |  |  |
| battle_only_baseline | 858 | 876 | -18 |
| hierarchical_weighted | 9 | 16 | -7 |
| hierarchical_full_credit | 13 | 17 | -4 |
| hierarchical_equal_split | 6 | 7 | -1 |
| hierarchical_broader_eligibility | 11 | 21 | -10 |

Current driver summary:

| rank_hierarchical | score_hierarchical | interpretive_group | caution_flags | strict_engagements | battle_pages | operation_pages | campaign_pages | war_pages | known_outcomes | known_outcome_share | first_year | last_year | active_span_years | nonwar_span_used_for_model | higher_level_share | component_outcome | component_scope | component_temporal | component_centrality | component_higher_level | component_evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 16 | 83.79 | caution_likely_artifact | higher_level_dependent | 11 | 3 | 0 | 2 | 6 | 6 | 0.545 | 1849 | 1906 | 57 | 33 | 0.516 | 99.1 | 69.7 | 92.1 | 54.1 | 90.1 | 15.2 |

Current counted engagement rows:

| battle_name | page_type | analytic_year | result_raw | outcome_category | outcome_inference_method | same_side_commander_count | known_outcome_flag |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Apache Wars | war_conflict_article | 1849 | United States victory | victory | inferred_unique_belligerent_match | 17 | 1 |
| Sioux Wars | war_conflict_article | 1854 | United States victory, Sioux moved to reservations. | unknown | unknown | 7 | 0 |
| Battle of Sutherland's Station | battle_article | 1865 | Union victory | unknown | unknown | 1 | 0 |
| Great Sioux War of 1876 | war_conflict_article | 1876 | United States victory | victory | inferred_unique_belligerent_match | 7 | 1 |
| Battle of Bear Paw | battle_article | 1877 | United States decisive victory | decisive_victory | inferred_unique_belligerent_match | 1 | 1 |
| Battle of Little Muddy Creek | battle_article | 1877 | American victory | unknown | unknown | 1 | 0 |
| Nez Perce War | war_conflict_article | 1877 | United States victory | victory | explicit_commander_side_result | 4 | 1 |
| Geronimo Campaign | campaign_article | 1885 | Decisive United States victory | decisive_victory | explicit_commander_side_result | 2 | 1 |
| Ghost Dance War | war_conflict_article | 1890 | United States victory | victory | explicit_commander_side_result | 3 | 1 |
| Puerto Rico campaign | campaign_article | 1898 | Victory | unknown | unknown | 2 | 0 |
| Spanish–American War | war_conflict_article | 1906 | Victory | unknown | unknown | 19 | 0 |

No unresolved coalition/allied rows remain for this commander.



## Flavius Aetius

Verdict: **plausible but low-confidence high placement**

Why this commander still ranks where he does:

He remains high because his late Roman dossier is compact, outcome-positive, and spans six battle pages plus six war pages. This is not a residual coalition bug case. The caution comes from sparse ancient coverage and the fact that higher-level Roman war pages still amplify scope and centrality. His rank is plausible but lower-confidence than the leading robust elite.

Model rank shift from the previous snapshot:

| model | old_rank | new_rank | rank_change |
| --- | --- | --- | --- |
| baseline_conservative | 167 | 169 | -2 |
| battle_only_baseline | 116 | 113 | +3 |
| hierarchical_weighted | 15 | 10 | +5 |
| hierarchical_full_credit | 18 | 9 | +9 |
| hierarchical_equal_split | 9 | 5 | +4 |
| hierarchical_broader_eligibility | 17 | 10 | +7 |

Current driver summary:

| rank_hierarchical | score_hierarchical | interpretive_group | caution_flags | strict_engagements | battle_pages | operation_pages | campaign_pages | war_pages | known_outcomes | known_outcome_share | first_year | last_year | active_span_years | nonwar_span_used_for_model | higher_level_share | component_outcome | component_scope | component_temporal | component_centrality | component_higher_level | component_evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 10 | 85.53 | caution_likely_artifact |  | 13 | 6 | 0 | 1 | 6 | 9 | 0.692 | 425 | 451 | 26 | 26 | 0.306 | 98.6 | 67.8 | 85.1 | 76.1 | 86.3 | 50.9 |

Current counted engagement rows:

| battle_name | page_type | analytic_year | result_raw | outcome_category | outcome_inference_method | same_side_commander_count | known_outcome_flag |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Frankish War (428) | war_conflict_article | 425 | Roman victory | victory | inferred_unique_belligerent_match | 2 | 1 |
| Roman civil war of 425 | war_conflict_article | 425 | Eastern Roman victory Flavius Aetius becomes the Magister militum per Gallias | unknown | unknown | 3 | 0 |
| Siege of Arles (425) | battle_article | 425 | Roman-Hunnic victory | victory | inferred_unique_belligerent_match | 1 | 1 |
| Aetius campaign in the Alps | campaign_article | 431 | Roman victory | victory | inferred_unique_belligerent_match | 3 | 1 |
| Frankish War (431–432) | war_conflict_article | 431 | Roman victory | victory | inferred_unique_belligerent_match | 1 | 1 |
| Battle of Rimini (432) | battle_article | 432 | Bonifacius victorious, but mortally wounded | unknown | unknown | 1 | 0 |
| Roman civil war of 432 | war_conflict_article | 432 | Aetian victory | unknown | unknown | 1 | 0 |
| Battle of Arles (435) | battle_article | 435 | Roman-Hunnic victory | victory | inferred_unique_belligerent_match | 2 | 1 |
| Gothic War (436–439) | war_conflict_article | 436 | Roman victory | victory | inferred_unique_belligerent_match | 3 | 1 |
| Battle of Narbonne (436) | battle_article | 437 | Roman victory | victory | inferred_unique_belligerent_match | 2 | 1 |
| Vandal War (439–442) | war_conflict_article | 442 | Indecisive Treaty of 442 | indecisive | explicit_commander_side_result | 2 | 1 |
| Battle of Vicus Helena | battle_article | 445 | Roman victory | victory | inferred_unique_belligerent_match | 2 | 1 |
| Battle of the Catalaunian Plains | battle_article | 451 |  | unknown | unknown | 5 | 0 |

No unresolved coalition/allied rows remain for this commander.



## Charles XIV John

Verdict: **acceptable hierarchical leader with bounded coalition ambiguity**

Why this commander still ranks where he does:

He is no longer being treated as a suspicious artifact. He has a broad dossier with sixteen battle pages, three campaigns, eight wars, and seventeen known outcomes. He does still carry two unresolved coalition battle pages (`Battle of Dennewitz` and `Battle of Großbeeren`), so his exact slot remains somewhat sensitive, but the overall profile is substantially richer than the first-pass caution cases.

Model rank shift from the previous snapshot:

| model | old_rank | new_rank | rank_change |
| --- | --- | --- | --- |
| baseline_conservative | 81 | 65 | +16 |
| battle_only_baseline | 71 | 67 | +4 |
| hierarchical_weighted | 22 | 9 | +13 |
| hierarchical_full_credit | 14 | 6 | +8 |
| hierarchical_equal_split | 31 | 10 | +21 |
| hierarchical_broader_eligibility | 25 | 8 | +17 |

Current driver summary:

| rank_hierarchical | score_hierarchical | interpretive_group | caution_flags | strict_engagements | battle_pages | operation_pages | campaign_pages | war_pages | known_outcomes | known_outcome_share | first_year | last_year | active_span_years | nonwar_span_used_for_model | higher_level_share | component_outcome | component_scope | component_temporal | component_centrality | component_higher_level | component_evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 9 | 85.72 | strong_but_model_sensitive |  | 27 | 16 | 0 | 3 | 8 | 17 | 0.630 | 1796 | 1814 | 18 | 18 | 0.196 | 97.2 | 73.1 | 70.8 | 97 | 93.4 | 35.7 |

Current counted engagement rows:

| battle_name | page_type | analytic_year | result_raw | outcome_category | outcome_inference_method | same_side_commander_count | known_outcome_flag |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Battle of Theiningen | battle_article | 1796 |  | unknown | unknown | 1 | 0 |
| Battle of Valvasone | battle_article | 1797 | French victory | victory | inferred_unique_belligerent_match | 6 | 1 |
| English Wars (Scandinavia) | war_conflict_article | 1801 | Victory | unknown | ambiguous_multi_side_commander | 0 | 0 |
| Napoleonic Wars | war_conflict_article | 1803 | Coalition victory | victory | inferred_unique_belligerent_match | 12 | 1 |
| Battle of Austerlitz | battle_article | 1805 | French victory | victory | inferred_unique_belligerent_match | 11 | 1 |
| Ulm campaign | campaign_article | 1805 | French victory | victory | inferred_unique_belligerent_match | 12 | 1 |
| War of the Third Coalition | war_conflict_article | 1805 | French victory | victory | inferred_unique_belligerent_match | 19 | 1 |
| Battle of Halle | battle_article | 1806 | French victoryBodart 1908 | unknown | unknown | 1 | 0 |
| Battle of Lübeck | battle_article | 1806 | French victoryBodart 1908 | unknown | unknown | 3 | 0 |
| Battle of Schleiz | battle_article | 1806 | French victory | victory | inferred_unique_belligerent_match | 3 | 1 |
| Battle of Waren-Nossentin | battle_article | 1806 | Prussian victory | defeat | inferred_unique_belligerent_match | 2 | 1 |
| War of the Fourth Coalition | war_conflict_article | 1806 | French victory | victory | inferred_unique_belligerent_match | 17 | 1 |
| Battle of Friedland | battle_article | 1807 | French victory | victory | inferred_unique_belligerent_match | 10 | 1 |
| Battle of Guttstadt-Deppen | battle_article | 1807 |  | unknown | unknown | 4 | 0 |
| Battle of Mohrungen | battle_article | 1807 | French victoryBodart 1908 | unknown | unknown | 2 | 0 |
| Gunboat War | war_conflict_article | 1807 | Anglo-Swedish victory Treaty of Kiel End of Denmark–Norway | unknown | unknown | 10 | 0 |
| Dano-Swedish War (1808–1809) | war_conflict_article | 1808 |  | unknown | unknown | 9 | 0 |
| Battle of Linz-Urfahr | battle_article | 1809 | Allied victory | victory | inferred_coalition_side_heuristic | 2 | 1 |
| Battle of Wagram | battle_article | 1809 | French victory Continuation of the Fifth Coalition until Armistice of Znaim | victory | inferred_unique_belligerent_match | 10 | 1 |
| Walcheren Campaign | campaign_article | 1809 | Franco-Dutch victory | victory | inferred_unique_belligerent_match | 3 | 1 |
| War of the Sixth Coalition | war_conflict_article | 1812 | Coalition victory | victory | inferred_coalition_label_match | 16 | 1 |
| Battle of Dennewitz | battle_article | 1813 | Coalition victoryLeggiere 2002Leggiere 2015 | unknown | unknown | 3 | 0 |
| Battle of Großbeeren | battle_article | 1813 | Coalition victory | unknown | unknown | 2 | 0 |
| Battle of Leipzig | battle_article | 1813 | Coalition victory | victory | inferred_coalition_label_match | 6 | 1 |
| Dano-Swedish War (1813–1814) | war_conflict_article | 1813 | Coalition victory (Treaty of Kiel) | victory | inferred_coalition_strength_heuristic | 6 | 1 |
| German campaign of 1813 | campaign_article | 1813 | Coalition victory | victory | inferred_coalition_strength_heuristic | 16 | 1 |
| Siege of Fredrikstad | battle_article | 1814 | Swedish victory | victory | inferred_unique_belligerent_match | 2 | 1 |
| Swedish–Norwegian War | war_conflict_article | 1814 | Victory | unknown | unknown | 8 | 0 |

Residual unresolved coalition/allied rows still attached to this commander:

| battle_name | page_type | analytic_year | result_raw | outcome_category | outcome_inference_method | same_side_commander_count | known_outcome_flag |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Battle of Dennewitz | battle_article | 1813 | Coalition victoryLeggiere 2002Leggiere 2015 | unknown | unknown | 3 | 0 |
| Battle of Großbeeren | battle_article | 1813 | Coalition victory | unknown | unknown | 2 | 0 |


## Residual Group-Level Concern

The remaining historical caution in the hierarchical layer is now less about a single parsing bug and more about profile type:

- commanders with heavy war/campaign exposure and modest battle-level defeat documentation
- commanders whose dossiers rely on generic coalition-result pages
- ancient or modern figures whose Wikipedia coverage is structurally uneven

That is why the interpretive layer still marks names such as `Qasem Soleimani`, `Nelson A. Miles`, and `Flavius Aetius` as caution-heavy or low-confidence, even after the second pass.

## Bottom Line

- `Qasem Soleimani` and `Nelson A. Miles` are no longer top-10 hierarchical leaders and are no longer being lifted by the residual anti/coaltition bug class.
- Their remaining elevation is mainly a model-and-coverage interaction problem, not a confirmed scoring bug.
- `Flavius Aetius` remains high but is better interpreted as a sparse-coverage caution case than as a parser artifact.
- `Charles XIV John` remains high but looks methodologically acceptable on the current evidence, with only bounded unresolved coalition ambiguity.
