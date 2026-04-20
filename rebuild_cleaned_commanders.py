from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import battle_dataset_pipeline as bdp
from battles_clean_common import fetch_page_wikitext_batch
from commander_clean_common import (
    BATTLE_COMMANDER_FIELDNAMES,
    COMMANDER_QUARANTINE_FIELDNAMES,
    MASTER_FIELDNAMES,
    SIDE_ISSUE_FIELDNAMES,
    build_commander_row,
    build_commanders_master,
    cleanup_rules_text,
    copy_battle_snapshot_files,
    dedupe_commander_rows,
    extract_commander_candidates,
    fetch_link_metadata_for_titles,
    load_rows,
    normalize_text,
    side_cell_for_key,
    summarize_reasons,
    write_csv,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Rebuild battle commanders from the validated battle snapshot.")
    parser.add_argument("--battle-snapshot-dir", default="outputs_cleaned_2026-04-07_authoritative")
    parser.add_argument("--output-dir", default="outputs_cleaned_2026-04-09_authoritative")
    parser.add_argument("--cache-dir", default=".cache/wiki_api_commanders")
    parser.add_argument("--batch-size", type=int, default=25)
    parser.add_argument("--request-timeout", type=int, default=60)
    parser.add_argument("--request-sleep", type=float, default=0.0)
    parser.add_argument("--limit", type=int, default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_dir = Path(args.battle_snapshot_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    copy_battle_snapshot_files(input_dir, output_dir)

    battles_path = input_dir / "battles_clean.csv"
    battles_rows = load_rows(battles_path)
    if args.limit:
        battles_rows = battles_rows[: args.limit]

    config = bdp.PipelineConfig(
        output_dir=output_dir,
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

    commanders_rows: list[dict[str, str]] = []
    quarantine_rows: list[dict[str, str]] = []
    side_issue_rows: list[dict[str, str]] = []
    rejection_counter: Counter[str] = Counter()
    parsed_commander_fields: dict[str, list[dict[str, object]]] = {}
    all_link_titles: list[str] = []

    for batch_start in range(0, len(battles_rows), args.batch_size):
        batch = battles_rows[batch_start : batch_start + args.batch_size]
        titles = [row["wikipedia_title"] for row in batch]
        pages = fetch_page_wikitext_batch(client, titles)

        for row in batch:
            title = row["wikipedia_title"]
            page = pages.get(title, {"wikitext": ""})
            infobox = bdp.parse_infobox_wikitext(page.get("wikitext", "") or "")
            commander_fields = infobox.get("fields", {}).get("commanders", []) or []
            parsed_commander_fields[title] = commander_fields
            for side_cell in infobox.get("fields", {}).get("commanders", []):
                for link in side_cell.get("links", []):
                    if normalize_text(link.get("title")):
                        all_link_titles.append(normalize_text(link["title"]))

    link_meta = fetch_link_metadata_for_titles(client, all_link_titles, chunk_size=50)

    for battle_row in battles_rows:
        title = battle_row["wikipedia_title"]
        commander_fields = parsed_commander_fields.get(title, [])
        accepted_by_side: dict[str, list[dict[str, str]]] = {}
        rejected_by_side: dict[str, list[dict[str, str]]] = {}

        for side_key in ("side_a", "side_b", "side_c"):
            side_cell = side_cell_for_key(commander_fields, side_key, battle_row)
            if not side_cell:
                continue
            accepted, rejected, issues = extract_commander_candidates(side_cell, side_key, battle_row, link_meta)
            if accepted:
                accepted_by_side[side_key] = accepted
            if rejected:
                rejected_by_side[side_key] = rejected
            side_issue_rows.extend(issues)

        for side_key, rejected in rejected_by_side.items():
            for rejected_candidate in rejected:
                rejection_counter.update(rejected_candidate["reason"].split("|"))
                quarantine_row = build_commander_row(
                    battle_row,
                    side_key,
                    {
                        "raw_name": rejected_candidate["raw_name"],
                        "normalized_name": rejected_candidate["normalized_name"],
                        "wikipedia_url": rejected_candidate["wikipedia_url"],
                        "identity_confidence": "medium",
                        "identity_resolution_method": "quarantined_candidate",
                        "candidate_source": rejected_candidate["candidate_source"],
                    },
                    [],
                )
                quarantine_row["quarantine_reason"] = rejected_candidate["reason"]
                quarantine_row["candidate_source"] = rejected_candidate["candidate_source"]
                quarantine_row["validation_status"] = "quarantined"
                quarantine_rows.append(quarantine_row)

        for side_key, accepted in accepted_by_side.items():
            opposing_names: list[str] = []
            for other_side, other_candidates in accepted_by_side.items():
                if other_side != side_key:
                    opposing_names.extend(candidate["raw_name"] for candidate in other_candidates)
            for candidate in accepted:
                commanders_rows.append(build_commander_row(battle_row, side_key, candidate, opposing_names))

    commanders_rows = dedupe_commander_rows(commanders_rows)
    quarantine_rows = dedupe_commander_rows(quarantine_rows)
    commanders_master_rows = build_commanders_master(commanders_rows)

    write_csv(output_dir / "battle_commanders.csv", BATTLE_COMMANDER_FIELDNAMES, commanders_rows)
    write_csv(output_dir / "battle_commanders_quarantine.csv", COMMANDER_QUARANTINE_FIELDNAMES, quarantine_rows)
    write_csv(output_dir / "battle_commander_side_issues.csv", SIDE_ISSUE_FIELDNAMES, side_issue_rows)
    write_csv(output_dir / "commanders_master.csv", MASTER_FIELDNAMES, commanders_master_rows)
    (output_dir / "COMMANDER_CLEANUP_RULES.md").write_text(cleanup_rules_text(), encoding="utf-8")

    summary = {
        "input_battles": len(battles_rows),
        "battles_with_any_commander_rows": len({row["battle_id"] for row in commanders_rows}),
        "battle_commander_rows": len(commanders_rows),
        "battle_commander_quarantine_rows": len(quarantine_rows),
        "battle_commander_side_issues": len(side_issue_rows),
        "commanders_master_rows": len(commanders_master_rows),
        "linked_commander_rows": sum(1 for row in commanders_rows if normalize_text(row.get("commander_wikipedia_url"))),
        "unlinked_commander_rows": sum(1 for row in commanders_rows if not normalize_text(row.get("commander_wikipedia_url"))),
        "identity_confidence_counts": dict(Counter(normalize_text(row["identity_confidence"]) for row in commanders_rows)),
        "quarantine_reason_counts": summarize_reasons(quarantine_rows, "quarantine_reason"),
    }
    (output_dir / "commander_cleanup_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
