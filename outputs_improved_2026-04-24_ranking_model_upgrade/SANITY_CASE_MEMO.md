# Sanity Case Memo

Snapshot: `outputs_improved_2026-04-24_ranking_model_upgrade`

## Trust-First V2 sanity cases

- `Alexander Suvorov`: baseline `4`, weighted `1`, trust v2 `1`; tier `robust_elite_core`, confidence `high`. Trust-first v2 rank 1 with high confidence; Top-25 in 6 trusted models and rank spread 3.
- `Napoleon Bonaparte`: baseline `3`, weighted `6`, trust v2 `3`; tier `robust_elite_core`, confidence `very_high`. Trust-first v2 rank 3 with very_high confidence; Top-25 in 6 trusted models and rank spread 4.
- `Jean Lannes`: baseline `2`, weighted `9`, trust v2 `6`; tier `robust_elite_core`, confidence `high`. Trust-first v2 rank 6 with high confidence; Top-25 in 6 trusted models and rank spread 15.
- `Louis-Nicolas Davout`: baseline `21`, weighted `8`, trust v2 `7`; tier `robust_elite_core`, confidence `high`. Trust-first v2 rank 7 with high confidence; Top-25 in 6 trusted models and rank spread 14.
- `Douglas MacArthur`: baseline `44`, weighted `14`, trust v2 `8`; tier `model_sensitive_band`, confidence `caution`. Visible in upper-model results, but the rank remains too model-sensitive for headline trust treatment.
- `Khalid ibn al-Walid`: baseline `1`, weighted `21`, trust v2 `18`; tier `high_confidence_upper_band`, confidence `moderate`. High-confidence upper-band commander; rank 18 but not stable enough for the headline core.
- `Takeda Shingen`: baseline `6`, weighted `37`, trust v2 `32`; tier `model_sensitive_band`, confidence `caution`. Visible in upper-model results, but the rank remains too model-sensitive for headline trust treatment.
- `Suleiman the Magnificent`: baseline `68`, weighted `132`, trust v2 `83`; tier `model_sensitive_band`, confidence `caution`. Visible in upper-model results, but the rank remains too model-sensitive for headline trust treatment.

## Regression checks

- Strict eligibility preserved: `True`
- Non-person leakage: `True`
- Top-10 overlap between weighted and trust v2: `9`
- Robust core free of fragile higher-level anchors: `True`
