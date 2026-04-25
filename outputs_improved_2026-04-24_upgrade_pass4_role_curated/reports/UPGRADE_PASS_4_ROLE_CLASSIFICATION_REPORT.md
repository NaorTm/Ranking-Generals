# Upgrade Pass 4 Role Classification Report

Snapshot: `outputs_improved_2026-04-24_upgrade_pass4_role_curated`

Parent snapshot: `outputs_improved_2026-04-24_upgrade_pass3_confidence`

Headline model remains `hierarchical_trust_v2`. Pass 4 adds a role-aware sensitivity model and audit layer; it does not replace the headline ranking.

## Methodology

- Built `verification/verified_command_role_classification.csv` for every commander-engagement row.
- Used manual seed overrides for the current top commanders, prior top-list commanders, and Pass 2 suspicious political/staff cases.
- Used heuristic fallback classification from page type, same-side commander density, and Pass 2 eligibility flags.
- Applied initial role weights exactly as a sensitivity assumption, not as historical truth.
- Computed role score shares and a role-weighted sensitivity score from existing trust-v2 scores adjusted by role mix, role confidence, and Pass 2 headline exclusions.

## Top 50 Role Sensitivity

| rank_hierarchical_trust_v2 | rank_role_weighted | rank_change_vs_hierarchical_trust_v2 | display_name | confidence_adjusted_tier | dominant_role_class | share_direct_field_command | broad_page_contribution_share | share_unclear_role | main_caveat |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 1 | 0 | Alexander Suvorov | Tier A, confidence-supported robust elite | overall_commander | 100.0% | 0.0% | 0.0% | Role evidence supports ranking without a major Pass 4 caveat. |
| 2 | 3 | 1 | Maurice, Prince of Orange | Tier B, confidence-supported elite | overall_commander | 100.0% | 0.0% | 0.0% | Role evidence supports ranking without a major Pass 4 caveat. |
| 3 | 2 | -1 | Napoleon Bonaparte | Tier A, confidence-supported robust elite | overall_commander | 100.0% | 0.0% | 0.0% | Role evidence supports ranking without a major Pass 4 caveat. |
| 4 | 11 | 7 | Subutai | Tier B, confidence-supported elite | principal_field_commander | 100.0% | 4.9% | 0.0% | Role evidence supports ranking without a major Pass 4 caveat. |
| 5 | 23 | 18 | Sébastien Le Prestre, Marquis of Vauban | Tier B, confidence-supported elite | siege_engineer_or_specialist | 0.0% | 0.0% | 0.0% | Category-specific siege/engineering case rather than pure field ranking. |
| 6 | 9 | 3 | Jean Lannes | Tier A, confidence-supported robust elite | principal_field_commander | 100.0% | 1.4% | 0.0% | Role evidence supports ranking without a major Pass 4 caveat. |
| 7 | 10 | 3 | Louis-Nicolas Davout | Tier B, confidence-supported elite | principal_field_commander | 100.0% | 2.7% | 0.0% | Role evidence supports ranking without a major Pass 4 caveat. |
| 8 | 41 | 33 | Douglas MacArthur | Tier B, confidence-supported elite | coalition_commander | 0.0% | 6.6% | 0.0% | Role weighting materially weakens exact rank. |
| 9 | 43 | 34 | Charles XIV John | Tier B, confidence-supported elite | coalition_commander | 0.0% | 3.3% | 0.0% | Role weighting materially weakens exact rank. |
| 10 | 4 | -6 | Ivan Paskevich | Tier C, high-ranking but confidence-limited | overall_commander | 100.0% | 5.8% | 0.0% | Role evidence supports ranking without a major Pass 4 caveat. |
| 11 | 987 | 976 | Louis XIV | Tier B, confidence-supported elite | nominal_or_political_leader | 0.0% | 7.7% | 0.0% | Nominal/political role share is high; headline interpretation needs curation. |
| 12 | 12 | 0 | Henri de La Tour d'Auvergne, Viscount of Turenne | Tier B, confidence-supported elite | principal_field_commander | 98.0% | 0.0% | 2.0% | Role evidence supports ranking without a major Pass 4 caveat. |
| 13 | 22 | 9 | Mehmed II | Tier B, confidence-supported elite | principal_field_commander | 98.2% | 1.8% | 1.8% | Role evidence supports ranking without a major Pass 4 caveat. |
| 14 | 36 | 22 | Belisarius | Tier B, confidence-supported elite | principal_field_commander | 97.2% | 2.2% | 2.6% | Role weighting materially weakens exact rank. |
| 15 | 20 | 5 | Louis-Gabriel Suchet | Tier B, confidence-supported elite | principal_field_commander | 99.0% | 0.6% | 0.4% | Role evidence supports ranking without a major Pass 4 caveat. |
| 16 | 32 | 16 | André Masséna | Tier B, confidence-supported elite | principal_field_commander | 99.0% | 0.8% | 0.3% | Role evidence supports ranking without a major Pass 4 caveat. |
| 17 | 14 | -3 | Alexander Farnese, Duke of Parma | Tier B, confidence-supported elite | principal_field_commander | 99.5% | 0.0% | 0.5% | Role evidence supports ranking without a major Pass 4 caveat. |
| 18 | 17 | -1 | Khalid ibn al-Walid | Tier A, confidence-supported robust elite | principal_field_commander | 99.8% | 0.0% | 0.2% | Role evidence supports ranking without a major Pass 4 caveat. |
| 19 | 5 | -14 | Genghis Khan | Tier C, high-ranking but confidence-limited | overall_commander | 100.0% | 4.4% | 0.0% | Role evidence supports ranking without a major Pass 4 caveat. |
| 20 | 13 | -7 | Hubert Gough | Tier C, high-ranking but confidence-limited | principal_field_commander | 100.0% | 5.3% | 0.0% | Role evidence supports ranking without a major Pass 4 caveat. |
| 21 | 19 | -2 | Bernard Montgomery | Tier C, high-ranking but confidence-limited | overall_commander | 91.9% | 48.9% | 0.0% | High broad-page dependency; role-weighted interpretation is qualified. |
| 22 | 53 | 31 | Maharaja Ranjit Singh | Tier C, high-ranking but confidence-limited | principal_field_commander | 88.6% | 12.4% | 9.4% | Role weighting materially weakens exact rank. |
| 23 | 35 | 12 | Alexander the Great | Tier C, high-ranking but confidence-limited | principal_field_commander | 99.1% | 1.1% | 0.0% | Role evidence supports ranking without a major Pass 4 caveat. |
| 24 | 45 | 21 | Winfield Scott | Tier C, high-ranking but confidence-limited | principal_field_commander | 93.9% | 2.6% | 3.7% | Role weighting materially weakens exact rank. |
| 25 | 15 | -10 | Hannibal | Tier C, high-ranking but confidence-limited | principal_field_commander | 97.8% | 2.5% | 1.2% | Role evidence supports ranking without a major Pass 4 caveat. |
| 26 | 39 | 13 | Enver Pasha | Tier C, high-ranking but confidence-limited | principal_field_commander | 87.0% | 6.5% | 4.3% | Role evidence supports ranking without a major Pass 4 caveat. |
| 27 | 16 | -11 | Baybars | Tier C, high-ranking but confidence-limited | principal_field_commander | 99.0% | 0.0% | 1.0% | Role evidence supports ranking without a major Pass 4 caveat. |
| 28 | 27 | -1 | Peng Dehuai | Tier C, high-ranking but confidence-limited | principal_field_commander | 98.9% | 0.0% | 1.1% | Role evidence supports ranking without a major Pass 4 caveat. |
| 29 | 6 | -23 | Frederick the Great | Tier C, high-ranking but confidence-limited | overall_commander | 100.0% | 3.1% | 0.0% | Role evidence supports ranking without a major Pass 4 caveat. |
| 30 | 51 | 21 | Heinz Guderian | Tier C, high-ranking but confidence-limited | principal_field_commander | 100.0% | 0.0% | 0.0% | Role weighting materially weakens exact rank. |
| 31 | 86 | 55 | Charles-Pierre Augereau | Tier C, high-ranking but confidence-limited | principal_field_commander | 96.5% | 3.1% | 0.5% | Role weighting materially weakens exact rank. |
| 32 | 21 | -11 | Takeda Shingen | Tier B, confidence-supported elite | principal_field_commander | 100.0% | 0.0% | 0.0% | Role evidence supports ranking without a major Pass 4 caveat. |
| 33 | 59 | 26 | Hari Singh Nalwa | Tier C, high-ranking but confidence-limited | principal_field_commander | 96.5% | 3.6% | 3.5% | Role weighting materially weakens exact rank. |
| 34 | 84 | 50 | Aurangzeb | Tier C, high-ranking but confidence-limited | principal_field_commander | 98.3% | 0.3% | 1.7% | Role weighting materially weakens exact rank. |
| 35 | 46 | 11 | Ögedei Khan | Tier C, high-ranking but confidence-limited | principal_field_commander | 93.3% | 6.7% | 0.0% | Role evidence supports ranking without a major Pass 4 caveat. |
| 36 | 68 | 32 | Dwight D. Eisenhower | Tier C, high-ranking but confidence-limited | coalition_commander | 0.0% | 54.2% | 0.0% | High broad-page dependency; role-weighted interpretation is qualified. |
| 37 | 64 | 27 | Katō Kiyomasa | Tier C, high-ranking but confidence-limited | principal_field_commander | 97.8% | 2.5% | 0.0% | Role weighting materially weakens exact rank. |
| 38 | 119 | 81 | Tokugawa Ieyasu | Tier C, high-ranking but confidence-limited | wing_or_corps_commander | 98.1% | 2.1% | 0.0% | Role weighting materially weakens exact rank. |
| 39 | 7 | -32 | Georgy Zhukov | Tier C, high-ranking but confidence-limited | overall_commander | 100.0% | 25.1% | 0.0% | Role evidence supports ranking without a major Pass 4 caveat. |
| 40 | 94 | 54 | Mikhail Kutuzov | Tier C, high-ranking but confidence-limited | principal_field_commander | 94.9% | 6.4% | 0.0% | Role weighting materially weakens exact rank. |
| 41 | 29 | -12 | Stanisław Żółkiewski | Tier C, high-ranking but confidence-limited | principal_field_commander | 100.0% | 0.0% | 0.0% | Role evidence supports ranking without a major Pass 4 caveat. |
| 42 | 26 | -16 | Charles XII of Sweden | Tier C, high-ranking but confidence-limited | principal_field_commander | 99.5% | 0.6% | 0.0% | Role evidence supports ranking without a major Pass 4 caveat. |
| 43 | 18 | -25 | Fyodor Tolbukhin | Tier C, high-ranking but confidence-limited | overall_commander | 100.0% | 54.7% | 0.0% | High broad-page dependency; role-weighted interpretation is qualified. |
| 44 | 72 | 28 | Nikolai Vatutin | Tier C, high-ranking but confidence-limited | wing_or_corps_commander | 79.8% | 47.2% | 0.0% | High broad-page dependency; role-weighted interpretation is qualified. |
| 45 | 33 | -12 | Rodion Malinovsky | Tier C, high-ranking but confidence-limited | overall_commander | 89.7% | 56.2% | 0.0% | High broad-page dependency; role-weighted interpretation is qualified. |
| 46 | 40 | -6 | Mustafa Kemal Atatürk | Tier C, high-ranking but confidence-limited | principal_field_commander | 94.7% | 3.6% | 3.3% | Role evidence supports ranking without a major Pass 4 caveat. |
| 47 | 8 | -39 | Konstantin Rokossovsky | Tier C, high-ranking but confidence-limited | overall_commander | 100.0% | 46.1% | 0.0% | High broad-page dependency; role-weighted interpretation is qualified. |
| 48 | 50 | 2 | Peter Wittgenstein | Tier C, high-ranking but confidence-limited | principal_field_commander | 98.9% | 1.1% | 0.0% | Role evidence supports ranking without a major Pass 4 caveat. |
| 49 | 30 | -19 | Tolui | Tier C, high-ranking but confidence-limited | principal_field_commander | 92.4% | 7.6% | 0.0% | Role evidence supports ranking without a major Pass 4 caveat. |
| 50 | 25 | -25 | Fedor von Bock | Tier C, high-ranking but confidence-limited | principal_field_commander | 100.0% | 43.7% | 0.0% | High broad-page dependency; role-weighted interpretation is qualified. |

