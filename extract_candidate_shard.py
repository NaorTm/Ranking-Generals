from __future__ import annotations

import argparse
import csv
import json
import multiprocessing as mp
import time
from collections import defaultdict, deque
from pathlib import Path
from queue import Empty
from typing import Any

import pandas as pd
from tqdm import tqdm

from battle_dataset_pipeline import (
    PipelineConfig,
    build_battle_rows,
    build_commanders_master,
    build_quality_report,
    build_source_record,
    chunked,
    compute_run_metrics,
    extract_page_process_target,
    issue_record,
    merge_pipe_values,
    setup_logging,
    wikipedia_url_for_title,
)


def parse_bool(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def load_candidate_context(candidate_csv: Path) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]], dict[str, dict[str, Any]], list[str]]:
    with candidate_csv.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))

    candidate_origins: dict[str, list[dict[str, Any]]] = defaultdict(list)
    candidate_statuses: dict[str, dict[str, Any]] = {}
    candidate_priority: dict[str, tuple[int, int]] = {}

    for row in rows:
        title = row["candidate_title"]
        try:
            score = int(float(row.get("candidate_score", 0) or 0))
        except ValueError:
            score = 0
        previous_score, previous_count = candidate_priority.get(title, (0, 0))
        candidate_priority[title] = (max(previous_score, score), previous_count + 1)
        candidate_origins[title].append(row)
        if title not in candidate_statuses:
            candidate_statuses[title] = {
                "metadata_fetch_status": row.get("metadata_fetch_status", "not_classified"),
                "metadata_page_type": row.get("metadata_page_type", ""),
                "metadata_confidence": row.get("metadata_page_type_confidence", ""),
                "metadata_reason": row.get("metadata_acceptance_reason", ""),
                "metadata_accepted": parse_bool(row.get("metadata_accepted", False)),
                "full_fetch_status": row.get("full_fetch_status", "pending"),
                "final_page_type": row.get("final_page_type", ""),
                "final_reason": row.get("final_acceptance_reason", ""),
                "source_url": row.get("candidate_url", ""),
                "parent_source": row.get("parent_source", ""),
                "discovery_root": row.get("discovery_root", ""),
                "source_family": row.get("source_family", ""),
            }

    deduped_candidates = sorted(
        candidate_origins.keys(),
        key=lambda title: (
            -candidate_priority.get(title, (0, 0))[0],
            -candidate_priority.get(title, (0, 0))[1],
            title.lower(),
        ),
    )
    return rows, candidate_origins, candidate_statuses, deduped_candidates


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract one shard from candidate_battle_pages.csv.")
    parser.add_argument("--candidate-csv", required=True, help="Candidate CSV produced by battle_dataset_pipeline.py --stop-after-metadata")
    parser.add_argument("--output-dir", required=True, help="Shard output directory.")
    parser.add_argument("--cache-dir", default=".cache/wiki_api", help="Directory for cached MediaWiki responses.")
    parser.add_argument("--shard-index", type=int, required=True, help="Zero-based shard index.")
    parser.add_argument("--shard-count", type=int, required=True, help="Total shard count.")
    parser.add_argument("--request-timeout", type=int, default=30)
    parser.add_argument("--request-sleep", type=float, default=0.02)
    parser.add_argument("--full-fetch-workers", type=int, default=4)
    parser.add_argument("--full-fetch-batch-size", type=int, default=20)
    parser.add_argument("--page-task-timeout", type=int, default=60)
    parser.add_argument("--no-json", action="store_true")
    parser.add_argument("--no-cache", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.shard_index < 0 or args.shard_count <= 0 or args.shard_index >= args.shard_count:
        raise SystemExit("Invalid shard index/count.")

    output_dir = Path(args.output_dir).resolve()
    cache_dir = Path(args.cache_dir).resolve()
    candidate_csv = Path(args.candidate_csv).resolve()
    json_dir = output_dir / "page_json"
    output_dir.mkdir(parents=True, exist_ok=True)
    cache_dir.mkdir(parents=True, exist_ok=True)
    if not args.no_json:
        json_dir.mkdir(parents=True, exist_ok=True)

    setup_logging(output_dir)
    import logging

    logger = logging.getLogger("pipeline")
    config = PipelineConfig(
        output_dir=output_dir,
        cache_dir=cache_dir,
        save_json=not args.no_json,
        max_root_links=None,
        max_list_pages=None,
        max_battle_pages=None,
        request_timeout=args.request_timeout,
        request_sleep=args.request_sleep,
        reuse_cache=not args.no_cache,
        category_depth=1,
        full_fetch_workers=max(1, args.full_fetch_workers),
        full_fetch_batch_size=max(1, args.full_fetch_batch_size),
        page_task_timeout=max(30, args.page_task_timeout),
    )

    candidate_rows, candidate_origins, candidate_statuses, deduped_candidates = load_candidate_context(candidate_csv)
    full_fetch_titles = [title for title in deduped_candidates if candidate_statuses.get(title, {}).get("metadata_accepted")]
    shard_titles = [title for index, title in enumerate(full_fetch_titles) if index % args.shard_count == args.shard_index]
    logger.info("Shard %s/%s processing %s accepted pages", args.shard_index, args.shard_count, len(shard_titles))

    sources_index: list[dict[str, Any]] = []
    extraction_issues: list[dict[str, Any]] = []
    battles_raw_rows: list[dict[str, Any]] = []
    battles_clean_rows: list[dict[str, Any]] = []
    commander_rows: list[dict[str, Any]] = []
    seen_battle_ids: dict[str, int] = {}

    progress_bar = tqdm(total=len(shard_titles), desc=f"Shard {args.shard_index}")
    processed_titles = 0
    try:
        for batch_index, title_batch in enumerate(chunked(shard_titles, config.full_fetch_batch_size), start=1):
            logger.info(
                "Starting shard batch %s with %s pages (%s/%s processed so far)",
                batch_index,
                len(title_batch),
                processed_titles,
                len(shard_titles),
            )
            pending_titles = deque(title_batch)
            active_workers: dict[str, dict[str, Any]] = {}

            def finalize_result(title: str, result: dict[str, Any]) -> None:
                nonlocal processed_titles
                if result.get("error_kind"):
                    error_kind = result["error_kind"]
                    candidate_statuses[title]["full_fetch_status"] = error_kind
                    extraction_issues.append(
                        issue_record(title, wikipedia_url_for_title(title), error_kind, "page", "high", f"Failed to fetch candidate page: {result['error_message']}")
                    )
                    sources_index.append(
                        build_source_record(
                            title,
                            wikipedia_url_for_title(title),
                            candidate_statuses[title].get("metadata_page_type", "candidate_page"),
                            candidate_statuses[title].get("parent_source", ""),
                            error_kind,
                            result["error_message"],
                            discovery_root=candidate_statuses[title].get("discovery_root", ""),
                            source_family=candidate_statuses[title].get("source_family", ""),
                        )
                    )
                    progress_bar.update(1)
                    processed_titles += 1
                    return

                extraction_issues.extend(result.get("issues", []))
                page = result["page"]
                raw_row = result["raw_row"]
                clean_row = result["clean_row"]
                commander_entries = result["commander_entries"]
                page_classification = result["page_classification"]
                candidate_statuses[title]["full_fetch_status"] = "accepted" if clean_row else "rejected_after_full_fetch"
                candidate_statuses[title]["final_page_type"] = page_classification["page_type"]
                candidate_statuses[title]["final_reason"] = page_classification["reasons"]
                sources_index.append(
                    build_source_record(
                        page["title"],
                        page["fullurl"],
                        page_classification["page_type"],
                        candidate_statuses[title].get("parent_source", ""),
                        "ok" if clean_row else "excluded",
                        page_classification["reasons"],
                        discovery_root=candidate_statuses[title].get("discovery_root", ""),
                        source_family=candidate_statuses[title].get("source_family", ""),
                    )
                )
                if raw_row and clean_row:
                    battle_id = clean_row["battle_id"]
                    if battle_id in seen_battle_ids:
                        existing_index = seen_battle_ids[battle_id]
                        battles_raw_rows[existing_index]["list_page_origin"] = merge_pipe_values(
                            battles_raw_rows[existing_index]["list_page_origin"],
                            clean_row["list_page_origin"],
                        )
                        battles_clean_rows[existing_index]["list_page_origin"] = merge_pipe_values(
                            battles_clean_rows[existing_index]["list_page_origin"],
                            clean_row["list_page_origin"],
                        )
                    else:
                        seen_battle_ids[battle_id] = len(battles_raw_rows)
                        battles_raw_rows.append(raw_row)
                        battles_clean_rows.append(clean_row)
                        commander_rows.extend(commander_entries)
                progress_bar.update(1)
                processed_titles += 1

            while pending_titles or active_workers:
                while pending_titles and len(active_workers) < config.full_fetch_workers:
                    title = pending_titles.popleft()
                    result_queue: mp.Queue = mp.Queue()
                    process = mp.Process(
                        target=extract_page_process_target,
                        args=(
                            result_queue,
                            title,
                            candidate_origins[title],
                            config,
                            json_dir,
                            None,
                        ),
                    )
                    process.start()
                    active_workers[title] = {
                        "process": process,
                        "queue": result_queue,
                        "started_at": time.monotonic(),
                    }

                finished_titles: list[str] = []
                for title, worker_state in list(active_workers.items()):
                    process = worker_state["process"]
                    result_queue = worker_state["queue"]
                    try:
                        result = result_queue.get_nowait()
                    except Empty:
                        result = None

                    if result is not None:
                        process.join(timeout=1)
                        result_queue.close()
                        result_queue.join_thread()
                        finalize_result(title, result)
                        finished_titles.append(title)
                        continue

                    if not process.is_alive():
                        process.join(timeout=1)
                        result_queue.close()
                        result_queue.join_thread()
                        finalize_result(
                            title,
                            {
                                "title": title,
                                "error_kind": "worker_exit",
                                "error_message": "Page worker exited without returning a result.",
                            },
                        )
                        finished_titles.append(title)
                        continue

                    elapsed = time.monotonic() - worker_state["started_at"]
                    if elapsed > config.page_task_timeout:
                        process.terminate()
                        process.join(timeout=5)
                        result_queue.close()
                        result_queue.join_thread()
                        finalize_result(
                            title,
                            {
                                "title": title,
                                "error_kind": "task_timeout",
                                "error_message": f"Page extraction exceeded {config.page_task_timeout} seconds and was terminated.",
                            },
                        )
                        finished_titles.append(title)

                for title in finished_titles:
                    active_workers.pop(title, None)

                if not finished_titles:
                    time.sleep(0.2)

            logger.info(
                "Completed shard batch %s; processed %s/%s pages",
                batch_index,
                processed_titles,
                len(shard_titles),
            )
    finally:
        progress_bar.close()

    shard_candidate_rows = [row for row in candidate_rows if row["candidate_title"] in set(shard_titles)]
    pd.DataFrame(shard_candidate_rows).to_csv(output_dir / "candidate_battle_pages.csv", index=False, encoding="utf-8-sig")

    battles_raw_df = pd.DataFrame(battles_raw_rows)
    battles_clean_df = pd.DataFrame(battles_clean_rows)
    commander_df = pd.DataFrame(commander_rows)
    commander_master_df, commander_master_issues = build_commanders_master(commander_df, config.fuzzy_merge_threshold)
    extraction_issues.extend(commander_master_issues)
    issues_df = pd.DataFrame(extraction_issues).drop_duplicates() if extraction_issues else pd.DataFrame(
        columns=["timestamp_utc", "page_title", "source_url", "issue_type", "field_name", "severity", "message", "raw_value"]
    )
    sources_df = pd.DataFrame(sources_index).drop_duplicates()

    battles_raw_df.to_csv(output_dir / "battles_raw.csv", index=False, encoding="utf-8-sig")
    battles_clean_df.to_csv(output_dir / "battles_clean.csv", index=False, encoding="utf-8-sig")
    commander_df.to_csv(output_dir / "battle_commanders.csv", index=False, encoding="utf-8-sig")
    commander_master_df.to_csv(output_dir / "commanders_master.csv", index=False, encoding="utf-8-sig")
    issues_df.to_csv(output_dir / "extraction_issues.csv", index=False, encoding="utf-8-sig")
    sources_df.to_csv(output_dir / "sources_index.csv", index=False, encoding="utf-8-sig")

    coverage_context = {
        "root_pages": [f"candidate_csv:{candidate_csv.name}"],
        "list_pages": [],
        "category_discovery_used": True,
        "configured_bounds": {
            "shard_index": args.shard_index,
            "shard_count": args.shard_count,
        },
    }
    run_metrics = compute_run_metrics(
        battles_clean_df,
        commander_df,
        commander_master_df,
        issues_df,
        shard_candidate_rows,
        sources_index,
        coverage_context=coverage_context,
    )
    (output_dir / "run_metrics.json").write_text(json.dumps(run_metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    build_quality_report(
        battles_clean_df if not battles_clean_df.empty else pd.DataFrame(columns=["battle_id", "result_raw", "year", "battle_type"]),
        commander_df if not commander_df.empty else pd.DataFrame(columns=["battle_id", "commander_wikipedia_url"]),
        commander_master_df if not commander_master_df.empty else pd.DataFrame(columns=["commander_id"]),
        issues_df if not issues_df.empty else pd.DataFrame(columns=["severity", "page_title", "issue_type", "field_name", "message"]),
        shard_candidate_rows,
        sources_index,
        output_dir / "data_quality_report.md",
        previous_metrics=None,
        coverage_context=coverage_context,
    )
    logger.info("Shard extraction complete")
    logger.info("Accepted pages extracted: %s", len(battles_clean_df))
    logger.info("Commander rows extracted: %s", len(commander_df))


if __name__ == "__main__":
    main()
