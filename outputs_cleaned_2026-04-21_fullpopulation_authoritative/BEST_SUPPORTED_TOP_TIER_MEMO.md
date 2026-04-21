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

- `Alexander Suvorov`: Trust-first v2 rank 1 with high confidence; Top-25 in 6 trusted models and rank spread 4. Rank signature `B0=4, B1=5, HT=1, H=1, HF=1, HE=3, HB=1`.
- `Napoleon Bonaparte`: Trust-first v2 rank 3 with very_high confidence; Top-25 in 6 trusted models and rank spread 5. Rank signature `B0=3, B1=3, HT=3, H=2, HF=2, HE=1, HB=6`.
- `Jean Lannes`: Trust-first v2 rank 10 with high confidence; Top-25 in 6 trusted models and rank spread 17. Rank signature `B0=2, B1=2, HT=10, H=11, HF=12, HE=17, HB=19`.
- `Maurice, Prince of Orange`: Trust-first v2 rank 12 with very_high confidence; Top-25 in 6 trusted models and rank spread 7. Rank signature `B0=7, B1=14, HT=12, H=13, HF=13, HE=10, HB=7`.
- `Charles XIV John`: Trust-first v2 rank 6 with high confidence; Top-25 in 6 trusted models and rank spread 11. Rank signature `B0=15, B1=13, HT=6, H=9, HF=8, HE=5, HB=16`.
- `Subutai`: Trust-first v2 rank 7 with high confidence; Top-25 in 5 trusted models and rank spread 24. Rank signature `B0=14, B1=28, HT=7, H=8, HF=9, HE=7, HB=4`.
- `Louis-Nicolas Davout`: Trust-first v2 rank 9 with high confidence; Top-25 in 6 trusted models and rank spread 13. Rank signature `B0=21, B1=8, HT=9, H=10, HF=94, HE=11, HB=20`.

The clearest current cross-model core is `Alexander Suvorov`, `Napoleon Bonaparte`, `Jean Lannes`, `Maurice, Prince of Orange`, `Charles XIV John`, `Subutai`, and `Louis-Nicolas Davout`. These names remain near the top under meaningfully different ranking assumptions, so the exact internal order should not be over-read more than the cluster itself.

## Strong Upper Tier

These commanders perform well enough to belong in the serious discussion, but the model structure affects how high they climb.

### Battle-Specialist Leaders


These cases are not obvious artifacts. The main issue is that battle-only excellence does not necessarily survive once war-level and campaign-level pages are allowed to absorb some of the score.

### Broad But Still Sensitive Contenders

- `André Masséna`: Upper-tier contender with high confidence; rank 19 and enough scale (37 known outcomes, 40 battle pages) to remain defensible under the trust-first model. Rank signature `B0=22, B1=34, HT=19, H=28, HF=19, HE=33, HB=43`.

The strongest names in this cluster are `André Masséna`. They remain important contenders, but they are not as secure as the robust elite core and still need model-context qualification.

## Model-Sensitive Band

These are the cases where the current data structure appears to be doing too much of the work. They should stay in the audit layer, not in the headline conclusion layer.

- `Suleiman the Magnificent`: Visible in upper-model results, but the rank remains too model-sensitive for headline trust treatment. Rank signature `B0=45, B1=92, HT=2, H=3, HF=3, HE=2, HB=2`.
- `Ivan Paskevich`: Visible in upper-model results, but the rank remains too model-sensitive for headline trust treatment. Rank signature `B0=46, B1=57, HT=13, H=6, HF=5, HE=16, HB=3`.
- `Douglas MacArthur`: Visible in upper-model results, but the rank remains too model-sensitive for headline trust treatment. Rank signature `B0=44, B1=78, HT=4, H=4, HF=4, HE=4, HB=17`.
- `Takeda Shingen`: Visible in upper-model results, but the rank remains too model-sensitive for headline trust treatment. Rank signature `B0=6, B1=4, HT=81, H=80, HF=89, HE=69, HB=58`.
- `Dwight D. Eisenhower`: Ranks well enough to monitor, but higher-level evidence dependence keeps this case out of the headline tiers. Rank signature `B0=375, B1=322, HT=5, H=5, HF=10, HE=13, HB=8`.
- `Babur`: Visible in upper-model results, but the rank remains too model-sensitive for headline trust treatment. Rank signature `B0=108, B1=64, HT=18, H=18, HF=25, HE=6, HB=9`.
- `Abu Ubayda ibn al-Jarrah`: Visible in upper-model results, but the rank remains too model-sensitive for headline trust treatment. Rank signature `B0=10, B1=15, HT=60, H=56, HF=55, HE=79, HB=36`.
- `Petar Bojović`: Ranks well enough to monitor, but higher-level evidence dependence keeps this case out of the headline tiers. Rank signature `B0=NA, B1=270, HT=22, H=14, HF=14, HE=27, HB=10`.