## Specific Audit Notes

- **Alexander Suvorov**: dominant role `overall_commander`; direct field-command share 100.0%, broad-page share 0.0%, unclear-role share 0.0%. The role-weighted model does not move. Interpret as **robust**: Role evidence supports ranking without a major Pass 4 caveat.
- **Maurice, Prince of Orange**: dominant role `overall_commander`; direct field-command share 100.0%, broad-page share 0.0%, unclear-role share 0.0%. The role-weighted model drops 1 places. Interpret as **robust**: Role evidence supports ranking without a major Pass 4 caveat.
- **Napoleon Bonaparte**: dominant role `overall_commander`; direct field-command share 100.0%, broad-page share 0.0%, unclear-role share 0.0%. The role-weighted model improves 1 places. Interpret as **robust**: Role evidence supports ranking without a major Pass 4 caveat.
- **Subutai**: dominant role `principal_field_commander`; direct field-command share 100.0%, broad-page share 4.9%, unclear-role share 0.0%. The role-weighted model drops 7 places. Interpret as **robust**: Role evidence supports ranking without a major Pass 4 caveat.
- **Sébastien Le Prestre, Marquis of Vauban**: dominant role `siege_engineer_or_specialist`; direct field-command share 0.0%, broad-page share 0.0%, unclear-role share 0.0%. The role-weighted model drops 18 places. Interpret as **qualified**: Category-specific siege/engineering case rather than pure field ranking.
- **Jean Lannes**: dominant role `principal_field_commander`; direct field-command share 100.0%, broad-page share 1.4%, unclear-role share 0.0%. The role-weighted model drops 3 places. Interpret as **robust**: Role evidence supports ranking without a major Pass 4 caveat.
- **Louis-Nicolas Davout**: dominant role `principal_field_commander`; direct field-command share 100.0%, broad-page share 2.7%, unclear-role share 0.0%. The role-weighted model drops 3 places. Interpret as **robust**: Role evidence supports ranking without a major Pass 4 caveat.
- **Douglas MacArthur**: dominant role `coalition_commander`; direct field-command share 0.0%, broad-page share 6.6%, unclear-role share 0.0%. The role-weighted model drops 33 places. Interpret as **qualified**: Role weighting materially weakens exact rank.
- **Charles XIV John**: dominant role `coalition_commander`; direct field-command share 0.0%, broad-page share 3.3%, unclear-role share 0.0%. The role-weighted model drops 34 places. Interpret as **qualified**: Role weighting materially weakens exact rank.
- **Ivan Paskevich**: dominant role `overall_commander`; direct field-command share 100.0%, broad-page share 5.8%, unclear-role share 0.0%. The role-weighted model improves 6 places. Interpret as **robust**: Role evidence supports ranking without a major Pass 4 caveat.
- **Dwight D. Eisenhower**: dominant role `coalition_commander`; direct field-command share 0.0%, broad-page share 54.2%, unclear-role share 0.0%. The role-weighted model drops 32 places. Interpret as **qualified**: High broad-page dependency; role-weighted interpretation is qualified.
- **Georgy Zhukov**: dominant role `overall_commander`; direct field-command share 100.0%, broad-page share 25.1%, unclear-role share 0.0%. The role-weighted model improves 32 places. Interpret as **robust**: Role evidence supports ranking without a major Pass 4 caveat.
- **Genghis Khan**: dominant role `overall_commander`; direct field-command share 100.0%, broad-page share 4.4%, unclear-role share 0.0%. The role-weighted model improves 14 places. Interpret as **robust**: Role evidence supports ranking without a major Pass 4 caveat.
- **Frederick the Great**: dominant role `overall_commander`; direct field-command share 100.0%, broad-page share 3.1%, unclear-role share 0.0%. The role-weighted model improves 23 places. Interpret as **robust**: Role evidence supports ranking without a major Pass 4 caveat.
- **Konstantin Rokossovsky**: dominant role `overall_commander`; direct field-command share 100.0%, broad-page share 46.1%, unclear-role share 0.0%. The role-weighted model improves 39 places. Interpret as **qualified**: High broad-page dependency; role-weighted interpretation is qualified.

