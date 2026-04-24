# Hardening Pass Impact Report

Starting snapshot: `outputs_cleaned_2026-04-11_globaltrust_authoritative`
Current snapshot: `outputs_cleaned_2026-04-11_hardening_authoritative`

## Quantitative Changes

- Annotated commander-engagement rows: `60,395` -> `60,321`
- Strict known-outcome rows: `29,311` -> `30,267`
- Unknown-outcome rows: `31,084` -> `30,054`
- Baseline cohort size: `709` -> `719`
- Hierarchical weighted cohort size: `1,334` -> `1,363`
- Dashboard ranked commanders: `2,448` -> `2,477`

## Ambiguity Reduction

- Unresolved coalition/allied rows: `1,224` -> `242`
- Unresolved coalition/allied pages: `260` -> `69`
- Unresolved coalition/allied commanders: `832` -> `229`
- Unresolved bare `Victory` / `Defeat` rows: `4,520` -> `4,503`
- Unresolved bare `Victory` / `Defeat` pages: `445` -> `445`

## Non-Person Leakage

- Heuristic obvious non-person identities in identity bridge: `35` -> `0`
- Heuristic obvious non-person names in ranked baseline/hierarchical tables: `1` -> `0`

## Leader Stability

- Baseline leader: `Jean Lannes` -> `Jean Lannes`
- Hierarchical leader: `Suleiman the Magnificent` -> `Suleiman the Magnificent`

## Notable Rank Changes (Hierarchical Weighted)

- `Suleiman the Magnificent`: `1` -> `1`
- `Alexander Suvorov`: `2` -> `2`
- `Napoleon Bonaparte`: `3` -> `3`
- `Douglas MacArthur`: `125` -> `4`
- `Qasem Soleimani`: `17` -> `45`
- `Nelson A. Miles`: `19` -> `19`
- `Suhayl al-Hasan`: `52` -> `94`
- `Valery Gerasimov`: `94` -> `156`
- `George S. Patton`: `750` -> `145`
- `John J. Pershing`: `528` -> `102`
- `Bernard Montgomery`: `223` -> `38`
- `Dwight D. Eisenhower`: `148` -> `40`
- `William Halsey Jr.`: `79` -> `37`
- `Ivan Sirko`: `25` -> `24`

## `hierarchical_full_credit` Diagnostic Drift

Largest remaining full-credit gains among the hierarchical top 300:

```text
              display_name  rank_hierarchical_weighted  rank_hierarchical_full_credit  full_credit_gain
               Philip Vian                       856.0                          558.0             298.0
        Alexander Tormasov                       857.0                          590.0             267.0
       Kobayakawa Takakage                       637.0                          372.0             265.0
           John of Austria                       843.0                          610.0             233.0
                   Eumenes                       826.0                          599.0             227.0
Alfonso Ferrero La Marmora                       742.0                          522.0             220.0
       Harold Barrowclough                       695.0                          476.0             219.0
                   Cao Ren                       874.0                          660.0             214.0
         Matsudaira Ietada                       959.0                          754.0             205.0
   Georg Andreas von Rosen                      1001.0                          800.0             201.0
           Nicolas Oudinot                       671.0                          488.0             183.0
            Sassa Narimasa                      1153.0                          971.0             182.0
         Vasily Sokolovsky                       932.0                          755.0             177.0
               Xiahou Yuan                       850.0                          678.0             172.0
        Dominique Vandamme                       578.0                          408.0             170.0
```