The sharpest caution signals in this snapshot are `Suleiman the Magnificent`, `Ivan Paskevich`, `Douglas MacArthur`, `Takeda Shingen`, `Dwight D. Eisenhower`, `Babur`, `Abu Ubayda ibn al-Jarrah`, and `Petar Bojović`. These outcomes may still reflect real historical prominence, but the current package does not support treating them as robust all-time elite placements.

## Focused Audit Of Model-Sensitive High-Rank Cases

This is the short list of cases that deserve the most scrutiny before any public-facing interpretation.

- `Khalid ibn al-Walid`: best `1`, worst `42`, range `41`. High-confidence upper-band commander; rank 37 but not stable enough for the headline core. Rank signature `B0=1, B1=1, HT=37, H=42, HF=43, HE=39, HB=28`.
- `Suleiman the Magnificent`: best `2`, worst `92`, range `90`. Visible in upper-model results, but the rank remains too model-sensitive for headline trust treatment. Rank signature `B0=45, B1=92, HT=2, H=3, HF=3, HE=2, HB=2`.
- `Ivan Paskevich`: best `3`, worst `57`, range `54`. Visible in upper-model results, but the rank remains too model-sensitive for headline trust treatment. Rank signature `B0=46, B1=57, HT=13, H=6, HF=5, HE=16, HB=3`.
- `Douglas MacArthur`: best `4`, worst `78`, range `74`. Visible in upper-model results, but the rank remains too model-sensitive for headline trust treatment. Rank signature `B0=44, B1=78, HT=4, H=4, HF=4, HE=4, HB=17`.
- `Takeda Shingen`: best `4`, worst `81`, range `77`. Visible in upper-model results, but the rank remains too model-sensitive for headline trust treatment. Rank signature `B0=6, B1=4, HT=81, H=80, HF=89, HE=69, HB=58`.
- `Louis XIV`: best `5`, worst `42`, range `37`. High-confidence upper-band commander; rank 8 but not stable enough for the headline core. Rank signature `B0=31, B1=42, HT=8, H=7, HF=7, HE=8, HB=5`.
- `Alexander Farnese, Duke of Parma`: best `5`, worst `38`, range `33`. High-confidence upper-band commander; rank 36 but not stable enough for the headline core. Rank signature `B0=5, B1=6, HT=36, H=38, HF=42, HE=37, HB=30`.
- `Dwight D. Eisenhower`: best `5`, worst `375`, range `370`. Ranks well enough to monitor, but higher-level evidence dependence keeps this case out of the headline tiers. Rank signature `B0=375, B1=322, HT=5, H=5, HF=10, HE=13, HB=8`.
- `Babur`: best `6`, worst `108`, range `102`. Visible in upper-model results, but the rank remains too model-sensitive for headline trust treatment. Rank signature `B0=108, B1=64, HT=18, H=18, HF=25, HE=6, HB=9`.
- `Saladin`: best `7`, worst `119`, range `112`. The placement is too model-dependent to treat as a strong all-model conclusion. Rank signature `B0=40, B1=7, HT=118, H=119, HF=122, HE=103, HB=89`.
- `Louis-Nicolas Davout`: best `8`, worst `21`, range `13`. Trust-first v2 rank 9 with high confidence; Top-25 in 6 trusted models and rank spread 13. Rank signature `B0=21, B1=8, HT=9, H=10, HF=94, HE=11, HB=20`.
- `Abu Ubayda ibn al-Jarrah`: best `10`, worst `79`, range `69`. Visible in upper-model results, but the rank remains too model-sensitive for headline trust treatment. Rank signature `B0=10, B1=15, HT=60, H=56, HF=55, HE=79, HB=36`.

The main audit pattern is clear:

- Some commanders are `battle specialists` in the current dataset. They excel in strict and battle-only models but fall sharply in hierarchical models. The clearest current examples are `none`.
- Some commanders are `hierarchical beneficiaries`. They climb when operations, campaigns, and war pages are counted. `Enver Pasha`, `Ivan Konev`, `Aleksandr Vasilevsky`, `Mahmud II`, and `Nelson A. Miles` fit this pattern to different degrees.
- Some commanders are `credit-rule beneficiaries`. They jump when full presence credit is used. `Qasem Soleimani`, `Saddam Hussein`, `Joseph Stalin`, and `Deng Xiaoping` are the clearest cases.
- A few cases show `unusual attribution fragility` even without the higher-level-page flag. `Belisarius` is the most obvious example; the battle-based signal is strong, but one attribution variant produces a major shock.

## Era-By-Era Elite Shortlist

