# Best-Supported Top Tier Memo

## Scope

This memo adds an interpretive layer on top of the completed ranking package. It does not rerun crawling, extraction, or framework design. The purpose is to separate the strongest model-robust conclusions from the rankings that remain materially dependent on page-type weighting, commander-credit rules, or broader-eligibility choices.

The memo uses the following outputs as its evidence base:

- `RANKING_RESULTS_BASELINE.csv`
- `RANKING_RESULTS_HIERARCHICAL.csv`
- `RANKING_RESULTS_SENSITIVITY.csv`
- `TOP_COMMANDERS_SUMMARY.csv`

Interpretive heuristics used here:

- `Robust elite`: top-25 in at least 5 of 5 trusted models, rank range at most 18, mean rank at most 25, and no `higher_level_dependent` caution flag.
- `Strong but model-sensitive`: still reaches the leading cohort repeatedly, but placement depends materially on battle-only vs hierarchical weighting or on credit rules.
- `Caution / likely artifact`: high placement appears heavily dependent on higher-level pages, credit-attribution variants, or broad-eligibility inclusion.

These are interpretive categories layered on top of the existing ranking framework. They are meant to support judgment, not replace the underlying score tables.

## Robust Elite

This is the strongest cross-model core in the current package. These commanders stay near the top even when the model changes meaningfully.

- `Napoleon Bonaparte`: Top-25 in 5 of 5 trusted models with a rank range of 1; remains competitive under both battle-only and hierarchical runs. Rank signature `B0=2, B1=3, H=3, HF=3, HE=2, HB=3`.
- `Alexander Suvorov`: Top-25 in 5 of 5 trusted models with a rank range of 3; remains competitive under both battle-only and hierarchical runs. Rank signature `B0=3, B1=5, H=2, HF=2, HE=3, HB=2`.
- `Suleiman the Magnificent`: Top-25 in 5 of 5 trusted models with a rank range of 17; remains competitive under both battle-only and hierarchical runs. Rank signature `B0=18, B1=8, H=1, HF=1, HE=1, HB=1`.
- `Jean Lannes`: Top-25 in 5 of 5 trusted models with a rank range of 12; remains competitive under both battle-only and hierarchical runs. Rank signature `B0=1, B1=2, H=8, HF=7, HE=13, HB=9`.
- `Louis-Nicolas Davout`: Top-25 in 5 of 5 trusted models with a rank range of 3; remains competitive under both battle-only and hierarchical runs. Rank signature `B0=10, B1=7, H=7, HF=17, HE=9, HB=7`.
- `Charles XIV John`: Top-25 in 5 of 5 trusted models with a rank range of 8; remains competitive under both battle-only and hierarchical runs. Rank signature `B0=14, B1=13, H=6, HF=6, HE=6, HB=6`.
- `Maurice, Prince of Orange`: Top-25 in 5 of 5 trusted models with a rank range of 6; remains competitive under both battle-only and hierarchical runs. Rank signature `B0=9, B1=14, H=11, HF=13, HE=11, HB=15`.
- `Henri de La Tour d'Auvergne, Viscount of Turenne`: Top-25 in 5 of 5 trusted models with a rank range of 10; remains competitive under both battle-only and hierarchical runs. Rank signature `B0=19, B1=9, H=12, HF=10, HE=12, HB=12`.
- `Sébastien Le Prestre, Marquis of Vauban`: Top-25 in 5 of 5 trusted models with a rank range of 14; remains competitive under both battle-only and hierarchical runs. Rank signature `B0=8, B1=11, H=18, HF=18, HE=19, HB=22`.
- `André Masséna`: Top-25 in 5 of 5 trusted models with a rank range of 8; remains competitive under both battle-only and hierarchical runs. Rank signature `B0=12, B1=17, H=17, HF=12, HE=18, HB=20`.

