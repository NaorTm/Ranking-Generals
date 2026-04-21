from __future__ import annotations

import csv
import hashlib
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

import battle_dataset_pipeline as bdp


BATTLE_COMMANDER_FIELDNAMES = [
    "battle_id",
    "battle_name",
    "year",
    "war_name",
    "commander_name_raw",
    "commander_name_normalized",
    "commander_wikipedia_url",
    "side",
    "belligerent",
    "battle_result_for_commander",
    "role_in_battle",
    "opposing_commander_names_raw",
    "location_normalized",
    "strength_side_raw",
    "strength_enemy_raw",
    "casualties_side_raw",
    "casualties_enemy_raw",
    "source_url",
    "parse_notes",
    "identity_confidence",
]

COMMANDER_QUARANTINE_FIELDNAMES = BATTLE_COMMANDER_FIELDNAMES + [
    "quarantine_reason",
    "candidate_source",
    "validation_status",
]

SIDE_ISSUE_FIELDNAMES = [
    "battle_id",
    "battle_name",
    "wikipedia_title",
    "side",
    "raw_text",
    "issue_type",
    "details",
]

MASTER_FIELDNAMES = [
    "commander_id",
    "name_primary",
    "name_variants",
    "wikipedia_page",
    "birth_year",
    "death_year",
    "civilization_or_state",
    "era",
    "service_branch",
    "notes",
    "identity_resolution_method",
]

ROW_AUDIT_FIELDNAMES = [
    "row_number",
    "battle_id",
    "battle_name",
    "commander_name_normalized",
    "commander_wikipedia_url",
    "status",
    "blocker_count",
    "blockers",
]

MASTER_AUDIT_FIELDNAMES = [
    "row_number",
    "commander_id",
    "name_primary",
    "wikipedia_page",
    "status",
    "blocker_count",
    "blockers",
]

PERSON_CATEGORY_KEYWORDS = (
    "births",
    "deaths",
    "people",
    "biographies",
    "military personnel",
    "generals",
    "admirals",
    "marshals",
    "officers",
    "commanders",
    "monarchs",
    "kings",
    "queens",
    "princes",
    "dukes",
    "earls",
    "counts",
    "barons",
    "nobility",
    "rulers",
    "sultans",
    "khans",
    "pashas",
    "emperors",
    "pharaohs",
    "chieftains",
    "viziers",
    "statesmen",
    "consuls",
    "censors",
    "magistri",
    "senators",
    "patricians",
    "nobles",
    "politicians",
)

NON_PERSON_CATEGORY_KEYWORDS = (
    "flags",
    "emblems",
    "military units",
    "regiments",
    "brigades",
    "battalions",
    "divisions",
    "corps",
    "armies",
    "fleets",
    "navies",
    "ships",
    "aircraft",
    "weapons",
    "battles",
    "wars",
    "campaigns",
    "operations",
    "conflicts",
    "massacres",
    "sieges",
    "organizations",
    "political parties",
    "political movements",
    "governments",
    "states",
    "countries",
    "kingdoms",
    "empires",
    "republics",
    "insurgent groups",
    "observer missions",
    "geography",
    "villages",
    "castles",
    "districts",
    "neighborhoods",
    "newspapers",
    "websites",
    "treaties",
)

NON_PERSON_TITLE_KEYWORDS = (
    "flag",
    ".svg",
    "naval flag",
    "army",
    "corps",
    "division",
    "brigade",
    "regiment",
    "battalion",
    "fleet",
    "forces",
    "front",
    "movement",
    "government",
    "kingdom",
    "empire",
    "republic",
    "state",
    "operation",
    "campaign",
    "war",
    "battle",
    "siege",
    "conflict",
    "observer force",
    "sultanate",
    "despotate",
    "sanjak",
    "treaty",
    "press",
    "media group",
    "reliefweb",
    "politico",
    "castle",
)

SUSPICIOUS_NAME_PHRASES = (
    "according to",
    "not reliable",
    "via social media",
    "currently no confirmed information",
    "later ruled",
    "although",
    "overall",
    "captured",
    "killed during",
    "unknown",
    "see ]",
    "see also",
    "citation needed",
    "probably none",
    "former flag",
)