Requested era buckets are compressed as follows: `modern` here combines `revolutionary_napoleonic`, `long_nineteenth_century`, `world_wars`, and `cold_war`. This keeps the interpretive memo aligned with the requested era structure while preserving the original bucket labels in the supporting CSV.

### Ancient

- `Alexander the Great` (model_sensitive_band): Useful as an audit case for the era, not as a secure top-tier conclusion; rank signature B0=61, B1=45, HT=30, H=26, HF=18, HE=19, HB=73. The era signal is still model-sensitive; treat this as a provisional inclusion rather than a headline conclusion.
- `Hannibal` (model_sensitive_band): Useful as an audit case for the era, not as a secure top-tier conclusion; rank signature B0=38, B1=16, HT=84, H=90, HF=117, HE=67, HB=54. The era signal is still model-sensitive; treat this as a provisional inclusion rather than a headline conclusion.
- `Shapur I` (model_sensitive_band): Useful as an audit case for the era, not as a secure top-tier conclusion; rank signature B0=155, B1=215, HT=76, H=102, HF=106, HE=80, HB=194. The era signal is still model-sensitive; treat this as a provisional inclusion rather than a headline conclusion.
- `Flavius Aetius` (model_sensitive_band): Useful as an audit case for the era, not as a secure top-tier conclusion; rank signature B0=347, B1=464, HT=88, H=93, HF=67, HE=66, HB=146. The era signal is still model-sensitive; treat this as a provisional inclusion rather than a headline conclusion.

Ancient evidence is meaningful but thinner and more abstraction-sensitive than early modern or modern evidence. The current ancient shortlist is led by `Alexander the Great`, `Hannibal`, and `Shapur I`.

### Medieval

- `Amr ibn al-As` (model_sensitive_band): Useful as an audit case for the era, not as a secure top-tier conclusion; rank signature B0=13, B1=11, HT=54, H=33, HF=33, HE=36, HB=23. The era signal is still model-sensitive; treat this as a provisional inclusion rather than a headline conclusion.
- `Abu Ubayda ibn al-Jarrah` (model_sensitive_band): Useful as an audit case for the era, not as a secure top-tier conclusion; rank signature B0=10, B1=15, HT=60, H=56, HF=55, HE=79, HB=36. The era signal is still model-sensitive; treat this as a provisional inclusion rather than a headline conclusion.
- `Philip the Good` (model_sensitive_band): Useful as an audit case for the era, not as a secure top-tier conclusion; rank signature B0=55, B1=69, HT=62, H=45, HF=66, HE=21, HB=37. The era signal is still model-sensitive; treat this as a provisional inclusion rather than a headline conclusion.
- `Emperor Taizong of Tang` (model_sensitive_band): Useful as an audit case for the era, not as a secure top-tier conclusion; rank signature B0=NA, B1=237, HT=28, H=20, HF=31, HE=42, HB=68. The era signal is still model-sensitive; treat this as a provisional inclusion rather than a headline conclusion.
- `Subutai` (robust_elite_core): Best-supported medieval candidate; rank signature B0=14, B1=28, HT=7, H=8, HF=9, HE=7, HB=4. Trust-first v2 rank 7 with high confidence; Top-25 in 5 trusted models and rank spread 24.

The medieval shortlist is centered on `Amr ibn al-As`, `Abu Ubayda ibn al-Jarrah`, and `Philip the Good`. These remain powerful cases, but the cross-model stability inside that set still varies materially.

### Early Modern

- `Suleiman the Magnificent` (model_sensitive_band): Useful as an audit case for the era, not as a secure top-tier conclusion; rank signature B0=45, B1=92, HT=2, H=3, HF=3, HE=2, HB=2. The era signal is still model-sensitive; treat this as a provisional inclusion rather than a headline conclusion.
- `Babur` (model_sensitive_band): Useful as an audit case for the era, not as a secure top-tier conclusion; rank signature B0=108, B1=64, HT=18, H=18, HF=25, HE=6, HB=9. The era signal is still model-sensitive; treat this as a provisional inclusion rather than a headline conclusion.
- `Takeda Shingen` (model_sensitive_band): Useful as an audit case for the era, not as a secure top-tier conclusion; rank signature B0=6, B1=4, HT=81, H=80, HF=89, HE=69, HB=58. The era signal is still model-sensitive; treat this as a provisional inclusion rather than a headline conclusion.
- `Francis Vere` (model_sensitive_band): Useful as an audit case for the era, not as a secure top-tier conclusion; rank signature B0=11, B1=18, HT=70, H=82, HF=101, HE=73, HB=52. The era signal is still model-sensitive; treat this as a provisional inclusion rather than a headline conclusion.
- `Ivan Sirko` (model_sensitive_band): Useful as an audit case for the era, not as a secure top-tier conclusion; rank signature B0=NA, B1=309, HT=57, H=12, HF=11, HE=25, HB=18. The era signal is still model-sensitive; treat this as a provisional inclusion rather than a headline conclusion.
- `Maurice, Prince of Orange` (robust_elite_core): Best-supported early modern candidate; rank signature B0=7, B1=14, HT=12, H=13, HF=13, HE=10, HB=7. Trust-first v2 rank 12 with very_high confidence; Top-25 in 6 trusted models and rank spread 7.