The clearest current cross-model core is `Napoleon Bonaparte`, `Alexander Suvorov`, `Suleiman the Magnificent`, `Jean Lannes`, `Louis-Nicolas Davout`, `Charles XIV John`, and `Maurice, Prince of Orange`. These names remain near the top under meaningfully different ranking assumptions, so the exact internal order should not be over-read more than the cluster itself.

## Strong But Model-Sensitive

These commanders perform well enough to belong in the serious discussion, but the model structure affects how high they climb.

### Battle-Specialist Leaders

- `Takeda Shingen`: Performs very strongly in battle-dominant models, but the rank drops when higher-level war/campaign pages are allowed to dilute battle-only performance. Rank signature `B0=4, B1=4, H=76, HF=75, HE=63, HB=84`.
- `Abu Ubayda ibn al-Jarrah`: Performs very strongly in battle-dominant models, but the rank drops when higher-level war/campaign pages are allowed to dilute battle-only performance. Rank signature `B0=13, B1=19, H=66, HF=72, HE=83, HB=58`.
- `Francis Vere`: Performs very strongly in battle-dominant models, but the rank drops when higher-level war/campaign pages are allowed to dilute battle-only performance. Rank signature `B0=11, B1=18, H=74, HF=85, HE=61, HB=83`.
- `Saladin`: Performs very strongly in battle-dominant models, but the rank drops when higher-level war/campaign pages are allowed to dilute battle-only performance. Rank signature `B0=29, B1=6, H=103, HF=108, HE=97, HB=114`.
- `Robert L. Eichelberger`: Performs very strongly in battle-dominant models, but the rank drops when higher-level war/campaign pages are allowed to dilute battle-only performance. Rank signature `B0=15, B1=25, H=118, HF=119, HE=183, HB=74`.

These cases are not obvious artifacts. The main issue is that battle-only excellence does not necessarily survive once war-level and campaign-level pages are allowed to absorb some of the score.

### Broad But Still Sensitive Contenders

- `Louis XIV`: Appears repeatedly near the top, but the exact placement depends on model structure. Rank signature `B0=25, B1=36, H=5, HF=5, HE=7, HB=5`.
- `Subutai`: Appears repeatedly near the top, but the exact placement depends on model structure. Rank signature `B0=21, B1=27, H=10, HF=8, HE=14, HB=8`.
- `Louis-Gabriel Suchet`: Appears repeatedly near the top, but the exact placement depends on model structure. Rank signature `B0=7, B1=12, H=21, HF=24, HE=15, HB=27`.
- `Douglas MacArthur`: Appears repeatedly near the top, but the exact placement depends on model structure. Rank signature `B0=31, B1=74, H=4, HF=4, HE=4, HB=4`.
- `Stanisław Żółkiewski`: Appears repeatedly near the top, but the exact placement depends on model structure. Rank signature `B0=28, B1=22, H=24, HF=29, HE=20, HB=26`.
- `Alexander Farnese, Duke of Parma`: Appears repeatedly near the top, but the exact placement depends on model structure. Rank signature `B0=6, B1=10, H=41, HF=48, HE=34, HB=43`.

The strongest names in this cluster are `Louis XIV`, `Subutai`, `Louis-Gabriel Suchet`, `Douglas MacArthur`, `Stanisław Żółkiewski`, and `Alexander Farnese, Duke of Parma`. They remain important contenders, but they are not as secure as the robust-elite core and still need model-context qualification.

## Caution / Likely Artifact Cases

These are the cases where the current data structure appears to be doing too much of the work. They should stay in the audit layer, not in the headline conclusion layer.