LANGUAGE_CODE_TOKENS = {
    "ar",
    "cs",
    "da",
    "de",
    "el",
    "es",
    "fa",
    "fi",
    "fr",
    "he",
    "hu",
    "it",
    "ja",
    "ko",
    "nl",
    "pl",
    "pt",
    "ro",
    "ru",
    "sv",
    "tr",
    "uk",
    "ur",
    "vi",
    "zh",
}

VALID_SIDE_RESULTS = {"victory", "defeat", "draw", "stalemate", "indecisive", "disputed", "unknown"}
VALID_IDENTITY_CONFIDENCE = {"high", "medium"}
VALID_SIDES = {"side_a", "side_b", "side_c"}
GENERIC_RANK_ONLY_NAMES = {
    "admiral",
    "brigadier",
    "brigadier general",
    "captain",
    "colonel",
    "colonel general",
    "commander",
    "general",
    "general officer",
    "lieutenant",
    "lieutenant colonel",
    "lieutenant general",
    "major",
    "major general",
    "marshal",
    "officer",
}


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def normalize_text(value: Any) -> str:
    return bdp.normalize_space("" if value is None else str(value))


def url_to_title(url: str) -> str:
    if not url:
        return ""
    path = urlparse(url).path
    if "/wiki/" not in path:
        return ""
    tail = path.split("/wiki/", 1)[1]
    return unquote(tail).replace("_", " ")


def canonical_wikipedia_url(url: str) -> str:
    title = url_to_title(url)
    if not title:
        return normalize_text(url)
    return bdp.wikipedia_url_for_title(title)


def split_pipe_values(value: Any) -> list[str]:
    text = normalize_text(value)
    if not text:
        return []
    return [normalize_text(part) for part in text.split("|") if normalize_text(part)]


def battle_side_value(row: dict[str, Any], stem: str, side_key: str) -> str:
    if stem == "belligerent":
        suffix = {"side_a": "1", "side_b": "2", "side_c": "3"}[side_key]
        return normalize_text(row.get(f"belligerent_{suffix}_raw", ""))
    if stem == "commander":
        suffix = {"side_a": "a", "side_b": "b", "side_c": "c"}[side_key]
        return normalize_text(row.get(f"commander_side_{suffix}_raw", ""))
    suffix = {"side_a": "a", "side_b": "b", "side_c": "c"}[side_key]
    return normalize_text(row.get(f"{stem}_side_{suffix}_raw", ""))


def battle_side_map(row: dict[str, Any], stem: str) -> dict[str, str]:
    return {side_key: battle_side_value(row, stem, side_key) for side_key in VALID_SIDES}


def split_lines(value: str) -> list[str]:
    parts = [normalize_text(part) for part in re.split(r"[\n;]+", value) if normalize_text(part)]
    return parts


def split_belligerent_tokens(value: str) -> list[str]:
    tokens: list[str] = []
    for part in re.split(r"[\n|/,;]+", value):
        cleaned = normalize_text(part)
        if cleaned:
            tokens.append(cleaned)
    return tokens


def strip_language_edge_tokens(text: str) -> str:
    tokens = text.split()
    while tokens and tokens[0].lower() in LANGUAGE_CODE_TOKENS:
        tokens.pop(0)
    while tokens and tokens[-1].lower() in LANGUAGE_CODE_TOKENS:
        tokens.pop()
    return " ".join(tokens)


def strip_belligerent_prefix(text: str, belligerent: str) -> str:
    working = normalize_text(text)
    prefixes = sorted(split_belligerent_tokens(belligerent), key=len, reverse=True)
    for prefix in prefixes:
        if len(prefix.split()) > 6:
            continue
        pattern = re.compile(rf"^{re.escape(prefix)}\s+", re.I)
        updated = pattern.sub("", working)
        if updated != working:
            working = normalize_text(updated)
            break
    return working


