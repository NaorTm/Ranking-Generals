from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import battle_dataset_pipeline as bdp
from battles_clean_common import (
    MAIN_FIELDNAMES,
    build_full_parse_candidate,
    build_origin_map,
    build_wikitext_candidate,
    decide_rebuild_result,
    fetch_page_wikitext_batch,
    load_rows,
    main_row_blockers,
    rows_differ,
    sanitize_candidate_row,
)


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
    parser = argparse.ArgumentParser(description="Fully rebuild and clean battles_clean.csv into a new authoritative snapshot.")
    parser.add_argument("--csv", default="outputs_final_2026-04-05/battles_clean.csv")
    parser.add_argument("--candidate-csv", default="outputs_final_2026-04-05/candidate_battle_pages.csv")
    parser.add_argument("--output-dir", default="outputs_cleaned_2026-04-07")
    parser.add_argument("--cache-dir", default=".cache/wiki_api_cleaned")
    parser.add_argument("--request-timeout", type=int, default=60)
    parser.add_argument("--request-sleep", type=float, default=0.0)
    parser.add_argument("--batch-size", type=int, default=50)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--resume", action="store_true")
    return parser.parse_args()


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_cleanup_rules(path: Path) -> None:
    content = """# Battle File Cleanup Rules

- The current frozen snapshot is preserved unchanged.
- Every original row is rebuilt from Wikipedia source evidence, preferring cached API data and using live API only when needed.
- Rows are kept in the main file only if they rebuild into an accepted `battle_article`, `war_conflict_article`, `campaign_article`, or `operation_article` with:
  - a valid date field set
  - a valid or conservative result field
  - enough event-specific source evidence to avoid weak-source classification
- Rows are removed completely if rebuild/classification indicates they are non-conflict pages, generic military concepts, biographies, organizations, missions, units, doctrines, manuals, or other false positives.
- Rows that still look like genuine conflict entries but cannot be validated confidently are moved to quarantine instead of staying in the main file.
- All kept rows are rewritten from the rebuilt source row rather than patched field by field.
- Result text is sanitized conservatively; malformed commentary-heavy result strings are reduced to a clean normalized label or `unknown`.
- Notes are standardized to `validated_rebuild_mode=<mode>` so the cleaned snapshot reflects actual rebuild provenance.
"""
    path.write_text(content, encoding="utf-8")


