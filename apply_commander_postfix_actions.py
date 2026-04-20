from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from commander_clean_common import (
    BATTLE_COMMANDER_FIELDNAMES,
    COMMANDER_QUARANTINE_FIELDNAMES,
    MASTER_FIELDNAMES,
    build_commanders_master,
    dedupe_commander_rows,
    load_rows,
    normalize_text,
    summarize_reasons,
    write_csv,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Apply commander post-fix audit blockers to the snapshot.")
    parser.add_argument("--snapshot-dir", default="outputs_cleaned_2026-04-09_authoritative")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    snapshot_dir = Path(args.snapshot_dir)
    audit_dir = snapshot_dir / "commander_postfix_audit"

    main_rows = load_rows(snapshot_dir / "battle_commanders.csv")
    quarantine_rows = load_rows(snapshot_dir / "battle_commanders_quarantine.csv")
    side_issue_rows = load_rows(snapshot_dir / "battle_commander_side_issues.csv")
    row_audit = load_rows(audit_dir / "row_audit.csv")

    blocker_keys = {
        "||".join(
            [
                normalize_text(row.get("battle_id")),
                normalize_text(row.get("commander_name_normalized")).lower(),
                normalize_text(row.get("commander_wikipedia_url")).lower(),
            ]
        ): normalize_text(row.get("blockers"))
        for row in row_audit
        if row.get("status") == "blocker"
    }

    kept_rows: list[dict[str, Any]] = []
    moved_rows: list[dict[str, Any]] = []
    for row in main_rows:
        key = "||".join(
            [
                normalize_text(row.get("battle_id")),
                normalize_text(row.get("commander_name_normalized")).lower(),
                normalize_text(row.get("commander_wikipedia_url")).lower(),
            ]
        )
        blockers = blocker_keys.get(key, "")
        if blockers:
            quarantine_row = {field: row.get(field, "") for field in BATTLE_COMMANDER_FIELDNAMES}
            quarantine_row["quarantine_reason"] = f"postfix_audit:{blockers}"
            quarantine_row["candidate_source"] = "postfix_audit"
            quarantine_row["validation_status"] = "quarantined_after_postfix_audit"
            moved_rows.append(quarantine_row)
        else:
            kept_rows.append(row)

    quarantine_rows.extend(moved_rows)
    kept_rows = dedupe_commander_rows(kept_rows)
    quarantine_rows = dedupe_commander_rows(quarantine_rows)
    master_rows = build_commanders_master(kept_rows)

    write_csv(snapshot_dir / "battle_commanders.csv", BATTLE_COMMANDER_FIELDNAMES, kept_rows)
    write_csv(snapshot_dir / "battle_commanders_quarantine.csv", COMMANDER_QUARANTINE_FIELDNAMES, quarantine_rows)
    write_csv(snapshot_dir / "commanders_master.csv", MASTER_FIELDNAMES, master_rows)

    summary = {
        "input_battles": len(load_rows(snapshot_dir / "battles_clean.csv")),
        "battles_with_any_commander_rows": len({row["battle_id"] for row in kept_rows}),
        "battle_commander_rows": len(kept_rows),
        "battle_commander_quarantine_rows": len(quarantine_rows),
        "battle_commander_side_issues": len(side_issue_rows),
        "commanders_master_rows": len(master_rows),
        "linked_commander_rows": sum(1 for row in kept_rows if normalize_text(row.get("commander_wikipedia_url"))),
        "unlinked_commander_rows": sum(1 for row in kept_rows if not normalize_text(row.get("commander_wikipedia_url"))),
        "identity_confidence_counts": dict(Counter(normalize_text(row["identity_confidence"]) for row in kept_rows)),
        "quarantine_reason_counts": summarize_reasons(quarantine_rows, "quarantine_reason"),
        "postfix_audit_moved_to_quarantine": len(moved_rows),
    }
    (snapshot_dir / "commander_cleanup_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
