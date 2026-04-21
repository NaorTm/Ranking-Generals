from __future__ import annotations

import argparse
import csv
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
    clean_commander_name,
    cleanup_rules_text,
    conservative_name_match,
    copy_battle_snapshot_files,
    dedupe_commander_rows,
    extract_commander_candidates,
    fetch_link_metadata_for_titles,
    load_rows,
    normalize_text,
    recover_linked_commander_candidates,
    side_cell_for_key,
    summarize_reasons,
    write_csv,
)

RECOVERY_AUDIT_FIELDNAMES = BATTLE_COMMANDER_FIELDNAMES + ["recovery_source", "recovery_side_raw_text"]
REBUILD_ACTION_FIELDNAMES = ["battle_id", "wikipedia_title", "status"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Rebuild battle commanders from the validated battle snapshot.")
    parser.add_argument("--battle-snapshot-dir", default="outputs_cleaned_2026-04-07_authoritative")
    parser.add_argument("--output-dir", default="outputs_cleaned_2026-04-09_authoritative")
    parser.add_argument("--cache-dir", default=".cache/wiki_api_commanders")
    parser.add_argument("--batch-size", type=int, default=25)
    parser.add_argument("--request-timeout", type=int, default=60)
    parser.add_argument("--request-sleep", type=float, default=0.0)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--recovery-only", action="store_true")
    return parser.parse_args()


def append_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    if not rows:
        return
    file_exists = path.exists()
    with path.open("a", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        if not file_exists or path.stat().st_size == 0:
            writer.writeheader()
        for row in rows:
            writer.writerow(row)


def dedupe_rows(rows: list[dict[str, str]], key_fn) -> list[dict[str, str]]:
    deduped: list[dict[str, str]] = []
    seen: set[str] = set()
    for row in rows:
        key = key_fn(row)
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(row)
    return deduped


def read_processed_battle_ids(path: Path) -> set[str]:
    if not path.exists() or path.stat().st_size == 0:
        return set()
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return {row.get("battle_id", "") for row in csv.DictReader(handle) if row.get("battle_id")}


def main() -> None:
    args = parse_args()
    input_dir = Path(args.battle_snapshot_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    if input_dir.resolve() != output_dir.resolve():
        copy_battle_snapshot_files(input_dir, output_dir)

    battles_path = input_dir / "battles_clean.csv"
    battles_rows = load_rows(battles_path)
    if args.limit:
        battles_rows = battles_rows[: args.limit]

    commanders_path = output_dir / "battle_commanders.csv"
    quarantine_path = output_dir / "battle_commanders_quarantine.csv"
    side_issues_path = output_dir / "battle_commander_side_issues.csv"
    recovery_audit_path = output_dir / "commander_recovery_audit.csv"
    actions_path = output_dir / "commander_rebuild_actions.csv"

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

    rejection_counter: Counter[str] = Counter()
    existing_commanders_seed = load_rows(commanders_path) if args.recovery_only and commanders_path.exists() else []
    existing_quarantine_seed = load_rows(quarantine_path) if args.recovery_only and quarantine_path.exists() else []
    existing_side_issues_seed = load_rows(side_issues_path) if args.recovery_only and side_issues_path.exists() else []
    existing_recovery_audit_seed = load_rows(recovery_audit_path) if args.recovery_only and recovery_audit_path.exists() else []
    existing_candidates_by_battle: dict[str, dict[str, list[dict[str, str]]]] = {}
    if args.recovery_only:
        for row in existing_commanders_seed:
            battle_id = normalize_text(row.get("battle_id"))
            side = normalize_text(row.get("side"))
            if not battle_id or not side:
                continue
            existing_candidates_by_battle.setdefault(battle_id, {}).setdefault(side, []).append(
                {
                    "raw_name": normalize_text(row.get("commander_name_raw")),
                    "normalized_name": normalize_text(row.get("commander_name_normalized")),
                    "wikipedia_url": normalize_text(row.get("commander_wikipedia_url")),
                    "identity_confidence": normalize_text(row.get("identity_confidence")) or "medium",
                    "identity_resolution_method": "seed_existing_row",
                    "candidate_source": "seed_existing_row",
                }
            )
    if args.resume:
        if commanders_path.exists():
            write_csv(
                commanders_path,
                BATTLE_COMMANDER_FIELDNAMES,
                dedupe_commander_rows(load_rows(commanders_path)),
            )
        if quarantine_path.exists():
            write_csv(
                quarantine_path,
                COMMANDER_QUARANTINE_FIELDNAMES,
                dedupe_commander_rows(load_rows(quarantine_path)),
            )
        if side_issues_path.exists():
            write_csv(
                side_issues_path,
                SIDE_ISSUE_FIELDNAMES,
                dedupe_rows(
                    load_rows(side_issues_path),
                    lambda row: "||".join(
                        [
                            normalize_text(row.get("battle_id")),
                            normalize_text(row.get("side")),
                            normalize_text(row.get("issue_type")),
                            normalize_text(row.get("raw_text")),
                        ]
                    ),
                ),
            )
        if recovery_audit_path.exists():
            write_csv(
                recovery_audit_path,
                RECOVERY_AUDIT_FIELDNAMES,
                dedupe_rows(
                    load_rows(recovery_audit_path),
                    lambda row: "||".join(
                        [
                            normalize_text(row.get("battle_id")),
                            normalize_text(row.get("side")),
                            normalize_text(row.get("commander_name_normalized")).lower(),
                            normalize_text(row.get("commander_wikipedia_url")).lower(),
                        ]
                    ),
                ),
            )
        if actions_path.exists():
            write_csv(
                actions_path,
                REBUILD_ACTION_FIELDNAMES,
                dedupe_rows(load_rows(actions_path), lambda row: normalize_text(row.get("battle_id"))),
            )

    processed_battle_ids = read_processed_battle_ids(actions_path) if args.resume else set()
    recovery_target_ids: set[str] | None = None
    if args.recovery_only:
        existing_battle_ids_with_rows = {normalize_text(row.get("battle_id")) for row in existing_commanders_seed if normalize_text(row.get("battle_id"))}
        existing_battle_ids_with_unlinked = {
            normalize_text(row.get("battle_id"))
            for row in existing_commanders_seed
            if normalize_text(row.get("battle_id")) and not normalize_text(row.get("commander_wikipedia_url"))
        }
        existing_issue_battle_ids = {
            normalize_text(row.get("battle_id"))
            for row in existing_side_issues_seed
            if normalize_text(row.get("battle_id"))
        }
        missing_commander_battle_ids = {
            normalize_text(row.get("battle_id"))
            for row in battles_rows
            if normalize_text(row.get("battle_id")) and normalize_text(row.get("battle_id")) not in existing_battle_ids_with_rows
        }
        recovery_target_ids = existing_battle_ids_with_unlinked | existing_issue_battle_ids | missing_commander_battle_ids
    pending_battles = [
        row
        for row in battles_rows
        if normalize_text(row.get("battle_id")) not in processed_battle_ids
        and (recovery_target_ids is None or normalize_text(row.get("battle_id")) in recovery_target_ids)
    ]

    for batch_start in range(0, len(pending_battles), args.batch_size):
        batch = pending_battles[batch_start : batch_start + args.batch_size]
        titles = [row["wikipedia_title"] for row in batch]
        pages = fetch_page_wikitext_batch(client, titles)
        all_link_titles: list[str] = []
        parsed_commander_fields: dict[str, list[dict[str, object]]] = {}
        page_wikitext_by_title: dict[str, str] = {}

        for row in batch:
            title = row["wikipedia_title"]
            page = pages.get(title, {"wikitext": ""})
            page_wikitext_by_title[title] = page.get("wikitext", "") or ""
            infobox = bdp.parse_infobox_wikitext(page.get("wikitext", "") or "")
            commander_fields = infobox.get("fields", {}).get("commanders", []) or []
            parsed_commander_fields[title] = commander_fields
            page_links = bdp.extract_wikilinks_from_wikitext(page.get("wikitext", "") or "")
            for side_cell in commander_fields:
                if not args.recovery_only:
                    for link in side_cell.get("links", []):
                        if normalize_text(link.get("title")):
                            all_link_titles.append(normalize_text(link["title"]))
                raw_segments = side_cell.get("segments") or bdp.split_raw_commander_text(side_cell.get("raw_text", ""))
                for segment in raw_segments:
                    cleaned_segment = clean_commander_name(segment)
                    if not cleaned_segment:
                        continue
                    for link in page_links:
                        title_candidate = normalize_text(link.get("title", ""))
                        label_candidate = normalize_text(link.get("text") or title_candidate)
                        if not title_candidate:
                            continue
                        if conservative_name_match(cleaned_segment, clean_commander_name(label_candidate)) or conservative_name_match(
                            cleaned_segment, clean_commander_name(title_candidate)
                        ):
                            all_link_titles.append(title_candidate)

        link_meta = fetch_link_metadata_for_titles(client, all_link_titles, chunk_size=50)
        batch_commanders_rows: list[dict[str, str]] = []
        batch_quarantine_rows: list[dict[str, str]] = []
        batch_side_issue_rows: list[dict[str, str]] = []
        batch_recovery_audit_rows: list[dict[str, str]] = []
        batch_actions: list[dict[str, str]] = []

        for battle_row in batch:
            title = battle_row["wikipedia_title"]
            commander_fields = parsed_commander_fields.get(title, [])
            accepted_by_side: dict[str, list[dict[str, str]]] = (
                {
                    side_key: list(side_candidates)
                    for side_key, side_candidates in existing_candidates_by_battle.get(
                        normalize_text(battle_row.get("battle_id")), {}
                    ).items()
                }
                if args.recovery_only
                else {}
            )
            rejected_by_side: dict[str, list[dict[str, str]]] = {}

            if not args.recovery_only:
                for side_key in ("side_a", "side_b", "side_c"):
                    side_cell = side_cell_for_key(commander_fields, side_key, battle_row)
                    if not side_cell:
                        continue
                    accepted, rejected, issues = extract_commander_candidates(side_cell, side_key, battle_row, link_meta)
                    if accepted:
                        accepted_by_side[side_key] = accepted
                    if rejected:
                        rejected_by_side[side_key] = rejected
                    batch_side_issue_rows.extend(issues)

            page_wikitext = page_wikitext_by_title.get(title, "")
            for side_key in ("side_a", "side_b", "side_c"):
                side_cell = side_cell_for_key(commander_fields, side_key, battle_row)
                recovered, recovery_rejected, recovery_issues = recover_linked_commander_candidates(
                    side_cell,
                    side_key,
                    battle_row,
                    page_wikitext,
                    link_meta,
                    accepted_by_side.get(side_key, []),
                )
                if recovered:
                    accepted_by_side.setdefault(side_key, []).extend(recovered)
                    for candidate in recovered:
                        audit_row = build_commander_row(battle_row, side_key, candidate, [])
                        audit_row["recovery_source"] = candidate["candidate_source"]
                        audit_row["recovery_side_raw_text"] = normalize_text(side_cell.get("raw_text", "")) if side_cell else ""
                        batch_recovery_audit_rows.append(audit_row)
                batch_side_issue_rows.extend(recovery_issues)

            if not args.recovery_only:
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
                        batch_quarantine_rows.append(quarantine_row)

                for side_key, accepted in accepted_by_side.items():
                    opposing_names: list[str] = []
                    for other_side, other_candidates in accepted_by_side.items():
                        if other_side != side_key:
                            opposing_names.extend(candidate["raw_name"] for candidate in other_candidates)
                    for candidate in accepted:
                        batch_commanders_rows.append(build_commander_row(battle_row, side_key, candidate, opposing_names))
            else:
                for side_key, accepted in accepted_by_side.items():
                    seed_keys = {
                        f"{normalize_text(candidate.get('normalized_name')).lower()}|{normalize_text(candidate.get('wikipedia_url')).lower()}"
                        for candidate in existing_candidates_by_battle.get(normalize_text(battle_row.get("battle_id")), {}).get(side_key, [])
                    }
                    recovered_only = [
                        candidate
                        for candidate in accepted
                        if f"{normalize_text(candidate.get('normalized_name')).lower()}|{normalize_text(candidate.get('wikipedia_url')).lower()}"
                        not in seed_keys
                    ]
                    if not recovered_only:
                        continue
                    opposing_names: list[str] = []
                    for other_side, other_candidates in accepted_by_side.items():
                        if other_side != side_key:
                            opposing_names.extend(candidate["raw_name"] for candidate in other_candidates)
                    for candidate in recovered_only:
                        batch_commanders_rows.append(build_commander_row(battle_row, side_key, candidate, opposing_names))

            batch_actions.append(
                {
                    "battle_id": normalize_text(battle_row.get("battle_id")),
                    "wikipedia_title": normalize_text(battle_row.get("wikipedia_title")),
                    "status": "processed",
                }
            )

        append_csv(commanders_path, BATTLE_COMMANDER_FIELDNAMES, dedupe_commander_rows(batch_commanders_rows))
        append_csv(quarantine_path, COMMANDER_QUARANTINE_FIELDNAMES, dedupe_commander_rows(batch_quarantine_rows))
        append_csv(
            side_issues_path,
            SIDE_ISSUE_FIELDNAMES,
            dedupe_rows(
                batch_side_issue_rows,
                lambda row: "||".join(
                    [
                        normalize_text(row.get("battle_id")),
                        normalize_text(row.get("side")),
                        normalize_text(row.get("issue_type")),
                        normalize_text(row.get("raw_text")),
                    ]
                ),
            ),
        )
        append_csv(
            recovery_audit_path,
            RECOVERY_AUDIT_FIELDNAMES,
            dedupe_rows(
                batch_recovery_audit_rows,
                lambda row: "||".join(
                    [
                        normalize_text(row.get("battle_id")),
                        normalize_text(row.get("side")),
                        normalize_text(row.get("commander_name_normalized")).lower(),
                        normalize_text(row.get("commander_wikipedia_url")).lower(),
                    ]
                ),
            ),
        )
        append_csv(actions_path, REBUILD_ACTION_FIELDNAMES, batch_actions)

    commanders_rows = dedupe_commander_rows(load_rows(commanders_path)) if commanders_path.exists() else []
    quarantine_rows = dedupe_commander_rows(load_rows(quarantine_path)) if quarantine_path.exists() else []
    side_issue_rows = load_rows(side_issues_path) if side_issues_path.exists() else []
    recovery_audit_rows = load_rows(recovery_audit_path) if recovery_audit_path.exists() else []
    if args.recovery_only:
        commanders_rows = dedupe_commander_rows(existing_commanders_seed + commanders_rows)
        quarantine_rows = dedupe_commander_rows(existing_quarantine_seed + quarantine_rows)
        side_issue_rows = dedupe_rows(
            existing_side_issues_seed + side_issue_rows,
            lambda row: "||".join(
                [
                    normalize_text(row.get("battle_id")),
                    normalize_text(row.get("side")),
                    normalize_text(row.get("issue_type")),
                    normalize_text(row.get("raw_text")),
                ]
            ),
        )
        recovery_audit_rows = dedupe_rows(
            existing_recovery_audit_seed + recovery_audit_rows,
            lambda row: "||".join(
                [
                    normalize_text(row.get("battle_id")),
                    normalize_text(row.get("side")),
                    normalize_text(row.get("commander_name_normalized")).lower(),
                    normalize_text(row.get("commander_wikipedia_url")).lower(),
                ]
            ),
        )
    write_csv(commanders_path, BATTLE_COMMANDER_FIELDNAMES, commanders_rows)
    write_csv(quarantine_path, COMMANDER_QUARANTINE_FIELDNAMES, quarantine_rows)
    write_csv(
        side_issues_path,
        SIDE_ISSUE_FIELDNAMES,
        dedupe_rows(
            side_issue_rows,
            lambda row: "||".join(
                [
                    normalize_text(row.get("battle_id")),
                    normalize_text(row.get("side")),
                    normalize_text(row.get("issue_type")),
                    normalize_text(row.get("raw_text")),
                ]
            ),
        ),
    )
    write_csv(
        recovery_audit_path,
        RECOVERY_AUDIT_FIELDNAMES,
        dedupe_rows(
            recovery_audit_rows,
            lambda row: "||".join(
                [
                    normalize_text(row.get("battle_id")),
                    normalize_text(row.get("side")),
                    normalize_text(row.get("commander_name_normalized")).lower(),
                    normalize_text(row.get("commander_wikipedia_url")).lower(),
                ]
            ),
        ),
    )
    commanders_master_rows = build_commanders_master(commanders_rows)

    write_csv(output_dir / "commanders_master.csv", MASTER_FIELDNAMES, commanders_master_rows)
    (output_dir / "COMMANDER_CLEANUP_RULES.md").write_text(cleanup_rules_text(), encoding="utf-8")

    recovered_battle_ids = {normalize_text(row.get("battle_id")) for row in recovery_audit_rows if normalize_text(row.get("battle_id"))}
    summary = {
        "input_battles": len(battles_rows),
        "battles_with_any_commander_rows": len({row["battle_id"] for row in commanders_rows}),
        "battle_commander_rows": len(commanders_rows),
        "battle_commander_quarantine_rows": len(quarantine_rows),
        "battle_commander_side_issues": len(side_issue_rows),
        "commanders_master_rows": len(commanders_master_rows),
        "linked_commander_rows": sum(1 for row in commanders_rows if normalize_text(row.get("commander_wikipedia_url"))),
        "unlinked_commander_rows": sum(1 for row in commanders_rows if not normalize_text(row.get("commander_wikipedia_url"))),
        "recovered_linked_commander_rows": len(recovery_audit_rows),
        "pages_touched_by_recovery": len(recovered_battle_ids),
        "recovery_quarantine_rows": 0,
        "identity_confidence_counts": dict(Counter(normalize_text(row["identity_confidence"]) for row in commanders_rows)),
        "quarantine_reason_counts": summarize_reasons(quarantine_rows, "quarantine_reason"),
    }
    (output_dir / "commander_cleanup_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
