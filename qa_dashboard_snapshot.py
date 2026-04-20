from __future__ import annotations

import argparse
import json
import threading
import time
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pandas as pd
from playwright.sync_api import sync_playwright


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run browser QA against a rebuilt dashboard snapshot.")
    parser.add_argument("--snapshot-dir", type=Path, required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    return parser.parse_args()


def read_expected(snapshot_dir: Path) -> dict[str, object]:
    ranking_metrics = json.loads((snapshot_dir / "RANKING_BUILD_METRICS.json").read_text(encoding="utf-8"))
    commander_count = len(pd.read_csv(snapshot_dir / "RANKING_RESULTS_SENSITIVITY.csv", dtype=str).fillna(""))
    return {
        "commander_count": commander_count,
        "baseline_leader": ranking_metrics["top_baseline"][0]["display_name"],
        "hierarchical_leader": ranking_metrics["top_hierarchical"][0]["display_name"],
    }


def start_server(directory: Path, host: str, port: int) -> tuple[ThreadingHTTPServer, threading.Thread]:
    handler = partial(SimpleHTTPRequestHandler, directory=str(directory))
    server = ThreadingHTTPServer((host, port), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def table_rows(page) -> list[list[str]]:
    rows = []
    for row in page.locator("#explorer-table tbody tr").all():
        cells = [cell.inner_text().strip() for cell in row.locator("td").all()]
        if cells:
            rows.append(cells)
    return rows


def parse_rank(value: str) -> int:
    return int(value.replace("#", "").strip())


def parse_number(value: str) -> int:
    return int(value.replace(",", "").strip())


def chart_trace_count(page, selector: str) -> int:
    return int(
        page.evaluate(
            """selector => {
                const node = document.querySelector(selector);
                return node && Array.isArray(node.data) ? node.data.length : 0;
            }""",
            selector,
        )
    )


def run_checks(snapshot_dir: Path, host: str, port: int) -> dict[str, object]:
    dashboard_dir = snapshot_dir / "dashboard"
    expected = read_expected(snapshot_dir)
    summary: dict[str, object] = {
        "snapshot": snapshot_dir.name,
        "dashboard_dir": str(dashboard_dir),
        "expected": expected,
        "checks": {},
        "console_errors": [],
        "page_errors": [],
    }

    server, _thread = start_server(dashboard_dir, host, port)
    time.sleep(0.5)
    url = f"http://{host}:{port}/"

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1440, "height": 2200})
            page.on("console", lambda message: summary["console_errors"].append({"type": message.type, "text": message.text}) if message.type == "error" else None)
            page.on("pageerror", lambda exc: summary["page_errors"].append(str(exc)))

            response = page.goto(url, wait_until="networkidle", timeout=120000)
            page.wait_for_timeout(1500)

            summary["checks"]["http_load"] = {
                "ok": bool(response and response.ok),
                "status": response.status if response else None,
                "url": url,
            }
            summary["checks"]["title"] = {
                "ok": "Commander Ranking Analysis" in page.title(),
                "value": page.title(),
            }

            commander_count_text = page.locator("#commander-count").inner_text().strip().replace(",", "")
            snapshot_label = page.locator("#snapshot-label").inner_text().strip()
            summary["checks"]["header_metadata"] = {
                "ok": int(commander_count_text) == expected["commander_count"] and snapshot_label == snapshot_dir.name,
                "commander_count": int(commander_count_text),
                "snapshot_label": snapshot_label,
            }

            chart_ids = [
                "#leaderboard-chart",
                "#movement-chart",
                "#sensitivity-chart",
                "#page-dependence-chart",
                "#page-composition-chart",
                "#era-chart",
                "#outcome-chart",
            ]
            panel_counts = {chart_id: chart_trace_count(page, chart_id) for chart_id in chart_ids}
            summary["checks"]["panel_render"] = {
                "ok": all(count > 0 for count in panel_counts.values())
                and page.locator("#overview-cards .metric-card").count() >= 4
                and page.locator("#top-tier-columns .tier-column").count() >= 3
                and page.locator("#comparison-cards article").count() >= 1
                and page.locator("#audit-list li").count() >= 1
                and page.locator("#era-shortlist-list li").count() >= 1
                and page.locator("#explorer-table tbody tr").count() >= 10,
                "chart_trace_counts": panel_counts,
                "overview_cards": page.locator("#overview-cards .metric-card").count(),
                "tier_columns": page.locator("#top-tier-columns .tier-column").count(),
                "comparison_cards": page.locator("#comparison-cards article").count(),
                "audit_rows": page.locator("#audit-list li").count(),
                "shortlist_rows": page.locator("#era-shortlist-list li").count(),
                "explorer_rows": page.locator("#explorer-table tbody tr").count(),
            }

            initial_rows = table_rows(page)
            summary["checks"]["baseline_alignment"] = {
                "ok": bool(initial_rows) and initial_rows[0][0] == expected["baseline_leader"],
                "leader_from_table": initial_rows[0][0] if initial_rows else None,
                "expected_leader": expected["baseline_leader"],
            }

            page.select_option("#model-select", "hierarchical_weighted")
            page.wait_for_timeout(700)
            hier_rows = table_rows(page)
            summary["checks"]["hierarchical_alignment"] = {
                "ok": bool(hier_rows) and hier_rows[0][0] == expected["hierarchical_leader"],
                "leader_from_table": hier_rows[0][0] if hier_rows else None,
                "expected_leader": expected["hierarchical_leader"],
            }

            page.select_option("#model-select", "baseline_conservative")
            page.wait_for_timeout(400)
            page.fill("#search-input", "Alexander Suvorov")
            page.wait_for_timeout(500)
            search_rows = table_rows(page)
            summary["checks"]["search"] = {
                "ok": len(search_rows) >= 1 and all("Alexander Suvorov" in row[0] for row in search_rows),
                "rows_after_search": len(search_rows),
                "first_row": search_rows[0][0] if search_rows else None,
            }

            page.fill("#search-input", "")
            page.select_option("#robustness-filter", "robust_elite")
            page.wait_for_timeout(500)
            robust_rows = table_rows(page)
            summary["checks"]["filtering"] = {
                "ok": len(robust_rows) >= 1 and all("Robust elite" in row[2] for row in robust_rows),
                "rows_after_filter": len(robust_rows),
            }

            page.select_option("#robustness-filter", "all")
            page.wait_for_timeout(400)

            page.locator("#explorer-table thead th[data-sort-key='engagements']").click()
            page.wait_for_timeout(300)
            desc_rows = table_rows(page)
            desc_values = [parse_number(row[4]) for row in desc_rows[:5]]
            page.locator("#explorer-table thead th[data-sort-key='engagements']").click()
            page.wait_for_timeout(300)
            asc_rows = table_rows(page)
            asc_values = [parse_number(row[4]) for row in asc_rows[:5]]
            summary["checks"]["sorting"] = {
                "ok": desc_values == sorted(desc_values, reverse=True) and asc_values == sorted(asc_values),
                "descending_sample": desc_values,
                "ascending_sample": asc_values,
            }

            page.locator("#explorer-table tbody tr").nth(0).click()
            page.wait_for_timeout(300)
            page.locator("#explorer-table tbody tr").nth(1).click()
            page.wait_for_timeout(500)
            summary["checks"]["selection_and_comparison"] = {
                "ok": page.locator("#selected-commander-chips .chip").count() >= 2
                and page.locator("#comparison-cards article").count() >= 2,
                "selected_chip_count": page.locator("#selected-commander-chips .chip").count(),
                "comparison_card_count": page.locator("#comparison-cards article").count(),
            }

            page.locator("#clear-selection-button").click()
            page.wait_for_timeout(300)
            summary["checks"]["clear_selection"] = {
                "ok": page.locator("#selected-commander-chips .chip").count() == 0,
                "selected_chip_count": page.locator("#selected-commander-chips .chip").count(),
            }

            summary["checks"]["console_clean"] = {
                "ok": len(summary["console_errors"]) == 0 and len(summary["page_errors"]) == 0,
                "console_error_count": len(summary["console_errors"]),
                "page_error_count": len(summary["page_errors"]),
            }

            browser.close()
    finally:
        server.shutdown()
        server.server_close()

    summary["all_checks_passed"] = all(check.get("ok") for check in summary["checks"].values())
    return summary


def main() -> None:
    args = parse_args()
    summary = run_checks(args.snapshot_dir, args.host, args.port)
    output_path = args.snapshot_dir / "dashboard_qa_summary.json"
    output_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
