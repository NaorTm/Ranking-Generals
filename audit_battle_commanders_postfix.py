from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import battle_dataset_pipeline as bdp
from commander_clean_common import (
    MASTER_AUDIT_FIELDNAMES,
    ROW_AUDIT_FIELDNAMES,
    dedupe_commander_rows,
    fetch_link_metadata_for_titles,
    load_rows,
    master_level_blockers,
    normalize_text,
    row_level_blockers,
    url_to_title,
    write_csv,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Post-fix audit for rebuilt commander datasets.")
    parser.add_argument("--snapshot-dir", default="outputs_cleaned_2026-04-09_authoritative")
    parser.add_argument("--cache-dir", default=".cache/wiki_api_commanders")
    parser.add_argument("--request-timeout", type=int, default=60)
    parser.add_argument("--request-sleep", type=float, default=0.0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    snapshot_dir = Path(args.snapshot_dir)
    audit_dir = snapshot_dir / "commander_postfix_audit"
    audit_dir.mkdir(parents=True, exist_ok=True)

    battles_rows = load_rows(snapshot_dir / "battles_clean.csv")
    battle_by_id = {row["battle_id"]: row for row in battles_rows}
    commander_rows = dedupe_commander_rows(load_rows(snapshot_dir / "battle_commanders.csv"))
    master_rows = load_rows(snapshot_dir / "commanders_master.csv")

    config = bdp.PipelineConfig(
        output_dir=snapshot_dir,
        cache_dir=Path(args.cache_dir),
        save_json=False,
        max_root_links=None,
        max_list_pages=None,
        max_battle_pages=None,
        request_timeout=args.request_timeout,
        request_sleep=args.request_sleep,
        reuse_cache=True,
    )
    config.cache_dir.mkdir(parents=True, exist_ok=True)
    client = bdp.WikipediaClient(config)

    linked_titles = [
        url_to_title(row.get("commander_wikipedia_url", ""))
        for row in commander_rows
        if normalize_text(row.get("commander_wikipedia_url"))
    ]
    linked_titles.extend(
        url_to_title(row.get("wikipedia_page", ""))
        for row in master_rows
        if normalize_text(row.get("wikipedia_page"))
    )
    link_meta = fetch_link_metadata_for_titles(client, linked_titles, chunk_size=50)

    row_audit_rows: list[dict[str, str | int]] = []
    row_blockers: Counter[str] = Counter()
    seen_keys: set[str] = set()
    for idx, row in enumerate(commander_rows, start=1):
        key = "||".join(
            [
                normalize_text(row.get("battle_id")),
                normalize_text(row.get("side")),
                normalize_text(row.get("commander_name_normalized")).lower(),
                normalize_text(row.get("commander_wikipedia_url")).lower(),
            ]
        )
        blockers = row_level_blockers(row, battle_by_id, link_meta)
        if key in seen_keys:
            blockers.append("duplicate_row")
        else:
            seen_keys.add(key)
        blockers = sorted(set(blockers))
        for blocker in blockers:
            row_blockers[blocker] += 1
        row_audit_rows.append(
            {
                "row_number": idx,
                "battle_id": normalize_text(row.get("battle_id")),
                "battle_name": normalize_text(row.get("battle_name")),
                "commander_name_normalized": normalize_text(row.get("commander_name_normalized")),
                "commander_wikipedia_url": normalize_text(row.get("commander_wikipedia_url")),
                "status": "ok" if not blockers else "blocker",
                "blocker_count": len(blockers),
                "blockers": "|".join(blockers),
            }
        )

    master_audit_rows: list[dict[str, str | int]] = []
    master_blockers: Counter[str] = Counter()
    seen_master_ids: set[str] = set()
    seen_master_keys: set[str] = set()
    for idx, row in enumerate(master_rows, start=1):
        blockers = master_level_blockers(row, link_meta)
        commander_id = normalize_text(row.get("commander_id"))
        if commander_id in seen_master_ids:
            blockers.append("duplicate_commander_id")
        else:
            seen_master_ids.add(commander_id)
        dupe_key = f"{normalize_text(row.get('name_primary')).lower()}|{normalize_text(row.get('wikipedia_page')).lower()}"
        if dupe_key in seen_master_keys:
            blockers.append("duplicate_master_identity")
        else:
            seen_master_keys.add(dupe_key)
        blockers = sorted(set(blockers))
        for blocker in blockers:
            master_blockers[blocker] += 1
        master_audit_rows.append(
            {
                "row_number": idx,
                "commander_id": commander_id,
                "name_primary": normalize_text(row.get("name_primary")),
                "wikipedia_page": normalize_text(row.get("wikipedia_page")),
                "status": "ok" if not blockers else "blocker",
                "blocker_count": len(blockers),
                "blockers": "|".join(blockers),
            }
        )

    write_csv(audit_dir / "row_audit.csv", ROW_AUDIT_FIELDNAMES, row_audit_rows)
    write_csv(audit_dir / "master_audit.csv", MASTER_AUDIT_FIELDNAMES, master_audit_rows)
    summary = {
        "rows_checked": len(row_audit_rows),
        "row_blocker_rows": sum(1 for row in row_audit_rows if row["status"] == "blocker"),
        "row_ok_rows": sum(1 for row in row_audit_rows if row["status"] == "ok"),
        "row_blocker_counts": dict(row_blockers.most_common()),
        "master_rows_checked": len(master_audit_rows),
        "master_blocker_rows": sum(1 for row in master_audit_rows if row["status"] == "blocker"),
        "master_ok_rows": sum(1 for row in master_audit_rows if row["status"] == "ok"),
        "master_blocker_counts": dict(master_blockers.most_common()),
    }
    (audit_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
