# Commander Ranking Dashboard

This folder contains the published static dashboard for `outputs_cleaned_2026-04-21_fullpopulation_authoritative`.

Read it as a conservative, audited ranking framework:

- tiers first
- exact ranks second
- confidence labels as primary interpretation
- residual ambiguity as an explicit part of the system, not hidden failure

## Open locally

Default option:

1. Open [index.html](C:/Users/gameo/OneDrive/Desktop/test/outputs_cleaned_2026-04-21_fullpopulation_authoritative/dashboard/index.html) in a browser.

If your browser blocks local file scripts, use a trivial local server instead:

```powershell
cd C:\Users\gameo\OneDrive\Desktop\test\outputs_cleaned_2026-04-21_fullpopulation_authoritative\dashboard
python -m http.server 8000
```

Then open `http://localhost:8000`.

## Files

- `index.html`: dashboard shell
- `styles.css`: dashboard styling
- `app.js`: client-side interactions and chart rendering
- `dashboard_data.js`: prebuilt browser dataset generated from the frozen ranking outputs
- `plotly.min.js`: bundled plotting library for offline/local use

## Rebuild the data layer

From the workspace root:

```powershell
cd C:\Users\gameo\OneDrive\Desktop\test
python build_ranking_dashboard.py
```

That rebuilds `dashboard/dashboard_data.js` and updates [RANKING_DASHBOARD_TECHNICAL_NOTE.md](C:/Users/gameo/OneDrive/Desktop/test/outputs_cleaned_2026-04-21_fullpopulation_authoritative/RANKING_DASHBOARD_TECHNICAL_NOTE.md).

## Publication Notes

- the full ranked population behind this release was reviewed
- the release is globally defensible at the framework level
- exact adjacent ordering is not fully settled in every case
- remaining unresolved cases reflect conservative evidence rules, not silent breakage