- `Flavius Aetius`: Higher-level war/campaign/operation pages are doing substantial work. The commander is not competitive in the strict baseline cohort. Rank signature `B0=198, B1=114, H=14, HF=11, HE=8, HB=16`.
- `Petar Bojović`: Higher-level war/campaign/operation pages are doing substantial work. Battle-only restrictions cause a severe collapse. Rank signature `B0=NA, B1=260, H=16, HF=14, HE=29, HB=10`.
- `Nelson A. Miles`: Higher-level war/campaign/operation pages are doing substantial work. Battle-only restrictions cause a severe collapse. Rank signature `B0=NA, B1=921, H=77, HF=73, HE=10, HB=87`.
- `Emperor Taizong of Tang`: Higher-level war/campaign/operation pages are doing substantial work. Battle-only restrictions cause a severe collapse. Rank signature `B0=NA, B1=220, H=13, HF=25, HE=25, HB=18`.
- `Stepa Stepanović`: Higher-level war/campaign/operation pages are doing substantial work. The commander is not competitive in the strict baseline cohort. Rank signature `B0=191, B1=103, H=15, HF=16, HE=22, HB=36`.
- `Dwight D. Eisenhower`: Higher-level war/campaign/operation pages are doing substantial work. Battle-only restrictions cause a severe collapse. Rank signature `B0=NA, B1=292, H=39, HF=39, HE=84, HB=17`.
- `Živojin Mišić`: Higher-level war/campaign/operation pages are doing substantial work. The commander is not competitive in the strict baseline cohort. Rank signature `B0=341, B1=209, H=20, HF=22, HE=32, HB=19`.
- `Ivan Sirko`: Higher-level war/campaign/operation pages are doing substantial work. Battle-only restrictions cause a severe collapse. Rank signature `B0=NA, B1=591, H=22, HF=20, HE=50, HB=29`.

The sharpest caution signals in this snapshot are `Flavius Aetius`, `Petar Bojović`, `Nelson A. Miles`, `Emperor Taizong of Tang`, `Stepa Stepanović`, `Dwight D. Eisenhower`, `Živojin Mišić`, and `Ivan Sirko`. These outcomes may still reflect real historical prominence, but the current package does not support treating them as robust all-time elite placements.

## Focused Audit Of Model-Sensitive High-Rank Cases

This is the short list of cases that deserve the most scrutiny before any public-facing interpretation.

- `Khalid ibn al-Walid`: best `1`, worst `48`, range `47`. The placement is too model-dependent to treat as a strong all-model conclusion. Rank signature `B0=5, B1=1, H=48, HF=51, HE=39, HB=47`.
- `Douglas MacArthur`: best `4`, worst `74`, range `70`. The placement is too model-dependent to treat as a strong all-model conclusion. Rank signature `B0=31, B1=74, H=4, HF=4, HE=4, HB=4`.
- `Takeda Shingen`: best `4`, worst `84`, range `80`. The placement is too model-dependent to treat as a strong all-model conclusion. Rank signature `B0=4, B1=4, H=76, HF=75, HE=63, HB=84`.
- `Louis XIV`: best `5`, worst `36`, range `31`. The placement is too model-dependent to treat as a strong all-model conclusion. Rank signature `B0=25, B1=36, H=5, HF=5, HE=7, HB=5`.
- `Babur`: best `5`, worst `83`, range `78`. The placement is too model-dependent to treat as a strong all-model conclusion. Rank signature `B0=83, B1=56, H=9, HF=21, HE=5, HB=11`.
- `Saladin`: best `6`, worst `114`, range `108`. The placement is too model-dependent to treat as a strong all-model conclusion. Rank signature `B0=29, B1=6, H=103, HF=108, HE=97, HB=114`.
- `Flavius Aetius`: best `8`, worst `198`, range `190`. Higher-level war/campaign/operation pages are doing substantial work. The commander is not competitive in the strict baseline cohort. Rank signature `B0=198, B1=114, H=14, HF=11, HE=8, HB=16`.
- `Petar Bojović`: best `10`, worst `260`, range `250`. Higher-level war/campaign/operation pages are doing substantial work. Battle-only restrictions cause a severe collapse. Rank signature `B0=NA, B1=260, H=16, HF=14, HE=29, HB=10`.
- `Nelson A. Miles`: best `10`, worst `921`, range `911`. Higher-level war/campaign/operation pages are doing substantial work. Battle-only restrictions cause a severe collapse. Rank signature `B0=NA, B1=921, H=77, HF=73, HE=10, HB=87`.
- `Francis Vere`: best `11`, worst `83`, range `72`. The placement is too model-dependent to treat as a strong all-model conclusion. Rank signature `B0=11, B1=18, H=74, HF=85, HE=61, HB=83`.
- `Mehmed II`: best `13`, worst `87`, range `74`. The placement is too model-dependent to treat as a strong all-model conclusion. Rank signature `B0=47, B1=87, H=26, HF=9, HE=23, HB=13`.
- `Abu Ubayda ibn al-Jarrah`: best `13`, worst `83`, range `70`. The placement is too model-dependent to treat as a strong all-model conclusion. Rank signature `B0=13, B1=19, H=66, HF=72, HE=83, HB=58`.

