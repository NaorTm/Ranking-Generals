# Coalition Hardening Impact Report

## What Was Fixed

This pass fixed a narrow scoring-taxonomy gap inside the coalition/allied unresolved bucket.

The scoring layer now treats these phrases conservatively as `tactical_victory` when the allied side is already uniquely identifiable:

- `Allied operational success`
- `Allied partial success`
- `Allied occupation`

This was implemented in [build_scoring_framework_package.py](C:\Users\gameo\OneDrive\Desktop\test\build_scoring_framework_package.py) as a scoring-specific override. The underlying battle dataset was not rewritten.

## Quantitative Effect

Compared with `outputs_cleaned_2026-04-12_victoryhardening_authoritative`:

- coalition/allied unresolved rows: `248 -> 211` (`-37`)
- unresolved pages: `71 -> 56` (`-15`)
- affected commanders: `235 -> 204` (`-31`)
- strict known-outcome rows: `30393 -> 30430` (`+37`)

Recovered tactical-victory rows added by this pass:

- `37`

## Ranking Impact

### Top-of-table stability

- hierarchical top 10: unchanged
- baseline top 10: unchanged
- battle-only top 10: unchanged
- hierarchical top 100 changed commanders: `0`

This is the strongest signal that the pass improved correctness without destabilizing the trusted top layer.

### Affected ranked commanders

The recovered subclass touched only a small ranked population.

Examples:

- `Walter Krueger`: stayed `56`
- `Charles Macpherson Dobell`: stayed `377`
- `Nelson A. Miles`: stayed `77`
- `Qasem Soleimani`: stayed `44`
- `Douglas MacArthur`: stayed `4`
- `Suleiman the Magnificent`: stayed `1`

The largest rank deltas were all outside the top 100 and modest in absolute analytical importance.

## Dashboard Synchronization

The dashboard was rebuilt and revalidated in the new snapshot.

Confirmed in [dashboard_qa_summary.json](C:\Users\gameo\OneDrive\Desktop\test\outputs_cleaned_2026-04-12_coalitionhardening_authoritative\dashboard_qa_summary.json):

- baseline default view still shows `Jean Lannes`
- hierarchical view still shows `Suleiman the Magnificent`
- charts render
- search works
- row selection works
- console errors: `0`
- page errors: `0`

## Interpretation

This was a successful final-trust-style pass:

- a real recoverable coalition subclass was found
- it was repaired conservatively
- the unresolved coalition bucket shrank materially
- no top-level conclusions were destabilized

## Current Judgment

The coalition/allied class is now in a similar position to the bare `Victory / Defeat` class:

- the meaningful easy recovery has largely been taken
- what remains is mostly structural ambiguity, not a broad missed parser opportunity

If another coalition pass is considered later, it should be limited to:

- separately audited loser-side inference for phrases like `Allied failure`, or
- manual review / curated exceptions

It should not reopen broad coalition-side heuristics.
