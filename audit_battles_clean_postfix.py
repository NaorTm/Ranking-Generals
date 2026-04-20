from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
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
    split_pipe_values,
)


AUDIT_FIELDNAMES = [
    "row_number",
    "wikipedia_title",
    "battle_id",
    "status",
    "blocker_count",
    "blockers",
    "rebuild_mode",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Post-fix audit for cleaned battles_clean.csv.")
    parser.add_argument("--csv", default="outputs_cleaned_2026-04-07/battles_clean.csv")
    parser.add_argument("--candidate-csv", default="outputs_final_2026-04-05/candidate_battle_pages.csv")
    parser.add_argument("--output-dir", default="outputs_cleaned_2026-04-07/postfix_audit")
    parser.add_argument("--cache-dir", default=".cache/wiki_api_cleaned")
    parser.add_argument("--request-timeout", type=int, default=60)
    parser.add_argument("--request-sleep", type=float, default=0.0)
    parser.add_argument("--batch-size", type=int, default=50)
    parser.add_argument("--limit", type=int, default=None)
    return parser.parse_args()


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main() -> None:
    args = parse_args()
    csv_path = Path(args.csv)
    candidate_csv_path = Path(args.candidate_csv)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    temp_dir = output_dir / "_tmp"
    temp_dir.mkdir(parents=True, exist_ok=True)

    cleaned_rows = load_rows(csv_path)
    if args.limit:
        cleaned_rows = cleaned_rows[: args.limit]
    candidate_rows = load_rows(candidate_csv_path)
    origin_map = build_origin_map(candidate_rows)

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
    client = bdp.WikipediaClient(config)

    audit_rows: list[dict[str, object]] = []
    blocker_counter: Counter[str] = Counter()

    for batch_start in range(0, len(cleaned_rows), args.batch_size):
        batch = cleaned_rows[batch_start : batch_start + args.batch_size]
        titles = [row["wikipedia_title"] for row in batch]
        wikitext_pages = fetch_page_wikitext_batch(client, titles)

        for offset, current_row in enumerate(batch, start=batch_start + 1):
            title = current_row["wikipedia_title"]
            origin_rows = origin_map.get(title, [])
            wikitext_page = wikitext_pages.get(
                title,
                {
                    "title": title,
                    "pageid": None,
                    "fullurl": current_row.get("source_url", ""),
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
            full_candidate = None
            if not wikitext_candidate.get("classification", {}).get("accepted", False):
                full_candidate = build_full_parse_candidate(
                    client=client,
                    title=title,
                    origin_rows=origin_rows,
                    config=config,
                    json_dir=temp_dir,
                )
            decision = decide_rebuild_result(title, wikitext_candidate, full_candidate)

            current_categories = split_pipe_values(current_row.get("categories", ""))
            decision_categories = decision.get("categories", [])
            blockers = main_row_blockers(title, current_row, current_categories or decision_categories)
            if decision["decision"] != "valid" and not blockers:
                # Treat classifier drift as diagnostic noise unless it maps to an
                # actual row-integrity blocker in the cleaned row itself.
                non_blocking_drift = {"list_page", "uncertain_military_page"}
                if not set(decision["reason_codes"]).issubset(non_blocking_drift):
                    blockers = decision["reason_codes"] or ["row_failed_revalidation"]
            for blocker in blockers:
                blocker_counter[blocker] += 1

            audit_rows.append(
                {
                    "row_number": offset,
                    "wikipedia_title": title,
                    "battle_id": current_row.get("battle_id", ""),
                    "status": "ok" if not blockers else "blocker",
                    "blocker_count": len(blockers),
                    "blockers": "|".join(blockers),
                    "rebuild_mode": decision.get("rebuild_mode", "none"),
                }
            )

    write_csv(output_dir / "row_audit.csv", AUDIT_FIELDNAMES, audit_rows)
    summary = {
        "rows_checked": len(audit_rows),
        "blocker_rows": sum(1 for row in audit_rows if row["status"] == "blocker"),
        "ok_rows": sum(1 for row in audit_rows if row["status"] == "ok"),
        "blocker_counts": dict(blocker_counter.most_common()),
    }
    (output_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