def count_existing_rows(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        next(reader, None)
        return sum(1 for _ in reader)


def dedupe_existing_csv(path: Path, key_field: str, fieldnames: list[str] | None = None) -> None:
    if not path.exists() or path.stat().st_size == 0:
        return
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            return
        rows = list(reader)
        columns = fieldnames or reader.fieldnames
    deduped: dict[str, dict[str, str]] = {}
    ordered_keys: list[str] = []
    for row in rows:
        key = row.get(key_field, "")
        if not key:
            continue
        if key not in deduped:
            ordered_keys.append(key)
        deduped[key] = row
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for key in ordered_keys:
            writer.writerow(deduped[key])


def read_processed_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return {row.get("original_battle_id", "") for row in csv.DictReader(handle) if row.get("original_battle_id")}


def main() -> None:
    args = parse_args()
    csv_path = Path(args.csv)
    candidate_csv_path = Path(args.candidate_csv)
    output_dir = Path(args.output_dir)
    temp_dir = output_dir / "_tmp"
    output_dir.mkdir(parents=True, exist_ok=True)
    temp_dir.mkdir(parents=True, exist_ok=True)
    cache_dir = Path(args.cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)

    battles_rows = load_rows(csv_path)
    if args.limit:
        battles_rows = battles_rows[: args.limit]
    candidate_rows = load_rows(candidate_csv_path)
    origin_map = build_origin_map(candidate_rows)

    config = bdp.PipelineConfig(
        output_dir=output_dir,
        cache_dir=cache_dir,
        save_json=False,
        max_root_links=None,
        max_list_pages=None,
        max_battle_pages=None,
        request_timeout=args.request_timeout,
        request_sleep=args.request_sleep,
        reuse_cache=True,
    )
    client = bdp.WikipediaClient(config)

    main_path = output_dir / "battles_clean.csv"
    quarantine_path = output_dir / "battles_clean_quarantine.csv"
    removed_path = output_dir / "battles_clean_removed_false_positives.csv"
    actions_path = output_dir / "cleanup_actions.csv"
    summary_path = output_dir / "cleanup_summary.json"

    counts = {
        "original_rows": len(battles_rows),
        "kept": 0,
        "repaired": 0,
        "quarantined": 0,
        "removed_false_positive": 0,
    }

    processed_ids = read_processed_ids(actions_path) if args.resume else set()
    if args.resume:
        dedupe_existing_csv(main_path, "battle_id", MAIN_FIELDNAMES)
        dedupe_existing_csv(quarantine_path, "battle_id", QUARANTINE_FIELDNAMES)
        dedupe_existing_csv(removed_path, "battle_id", REMOVED_FIELDNAMES)
        dedupe_existing_csv(actions_path, "original_battle_id", ACTIONS_FIELDNAMES)
        processed_ids = read_processed_ids(actions_path)
        if summary_path.exists():
            counts.update(json.loads(summary_path.read_text(encoding="utf-8")))
            counts["original_rows"] = len(battles_rows)
        else:
            counts["kept"] = 0
            counts["repaired"] = 0
            counts["quarantined"] = count_existing_rows(quarantine_path)
            counts["removed_false_positive"] = count_existing_rows(removed_path)
            for row in load_rows(actions_path):
                decision = row.get("decision", "")
                if decision == "kept":
                    counts["kept"] += 1
                elif decision == "repaired":
                    counts["repaired"] += 1

    main_mode = "a" if args.resume and main_path.exists() else "w"
    quarantine_mode = "a" if args.resume and quarantine_path.exists() else "w"
    removed_mode = "a" if args.resume and removed_path.exists() else "w"
    actions_mode = "a" if args.resume and actions_path.exists() else "w"

    write_cleanup_rules(output_dir / "CLEANUP_RULES.md")

    with (
        main_path.open(main_mode, encoding="utf-8-sig", newline="") as main_handle,
        quarantine_path.open(quarantine_mode, encoding="utf-8-sig", newline="") as quarantine_handle,
        removed_path.open(removed_mode, encoding="utf-8-sig", newline="") as removed_handle,
        actions_path.open(actions_mode, encoding="utf-8-sig", newline="") as actions_handle,
    ):
        main_writer = csv.DictWriter(main_handle, fieldnames=MAIN_FIELDNAMES)
        quarantine_writer = csv.DictWriter(quarantine_handle, fieldnames=QUARANTINE_FIELDNAMES)
        removed_writer = csv.DictWriter(removed_handle, fieldnames=REMOVED_FIELDNAMES)
        actions_writer = csv.DictWriter(actions_handle, fieldnames=ACTIONS_FIELDNAMES)

        if main_mode == "w":
            main_writer.writeheader()
        if quarantine_mode == "w":
            quarantine_writer.writeheader()
        if removed_mode == "w":
            removed_writer.writeheader()
        if actions_mode == "w":
            actions_writer.writeheader()

        pending_rows = [row for row in battles_rows if row["battle_id"] not in processed_ids]

        for batch_start in range(0, len(pending_rows), args.batch_size):
            batch = pending_rows[batch_start : batch_start + args.batch_size]
            titles = [row["wikipedia_title"] for row in batch]
            wikitext_pages = fetch_page_wikitext_batch(client, titles)

            for offset, original_row in enumerate(batch, start=batch_start + 1):
                title = original_row["wikipedia_title"]
                origin_rows = origin_map.get(title, [])
                wikitext_page = wikitext_pages.get(
                    title,
                    {
                        "title": title,
                        "pageid": None,
                        "fullurl": original_row.get("source_url", ""),
                        "categories": [],
                        "coordinates": [],
                        "pageprops": {},
                        "wikitext": "",
                    },
                )

                wikitext_candidate = build_wikitext_candidate(
                    client=client,
                    page=wikitext_page,
                    origin_rows=origin_rows,
                    config=config,
                    json_dir=temp_dir,
                )

                need_full_parse = True
                if wikitext_candidate.get("clean_row"):
                    sanitized = sanitize_candidate_row(wikitext_candidate["clean_row"], "wikitext")
                    blockers = main_row_blockers(title, sanitized, wikitext_page.get("categories", []))
                    need_full_parse = not wikitext_candidate.get("classification", {}).get("accepted", False)
                    if not blockers:
                        need_full_parse = False

                full_candidate = None
                if need_full_parse:
                    full_candidate = build_full_parse_candidate(
                        client=client,
                        title=title,
                        origin_rows=origin_rows,
                        config=config,
                        json_dir=temp_dir,
                    )

                decision = decide_rebuild_result(title, wikitext_candidate, full_candidate)
                decision_name = decision["decision"]
                reason_code = "|".join(decision["reason_codes"])
                rebuild_mode = decision["rebuild_mode"]

                if decision_name == "valid":
                    final_row = decision["row"]
                    if rows_differ(original_row, final_row):
                        counts["repaired"] += 1
                        final_decision = "repaired"
                    else:
                        counts["kept"] += 1
                        final_decision = "kept"
                    main_writer.writerow(final_row)
                    actions_writer.writerow(
                        {
                            "row_number": offset,
                            "original_battle_id": original_row.get("battle_id", ""),
                            "original_title": title,
                            "decision": final_decision,
                            "reason_code": reason_code,
                            "rebuild_mode": rebuild_mode,
                            "main_file_included": "true",
                            "quarantine_included": "false",
                            "removed_included": "false",
                        }
                    )
                    continue

                if decision_name == "quarantine":
                    counts["quarantined"] += 1
                    quarantine_source = decision["row"] or original_row
                    quarantine_row = {field: quarantine_source.get(field, "") for field in MAIN_FIELDNAMES}
                    quarantine_row["quarantine_reason"] = reason_code or "unvalidated_conflict_row"
                    quarantine_row["validation_status"] = "quarantined"
                    quarantine_writer.writerow(quarantine_row)
                    actions_writer.writerow(
                        {
                            "row_number": offset,
                            "original_battle_id": original_row.get("battle_id", ""),
                            "original_title": title,
                            "decision": "quarantined",
                            "reason_code": reason_code,
                            "rebuild_mode": rebuild_mode,
                            "main_file_included": "false",
                            "quarantine_included": "true",
                            "removed_included": "false",
                        }
                    )
                    continue

                counts["removed_false_positive"] += 1
                removed_row = {field: original_row.get(field, "") for field in MAIN_FIELDNAMES}
                removed_row["removal_reason"] = reason_code or "removed_false_positive"
                removed_row["validation_status"] = "removed_false_positive"
                removed_writer.writerow(removed_row)
                actions_writer.writerow(
                    {
                        "row_number": offset,
                        "original_battle_id": original_row.get("battle_id", ""),
                        "original_title": title,
                        "decision": "removed_false_positive",
                        "reason_code": reason_code,
                        "rebuild_mode": rebuild_mode,
                        "main_file_included": "false",
                        "quarantine_included": "false",
                        "removed_included": "true",
                    }
                )

            main_handle.flush()
            quarantine_handle.flush()
            removed_handle.flush()
            actions_handle.flush()

    summary = {
        **counts,
        "final_main_rows": count_existing_rows(main_path),
        "final_quarantine_rows": count_existing_rows(quarantine_path),
        "final_removed_rows": count_existing_rows(removed_path),
    }
    summary["reconciliation_ok"] = (
        summary["final_main_rows"] + summary["final_quarantine_rows"] + summary["final_removed_rows"] == len(battles_rows)
    )
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
