# Generic Result Hardening Impact Report

## Model-Level Impact

### Baseline conservative

- cohort size: unchanged at `719`
- rank changes: `0`
- leader: unchanged, `Jean Lannes`
- top 10: unchanged

Interpretation:
- this pass did not affect the battle-only baseline layers materially, which is expected because the recovered pages were mostly outside the baseline’s battle-heavy eligible core and the new guardrail applies only to hierarchical models.

### Battle-only baseline

- cohort size: unchanged at `2255`
- rank changes: `0`
- leader: unchanged, `Khalid ibn al-Walid`
- top 10: unchanged

Interpretation:
- same conclusion as baseline conservative: the pass did not perturb the battle-only table.

### Hierarchical weighted

- cohort size: unchanged at `1366`
- leaders: unchanged
- top 10: unchanged
- commanders with rank changes: `1251`

Top 10 remained:

1. Suleiman the Magnificent
2. Alexander Suvorov
3. Napoleon Bonaparte
4. Douglas MacArthur
5. Louis XIV
6. Charles XIV John
7. Louis-Nicolas Davout
8. Jean Lannes
9. Babur
10. Subutai

Interpretation:
- the top of the table stayed stable
- the impact was concentrated below the very top and in the structural-risk pocket
- this is the right shape for a trust-hardening pass

## Commander-Level Impact

### Nelson A. Miles

- hierarchical rank: `19 -> 77`
- cause: `thin_battle_anchor` guardrail
- post-fix flags: `higher_level_dependent | thin_battle_anchor`

Interpretation:
- this is the clearest intended correction in the top 100
- his prior placement depended too heavily on higher-level pages relative to battle-level confirmed outcomes

### Qasem Soleimani

- hierarchical rank: `45 -> 44`
- effectively unchanged
- flag remains: `sparse_higher_level_evidence`

Interpretation:
- this pass did not artificially push him down
- the residual caution here is still primarily evidence sparsity, not this particular bare-result class

### Valery Gerasimov

- hierarchical rank: unchanged at `93`
- flags remain: `higher_level_dependent | higher_level_low_evidence_combo | sparse_higher_level_evidence`

Interpretation:
- the pass did not change his structural profile materially
- his remaining caution remains real, but he is no longer a top-tier distortion

### Douglas MacArthur

- hierarchical rank: unchanged at `4`
- no caution flags

Interpretation:
- the guardrail did not hit the high-evidence mixed-profile commanders
- this is an important validation that the new rule is narrow rather than blunt

### Other notable effects

The largest rank drops were concentrated among commanders with very thin battle anchoring and high higher-level dependence, including:

- Claude Auchinleck: `420 -> 552`
- Selim II: `447 -> 576`
- Deng Ai: `524 -> 651`
- Valerian Frolov: `396 -> 523`
- Khalid bin Sultan Al Saud: `366 -> 491`
- Nicholas I of Russia: `373 -> 498`
- Catherine the Great: `197 -> 303`

These are not arbitrary result changes. They are the direct effect of constraining structurally weak hierarchical profiles.

## Top-Rank Plausibility Recheck

### Hierarchical top 20

The top 20 remained broadly stable and materially more defensible than earlier snapshots. The leading names are still dominated by high-evidence commanders rather than thin higher-level artifacts.

Remaining cautions inside the top 20 are limited:

- `Petar Bojović` remains flagged `higher_level_dependent` at rank `16`

That is a caution flag, not a blocker. The more problematic thin-anchor case, `Nelson A. Miles`, is no longer near the top 20.

### Global trust read

- No non-person leaks reappeared.
- No coalition/allied regression was introduced.
- No top-leader turnover occurred from this pass.
- The hierarchical leader remained `Suleiman the Magnificent`.

## Dashboard Synchronization

The dashboard was rebuilt and revalidated against the new snapshot.

Confirmed in [dashboard_qa_summary.json](C:\Users\gameo\OneDrive\Desktop\test\outputs_cleaned_2026-04-12_victoryhardening_authoritative\dashboard_qa_summary.json):

- all major panels render
- baseline default view matches `Jean Lannes`
- hierarchical view matches `Suleiman the Magnificent`
- search works
- era and page-type filtering work
- minimum-engagement filtering works
- row selection works
- side-by-side comparison works
- console errors: `0`
- page errors: `0`

## Final Judgment After This Pass

- The remaining bare `Victory` / `Defeat` ambiguity class is smaller and better bounded.
- The newly added rules recovered valid signal without reintroducing unsafe broad inference.
- The new hierarchical guardrail corrected a real trust weakness without destabilizing the top plausible leaders.

Current judgment:

- `hierarchical_weighted` is still the strongest single model.
- The system is now closer to a stable and defensible final state.
- Remaining unresolved issues are increasingly concentrated in classes that are genuinely hard to solve safely, rather than in obvious missed corrections.