The main audit pattern is clear:

- Some commanders are `battle specialists` in the current dataset. They excel in strict and battle-only models but fall sharply in hierarchical models. The clearest current examples are `Takeda Shingen`, `Abu Ubayda ibn al-Jarrah`, `Francis Vere`, `Saladin`, and `Robert L. Eichelberger`.
- Some commanders are `hierarchical beneficiaries`. They climb when operations, campaigns, and war pages are counted. `Enver Pasha`, `Ivan Konev`, `Aleksandr Vasilevsky`, `Mahmud II`, and `Nelson A. Miles` fit this pattern to different degrees.
- Some commanders are `credit-rule beneficiaries`. They jump when full presence credit is used. `Qasem Soleimani`, `Saddam Hussein`, `Joseph Stalin`, and `Deng Xiaoping` are the clearest cases.
- A few cases show `unusual attribution fragility` even without the higher-level-page flag. `Belisarius` is the most obvious example; the battle-based signal is strong, but one attribution variant produces a major shock.

## Era-By-Era Elite Shortlist

Requested era buckets are compressed as follows: `modern` here combines `revolutionary_napoleonic`, `long_nineteenth_century`, `world_wars`, and `cold_war`. This keeps the interpretive memo aligned with the requested era structure while preserving the original bucket labels in the supporting CSV.

### Ancient

- `Publius Cornelius Scipio` (tentative_signal): Useful as an audit case for the era, not as a secure top-tier conclusion; rank signature B0=68, B1=64, H=69, HF=68, HE=36, HB=75. The era signal is thin; treat this as a weak provisional inclusion.
- `Stilicho` (tentative_signal): Useful as an audit case for the era, not as a secure top-tier conclusion; rank signature B0=117, B1=93, H=96, HF=104, HE=54, HB=105. The era signal is thin; treat this as a weak provisional inclusion.
- `Julian` (tentative_signal): Useful as an audit case for the era, not as a secure top-tier conclusion; rank signature B0=48, B1=99, H=168, HF=227, HE=162, HB=183. The era signal is thin; treat this as a weak provisional inclusion.
- `Constantine the Great` (tentative_signal): Useful as an audit case for the era, not as a secure top-tier conclusion; rank signature B0=108, B1=72, H=339, HF=333, HE=265, HB=361. The era signal is thin; treat this as a weak provisional inclusion.

Ancient evidence is meaningful but thinner and more abstraction-sensitive than early modern or modern evidence. The current ancient shortlist is led by `Publius Cornelius Scipio`, `Stilicho`, and `Julian`.

### Medieval

