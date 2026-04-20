from __future__ import annotations

import csv
import math
import re
from collections import defaultdict
from pathlib import Path
from typing import Any
from urllib.parse import quote, unquote, urlparse

import battle_dataset_pipeline as bdp


ALLOWED_PAGE_TYPES = {
    "battle_article",
    "war_conflict_article",
    "campaign_article",
    "operation_article",
}

ALLOWED_RESULT_TYPES = {
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

KNOWN_FALSE_POSITIVE_TITLES = {
    "air assault",
    "principles of war",
    "united nations disengagement observer force",
    "zhang xiu (warlord)",
    "popular front for the liberation of palestine - general command",
    "popular front for the liberation of palestine - general command".replace("-", "\u2013"),
}

GENERIC_FALSE_POSITIVE_CATEGORY_KEYWORDS = (
    "strategy",
    "tactics",
    "doctrine",
    "manual",
    "observer mission",
    "observer force",
    "military unit",
    "political party",
    "political movement",
    "organization",
    "infantry",
    "airborne warfare",
    "aerial warfare",
)

SUSPICIOUS_DATE_TOKENS = (
    "fm ",
    "field manual",
    "manual",
    "isbn",
    "edition",
    "chapter",
    "outline",
)

SUSPICIOUS_RESULT_TOKENS = (
    "although",
    "however",
    "according to",
    "some authors",
    "see ",
    "aftermath",
    "citation needed",
    "claimed by",
)

MAIN_FIELDNAMES = [
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
    "date_parse_confidence",
    "war_name",
    "campaign_name",
    "location_raw",
    "location_normalized",
    "latitude",
    "longitude",
    "present_day_country",
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
    "page_type_confidence",
    "classification_notes",
    "acceptance_reason",
    "battle_type",
    "infobox_present",
    "text_length",
    "categories",
    "list_page_origin",
    "parent_list_page",
    "discovery_root",
    "source_family",
    "extraction_confidence",
    "notes",
]

COMPARISON_FIELDS = [
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
    "location_raw",
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
    "page_type",
    "battle_type",
    "infobox_present",
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


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def normalize_text(value: Any) -> str:
    return bdp.normalize_space("" if value is None else str(value))


def normalize_bool(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    lowered = normalize_text(value).lower()
    if lowered in {"true", "1", "yes"}:
        return "true"
    if lowered in {"false", "0", "no"}:
        return "false"
    return lowered


def normalize_float(value: Any) -> float | None:
    text = normalize_text(value)
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def canonical_wikipedia_url(url: str) -> str:
    if not url:
        return ""
    parsed = urlparse(url)
    path = unquote(parsed.path)
    if path.startswith("/wiki/"):
        title = path[len("/wiki/") :].replace("_", " ")
        return f"{bdp.WIKIPEDIA_BASE}/wiki/{quote(title.replace(' ', '_'))}"
    return url.rstrip("/")


def equivalent(field: str, left: Any, right: Any) -> bool:
    if field == "source_url":
        return canonical_wikipedia_url(str(left)) == canonical_wikipedia_url(str(right))
    if field in BOOL_FIELDS:
        return normalize_bool(left) == normalize_bool(right)
    if field in FLOAT_FIELDS:
        left_value = normalize_float(left)
        right_value = normalize_float(right)
        if left_value is None and right_value is None:
            return True
        if left_value is None or right_value is None:
            return False
        return math.isclose(left_value, right_value, rel_tol=1e-9, abs_tol=1e-6)
    return normalize_text(left) == normalize_text(right)


def rows_differ(left: dict[str, Any], right: dict[str, Any]) -> bool:
    return any(not equivalent(field, left.get(field, ""), right.get(field, "")) for field in COMPARISON_FIELDS)


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


def result_label_for_type(result_type: str) -> str:
    mapping = {
        "victory": "Victory",
        "decisive_victory": "Decisive victory",
        "pyrrhic_victory": "Pyrrhic victory",
        "tactical_victory": "Tactical victory",
        "defeat": "Defeat",
        "draw": "Draw",
        "stalemate": "Stalemate",
        "indecisive": "Indecisive",
        "disputed": "Disputed",
        "unknown": "",
    }
    return mapping.get(result_type, "")


def sanitize_result_raw(raw_value: Any, result_type: str) -> str:
    text = normalize_text(raw_value)
    if not text:
        return ""
    lowered = text.lower()
    if any(token in lowered for token in SUSPICIOUS_RESULT_TOKENS) or len(text) > 120:
        return result_label_for_type(result_type)
    return text


def sanitize_candidate_row(row: dict[str, Any], rebuild_mode: str) -> dict[str, Any]:
    cleaned: dict[str, Any] = {}
    for field in MAIN_FIELDNAMES:
        cleaned[field] = row.get(field, "")

    cleaned["battle_name"] = normalize_text(cleaned.get("battle_name"))
    cleaned["battle_name_normalized"] = re.sub(r"\s*\([^)]*\)$", "", cleaned["battle_name"]).strip()
    cleaned["wikipedia_title"] = normalize_text(cleaned.get("wikipedia_title"))
    cleaned["source_url"] = canonical_wikipedia_url(str(cleaned.get("source_url", "")))
    cleaned["war_name"] = normalize_text(cleaned.get("war_name"))
    cleaned["campaign_name"] = normalize_text(cleaned.get("campaign_name"))
    cleaned["location_raw"] = normalize_text(cleaned.get("location_raw"))
    cleaned["location_normalized"] = normalize_text(cleaned.get("location_normalized") or cleaned["location_raw"])
    cleaned["present_day_country"] = normalize_text(cleaned.get("present_day_country"))
    cleaned["date_raw"] = normalize_text(cleaned.get("date_raw"))
    date_info = bdp.parse_year_and_dates(cleaned["date_raw"])
    cleaned["start_date"] = date_info.get("start_date", "")
    cleaned["end_date"] = date_info.get("end_date", "")
    cleaned["year"] = date_info.get("year", "")
    cleaned["century"] = date_info.get("century", "")
    cleaned["date_parse_confidence"] = date_info.get("date_parse_confidence", 0.0)

    inferred_normalized, inferred_type = bdp.normalize_result(cleaned.get("result_raw", ""))
    if normalize_text(cleaned.get("result_type")) not in ALLOWED_RESULT_TYPES:
        cleaned["result_type"] = inferred_type
    cleaned["result_type"] = normalize_text(cleaned.get("result_type")).lower() or inferred_type
    cleaned["result_raw"] = sanitize_result_raw(cleaned.get("result_raw"), cleaned["result_type"])
    cleaned["result_normalized"], cleaned["result_type"] = bdp.normalize_result(cleaned["result_raw"])

    for field in (
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
        "categories",
        "list_page_origin",
        "parent_list_page",
        "discovery_root",
        "source_family",
        "classification_notes",
        "acceptance_reason",
        "battle_type",
        "page_type",
    ):
        cleaned[field] = normalize_text(cleaned.get(field))

    for raw_field, min_field, max_field in [
        ("strength_side_a_raw", "strength_side_a_min", "strength_side_a_max"),
        ("strength_side_b_raw", "strength_side_b_min", "strength_side_b_max"),
        ("casualties_side_a_raw", "casualties_side_a_min", "casualties_side_a_max"),
        ("casualties_side_b_raw", "casualties_side_b_min", "casualties_side_b_max"),
    ]:
        numeric_range = bdp.parse_numeric_range(cleaned.get(raw_field, ""))
        cleaned[min_field] = numeric_range.get("min", "")
        cleaned[max_field] = numeric_range.get("max", "")

    cleaned["notes"] = f"validated_rebuild_mode={rebuild_mode}"
    return cleaned


def date_validation_reasons(row: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    raw_date = normalize_text(row.get("date_raw"))
    if not raw_date:
        return ["missing_date"]
    lowered = raw_date.lower()
    if any(token in lowered for token in SUSPICIOUS_DATE_TOKENS):
        reasons.append("suspicious_date_text")
    date_info = bdp.parse_year_and_dates(raw_date)
    year_value = date_info.get("year")
    if year_value in {"", None}:
        reasons.append("unparsed_year")
    else:
        try:
            year_float = float(year_value)
            if year_float < 1 or year_float > 2100:
                reasons.append("year_out_of_range")
        except (TypeError, ValueError):
            reasons.append("invalid_year_value")
    start_date = date_info.get("start_date", "")
    end_date = date_info.get("end_date", "")
    if start_date and end_date and start_date > end_date:
        reasons.append("start_after_end")
    return reasons


def weak_source_reasons(row: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    belligerent_signal = bool(normalize_text(row.get("belligerent_1_raw")) and normalize_text(row.get("belligerent_2_raw")))
    commander_signal = bool(normalize_text(row.get("commander_side_a_raw")) or normalize_text(row.get("commander_side_b_raw")))
    location_signal = bool(normalize_text(row.get("location_raw")))
    war_signal = bool(normalize_text(row.get("war_name")))
    result_signal = normalize_text(row.get("result_type")) != "unknown"
    infobox_signal = normalize_bool(row.get("infobox_present")) == "true"
    signal_count = sum(
        [
            1 if belligerent_signal else 0,
            1 if commander_signal else 0,
            1 if location_signal else 0,
            1 if war_signal else 0,
            1 if result_signal else 0,
            1 if infobox_signal else 0,
        ]
    )
    if signal_count < 2:
        reasons.append("insufficient_source_evidence")
    if not infobox_signal and not result_signal:
        reasons.append("no_infobox_and_no_result")
    return reasons


def result_validation_reasons(row: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    result_type = normalize_text(row.get("result_type")).lower()
    if result_type not in ALLOWED_RESULT_TYPES:
        reasons.append("invalid_result_type")
        return reasons
    result_raw = normalize_text(row.get("result_raw"))
    normalized, inferred_type = bdp.normalize_result(result_raw)
    if result_type == "unknown":
        if result_raw and normalize_text(row.get("result_normalized")) not in {"Unknown", ""}:
            reasons.append("unknown_result_mismatch")
    else:
        if inferred_type == "unknown":
            reasons.append("unsupported_result_text")
        if normalize_text(row.get("result_normalized")) != normalize_text(normalized):
            reasons.append("result_normalized_mismatch")
        if inferred_type != result_type:
            reasons.append("result_type_mismatch")
    return reasons


def generic_false_positive_reasons(title: str, row: dict[str, Any], categories: list[str]) -> list[str]:
    reasons: list[str] = []
    lowered_title = normalize_text(title).lower()
    category_blob = " | ".join(categories).lower()
    if lowered_title in KNOWN_FALSE_POSITIVE_TITLES:
        reasons.append("known_false_positive")
    if any(keyword in category_blob for keyword in GENERIC_FALSE_POSITIVE_CATEGORY_KEYWORDS):
        reasons.append("generic_category_signal")
    has_any_event_fields = any(
        normalize_text(row.get(field))
        for field in (
            "date_raw",
            "result_raw",
            "belligerent_1_raw",
            "belligerent_2_raw",
            "commander_side_a_raw",
            "commander_side_b_raw",
            "location_raw",
            "war_name",
        )
    )
    if normalize_bool(row.get("infobox_present")) != "true" and not has_any_event_fields:
        reasons.append("no_event_specific_fields")
    if "(warlord)" in lowered_title:
        reasons.append("biography_title_signal")
    return reasons


def main_row_blockers(title: str, row: dict[str, Any], categories: list[str]) -> list[str]:
    blockers: list[str] = []
    page_type = normalize_text(row.get("page_type"))
    if page_type not in ALLOWED_PAGE_TYPES:
        blockers.append("disallowed_page_type")
    blockers.extend(generic_false_positive_reasons(title, row, categories))
    blockers.extend(date_validation_reasons(row))
    blockers.extend(result_validation_reasons(row))
    blockers.extend(weak_source_reasons(row))
    deduped: list[str] = []
    seen: set[str] = set()
    for reason in blockers:
        if reason and reason not in seen:
            seen.add(reason)
            deduped.append(reason)
    return deduped


def build_wikitext_candidate(
    client: bdp.WikipediaClient,
    page: dict[str, Any],
    origin_rows: list[dict[str, str]],
    config: bdp.PipelineConfig,
    json_dir: Path,
) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    raw_row, clean_row, _commander_rows, classification = bdp.build_battle_rows_from_wikitext(
        page=page,
        origin_rows=origin_rows,
        config=config,
        issues=issues,
        json_dir=json_dir,
        client=client,
    )
    return {
        "raw_row": raw_row,
        "clean_row": clean_row,
        "classification": classification,
        "issues": issues,
        "page": page,
        "mode": "wikitext",
    }


def build_full_parse_candidate(
    client: bdp.WikipediaClient,
    title: str,
    origin_rows: list[dict[str, str]],
    config: bdp.PipelineConfig,
    json_dir: Path,
) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    try:
        page = client.fetch_page_bundle(title, include_query_metadata=True)
    except Exception as exc:  # noqa: BLE001
        return {
            "raw_row": None,
            "clean_row": None,
            "classification": {"accepted": False, "page_type": "fetch_error", "confidence": 0.0, "reasons": str(exc)},
            "issues": [],
            "page": {"title": title, "categories": []},
            "mode": "full_parse_error",
            "error_message": str(exc),
        }
    raw_row, clean_row, _commander_rows, classification = bdp.build_battle_rows(
        page=page,
        origin_rows=origin_rows,
        config=config,
        issues=issues,
        json_dir=json_dir,
        client=client,
    )
    return {
        "raw_row": raw_row,
        "clean_row": clean_row,
        "classification": classification,
        "issues": issues,
        "page": page,
        "mode": "full_parse",
    }


def decide_rebuild_result(
    title: str,
    wikitext_candidate: dict[str, Any],
    full_candidate: dict[str, Any] | None,
) -> dict[str, Any]:
    candidates = [candidate for candidate in [wikitext_candidate, full_candidate] if candidate]
    for candidate in candidates:
        clean_row = candidate.get("clean_row")
        if not clean_row:
            continue
        sanitized = sanitize_candidate_row(clean_row, candidate["mode"])
        categories = split_pipe_values(sanitized.get("categories", "")) or candidate.get("page", {}).get("categories", [])
        blockers = main_row_blockers(title, sanitized, categories)
        if not blockers:
            return {
                "decision": "valid",
                "row": sanitized,
                "reason_codes": [],
                "rebuild_mode": candidate["mode"],
                "categories": categories,
            }

    rejection_signals: list[str] = []
    for candidate in candidates:
        classification = candidate.get("classification", {})
        if classification and not classification.get("accepted", False):
            rejection_signals.append(normalize_text(classification.get("page_type")))
    if rejection_signals:
        return {
            "decision": "remove_false_positive",
            "row": None,
            "reason_codes": sorted(set(rejection_signals)),
            "rebuild_mode": "none",
            "categories": wikitext_candidate.get("page", {}).get("categories", []),
        }

    best_invalid: dict[str, Any] | None = None
    best_invalid_blockers: list[str] | None = None
    for candidate in candidates:
        clean_row = candidate.get("clean_row")
        if not clean_row:
            continue
        sanitized = sanitize_candidate_row(clean_row, candidate["mode"])
        categories = split_pipe_values(sanitized.get("categories", "")) or candidate.get("page", {}).get("categories", [])
        blockers = main_row_blockers(title, sanitized, categories)
        if best_invalid is None or len(blockers) < len(best_invalid_blockers or []):
            best_invalid = {
                "row": sanitized,
                "rebuild_mode": candidate["mode"],
                "categories": categories,
            }
            best_invalid_blockers = blockers

    if best_invalid:
        generic_reasons = generic_false_positive_reasons(title, best_invalid["row"], best_invalid["categories"])
        strong_generic_reasons = {"known_false_positive", "no_event_specific_fields", "biography_title_signal"}
        if generic_reasons and (
            len(best_invalid_blockers or []) == len(generic_reasons)
            or any(reason in strong_generic_reasons for reason in generic_reasons)
        ):
            return {
                "decision": "remove_false_positive",
                "row": None,
                "reason_codes": generic_reasons,
                "rebuild_mode": best_invalid["rebuild_mode"],
                "categories": best_invalid["categories"],
            }
        return {
            "decision": "quarantine",
            "row": best_invalid["row"],
            "reason_codes": best_invalid_blockers or ["unvalidated_conflict_row"],
            "rebuild_mode": best_invalid["rebuild_mode"],
            "categories": best_invalid["categories"],
        }

    return {
        "decision": "quarantine",
        "row": None,
        "reason_codes": ["rebuild_failed"],
        "rebuild_mode": "none",
        "categories": wikitext_candidate.get("page", {}).get("categories", []),
    }


def split_pipe_values(value: Any) -> list[str]:
    text = normalize_text(value)
    if not text:
        return []
    return [part.strip() for part in text.split("|") if part.strip()]
