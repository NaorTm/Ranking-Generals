# Scoring Readiness Report

## Current State

The scoring-stage foundation is built on `outputs_cleaned_2026-04-11_globaltrust_authoritative`.

- source retained pages: `13,492`
- source commander rows after exclusion: `60,572`
- source commander master rows after exclusion: `30,722`
- strict-eligible pages: `11,644`
- balanced-eligible pages: `11,917`
- annotated commander-engagement rows: `60,395`
- default conservative ranking cohort: `709` commanders

## This Pass Changed

- known outcome rows: `28,067` -> `29,311`
- unknown outcome rows: `32,340` -> `31,084`
- sanitized result fallback affected `322` pages, `1,546` commander rows, and `1,254` commanders
- scoring exclusions now remove `76` confirmed non-person commander rows

## Trust Judgment

- `hierarchical_weighted` remains the most trustworthy single ranking model.
- `baseline_conservative` is cleaner, but still battle-specialist heavy.
- `hierarchical_full_credit` remains diagnostic, not definitive.