def clean_commander_name(raw_value: str, belligerent: str = "") -> str:
    text = normalize_text(raw_value)
    if not text:
        return ""
    text = re.sub(r"\[[^\]]*\]", "", text)
    text = re.sub(r"\([^)]*\)", "", text)
    text = re.sub(r"\b\d+px\b", "", text, flags=re.I)
    text = re.sub(r"\.svg\b", "", text, flags=re.I)
    text = re.sub(r"\bFile:[^ ]+\b", "", text, flags=re.I)
    text = text.replace("“", "").replace("”", "").replace('"', "")
    text = text.replace("‘", "'").replace("’", "'")
    text = bdp.COMMANDER_PREFIX_PATTERN.sub("", text)
    text = strip_belligerent_prefix(text, belligerent)
    text = strip_language_edge_tokens(text)
    text = re.sub(r"\s+", " ", text).strip(" ,;:/|-")
    return normalize_text(text)


def commander_name_blockers(raw_name: str, normalized_name: str, linked: bool) -> list[str]:
    blockers: list[str] = []
    raw_lower = normalize_text(raw_name).lower()
    name_lower = normalize_text(normalized_name).lower()
    if not normalized_name:
        blockers.append("empty_name")
        return blockers
    if any(phrase in raw_lower or phrase in name_lower for phrase in SUSPICIOUS_NAME_PHRASES):
        blockers.append("narrative_text_artifact")
    if re.search(r"\.(?:svg|png)|\b\d+px\b|\bflag\b", raw_lower, flags=re.I) or re.search(
        r"\.(?:svg|png)|\bflag\b", name_lower, flags=re.I
    ):
        blockers.append("graphic_artifact")
    if bdp.is_generic_commander_value(normalized_name):
        blockers.append("generic_commander_value")
    if name_lower in GENERIC_RANK_ONLY_NAMES:
        blockers.append("generic_rank_only_name")
    if len(normalized_name) > 80:
        blockers.append("name_too_long")
    if len(normalized_name.split()) > 10:
        blockers.append("too_many_tokens")
    if "|" in normalized_name or "\n" in normalized_name:
        blockers.append("unbroken_multi_value_name")
    if '"' in raw_name and len(normalized_name.split()) == 1:
        blockers.append("quoted_single_token_alias")
    if not linked and len(normalized_name.split()) == 1 and raw_lower.startswith("colonel "):
        blockers.append("title_only_short_name")
    return sorted(set(blockers))


def classify_commander_page(title: str, categories: list[str]) -> str:
    title_lower = normalize_text(title).lower()
    if title_lower.startswith(":") or re.match(r"^[a-z]{2,5}:", title_lower):
        return "nonperson"
    if any(keyword in title_lower for keyword in NON_PERSON_TITLE_KEYWORDS):
        return "nonperson"
    category_blob = " | ".join(categories).lower()
    person_hits = sum(1 for keyword in PERSON_CATEGORY_KEYWORDS if keyword in category_blob)
    nonperson_hits = sum(1 for keyword in NON_PERSON_CATEGORY_KEYWORDS if keyword in category_blob)
    if person_hits and nonperson_hits == 0:
        return "person"
    if nonperson_hits and person_hits == 0:
        title_name_blockers = commander_name_blockers(title, title, linked=True)
        if nonperson_hits == 1 and not title_name_blockers:
            return "uncertain"
        return "nonperson"
    if person_hits and nonperson_hits:
        return "person" if person_hits >= nonperson_hits else "nonperson"
    return "uncertain"


def belligerent_conflict(title: str, belligerent: str) -> bool:
    title_lower = normalize_text(title).lower()
    belligerent_lower = normalize_text(belligerent).lower()
    if title_lower and belligerent_lower and (
        title_lower == belligerent_lower
        or title_lower in belligerent_lower
        or belligerent_lower in title_lower
    ):
        return True
    for token in split_belligerent_tokens(belligerent):
        token_lower = token.lower()
        if len(token_lower) >= 4 and (token_lower == title_lower or token_lower in title_lower or title_lower in token_lower):
            return True
    return False


