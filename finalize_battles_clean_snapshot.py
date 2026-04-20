from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from battles_clean_common import (
    MAIN_FIELDNAMES,
    generic_false_positive_reasons,
    load_rows,
    main_row_blockers,
    normalize_bool,
    normalize_text,
    sanitize_candidate_row,
)


ACTIONS_FIELDNAMES = [
    "original_battle_id",
    "original_title",
    "decision",
    "reason_code",
    "candidate_source",
    "main_file_included",
    "quarantine_included",
    "removed_included",
]

QUARANTINE_FIELDNAMES = MAIN_FIELDNAMES + ["quarantine_reason", "validation_status"]
REMOVED_FIELDNAMES = MAIN_FIELDNAMES + ["removal_reason", "validation_status"]
AUDIT_FIELDNAMES = ["battle_id", "wikipedia_title", "status", "blockers"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a coherent final cleaned snapshot from noisy cleanup artifacts.")
    parser.add_argument("--original-csv", default="outputs_final_2026-04-05/battles_clean.csv")
    parser.add_argument("--source-snapshot-dir", default="outputs_cleaned_2026-04-07")
    parser.add_argument("--output-dir", default="outputs_cleaned_2026-04-07_final")
    return parser.parse_args()


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def candidate_source_rows(source_dir: Path) -> dict[str, list[tuple[str, dict[str, Any]]]]:
    mapping: dict[str, list[tuple[str, dict[str, Any]]]] = defaultdict(list)
    for name in [
        "battles_clean.csv",
        "battles_clean_quarantine.csv",
        "battles_clean_removed_false_positives.csv",
    ]:
        path = source_dir / name
        if not path.exists():
            continue
        for row in load_rows(path):
            battle_id = row.get("battle_id", "")
            if not battle_id:
                continue
            core_row = {field: row.get(field, "") for field in MAIN_FIELDNAMES}
            mapping[battle_id].append((name, sanitize_candidate_row(core_row, f"finalize:{name}")))
    return mapping


def evidence_score(row: dict[str, Any]) -> int:
    score = 0
    if normalize_bool(row.get("infobox_present")) == "true":
        score += 2
    if normalize_text(row.get("date_raw")):
        score += 2
    if normalize_text(row.get("result_type")) != "unknown":
        score += 1
    if normalize_text(row.get("belligerent_1_raw")) and normalize_text(row.get("belligerent_2_raw")):
        score += 2
    if normalize_text(row.get("commander_side_a_raw")) or normalize_text(row.get("commander_side_b_raw")):
        score += 1
    if normalize_text(row.get("location_raw")):
        score += 1
    if normalize_text(row.get("war_name")):
        score += 1
    return score


def choose_best_zero_blocker(candidates: list[tuple[str, dict[str, Any]]], title: str) -> tuple[str, dict[str, Any]] | None:
    valid_candidates: list[tuple[int, int, str, dict[str, Any]]] = []
    for source_name, row in candidates:
        blockers = main_row_blockers(title, row, row.get("categories", "").split(" | ") if row.get("categories") else [])
        if not blockers:
            source_priority = 0 if source_name == "battles_clean.csv" else 1 if source_name == "battles_clean_quarantine.csv" else 2 if source_name == "original" else 3
            valid_candidates.append((source_priority, -evidence_score(row), source_name, row))
    if not valid_candidates:
        return None
    valid_candidates.sort()
    _priority, _neg_score, source_name, row = valid_candidates[0]
    return source_name, row


def strong_false_positive(title: str, row: dict[str, Any]) -> list[str]:
    reasons = generic_false_positive_reasons(title, row, row.get("categories", "").split(" | ") if row.get("categories") else [])
    strong = [reason for reason in reasons if reason in {"known_false_positive", "biography_title_signal", "no_event_specific_fields"}]
    return strong


def cleanup_rules_text() -> str:
    return """# Battle File Cleanup Rules

- Main rows must pass the cleanup blocker check with zero blockers.
- False positives are removed when a row shows strong non-conflict signals such as known false-positive titles, biography-style titles, or no event-specific fields.
- Rows that are not confidently clean but still look like military conflict entries are quarantined rather than kept.
- Candidate rows are chosen from the union of original frozen rows and rebuilt cleanup artifacts, preferring zero-blocker candidates with stronger event evidence.
- Main rows may keep `result_type=unknown`, but not malformed or contradictory result fields.
- Main rows may not keep malformed or low-confidence date fields.
"""


def main() -> None:
    args = parse_args()
    original_rows = load_rows(Path(args.original_csv))
    original_by_id = {row["battle_id"]: sanitize_candidate_row({field: row.get(field, "") for field in MAIN_FIELDNAMES}, "finalize:original") for row in original_rows}
    source_candidates = candidate_source_rows(Path(args.source_snapshot_dir))
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    final_main: list[dict[str, Any]] = []
    final_quarantine: list[dict[str, Any]] = []
    final_removed: list[dict[str, Any]] = []
    final_actions: list[dict[str, Any]] = []
    audit_rows: list[dict[str, Any]] = []

    counts = {"kept": 0, "repaired": 0, "quarantined": 0, "removed_false_positive": 0}

    for original in original_rows:
        battle_id = original["battle_id"]
        title = original["wikipedia_title"]
        candidates = [("original", original_by_id[battle_id])]
        candidates.extend(source_candidates.get(battle_id, []))

        best_valid = choose_best_zero_blocker(candidates, title)
        if best_valid:
            source_name, row = best_valid
            final_main.append(row)
            decision = "kept" if source_name == "original" else "repaired"
            counts[decision] += 1
            final_actions.append(
                {
                    "original_battle_id": battle_id,
                    "original_title": title,
                    "decision": decision,
                    "reason_code": "",
                    "candidate_source": source_name,
                    "main_file_included": "true",
                    "quarantine_included": "false",
                    "removed_included": "false",
                }
            )
            audit_rows.append({"battle_id": battle_id, "wikipedia_title": title, "status": "ok", "blockers": ""})
            continue

        best_candidate = sorted(
            candidates,
            key=lambda item: (
                len(main_row_blockers(title, item[1], item[1].get("categories", "").split(" | ") if item[1].get("categories") else [])),
                -evidence_score(item[1]),
            ),
        )[0]
        source_name, row = best_candidate
        blockers = main_row_blockers(title, row, row.get("categories", "").split(" | ") if row.get("categories") else [])
        strong_fp = strong_false_positive(title, row)

        if strong_fp:
            removed_row = {field: row.get(field, "") for field in MAIN_FIELDNAMES}
            removed_row["removal_reason"] = "|".join(strong_fp)
            removed_row["validation_status"] = "removed_false_positive"
            final_removed.append(removed_row)
            counts["removed_false_positive"] += 1
            final_actions.append(
                {
                    "original_battle_id": battle_id,
                    "original_title": title,
                    "decision": "removed_false_positive",
                    "reason_code": "|".join(strong_fp),
                    "candidate_source": source_name,
                    "main_file_included": "false",
                    "quarantine_included": "false",
                    "removed_included": "true",
                }
            )
            continue

        quarantine_row = {field: row.get(field, "") for field in MAIN_FIELDNAMES}
        quarantine_row["quarantine_reason"] = "|".join(blockers) or "unvalidated_conflict_row"
        quarantine_row["validation_status"] = "quarantined"
        final_quarantine.append(quarantine_row)
        counts["quarantined"] += 1
        final_actions.append(
            {
                "original_battle_id": battle_id,
                "original_title": title,
                "decision": "quarantined",
                "reason_code": quarantine_row["quarantine_reason"],
                "candidate_source": source_name,
                "main_file_included": "false",
                "quarantine_included": "true",
                "removed_included": "false",
            }
        )

    write_csv(output_dir / "battles_clean.csv", MAIN_FIELDNAMES, final_main)
    write_csv(output_dir / "battles_clean_quarantine.csv", QUARANTINE_FIELDNAMES, final_quarantine)
    write_csv(output_dir / "battles_clean_removed_false_positives.csv", REMOVED_FIELDNAMES, final_removed)
    write_csv(output_dir / "cleanup_actions.csv", ACTIONS_FIELDNAMES, final_actions)
    (output_dir / "CLEANUP_RULES.md").write_text(cleanup_rules_text(), encoding="utf-8")

    audit_dir = output_dir / "postfix_audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    write_csv(audit_dir / "row_audit.csv", AUDIT_FIELDNAMES, audit_rows)
    audit_summary = {
        "rows_checked": len(final_main),
        "blocker_rows": 0,
        "ok_rows": len(final_main),
        "blocker_counts": {},
    }
    (audit_dir / "summary.json").write_text(json.dumps(audit_summary, ensure_ascii=False, indent=2), encoding="utf-8")

    summary = {
        "original_rows": len(original_rows),
        **counts,
        "final_main_rows": len(final_main),
        "final_quarantine_rows": len(final_quarantine),
        "final_removed_rows": len(final_removed),
        "reconciliation_ok": len(final_main) + len(final_quarantine) + len(final_removed) == len(original_rows),
    }
    (output_dir / "cleanup_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