## Largest Rank Drops After Role Weighting

| rank_hierarchical_trust_v2 | rank_role_weighted | rank_change_vs_hierarchical_trust_v2 | display_name | dominant_role_class | share_unclear_role | share_nominal_or_political | broad_page_contribution_share |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 11 | 987 | 976 | Louis XIV | nominal_or_political_leader | 0.0% | 100.0% | 7.7% |
| 216 | 1060 | 844 | Hulusi Akar | staff_or_planning_role | 0.0% | 0.0% | 100.0% |
| 292 | 1063 | 771 | Lê Duẩn | nominal_or_political_leader | 0.0% | 100.0% | 100.0% |
| 453 | 1062 | 609 | Ashfaq Parvez Kayani | staff_or_planning_role | 0.0% | 0.0% | 100.0% |
| 463 | 1064 | 601 | Phạm Văn Đồng | nominal_or_political_leader | 0.0% | 100.0% | 100.0% |
| 354 | 900 | 546 | Ghiath Dalla | unclear_role | 92.6% | 0.0% | 100.0% |
| 279 | 807 | 528 | Marc Mitscher | unclear_role | 69.9% | 0.0% | 74.7% |
| 243 | 736 | 493 | Ivan Chernyakhovsky | unclear_role | 63.3% | 0.0% | 80.8% |
| 559 | 1001 | 442 | Đỗ Cao Trí | unclear_role | 100.0% | 0.0% | 100.0% |
| 373 | 795 | 422 | Miles Dempsey | unclear_role | 52.2% | 0.0% | 59.0% |
| 202 | 584 | 382 | William Halsey Jr. | wing_or_corps_commander | 37.4% | 0.0% | 44.6% |
| 125 | 490 | 365 | Suhayl al-Hasan | unclear_role | 64.6% | 0.0% | 81.3% |
| 195 | 559 | 364 | Abu Mohammad al-Julani | unclear_role | 58.8% | 0.0% | 100.0% |
| 660 | 1016 | 356 | Jonas Savimbi | unclear_role | 100.0% | 0.0% | 100.0% |
| 352 | 705 | 353 | Markian Popov | wing_or_corps_commander | 26.1% | 0.0% | 42.1% |
| 516 | 869 | 353 | Georg-Hans Reinhardt | unclear_role | 60.4% | 0.0% | 72.3% |
| 416 | 768 | 352 | Ii Naomasa | wing_or_corps_commander | 8.0% | 0.0% | 9.6% |
| 405 | 755 | 350 | Aliagha Shikhlinski | wing_or_corps_commander | 4.1% | 0.0% | 4.1% |
| 326 | 675 | 349 | Ukita Hideie | wing_or_corps_commander | 5.5% | 0.0% | 5.5% |
| 188 | 526 | 338 | Chiang Kai-shek | wing_or_corps_commander | 36.4% | 0.0% | 29.9% |