- `Subutai` (strong_but_model_sensitive): Belongs in the era shortlist, but the case depends on model choice; rank signature B0=21, B1=27, H=10, HF=8, HE=14, HB=8. Appears repeatedly near the top, but the exact placement depends on model structure.
- `Khalid ibn al-Walid` (strong_but_model_sensitive): Belongs in the era shortlist, but the case depends on model choice; rank signature B0=5, B1=1, H=48, HF=51, HE=39, HB=47. Appears repeatedly near the top, but the exact placement depends on model structure.
- `Mehmed II` (strong_but_model_sensitive): Belongs in the era shortlist, but the case depends on model choice; rank signature B0=47, B1=87, H=26, HF=9, HE=23, HB=13. Appears repeatedly near the top, but the exact placement depends on model structure.
- `Abu Ubayda ibn al-Jarrah` (strong_but_model_sensitive): Belongs in the era shortlist, but the case depends on model choice; rank signature B0=13, B1=19, H=66, HF=72, HE=83, HB=58. Performs very strongly in battle-dominant models, but the rank drops when higher-level war/campaign pages are allowed to dilute battle-only performance.
- `Saladin` (strong_but_model_sensitive): Belongs in the era shortlist, but the case depends on model choice; rank signature B0=29, B1=6, H=103, HF=108, HE=97, HB=114. Performs very strongly in battle-dominant models, but the rank drops when higher-level war/campaign pages are allowed to dilute battle-only performance.

The medieval shortlist is centered on `Subutai`, `Khalid ibn al-Walid`, and `Mehmed II`. These remain powerful cases, but the cross-model stability inside that set still varies materially.

### Early Modern

- `Suleiman the Magnificent` (robust_elite): Best-supported early modern candidate; rank signature B0=18, B1=8, H=1, HF=1, HE=1, HB=1. Top-25 in 5 of 5 trusted models with a rank range of 17; remains competitive under both battle-only and hierarchical runs.
- `Maurice, Prince of Orange` (robust_elite): Best-supported early modern candidate; rank signature B0=9, B1=14, H=11, HF=13, HE=11, HB=15. Top-25 in 5 of 5 trusted models with a rank range of 6; remains competitive under both battle-only and hierarchical runs.
- `Henri de La Tour d'Auvergne, Viscount of Turenne` (robust_elite): Best-supported early modern candidate; rank signature B0=19, B1=9, H=12, HF=10, HE=12, HB=12. Top-25 in 5 of 5 trusted models with a rank range of 10; remains competitive under both battle-only and hierarchical runs.
- `Sébastien Le Prestre, Marquis of Vauban` (robust_elite): Best-supported early modern candidate; rank signature B0=8, B1=11, H=18, HF=18, HE=19, HB=22. Top-25 in 5 of 5 trusted models with a rank range of 14; remains competitive under both battle-only and hierarchical runs.
- `Louis XIV` (strong_but_model_sensitive): Belongs in the era shortlist, but the case depends on model choice; rank signature B0=25, B1=36, H=5, HF=5, HE=7, HB=5. Appears repeatedly near the top, but the exact placement depends on model structure.
- `Takeda Shingen` (strong_but_model_sensitive): Belongs in the era shortlist, but the case depends on model choice; rank signature B0=4, B1=4, H=76, HF=75, HE=63, HB=84. Performs very strongly in battle-dominant models, but the rank drops when higher-level war/campaign pages are allowed to dilute battle-only performance.

The early modern shortlist is led by `Suleiman the Magnificent`, `Maurice, Prince of Orange`, `Henri de La Tour d'Auvergne, Viscount of Turenne`, `Sébastien Le Prestre, Marquis of Vauban`, and `Louis XIV`. Several of the strongest early-modern cases are battle-heavy, so their exact standing still depends on whether the model stays battle-dominant or absorbs more higher-level pages.

### Modern

