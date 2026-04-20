from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from battles_clean_common import MAIN_FIELDNAMES, load_rows


ACTIONS_FIELDNAMES = [
    "row_number",
    "original_battle_id",
    "original_title",
    "decision",
    "reason_code",
    "rebuild_mode",
    "main_file_included",
    "quarantine_included",
    "removed_included",
]

QUARANTINE_FIELDNAMES = MAIN_FIELDNAMES + ["quarantine_reason", "validation_status"]
REMOVED_FIELDNAMES = MAIN_FIELDNAMES + ["removal_reason", "validation_status"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Reconcile cleanup snapshot outputs to one final row per original battle_id.")
    parser.add_argument("--snapshot-dir", default="outputs_cleaned_2026-04-07")
    parser.add_argument("--original-csv", default="outputs_final_2026-04-05/battles_clean.csv")
    return parser.parse_args()


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def dedupe_latest(rows: list[dict[str, str]], key_field: str) -> dict[str, dict[str, str]]:
    latest: dict[str, dict[str, str]] = {}
    for row in rows:
        key = row.get(key_field, "")
        if key:
            latest[key] = row
    return latest


def main() -> None:
    args = parse_args()
    snapshot_dir = Path(args.snapshot_dir)
    original_rows = load_rows(Path(args.original_csv))

    actions = load_rows(snapshot_dir / "cleanup_actions.csv")
    main_rows = load_rows(snapshot_dir / "battles_clean.csv")
    quarantine_rows = load_rows(snapshot_dir / "battles_clean_quarantine.csv")
    removed_rows = load_rows(snapshot_dir / "battles_clean_removed_false_positives.csv")

    latest_actions = dedupe_latest(actions, "original_battle_id")
    latest_main = dedupe_latest(main_rows, "battle_id")
    latest_quarantine = dedupe_latest(quarantine_rows, "battle_id")
    latest_removed = dedupe_latest(removed_rows, "battle_id")
    original_by_id = {row["battle_id"]: row for row in original_rows}

    final_actions: list[dict[str, object]] = []
    final_main_rows: list[dict[str, object]] = []
    final_quarantine_rows: list[dict[str, object]] = []
    final_removed_rows: list[dict[str, object]] = []

    for original_row in original_rows:
        battle_id = original_row["battle_id"]
        action = latest_actions.get(battle_id)
        if not action:
            continue
        final_actions.append(action)
        decision = action.get("decision", "")
        if decision in {"kept", "repaired"}:
            row = latest_main.get(battle_id)
            if row:
                final_main_rows.append(row)
        elif decision == "quarantined":
            row = latest_quarantine.get(battle_id)
            if not row:
                source_row = latest_main.get(battle_id) or latest_removed.get(battle_id) or original_by_id.get(battle_id, {})
                row = {field: source_row.get(field, "") for field in MAIN_FIELDNAMES}
                row["quarantine_reason"] = action.get("reason_code", "") or "quarantined_after_reconcile"
                row["validation_status"] = "quarantined"
            final_quarantine_rows.append(row)
        elif decision == "removed_false_positive":
            row = latest_removed.get(battle_id)
            if row:
                final_removed_rows.append(row)

    write_csv(snapshot_dir / "cleanup_actions.csv", ACTIONS_FIELDNAMES, final_actions)
    write_csv(snapshot_dir / "battles_clean.csv", MAIN_FIELDNAMES, final_main_rows)
    write_csv(snapshot_dir / "battles_clean_quarantine.csv", QUARANTINE_FIELDNAMES, final_quarantine_rows)
    write_csv(snapshot_dir / "battles_clean_removed_false_positives.csv", REMOVED_FIELDNAMES, final_removed_rows)

    counts = {
        "original_rows": len(original_rows),
        "kept": sum(1 for row in final_actions if row.get("decision") == "kept"),
        "repaired": sum(1 for row in final_actions if row.get("decision") == "repaired"),
        "quarantined": sum(1 for row in final_actions if row.get("decision") == "quarantined"),
        "removed_false_positive": sum(1 for row in final_actions if row.get("decision") == "removed_false_positive"),
        "final_main_rows": len(final_main_rows),
        "final_quarantine_rows": len(final_quarantine_rows),
        "final_removed_rows": len(final_removed_rows),
    }
    counts["reconciliation_ok"] = (
        counts["final_main_rows"] + counts["final_quarantine_rows"] + counts["final_removed_rows"] == counts["original_rows"]
    )
    (snapshot_dir / "cleanup_summary.json").write_text(json.dumps(counts, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(counts, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
