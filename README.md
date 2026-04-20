# General Ranking Project

This repository contains the data pipeline, cleaning logic, scoring framework, ranking package, and static dashboard for the historical general-ranking project.

The project starts from Wikipedia military-history discovery pages, builds a conservative battle-command dataset, cleans and audits the extracted records, and produces a final ranking framework for historical commanders across multiple model views.

## Current Project Status

The latest authoritative deliverable in this workspace is:

- `outputs_cleaned_2026-04-12_coalitionhardening_authoritative`

Under the current methodology, that snapshot is the best final system state. The primary trusted model is `hierarchical_weighted`. The static dashboard in that snapshot is the recommended way to browse the results locally.

## Repository Contents

Tracked in this repository:

- core extraction pipeline
- battle and commander cleaning scripts
- scoring, ranking, interpretive, and dashboard builders
- `requirements.txt`
- the latest authoritative output snapshot

Ignored from the repository:

- cache folders
- smoke-test runs
- superseded output snapshots
- temporary CSVs
- unrelated mockups, binary files, and document files in this workspace

## Main Scripts

- `battle_dataset_pipeline.py`: raw discovery and extraction pipeline
- `cleanup_battles_clean.py`: battle-level cleanup pass
- `rebuild_cleaned_commanders.py`: commander rebuild after cleanup/postfix work
- `build_scoring_framework_package.py`: scoring dataset and model inputs
- `build_ranking_package.py`: final ranking tables
- `build_interpretive_layer.py`: interpretation and profile outputs
- `build_ranking_dashboard.py`: static dashboard data bundle
- `qa_dashboard_snapshot.py`: dashboard QA checks

## Final Deliverable

The main deliverable lives here:

- `outputs_cleaned_2026-04-12_coalitionhardening_authoritative`

Useful files inside that snapshot:

- `outputs_cleaned_2026-04-12_coalitionhardening_authoritative/FINAL_SYSTEM_TRUST_ASSESSMENT.md`
- `outputs_cleaned_2026-04-12_coalitionhardening_authoritative/SCORING_FRAMEWORK.md`
- `outputs_cleaned_2026-04-12_coalitionhardening_authoritative/RANKING_RESULTS_HIERARCHICAL.csv`
- `outputs_cleaned_2026-04-12_coalitionhardening_authoritative/TOP_COMMANDERS_PROFILES.md`
- `outputs_cleaned_2026-04-12_coalitionhardening_authoritative/dashboard/index.html`

## Setup

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

## Run The Pipeline

Run the raw extraction pipeline:

```powershell
python .\battle_dataset_pipeline.py
```

Useful bounded run example:

```powershell
python .\battle_dataset_pipeline.py --max-list-pages 20 --max-candidate-pages 1500 --category-depth 1 --request-sleep 0.05
```

## Rebuild Ranking Outputs

From the workspace root:

```powershell
python .\build_scoring_framework_package.py
python .\build_ranking_package.py
python .\build_interpretive_layer.py
python .\build_ranking_dashboard.py
```

## Run The Dashboard

Quickest option:

```powershell
.\serve_dashboard.ps1
```

Manual option:

```powershell
cd .\outputs_cleaned_2026-04-12_coalitionhardening_authoritative\dashboard
python -m http.server 8000
```

Then open [http://127.0.0.1:8000](http://127.0.0.1:8000).

## Notes

- The ranking framework is intended to be conservative and auditable, not exhaustive.
- Remaining ambiguity is explicitly bounded in the authoritative snapshot documentation.
- Exact adjacent rank ordering should be treated more cautiously than stable top-tier groupings.