- `Napoleon Bonaparte` (robust_elite): Best-supported modern candidate; rank signature B0=2, B1=3, H=3, HF=3, HE=2, HB=3. Top-25 in 5 of 5 trusted models with a rank range of 1; remains competitive under both battle-only and hierarchical runs.
- `Alexander Suvorov` (robust_elite): Best-supported modern candidate; rank signature B0=3, B1=5, H=2, HF=2, HE=3, HB=2. Top-25 in 5 of 5 trusted models with a rank range of 3; remains competitive under both battle-only and hierarchical runs.
- `Jean Lannes` (robust_elite): Best-supported modern candidate; rank signature B0=1, B1=2, H=8, HF=7, HE=13, HB=9. Top-25 in 5 of 5 trusted models with a rank range of 12; remains competitive under both battle-only and hierarchical runs.
- `Louis-Nicolas Davout` (robust_elite): Best-supported modern candidate; rank signature B0=10, B1=7, H=7, HF=17, HE=9, HB=7. Top-25 in 5 of 5 trusted models with a rank range of 3; remains competitive under both battle-only and hierarchical runs.
- `Charles XIV John` (robust_elite): Best-supported modern candidate; rank signature B0=14, B1=13, H=6, HF=6, HE=6, HB=6. Top-25 in 5 of 5 trusted models with a rank range of 8; remains competitive under both battle-only and hierarchical runs.
- `André Masséna` (robust_elite): Best-supported modern candidate; rank signature B0=12, B1=17, H=17, HF=12, HE=18, HB=20. Top-25 in 5 of 5 trusted models with a rank range of 8; remains competitive under both battle-only and hierarchical runs.
- `Louis-Gabriel Suchet` (strong_but_model_sensitive): Belongs in the era shortlist, but the case depends on model choice; rank signature B0=7, B1=12, H=21, HF=24, HE=15, HB=27. Appears repeatedly near the top, but the exact placement depends on model structure.
- `Douglas MacArthur` (strong_but_model_sensitive): Belongs in the era shortlist, but the case depends on model choice; rank signature B0=31, B1=74, H=4, HF=4, HE=4, HB=4. Appears repeatedly near the top, but the exact placement depends on model structure.

Modern evidence is the richest part of the current package. The most secure modern shortlist is `Napoleon Bonaparte`, `Alexander Suvorov`, `Jean Lannes`, `Louis-Nicolas Davout`, and `Charles XIV John`. The late-modern and Cold War end of this bucket is more abstraction-sensitive, so the exact order should stay in the interpretation layer rather than be treated as a clean headline ranking.

### Contemporary

- `Qasem Soleimani` (tentative_signal): Useful as an audit case for the era, not as a secure top-tier conclusion; rank signature B0=NA, B1=308, H=44, HF=43, HE=69, HB=45. The era signal is thin; treat this as a weak provisional inclusion.
- `Sarath Fonseka` (tentative_signal): Useful as an audit case for the era, not as a secure top-tier conclusion; rank signature B0=92, B1=66, H=230, HF=220, HE=254, HB=244. The era signal is thin; treat this as a weak provisional inclusion.
- `Valery Gerasimov` (tentative_signal): Useful as an audit case for the era, not as a secure top-tier conclusion; rank signature B0=NA, B1=555, H=93, HF=99, HE=95, HB=101. The era signal is thin; treat this as a weak provisional inclusion.

The current contemporary shortlist is `Qasem Soleimani`, `Sarath Fonseka`, and `Valery Gerasimov`. Contemporary results are thin, highly model-sensitive, and often depend on higher-level pages or sparse battle coverage. That means the contemporary shortlist should be treated as a weak provisional signal, not as a settled conclusion.

## Bottom Line

The safest current statement is not a final all-time list. It is that the most defensible all-model core in this snapshot is `Napoleon Bonaparte`, `Alexander Suvorov`, `Suleiman the Magnificent`, `Jean Lannes`, `Louis-Nicolas Davout`, `Charles XIV John`, and `Maurice, Prince of Orange`.

A second cluster remains historically important but model-sensitive: `Louis XIV`, `Subutai`, `Louis-Gabriel Suchet`, `Douglas MacArthur`, `Stanisław Żółkiewski`, `Alexander Farnese, Duke of Parma`, `Khalid ibn al-Walid`, and `Babur`. Those names belong in the serious discussion, but not yet in a single public-facing headline ranking without stronger qualification.

The weakest claims are the ones driven by higher-level page weighting or by full-credit attribution. Those cases are visible in the package and should remain explicit audit items rather than be smoothed over.