The early modern shortlist is led by `Suleiman the Magnificent`, `Babur`, `Takeda Shingen`, `Francis Vere`, and `Ivan Sirko`. Several of the strongest early-modern cases are battle-heavy, so their exact standing still depends on whether the model stays battle-dominant or absorbs more higher-level pages.

### Modern

- `Ivan Paskevich` (model_sensitive_band): Useful as an audit case for the era, not as a secure top-tier conclusion; rank signature B0=46, B1=57, HT=13, H=6, HF=5, HE=16, HB=3. The era signal is still model-sensitive; treat this as a provisional inclusion rather than a headline conclusion.
- `Douglas MacArthur` (model_sensitive_band): Useful as an audit case for the era, not as a secure top-tier conclusion; rank signature B0=44, B1=78, HT=4, H=4, HF=4, HE=4, HB=17. The era signal is still model-sensitive; treat this as a provisional inclusion rather than a headline conclusion.
- `Alexander Suvorov` (robust_elite_core): Best-supported modern candidate; rank signature B0=4, B1=5, HT=1, H=1, HF=1, HE=3, HB=1. Trust-first v2 rank 1 with high confidence; Top-25 in 6 trusted models and rank spread 4.
- `Napoleon Bonaparte` (robust_elite_core): Best-supported modern candidate; rank signature B0=3, B1=3, HT=3, H=2, HF=2, HE=1, HB=6. Trust-first v2 rank 3 with very_high confidence; Top-25 in 6 trusted models and rank spread 5.
- `Jean Lannes` (robust_elite_core): Best-supported modern candidate; rank signature B0=2, B1=2, HT=10, H=11, HF=12, HE=17, HB=19. Trust-first v2 rank 10 with high confidence; Top-25 in 6 trusted models and rank spread 17.
- `Charles XIV John` (robust_elite_core): Best-supported modern candidate; rank signature B0=15, B1=13, HT=6, H=9, HF=8, HE=5, HB=16. Trust-first v2 rank 6 with high confidence; Top-25 in 6 trusted models and rank spread 11.
- `Louis-Nicolas Davout` (robust_elite_core): Best-supported modern candidate; rank signature B0=21, B1=8, HT=9, H=10, HF=94, HE=11, HB=20. Trust-first v2 rank 9 with high confidence; Top-25 in 6 trusted models and rank spread 13.
- `André Masséna` (strong_upper_tier): Belongs in the era shortlist, but the case depends on model choice; rank signature B0=22, B1=34, HT=19, H=28, HF=19, HE=33, HB=43. Upper-tier contender with high confidence; rank 19 and enough scale (37 known outcomes, 40 battle pages) to remain defensible under the trust-first model.

Modern evidence is the richest part of the current package. The most secure modern shortlist is `Ivan Paskevich`, `Douglas MacArthur`, `Alexander Suvorov`, `Napoleon Bonaparte`, and `Jean Lannes`. The late-modern and Cold War end of this bucket is more abstraction-sensitive, so the exact order should stay in the interpretation layer rather than be treated as a clean headline ranking.

### Contemporary

- `Qasem Soleimani` (model_sensitive_band): Useful as an audit case for the era, not as a secure top-tier conclusion; rank signature B0=NA, B1=323, HT=87, H=49, HF=45, HE=78, HB=86. The era signal is still model-sensitive; treat this as a provisional inclusion rather than a headline conclusion.

The current contemporary shortlist is `Qasem Soleimani`. Contemporary results are thin, highly model-sensitive, and often depend on higher-level pages or sparse battle coverage. That means the contemporary shortlist should be treated as a weak provisional signal, not as a settled conclusion.

## Bottom Line

The safest current statement is not a final all-time list. It is that the most defensible all-model core in this snapshot is `Alexander Suvorov`, `Napoleon Bonaparte`, `Jean Lannes`, `Maurice, Prince of Orange`, `Charles XIV John`, `Subutai`, and `Louis-Nicolas Davout`.

A second cluster remains historically important but model-sensitive: `André Masséna`. Those names belong in the serious discussion, but not yet in a single public-facing headline ranking without stronger qualification.

The weakest claims are the ones driven by higher-level page weighting or by full-credit attribution. Those cases are visible in the package and should remain explicit audit items rather than be smoothed over.
