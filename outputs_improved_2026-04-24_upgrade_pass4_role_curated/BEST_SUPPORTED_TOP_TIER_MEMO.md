# Best-Supported Top Tier Memo

## Scope

This memo adds an interpretive layer on top of the completed ranking package. It does not rerun crawling, extraction, or framework design. The purpose is to separate the strongest model-robust conclusions from the rankings that remain materially dependent on page-type weighting, commander-credit rules, or broader-eligibility choices.

The memo uses the following outputs as its evidence base:

- `RANKING_RESULTS_BASELINE.csv`
- `RANKING_RESULTS_HIERARCHICAL.csv`
- `RANKING_RESULTS_SENSITIVITY.csv`
- `TOP_COMMANDERS_SUMMARY.csv`

Interpretive heuristics used here:

- `Robust elite core`: the strongest all-model cluster and the safest headline tier.
- `Strong upper tier`: belongs in the serious top discussion, but exact order still depends on model structure.
- `High-confidence upper band`: supported and important, but not strong enough to be merged into the headline core.
- `Model-sensitive band`: worth auditing and discussing, but too structurally sensitive to treat as a secure headline conclusion.

These are interpretive categories layered on top of the existing ranking framework. They are meant to support judgment, not replace the underlying score tables.

## Robust Elite Core

This is the strongest cross-model core in the current package. These commanders stay near the top even when the model changes meaningfully.

- `Alexander Suvorov`: Trust-first v2 rank 1 with high confidence; Top-25 in 6 trusted models and rank spread 3. Rank signature `B0=4, B1=4, HT=1, H=1, HF=1, HE=1, HB=1`.
- `Napoleon Bonaparte`: Trust-first v2 rank 3 with very_high confidence; Top-25 in 6 trusted models and rank spread 4. Rank signature `B0=3, B1=3, HT=3, H=6, HF=5, HE=2, HB=5`.
- `Maurice, Prince of Orange`: Trust-first v2 rank 2 with very_high confidence; Top-25 in 6 trusted models and rank spread 12. Rank signature `B0=8, B1=14, HT=2, H=5, HF=4, HE=3, HB=6`.
- `Jean Lannes`: Trust-first v2 rank 6 with high confidence; Top-25 in 6 trusted models and rank spread 15. Rank signature `B0=2, B1=2, HT=6, H=9, HF=9, HE=13, HB=17`.
- `Louis-Nicolas Davout`: Trust-first v2 rank 7 with high confidence; Top-25 in 6 trusted models and rank spread 14. Rank signature `B0=21, B1=8, HT=7, H=8, HF=44, HE=9, HB=18`.
- `Charles XIV John`: Trust-first v2 rank 9 with high confidence; Top-25 in 6 trusted models and rank spread 7. Rank signature `B0=15, B1=13, HT=9, H=10, HF=8, HE=11, HB=16`.

The clearest current cross-model core is `Alexander Suvorov`, `Napoleon Bonaparte`, `Maurice, Prince of Orange`, `Jean Lannes`, `Louis-Nicolas Davout`, and `Charles XIV John`. These names remain near the top under meaningfully different ranking assumptions, so the exact internal order should not be over-read more than the cluster itself.

## Strong Upper Tier

These commanders perform well enough to belong in the serious discussion, but the model structure affects how high they climb.

### Battle-Specialist Leaders


These cases are not obvious artifacts. The main issue is that battle-only excellence does not necessarily survive once war-level and campaign-level pages are allowed to absorb some of the score.

### Broad But Still Sensitive Contenders


The strongest names in this cluster are `none`. They remain important contenders, but they are not as secure as the robust elite core and still need model-context qualification.

## Model-Sensitive Band

These are the cases where the current data structure appears to be doing too much of the work. They should stay in the audit layer, not in the headline conclusion layer.