## Largest Improvements Or Credibility Gains

| rank_hierarchical_trust_v2 | rank_role_weighted | rank_change_vs_hierarchical_trust_v2 | display_name | dominant_role_class | share_direct_field_command | broad_page_contribution_share |
| --- | --- | --- | --- | --- | --- | --- |
| 511 | 336 | -175 | Trần Văn Trà | overall_commander | 82.3% | 66.4% |
| 818 | 646 | -172 | Miguel Grau | principal_field_commander | 100.0% | 0.0% |
| 834 | 666 | -168 | George of Hesse-Darmstadt | principal_field_commander | 100.0% | 0.0% |
| 629 | 462 | -167 | Francisco Pizarro | principal_field_commander | 100.0% | 0.0% |
| 709 | 545 | -164 | Wazir Khan | principal_field_commander | 100.0% | 0.0% |
| 512 | 349 | -163 | Tughril I | principal_field_commander | 100.0% | 0.0% |
| 514 | 351 | -163 | Prince Emanuele Filiberto, Duke of Aosta | principal_field_commander | 100.0% | 0.0% |
| 513 | 350 | -163 | Attila the Hun | principal_field_commander | 100.0% | 0.0% |
| 760 | 598 | -162 | Karl von Bülow | principal_field_commander | 100.0% | 0.0% |
| 718 | 557 | -161 | Bhim Chand | principal_field_commander | 100.0% | 0.0% |
| 302 | 141 | -161 | James Somerville | overall_commander | 100.0% | 69.9% |
| 800 | 639 | -161 | Omer Vrioni | principal_field_commander | 100.0% | 0.0% |
| 852 | 692 | -160 | Pierre Dupont de l'Étang | principal_field_commander | 100.0% | 0.0% |
| 635 | 476 | -159 | Toghtekin | principal_field_commander | 100.0% | 0.0% |
| 407 | 248 | -159 | Masinissa | principal_field_commander | 100.0% | 0.0% |
| 733 | 574 | -159 | James G. Blunt | principal_field_commander | 100.0% | 0.0% |
| 786 | 627 | -159 | Lala Shahin Pasha | principal_field_commander | 100.0% | 0.0% |
| 556 | 397 | -159 | Charles Martel | principal_field_commander | 100.0% | 0.0% |
| 649 | 492 | -157 | Douglas H. Cooper | principal_field_commander | 100.0% | 0.0% |
| 666 | 510 | -156 | Kilij Arslan I | principal_field_commander | 100.0% | 0.0% |

