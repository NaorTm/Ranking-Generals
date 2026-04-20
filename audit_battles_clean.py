from __future__ import annotations

import argparse
import csv
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
from urllib.parse import quote, unquote, urlparse

import battle_dataset_pipeline as bdp


STABLE_COMPARE_FIELDS = [
    "battle_id",
    "battle_name",
    "battle_name_normalized",
    "wikipedia_title",
    "source_url",
    "date_raw",
    "start_date",
    "end_date",
    "year",
    "century",
    "war_name",
    "campaign_name",
    "location_raw",
    "location_normalized",
    "latitude",
    "longitude",
    "result_raw",
    "result_normalized",
    "result_type",
    "belligerent_1_raw",
    "belligerent_2_raw",
    "belligerent_3_raw",
    "commander_side_a_raw",
    "commander_side_b_raw",
    "commander_side_c_raw",
    "strength_side_a_raw",
    "strength_side_b_raw",
    "strength_side_c_raw",
    "casualties_side_a_raw",
    "casualties_side_b_raw",
    "casualties_side_c_raw",
    "strength_side_a_min",
    "strength_side_a_max",
    "strength_side_b_min",
    "strength_side_b_max",
    "casualties_side_a_min",
    "casualties_side_a_max",
    "casualties_side_b_min",
    "casualties_side_b_max",
    "page_type",
    "battle_type",
    "infobox_present",
    "notes",
]

DIAGNOSTIC_COMPARE_FIELDS = [
    "page_type_confidence",
    "classification_notes",
    "acceptance_reason",
    "text_length",
    "categories",
    "list_page_origin",
    "parent_list_page",
    "discovery_root",
    "source_family",
    "extraction_confidence",
]

BOOL_FIELDS = {"infobox_present"}
FLOAT_FIELDS = {
    "latitude",
    "longitude",
    "page_type_confidence",
    "extraction_confidence",
    "date_parse_confidence",
    "text_length",
    "year",
    "century",
    "strength_side_a_min",
    "strength_side_a_max",
    "strength_side_b_min",
    "strength_side_b_max",
    "casualties_side_a_min",
    "casualties_side_a_max",
    "casualties_side_b_min",
    "casualties_side_b_max",
}

RESULT_TYPES = {
    "victory",
    "decisive_victory",
    "pyrrhic_victory",
    "tactical_victory",
    "defeat",
    "draw",
    "stalemate",
    "indecisive",
    "disputed",
    "unknown",
}
PAGE_TYPES = {"battle_article", "war_conflict_article", "campaign_article", "operation_article"}