- `Ivan Paskevich`: Visible in upper-model results, but the rank remains too model-sensitive for headline trust treatment. Rank signature `B0=46, B1=60, HT=10, H=2, HF=2, HE=7, HB=2`.
- `Takeda Shingen`: Visible in upper-model results, but the rank remains too model-sensitive for headline trust treatment. Rank signature `B0=6, B1=5, HT=32, H=37, HF=38, HE=31, HB=58`.
- `Saladin`: Visible in upper-model results, but the rank remains too model-sensitive for headline trust treatment. Rank signature `B0=40, B1=6, HT=60, H=57, HF=58, HE=45, HB=87`.
- `Babur`: Visible in upper-model results, but the rank remains too model-sensitive for headline trust treatment. Rank signature `B0=106, B1=63, HT=77, H=62, HF=83, HE=53, HB=7`.
- `Douglas MacArthur`: Visible in upper-model results, but the rank remains too model-sensitive for headline trust treatment. Rank signature `B0=44, B1=79, HT=8, H=14, HF=27, HE=22, HB=15`.
- `Petar Bojović`: Ranks well enough to monitor, but higher-level evidence dependence keeps this case out of the headline tiers. Rank signature `B0=NA, B1=263, HT=66, H=20, HF=21, HE=35, HB=8`.
- `Bernard Montgomery`: Ranks well enough to monitor, but higher-level evidence dependence keeps this case out of the headline tiers. Rank signature `B0=113, B1=55, HT=21, H=27, HF=26, HE=28, HB=9`.
- `Abu Ubayda ibn al-Jarrah`: Visible in upper-model results, but the rank remains too model-sensitive for headline trust treatment. Rank signature `B0=10, B1=15, HT=58, H=50, HF=57, HE=73, HB=35`.

The sharpest caution signals in this snapshot are `Ivan Paskevich`, `Takeda Shingen`, `Saladin`, `Babur`, `Douglas MacArthur`, `Petar Bojović`, `Bernard Montgomery`, and `Abu Ubayda ibn al-Jarrah`. These outcomes may still reflect real historical prominence, but the current package does not support treating them as robust all-time elite placements.

## Focused Audit Of Model-Sensitive High-Rank Cases

This is the short list of cases that deserve the most scrutiny before any public-facing interpretation.

- `Ivan Paskevich`: best `2`, worst `60`, range `58`. Visible in upper-model results, but the rank remains too model-sensitive for headline trust treatment. Rank signature `B0=46, B1=60, HT=10, H=2, HF=2, HE=7, HB=2`.
- `Louis XIV`: best `4`, worst `42`, range `38`. High-confidence upper-band commander; rank 11 but not stable enough for the headline core. Rank signature `B0=31, B1=42, HT=11, H=7, HF=7, HE=16, HB=4`.
- `Takeda Shingen`: best `5`, worst `58`, range `53`. Visible in upper-model results, but the rank remains too model-sensitive for headline trust treatment. Rank signature `B0=6, B1=5, HT=32, H=37, HF=38, HE=31, HB=58`.
- `Saladin`: best `6`, worst `87`, range `81`. Visible in upper-model results, but the rank remains too model-sensitive for headline trust treatment. Rank signature `B0=40, B1=6, HT=60, H=57, HF=58, HE=45, HB=87`.
- `Babur`: best `7`, worst `106`, range `99`. Visible in upper-model results, but the rank remains too model-sensitive for headline trust treatment. Rank signature `B0=106, B1=63, HT=77, H=62, HF=83, HE=53, HB=7`.
- `Douglas MacArthur`: best `8`, worst `79`, range `71`. Visible in upper-model results, but the rank remains too model-sensitive for headline trust treatment. Rank signature `B0=44, B1=79, HT=8, H=14, HF=27, HE=22, HB=15`.
- `Petar Bojović`: best `8`, worst `263`, range `255`. Ranks well enough to monitor, but higher-level evidence dependence keeps this case out of the headline tiers. Rank signature `B0=NA, B1=263, HT=66, H=20, HF=21, HE=35, HB=8`.
- `Bernard Montgomery`: best `9`, worst `113`, range `104`. Ranks well enough to monitor, but higher-level evidence dependence keeps this case out of the headline tiers. Rank signature `B0=113, B1=55, HT=21, H=27, HF=26, HE=28, HB=9`.
- `Abu Ubayda ibn al-Jarrah`: best `10`, worst `73`, range `63`. Visible in upper-model results, but the rank remains too model-sensitive for headline trust treatment. Rank signature `B0=10, B1=15, HT=58, H=50, HF=57, HE=73, HB=35`.
- `Amr ibn al-As`: best `11`, worst `53`, range `42`. Visible in upper-model results, but the rank remains too model-sensitive for headline trust treatment. Rank signature `B0=13, B1=11, HT=53, H=36, HF=35, HE=33, HB=22`.
- `Francis Vere`: best `11`, worst `66`, range `55`. Visible in upper-model results, but the rank remains too model-sensitive for headline trust treatment. Rank signature `B0=11, B1=17, HT=62, H=66, HF=81, HE=66, HB=53`.
- `Mahmud Pasha Angelović`: best `12`, worst `57`, range `45`. Visible in upper-model results, but the rank remains too model-sensitive for headline trust treatment. Rank signature `B0=20, B1=21, HT=54, H=52, HF=65, HE=57, HB=12`.

The main audit pattern is clear:

- Some commanders are `battle specialists` in the current dataset. They excel in strict and battle-only models but fall sharply in hierarchical models. The clearest current examples are `none`.
- Some commanders are `hierarchical beneficiaries`. They climb when operations, campaigns, and war pages are counted. `Enver Pasha`, `Ivan Konev`, `Aleksandr Vasilevsky`, `Mahmud II`, and `Nelson A. Miles` fit this pattern to different degrees.
- Some commanders are `credit-rule beneficiaries`. They jump when full presence credit is used. `Qasem Soleimani`, `Saddam Hussein`, `Joseph Stalin`, and `Deng Xiaoping` are the clearest cases.
- A few cases show `unusual attribution fragility` even without the higher-level-page flag. `Belisarius` is the most obvious example; the battle-based signal is strong, but one attribution variant produces a major shock.

## Era-By-Era Elite Shortlist

Requested era buckets are compressed as follows: `modern` here combines `revolutionary_napoleonic`, `long_nineteenth_century`, `world_wars`, and `cold_war`. This keeps the interpretive memo aligned with the requested era structure while preserving the original bucket labels in the supporting CSV.

### Ancient

- `Hannibal` (high_confidence_upper_band): Strong ancient signal with meaningful support, but not yet part of the headline core; rank signature B0=38, B1=16, HT=25, H=28, HF=36, HE=21, HB=55. High-confidence upper-band commander; rank 25 but not stable enough for the headline core.
- `Alexander the Great` (high_confidence_upper_band): Strong ancient signal with meaningful support, but not yet part of the headline core; rank signature B0=57, B1=39, HT=23, H=22, HF=14, HE=23, HB=52. High-confidence upper-band commander; rank 23 but not stable enough for the headline core.

Ancient evidence is meaningful but thinner and more abstraction-sensitive than early modern or modern evidence. The current ancient shortlist is led by `Hannibal` and `Alexander the Great`.

### Medieval

- `Amr ibn al-As` (model_sensitive_band): Useful as an audit case for the era, not as a secure top-tier conclusion; rank signature B0=13, B1=11, HT=53, H=36, HF=35, HE=33, HB=22. The era signal is still model-sensitive; treat this as a provisional inclusion rather than a headline conclusion.
- `Mahmud Pasha Angelović` (model_sensitive_band): Useful as an audit case for the era, not as a secure top-tier conclusion; rank signature B0=20, B1=21, HT=54, H=52, HF=65, HE=57, HB=12. The era signal is still model-sensitive; treat this as a provisional inclusion rather than a headline conclusion.
- `Abu Ubayda ibn al-Jarrah` (model_sensitive_band): Useful as an audit case for the era, not as a secure top-tier conclusion; rank signature B0=10, B1=15, HT=58, H=50, HF=57, HE=73, HB=35. The era signal is still model-sensitive; treat this as a provisional inclusion rather than a headline conclusion.
- `Saladin` (model_sensitive_band): Useful as an audit case for the era, not as a secure top-tier conclusion; rank signature B0=40, B1=6, HT=60, H=57, HF=58, HE=45, HB=87. The era signal is still model-sensitive; treat this as a provisional inclusion rather than a headline conclusion.
- `Genghis Khan` (model_sensitive_band): Useful as an audit case for the era, not as a secure top-tier conclusion; rank signature B0=90, B1=213, HT=19, H=29, HF=10, HE=25, HB=28. The era signal is still model-sensitive; treat this as a provisional inclusion rather than a headline conclusion.

The medieval shortlist is centered on `Amr ibn al-As`, `Mahmud Pasha Angelović`, and `Abu Ubayda ibn al-Jarrah`. These remain powerful cases, but the cross-model stability inside that set still varies materially.

### Early Modern

- `Takeda Shingen` (model_sensitive_band): Useful as an audit case for the era, not as a secure top-tier conclusion; rank signature B0=6, B1=5, HT=32, H=37, HF=38, HE=31, HB=58. The era signal is still model-sensitive; treat this as a provisional inclusion rather than a headline conclusion.
- `Katō Kiyomasa` (model_sensitive_band): Useful as an audit case for the era, not as a secure top-tier conclusion; rank signature B0=36, B1=18, HT=37, H=35, HF=47, HE=44, HB=71. The era signal is still model-sensitive; treat this as a provisional inclusion rather than a headline conclusion.
- `Francis Vere` (model_sensitive_band): Useful as an audit case for the era, not as a secure top-tier conclusion; rank signature B0=11, B1=17, HT=62, H=66, HF=81, HE=66, HB=53. The era signal is still model-sensitive; treat this as a provisional inclusion rather than a headline conclusion.
- `Babur` (model_sensitive_band): Useful as an audit case for the era, not as a secure top-tier conclusion; rank signature B0=106, B1=63, HT=77, H=62, HF=83, HE=53, HB=7. The era signal is still model-sensitive; treat this as a provisional inclusion rather than a headline conclusion.
- `Suleiman the Magnificent` (model_sensitive_band): Useful as an audit case for the era, not as a secure top-tier conclusion; rank signature B0=68, B1=200, HT=83, H=132, HF=75, HE=121, HB=14. The era signal is still model-sensitive; treat this as a provisional inclusion rather than a headline conclusion.
- `Maurice, Prince of Orange` (robust_elite_core): Best-supported early modern candidate; rank signature B0=8, B1=14, HT=2, H=5, HF=4, HE=3, HB=6. Trust-first v2 rank 2 with very_high confidence; Top-25 in 6 trusted models and rank spread 12.

