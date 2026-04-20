from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from battle_dataset_pipeline import build_commanders_master, build_quality_report, compute_run_metrics


def read_csv_if_exists(path: Path) -> pd.DataFrame:
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


def reconcile_candidate_statuses(candidates: pd.DataFrame, battles_clean: pd.DataFrame, issues: pd.DataFrame) -> pd.DataFrame:
    if candidates.empty:
        return candidates

    candidates = candidates.copy()
    candidates["metadata_accepted"] = candidates["metadata_accepted"].astype(str).str.lower().isin(["true", "1", "yes", "y"])

    accepted_by_title: dict[str, dict[str, str]] = {}
    if not battles_clean.empty:
        for _, row in battles_clean.iterrows():
            title = str(row.get("wikipedia_title", "")).strip()
            if not title:
                continue
            accepted_by_title[title] = {
                "final_page_type": str(row.get("page_type", "") or ""),
                "final_acceptance_reason": str(row.get("acceptance_reason", "") or ""),
            }

    issue_status_priority = {
        "rate_limit": 5,
        "protection": 5,
        "fetch_error": 5,
        "missing_or_unavailable": 5,
        "task_timeout": 4,
        "worker_exit": 4,
        "rejected_candidate": 3,
    }
    issue_statuses: dict[str, dict[str, str | int]] = {}
    if not issues.empty:
        for _, row in issues.iterrows():
            title = str(row.get("page_title", "")).strip()
            issue_type = str(row.get("issue_type", "")).strip()
            if not title or not issue_type:
                continue
            mapped_status = "rejected_after_full_fetch" if issue_type == "rejected_candidate" else issue_type
            priority = issue_status_priority.get(issue_type, 1)
            previous = issue_statuses.get(title)
            if previous and int(previous["priority"]) > priority:
                continue
            issue_statuses[title] = {
                "full_fetch_status": mapped_status,
                "final_acceptance_reason": str(row.get("message", "") or ""),
                "priority": priority,
            }

    reconciled_rows: list[dict[str, object]] = []
    for row in candidates.to_dict(orient="records"):
        title = str(row.get("candidate_title", "")).strip()
        if title in accepted_by_title:
            row["full_fetch_status"] = "accepted"
            row["final_page_type"] = accepted_by_title[title]["final_page_type"]
            if accepted_by_title[title]["final_acceptance_reason"]:
                row["final_acceptance_reason"] = accepted_by_title[title]["final_acceptance_reason"]
        elif title in issue_statuses:
            row["full_fetch_status"] = issue_statuses[title]["full_fetch_status"]
            if issue_statuses[title]["final_acceptance_reason"]:
                row["final_acceptance_reason"] = issue_statuses[title]["final_acceptance_reason"]
        elif row.get("metadata_accepted"):
            row["full_fetch_status"] = "pending"
        else:
            row["full_fetch_status"] = "skipped_rejected"
        reconciled_rows.append(row)

    return pd.DataFrame(reconciled_rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Merge shard extraction outputs.")
    parser.add_argument("--shards-dir", required=True, help="Parent directory containing shard output folders.")
    parser.add_argument("--output-dir", required=True, help="Merged output directory.")
    args = parser.parse_args()

    shards_dir = Path(args.shards_dir).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    shard_dirs = sorted([path for path in shards_dir.iterdir() if path.is_dir()])
    if not shard_dirs:
        raise SystemExit("No shard directories found.")

    battles_raw = pd.concat([read_csv_if_exists(path / "battles_raw.csv") for path in shard_dirs], ignore_index=True)
    battles_clean = pd.concat([read_csv_if_exists(path / "battles_clean.csv") for path in shard_dirs], ignore_index=True)
    commanders = pd.concat([read_csv_if_exists(path / "battle_commanders.csv") for path in shard_dirs], ignore_index=True)
    issues = pd.concat([read_csv_if_exists(path / "extraction_issues.csv") for path in shard_dirs], ignore_index=True)
    sources = pd.concat([read_csv_if_exists(path / "sources_index.csv") for path in shard_dirs], ignore_index=True)
    candidates = pd.concat([read_csv_if_exists(path / "candidate_battle_pages.csv") for path in shard_dirs], ignore_index=True)

    if not battles_raw.empty:
        battles_raw = battles_raw.drop_duplicates(subset=["battle_id"]).sort_values(["battle_name", "source_url"])
    if not battles_clean.empty:
        battles_clean = battles_clean.drop_duplicates(subset=["battle_id"]).sort_values(["year", "battle_name"], na_position="last")
    if not commanders.empty:
        commanders = commanders.drop_duplicates(subset=["battle_id", "commander_name_normalized", "side", "source_url"])
        commanders = commanders.sort_values(["commander_name_normalized", "year", "battle_name"], na_position="last")
    if not issues.empty:
        issues = issues.drop_duplicates()
    if not sources.empty:
        sources = sources.drop_duplicates()
    if not candidates.empty:
        candidates = candidates.drop_duplicates()

    commanders_master, commander_master_issues = build_commanders_master(commanders, 97)
    if commander_master_issues:
        issues = pd.concat([issues, pd.DataFrame(commander_master_issues)], ignore_index=True).drop_duplicates()

    candidates = reconcile_candidate_statuses(candidates, battles_clean, issues)

    battles_raw.to_csv(output_dir / "battles_raw.csv", index=False, encoding="utf-8-sig")
    battles_clean.to_csv(output_dir / "battles_clean.csv", index=False, encoding="utf-8-sig")
    commanders.to_csv(output_dir / "battle_commanders.csv", index=False, encoding="utf-8-sig")
    commanders_master.to_csv(output_dir / "commanders_master.csv", index=False, encoding="utf-8-sig")
    issues.to_csv(output_dir / "extraction_issues.csv", index=False, encoding="utf-8-sig")
    sources.to_csv(output_dir / "sources_index.csv", index=False, encoding="utf-8-sig")
    candidates.to_csv(output_dir / "candidate_battle_pages.csv", index=False, encoding="utf-8-sig")

    coverage_context = {
        "root_pages": [f"merged_shards:{shards_dir.name}"],
        "list_pages": [],
        "category_discovery_used": True,
        "configured_bounds": {},
    }
    run_metrics = compute_run_metrics(
        battles_clean,
        commanders,
        commanders_master,
        issues,
        candidates.to_dict(orient="records"),
        sources.to_dict(orient="records"),
        coverage_context=coverage_context,
    )
    (output_dir / "run_metrics.json").write_text(json.dumps(run_metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    build_quality_report(
        battles_clean if not battles_clean.empty else pd.DataFrame(columns=["battle_id", "result_raw", "year", "battle_type"]),
        commanders if not commanders.empty else pd.DataFrame(columns=["battle_id", "commander_wikipedia_url"]),
        commanders_master if not commanders_master.empty else pd.DataFrame(columns=["commander_id"]),
        issues if not issues.empty else pd.DataFrame(columns=["severity", "page_title", "issue_type", "field_name", "message"]),
        candidates.to_dict(orient="records"),
        sources.to_dict(orient="records"),
        output_dir / "data_quality_report.md",
        previous_metrics=None,
        coverage_context=coverage_context,
    )


if __name__ == "__main__":
    main()