def side_cell_for_key(commander_fields: list[dict[str, Any]], side_key: str, battle_row: dict[str, Any]) -> dict[str, Any] | None:
    for entry in commander_fields:
        if entry.get("side") == side_key:
            return entry
    fallback_raw = battle_side_value(battle_row, "commander", side_key)
    if not fallback_raw:
        return None
    segments = split_lines(fallback_raw)
    if not segments:
        segments = bdp.split_raw_commander_text(fallback_raw)
    return {
        "side": side_key,
        "raw_text": fallback_raw,
        "raw_html": "",
        "segments": segments,
        "links": [],
    }


def extract_commander_candidates(
    side_cell: dict[str, Any],
    side_key: str,
    battle_row: dict[str, Any],
    link_meta: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    belligerent = battle_side_value(battle_row, "belligerent", side_key)
    accepted: list[dict[str, str]] = []
    rejected: list[dict[str, str]] = []
    issues: list[dict[str, str]] = []
    seen: set[str] = set()

    links = side_cell.get("links", []) or []
    if links:
        for link in links:
            title = normalize_text(link.get("title", ""))
            raw_name = normalize_text(link.get("text") or title)
            meta = link_meta.get(title, {"title": title, "categories": []})
            title_normalized = clean_commander_name(meta.get("title") or title, belligerent)
            display_normalized = clean_commander_name(raw_name, belligerent)
            normalized_name = title_normalized
            if display_normalized:
                display_blockers = commander_name_blockers(raw_name, display_normalized, linked=True)
                if not display_blockers and (
                    len(display_normalized.split()) > len(title_normalized.split())
                    or len(display_normalized) > len(title_normalized) + 8
                ):
                    normalized_name = display_normalized
            blockers = commander_name_blockers(raw_name, normalized_name, linked=True)
            page_class = classify_commander_page(meta.get("title") or title, meta.get("categories", []))
            if belligerent_conflict(meta.get("title") or title, belligerent):
                blockers.append("belligerent_link_not_person")
            if page_class == "nonperson":
                blockers.append("linked_page_nonperson")
            if blockers:
                rejected.append(
                    {
                        "raw_name": raw_name,
                        "normalized_name": normalized_name,
                        "wikipedia_url": canonical_wikipedia_url(meta.get("fullurl") or link.get("url", "")),
                        "reason": "|".join(sorted(set(blockers))),
                        "candidate_source": "linked_article",
                    }
                )
                continue
            canonical_url = canonical_wikipedia_url(meta.get("fullurl") or link.get("url", ""))
            key = f"{normalized_name.lower()}|{canonical_url}"
            if key in seen:
                continue
            seen.add(key)
            accepted.append(
                {
                    "raw_name": clean_commander_name(raw_name, belligerent) or normalized_name,
                    "normalized_name": normalized_name,
                    "wikipedia_url": canonical_url,
                    "identity_confidence": "high" if page_class == "person" else "medium",
                    "identity_resolution_method": "linked_article",
                    "candidate_source": "linked_article",
                }
            )

    if accepted:
        return accepted, rejected, issues

    raw_segments = side_cell.get("segments") or []
    if not raw_segments:
        raw_segments = bdp.split_raw_commander_text(side_cell.get("raw_text", ""))
    expanded_segments: list[str] = []
    for segment in raw_segments:
        split_segments = bdp.split_raw_commander_text(segment)
        if split_segments:
            expanded_segments.extend(split_segments)
        else:
            expanded_segments.append(segment)

    for segment in expanded_segments:
        raw_name = normalize_text(segment)
        normalized_name = clean_commander_name(raw_name, belligerent)
        blockers = commander_name_blockers(raw_name, normalized_name, linked=False)
        if blockers:
            rejected.append(
                {
                    "raw_name": raw_name,
                    "normalized_name": normalized_name,
                    "wikipedia_url": "",
                    "reason": "|".join(sorted(set(blockers))),
                    "candidate_source": "raw_segment",
                }
            )
            continue
        key = f"{normalized_name.lower()}|"
        if key in seen:
            continue
        seen.add(key)
        accepted.append(
            {
                "raw_name": raw_name,
                "normalized_name": normalized_name,
                "wikipedia_url": "",
                "identity_confidence": "medium",
                "identity_resolution_method": "cleaned_segment_text",
                "candidate_source": "raw_segment",
            }
        )

    if not accepted and normalize_text(side_cell.get("raw_text", "")):
        issues.append(
            {
                "battle_id": normalize_text(battle_row.get("battle_id")),
                "battle_name": normalize_text(battle_row.get("battle_name")),
                "wikipedia_title": normalize_text(battle_row.get("wikipedia_title")),
                "side": side_key,
                "raw_text": normalize_text(side_cell.get("raw_text", "")),
                "issue_type": "no_valid_commander_candidates",
                "details": "All candidate commanders were rejected by strict validation.",
            }
        )

    return accepted, rejected, issues


def conservative_name_match(raw_name: str, candidate_name: str) -> bool:
    raw_clean = clean_commander_name(raw_name)
    candidate_clean = clean_commander_name(candidate_name)
    if not raw_clean or not candidate_clean:
        return False
    if raw_clean.lower() == candidate_clean.lower():
        return True
    raw_tokens = raw_clean.split()
    candidate_tokens = candidate_clean.split()
    if len(raw_tokens) == 1 and len(candidate_tokens) >= 2 and len(raw_tokens[0]) >= 6:
        return raw_tokens[0].lower() == candidate_tokens[-1].lower()
    return False


def recover_linked_commander_candidates(
    side_cell: dict[str, Any] | None,
    side_key: str,
    battle_row: dict[str, Any],
    page_wikitext: str,
    link_meta: dict[str, dict[str, Any]],
    existing_candidates: list[dict[str, str]],
) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    if not side_cell or not normalize_text(side_cell.get("raw_text", "")):
        return [], [], []

    belligerent = battle_side_value(battle_row, "belligerent", side_key)
    existing_keys = {
        f"{normalize_text(candidate.get('normalized_name')).lower()}|{normalize_text(candidate.get('wikipedia_url')).lower()}"
        for candidate in existing_candidates
    }
    raw_segments = side_cell.get("segments") or bdp.split_raw_commander_text(side_cell.get("raw_text", ""))
    usable_segments = []
    for segment in raw_segments:
        cleaned = clean_commander_name(segment, belligerent)
        blockers = commander_name_blockers(segment, cleaned, linked=False)
        if cleaned and not blockers:
            usable_segments.append((segment, cleaned))
    if not usable_segments:
        return [], [], []

    page_links = bdp.extract_wikilinks_from_wikitext(page_wikitext)
    person_links: list[dict[str, str]] = []
    surname_index: dict[str, list[dict[str, str]]] = defaultdict(list)
    for link in page_links:
        title = normalize_text(link.get("title", ""))
        if not title:
            continue
        meta = link_meta.get(title, {"title": title, "categories": [], "fullurl": link.get("url", "")})
        page_class = classify_commander_page(meta.get("title") or title, meta.get("categories", []))
        if page_class == "nonperson" or belligerent_conflict(meta.get("title") or title, belligerent):
            continue
        candidate_name = clean_commander_name(meta.get("title") or title, belligerent)
        blockers = commander_name_blockers(link.get("text") or title, candidate_name, linked=True)
        if not candidate_name or blockers:
            continue
        candidate = {
            "raw_name": candidate_name,
            "normalized_name": candidate_name,
            "wikipedia_url": canonical_wikipedia_url(meta.get("fullurl") or link.get("url", "")),
            "identity_confidence": "high" if page_class == "person" else "medium",
            "identity_resolution_method": "page_wikitext_link_match",
            "candidate_source": "page_wikitext_link_match",
        }
        person_links.append(candidate)
        surname = candidate_name.split()[-1].lower()
        surname_index[surname].append(candidate)

    recovered: list[dict[str, str]] = []
    rejected: list[dict[str, str]] = []
    issues: list[dict[str, str]] = []
    seen: set[str] = set()
    for raw_segment, cleaned_segment in usable_segments:
        matched_candidate = next(
            (candidate for candidate in person_links if conservative_name_match(cleaned_segment, candidate["normalized_name"])),
            None,
        )
        if matched_candidate is None and len(cleaned_segment.split()) == 1:
            surname_matches = surname_index.get(cleaned_segment.lower(), [])
            if len(surname_matches) == 1:
                matched_candidate = surname_matches[0]
        if matched_candidate is None:
            continue
        key = f"{matched_candidate['normalized_name'].lower()}|{matched_candidate['wikipedia_url'].lower()}"
        if key in existing_keys or key in seen:
            continue
        seen.add(key)
        recovered.append(
            {
                **matched_candidate,
                "raw_name": clean_commander_name(raw_segment, belligerent) or matched_candidate["normalized_name"],
            }
        )

    if not recovered and person_links:
        issues.append(
            {
                "battle_id": normalize_text(battle_row.get("battle_id")),
                "battle_name": normalize_text(battle_row.get("battle_name")),
                "wikipedia_title": normalize_text(battle_row.get("wikipedia_title")),
                "side": side_key,
                "raw_text": normalize_text(side_cell.get("raw_text", "")),
                "issue_type": "no_recoverable_linked_commander",
                "details": "No conservative page-local linked commander match was found for the side cell text.",
            }
        )

    return recovered, rejected, issues


def build_commander_row(
    battle_row: dict[str, Any],
    side_key: str,
    commander: dict[str, str],
    opposing_names: list[str],
) -> dict[str, str]:
    belligerent_map = battle_side_map(battle_row, "belligerent")
    strength_map = battle_side_map(battle_row, "strength")
    casualty_map = battle_side_map(battle_row, "casualties")
    return {
        "battle_id": normalize_text(battle_row.get("battle_id")),
        "battle_name": normalize_text(battle_row.get("battle_name")),
        "year": normalize_text(battle_row.get("year")),
        "war_name": normalize_text(battle_row.get("war_name")),
        "commander_name_raw": normalize_text(commander["raw_name"]),
        "commander_name_normalized": normalize_text(commander["normalized_name"]),
        "commander_wikipedia_url": normalize_text(commander.get("wikipedia_url", "")),
        "side": side_key,
        "belligerent": belligerent_map.get(side_key, ""),
        "battle_result_for_commander": bdp.choose_side_result(
            side_key,
            normalize_text(battle_row.get("result_type")),
            normalize_text(battle_row.get("result_raw")),
            belligerent_map,
        ),
        "role_in_battle": "",
        "opposing_commander_names_raw": " | ".join(name for name in opposing_names if name),
        "location_normalized": normalize_text(battle_row.get("location_normalized") or battle_row.get("location_raw")),
        "strength_side_raw": strength_map.get(side_key, ""),
        "strength_enemy_raw": " | ".join(value for key, value in strength_map.items() if key != side_key and value),
        "casualties_side_raw": casualty_map.get(side_key, ""),
        "casualties_enemy_raw": " | ".join(value for key, value in casualty_map.items() if key != side_key and value),
        "source_url": normalize_text(battle_row.get("source_url")),
        "parse_notes": f"validated_commander_source={commander['candidate_source']};identity_resolution_method={commander['identity_resolution_method']}",
        "identity_confidence": normalize_text(commander["identity_confidence"]),
    }


def dedupe_commander_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    deduped: list[dict[str, str]] = []
    seen: set[str] = set()
    for row in rows:
        key = "||".join(
            [
                normalize_text(row.get("battle_id")),
                normalize_text(row.get("side")),
                normalize_text(row.get("commander_name_normalized")).lower(),
                normalize_text(row.get("commander_wikipedia_url")).lower(),
            ]
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)
    return deduped


def build_commanders_master(commanders_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    rows = dedupe_commander_rows(commanders_rows)
    linked_name_map: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        name_key = normalize_text(row.get("commander_name_normalized")).lower()
        url = canonical_wikipedia_url(normalize_text(row.get("commander_wikipedia_url")))
        url_title = url_to_title(url)
        url_title_blockers = commander_name_blockers(url_title, url_title, linked=True) if url_title else ["empty_name"]
        if name_key and url and not url_title.startswith(":") and not url_title_blockers:
            linked_name_map[name_key].add(url)

    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        normalized_name = normalize_text(row.get("commander_name_normalized"))
        url = canonical_wikipedia_url(normalize_text(row.get("commander_wikipedia_url")))
        if not url and len(linked_name_map.get(normalized_name.lower(), set())) == 1:
            url = next(iter(linked_name_map[normalized_name.lower()]))
        key = f"url:{url.lower()}" if url else f"name:{normalized_name.lower()}"
        grouped[key].append({**row, "resolved_url": url})

    master_rows: list[dict[str, str]] = []
    for key, group in grouped.items():
        resolved_url = normalize_text(group[0].get("resolved_url", ""))
        variants = sorted(
            {
                normalize_text(row.get("commander_name_raw"))
                for row in group
                if normalize_text(row.get("commander_name_raw"))
            }
        )
        if resolved_url:
            url_primary = url_to_title(resolved_url)
            normalized_counts = Counter(normalize_text(row.get("commander_name_normalized")) for row in group if normalize_text(row.get("commander_name_normalized")))
            fallback_primary = normalized_counts.most_common(1)[0][0] if normalized_counts else normalize_text(group[0].get("commander_name_normalized"))
            url_primary_blockers = commander_name_blockers(url_primary, url_primary, linked=True) if url_primary else ["empty_name"]
            primary = fallback_primary if (url_primary.startswith(":") or url_primary_blockers) else url_primary
            resolution_method = "linked_article"
        else:
            primary = normalize_text(group[0].get("commander_name_normalized"))
            resolution_method = "exact_cleaned_name"
        commander_id = f"cmd_{hashlib.sha1(key.encode('utf-8')).hexdigest()[:12]}"
        master_rows.append(
            {
                "commander_id": commander_id,
                "name_primary": primary,
                "name_variants": " | ".join(variants),
                "wikipedia_page": resolved_url,
                "birth_year": "",
                "death_year": "",
                "civilization_or_state": "",
                "era": "",
                "service_branch": "",
                "notes": f"engagement_rows={len(group)}",
                "identity_resolution_method": resolution_method,
            }
        )
    master_rows.sort(key=lambda row: normalize_text(row["name_primary"]).lower())
    return master_rows


def row_level_blockers(row: dict[str, str], battle_by_id: dict[str, dict[str, str]], link_meta: dict[str, dict[str, Any]]) -> list[str]:
    blockers: list[str] = []
    battle_id = normalize_text(row.get("battle_id"))
    battle = battle_by_id.get(battle_id)
    if not battle:
        return ["missing_battle_reference"]
    side = normalize_text(row.get("side"))
    if side not in VALID_SIDES:
        blockers.append("invalid_side")
        return blockers

    normalized_name = normalize_text(row.get("commander_name_normalized"))
    raw_name = normalize_text(row.get("commander_name_raw"))
    blockers.extend(commander_name_blockers(raw_name, normalized_name, linked=bool(normalize_text(row.get("commander_wikipedia_url")))))
    if normalize_text(row.get("battle_name")) != normalize_text(battle.get("battle_name")):
        blockers.append("battle_name_mismatch")
    if normalize_text(row.get("source_url")) != normalize_text(battle.get("source_url")):
        blockers.append("source_url_mismatch")
    if normalize_text(row.get("year")) != normalize_text(battle.get("year")):
        blockers.append("year_mismatch")
    expected_belligerent = battle_side_value(battle, "belligerent", side)
    if normalize_text(row.get("belligerent")) != expected_belligerent:
        blockers.append("belligerent_mismatch")
    expected_strength = battle_side_value(battle, "strength", side)
    if normalize_text(row.get("strength_side_raw")) != expected_strength:
        blockers.append("strength_side_mismatch")
    expected_casualties = battle_side_value(battle, "casualties", side)
    if normalize_text(row.get("casualties_side_raw")) != expected_casualties:
        blockers.append("casualties_side_mismatch")
    if normalize_text(row.get("battle_result_for_commander")) not in VALID_SIDE_RESULTS:
        blockers.append("invalid_side_result")
    if normalize_text(row.get("identity_confidence")) not in VALID_IDENTITY_CONFIDENCE:
        blockers.append("invalid_identity_confidence")
    if "validated_commander_source=" not in normalize_text(row.get("parse_notes")):
        blockers.append("missing_parse_notes_marker")
    wiki_url = normalize_text(row.get("commander_wikipedia_url"))
    if wiki_url:
        title = url_to_title(wiki_url)
        meta = link_meta.get(title)
        if meta and classify_commander_page(meta.get("title") or title, meta.get("categories", [])) == "nonperson":
            blockers.append("linked_page_nonperson")
    return sorted(set(blockers))


def master_level_blockers(row: dict[str, str], link_meta: dict[str, dict[str, Any]]) -> list[str]:
    blockers = commander_name_blockers(normalize_text(row.get("name_primary")), normalize_text(row.get("name_primary")), linked=bool(normalize_text(row.get("wikipedia_page"))))
    wiki_url = normalize_text(row.get("wikipedia_page"))
    if wiki_url:
        title = url_to_title(wiki_url)
        meta = link_meta.get(title)
        if meta and classify_commander_page(meta.get("title") or title, meta.get("categories", [])) == "nonperson":
            blockers.append("linked_page_nonperson")
    return sorted(set(blockers))


def cleanup_rules_text() -> str:
    return """# Commander Cleanup Rules

- Commander rows are rebuilt from the validated battle snapshot, not patched from the old commander CSV.
- Commander extraction uses Wikipedia infobox commander cells as the source of truth.
- A second conservative recovery pass may upgrade or recover linked commanders only when the retained page itself contains a page-local linked-person match for the side-cell commander text.
- Linked commander candidates are accepted only if the cleaned name passes strict person-name rules and the linked page is not classified as a non-person page.
- Unlinked commander candidates are accepted only when the raw segment itself passes strict person-name rules.
- Nickname-only quoted fragments, graphic/template artifacts, narrative text, and non-person entities are excluded from the main commander file.
- Ambiguous or rejected commander candidates are moved to quarantine instead of remaining in the main commander file.
- `commanders_master.csv` is built only from validated commander rows.
"""


def copy_battle_snapshot_files(src_dir: Path, dst_dir: Path) -> None:
    dst_dir.mkdir(parents=True, exist_ok=True)
    for name in [
        "battles_clean.csv",
        "battles_clean_quarantine.csv",
        "battles_clean_removed_false_positives.csv",
        "cleanup_actions.csv",
        "cleanup_summary.json",
        "CLEANUP_RULES.md",
    ]:
        src = src_dir / name
        if src.exists():
            (dst_dir / name).write_bytes(src.read_bytes())
    src_postfix = src_dir / "postfix_audit"
    dst_postfix = dst_dir / "postfix_audit"
    if src_postfix.exists():
        dst_postfix.mkdir(parents=True, exist_ok=True)
        for name in ["row_audit.csv", "summary.json"]:
            src = src_postfix / name
            if src.exists():
                (dst_postfix / name).write_bytes(src.read_bytes())


def fetch_link_metadata_for_titles(client: bdp.WikipediaClient, titles: list[str], chunk_size: int = 50) -> dict[str, dict[str, Any]]:
    unique_titles = sorted({normalize_text(title) for title in titles if normalize_text(title)})
    if not unique_titles:
        return {}
    return client.fetch_page_metadata_batch(unique_titles, chunk_size=chunk_size)


def summarize_reasons(rows: list[dict[str, str]], field: str) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for row in rows:
        for reason in split_pipe_values(row.get(field, "")):
            counts[reason] += 1
    return dict(counts.most_common())
