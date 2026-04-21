# Top 200 Verification Audit Memo

Audit base: `outputs_cleaned_2026-04-21_fullverification_authoritative`
Before-verification comparison base: `outputs_cleaned_2026-04-21_trustfirstv2_authoritative`

## Overall

- Top 200 commanders reviewed in the current verified trust ranking.
- Structurally clean: `2`
- Mildly inflated: `16`
- Materially inflated: `164`
- High-priority for manual audit: `18`

## Structurally Clean

The cleanest current top-end cases are `Subutai`, `Ivan Paskevich`.

## Mildly Inflated

The main mild-inflation cluster is `Alexander Suvorov`, `Louis-Nicolas Davout`, `Jean Lannes`, `Maurice, Prince of Orange`, `André Masséna`, `Petar Bojović`, `Louis-Gabriel Suchet`, `Sébastien Le Prestre, Marquis of Vauban`, `Alexander Farnese, Duke of Parma`, `Stanisław Żółkiewski`, `Walter Krueger`, `Abu Ubayda ibn al-Jarrah`.

## Materially Inflated

The strongest structural-inflation concerns are `Mahmud II`, `William Halsey Jr.`, `Nelson A. Miles`, `Peter the Great`, `Richmond K. Turner`, `Ivan Sirko`, `Emperor Taizong of Tang`, `Ahmad Shah Durrani`, `Holland M. Smith`, `Alexander Vandegrift`, `Chiang Kai-shek`, `Enver Pasha`.

## High-Priority Manual Outcome Audit

The most important next outcome-review cases are `Suleiman the Magnificent`, `Douglas MacArthur`, `Nader Shah`, `Abbas the Great`, `Dwight D. Eisenhower`, `Flavius Aetius`, `Charles XIV John`, `Joseph Stalin`, `Živojin Mišić`, `Napoleon Bonaparte`, `Ivan Konev`, `Mehmed II`.

## Headline Figures

- `Suleiman the Magnificent`: `high_priority_manual_audit`, rank `1`, tier `high_confidence_upper_band`, confidence `moderate`. 7 structurally suspect rows; 12 downgraded broad rows; war-page reduction 17→0; campaign reduction 2→0; strict engagements reduced by 18; clean record with unresolved battle outcomes; victory count dropped by 9; known outcomes dropped by 13; multiple surviving battle pages still unresolved; headline rank with softened trust confidence
- `Alexander Suvorov`: `mildly_inflated`, rank `2`, tier `robust_elite_core`, confidence `high`. 2 structurally suspect rows; 3 downgraded broad rows; war-page reduction 5→1; campaign reduction 1→0; strict engagements reduced by 4
- `Napoleon Bonaparte`: `high_priority_manual_audit`, rank `3`, tier `robust_elite_core`, confidence `very_high`. 7 structurally suspect rows; 3 downgraded broad rows; war-page reduction 5→2; campaign reduction 6→0; strict engagements reduced by 7; known outcomes dropped by 4; multiple surviving battle pages still unresolved
- `Louis-Nicolas Davout`: `mildly_inflated`, rank `10`, tier `robust_elite_core`, confidence `high`. 3 structurally suspect rows; campaign reduction 3→0; multiple surviving battle pages still unresolved
- `Jean Lannes`: `mildly_inflated`, rank `11`, tier `robust_elite_core`, confidence `high`. 1 structurally suspect rows; 1 downgraded broad rows; war-page reduction 4→3; campaign reduction 1→0
- `Khalid ibn al-Walid`: `high_priority_manual_audit`, rank `44`, tier `model_sensitive_band`, confidence `caution`. 1 downgraded broad rows; rank moved materially after verification; clean record with unresolved battle outcomes; multiple surviving battle pages still unresolved

## Bottom Line

This audit is a global top-of-ranking review, not a Suleiman-only patch. Commanders in the clean bucket now look broadly defensible under the current verification layer, while the material and high-priority buckets are the cases where DB structure or outcome interpretation still appears capable of overstating current placement.
