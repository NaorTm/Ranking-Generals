# Ranking Generals

Historical general-ranking pipeline, cleaned evidence package, and static dashboard.

This repository builds a conservative commander-performance dataset from Wikipedia military-history pages, applies multiple audited ranking models, and publishes a frozen final dashboard for browsing the results.

## Live Links

- Repository: [NaorTm/Ranking-Generals](https://github.com/NaorTm/Ranking-Generals)
- Planned GitHub Pages dashboard: `https://naortm.github.io/Ranking-Generals/`
- Final authoritative snapshot: `outputs_cleaned_2026-04-21_conservativepatch_authoritative`

## What This Repo Contains

- extraction pipeline from Wikipedia list and category pages
- battle and commander cleanup/audit scripts
- scoring framework and ranking package builders
- interpretive reports and top-commander summaries
- a frozen static dashboard for the final authoritative snapshot

## Current Best Snapshot

The current best final system state is:

- `outputs_cleaned_2026-04-21_conservativepatch_authoritative`

Under the current methodology, this is the authoritative deliverable. The primary trusted ranking model is `hierarchical_weighted`.

Key files:

- `outputs_cleaned_2026-04-21_conservativepatch_authoritative/FINAL_SYSTEM_TRUST_ASSESSMENT.md`
- `outputs_cleaned_2026-04-21_conservativepatch_authoritative/SCORING_FRAMEWORK.md`
- `outputs_cleaned_2026-04-21_conservativepatch_authoritative/RANKING_RESULTS_HIERARCHICAL.csv`
- `outputs_cleaned_2026-04-21_conservativepatch_authoritative/TOP_COMMANDERS_PROFILES.md`

## Project Structure

- `battle_dataset_pipeline.py`: main extraction pipeline
- `cleanup_battles_clean.py`: battle cleanup stage
- `rebuild_cleaned_commanders.py`: commander rebuilds after cleanup/postfix actions
- `build_scoring_framework_package.py`: scoring features and scoring-layer outputs
- `build_ranking_package.py`: ranking tables and comparison outputs
- `build_interpretive_layer.py`: narrative summaries and profiles
- `build_ranking_dashboard.py`: static dashboard data bundle builder
- `qa_dashboard_snapshot.py`: dashboard QA checks
- `docs/`: GitHub Pages copy of the final dashboard

## Local Setup

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

## Run The Extraction Pipeline

Full run:

```powershell
python .\battle_dataset_pipeline.py
```

Bounded run example:

```powershell
python .\battle_dataset_pipeline.py --max-list-pages 20 --max-candidate-pages 1500 --category-depth 1 --request-sleep 0.05
```

## Rebuild The Ranking Outputs

From the repository root:

```powershell
python .\build_scoring_framework_package.py
python .\build_ranking_package.py
python .\build_interpretive_layer.py
python .\build_ranking_dashboard.py
```

## Run The Dashboard Locally

Quickest option:

```powershell
.\serve_dashboard.ps1
```

Manual option:

```powershell
cd .\outputs_cleaned_2026-04-21_conservativepatch_authoritative\dashboard
python -m http.server 8000
```

Then open `http://127.0.0.1:8000`.

## Publish The Dashboard To GitHub Pages

The repository includes a Pages-ready copy of the dashboard in `docs/`.

If the authoritative dashboard is rebuilt and you want to refresh the hosted site:

```powershell
.\sync_github_pages_dashboard.ps1
```

That copies the latest frozen dashboard assets from the authoritative snapshot into `docs/`.

## Trust Notes

- The framework is conservative and audit-oriented rather than exhaustive.
- Remaining ambiguity is explicitly documented in the authoritative snapshot.
- Stable cores and top tiers are more defensible than tiny adjacent rank differences.
- `hierarchical_full_credit` should be treated as diagnostic, not as the headline final model.
