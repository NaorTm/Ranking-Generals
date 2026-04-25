# Second Pass Anti Coalition Audit

## Scope

This is a focused residual audit on top of `outputs_cleaned_2026-04-10_rankfix_authoritative`. It reviews only the remaining `anti-*`, `allied`, `coalition`, and related target-of-coalition outcome patterns in the rebuilt second-pass snapshot `outputs_cleaned_2026-04-10_secondpass_authoritative`.

## What Changed In This Pass

- Confirmed anti-target bug fixes were extended to short targets and alias-bearing sides by searching both belligerent labels and commander-side raw text.
- Coalition/allied inference was tightened with direct label matches, coalition-strength heuristics, and additional coalition aliases.
- Narrative false positives using the word `against` were reviewed, but they were left unresolved when they did not actually express winner-side meaning.

## Residual Anti Pattern Status

- anti-pattern pages unresolved before this pass: `5`
- anti-pattern pages unresolved after this pass: `1`
- anti/coaltition row-level changes in annotated commander engagements: `795`

Confirmed anti-target pages fixed in this pass:

- `Barrios' War of Reunification`, `Battle of Chuisha`, `War against Nabis`

Remaining anti-pattern pages after the pass:

| battle_name | page_type | result_raw | outcome_inference_method |
| --- | --- | --- | --- |
| Battle of Northern Henan | battle_article | Chiang Kai-shek's Han Fuju led military attack failed anti Feng | unknown |

Affected commanders for the remaining anti-pattern page(s):

| battle_name | display_name | rank_hierarchical_weighted | rank_battle_only_baseline |
| --- | --- | --- | --- |
| Battle of Northern Henan | Han Fuju |  |  |
| Battle of Northern Henan | Pang Bingxun |  | 1560 |

Judgment:

- There is no remaining confirmed `anti-X` winner-inversion bug affecting any top-ranked commander.
- The only remaining anti-pattern page is `Battle of Northern Henan`, whose result text is narrative (`failed anti Feng`) rather than a clean coalition-result label.
- Its only ranking-visible commander is `Pang Bingxun`, who is unranked in hierarchical and `#1560` in battle-only. This is not a material distortion case.

## Residual Coalition Pattern Status

- coalition/allied pages unresolved before this pass: `332`
- coalition/allied pages unresolved after this pass: `283`
- coalition/allied pages newly resolved from unknown to known in this pass: `47` distinct pages

Representative coalition/allied pages fixed in this pass:

- `Adriatic campaign of 1807–1814`, `African theatre of World War I`, `Asian and Pacific theatre of World War I`, `Battle of Aden (2015)`, `Battle of Beersheba (1917)`, `Battle of Bornholm (1535)`, `Battle of Dobro Pole`, `Battle of Durazzo (1915)`, `Battle of Jaffa (1917)`, `Battle of Leipzig`, `Battle of Little Belt`, `Battle of Madagascar`

Most affected coalition/allied pages in row-count terms:

| battle_name | result_raw | affected_rows | changed_outcomes |
| --- | --- | --- | --- |
| Eastern Front (World War II) | Soviet victoryAs part of the Allied victory in the European theatre of World War II | 79 | 79 |
| Middle Eastern theatre of World War I | Allied victory | 42 | 42 |
| Seven Years' War | Anglo-Prussian coalition victory | 34 | 34 |
| African theatre of World War I | Allied victory | 33 | 33 |
| War of the Sixth Coalition | Coalition victory | 33 | 33 |
| German campaign of 1813 | Coalition victory | 31 | 31 |
| Persian campaign (World War I) | Allied victory Armistice of Mudros Ottoman forces withdraw from Persia | 29 | 29 |
| European theatre of World War II | Allied victory | 24 | 24 |
| Serbian campaign | Serbian victory (1914); Central Powers victory (1915); Allied victory (1918) | 20 | 20 |
| North African campaign | Allied victory | 19 | 19 |
| Siege of the International Legations | Allied victory | 19 | 0 |
| Battle of the Mediterranean | Allied victory | 18 | 18 |

Remaining unresolved coalition/allied pages that still touch the hierarchical top 30:

| display_name | unresolved_pages | page_names |
| --- | --- | --- |
| Mustafa Kemal Atatürk | 3 | Battle of Jisr Benat Yakub; Battle of Nablus (1918); Battle of Sharon |
| Charles XIV John | 2 | Battle of Dennewitz; Battle of Großbeeren |
| Charles-Pierre Augereau | 1 | Battle of Limonest |
| Napoleon Bonaparte | 1 | Mediterranean campaign of 1798 |

These residual pages are not confirmed bugs. They fall into three buckets:

1. Generic coalition labels with insufficient side labeling: plain `Allied victory` or `Coalition victory` where the side text is too generic to map safely.
2. Citation-polluted result fields: examples like `Coalition victoryLeggiere 2002` where the result text is fused to source notes.
3. Real ambiguity on multi-side pages: war/campaign pages whose page-level result is clear in the abstract but not safe to assign to every listed commander side without overclaiming.

## Narrative `against` False Positives

These rows still contain `against`, but they are not outcome-inference bugs:

| battle_name | page_type | result_raw |
| --- | --- | --- |
| Siege of La Charité | battle_article | Impasse, the city delivered to Charles VII against a huge ransom |
| Mačva operation | operation_article | Failure of Axis forces to capture or destroy rebel forces which retreated from Mačva massive reprisals against civilians |
| Operation Billings | operation_article | The operation was conducted from 12 to 26 June 1967 and resulted in 347 VC killed and one captured against U.S. |

They were deliberately left conservative because the word `against` is narrative here, not coalition-target logic.

## Materiality Assessment

- The anti-target inversion bug is now bounded to zero material ranking cases.
- Residual coalition/allied unknowns still exist, but they are now mostly a coverage/underspecification issue rather than a winner-side inversion bug.
- After the split-denominator fix, unresolved coalition/allied rows no longer enter outcome denominators as zero-value evidence.
- Their remaining effect is limited to presence, scope, and centrality exposure.
- In the hierarchical top 30, only four commanders still have unresolved coalition/allied pages: `Mustafa Kemal Ataturk`, `Charles XIV John`, `Charles-Pierre Augereau`, and `Napoleon Bonaparte`.
- None of the two main suspicious leaders from the first pass, `Qasem Soleimani` and `Nelson A. Miles`, are still being lifted by unresolved anti/coaltition rows.

## Bottom Line

This second pass fixed the remaining confirmed anti-target inversion cases and a large additional block of coalition/allied unknowns. What remains is bounded ambiguity, not an obvious residual bug. The remaining unresolved pages are auditable and no longer appear to materially distort the top-level ranking conclusions.
