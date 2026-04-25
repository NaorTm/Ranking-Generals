# Generic Result Hardening Report

## Snapshot Lineage

- Starting snapshot: `outputs_cleaned_2026-04-12_genericrecovery_authoritative`
- Superseding snapshot: `outputs_cleaned_2026-04-12_victoryhardening_authoritative`

This pass did not restart the project. It applied a targeted correction to the remaining bare `Victory` / `Defeat` ambiguity class and a narrow hierarchical guardrail, then rebuilt scoring, ranking, interpretive, and dashboard outputs in the new snapshot.

## What Was Changed

### 1. Safe actor-led bare-result recovery was expanded

`build_scoring_framework_package.py` was extended with additional high-precision actor-led title patterns:

- `X campaigns against Y`
- `X expedition(s) to Y`
- `X invasion of Y`
- `X occupation of Y`
- `X landing at Y`

These rules still require a unique actor-to-side match. They do not guess from general title semantics alone.

### 2. Safe actor-led recovery was opened to battle articles

The actor-led inference helper previously applied only to `war_conflict_article`, `campaign_article`, and `operation_article`. That was too narrow. Safe actor-led `battle_article` pages such as `United States occupation of Nicaragua` and `Greek landing at Smyrna` were being left unresolved even though the title subject matched one side cleanly.

`SUBJECT_RESULT_PAGE_TYPES` now includes `battle_article` for this narrow actor-led path.

### 3. Empty side fields no longer normalize to the string `nan`

`normalize_space()` now treats pandas `NaN` as empty text. This removes a latent side-detection hazard where an absent third belligerent could behave like a populated side.

### 4. A narrow higher-level structural guardrail was added

`build_ranking_package.py` now applies a `thin_battle_anchor` guardrail in hierarchical models when all of the following are true:

- `higher_level_share >= 0.50`
- `known_battle_outcome_count < 2`
- `battle_count < 4`

For those commanders, `confidence_guardrail_factor` is capped at `0.92`.

This is a design guardrail, not a data rewrite. It targets the remaining structural risk pocket where commanders with very thin battle-level confirmation can ride higher-level exposure too far upward.

## Newly Resolved Bare Victory / Defeat Signal

### Main unresolved bucket reduction

Compared with `outputs_cleaned_2026-04-12_genericrecovery_authoritative`:

- unresolved bare `Victory` / `Defeat` rows: `4403 -> 4351` (`-52`)
- unresolved pages: `440 -> 433` (`-7`)
- affected commanders: `3727 -> 3677` (`-50`)

Cumulative reduction since `outputs_cleaned_2026-04-11_hardening_authoritative`:

- unresolved rows: `4503 -> 4351` (`-152`)
- unresolved pages: `445 -> 433` (`-12`)
- affected commanders: `3786 -> 3677` (`-109`)

### Strict known-outcome gain

- strict known-outcome annotated rows: `30341 -> 30393` (`+52`)
- `inferred_generic_actor_title_match` rows: `87 -> 139` (`+52`)

### Newly recovered pages in this pass

All newly recovered rows were resolved conservatively through `inferred_generic_actor_title_match`:

- `United States invasion of Panama`: `12`
- `Greek landing at Smyrna`: `10`
- `Han campaigns against Minyue`: `9`
- `Ottoman expeditions to Morocco`: `8`
- `United States occupation of Nicaragua`: `7`
- `Tang campaigns against Karasahr`: `4`
- `British expedition to Tibet`: `2`

No new broad title-subject heuristic was reintroduced.

## What Was Intentionally Left Unresolved

### Remaining bare-result bucket

The remaining unresolved bare `Victory` / `Defeat` class is still large:

- `4351` commander rows
- `433` pages
- `3677` commanders

This pocket is now dominated by page types that still lack a safe automatic side anchor:

- `189` `war_conflict_article`
- `170` `battle_article`
- `47` `operation_article`
- `27` `campaign_article`

High-level title families still present:

- `war`: `140` pages
- `battle`: `111`
- `civil war`: `27`
- `offensive`: `25`
- `campaign`: `23`
- `siege`: `23`
- `conflict`: `17`
- `rebellion`: `15`
- `insurgency`: `13`
- `coup`: `13`

### Intentionally unresolved for safety

This pass deliberately left cases unresolved when safe actor-to-side mapping was not available without risky inference. The clearest example is:

- `Mongol invasion of India (1306)`

Reason:
- the title subject is `Mongol`
- the belligerent field is `Chagatai Khanate`
- resolving that automatically would require a broader ethnopolitical alias jump, which is not high-precision enough for this stage

Other unmatched pages such as `Invasion of Poland`, `Operation Blue Star`, `Hundred Days`, `Seven Days Battles`, and `Operation Serval` still do not provide a safely unique side anchor from title text alone.

### Coalition / allied ambiguity

This pass did not materially change the separate coalition/allied bucket:

- unresolved coalition/allied rows: `248`
- unresolved coalition/allied pages: `71`
- affected commanders: `235`

That class remains bounded but unresolved.

## Higher-Level Guardrail Impact

The new `thin_battle_anchor` guardrail affects:

- `94` hierarchical-ranked commanders overall
- `1` commander in the hierarchical top `100`
- `1` commander in the hierarchical top `200`

The top-100 affected commander is:

- `Nelson A. Miles`

This is the intended behavior. The guardrail is population-level, but its top-table effect is narrow rather than disruptive.

## Rebuilt Outputs

This pass rebuilt:

- scoring layer outputs
- ranking layer outputs
- interpretive outputs
- dashboard bundle

Dashboard QA was rerun against the rebuilt snapshot and passed in [dashboard_qa_summary.json](C:\Users\gameo\OneDrive\Desktop\test\outputs_cleaned_2026-04-12_victoryhardening_authoritative\dashboard_qa_summary.json).

## Current Trust Judgment

- `hierarchical_weighted` remains the most trustworthy single model.
- `baseline_conservative` remains useful but battle-specialist heavy.
- `hierarchical_full_credit` remains diagnostic-only and should not be treated as a trusted co-equal model.

This pass improved the system in a defensible way:

- more valid signal was recovered from the main remaining ambiguity class
- no broad unsafe heuristic was added
- one real structural higher-level weakness was constrained without disturbing the top plausible leaders

The system is closer to a stable trustable state, but not fully “complete.” The remaining unresolved bare-result pocket is now better characterized as a bounded safety class than as an overlooked easy win.
