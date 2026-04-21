# Sanity Case Memo

Snapshot: `outputs_cleaned_2026-04-21_fullpopulation_authoritative`

## Trust-First V2 sanity cases

- `Alexander Suvorov`: baseline `4`, weighted `1`, trust v2 `1`; tier `robust_elite_core`, confidence `high`. Trust-first v2 rank 1 with high confidence; Top-25 in 6 trusted models and rank spread 4.
- `Suleiman the Magnificent`: baseline `45`, weighted `3`, trust v2 `2`; tier `model_sensitive_band`, confidence `caution`. Visible in upper-model results, but the rank remains too model-sensitive for headline trust treatment.
- `Napoleon Bonaparte`: baseline `3`, weighted `2`, trust v2 `3`; tier `robust_elite_core`, confidence `very_high`. Trust-first v2 rank 3 with very_high confidence; Top-25 in 6 trusted models and rank spread 5.
- `Douglas MacArthur`: baseline `44`, weighted `4`, trust v2 `4`; tier `model_sensitive_band`, confidence `caution`. Visible in upper-model results, but the rank remains too model-sensitive for headline trust treatment.
- `Louis-Nicolas Davout`: baseline `21`, weighted `10`, trust v2 `9`; tier `robust_elite_core`, confidence `high`. Trust-first v2 rank 9 with high confidence; Top-25 in 6 trusted models and rank spread 13.
- `Jean Lannes`: baseline `2`, weighted `11`, trust v2 `10`; tier `robust_elite_core`, confidence `high`. Trust-first v2 rank 10 with high confidence; Top-25 in 6 trusted models and rank spread 17.
- `Khalid ibn al-Walid`: baseline `1`, weighted `42`, trust v2 `37`; tier `high_confidence_upper_band`, confidence `moderate`. High-confidence upper-band commander; rank 37 but not stable enough for the headline core.
- `Takeda Shingen`: baseline `6`, weighted `80`, trust v2 `81`; tier `model_sensitive_band`, confidence `caution`. Visible in upper-model results, but the rank remains too model-sensitive for headline trust treatment.

## Regression checks

- Strict eligibility preserved: `True`
- Non-person leakage: `True`
- Top-10 overlap between weighted and trust v2: `9`
- Robust core free of fragile higher-level anchors: `True`
