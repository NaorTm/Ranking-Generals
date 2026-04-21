# Commander Ranking Dashboard

This folder contains a static, client-side dashboard built on top of the frozen ranking package in `outputs_cleaned_2026-04-21_fullpopulation_authoritative`.

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
