# Coalition / Allied Residual Audit

## Snapshot Lineage

- Starting snapshot: `outputs_cleaned_2026-04-12_victoryhardening_authoritative`
- Superseding snapshot: `outputs_cleaned_2026-04-12_coalitionhardening_authoritative`

This pass stayed within the analytics stack. It did not alter the battle or commander layers.

## Starting Coalition / Allied Bucket

Before the pass:

- `248` unresolved commander rows
- `71` pages
- `235` affected commanders

These are rows whose `result_raw` contains `coalition`, `allied`, or `anti-...`, but whose outcome remained unresolved.

## Residual Subtype Audit Before Fix

The pre-fix bucket separated into two main families:

### 1. Real side-anchor ambiguity

Examples:

- `Battle of Argos`
- `Battle of Melitaea`
- `Battle of Sagrajas`
- `Pacific War`
- `Siege of Bonn (1689)`

These pages still had coalition/allied language, but the text did not identify one side safely enough for automatic scoring.

### 2. Result-taxonomy gap with already-identified allied side

This was the meaningful recoverable subclass.

It consisted of pages where:

- the result string clearly referred to the allied side, and
- the allied side matched uniquely from belligerents, but
- the result string still normalized to `unknown`

This subclass included:

- `Allied operational success`
- `Allied operational success ...`
- `Allied partial success`
- `Allied occupation`
- `Allied occupation of Jaunde`
- `Allied failure`
- `Allied withdrawal`
- `Allied objectives largely unmet`

## Recoverable Class Decision

I treated only the highest-precision subset as safely recoverable.

### Safely recoverable and fixed

These positive allied phrases were normalized conservatively in the scoring layer:

- `Allied operational success` -> `tactical_victory`
- `Allied partial success` -> `tactical_victory`
- `Allied occupation` -> `tactical_victory`

Why this was safe:

- the side anchor was already uniquely identified by the existing allied-side matcher
- the problem was taxonomy, not winner-side ambiguity
- mapping to `tactical_victory` is conservative and does not over-credit them as full victories

### Intentionally left unresolved

These remained unresolved for safety:

- `Allied failure`
- `Allied withdrawal`
- `Allied objectives largely unmet`
- `Aborted Allied landing`

Reason:

- these are loser-side or mixed/negative phrases
- fixing them safely would require a separate loser-side inference path or a stronger semantics layer
- that is a different change than the narrow scoring-taxonomy repair applied here

## Logic Change Applied

`build_scoring_framework_package.py` now includes a scoring-specific override in `derive_scoring_result_fields()` for the positive allied phrases above.

This was intentionally done in the scoring layer only.

It did **not** rewrite the underlying dataset’s stored `result_type`.

## Quantified Recovery

### Fixed subclass

- `15` pages
- `37` previously unresolved commander rows
- `31` affected commanders

Breakdown:

- `allied_operational_success`: `30` rows
- `allied_partial_success`: `4` rows
- `allied_occupation`: `3` rows

Recovered pages:

- `Operation Harvest Moon`
- `Operation Source`
- `Operation Byrd`
- `Operation Pipestone Canyon`
- `Operation Toan Thang II`
- `Operation Toan Thang III`
- `Operation Chronicle`
- `Operation Jackstay`
- `Operation Coronado IX`
- `Operation Truong Cong Dinh`
- `Operation Toan Thang IV`
- `Second Battle of Jaunde`
- `Operation Coronado X`
- `Operation Coronado XI`
- `Operation McLain`

### Post-fix coalition bucket

After the pass:

- unresolved coalition/allied rows: `248 -> 211`
- unresolved pages: `71 -> 56`
- affected commanders: `235 -> 204`

## Residual Coalition / Allied Bucket After Fix

What remains now is mostly structural ambiguity, not a missed easy recovery class.

Current residual subtype breakdown:

### 1. Allied label without allied-side anchor

- `29` pages
- `109` unresolved commander rows

Examples:

- `Battle of Ambur`
- `Battle of Argos`
- `Battle of Dettingen`
- `Battle of Red Cliffs`
- `Pacific War`
- `Operation Plunder`

These are pages where `Allied victory` appears, but the page belligerents do not expose a clean unique allied-side marker.

### 2. Coalition label without coalition-side anchor

- `10` pages
- `38` unresolved commander rows

Examples:

- `Battle of Caesar's Camp`
- `Battle of Famars`
- `Battle of Melitaea`
- `Battle of Sagrajas`
- `Siege of Genoa (1814)`

These pages name a coalition outcome, but the coalition identity is not safely recoverable from the page-side text alone.

### 3. Mostly resolved pages with only multi-side commander rows remaining

- `4` pages
- `5` unresolved commander rows

Pages:

- `Burma campaign`
- `Operation Torch`
- `War of the Sixth Coalition`
- `Eastern Front (World War II)`

These pages are no longer page-level inference problems. Their residual rows are row-level `multiple_sides` ambiguity cases.

### 4. Negative or mixed allied phrase without safe auto-mapping

- `4` pages
- `9` unresolved commander rows

Pages:

- `Battle of Mission Ridge–Brigade Hill`
- `Landing at Barcelona (1704)`
- `Operation Abercrombie`
- `Operation Title`

These are the phrases intentionally left unresolved in this pass.

### 5. Citation-fused coalition strings still side-ambiguous

- `3` pages
- `8` unresolved commander rows

Pages:

- `Battle of Limonest`
- `Battle of Lüneburg`
- `Siege of Tarifa (1812)`

Even if their citation-fused strings are sanitized, the coalition-side anchor is still not uniquely safe.

### 6. Anti-target phrase still ambiguous

- `2` pages
- `6` unresolved commander rows

Pages:

- `Battle of Northern Henan`
- `Third Javanese War of Succession`

These still require interpretation beyond the current safe automatic rules.

### 7. Other structural ambiguity

- `3` pages
- `34` unresolved commander rows

Pages:

- `Battle of Großbeeren`
- `Campaign against Dong Zhuo`
- `Mediterranean campaign of 1798`

## Trust Judgment

The meaningful recoverable class inside the coalition bucket was real, but small and bounded. It has now been taken.

What remains is mostly:

- no safe side anchor
- citation/noise fused strings whose side still remains ambiguous
- row-level `multiple_sides` ambiguity
- negative or mixed outcome phrases requiring a different inference path

## Recommendation

I do **not** recommend broadening coalition/allied heuristics further at this stage.

The next automatic step, if any, should be extremely narrow:

- possibly a separate loser-side inference path for phrases like `Allied failure`
- only if it is implemented with the same precision standard and separately audited

Otherwise, the coalition/allied bucket is now mostly bounded and should be treated similarly to the exhausted bare `Victory / Defeat` class: limited further gains, rising trust risk.