The early modern shortlist is led by `Takeda Shingen`, `Katō Kiyomasa`, `Francis Vere`, `Babur`, and `Suleiman the Magnificent`. Several of the strongest early-modern cases are battle-heavy, so their exact standing still depends on whether the model stays battle-dominant or absorbs more higher-level pages.

### Modern

- `Ivan Paskevich` (model_sensitive_band): Useful as an audit case for the era, not as a secure top-tier conclusion; rank signature B0=46, B1=60, HT=10, H=2, HF=2, HE=7, HB=2. The era signal is still model-sensitive; treat this as a provisional inclusion rather than a headline conclusion.
- `Douglas MacArthur` (model_sensitive_band): Useful as an audit case for the era, not as a secure top-tier conclusion; rank signature B0=44, B1=79, HT=8, H=14, HF=27, HE=22, HB=15. The era signal is still model-sensitive; treat this as a provisional inclusion rather than a headline conclusion.
- `Petar Bojović` (model_sensitive_band): Useful as an audit case for the era, not as a secure top-tier conclusion; rank signature B0=NA, B1=263, HT=66, H=20, HF=21, HE=35, HB=8. The era signal is still model-sensitive; treat this as a provisional inclusion rather than a headline conclusion.
- `Alexander Suvorov` (robust_elite_core): Best-supported modern candidate; rank signature B0=4, B1=4, HT=1, H=1, HF=1, HE=1, HB=1. Trust-first v2 rank 1 with high confidence; Top-25 in 6 trusted models and rank spread 3.
- `Napoleon Bonaparte` (robust_elite_core): Best-supported modern candidate; rank signature B0=3, B1=3, HT=3, H=6, HF=5, HE=2, HB=5. Trust-first v2 rank 3 with very_high confidence; Top-25 in 6 trusted models and rank spread 4.
- `Jean Lannes` (robust_elite_core): Best-supported modern candidate; rank signature B0=2, B1=2, HT=6, H=9, HF=9, HE=13, HB=17. Trust-first v2 rank 6 with high confidence; Top-25 in 6 trusted models and rank spread 15.
- `Louis-Nicolas Davout` (robust_elite_core): Best-supported modern candidate; rank signature B0=21, B1=8, HT=7, H=8, HF=44, HE=9, HB=18. Trust-first v2 rank 7 with high confidence; Top-25 in 6 trusted models and rank spread 14.
- `Charles XIV John` (robust_elite_core): Best-supported modern candidate; rank signature B0=15, B1=13, HT=9, H=10, HF=8, HE=11, HB=16. Trust-first v2 rank 9 with high confidence; Top-25 in 6 trusted models and rank spread 7.

Modern evidence is the richest part of the current package. The most secure modern shortlist is `Ivan Paskevich`, `Douglas MacArthur`, `Petar Bojović`, `Alexander Suvorov`, and `Napoleon Bonaparte`. The late-modern and Cold War end of this bucket is more abstraction-sensitive, so the exact order should stay in the interpretation layer rather than be treated as a clean headline ranking.

### Contemporary


The current contemporary shortlist is `none`. Contemporary results are thin, highly model-sensitive, and often depend on higher-level pages or sparse battle coverage. That means the contemporary shortlist should be treated as a weak provisional signal, not as a settled conclusion.

## Bottom Line

The safest current statement is not a final all-time list. It is that the most defensible all-model core in this snapshot is `Alexander Suvorov`, `Napoleon Bonaparte`, `Maurice, Prince of Orange`, `Jean Lannes`, `Louis-Nicolas Davout`, and `Charles XIV John`.

A second cluster remains historically important but model-sensitive: `none`. Those names belong in the serious discussion, but not yet in a single public-facing headline ranking without stronger qualification.

The weakest claims are the ones driven by higher-level page weighting or by full-credit attribution. Those cases are visible in the package and should remain explicit audit items rather than be smoothed over.
