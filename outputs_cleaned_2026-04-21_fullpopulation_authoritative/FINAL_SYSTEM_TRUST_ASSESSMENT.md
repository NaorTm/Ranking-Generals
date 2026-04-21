# Final System Trust Assessment

## Scope

This is the closure assessment for the current authoritative analytics snapshot:

- `outputs_cleaned_2026-04-21_fullpopulation_authoritative`

It does not restart the project, replace the cleaned battle or commander layers, or claim exact-order historical certainty. It consolidates the correction history, full-population review, and final trust judgment under the current conservative precision standard.

## Final Bottom Line

The system is not perfect, and it is not mathematically complete. It is now, however, strong enough to be treated as a globally defensible conservative ranking framework with explicit confidence limits under the current trust standard.

That means:

- tiers should be read before exact rank
- confidence labels are part of the primary interpretation
- exact adjacent ordering remains unsettled in some cases
- the remaining weakness is visible ambiguity, not hidden breakage

That judgment rests on five facts:

1. the major global failure modes have been fixed
2. the major ambiguity buckets have been reduced conservatively
3. the remaining unresolved classes are now mostly bounded structural ambiguity, not broad missed easy fixes
4. the cleaned battle and commander layers are stable and auditable
5. the top of the trusted ranking layer remained stable through multiple correction passes rather than changing chaotically

## What Global Bugs Were Fixed

Across the correction lineage from `outputs_cleaned_2026-04-10_authoritative` through the current snapshot, the following ranking-impacting global problems were fixed.

### 1. `anti-X` winner-side inversion bug

Old failure:

- phrases such as `Anti-Swedish coalition victory` could be interpreted as a Swedish victory

Fix:

- negated-target outcome logic now treats `anti-X` and similar target phrasing as loser-side evidence first

Measured effect in the first rank-fix pass:

- `171` anti-target annotated rows reviewed
- `137` rows changed outcome
- `42` wrong `victory -> defeat` flips corrected
- `45` wrong `defeat -> victory` flips corrected
- `31` rows moved `unknown -> known`
- `19` rows moved `known -> unknown` because the corrected logic refused to overclaim

### 2. Unknown outcomes polluting split-credit denominators

Old failure:

- `unknown` outcomes still sat in split-credit denominators as zero-value evidence instead of missing evidence

Fix:

- unknown outcomes no longer contribute split outcome factor

Validated after the fix:

- rows where `unknown` still contributed non-zero split outcome factor: `0`

### 3. Defeat dilution under strict same-side split credit

Old failure:

- same-side credit used `1 / side_count`, which washed out major defeats on crowded pages

Fix:

- same-side split changed to `1 / sqrt(side_count)`

This remained conservative but made crowded defeats materially count again.

### 4. Unsafe broad title-subject outcome inference

Old failure:

- generic subject-title matching could assign wins to the wrong side on pages where the title named a place, campaign theater, or conflict label rather than a belligerent

Fix:

- the unsafe broad subject-title rule was removed

Measured end state after removal:

- `subject_title_match` rows: `0`

### 5. Citation-fused and sanitized-result scoring failures

Old failure:

- some result strings were not being scored correctly because of citation-fused text and result-sanitization failures

Fix:

- scoring-only result sanitization and fallback normalization were added

Measured effect in the global trust pass:

- fallback sanitization affected `322` pages, `1,546` commander rows, and `1,254` commanders
- known-outcome rows improved from `28,067` to `29,311`

### 6. `NaN -> "nan"` normalization leakage

Old failure:

- missing values could leak into the scoring layer as literal `"nan"` strings

Fix:

- normalization was tightened in the scoring pipeline

### 7. Non-person leakage into scoring and ranking

Old failure:

- non-person entities were still being ranked or contributing to scoring inputs

Fix:

- global scoring exclusions were tightened repeatedly, removing media outlets, agencies, missions, groups, and similar non-person entities from ranking inputs

Measured effect across later passes:

- obvious non-person identities in the ranked baseline/hierarchical tables: `1 -> 0`
- confirmed removed examples included `Al-Masdar News`, `Newsweek`, `Kommersant`, `RBK Group`, `Wounded in action`, `Channel NewsAsia`, `Federal Investigation Agency`, and similar entities

### 8. Coalition/allied positive-taxonomy gap

Old failure:

- some positive allied phrases had a uniquely identifiable allied side but still normalized to `unknown`

Fix:

- narrow scoring-only overrides were added for:
  - `Allied operational success`
  - `Allied partial success`
  - `Allied occupation`

Measured effect in the coalition hardening pass:

- `37` unresolved commander rows recovered across `15` pages and `31` commanders

### 9. Higher-level sparse-evidence structural inflation

Old failure:

- war/campaign/operation-heavy commanders with thin confirmed battle evidence could sometimes rank too high

Fixes:

- sparse higher-level evidence guardrail
- later thin battle anchor guardrail
- `hierarchical_full_credit` downgraded to diagnostic-only status

This was a model-design hardening step rather than a data bug fix.

## What Ambiguity Classes Were Reduced

### Coalition / allied ambiguity

This class was reduced in several passes and is now mostly exhausted for safe automation.

Row-level reduction:

- `1,912` unresolved commander rows after the first rank-fix pass
- `211` unresolved commander rows in the current snapshot
- net reduction: `1,701` rows (`-88.9%`)

Page-level reduction:

- `332` unresolved pages in the second-pass audit stage
- `56` unresolved pages in the current snapshot
- net reduction: `276` pages (`-83.1%`)

Commander-level reduction where directly measured late in the process:

- `235 -> 204` affected commanders in the final coalition hardening pass

Important point:

- the recoverable subclasses were taken conservatively
- the remaining coalition bucket is now mostly alliance-label pages without a unique side anchor, negative/mixed allied phrases, or row-level multiple-side ambiguity

### Bare one-sided `Victory` / `Defeat`

This class was reduced conservatively through actor-led recovery rules and then closed for automation after residual audit.

Row-level reduction:

- `4,520` unresolved commander rows before generic-result hardening
- `4,351` unresolved commander rows in the current snapshot
- net reduction: `169` rows (`-3.7%`)

Page-level reduction:

- `445` unresolved pages before generic-result hardening
- `433` unresolved pages in the current snapshot
- net reduction: `12` pages (`-2.7%`)

Why the reduction is smaller:

- unlike the coalition class, the residual bare-result bucket is dominated by structurally ambiguous war/conflict and event pages with no unique side anchor
- the residual audit showed no meaningful high-precision automatic recovery class left

### Higher-level evidence risk pocket

This class was not “resolved” in the same way as text ambiguity, but it was materially reduced as a ranking-distortion risk.

Examples of meaningful downward corrections during hardening:

- `Qasem Soleimani`: hierarchical `17 -> 45`
- `Nelson A. Miles`: hierarchical `19 -> 77` after later guardrails
- `Suhayl al-Hasan`: hierarchical `52 -> 94`
- `Valery Gerasimov`: hierarchical `94 -> 156`

This is the main reason the current hierarchical table is materially more trustworthy than earlier snapshots.

## What Residual Unresolved Classes Remain

The remaining unresolved classes are now mostly bounded structural ambiguity rather than broad correctable bugs.

### 1. Bare `Victory` / `Defeat` pages with no safe side anchor

Current residual size:

- `433` pages
- `4,351` unresolved commander rows
- `3,677` affected commanders

Residual subtype breakdown from the residual audit:

- `war_conflict_no_unique_side_anchor`: `209` pages, `3,062` rows
- `event_title_no_unique_side_anchor`: `152` pages, `822` rows
- `operation_or_offensive_no_actor_anchor`: `44` pages, `283` rows
- `campaign_or_expedition_no_actor_anchor`: `27` pages, `179` rows
- `alias_or_ethnopolitical_inference_required`: `1` page, `5` rows

Trust judgment:

- closed for automatic recovery under the current precision standard

### 2. Coalition / allied ambiguity

Current residual size:

- `56` pages
- `211` unresolved commander rows
- `204` affected commanders

Residual subtype breakdown:

- `allied_label_without_allied_side_anchor`: `29` pages, `109` rows
- `coalition_label_without_coalition_side_anchor`: `10` pages, `38` rows
- `mostly_resolved_page_with_only_multi_side_rows_remaining`: `4` pages, `5` rows
- `negative_or_mixed_allied_phrase_without_safe_auto_mapping`: `4` pages, `9` rows
- `citation_fused_coalition_victory_still_side_ambiguous`: `3` pages, `8` rows
- `anti_target_phrase_still_ambiguous`: `2` pages, `6` rows
- `other_structural_ambiguity`: `3` pages, `34` rows

Trust judgment:

- also effectively closed for broad automatic recovery
- any further work should be narrow, explicitly audited, and probably manual or curated

### 3. Higher-level evidence design limitation

This is still a real interpretive limitation.

Current state:

- the strongest suspicious pocket was reduced materially
- it is no longer an obvious global bug
- it remains a model-design limitation tied to Wikipedia page-density imbalance and higher-level exposure

This affects interpretation more than raw execution correctness.

### 4. Coverage imbalance in source material

This remains irreducible at the current automation layer.

Effect:

- commanders with dense documentation on wars, campaigns, and operations can accumulate scope and centrality faster than commanders whose records are fragmented across thinner or less normalized pages

This is a real residual limitation and should be stated plainly rather than hidden.

## Current Trusted Model Hierarchy

### Primary trustworthy model

- `hierarchical_weighted`

Why:

- it survived multiple correction passes without chaotic top-level instability
- it now incorporates the strongest available balance of outcomes, scope, temporal span, centrality, and higher-level exposure
- the major known bug classes affecting it were corrected
- its remaining weaknesses are mostly bounded and interpretable rather than silent failure modes

Current top 10 in the latest snapshot:

1. `Suleiman the Magnificent`
2. `Alexander Suvorov`
3. `Napoleon Bonaparte`
4. `Douglas MacArthur`
5. `Louis XIV`
6. `Charles XIV John`
7. `Louis-Nicolas Davout`
8. `Jean Lannes`
9. `Babur`
10. `Subutai`

### Secondary models

- `baseline_conservative`
- `battle_only_baseline`
- `hierarchical_equal_split`
- `hierarchical_broader_eligibility`

How to use them:

- as comparative views, sensitivity checks, and stress tests
- not as the single final headline answer

Important caveats:

- `baseline_conservative` remains battle-specialist heavy
- `battle_only_baseline` is useful for battle-only stress testing, not for holistic final judgment
- `hierarchical_equal_split` and `hierarchical_broader_eligibility` are useful sensitivity views, not the primary trust anchor

Current top 10 in `baseline_conservative`:

1. `Jean Lannes`
2. `Napoleon Bonaparte`
3. `Alexander Suvorov`
4. `Takeda Shingen`
5. `Khalid ibn al-Walid`
6. `Alexander Farnese, Duke of Parma`
7. `Louis-Gabriel Suchet`
8. `Sebastien Le Prestre, Marquis of Vauban`
9. `Maurice, Prince of Orange`
10. `Louis-Nicolas Davout`

### Diagnostic only

- `hierarchical_full_credit`

Why:

- it remains structurally too permissive
- it is useful for stress-testing credit-attribution sensitivity
- it should not be treated as a co-equal trust vote in final interpretation

## What Still Materially Affects Interpretation

The framework is defensible, but several limitations still matter.

### 1. Exact ordering inside model-sensitive bands

The system is strongest at identifying robust cores, stable top groups, and caution cases.

It is weaker at defending:

- exact fine-grained ordering inside dense tiers
- narrow rank differences among adjacent commanders

### 2. Higher-level heavy commanders still require interpretation

Even after guardrails, commanders with strong war/campaign/operation exposure and thinner battle anchoring still need caution.

This no longer invalidates the model, but it does affect confidence in some placements.

### 3. Coverage imbalance remains real

Wikipedia page density is not historically neutral.

That means the framework is better interpreted as:

- a rigorously cleaned, conservative, multi-model ranking framework built on available structured evidence

not as:

- a fully complete measurement of all military performance in history

### 4. Residual ambiguity was intentionally left unresolved for safety

This is a strength, not a weakness in execution.

The system now prefers:

- conservative missingness

over:

- aggressive heuristic guessing

That improves trust, even though it lowers nominal coverage.

## Stability Checks Supporting Final Trust

The correction passes increasingly hardened the system without destabilizing the trusted top layer.

Evidence:

- the hierarchical leader remained `Suleiman the Magnificent`
- the hierarchical top 10 stayed unchanged through the final coalition hardening pass
- the battle-only top 10 stayed unchanged through that pass
- the baseline top 10 stayed unchanged through that pass
- dashboard QA passed in the current snapshot
- no obvious non-person entities remain in the trusted ranking layer
- the major suspicious hierarchical inflation cases were pushed down materially

Current dashboard QA state from the latest snapshot:

- charts render
- overview renders
- search works
- row selection works
- console errors: `0`
- page errors: `0`

## Current Scale Of The Final Framework

In the current authoritative snapshot:

- annotated commander-engagement rows: `60,259`
- strict known-outcome rows: `30,430`
- `baseline_conservative` cohort: `719`
- `battle_only_baseline` cohort: `2,255`
- `hierarchical_weighted` cohort: `1,366`
- `hierarchical_broader_eligibility` cohort: `1,437`

These are not toy-table outputs. The framework is now operating on a large cleaned evidence base with audited residual ambiguity.

## Final Trust Conclusion

Under the current trust standard, the system is now stable enough to be treated as the project’s defensible final ranking framework.

That does **not** mean:

- the rankings are perfect
- every row is resolved
- every remaining ambiguity is solved
- exact adjacent ranks should be over-read

It **does** mean:

- the major global bugs have been fixed
- the major ambiguity classes have been reduced conservatively
- the remaining unresolved classes are explicitly bounded and auditable
- the primary model is interpretable and materially more trustworthy than earlier snapshots
- the dashboard and downstream outputs are synchronized with the corrected logic

Final operating judgment:

- use `hierarchical_weighted` as the primary model
- use the other non-diagnostic models as sensitivity and comparison views
- treat `hierarchical_full_credit` as diagnostic only
- interpret robust cores and stable top groups with confidence
- interpret fine-grained ordering and higher-level-heavy cases with caution

That is strong enough to close the framework as a credible final system under the present methodology.
