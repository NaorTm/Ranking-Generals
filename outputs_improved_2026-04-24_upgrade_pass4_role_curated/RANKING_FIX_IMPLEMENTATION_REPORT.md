# Ranking Fix Implementation Report

## Scope

This is a targeted correction pass on top of `outputs_cleaned_2026-04-10_authoritative`. The old authoritative package is preserved unchanged. The corrected and rebuilt analytics snapshot is `outputs_cleaned_2026-04-10_rankfix_authoritative`, which supersedes `outputs_cleaned_2026-04-10_authoritative` for scoring, ranking, interpretive, and dashboard outputs.

No battle-layer or commander-layer rebuild was performed in this pass. The authoritative data layer consumed here is the already-clean battle and commander snapshot copied forward into `outputs_cleaned_2026-04-10_rankfix_authoritative`.

## Files Changed

- `build_scoring_framework_package.py`
- `build_ranking_package.py`
- `build_interpretive_layer.py`
- `generate_post_commander_reports.py`
- `generate_rankfix_reports.py`

## Fix 1: Outcome-Inference Bug For `anti-X` Results

Old incorrect behavior:

- Result strings like `Anti-Swedish coalition victory` could be interpreted as a Swedish victory because the old matcher treated the `Swedish` token as ordinary positive winner evidence.

Corrected behavior:

- `anti-X` / `against X` is now treated as loser-side evidence first.
- The corrected matcher resolves the winning side as the non-target side, preferring the unique opposing side and then the coalition side when available.
- This path now correctly handles Charles XII cases such as `Great Northern War` and `Siege of Stralsund (1711–1715)`.

Affected anti-target rows:

- anti-target rows in annotated commander engagements: `171`
- anti-target rows whose outcome changed: `137`
- wrong `victory -> defeat` flips corrected: `42`
- wrong `defeat -> victory` flips corrected: `45`
- `unknown -> known` because the new matcher could now resolve the row: `31`
- `known -> unknown` because the new matcher refused to overclaim on unresolved aliases or ambiguous pages: `19`

## Fix 2: Unknown Outcomes No Longer Pollute Split-Credit Denominators

Old behavior:

- In split-credit models, `outcome_factor_split` was equal to `outcome_credit_fraction`, even when `outcome_category = unknown`.
- That meant unknown outcomes still sat in the denominator as zero-value evidence instead of being treated as missing evidence.

Corrected behavior:

- `outcome_factor_split` is now `outcome_credit_fraction * 1[outcome_category != 'unknown']`.

Validation:

- unknown annotated rows in the rebuilt package: `33,451`
- rows where unknown still contributes non-zero split outcome factor: `0`

## Fix 3: Defeat Dilution Under Split Credit

Old behavior:

- Same-side outcome credit used a strict `1 / side_count` split.
- On crowded pages, defeats were diluted so aggressively that a serious loss could become too weak relative to the commander’s victories.

Corrected behavior:

- Same-side outcome credit now uses `1 / sqrt(side_count)`.
- This still discounts crowded pages, but it no longer crushes defeats as hard as the old linear split.

Observed effect:

- commander engagement rows whose split credit changed: `48,476`
- example: Charles XII at `Battle of Poltava` changed from `0.142857` to `0.377964`
- example: Charles XII at `Siege of Stralsund (1711–1715)` changed from `0.333333` to `0.577350`
- example: Charles XII at `Battle of Narva (1700)` changed from `0.333333` to `0.577350`

## Fix 4: Confirmed Charles XII Mis-Scoring

These corrections were produced by the fixed inference layer, not by manual hand-editing of battle rows:

| battle_name | page_type | result_raw | side | old_outcome | new_outcome | old_method | new_method | old_credit | new_credit |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Battle of Narva (1700) | battle_article | Swedish victory | side_a | victory | victory | inferred_unique_belligerent_match | inferred_unique_belligerent_match | 0.333333 | 0.577350 |
| Great Northern War | war_conflict_article | Anti-Swedish coalition victory | side_a | victory | defeat | inferred_unique_belligerent_match | inferred_negated_target_match | 0.071429 | 0.267261 |
| Landing at Humlebæk | battle_article | Swedish victory | side_a | victory | victory | inferred_unique_belligerent_match | inferred_unique_belligerent_match | 0.250000 | 0.500000 |
| Battle of Kliszów | battle_article | Swedish victory | side_a | victory | victory | inferred_unique_belligerent_match | inferred_unique_belligerent_match | 0.333333 | 0.577350 |
| Battle of Desna | battle_article | Swedish victory | side_a | victory | victory | inferred_unique_belligerent_match | inferred_unique_belligerent_match | 0.500000 | 0.707107 |
| Battle of Holowczyn | battle_article | Swedish victory | side_a | victory | victory | inferred_unique_belligerent_match | inferred_unique_belligerent_match | 0.500000 | 0.707107 |
| Battle of Malatitze | battle_article |  | side_a | unknown | unknown | unknown | unknown | 0.500000 | 0.707107 |
| Battle of Poltava | battle_article | Russian coalition victory | side_a | defeat | defeat | inferred_unique_belligerent_match | inferred_unique_belligerent_match | 0.142857 | 0.377964 |
| Siege of Stralsund (1711–1715) | battle_article | Anti-Swedish coalition victory | side_a | victory | defeat | inferred_unique_belligerent_match | inferred_negated_target_match | 0.333333 | 0.577350 |
| Skirmish at Bender | battle_article | Ottoman victory | side_b | defeat | defeat | inferred_unique_belligerent_match | inferred_unique_belligerent_match | 0.500000 | 0.707107 |
| Battle of Stresow | battle_article | Coalition victory | side_a | unknown | defeat | unknown | inferred_coalition_side_heuristic | 1.000000 | 1.000000 |
| Siege of Fredriksten | battle_article | Dano-Norwegian victory | side_b | unknown | defeat | unknown | inferred_unique_belligerent_match | 1.000000 | 1.000000 |

What changed materially for Charles XII:

- `Great Northern War`: `victory -> defeat`
- `Siege of Stralsund (1711–1715)`: `victory -> defeat`
- `Battle of Stresow`: `unknown -> defeat`
- `Siege of Fredriksten`: `unknown -> defeat`
- `Battle of Poltava`: still `defeat`, but its split-outcome weight increased materially under the new split rule

Known unresolved Charles XII caveat:

- `Battle of Malatitze` remains `unknown`; this pass did not guess an unsupported outcome.

## Rebuilt Outputs

- scoring docs and derived tables under `outputs_cleaned_2026-04-10_rankfix_authoritative\derived_scoring`
- ranking outputs: `RANKING_RESULTS_*.csv`, `RANKING_BUILD_METRICS.json`, `TOP_COMMANDERS_SUMMARY.csv`
- interpretive outputs: `TOP_TIER_CLASSIFICATION.csv`, `MODEL_SENSITIVITY_AUDIT.csv`, `ERA_ELITE_SHORTLIST.csv`, `BEST_SUPPORTED_TOP_TIER_MEMO.md`
- dashboard bundle: `outputs_cleaned_2026-04-10_rankfix_authoritative\dashboard`
- dashboard QA: `dashboard_qa_summary.json`

## Validation Summary

- total commander engagement rows with any outcome or credit change: `51,144`
- rows whose outcome category changed: `9,542`
- rows whose known-outcome flag changed: `9,439`
- coalition/allied outcome rows whose outcome changed: `1,012`
- coalition/allied rows resolved from `unknown` to known outcome: `938`

## Residual Caveats

- The old `anti-X` inversion bug is fixed on the confirmed Charles XII pages and on many similar rows, but `32` anti-target rows still remain unresolved because of alias gaps or structurally ambiguous pages.
- Representative unresolved anti-target examples:

| battle_name | display_name | result_raw | side | outcome_inference_method |
| --- | --- | --- | --- | --- |
| War against Nabis | Nabis of Sparta | Anti-Spartan coalition victory | side_a | unknown |
| War against Nabis | Pythagoras of Argos | Anti-Spartan coalition victory | side_a | unknown |
| War against Nabis | Dexagoridas | Anti-Spartan coalition victory | side_a | unknown |
| War against Nabis | Gorgopas | Anti-Spartan coalition victory | side_a | unknown |
| War against Nabis | Titus Quinctius Flamininus | Anti-Spartan coalition victory | side_b | unknown |
| War against Nabis | Philopoemen | Anti-Spartan coalition victory | side_b | unknown |
| War against Nabis | Eumenes II | Anti-Spartan coalition victory | side_b | unknown |
| War against Nabis | Aristaenus | Anti-Spartan coalition victory | side_b | unknown |

- Coalition/allied result strings improved substantially, but `1,912` coalition/allied rows still remain unresolved in the rebuilt snapshot. Those rows were left conservative rather than guessed.
- This pass intentionally did not touch the battle or commander source layers. It corrected logic and downstream scoring behavior only.
