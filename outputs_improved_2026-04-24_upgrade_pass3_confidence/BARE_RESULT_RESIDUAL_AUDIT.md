# Bare Result Residual Audit

## Scope

This audit reviews the remaining unresolved bare `Victory` / `Defeat` class in [outputs_cleaned_2026-04-12_victoryhardening_authoritative](C:\Users\gameo\OneDrive\Desktop\test\outputs_cleaned_2026-04-12_victoryhardening_authoritative).

The objective was not to add more heuristics. The objective was to determine whether the remaining bucket still contains meaningful high-precision recoverable signal, or whether it is now mostly irreducible under a conservative trust standard.

Current residual size:

- `433` pages
- `4351` unresolved commander rows
- `3677` affected commanders

## Page-Type Breakdown

- `189` `war_conflict_article`
- `170` `battle_article`
- `47` `operation_article`
- `27` `campaign_article`

## Residual Subtype Breakdown

The remaining pages were partitioned into conservative residual classes.

### 1. War/conflict titles with no unique side anchor

- `209` pages
- `3062` unresolved commander rows
- `48.3%` of remaining pages
- `70.4%` of remaining unresolved commander rows

Typical examples:

- `Taliban insurgency`
- `Mexican–American War`
- `Hussite Wars`
- `French Revolutionary Wars`
- `Iraqi–Kurdish conflict`
- `Afghan Civil War (1989–1992)`

Why these remain unresolved:

- the title names the conflict, not the winning side
- the result is only `Victory` or `Defeat`
- there is no unique side anchor in the title text
- resolving them would require broader historical interpretation, not safe string-based inference

### 2. Event titles with no unique side anchor

- `152` pages
- `822` unresolved commander rows
- `35.1%` of remaining pages
- `18.9%` of remaining unresolved commander rows

Typical examples:

- `Battle of the Bulge`
- `1991 Soviet coup attempt`
- `Hundred Days`
- `Battle of Vukovar`
- `Battle of Aleppo (2012–2016)`
- `Battle of Kabul (1992–1996)`

Why these remain unresolved:

- the title identifies the event, location, or period, not the side
- a generic `Victory` or `Defeat` string is not enough to assign the winning side safely

### 3. Operation/offensive titles with no actor anchor

- `44` pages
- `283` unresolved commander rows
- `10.2%` of remaining pages
- `6.5%` of remaining unresolved commander rows

Typical examples:

- `Dnieper–Carpathian offensive`
- `Tet Offensive`
- `Belgrade offensive`
- `1975 spring offensive`
- `Second Jassy–Kishinev offensive`

Why these remain unresolved:

- the apparent “subject” is usually a location, region, season, or code name
- those tokens are not side anchors
- recovering them safely would require operational-history interpretation

### 4. Campaign/expedition titles with no actor anchor

- `27` pages
- `179` unresolved commander rows
- `6.2%` of remaining pages
- `4.1%` of remaining unresolved commander rows

Typical examples:

- `Northern Expedition`
- `Long Expedition`
- `Puerto Rico campaign`
- `Mongol campaigns in Central Asia`
- `Kabul Expedition (1842)`

Why these remain unresolved:

- the title is generic, geographic, or historically named rather than side-anchored
- the page result string is too thin to resolve the winner safely

### 5. Alias or ethnopolitical inference required

- `1` page
- `5` unresolved commander rows
- `0.2%` of remaining pages
- `0.1%` of remaining unresolved commander rows

Page:

- `Mongol invasion of India (1306)`

Why it remains unresolved:

- the title subject is `Mongol`
- the belligerent field is `Chagatai Khanate`
- resolving that automatically would require an ethnopolitical alias jump
- that is historically loaded and not safe enough for a global automatic rule

## Residual Actor-Subject Audit

I specifically checked whether any pages still expose a title subject that looks like a recoverable actor.

Result:

- only `26` residual pages still produce any extracted title “subject”
- those `26` pages account for only `169` unresolved commander rows

Breakdown of those `26` pages:

- `25` pages / `164` rows are not true actor-side cases at all
- their extracted subject is a place, region, season, or time label:
  - `Dnieper–Carpathian`
  - `Belgrade`
  - `Tet`
  - `Spring 1945`
  - `Southern Syria`
  - `Qalamoun`
- `1` page / `5` rows requires an ethnopolitical alias jump:
  - `Mongol invasion of India (1306)`

This is the key finding of the audit. The residual bucket is not hiding a large missed actor-led recovery class.

## What Is Safely Recoverable vs Not

### Safely recoverable pages still missed

My current judgment is:

- `0` pages are clearly still safely recoverable under the current precision standard
- `0` remaining pages expose a unique side anchor that is both textually present and methodologically safe to resolve automatically

### Possibly recoverable only with broader interpretation

These pages are not safely recoverable by conservative automatic rules:

- `Mongol invasion of India (1306)`:
  requires ethnopolitical alias mapping
- geographic/seasonal offensives such as:
  - `Belgrade offensive`
  - `Tet Offensive`
  - `Dnieper–Carpathian offensive`
  - `1975 spring offensive`
  these require operational-history inference, not textual side anchoring

### Permanently unresolved for trust reasons

The large majority of the residual bucket should remain unresolved automatically unless the project accepts a materially lower precision standard.

That includes:

- most war/conflict pages with bare `Victory` / `Defeat`
- most battle/siege/event titles without a side in the title
- most named operations or offensives whose title subject is a place or codename rather than a belligerent

## Proportion of Remaining Rows by Residual Class

- `war_conflict_no_unique_side_anchor`: `3062` rows (`70.4%`)
- `event_title_no_unique_side_anchor`: `822` rows (`18.9%`)
- `operation_or_offensive_no_actor_anchor`: `283` rows (`6.5%`)
- `campaign_or_expedition_no_actor_anchor`: `179` rows (`4.1%`)
- `alias_or_ethnopolitical_inference_required`: `5` rows (`0.1%`)

This matters because it shows the remaining bucket is dominated by structurally ambiguous cases, not by a small overlooked parser gap.

## Trust-Risk Assessment

At this point, additional global automatic recovery on the bare-result bucket is unlikely to be worth the trust risk.

Reason:

- the main remaining class is not “actor-led pages we forgot to support”
- it is mostly pages whose title text does not name the winner side
- further automatic recovery would require broader historical interpretation, alias expansion, or event-specific hand tuning

That would move the system away from conservative auditable inference and back toward result-shaping heuristics.

## Recommendation

### Recommendation: stop automatic bare-result recovery here

I do **not** recommend another global automatic recovery pass on the bare `Victory` / `Defeat` bucket.

The evidence from this audit supports:

- the remaining residual class is mostly irreducible under a high-precision standard
- the amount of safely recoverable signal still left is negligible
- further automation would increase trust risk faster than it would improve coverage

### Recommended next priority

Move next to the coalition/allied unresolved bucket.

Reason:

- it is smaller and more bounded
- it is more likely to contain recoverable structured signal
- it remains a more plausible source of systematic ranking distortion than the now-audited bare-result residual class

### If the bare-result class is ever revisited again

It should be done only as:

- page-specific manual review, or
- narrowly curated alias rules with explicit historical justification and separate audit logging

It should not be reopened through broader automatic heuristics.

## Bottom Line

The residual `433`-page bare-result bucket is now best understood as a bounded trust-preserving unresolved class, not as a large missed recovery opportunity.

That means the current stopping point on this class is methodologically justified.