OUTPUT_FIELDNAMES = [
    "row_number",
    "wikipedia_title",
    "battle_id",
    "status",
    "issue_count",
    "internal_issue_count",
    "stable_mismatch_count",
    "diagnostic_mismatch_count",
    "issue_types",
    "stable_mismatch_fields",
    "diagnostic_mismatch_fields",
    "live_title",
    "live_pageid",
    "live_fetch_mode",
    "notes",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit every row in battles_clean.csv against live/cached Wikipedia data.")
    parser.add_argument("--csv", default="outputs_final_2026-04-05/battles_clean.csv")
    parser.add_argument("--candidate-csv", default="outputs_final_2026-04-05/candidate_battle_pages.csv")
    parser.add_argument("--output-dir", default="audits/battles_clean_full_audit")
    parser.add_argument("--cache-dir", default=".cache/wiki_api")
    parser.add_argument("--live-cache-dir", default=".cache/wiki_api_audit_live")
    parser.add_argument("--batch-size", type=int, default=25)
    parser.add_argument("--request-sleep", type=float, default=0.0)
    parser.add_argument("--request-timeout", type=float, default=60.0)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--resume", action="store_true")
    return parser.parse_args()


def normalize_text(value: Any) -> str:
    return bdp.normalize_space("" if value is None else str(value))


def canonical_wikipedia_url(url: str) -> str:
    if not url:
        return ""
    parsed = urlparse(url)
    path = unquote(parsed.path)
    if path.startswith("/wiki/"):
        title = path[len("/wiki/") :].replace("_", " ")
        return f"{bdp.WIKIPEDIA_BASE}/wiki/{quote(title.replace(' ', '_'))}"
    return url.rstrip("/")


def normalize_bool(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    text = normalize_text(value).lower()
    if text in {"true", "1", "yes"}:
        return "true"
    if text in {"false", "0", "no"}:
        return "false"
    return text


def normalize_float(value: Any) -> float | None:
    text = normalize_text(value)
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def equivalent(field: str, existing: Any, rebuilt: Any) -> bool:
    if field == "source_url":
        return canonical_wikipedia_url(str(existing)) == canonical_wikipedia_url(str(rebuilt))
    if field in BOOL_FIELDS:
        return normalize_bool(existing) == normalize_bool(rebuilt)
    if field in FLOAT_FIELDS:
        left = normalize_float(existing)
        right = normalize_float(rebuilt)
        if left is None and right is None:
            return True
        if left is None or right is None:
            return False
        return math.isclose(left, right, rel_tol=1e-9, abs_tol=1e-6)
    return normalize_text(existing) == normalize_text(rebuilt)


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def build_origin_map(candidate_rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    origin_map: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in candidate_rows:
        title = row.get("candidate_title", "")
        if not title:
            continue
        origin_map[title].append(
            {
                "list_page_origin": row.get("list_page_origin", ""),
                "parent_source": row.get("parent_source", ""),
                "discovery_root": row.get("discovery_root", ""),
                "source_family": row.get("source_family", ""),
            }
        )
    return origin_map


def fetch_page_wikitext_batch(client: bdp.WikipediaClient, titles: list[str]) -> dict[str, dict[str, Any]]:
    payload = client.api_get(
        {
            "action": "query",
            "titles": "|".join(titles),
            "redirects": 1,
            "prop": "revisions|info|coordinates|pageprops|categories",
            "rvslots": "main",
            "rvprop": "content",
            "inprop": "url",
            "cllimit": "max",
        }
    )
    query_block = payload.get("query", {})
    alias_map: dict[str, set[str]] = defaultdict(set)
    for item in query_block.get("normalized", []):
        alias_map[item.get("to", "")].add(item.get("from", ""))
    for item in query_block.get("redirects", []):
        alias_map[item.get("to", "")].add(item.get("from", ""))

    results: dict[str, dict[str, Any]] = {}
    for page in query_block.get("pages", []):
        page_title = page.get("title", "")
        if not page_title:
            continue
        revisions = page.get("revisions", [])
        wikitext = ""
        if revisions:
            revision = revisions[0]
            slots = revision.get("slots", {})
            main_slot = slots.get("main", {})
            wikitext = main_slot.get("content", "") or revision.get("content", "")
        record = {
            "title": page_title,
            "pageid": page.get("pageid"),
            "fullurl": page.get("fullurl") or bdp.wikipedia_url_for_title(page_title),
            "categories": [cat["title"].replace("Category:", "", 1) for cat in page.get("categories", [])],
            "coordinates": page.get("coordinates", []),
            "pageprops": page.get("pageprops", {}),
            "wikitext": wikitext,
            "fetched_at": bdp.NOW_UTC.isoformat(),
        }
        results[page_title] = record
        for alias in alias_map.get(page_title, set()):
            if alias:
                results[alias] = record
    for title in titles:
        if title not in results:
            results[title] = {
                "title": title,
                "pageid": None,
                "fullurl": bdp.wikipedia_url_for_title(title),
                "categories": [],
                "coordinates": [],
                "pageprops": {},
                "wikitext": "",
                "fetched_at": bdp.NOW_UTC.isoformat(),
            }
    return results


def compare_row(existing: dict[str, str], rebuilt: dict[str, Any], fields: list[str]) -> list[str]:
    mismatches: list[str] = []
    for field in fields:
        if not equivalent(field, existing.get(field, ""), rebuilt.get(field, "")):
            mismatches.append(field)
    return mismatches


def add_internal_issues(row: dict[str, str], issues: list[str]) -> None:
    battle_id = normalize_text(row.get("battle_id"))
    title = normalize_text(row.get("wikipedia_title"))
    battle_name = normalize_text(row.get("battle_name"))
    expected_id = ""
    match = re.fullmatch(r"battle_(\d+)", battle_id)
    if match:
        expected_id = match.group(1)
    source_url = canonical_wikipedia_url(row.get("source_url", ""))
    expected_url = bdp.wikipedia_url_for_title(title) if title else ""
    if source_url and expected_url and source_url != expected_url:
        issues.append("source_url_title_mismatch")
    if battle_name and title and battle_name != title:
        normalized_battle_name = normalize_text(row.get("battle_name_normalized"))
        normalized_expected = re.sub(r"\s*\([^)]*\)$", "", battle_name).strip()
        if normalized_battle_name != normalized_expected:
            issues.append("battle_name_normalization_mismatch")
    page_type = normalize_text(row.get("page_type"))
    if page_type and page_type not in PAGE_TYPES:
        issues.append("invalid_page_type")
    result_type = normalize_text(row.get("result_type")).lower()
    if result_type and result_type not in RESULT_TYPES:
        issues.append("invalid_result_type")
    normalized_result, derived_result_type = bdp.normalize_result(row.get("result_raw", ""))
    if not equivalent("result_normalized", row.get("result_normalized", ""), normalized_result):
        issues.append("result_normalization_mismatch")
    if not equivalent("result_type", row.get("result_type", ""), derived_result_type):
        issues.append("result_type_mismatch")
    parsed_date = bdp.parse_year_and_dates(row.get("date_raw", ""))
    for field in ["start_date", "end_date", "year", "century"]:
        if not equivalent(field, row.get(field, ""), parsed_date.get(field, "")):
            issues.append(f"date_field_mismatch:{field}")
    for raw_field, min_field, max_field in [
        ("strength_side_a_raw", "strength_side_a_min", "strength_side_a_max"),
        ("strength_side_b_raw", "strength_side_b_min", "strength_side_b_max"),
        ("casualties_side_a_raw", "casualties_side_a_min", "casualties_side_a_max"),
        ("casualties_side_b_raw", "casualties_side_b_min", "casualties_side_b_max"),
    ]:
        numeric = bdp.parse_numeric_range(row.get(raw_field, ""))
        if not equivalent(min_field, row.get(min_field, ""), numeric.get("min", "")):
            issues.append(f"numeric_range_mismatch:{min_field}")
        if not equivalent(max_field, row.get(max_field, ""), numeric.get("max", "")):
            issues.append(f"numeric_range_mismatch:{max_field}")
    lat = normalize_float(row.get("latitude"))
    lon = normalize_float(row.get("longitude"))
    if lat is not None and not (-90 <= lat <= 90):
        issues.append("latitude_out_of_range")
    if lon is not None and not (-180 <= lon <= 180):
        issues.append("longitude_out_of_range")
    if normalize_bool(row.get("infobox_present")) == "false" and normalize_text(row.get("result_raw")) == "":
        issues.append("weak_row_no_infobox_no_result")
    if normalize_text(row.get("battle_type")) == "land_battle" and title.lower() in {"air assault", "airborne warfare"}:
        issues.append("likely_false_positive_generic_topic")


def rebuild_row(
    client: bdp.WikipediaClient,
    page: dict[str, Any],
    origin_rows: list[dict[str, str]],
    config: bdp.PipelineConfig,
    temp_dir: Path,
) -> tuple[dict[str, Any] | None, list[str], str]:
    title = page.get("title", "")
    notes = ""
    issues: list[dict[str, Any]] = []
    clean_row, fetch_mode = None, "wikitext_batch"
    _raw_row, clean_row, _commander_rows, _classification = bdp.build_battle_rows_from_wikitext(
        page=page,
        origin_rows=origin_rows,
        config=config,
        issues=issues,
        json_dir=temp_dir,
        client=client,
    )
    if clean_row is None and title:
        fetch_mode = "full_parse_fallback"
        worker_result = bdp.extract_page_worker(
            title=title,
            origin_rows=origin_rows,
            config=config,
            json_dir=temp_dir,
            metadata_pageid=page.get("pageid"),
            mode="full",
        )
        clean_row = worker_result.get("clean_row")
        if worker_result.get("error_kind"):
            notes = f"worker_error={worker_result['error_kind']}"
    issue_types = sorted({issue.get("issue_type", "") for issue in issues if issue.get("issue_type")})
    return clean_row, issue_types, fetch_mode if not notes else f"{fetch_mode};{notes}"


def read_completed_titles(path: Path) -> set[str]:
    if not path.exists():
        return set()
    with path.open("r", encoding="utf-8", newline="") as handle:
        return {row.get("wikipedia_title", "") for row in csv.DictReader(handle) if row.get("wikipedia_title")}


def write_summary(path: Path, rows: list[dict[str, str]]) -> None:
    status_counts = Counter(row["status"] for row in rows)
    issue_type_counts = Counter()
    stable_field_counts = Counter()
    diagnostic_field_counts = Counter()
    for row in rows:
        for item in filter(None, row["issue_types"].split("|")):
            issue_type_counts[item] += 1
        for item in filter(None, row["stable_mismatch_fields"].split("|")):
            stable_field_counts[item] += 1
        for item in filter(None, row["diagnostic_mismatch_fields"].split("|")):
            diagnostic_field_counts[item] += 1
    summary = {
        "rows_checked": len(rows),
        "status_counts": dict(status_counts),
        "issue_type_counts_top50": dict(issue_type_counts.most_common(50)),
        "stable_mismatch_fields_top50": dict(stable_field_counts.most_common(50)),
        "diagnostic_mismatch_fields_top50": dict(diagnostic_field_counts.most_common(50)),
    }
    path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    args = parse_args()
    csv_path = Path(args.csv)
    candidate_csv_path = Path(args.candidate_csv)
    output_dir = Path(args.output_dir)
    temp_dir = output_dir / "_tmp"
    output_dir.mkdir(parents=True, exist_ok=True)
    temp_dir.mkdir(parents=True, exist_ok=True)
    result_csv_path = output_dir / "row_audit.csv"
    summary_path = output_dir / "summary.json"

    battle_rows = load_rows(csv_path)
    if args.limit:
        battle_rows = battle_rows[: args.limit]
    candidate_rows = load_rows(candidate_csv_path)
    origin_map = build_origin_map(candidate_rows)

    completed_titles = read_completed_titles(result_csv_path) if args.resume else set()
    should_write_header = not result_csv_path.exists() or not args.resume

    config = bdp.PipelineConfig(
        output_dir=output_dir,
        cache_dir=Path(args.live_cache_dir),
        reuse_cache=True,
        save_json=False,
        max_root_links=None,
        max_list_pages=None,
        max_battle_pages=None,
        request_sleep=args.request_sleep,
        request_timeout=args.request_timeout,
    )
    Path(args.live_cache_dir).mkdir(parents=True, exist_ok=True)
    client = bdp.WikipediaClient(config)

    processed_rows: list[dict[str, str]] = []
    if args.resume and result_csv_path.exists():
        with result_csv_path.open("r", encoding="utf-8", newline="") as handle:
            processed_rows.extend(list(csv.DictReader(handle)))

    with result_csv_path.open("a" if args.resume else "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_FIELDNAMES)
        if should_write_header:
            writer.writeheader()

        pending_rows = [row for row in battle_rows if row.get("wikipedia_title", "") not in completed_titles]
        for batch_start in range(0, len(pending_rows), args.batch_size):
            batch = pending_rows[batch_start : batch_start + args.batch_size]
            titles = [row["wikipedia_title"] for row in batch]
            page_map = fetch_page_wikitext_batch(client, titles)
            for offset, row in enumerate(batch, start=batch_start + 1):
                title = row["wikipedia_title"]
                page = page_map.get(title, {"title": title, "pageid": None, "fullurl": row.get("source_url", ""), "categories": [], "coordinates": [], "pageprops": {}, "wikitext": ""})
                internal_issues: list[str] = []
                add_internal_issues(row, internal_issues)
                rebuilt_row, extraction_issue_types, fetch_mode = rebuild_row(
                    client=client,
                    page=page,
                    origin_rows=origin_map.get(title, []),
                    config=config,
                    temp_dir=temp_dir,
                )

                stable_mismatch_fields: list[str] = []
                diagnostic_mismatch_fields: list[str] = []
                notes = ""
                live_title = page.get("title", "")
                live_pageid = page.get("pageid", "")
                status = "ok"
                if rebuilt_row is None:
                    status = "rebuild_failed"
                    notes = "Could not rebuild row from source."
                else:
                    stable_mismatch_fields = compare_row(row, rebuilt_row, STABLE_COMPARE_FIELDS)
                    diagnostic_mismatch_fields = compare_row(row, rebuilt_row, DIAGNOSTIC_COMPARE_FIELDS)
                    if internal_issues or stable_mismatch_fields:
                        status = "needs_review"

                combined_issue_types = sorted(set(internal_issues + extraction_issue_types))
                output_row = {
                    "row_number": str(offset),
                    "wikipedia_title": title,
                    "battle_id": row.get("battle_id", ""),
                    "status": status,
                    "issue_count": str(len(combined_issue_types) + len(stable_mismatch_fields) + len(diagnostic_mismatch_fields)),
                    "internal_issue_count": str(len(combined_issue_types)),
                    "stable_mismatch_count": str(len(stable_mismatch_fields)),
                    "diagnostic_mismatch_count": str(len(diagnostic_mismatch_fields)),
                    "issue_types": "|".join(combined_issue_types),
                    "stable_mismatch_fields": "|".join(stable_mismatch_fields),
                    "diagnostic_mismatch_fields": "|".join(diagnostic_mismatch_fields),
                    "live_title": str(live_title),
                    "live_pageid": str(live_pageid or ""),
                    "live_fetch_mode": fetch_mode,
                    "notes": notes,
                }
                writer.writerow(output_row)
                handle.flush()
                processed_rows.append(output_row)

    write_summary(summary_path, processed_rows)
    print(json.dumps(json.loads(summary_path.read_text(encoding="utf-8")), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
