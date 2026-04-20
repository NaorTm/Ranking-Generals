from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

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
    parser = argparse.ArgumentParser(description="Apply post-fix audit blockers to a cleaned snapshot.")
    parser.add_argument("--snapshot-dir", default="outputs_cleaned_2026-04-07_authoritative")
    parser.add_argument("--audit-dir", default=None)
    return parser.parse_args()


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main() -> None:
    args = parse_args()
    snapshot_dir = Path(args.snapshot_dir)
    audit_dir = Path(args.audit_dir) if args.audit_dir else snapshot_dir / "postfix_audit"

    main_path = snapshot_dir / "battles_clean.csv"
    quarantine_path = snapshot_dir / "battles_clean_quarantine.csv"
    removed_path = snapshot_dir / "battles_clean_removed_false_positives.csv"
    actions_path = snapshot_dir / "cleanup_actions.csv"
    summary_path = snapshot_dir / "cleanup_summary.json"
    audit_path = audit_dir / "row_audit.csv"

    main_rows = load_rows(main_path)
    quarantine_rows = load_rows(quarantine_path)
    removed_rows = load_rows(removed_path)
    actions_rows = load_rows(actions_path)
    audit_rows = load_rows(audit_path)

    blockers_by_id = {
        row["battle_id"]: [part for part in row.get("blockers", "").split("|") if part]
        for row in audit_rows
        if row.get("status") == "blocker" and row.get("battle_id")
    }

    kept_main: list[dict[str, Any]] = []
    moved_quarantine: list[dict[str, Any]] = []

    for row in main_rows:
        battle_id = row.get("battle_id", "")
        blockers = blockers_by_id.get(battle_id, [])
        if not blockers:
            kept_main.append(row)
            continue
        quarantine_row = {field: row.get(field, "") for field in MAIN_FIELDNAMES}
        quarantine_row["quarantine_reason"] = "postfix_audit:" + "|".join(blockers)
        quarantine_row["validation_status"] = "quarantined_after_postfix_audit"
        moved_quarantine.append(quarantine_row)

    quarantine_rows.extend(moved_quarantine)

    updated_actions: list[dict[str, Any]] = []
    for row in actions_rows:
        battle_id = row.get("original_battle_id", "")
        blockers = blockers_by_id.get(battle_id, [])
        if blockers:
            updated = dict(row)
            updated["decision"] = "quarantined"
            updated["reason_code"] = "postfix_audit:" + "|".join(blockers)
            updated["main_file_included"] = "false"
            updated["quarantine_included"] = "true"
            updated["removed_included"] = "false"
            updated_actions.append(updated)
        else:
            updated_actions.append(row)

    original_rows = len(kept_main) + len(quarantine_rows) + len(removed_rows)
    kept_count = sum(1 for row in updated_actions if row.get("decision") == "kept")
    repaired_count = sum(1 for row in updated_actions if row.get("decision") == "repaired")
    quarantined_count = sum(1 for row in updated_actions if row.get("decision") == "quarantined")
    removed_count = sum(1 for row in updated_actions if row.get("decision") == "removed_false_positive")

    write_csv(main_path, MAIN_FIELDNAMES, kept_main)
    write_csv(quarantine_path, QUARANTINE_FIELDNAMES, quarantine_rows)
    write_csv(removed_path, REMOVED_FIELDNAMES, removed_rows)
    write_csv(actions_path, ACTIONS_FIELDNAMES, updated_actions)

    summary = {
        "original_rows": original_rows,
        "kept": kept_count,
        "repaired": repaired_count,
        "quarantined": quarantined_count,
        "removed_false_positive": removed_count,
        "final_main_rows": len(kept_main),
        "final_quarantine_rows": len(quarantine_rows),
        "final_removed_rows": len(removed_rows),
        "postfix_audit_moved_to_quarantine": len(moved_quarantine),
        "reconciliation_ok": len(kept_main) + len(quarantine_rows) + len(removed_rows) == original_rows,
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
