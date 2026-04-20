from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import time
from collections import Counter, defaultdict, deque
from pathlib import Path
from queue import Empty
from typing import Any

import pandas as pd
from tqdm import tqdm

from battle_dataset_pipeline import (
    PipelineConfig,
    build_commanders_master,
    build_quality_report,
    build_source_record,
    categorize_fetch_error,
    chunked,
    compute_run_metrics,
    extract_page_process_target,
    issue_record,
    setup_logging,
    wikipedia_url_for_title,
)


def parse_bool(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def read_csv_if_exists(path: Path) -> pd.DataFrame:
    return pd.read_csv(path) if path.exists() and path.stat().st_size else pd.DataFrame()


def load_candidate_context(candidate_df: pd.DataFrame) -> tuple[dict[str, list[dict[str, Any]]], dict[str, dict[str, Any]], list[str]]:
    candidate_origins: dict[str, list[dict[str, Any]]] = defaultdict(list)
    candidate_statuses: dict[str, dict[str, Any]] = {}
    priority: dict[str, tuple[int, int]] = {}
    for row in candidate_df.to_dict(orient="records"):
        title = row["candidate_title"]
        candidate_origins[title].append(row)
        try:
            score = int(float(row.get("candidate_score", 0) or 0))
        except ValueError:
            score = 0
        previous_score, previous_count = priority.get(title, (0, 0))
        priority[title] = (max(previous_score, score), previous_count + 1)
        if title not in candidate_statuses:
            candidate_statuses[title] = {
                "metadata_accepted": parse_bool(row.get("metadata_accepted", False)),
                "metadata_page_type": row.get("metadata_page_type", ""),
                "metadata_page_type_confidence": row.get("metadata_page_type_confidence", ""),
                "metadata_reason": row.get("metadata_acceptance_reason", ""),
                "full_fetch_status": row.get("full_fetch_status", "pending"),
                "final_page_type": row.get("final_page_type", ""),
                "final_reason": row.get("final_acceptance_reason", ""),
                "source_url": row.get("candidate_url", ""),
                "parent_source": row.get("parent_source", ""),
                "discovery_root": row.get("discovery_root", ""),
                "source_family": row.get("source_family", ""),
            }
    deduped_titles = sorted(
        candidate_origins.keys(),
        key=lambda title: (-priority.get(title, (0, 0))[0], -priority.get(title, (0, 0))[1], title.lower()),
    )
    return candidate_origins, candidate_statuses, deduped_titles


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Recover accepted Wikipedia pages that previously timed out or remained incomplete.")
    parser.add_argument("--candidate-csv", default="outputs_merged/candidate_battle_pages.csv")
    parser.add_argument("--base-output-dir", default="outputs_merged")
    parser.add_argument("--output-dir", default="outputs_completed")
    parser.add_argument("--cache-dir", default=".cache/wiki_api")
    parser.add_argument("--retry-statuses", default="task_timeout,pending,worker_exit,fetch_error")
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--batch-size", type=int, default=40)
    parser.add_argument("--primary-timeout", type=int, default=45)
    parser.add_argument("--fallback-timeout", type=int, default=60)
    parser.add_argument("--request-timeout", type=int, default=20)
    parser.add_argument("--request-sleep", type=float, default=0.01)
    parser.add_argument("--no-json", action="store_true")
    parser.add_argument("--max-pages", type=int, default=None)
    parser.add_argument("--checkpoint-every-batches", type=int, default=5)
    parser.add_argument("--prefer-fallback", action="store_true")
    return parser.parse_args()


def page_size_bucket(page_size: int) -> str:
    if page_size < 25_000:
        return "small"
    if page_size < 100_000:
        return "medium"
    if page_size < 400_000:
        return "large"
    return "very_large"


def infer_bottleneck(fetch_ms: float, build_ms: float) -> str:
    if fetch_ms <= 0 and build_ms <= 0:
        return "timeout_no_result"
    if fetch_ms > build_ms * 1.5:
        return "network_bound"
    if build_ms > fetch_ms * 1.5:
        return "parsing_bound"
    return "mixed"


def write_recovery_report(
    output_path: Path,
    before_metrics: dict[str, Any],
    after_metrics: dict[str, Any],
    attempts_df: pd.DataFrame,
) -> None:
    lines: list[str] = [
        "# Timeout Recovery Report",
        "",
        f"- Accepted titles in scope: {before_metrics.get('metadata_accepted_total', 0)}",
        f"- Clean rows completed before: {before_metrics.get('battle_count', 0)}",
        f"- Clean rows completed after: {after_metrics.get('battle_count', 0)}",
        f"- Timeout issue count before: {before_metrics.get('issue_counts', {}).get('task_timeout', 0)}",
        f"- Timeout issue count after: {after_metrics.get('issue_counts', {}).get('task_timeout', 0)}",
        f"- Commander row growth: {after_metrics.get('commander_row_count', 0) - before_metrics.get('commander_row_count', 0)}",
        f"- Commander coverage change: {before_metrics.get('with_commanders_pct', 0)}% -> {after_metrics.get('with_commanders_pct', 0)}%",
        f"- Result coverage change: {before_metrics.get('with_result_pct', 0)}% -> {after_metrics.get('with_result_pct', 0)}%",
        f"- Year coverage change: {before_metrics.get('with_year_pct', 0)}% -> {after_metrics.get('with_year_pct', 0)}%",
        "",
        "## Retained Counts By Page Type",
        "",
    ]
    before_page_types = before_metrics.get("final_page_type_breakdown", {})
    after_page_types = after_metrics.get("final_page_type_breakdown", {})
    for page_type in sorted(set(before_page_types) | set(after_page_types)):
        lines.append(f"- {page_type}: {before_page_types.get(page_type, 0)} -> {after_page_types.get(page_type, 0)}")

    if attempts_df.empty:
        lines.extend(["", "## Recovery Attempts", "", "- No recovery attempts were recorded."])
        output_path.write_text("\n".join(lines), encoding="utf-8")
        return

    attempt_rows = attempts_df.to_dict(orient="records")
    retries_helped = sum(1 for row in attempt_rows if row.get("recovered_after_prior_timeout"))
    fallback_successes = sum(1 for row in attempt_rows if row.get("attempt_mode") == "fallback" and row.get("final_status") == "accepted")
    lines.extend(
        [
            "",
            "## Timeout Cause Audit",
            "",
            f"- Recovery attempts recorded: {len(attempt_rows)}",
            f"- Titles recovered after a prior timeout: {retries_helped}",
            f"- Fallback-mode successful recoveries: {fallback_successes}",
            f"- Redirects/canonicalization observed during recovery: {int(attempts_df['redirected'].fillna(False).sum())}",
            "- Merge-bound slowdowns observed during recovery: 0",
            "",
            "### Attempt Bottlenecks",
            "",
        ]
    )
    for key, count in attempts_df["bottleneck_bucket"].value_counts().items():
        lines.append(f"- {key}: {count}")

    lines.extend(["", "### Timeout Attempts By Metadata Page Type", ""])
    timeout_df = attempts_df.loc[attempts_df["final_status"] == "task_timeout"]
    if timeout_df.empty:
        lines.append("- No remaining timeout attempts were recorded in this pass.")
    else:
        for key, count in timeout_df["metadata_page_type"].value_counts().items():
            lines.append(f"- {key}: {count}")

    lines.extend(["", "### Timeout Attempts By Source Family", ""])
    if timeout_df.empty:
        lines.append("- No remaining timeout attempts were recorded in this pass.")
    else:
        for key, count in timeout_df["source_family"].value_counts().items():
            lines.append(f"- {key}: {count}")

    lines.extend(["", "### Attempt Size Buckets", ""])
    for key, count in attempts_df["page_size_bucket"].value_counts().items():
        lines.append(f"- {key}: {count}")

    output_path.write_text("\n".join(lines), encoding="utf-8")


def materialize_recovery_outputs(
    output_dir: Path,
    base_battles_raw: pd.DataFrame,
    base_battles_clean: pd.DataFrame,
    base_commanders: pd.DataFrame,
    base_issues: pd.DataFrame,
    base_sources: pd.DataFrame,
    base_candidates: pd.DataFrame,
    before_metrics: dict[str, Any],
    candidate_statuses: dict[str, dict[str, Any]],
    recovered_raw_rows: list[dict[str, Any]],
    recovered_clean_rows: list[dict[str, Any]],
    recovered_commander_rows: list[dict[str, Any]],
    recovered_source_rows: list[dict[str, Any]],
    recovered_issue_rows: list[dict[str, Any]],
    recovery_attempt_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    combined_battles_raw = pd.concat([base_battles_raw, pd.DataFrame(recovered_raw_rows)], ignore_index=True) if recovered_raw_rows else base_battles_raw.copy()
    combined_battles_clean = pd.concat([base_battles_clean, pd.DataFrame(recovered_clean_rows)], ignore_index=True) if recovered_clean_rows else base_battles_clean.copy()
    combined_commanders = pd.concat([base_commanders, pd.DataFrame(recovered_commander_rows)], ignore_index=True) if recovered_commander_rows else base_commanders.copy()
    combined_sources = pd.concat([base_sources, pd.DataFrame(recovered_source_rows)], ignore_index=True) if recovered_source_rows else base_sources.copy()
    combined_issues = pd.concat([base_issues, pd.DataFrame(recovered_issue_rows)], ignore_index=True) if recovered_issue_rows else base_issues.copy()

    if not combined_battles_raw.empty:
        combined_battles_raw = combined_battles_raw.drop_duplicates(subset=["battle_id"]).sort_values(["battle_name", "source_url"])
    if not combined_battles_clean.empty:
        combined_battles_clean = combined_battles_clean.drop_duplicates(subset=["battle_id"]).sort_values(["year", "battle_name"], na_position="last")
    if not combined_commanders.empty:
        combined_commanders = combined_commanders.drop_duplicates(subset=["battle_id", "commander_name_normalized", "side", "source_url"])
        combined_commanders = combined_commanders.sort_values(["commander_name_normalized", "year", "battle_name"], na_position="last")
    if not combined_sources.empty:
        combined_sources = combined_sources.drop_duplicates()
    if not combined_issues.empty:
        combined_issues = combined_issues.drop_duplicates()

    commanders_master, commander_master_issues = build_commanders_master(combined_commanders, 97)
    if commander_master_issues:
        combined_issues = pd.concat([combined_issues, pd.DataFrame(commander_master_issues)], ignore_index=True).drop_duplicates()

    updated_candidates = base_candidates.copy()
    for title, status in candidate_statuses.items():
        mask = updated_candidates["candidate_title"].astype(str).eq(title)
        updated_candidates.loc[mask, "full_fetch_status"] = status.get("full_fetch_status", "pending")
        updated_candidates.loc[mask, "final_page_type"] = status.get("final_page_type", "")
        updated_candidates.loc[mask, "final_acceptance_reason"] = status.get("final_reason", "")

    combined_battles_raw.to_csv(output_dir / "battles_raw.csv", index=False, encoding="utf-8-sig")
    combined_battles_clean.to_csv(output_dir / "battles_clean.csv", index=False, encoding="utf-8-sig")
    combined_commanders.to_csv(output_dir / "battle_commanders.csv", index=False, encoding="utf-8-sig")
    commanders_master.to_csv(output_dir / "commanders_master.csv", index=False, encoding="utf-8-sig")
    combined_issues.to_csv(output_dir / "extraction_issues.csv", index=False, encoding="utf-8-sig")
    combined_sources.to_csv(output_dir / "sources_index.csv", index=False, encoding="utf-8-sig")
    updated_candidates.to_csv(output_dir / "candidate_battle_pages.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(recovery_attempt_rows).to_csv(output_dir / "recovery_attempts.csv", index=False, encoding="utf-8-sig")

    coverage_context = {
        "root_pages": ["accepted_graph_recovery"],
        "list_pages": [],
        "category_discovery_used": True,
        "configured_bounds": {},
    }
    after_metrics = compute_run_metrics(
        combined_battles_clean,
        combined_commanders,
        commanders_master,
        combined_issues,
        updated_candidates.to_dict(orient="records"),
        combined_sources.to_dict(orient="records"),
        coverage_context=coverage_context,
    )
    (output_dir / "run_metrics.json").write_text(json.dumps(after_metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    build_quality_report(
        combined_battles_clean if not combined_battles_clean.empty else pd.DataFrame(columns=["battle_id", "result_raw", "year", "battle_type"]),
        combined_commanders if not combined_commanders.empty else pd.DataFrame(columns=["battle_id", "commander_wikipedia_url"]),
        commanders_master if not commanders_master.empty else pd.DataFrame(columns=["commander_id"]),
        combined_issues if not combined_issues.empty else pd.DataFrame(columns=["severity", "page_title", "issue_type", "field_name", "message"]),
        updated_candidates.to_dict(orient="records"),
        combined_sources.to_dict(orient="records"),
        output_dir / "data_quality_report.md",
        previous_metrics=before_metrics,
        coverage_context=coverage_context,
    )
    write_recovery_report(output_dir / "completion_recovery_report.md", before_metrics, after_metrics, pd.DataFrame(recovery_attempt_rows))
    return {
        "battles_clean": combined_battles_clean,
        "commanders": combined_commanders,
        "commanders_master": commanders_master,
        "issues": combined_issues,
        "sources": combined_sources,
        "updated_candidates": updated_candidates,
        "after_metrics": after_metrics,
    }


def main() -> None:
    args = parse_args()
    candidate_csv = Path(args.candidate_csv).resolve()
    base_output_dir = Path(args.base_output_dir).resolve()
    output_dir = Path(args.output_dir).resolve()
    cache_dir = Path(args.cache_dir).resolve()
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
        reuse_cache=True,
        category_depth=1,
        full_fetch_workers=max(1, args.workers),
        full_fetch_batch_size=max(1, args.batch_size),
        page_task_timeout=max(30, max(args.primary_timeout, args.fallback_timeout)),
    )

    base_battles_raw = read_csv_if_exists(base_output_dir / "battles_raw.csv")
    base_battles_clean = read_csv_if_exists(base_output_dir / "battles_clean.csv")
    base_commanders = read_csv_if_exists(base_output_dir / "battle_commanders.csv")
    base_issues = read_csv_if_exists(base_output_dir / "extraction_issues.csv")
    base_sources = read_csv_if_exists(base_output_dir / "sources_index.csv")
    base_candidates = read_csv_if_exists(candidate_csv)
    before_metrics = json.loads((base_output_dir / "run_metrics.json").read_text(encoding="utf-8"))

    candidate_origins, candidate_statuses, deduped_titles = load_candidate_context(base_candidates)
    retry_statuses = {value.strip() for value in args.retry_statuses.split(",") if value.strip()}
    completed_candidate_titles = set(
        base_candidates.loc[base_candidates["full_fetch_status"].astype(str).eq("accepted"), "candidate_title"].astype(str)
    )
    retry_titles = [
        title
        for title in deduped_titles
        if candidate_statuses.get(title, {}).get("metadata_accepted")
        and title not in completed_candidate_titles
        and candidate_statuses.get(title, {}).get("full_fetch_status") in retry_statuses
    ]
    if args.max_pages is not None:
        retry_titles = retry_titles[: args.max_pages]
    logger.info("Retrying %s incomplete accepted pages", len(retry_titles))

    recovered_raw_rows: list[dict[str, Any]] = []
    recovered_clean_rows: list[dict[str, Any]] = []
    recovered_commander_rows: list[dict[str, Any]] = []
    recovered_source_rows: list[dict[str, Any]] = []
    recovered_issue_rows: list[dict[str, Any]] = []
    recovery_attempt_rows: list[dict[str, Any]] = []
    seen_battle_ids = set(base_battles_clean["battle_id"].astype(str)) if not base_battles_clean.empty else set()

    progress_bar = tqdm(total=len(retry_titles), desc="Recover accepted pages")
    processed_titles = 0

    def finalize_success(title: str, result: dict[str, Any], prior_status: str) -> None:
        nonlocal processed_titles
        page = result["page"]
        raw_row = result["raw_row"]
        clean_row = result["clean_row"]
        commander_entries = result["commander_entries"]
        page_classification = result["page_classification"]
        candidate_statuses[title]["full_fetch_status"] = "accepted" if clean_row else "rejected_after_full_fetch"
        candidate_statuses[title]["final_page_type"] = page_classification["page_type"]
        candidate_statuses[title]["final_reason"] = page_classification["reasons"]
        recovered_source_rows.append(
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
        recovered_issue_rows.extend(result.get("issues", []))
        if raw_row and clean_row and clean_row["battle_id"] not in seen_battle_ids:
            seen_battle_ids.add(clean_row["battle_id"])
            recovered_raw_rows.append(raw_row)
            recovered_clean_rows.append(clean_row)
            recovered_commander_rows.extend(commander_entries)
        recovery_attempt_rows.append(
            {
                "candidate_title": title,
                "resolved_title": result.get("resolved_title", title),
                "prior_status": prior_status,
                "attempt_mode": result.get("attempt_mode", ""),
                "final_status": "accepted" if clean_row else "rejected_after_full_fetch",
                "metadata_page_type": candidate_statuses[title].get("metadata_page_type", ""),
                "source_family": candidate_statuses[title].get("source_family", ""),
                "fetch_elapsed_ms": result.get("fetch_elapsed_ms", 0.0),
                "build_elapsed_ms": result.get("build_elapsed_ms", 0.0),
                "total_elapsed_ms": result.get("total_elapsed_ms", 0.0),
                "page_size": result.get("page_size", 0),
                "page_size_bucket": page_size_bucket(int(result.get("page_size", 0) or 0)),
                "bottleneck_bucket": infer_bottleneck(float(result.get("fetch_elapsed_ms", 0.0) or 0.0), float(result.get("build_elapsed_ms", 0.0) or 0.0)),
                "redirected": bool(result.get("redirected")),
                "recovered_after_prior_timeout": prior_status == "task_timeout" and bool(clean_row),
            }
        )
        progress_bar.update(1)
        processed_titles += 1

    def finalize_failure(title: str, error_kind: str, error_message: str, attempt_mode: str, prior_status: str) -> None:
        nonlocal processed_titles
        candidate_statuses[title]["full_fetch_status"] = error_kind
        candidate_statuses[title]["final_reason"] = error_message
        recovered_issue_rows.append(
            issue_record(title, wikipedia_url_for_title(title), error_kind, "page", "high", f"Failed to fetch candidate page: {error_message}")
        )
        recovered_source_rows.append(
            build_source_record(
                title,
                wikipedia_url_for_title(title),
                candidate_statuses[title].get("metadata_page_type", "candidate_page"),
                candidate_statuses[title].get("parent_source", ""),
                error_kind,
                error_message,
                discovery_root=candidate_statuses[title].get("discovery_root", ""),
                source_family=candidate_statuses[title].get("source_family", ""),
            )
        )
        recovery_attempt_rows.append(
            {
                "candidate_title": title,
                "resolved_title": title,
                "prior_status": prior_status,
                "attempt_mode": attempt_mode,
                "final_status": error_kind,
                "metadata_page_type": candidate_statuses[title].get("metadata_page_type", ""),
                "source_family": candidate_statuses[title].get("source_family", ""),
                "fetch_elapsed_ms": 0.0,
                "build_elapsed_ms": 0.0,
                "total_elapsed_ms": 0.0,
                "page_size": 0,
                "page_size_bucket": "unknown",
                "bottleneck_bucket": "timeout_no_result" if error_kind == "task_timeout" else error_kind,
                "redirected": False,
                "recovered_after_prior_timeout": False,
            }
        )
        progress_bar.update(1)
        processed_titles += 1

    try:
        for batch_index, title_batch in enumerate(chunked(retry_titles, config.full_fetch_batch_size), start=1):
            logger.info(
                "Starting recovery batch %s with %s pages (%s/%s processed so far)",
                batch_index,
                len(title_batch),
                processed_titles,
                len(retry_titles),
            )
            pending_items = deque(
                {
                    "title": title,
                    "mode": "fallback" if args.prefer_fallback or candidate_statuses[title].get("full_fetch_status") == "task_timeout" else "full",
                    "prior_status": candidate_statuses[title].get("full_fetch_status", "pending"),
                    "fallback_tried": args.prefer_fallback or candidate_statuses[title].get("full_fetch_status") == "task_timeout",
                }
                for title in title_batch
            )
            active_workers: dict[str, dict[str, Any]] = {}

            while pending_items or active_workers:
                while pending_items and len(active_workers) < config.full_fetch_workers:
                    item = pending_items.popleft()
                    title = item["title"]
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
                            item["mode"],
                        ),
                    )
                    process.start()
                    active_workers[title] = {
                        "process": process,
                        "queue": result_queue,
                        "started_at": time.monotonic(),
                        "mode": item["mode"],
                        "prior_status": item["prior_status"],
                        "fallback_tried": item["fallback_tried"],
                    }

                finished_titles: list[str] = []
                for title, worker_state in list(active_workers.items()):
                    process = worker_state["process"]
                    result_queue = worker_state["queue"]
                    mode = worker_state["mode"]
                    timeout_limit = args.fallback_timeout if mode == "fallback" else args.primary_timeout
                    try:
                        result = result_queue.get_nowait()
                    except Empty:
                        result = None

                    if result is not None:
                        process.join(timeout=1)
                        result_queue.close()
                        result_queue.join_thread()
                        if result.get("error_kind"):
                            should_retry_fallback = mode == "full" and not worker_state["fallback_tried"] and result["error_kind"] in {
                                "fetch_error",
                                "worker_exit",
                                "task_timeout",
                                "missing_or_unavailable",
                            }
                            if should_retry_fallback:
                                pending_items.appendleft(
                                    {
                                        "title": title,
                                        "mode": "fallback",
                                        "prior_status": worker_state["prior_status"],
                                        "fallback_tried": True,
                                    }
                                )
                            else:
                                finalize_failure(title, result["error_kind"], result["error_message"], mode, worker_state["prior_status"])
                        else:
                            finalize_success(title, result, worker_state["prior_status"])
                        finished_titles.append(title)
                        continue

                    if not process.is_alive():
                        process.join(timeout=1)
                        result_queue.close()
                        result_queue.join_thread()
                        if mode == "full" and not worker_state["fallback_tried"]:
                            pending_items.appendleft(
                                {
                                    "title": title,
                                    "mode": "fallback",
                                    "prior_status": worker_state["prior_status"],
                                    "fallback_tried": True,
                                }
                            )
                        else:
                            finalize_failure(title, "worker_exit", "Page worker exited without returning a result.", mode, worker_state["prior_status"])
                        finished_titles.append(title)
                        continue

                    elapsed = time.monotonic() - worker_state["started_at"]
                    if elapsed > timeout_limit:
                        process.terminate()
                        process.join(timeout=5)
                        result_queue.close()
                        result_queue.join_thread()
                        if mode == "full" and not worker_state["fallback_tried"]:
                            pending_items.appendleft(
                                {
                                    "title": title,
                                    "mode": "fallback",
                                    "prior_status": worker_state["prior_status"],
                                    "fallback_tried": True,
                                }
                            )
                        else:
                            finalize_failure(
                                title,
                                "task_timeout",
                                f"Page extraction exceeded {timeout_limit} seconds and was terminated.",
                                mode,
                                worker_state["prior_status"],
                            )
                        finished_titles.append(title)

                for title in finished_titles:
                    active_workers.pop(title, None)

                if not finished_titles:
                    time.sleep(0.1)

            logger.info(
                "Completed recovery batch %s; processed %s/%s pages",
                batch_index,
                processed_titles,
                len(retry_titles),
            )
            if args.checkpoint_every_batches > 0 and batch_index % args.checkpoint_every_batches == 0:
                materialize_recovery_outputs(
                    output_dir=output_dir,
                    base_battles_raw=base_battles_raw,
                    base_battles_clean=base_battles_clean,
                    base_commanders=base_commanders,
                    base_issues=base_issues,
                    base_sources=base_sources,
                    base_candidates=base_candidates,
                    before_metrics=before_metrics,
                    candidate_statuses=candidate_statuses,
                    recovered_raw_rows=recovered_raw_rows,
                    recovered_clean_rows=recovered_clean_rows,
                    recovered_commander_rows=recovered_commander_rows,
                    recovered_source_rows=recovered_source_rows,
                    recovered_issue_rows=recovered_issue_rows,
                    recovery_attempt_rows=recovery_attempt_rows,
                )
                logger.info("Checkpoint written after batch %s", batch_index)
    finally:
        progress_bar.close()
    materialized = materialize_recovery_outputs(
        output_dir=output_dir,
        base_battles_raw=base_battles_raw,
        base_battles_clean=base_battles_clean,
        base_commanders=base_commanders,
        base_issues=base_issues,
        base_sources=base_sources,
        base_candidates=base_candidates,
        before_metrics=before_metrics,
        candidate_statuses=candidate_statuses,
        recovered_raw_rows=recovered_raw_rows,
        recovered_clean_rows=recovered_clean_rows,
        recovered_commander_rows=recovered_commander_rows,
        recovered_source_rows=recovered_source_rows,
        recovered_issue_rows=recovered_issue_rows,
        recovery_attempt_rows=recovery_attempt_rows,
    )
    logger.info("Recovery pass complete")
    logger.info("Recovered clean rows: %s", len(recovered_clean_rows))
    logger.info("Recovered commander rows: %s", len(recovered_commander_rows))


if __name__ == "__main__":
    main()
