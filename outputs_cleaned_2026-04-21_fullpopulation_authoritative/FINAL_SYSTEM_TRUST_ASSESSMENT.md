# Final System Trust Assessment

## Scope

This is the current closure assessment for:

- `outputs_cleaned_2026-04-21_fullpopulation_authoritative`

It reflects the rebuilt scoring, ranking, interpretive, dashboard, and QA outputs after the reliability audit fixes made on `2026-04-24`.

## Current Bottom Line

The system is usable as a conservative, auditable ranking framework, but it should be read as tiers and confidence bands first, exact rank second.

The current framework is more reliable than the previous generated snapshot because two scoring-order defects were fixed:

- unknown same-side rows no longer dilute known-outcome split-credit denominators
- commander verification overrides now apply before page weights are computed

Those fixes materially changed the hierarchy. This is expected: the older hierarchy was partly using rows that the verification layer had already marked out of strict ranking eligibility.

## Current Headline Model

Use `hierarchical_trust_v2` as the primary trust-first headline view.

Use these as sensitivity views:

- `hierarchical_weighted`
- `baseline_conservative`
- `battle_only_baseline`
- `hierarchical_equal_split`
- `hierarchical_broader_eligibility`

Treat `hierarchical_full_credit` as diagnostic only.

## Current Trust-First Top 10

1. `Alexander Suvorov`
2. `Maurice, Prince of Orange`
3. `Napoleon Bonaparte`
4. `Subutai`
5. `Sébastien Le Prestre, Marquis of Vauban`
6. `Jean Lannes`
7. `Louis-Nicolas Davout`
8. `Douglas MacArthur`
9. `Charles XIV John`
10. `Ivan Paskevich`

The most defensible headline statement is the robust core, not a hard exact-order claim. The current robust elite core is:

- `Alexander Suvorov`
- `Napoleon Bonaparte`
- `Maurice, Prince of Orange`
- `Jean Lannes`
- `Louis-Nicolas Davout`
- `Charles XIV John`

## Current Scale

- retained pages: `13,492`
- annotated commander-engagement rows: `60,512`
- strict known-outcome rows: `26,364`
- ranked commanders appearing in dashboard/sensitivity data: `2,541`
- `baseline_conservative` cohort: `781`
- `battle_only_baseline` cohort: `2,389`
- `hierarchical_trust_v2` cohort: `1,067`
- `hierarchical_weighted` cohort: `1,067`
- `hierarchical_broader_eligibility` cohort: `1,321`

## Validation Results

Current validation status:

- model regression checks: pass
- non-person leakage check: pass
- top-10 trust/weighted overlap check: pass with `9` overlapping names
- robust-core higher-level fragility check: pass
- dashboard browser QA: pass
- dashboard console errors: `0`
- dashboard page errors: `0`

## Remaining Limits

The system is not a final mathematical truth about all commanders. The remaining limits are explicit:

- unresolved outcomes remain missing evidence rather than guessed evidence
- higher-level pages can still affect broad-scope commanders
- Wikipedia source density is uneven across eras and regions
- exact adjacent ranks inside dense bands remain weaker than tier placement
- historically important model-sensitive cases should stay in the audit layer

## Final Operating Judgment

The current project state is structurally consistent and dashboard-verified. It is reliable enough for a conservative published framework if interpretation stays trust-first:

- lead with `hierarchical_trust_v2`
- discuss robust tiers before exact ranks
- use sensitivity models to explain movement
- keep model-sensitive cases visibly qualified