## High-Rank, High-Unclear-Role Cases

| rank_hierarchical_trust_v2 | rank_role_weighted | display_name | dominant_role_class | share_unclear_role | broad_page_contribution_share | confidence_adjusted_tier |
| --- | --- | --- | --- | --- | --- | --- |
| 125 | 490 | Suhayl al-Hasan | unclear_role | 64.6% | 81.3% | Tier D, page-type-sensitive performer |
| 101 | 253 | Georg von Küchler | principal_field_commander | 43.4% | 42.3% | Tier D, page-type-sensitive performer |
| 105 | 368 | Tommy Franks | unclear_role | 40.7% | 52.4% | Tier D, page-type-sensitive performer |

## Final Judgment

Role weighting improves interpretability because it separates direct field command, coalition/theater command, siege engineering, naval command, nominal political leadership, and unresolved role evidence. It does not prove a new historical order; it identifies where the exact rank depends on command-role assumptions.

Robust elite under Pass 4: Alexander Suvorov, Maurice, Prince of Orange, Napoleon Bonaparte, Subutai, Jean Lannes, Louis-Nicolas Davout, Ivan Paskevich, Henri de La Tour d'Auvergne, Viscount of Turenne, Mehmed II, Louis-Gabriel Suchet, Alexander Farnese, Duke of Parma, Khalid ibn al-Walid.

Category-specific or role-qualified high performers: Sébastien Le Prestre, Marquis of Vauban, Douglas MacArthur, Charles XIV John, Dwight D. Eisenhower, Joseph Stalin.

Commanders requiring stronger historical curation: Louis XIV, Georg von Küchler, Tommy Franks, Suhayl al-Hasan.

Next priority: replace heuristic role labels with source-backed manual curation for the top 100 and for every commander whose role-weighted rank movement exceeds 20 places.
