# Hardening Pass Remaining Issues

## Bounded But Still Unresolved

1. Coalition / allied ambiguity
   - Remaining scope: `242` commander rows on `69` pages.
   - Current judgment: mostly bounded historical-alliance ambiguity, not the earlier global winner-side bug.
   - Residual class: pages where `allied` / `coalition` wording exists but the side texts do not contain a uniquely dominant alliance marker.

2. Bare `Victory` / `Defeat` pages with no safe side mapping
   - Remaining scope: `4503` commander rows on `445` pages.
   - Current judgment: this is now primarily an evidence-limit problem rather than a safe automation problem.
   - Important point: the broad title-side heuristic was removed because it created wrong-side wins on some pages. These rows now remain unknown unless a safer global rule exists.

3. Higher-level exposure dependence
   - The new sparse-evidence guardrail reduced the strongest suspicious pocket materially.
   - Remaining caution cases in the top 30 are still visible, especially `Nelson A. Miles` (rank 19, `higher_level_dependent`) and `Ivan Sirko` (rank 24, low known-outcome share but not higher-level dependent).
   - Current judgment: this is no longer a clear bug; it is a residual model-design risk that should be interpreted through the caution flags.

## What Looks Irreducible Right Now

- Multi-side historical coalition pages with no unique side marker in the extracted belligerent text.
- Bilateral conflict pages with bare `Victory` / `Defeat` labels where the page title names both sides or a territory rather than a unique actor.
- Wikipedia coverage imbalance: commanders with dense operational documentation can still gain scope and centrality faster than commanders with thinner or more fragmented coverage.

## What Looks Potentially Solvable Later

- More advanced subject-actor inference for a subset of generic-result pages, but only if built with stricter actor/territory separation than the rule that was removed here.
- Optional manual audit queues for the highest-impact unresolved `Victory` / `Defeat` pages attached to current top-100 commanders.
- Additional model variants that expose stronger evidence penalties without replacing the current `hierarchical_weighted` baseline.

## Current Trust Position

- `hierarchical_weighted`: strongest single model currently available.
- `baseline_conservative`: useful but battle-specialist heavy.
- `battle_only_baseline`: informative stress test, not a holistic final answer.
- `hierarchical_full_credit`: diagnostic only.

## Bottom Line

The remaining issues are no longer dominated by obvious global bugs or entity leakage. They are now mostly bounded ambiguity classes plus a residual higher-level evidence-design limitation. That is materially stronger than the starting state, but it is not mathematical completeness.
