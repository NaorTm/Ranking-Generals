from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any
from urllib.parse import quote, unquote, urlparse

import pandas as pd

from battle_dataset_pipeline import normalize_result


CURRENT_YEAR = 2026
WIKIPEDIA_BASE = "https://en.wikipedia.org/wiki/"
EVENT_TITLE_KEYWORDS = {
    "battle",
    "siege",
    "war",
    "wars",
    "conflict",
    "campaign",
    "operation",
    "offensive",
    "raid",
    "skirmish",
    "massacre",
    "uprising",
    "rebellion",
    "revolt",
    "conquest",
    "expedition",
    "assault",
    "invasion",
    "theatre",
    "theater",
    "front",
    "mutiny",
    "engagement",
}
CONCEPT_TITLE_KEYWORDS = {
    "principles",
    "warfare",
    "observer force",
    "general command",
    "peacekeeping",
    "doctrine",
    "strategy",
    "tactics",
    "air assault",
    "political warfare",
}
GENERIC_NAME_PATTERNS = (
    "unknown",
    "various",
    "multiple commanders",
    "several commanders",
    "general",
    "major",
    "brigadier",
    "colonel",
    "lieutenant",
    "captain",
    "commander",
    "admiral",
)
ENTITY_STOPWORDS = {
    "and",
    "the",
    "of",
    "for",
    "in",
    "on",
    "at",
    "by",
    "with",
    "army",
    "armies",
    "force",
    "forces",
    "fleet",
    "fleets",
    "division",
    "divisions",
    "corps",
    "command",
    "front",
    "fronts",
    "coalition",
    "allies",
    "allied",
    "rebels",
    "insurgents",
    "government",
}
TOKEN_ALIAS_MAP = {
    "austria": {"austrian", "austro"},
    "britain": {"british", "anglo"},
    "china": {"chinese"},
    "denmark": {"danish", "dano"},
    "england": {"english", "anglo"},
    "france": {"french", "franco"},
    "germany": {"german"},
    "greece": {"greek"},
    "hungary": {"hungarian"},
    "india": {"indian"},
    "iran": {"iranian", "persian"},
    "ireland": {"irish"},
    "italy": {"italian", "italo"},
    "japan": {"japanese"},
    "mongolia": {"mongolian"},
    "netherlands": {"dutch"},
    "norway": {"norwegian"},
    "ottoman": {"turkish", "turco"},
    "persia": {"persian", "iranian"},
    "poland": {"polish", "polono"},
    "prussia": {"prussian", "prusso"},
    "rome": {"roman"},
    "russia": {"russian", "russo", "soviet"},
    "saxony": {"saxon", "saxo"},
    "serbia": {"serbian"},
    "sparta": {"spartan"},
    "spain": {"spanish"},
    "sweden": {"swedish"},
    "syria": {"syrian"},
    "turkey": {"turkish", "turco"},
    "ukraine": {"ukrainian"},
    "union": {"union"},
    "america": {"american"},
}
PHRASE_ALIAS_MAP = {
    "allied powers": {"allied", "allies"},
    "allied forces": {"allied", "allies"},
    "anti spartan": {"spartan"},
    "denmark norway": {"dano-norwegian", "dano norwegian", "danish-norwegian"},
    "first french empire": {"french"},
    "first french republic": {"french"},
    "great britain": {"british", "anglo-british", "anglo british"},
    "habsburg monarchy": {"austrian", "austro", "habsburg", "imperial"},
    "nazi germany": {"german", "nazi"},
    "ottoman empire": {"ottoman", "turkish", "turco"},
    "soviet union": {"soviet", "russian"},
    "swedish empire": {"swedish"},
    "tsardom of russia": {"russian", "russo"},
    "united kingdom": {"british", "anglo"},
    "united states": {"american"},
}
COALITION_HINT_TOKENS = {"coalition", "allied", "allies", "alliance", "combined"}
CANONICAL_MARKER_MAP: dict[str, set[str]] = {
    canonical: {canonical, *aliases} for canonical, aliases in TOKEN_ALIAS_MAP.items()
}
ALIAS_TO_CANONICALS: dict[str, set[str]] = {}
for canonical, aliases in TOKEN_ALIAS_MAP.items():
    for alias in aliases:
        ALIAS_TO_CANONICALS.setdefault(alias, set()).add(canonical)
NON_PERSON_COMMANDER_URL_TITLES = {
    "Manner_of_death",
    "Al-Masdar_News",
    "Wounded_in_action",
    "Newsweek",
    "Kommersant",
    "RBK_Group",
    "Rudaw_Media_Network",
    "Federal_Investigation_Agency",
    "CNA_(TV_network)",
    "Media_Trust",
    "Uganda_Radio_Network",
    "Hafiz_Gul_Bahadur_Group",
}
NON_PERSON_COMMANDER_NAMES = {
    "Manner of death",
    "Al-Masdar News",
    "Wounded in action",
    "Battle group",
}
NON_PERSON_COMMANDER_URL_PATTERNS = (
    r"^list_of_",
    r"(?:^|_)ministry(?:_|$)",
    r"(?:^|_)news(?:_|$)",
    r"(?:^|_)news_agency(?:_|$)",
    r"(?:^|_)tv_network(?:_|$)",
    r"(?:^|_)radio_network(?:_|$)",
    r"(?:^|_)media(?:_|$)",
    r"(?:^|_)media_network(?:_|$)",
    r"(?:^|_)mission(?:_|$)",
    r"(?:^|_)organization(?:_|$)",
    r"(?:^|_)commission(?:_|$)",
    r"(?:^|_)commissioner(?:_|$)",
    r"(?:^|_)agency(?:_|$)",
    r"(?:^|_)group(?:_|$)",
    r"(?:^|_)trust(?:_|$)",
    r"(?:^|_)publishing_group(?:_|$)",
    r"(?:^|_)crisis_group(?:_|$)",
    r"(?:^|_)service_group(?:_|$)",
    r"(?:^|_)support_mission(?:_|$)",
    r"(?:^|_)general_commission(?:_|$)",
    r"(?:^|_)times(?:_|$)",
    r"^tass$",
)
SUBJECT_RESULT_PAGE_TYPES = {"battle_article", "war_conflict_article", "campaign_article", "operation_article"}
TITLE_SIDE_EXCLUDE_TOKENS = {
    "world",
    "first",
    "second",
    "third",
    "fourth",
    "fifth",
    "civil",
    "independence",
    "campaign",
    "operation",
    "war",
    "wars",
    "conflict",
    "revolt",
    "rebellion",
    "revolution",
    "uprising",
    "coup",
    "offensive",
    "insurgency",
    "occupation",
    "expedition",
    "battle",
    "siege",
    "front",
    "the",
    "and",
    "of",
    "against",
    "during",
    "east",
    "west",
    "north",
    "south",
    "eastern",
    "western",
    "northern",
    "southern",
    "spring",
    "mandatory",
    "border",
    "battalion",
    "kingdom",
    "republic",
    "states",
    "state",
    "long",
    "area",
    "forces",
    "army",
    "united",
}
ALLIED_MARKER_HINTS = (
    "united states",
    "united kingdom",
    "british",
    "commonwealth",
    "australia",
    "canada",
    "new zealand",
    "soviet",
    "ussr",
    "nato",
    "poland",
    "free french",
)
GENERIC_ACTOR_RESULT_PATTERNS = (
    re.compile(r"^(?P<actor>.+?) intervention in .+$", re.I),
    re.compile(r"^(?P<actor>.+?) offensives?(?: \(.+\))?(?: into .+| in .+)?$", re.I),
    re.compile(r"^(?P<actor>(?!\d{3,4}\b).+?) campaigns? against .+$", re.I),
    re.compile(r"^(?P<actor>(?!\d{3,4}\b).+?) expedition(?:s)? to .+$", re.I),
    re.compile(r"^(?P<actor>(?!\d{3,4}\b).+?) invasion of .+$", re.I),
    re.compile(r"^(?P<actor>(?!\d{3,4}\b).+?) occupation of .+$", re.I),
    re.compile(r"^(?P<actor>(?!\d{3,4}\b).+?) landing at .+$", re.I),
)
NEUTRAL_OUTCOMES = {"indecisive", "draw", "stalemate", "disputed"}
PAGE_TYPE_WEIGHTS = {
    "battle_article": 1.0,
    "operation_article": 0.8,
    "campaign_article": 0.55,
    "war_conflict_article": 0.35,
}
OUTCOME_SCORE_MAPS = {
    "conservative": {
        "decisive_victory": 1.00,
        "victory": 0.75,
        "tactical_victory": 0.60,
        "pyrrhic_victory": 0.30,
        "indecisive": 0.00,
        "draw": 0.00,
        "stalemate": 0.00,
        "disputed": 0.00,
        "defeat": -0.75,
        "major_defeat": -1.00,
    },
    "balanced": {
        "decisive_victory": 1.00,
        "victory": 0.80,
        "tactical_victory": 0.65,
        "pyrrhic_victory": 0.25,
        "indecisive": 0.00,
        "draw": 0.00,
        "stalemate": -0.05,
        "disputed": -0.10,
        "defeat": -0.80,
        "major_defeat": -1.00,
    },
    "aggressive": {
        "decisive_victory": 1.20,
        "victory": 1.00,
        "tactical_victory": 0.80,
        "pyrrhic_victory": 0.10,
        "indecisive": -0.10,
        "draw": -0.10,
        "stalemate": -0.20,
        "disputed": -0.25,
        "defeat": -1.00,
        "major_defeat": -1.25,
    },
}


def normalize_space(value: Any) -> str:
    if value is None:
        return ""
    if pd.isna(value):
        return ""
    value = str(value)
    value = re.sub(r"\[\d+\]", "", value)
    value = value.replace("\xa0", " ")
    return re.sub(r"\s+", " ", value).strip()


def slugify(value: str) -> str:
    value = normalize_space(unquote(value).replace("_", " "))
    value = unicodedata.normalize("NFKC", value)
    value = value.replace("–", "-").replace("—", "-").replace("−", "-")
    value = re.sub(r"[^\w\s-]", "", value, flags=re.UNICODE)
    return re.sub(r"[-\s]+", "-", value.lower()).strip("-")


def clean_name(raw_name: str) -> str:
    name = normalize_space(raw_name)
    name = unicodedata.normalize("NFKC", name)
    name = re.sub(r"\([^)]*\)", "", name)
    name = re.sub(r"\[[^\]]+\]", "", name)
    name = re.sub(r"[†‡#*?]+", "", name)
    name = re.sub(r"\b(c\.|ca\.)\b", "", name, flags=re.I)
    return normalize_space(name)


def normalize_title(value: str) -> str:
    title = normalize_space(value)
    title = unicodedata.normalize("NFKC", title)
    return title.replace("–", "-").replace("—", "-").replace("−", "-")


def sanitize_result_text_for_scoring(result_raw: str) -> str:
    text = normalize_title(result_raw)
    if not text:
        return ""
    # Repair citation-fused result strings like "Roman victoryDaryaee 2010".
    text = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", text)
    text = re.sub(r"(?<=[A-Za-z])(?=\d)", " ", text)
    text = re.sub(r"(?<=\d)(?=[A-Za-z])", " ", text)
    return normalize_space(text)


def scoring_specific_result_override(result_raw: str) -> tuple[str, str]:
    text = normalize_space(result_raw).lower()
    if not text:
        return "", ""
    if "allied operational success" in text:
        return "Tactical Victory", "tactical_victory"
    if "allied partial success" in text:
        return "Tactical Victory", "tactical_victory"
    if "allied occupation" in text:
        return "Tactical Victory", "tactical_victory"
    return "", ""


def derive_scoring_result_fields(result_raw: str, result_normalized: str, result_type: str) -> tuple[str, str, str, str]:
    raw = normalize_title(result_raw)
    normalized = normalize_space(result_normalized)
    rtype = normalize_space(result_type).lower()
    if rtype and rtype != "unknown":
        return raw, normalized, rtype, "stored"

    sanitized_raw = sanitize_result_text_for_scoring(raw)
    sanitized_normalized, sanitized_type = normalize_result(sanitized_raw)
    sanitized_type = normalize_space(sanitized_type).lower()
    sanitized_normalized = normalize_space(sanitized_normalized)
    if sanitized_type and sanitized_type != "unknown":
        return sanitized_raw, sanitized_normalized, sanitized_type, "sanitized_result_raw"
    override_normalized, override_type = scoring_specific_result_override(sanitized_raw or raw)
    if override_type:
        return sanitized_raw or raw, override_normalized, override_type, "scoring_specific_override"
    fallback_normalized = normalized if normalized else ("Unknown" if raw else "")
    fallback_type = rtype if rtype else ("unknown" if raw else "")
    return raw, fallback_normalized, fallback_type, "stored_unknown"


def parse_float(value: Any) -> float | None:
    value = normalize_space(value)
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def canonicalize_wikipedia_url(url: str) -> str:
    url = normalize_space(url)
    if not url:
        return ""
    parsed = urlparse(url)
    path = parsed.path.rstrip("/")
    if "/wiki/" not in path:
        return url
    title = path.split("/wiki/", 1)[1]
    title = normalize_title(unquote(title)).replace(" ", "_")
    return f"{WIKIPEDIA_BASE}{quote(title, safe=':_()/-')}"


def wikipedia_title_from_url(url: str) -> str:
    canonical = canonicalize_wikipedia_url(url)
    if not canonical or "/wiki/" not in canonical:
        return ""
    title = canonical.split("/wiki/", 1)[1]
    return normalize_title(unquote(title).replace("_", " "))


def make_id(prefix: str, key: str) -> str:
    digest = hashlib.sha1(key.encode("utf-8")).hexdigest()[:12]
    return f"{prefix}_{digest}"


def join_flags(flags: list[str]) -> str:
    return " | ".join(sorted(dict.fromkeys(flag for flag in flags if flag)))


def is_non_person_commander_link(name: str, canonical_url: str) -> bool:
    cleaned_name = clean_name(name)
    lowered_name = cleaned_name.lower()
    if cleaned_name in NON_PERSON_COMMANDER_NAMES:
        return True
    if lowered_name.startswith("commissioner "):
        return True
    url_title = wikipedia_title_from_url(canonical_url).replace(" ", "_")
    if not url_title:
        return False
    if url_title in NON_PERSON_COMMANDER_URL_TITLES:
        return True
    lowered = url_title.lower()
    return any(re.search(pattern, lowered) is not None for pattern in NON_PERSON_COMMANDER_URL_PATTERNS)


def is_suspect_identity(name: str, canonical_url: str) -> bool:
    lower = clean_name(name).lower()
    if not lower:
        return True
    if len(lower) > 90:
        return True
    if ".svg" in lower or "flag of" in lower or "naval jack" in lower:
        return True
    if any(pattern == lower for pattern in GENERIC_NAME_PATTERNS):
        return True
    if lower.count(",") > 5:
        return True
    url_title = wikipedia_title_from_url(canonical_url).lower()
    if url_title and any(url_title == pattern for pattern in GENERIC_NAME_PATTERNS):
        return True
    return False


def title_has_event_keywords(title: str) -> bool:
    lower = normalize_space(title).lower()
    return any(keyword in lower for keyword in EVENT_TITLE_KEYWORDS)


def title_has_concept_keywords(title: str) -> bool:
    lower = normalize_space(title).lower()
    return any(keyword in lower for keyword in CONCEPT_TITLE_KEYWORDS)


def normalize_conflict_key(war_name: str, battle_name: str) -> str:
    basis = war_name if normalize_space(war_name) else battle_name
    return slugify(normalize_title(basis))


def title_year_hint(battle_name: str) -> int | None:
    title = normalize_title(battle_name)
    match = re.search(r"\((\d{3,4})\)", title)
    if not match:
        return None
    value = int(match.group(1))
    if 1 <= value <= CURRENT_YEAR + 1:
        return value
    return None


def infer_analytic_year(battle_name: str, date_raw: str, parsed_year_raw: str) -> tuple[str, str]:
    date_raw = normalize_title(date_raw)
    title_hint = title_year_hint(battle_name)
    parsed_year = parse_float(parsed_year_raw)
    if re.search(r"\b(\d{1,4})\s*(BC|BCE)\b", date_raw, re.I):
        match = re.search(r"\b(\d{1,4})\s*(BC|BCE)\b", date_raw, re.I)
        return str(-int(match.group(1))), "high"
    if re.search(r"\b(AD|CE)\s*(\d{1,4})\b", date_raw, re.I):
        match = re.search(r"\b(AD|CE)\s*(\d{1,4})\b", date_raw, re.I)
        return str(int(match.group(2))), "high"
    if re.search(r"\b(\d{1,4})\s*(AD|CE)\b", date_raw, re.I):
        match = re.search(r"\b(\d{1,4})\s*(AD|CE)\b", date_raw, re.I)
        return str(int(match.group(1))), "high"
    if title_hint is not None and parsed_year is not None and abs(parsed_year - title_hint) >= 50:
        return str(title_hint), "title_year_override"
    if parsed_year is not None and -5000 <= parsed_year <= CURRENT_YEAR + 1:
        return str(int(parsed_year)), "medium"

    year_candidates = [int(match) for match in re.findall(r"\b\d{1,4}\b", date_raw)]
    plausible_modern = [value for value in year_candidates if 1 <= value <= CURRENT_YEAR + 1]
    if title_hint is not None and plausible_modern:
        plausible_near_title = [value for value in plausible_modern if abs(value - title_hint) <= 5]
        if plausible_near_title:
            return str(plausible_near_title[-1]), "low"
        if all(abs(value - title_hint) >= 50 for value in plausible_modern):
            return str(title_hint), "title_year_override"
    if plausible_modern:
        return str(plausible_modern[-1]), "low"
    if title_hint is not None:
        return str(title_hint), "title_year_fallback"
    if parsed_year is not None:
        return "", "low"
    return "", "low"


def era_bucket_for_year(year_raw: str) -> str:
    if not year_raw:
        return "unknown"
    year = int(year_raw)
    if year <= 500:
        return "ancient"
    if year <= 1500:
        return "medieval"
    if year <= 1788:
        return "early_modern"
    if year <= 1815:
        return "revolutionary_napoleonic"
    if year <= 1913:
        return "long_nineteenth_century"
    if year <= 1945:
        return "world_wars"
    if year <= 1991:
        return "cold_war"
    return "contemporary"


def clean_belligerent_segment(value: str) -> str:
    value = normalize_title(value)
    value = re.sub(r"\b\w+\.svg\b", "", value, flags=re.I)
    value = re.sub(r"\b\d+px\b", "", value, flags=re.I)
    value = re.sub(r"\([^)]*\)", "", value)
    value = re.sub(r"['\"“”‘’]", "", value)
    return normalize_space(value)


def extract_belligerent_entities(raw_value: str) -> list[str]:
    if not normalize_space(raw_value):
        return []
    pieces = re.split(r"[\n|;/]+", str(raw_value))
    entities: list[str] = []
    seen: set[str] = set()
    for piece in pieces:
        entity = clean_belligerent_segment(piece)
        if not entity:
            continue
        key = slugify(entity)
        if not key or key in seen or key in ENTITY_STOPWORDS:
            continue
        seen.add(key)
        entities.append(entity)
    return entities


def extract_match_tokens(raw_value: str) -> list[str]:
    tokens: list[str] = []
    seen: set[str] = set()
    for entity in extract_belligerent_entities(raw_value):
        lowered = re.sub(r"[^a-z0-9\s-]", " ", entity.lower())
        lowered = normalize_space(lowered)
        lowered_spaces = lowered.replace("-", " ")
        candidates: set[str] = set()
        if len(lowered) >= 4:
            candidates.add(lowered)
        if len(lowered_spaces) >= 4:
            candidates.add(lowered_spaces)

        split_tokens = [
            token
            for token in re.split(r"[\s-]+", lowered_spaces)
            if len(token) >= 4 and token not in ENTITY_STOPWORDS
        ]
        candidates.update(split_tokens)

        for phrase, aliases in PHRASE_ALIAS_MAP.items():
            if phrase in lowered_spaces:
                candidates.update(aliases)
        for token in split_tokens:
            candidates.update(TOKEN_ALIAS_MAP.get(token, set()))

        if "denmark" in split_tokens and "norway" in split_tokens:
            candidates.update({"dano-norwegian", "dano norwegian", "danish-norwegian"})

        for candidate in candidates:
            normalized = normalize_space(candidate.lower())
            if len(normalized) < 4 or normalized in seen:
                continue
            seen.add(normalized)
            tokens.append(normalized)
    return tokens


def contains_result_token(text: str, token: str) -> bool:
    token = normalize_space(token.lower())
    if not token:
        return False
    pattern = rf"(?<![a-z0-9]){re.escape(token)}(?![a-z0-9])"
    return re.search(pattern, text) is not None


def contains_negative_target(text: str, token: str) -> bool:
    token = normalize_space(token.lower())
    if not token:
        return False
    patterns = [
        rf"anti[-\s]+{re.escape(token)}(?![a-z0-9])",
        rf"against\s+{re.escape(token)}(?![a-z0-9])",
    ]
    return any(re.search(pattern, text) is not None for pattern in patterns)


def first_token_position(text: str, token: str) -> int | None:
    token = normalize_space(token.lower())
    if not token:
        return None
    pattern = rf"(?<![a-z0-9]){re.escape(token)}(?![a-z0-9])"
    match = re.search(pattern, text)
    return match.start() if match else None


def extract_negative_target_tokens(text: str) -> list[str]:
    text = normalize_space(text.lower())
    if not text:
        return []
    targets: list[str] = []
    seen: set[str] = set()
    for match in re.finditer(r"(?:anti[-\s]+|against\s+)([a-z][a-z\s-]{2,60})", text):
        phrase = match.group(1)
        phrase = re.split(
            r"\b(coalition|allied|allies|alliance|victory|defeat|forces?|troops?|campaign|war)\b",
            phrase,
            maxsplit=1,
        )[0]
        phrase = normalize_space(phrase.strip(" -"))
        if not phrase:
            continue
        candidates: set[str] = {phrase}
        split_tokens = [
            token
            for token in re.split(r"[\s-]+", phrase)
            if len(token) >= 3 and token not in ENTITY_STOPWORDS
        ]
        candidates.update(split_tokens)
        for token in split_tokens:
            candidates.update(TOKEN_ALIAS_MAP.get(token, set()))
        for source_phrase, aliases in PHRASE_ALIAS_MAP.items():
            if source_phrase in phrase:
                candidates.update(aliases)
        for candidate in candidates:
            normalized = normalize_space(candidate)
            if len(normalized) < 3 or normalized in seen:
                continue
            seen.add(normalized)
            targets.append(normalized)
    return targets


def canonical_marker_hits(raw_value: str) -> set[str]:
    text = normalize_space(raw_value).lower()
    if not text:
        return set()
    hits: set[str] = set()
    for canonical, markers in CANONICAL_MARKER_MAP.items():
        if any(contains_result_token(text, marker) for marker in markers):
            hits.add(canonical)
    return hits


def infer_negated_loser_side(result_raw: str, side_to_raws: dict[str, list[str]]) -> str:
    result_lower = normalize_space(result_raw).lower()
    target_tokens = extract_negative_target_tokens(result_lower)
    if not target_tokens:
        return ""
    side_hits: list[tuple[str, int, int]] = []
    for side, raw_values in side_to_raws.items():
        positions: list[int] = []
        hit_count = 0
        for raw_value in raw_values:
            raw_lower = normalize_space(raw_value).lower()
            if not raw_lower:
                continue
            matched_positions = [first_token_position(raw_lower, token) for token in target_tokens]
            matched_positions = [position for position in matched_positions if position is not None]
            positions.extend(matched_positions)
            hit_count += len(matched_positions)
        positions = [position for position in positions if position is not None]
        if positions:
            side_hits.append((side, min(positions), hit_count))
    if not side_hits:
        return ""
    side_hits.sort(key=lambda item: (item[1], -item[2], item[0]))
    if len(side_hits) == 1:
        return side_hits[0][0]
    best_side, best_pos, best_hit_count = side_hits[0]
    _, second_pos, second_hit_count = side_hits[1]
    if best_pos + 20 <= second_pos:
        return best_side
    if best_pos < second_pos and best_hit_count >= second_hit_count:
        return best_side
    return ""


def side_is_coalition(raw_value: str) -> bool:
    text = normalize_space(raw_value).lower()
    entity_count = len(extract_belligerent_entities(raw_value))
    canonical_count = len(canonical_marker_hits(raw_value))
    return (
        entity_count >= 2
        or canonical_count >= 2
        or "*" in text
        or any(token in text for token in COALITION_HINT_TOKENS)
    )


def coalition_signal_score(raw_value: str) -> int:
    text = normalize_space(raw_value).lower()
    explicit_tokens = sum(1 for token in COALITION_HINT_TOKENS if token in text)
    return explicit_tokens * 4 + len(extract_belligerent_entities(raw_value)) + len(canonical_marker_hits(raw_value))


def allied_marker_score(raw_value: str) -> int:
    text = normalize_space(raw_value).lower()
    return sum(1 for token in ALLIED_MARKER_HINTS if token in text)


def infer_allied_marker_winner_side(result_raw: str, side_to_raw: dict[str, str]) -> str:
    result_lower = normalize_space(result_raw).lower()
    if "allied" not in result_lower and "coalition" not in result_lower:
        return ""
    scores = {
        side: allied_marker_score(raw_value)
        for side, raw_value in side_to_raw.items()
        if normalize_space(raw_value)
    }
    ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    if not ranked or ranked[0][1] <= 0:
        return ""
    if len(ranked) == 1 or ranked[1][1] == 0:
        return ranked[0][0]
    return ""


def generic_actor_title_subject(title: str) -> str:
    normalized = normalize_title(title)
    for pattern in GENERIC_ACTOR_RESULT_PATTERNS:
        match = pattern.match(normalized)
        if not match:
            continue
        actor = normalize_space(re.sub(r"^\d{3,4}\s+", "", match.group("actor")))
        if actor:
            return actor
    return ""


def actor_subject_side_matches(actor_subject: str, raw_value: str) -> bool:
    actor_norm = normalize_title(actor_subject).lower()
    raw_norm = normalize_title(raw_value).lower()
    if not actor_norm or not raw_norm:
        return False
    if actor_norm in raw_norm:
        return True
    actor_tokens = [
        token
        for token in re.split(r"[^a-z0-9]+", actor_norm)
        if len(token) >= 4 and not token.isdigit() and token not in TITLE_SIDE_EXCLUDE_TOKENS
    ]
    if not actor_tokens:
        return False
    side_tokens = set(extract_match_tokens(raw_value))
    for token in actor_tokens:
        for canonical in ALIAS_TO_CANONICALS.get(token, set()):
            if canonical in side_tokens:
                return True
    return False


def infer_actor_led_generic_winner_side(result_raw: str, battle_row: pd.Series) -> tuple[str, str]:
    page_type = normalize_space(battle_row.get("page_type", ""))
    if page_type not in SUBJECT_RESULT_PAGE_TYPES:
        return "", "unresolved"
    actor_subject = generic_actor_title_subject(battle_row.get("battle_name", "") or battle_row.get("wikipedia_title", ""))
    if not actor_subject:
        return "", "unresolved"
    side_to_raw = {
        "side_a": battle_row.get("belligerent_1_raw", ""),
        "side_b": battle_row.get("belligerent_2_raw", ""),
        "side_c": battle_row.get("belligerent_3_raw", ""),
    }
    populated_sides = [side for side, raw_value in side_to_raw.items() if normalize_space(raw_value)]
    actor_norm = normalize_title(actor_subject).lower()
    exact_sides = [
        side
        for side in populated_sides
        if actor_norm and actor_norm in normalize_title(side_to_raw[side]).lower()
    ]
    if len(exact_sides) == 1:
        matched_sides = exact_sides
    else:
        matched_sides = [side for side in populated_sides if actor_subject_side_matches(actor_subject, side_to_raw[side])]
    if len(matched_sides) != 1:
        return "", "unresolved"
    winner_side = matched_sides[0]
    result_lower = normalize_space(result_raw).lower()
    if result_lower == "victory":
        return winner_side, "generic_actor_title_match"
    if result_lower == "defeat":
        other_sides = [side for side in populated_sides if side != winner_side]
        if len(other_sides) == 1:
            return other_sides[0], "generic_actor_title_match"
    return "", "unresolved"


def subject_result_title_tokens(title: str) -> set[str]:
    normalized = normalize_title(title).lower()
    tokens = {
        token
        for token in re.split(r"[^a-z0-9]+", normalized)
        if len(token) >= 4 and not token.isdigit() and token not in TITLE_SIDE_EXCLUDE_TOKENS
    }
    return tokens


def infer_subject_side_from_title(battle_row: pd.Series) -> tuple[str, str]:
    if normalize_space(battle_row.get("page_type", "")) not in SUBJECT_RESULT_PAGE_TYPES:
        return "", "unresolved"
    title_tokens = subject_result_title_tokens(battle_row.get("battle_name", "") or battle_row.get("wikipedia_title", ""))
    if not title_tokens:
        return "", "unresolved"
    hit_map: dict[str, list[str]] = {}
    for side, field in (
        ("side_a", "belligerent_1_raw"),
        ("side_b", "belligerent_2_raw"),
        ("side_c", "belligerent_3_raw"),
    ):
        raw_value = normalize_space(battle_row.get(field, "")).lower()
        if not raw_value:
            continue
        side_tokens = set(extract_match_tokens(raw_value))
        side_tokens.update(
            token
            for token in re.split(r"[^a-z0-9]+", raw_value)
            if len(token) >= 4 and not token.isdigit()
        )
        hit_map[side] = sorted(title_tokens & side_tokens)
    ranked = sorted(
        ((side, len(tokens)) for side, tokens in hit_map.items()),
        key=lambda item: (-item[1], item[0]),
    )
    if not ranked or ranked[0][1] < 2:
        return "", "unresolved"
    if len(ranked) > 1 and ranked[0][1] < ranked[1][1] + 1:
        return "", "unresolved"
    return ranked[0][0], "subject_title_match"


def infer_winner_side(result_raw: str, result_type: str, battle_row: pd.Series) -> tuple[str, str]:
    result_lower = normalize_space(result_raw).lower()
    if not result_lower or result_type in ("", "unknown") or result_type in NEUTRAL_OUTCOMES:
        return "", "unresolved"
    side_to_raw = {
        "side_a": battle_row.get("belligerent_1_raw", ""),
        "side_b": battle_row.get("belligerent_2_raw", ""),
        "side_c": battle_row.get("belligerent_3_raw", ""),
    }
    side_to_supporting_raws = {
        "side_a": [battle_row.get("belligerent_1_raw", ""), battle_row.get("commander_side_a_raw", "")],
        "side_b": [battle_row.get("belligerent_2_raw", ""), battle_row.get("commander_side_b_raw", "")],
        "side_c": [battle_row.get("belligerent_3_raw", ""), battle_row.get("commander_side_c_raw", "")],
    }
    populated_sides = [side for side, raw_value in side_to_raw.items() if normalize_space(raw_value)]
    direct_loser_side = infer_negated_loser_side(result_lower, side_to_supporting_raws)
    if direct_loser_side:
        other_sides = [side for side in populated_sides if side != direct_loser_side]
        if len(other_sides) == 1:
            return other_sides[0], "negated_target_match"
        coalition_sides = [side for side in other_sides if side_is_coalition(side_to_raw[side])]
        if len(coalition_sides) == 1:
            return coalition_sides[0], "negated_target_match"
    allied_marker_side = infer_allied_marker_winner_side(result_raw, side_to_raw)
    if allied_marker_side:
        return allied_marker_side, "allied_marker_match"
    matched_sides: list[str] = []
    negated_sides: list[str] = []
    for side, raw_values in side_to_supporting_raws.items():
        side_tokens: list[str] = []
        for raw_value in raw_values:
            side_tokens.extend(extract_match_tokens(raw_value))
        side_tokens = sorted(dict.fromkeys(side_tokens))
        if any(contains_negative_target(result_lower, token) for token in side_tokens):
            negated_sides.append(side)
        if any(contains_result_token(result_lower, token) for token in side_tokens):
            matched_sides.append(side)
    matched_sides = sorted(dict.fromkeys(matched_sides))
    negated_sides = sorted(dict.fromkeys(negated_sides))

    if len(negated_sides) == 1:
        loser_side = negated_sides[0]
        other_sides = [side for side in populated_sides if side != loser_side]
        if len(other_sides) == 1:
            return other_sides[0], "negated_target_match"
        positive_other_sides = [side for side in matched_sides if side != loser_side]
        if len(positive_other_sides) == 1:
            return positive_other_sides[0], "negated_target_match"
        coalition_sides = [side for side in other_sides if side_is_coalition(side_to_raw[side])]
        if len(coalition_sides) == 1:
            return coalition_sides[0], "negated_target_match"
        return "", "unresolved"

    if len(matched_sides) == 1:
        return matched_sides[0], "unique_belligerent_match"

    if result_lower in {"victory", "defeat"}:
        generic_actor_side, generic_actor_method = infer_actor_led_generic_winner_side(result_raw, battle_row)
        if generic_actor_side:
            return generic_actor_side, generic_actor_method

    if any(token in result_lower for token in COALITION_HINT_TOKENS):
        direct_coalition_sides = [
            side
            for side in populated_sides
            if any(token in normalize_space(side_to_raw[side]).lower() for token in COALITION_HINT_TOKENS)
        ]
        if len(direct_coalition_sides) == 1:
            return direct_coalition_sides[0], "coalition_label_match"
        coalition_sides = [side for side in populated_sides if side_is_coalition(side_to_raw[side])]
        if len(coalition_sides) == 1:
            return coalition_sides[0], "coalition_side_heuristic"
        coalition_scores = {
            side: coalition_signal_score(side_to_raw[side])
            for side in populated_sides
        }
        ranked_scores = sorted(coalition_scores.items(), key=lambda item: (-item[1], item[0]))
        if len(ranked_scores) >= 2:
            if ranked_scores[0][1] >= ranked_scores[1][1] + 2:
                return ranked_scores[0][0], "coalition_strength_heuristic"
        elif len(ranked_scores) == 1 and ranked_scores[0][1] > 0:
            return ranked_scores[0][0], "coalition_strength_heuristic"

    return "", "unresolved"


def derive_outcome_category(
    battle_result_for_commander: str,
    result_type: str,
    result_raw: str,
    side: str,
    battle_row: pd.Series,
) -> tuple[str, str, str]:
    explicit = normalize_space(battle_result_for_commander).lower()
    result_type = normalize_space(result_type).lower()

    if explicit in NEUTRAL_OUTCOMES:
        return explicit, "explicit_commander_side_result", "high"
    if explicit == "victory":
        if result_type in {"decisive_victory", "tactical_victory", "pyrrhic_victory"}:
            return result_type, "explicit_commander_side_result", "high"
        return "victory", "explicit_commander_side_result", "high"
    if explicit == "defeat":
        if result_type == "decisive_victory":
            return "major_defeat", "explicit_commander_side_result", "high"
        return "defeat", "explicit_commander_side_result", "high"

    if result_type in NEUTRAL_OUTCOMES:
        return result_type, "neutral_page_result", "high"

    winner_side, winner_side_method = infer_winner_side(result_raw, result_type, battle_row)
    if winner_side:
        if side == winner_side:
            if result_type in {"decisive_victory", "tactical_victory", "pyrrhic_victory"}:
                return result_type, f"inferred_{winner_side_method}", "medium"
            return "victory", f"inferred_{winner_side_method}", "medium"
        if result_type == "decisive_victory":
            return "major_defeat", f"inferred_{winner_side_method}", "medium"
        return "defeat", f"inferred_{winner_side_method}", "medium"

    return "unknown", "unknown", "low"


def safe_mean(values: list[float]) -> str:
    if not values:
        return ""
    return f"{sum(values) / len(values):.6f}"


def safe_variance(values: list[float]) -> str:
    if len(values) < 2:
        return ""
    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / len(values)
    return f"{variance:.6f}"


def outcome_reliability_band(known_count: int) -> str:
    if known_count >= 10:
        return "high"
    if known_count >= 5:
        return "medium"
    if known_count >= 1:
        return "low"
    return "insufficient"


def write_csv(path: Path, frame: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, encoding="utf-8-sig", quoting=csv.QUOTE_MINIMAL)


def apply_battle_verification_overrides(output_root: Path, eligibility: pd.DataFrame) -> pd.DataFrame:
    override_path = output_root / "verification" / "verified_battle_eligibility.csv"
    eligibility = eligibility.copy()
    eligibility["verification_status"] = "unverified"
    eligibility["verification_issue_flags"] = ""
    eligibility["strict_gate_pre_verification"] = eligibility["strict_gate_include"]
    eligibility["balanced_gate_pre_verification"] = eligibility["balanced_gate_include"]
    if not override_path.exists():
        return eligibility

    overrides = pd.read_csv(override_path, dtype=str).fillna("")
    merged = eligibility.merge(
        overrides[
            [
                "battle_id",
                "verification_status",
                "verification_issue_flags",
                "strict_gate_override",
                "balanced_gate_override",
            ]
        ],
        on="battle_id",
        how="left",
        suffixes=("", "_verification"),
    )
    merged["verification_status"] = merged["verification_status_verification"].where(
        merged["verification_status_verification"].ne(""),
        merged["verification_status"],
    )
    merged["verification_issue_flags"] = merged["verification_issue_flags_verification"].where(
        merged["verification_issue_flags_verification"].ne(""),
        merged["verification_issue_flags"],
    )
    merged.loc[merged["strict_gate_override"].ne(""), "strict_gate_include"] = merged.loc[
        merged["strict_gate_override"].ne(""), "strict_gate_override"
    ]
    merged.loc[merged["balanced_gate_override"].ne(""), "balanced_gate_include"] = merged.loc[
        merged["balanced_gate_override"].ne(""), "balanced_gate_override"
    ]
    merged["exclude_reason_flags"] = merged.apply(
        lambda row: join_flags([normalize_space(row["exclude_reason_flags"]), normalize_space(row["verification_issue_flags"])]),
        axis=1,
    )
    return merged.drop(
        columns=[
            "verification_status_verification",
            "verification_issue_flags_verification",
            "strict_gate_override",
            "balanced_gate_override",
        ],
        errors="ignore",
    )


def apply_commander_verification_overrides(output_root: Path, annotated: pd.DataFrame) -> pd.DataFrame:
    override_path = output_root / "verification" / "verified_commander_ranking_eligibility.csv"
    annotated = annotated.copy()
    annotated["verification_status"] = "unverified"
    annotated["verification_issue_flags"] = ""
    annotated["recommended_action"] = ""
    annotated["eligible_strict_pre_verification"] = annotated["eligible_strict"]
    annotated["eligible_balanced_pre_verification"] = annotated["eligible_balanced"]
    if not override_path.exists():
        return annotated

    overrides = pd.read_csv(override_path, dtype=str).fillna("")
    merged = annotated.merge(
        overrides[
            [
                "analytic_commander_id",
                "battle_id",
                "verification_status",
                "verification_issue_flags",
                "recommended_action",
                "strict_include_override",
                "balanced_include_override",
            ]
        ],
        on=["analytic_commander_id", "battle_id"],
        how="left",
        suffixes=("", "_verification"),
    )
    merged["verification_status"] = merged["verification_status_verification"].where(
        merged["verification_status_verification"].ne(""),
        merged["verification_status"],
    )
    merged["verification_issue_flags"] = merged["verification_issue_flags_verification"].where(
        merged["verification_issue_flags_verification"].ne(""),
        merged["verification_issue_flags"],
    )
    merged["recommended_action"] = merged["recommended_action_verification"].where(
        merged["recommended_action_verification"].ne(""),
        merged["recommended_action"],
    )
    merged.loc[merged["strict_include_override"].ne(""), "eligible_strict"] = merged.loc[
        merged["strict_include_override"].ne(""), "strict_include_override"
    ]
    merged.loc[merged["balanced_include_override"].ne(""), "eligible_balanced"] = merged.loc[
        merged["balanced_include_override"].ne(""), "balanced_include_override"
    ]
    merged["exclude_reason_flags"] = merged.apply(
        lambda row: join_flags([normalize_space(row["exclude_reason_flags"]), normalize_space(row["verification_issue_flags"])]),
        axis=1,
    )
    return merged.drop(
        columns=[
            "verification_status_verification",
            "verification_issue_flags_verification",
            "recommended_action_verification",
            "strict_include_override",
            "balanced_include_override",
        ],
        errors="ignore",
    )


def apply_commander_outcome_overrides(output_root: Path, annotated: pd.DataFrame) -> pd.DataFrame:
    override_path = output_root / "verification" / "verified_outcome_overrides.csv"
    annotated = annotated.copy()
    annotated["outcome_category_pre_override"] = annotated["outcome_category"]
    annotated["outcome_inference_method_pre_override"] = annotated["outcome_inference_method"]
    annotated["outcome_inference_confidence_pre_override"] = annotated["outcome_inference_confidence"]
    annotated["outcome_override_applied"] = "0"
    annotated["outcome_override_justification"] = ""
    annotated["outcome_override_evidence_basis"] = ""
    if not override_path.exists():
        return annotated

    overrides = pd.read_csv(override_path, dtype=str).fillna("")
    merged = annotated.merge(
        overrides[
            [
                "analytic_commander_id",
                "battle_id",
                "new_outcome_category",
                "override_justification",
                "override_evidence_basis",
            ]
        ],
        on=["analytic_commander_id", "battle_id"],
        how="left",
    )
    merged["new_outcome_category"] = merged["new_outcome_category"].fillna("")
    merged["override_justification"] = merged["override_justification"].fillna("")
    merged["override_evidence_basis"] = merged["override_evidence_basis"].fillna("")
    override_mask = merged["new_outcome_category"].ne("")
    merged.loc[override_mask, "outcome_category"] = merged.loc[override_mask, "new_outcome_category"]
    merged.loc[override_mask, "outcome_inference_method"] = "verification_outcome_override"
    merged.loc[override_mask, "outcome_inference_confidence"] = "high"
    merged.loc[override_mask, "outcome_override_applied"] = "1"
    merged.loc[override_mask, "outcome_override_justification"] = merged.loc[
        override_mask, "override_justification"
    ]
    merged.loc[override_mask, "outcome_override_evidence_basis"] = merged.loc[
        override_mask, "override_evidence_basis"
    ]
    return merged.drop(
        columns=[
            "new_outcome_category",
            "override_justification",
            "override_evidence_basis",
        ],
        errors="ignore",
    )


def apply_split_outcome_credit(annotated: pd.DataFrame) -> pd.DataFrame:
    annotated = annotated.copy()
    valid_side_mask = annotated["side"].isin(["side_a", "side_b", "side_c", "side_d"])
    known_outcome_mask = annotated["outcome_category"].ne("unknown")
    same_side_counts = (
        annotated.loc[valid_side_mask]
        .groupby(["battle_id", "side"])
        .size()
        .to_dict()
    )
    known_side_counts = (
        annotated.loc[valid_side_mask & known_outcome_mask]
        .groupby(["battle_id", "side"])
        .size()
        .to_dict()
    )

    same_side_count_values: list[str] = []
    known_side_count_values: list[str] = []
    outcome_credit_fractions: list[str] = []
    for row in annotated.to_dict(orient="records"):
        key = (row["battle_id"], row["side"])
        if row["side"] in {"side_a", "side_b", "side_c", "side_d"}:
            side_count = max(same_side_counts.get(key, 1), 1)
            known_side_count = known_side_counts.get(key, 0)
            same_side_count_values.append(str(side_count))
            known_side_count_values.append(str(known_side_count))
            if row["outcome_category"] != "unknown" and known_side_count > 0:
                outcome_credit_fractions.append(f"{1.0 / math.sqrt(known_side_count):.6f}")
            else:
                outcome_credit_fractions.append("0.000000")
        else:
            same_side_count_values.append("0")
            known_side_count_values.append("0")
            outcome_credit_fractions.append("0.000000")

    annotated["same_side_commander_count"] = same_side_count_values
    annotated["same_side_known_outcome_count"] = known_side_count_values
    annotated["outcome_credit_fraction"] = outcome_credit_fractions
    annotated["outcome_credit_rule"] = "sqrt_known_same_side_split"
    return annotated


def apply_page_weights(annotated: pd.DataFrame) -> pd.DataFrame:
    annotated = annotated.copy()
    battle_presence_by_overlap = (
        annotated.loc[
            (annotated["page_type"].eq("battle_article"))
            & (annotated["eligible_strict"].eq("1"))
        ]
        .groupby(["analytic_commander_id", "hierarchy_overlap_key"])
        .size()
        .to_dict()
    )

    overlap_penalties: list[str] = []
    model_a_weights: list[str] = []
    model_b_weights: list[str] = []
    model_c_weights: list[str] = []
    for row in annotated.to_dict(orient="records"):
        eligible = row["eligible_strict"] == "1"
        has_battle_overlap = (row["analytic_commander_id"], row["hierarchy_overlap_key"]) in battle_presence_by_overlap
        penalty = 0.5 if eligible and row["page_type"] != "battle_article" and has_battle_overlap else 1.0
        overlap_penalties.append(f"{penalty:.2f}")

        if eligible and row["page_type"] == "battle_article":
            model_a_weights.append("1.000000")
            model_c_weights.append("1.000000")
        elif eligible and row["page_type"] == "operation_article":
            model_a_weights.append("0.800000")
            model_c_weights.append("0.000000")
        else:
            model_a_weights.append("0.000000")
            model_c_weights.append("0.000000")

        if eligible:
            base_weight = PAGE_TYPE_WEIGHTS.get(row["page_type"], 0.0)
            model_b_weights.append(f"{base_weight * penalty:.6f}")
        else:
            model_b_weights.append("0.000000")

    annotated["hierarchy_overlap_penalty"] = overlap_penalties
    annotated["page_weight_model_a"] = model_a_weights
    annotated["page_weight_model_b"] = model_b_weights
    annotated["page_weight_model_c"] = model_c_weights
    return annotated


def build_package(output_root: Path) -> dict[str, Any]:
    battles = pd.read_csv(output_root / "battles_clean.csv", dtype=str).fillna("")
    commanders = pd.read_csv(output_root / "battle_commanders.csv", dtype=str).fillna("")
    master = pd.read_csv(output_root / "commanders_master.csv", dtype=str).fillna("")

    derived_dir = output_root / "derived_scoring"
    derived_dir.mkdir(parents=True, exist_ok=True)

    commander_exclusion_mask = (
        commanders.apply(
            lambda row: is_non_person_commander_link(
                row["commander_name_normalized"],
                row["commander_wikipedia_url"],
            ),
            axis=1,
        )
    )
    excluded_commanders = commanders.loc[commander_exclusion_mask].copy()
    if not excluded_commanders.empty:
        write_csv(derived_dir / "scoring_excluded_commander_rows.csv", excluded_commanders)
    commanders = commanders.loc[~commander_exclusion_mask].copy()
    if not master.empty and "canonical_wikipedia_url" in master.columns:
        master_exclusion_mask = (
            master.apply(
                lambda row: is_non_person_commander_link(
                    row["display_name"],
                    row["canonical_wikipedia_url"],
                ),
                axis=1,
            )
        )
        if master_exclusion_mask.any():
            write_csv(derived_dir / "scoring_excluded_master_rows.csv", master.loc[master_exclusion_mask].copy())
        master = master.loc[~master_exclusion_mask].copy()

    battles["page_type_confidence_num"] = battles["page_type_confidence"].map(parse_float)
    battles["extraction_confidence_num"] = battles["extraction_confidence"].map(parse_float)
    battles["analytic_year"], battles["analytic_year_confidence"] = zip(
        *battles.apply(lambda row: infer_analytic_year(row["battle_name"], row["date_raw"], row["year"]), axis=1)
    )
    (
        battles["scoring_result_raw"],
        battles["scoring_result_normalized"],
        battles["scoring_result_type"],
        battles["scoring_result_source"],
    ) = zip(
        *battles.apply(
            lambda row: derive_scoring_result_fields(row["result_raw"], row["result_normalized"], row["result_type"]),
            axis=1,
        )
    )
    battles["era_bucket"] = battles["analytic_year"].map(era_bucket_for_year)
    battles["conflict_key"] = battles.apply(
        lambda row: normalize_conflict_key(row["war_name"], row["battle_name"]), axis=1
    )
    battles["hierarchy_overlap_key"] = battles.apply(
        lambda row: f"{row['conflict_key']}|{row['analytic_year'] or 'unknown'}",
        axis=1,
    )

    commander_counts = commanders.groupby("battle_id").size().to_dict()
    linked_counts = (
        commanders.loc[commanders["commander_wikipedia_url"].ne("")]
        .groupby("battle_id")
        .size()
        .to_dict()
    )
    side_counts = commanders.groupby(["battle_id", "side"]).size().to_dict()

    eligibility_rows: list[dict[str, Any]] = []
    for row in battles.to_dict(orient="records"):
        title = normalize_title(row["battle_name"] or row["wikipedia_title"])
        page_type_conf = row["page_type_confidence_num"]
        extraction_conf = row["extraction_confidence_num"]
        has_commanders = commander_counts.get(row["battle_id"], 0) > 0
        has_linked_commanders = linked_counts.get(row["battle_id"], 0) > 0
        flags: list[str] = []

        if (page_type_conf or 0.0) < 0.67:
            flags.append("low_page_type_confidence")
        if (extraction_conf or 0.0) < 0.6:
            flags.append("low_extraction_confidence")
        if not has_commanders:
            flags.append("missing_commanders")
        if not row["analytic_year"] and normalize_space(row["year"]):
            flags.append("unresolved_year_anomaly")
        if title.startswith("List of "):
            flags.append("list_like_title")
        if (page_type_conf or 0.0) < 0.67 and (extraction_conf or 0.0) < 0.6:
            flags.append("low_confidence_combo")
        if (page_type_conf or 0.0) < 0.67 and not title_has_event_keywords(title):
            flags.append("no_event_keyword_low_confidence")
        if title_has_concept_keywords(title) and (page_type_conf or 0.0) < 0.67:
            flags.append("conceptual_title_low_confidence")
        if "fallback_wikitext" in normalize_space(row["notes"]).lower() and not title_has_event_keywords(title):
            flags.append("fallback_non_event_title")

        likely_false_positive = any(
            flag in flags
            for flag in {
                "list_like_title",
                "low_confidence_combo",
                "no_event_keyword_low_confidence",
                "conceptual_title_low_confidence",
                "fallback_non_event_title",
            }
        )
        if likely_false_positive:
            flags.append("likely_false_positive")

        strict_gate_include = (
            (page_type_conf or 0.0) >= 0.67
            and (extraction_conf or 0.0) >= 0.6
            and has_commanders
            and not likely_false_positive
            and bool(row["analytic_year"])
        )
        balanced_gate_include = (
            (page_type_conf or 0.0) >= 0.5
            and (extraction_conf or 0.0) >= 0.4
            and has_commanders
            and not likely_false_positive
        )

        eligibility_rows.append(
            {
                "battle_id": row["battle_id"],
                "battle_name": row["battle_name"],
                "wikipedia_title": row["wikipedia_title"],
                "page_type": row["page_type"],
                "battle_type": row["battle_type"],
                "strict_gate_include": "1" if strict_gate_include else "0",
                "balanced_gate_include": "1" if balanced_gate_include else "0",
                "exclude_reason_flags": join_flags(flags),
                "page_type_confidence": row["page_type_confidence"],
                "extraction_confidence": row["extraction_confidence"],
                "has_commanders": "1" if has_commanders else "0",
                "has_linked_commanders": "1" if has_linked_commanders else "0",
                "has_result_raw": "1" if normalize_space(row["result_raw"]) else "0",
                "has_result_type": "1" if normalize_space(row["scoring_result_type"]) else "0",
                "analytic_year": row["analytic_year"],
                "analytic_year_confidence": row["analytic_year_confidence"],
                "era_bucket": row["era_bucket"],
                "conflict_key": row["conflict_key"],
                "likely_false_positive": "1" if likely_false_positive else "0",
                "hierarchy_overlap_key": row["hierarchy_overlap_key"],
                "scoring_result_source": row["scoring_result_source"],
            }
        )

    eligibility = pd.DataFrame(eligibility_rows)
    eligibility = apply_battle_verification_overrides(output_root, eligibility)
    write_csv(derived_dir / "engagement_eligibility.csv", eligibility)

    master["canonical_wikipedia_url"] = master["wikipedia_page"].map(canonicalize_wikipedia_url)
    url_to_source_ids = (
        master.loc[master["canonical_wikipedia_url"].ne("")]
        .groupby("canonical_wikipedia_url")["commander_id"]
        .apply(lambda series: sorted(set(series)))
        .to_dict()
    )
    raw_master_candidates = master.loc[master["canonical_wikipedia_url"].eq("")].copy()
    raw_master_candidates["raw_name_key"] = raw_master_candidates["name_primary"].map(clean_name).map(str.lower)
    raw_name_to_source_ids = (
        raw_master_candidates.groupby("raw_name_key")["commander_id"]
        .apply(lambda series: sorted(set(series)))
        .to_dict()
    )

    commanders["canonical_commander_url"] = commanders["commander_wikipedia_url"].map(canonicalize_wikipedia_url)
    commanders["clean_commander_name"] = commanders["commander_name_normalized"].map(clean_name)

    source_commander_ids: list[str] = []
    source_resolution_methods: list[str] = []
    analytic_identity_keys: list[str] = []
    for row in commanders.to_dict(orient="records"):
        canonical_url = row["canonical_commander_url"]
        clean_name_key = clean_name(row["commander_name_normalized"]).lower()
        if canonical_url and canonical_url in url_to_source_ids:
            source_commander_ids.append(url_to_source_ids[canonical_url][0])
            source_resolution_methods.append("linked_wikipedia_url")
            analytic_identity_keys.append(f"url:{canonical_url}")
        elif clean_name_key and clean_name_key in raw_name_to_source_ids:
            source_commander_ids.append(raw_name_to_source_ids[clean_name_key][0])
            source_resolution_methods.append("normalized_raw_name")
            analytic_identity_keys.append(f"name:{clean_name_key}")
        else:
            fallback_key = canonical_url or clean_name_key or row["commander_name_raw"]
            source_commander_ids.append(make_id("src", fallback_key))
            source_resolution_methods.append("synthetic_fallback")
            analytic_identity_keys.append(f"url:{canonical_url}" if canonical_url else f"name:{clean_name_key}")

    commanders["source_commander_id"] = source_commander_ids
    commanders["identity_source"] = source_resolution_methods
    commanders["analytic_identity_key"] = analytic_identity_keys
    commanders["analytic_commander_id"] = commanders["analytic_identity_key"].map(lambda key: make_id("acmd", key))
    commanders["is_linked_identity"] = commanders["canonical_commander_url"].ne("")
    commanders["is_raw_name_only"] = commanders["canonical_commander_url"].eq("")

    bridge_rows: list[dict[str, Any]] = []
    for analytic_commander_id, group in commanders.groupby("analytic_commander_id", sort=False):
        mode_names = group["clean_commander_name"].mode()
        display_name = clean_name(mode_names.iloc[0] if not mode_names.empty else group["clean_commander_name"].iloc[0])
        canonical_url = (
            group.loc[group["canonical_commander_url"].ne(""), "canonical_commander_url"].mode().iloc[0]
            if group["canonical_commander_url"].ne("").any()
            else ""
        )
        source_ids = sorted(set(group["source_commander_id"]))
        original_urls = sorted(set(url for url in group["commander_wikipedia_url"] if normalize_space(url)))
        linked_identity = bool(canonical_url)
        suspect = is_suspect_identity(display_name, canonical_url)
        if linked_identity:
            canonicalization_rule = (
                "canonicalized_url_variants"
                if len(set(group["canonical_commander_url"])) == 1 and len(original_urls) > 1
                else "direct_url"
            )
            identity_reliability = "low" if suspect else "high"
        else:
            canonicalization_rule = "raw_name_identity"
            identity_reliability = "low" if suspect else "medium"

        bridge_rows.append(
            {
                "analytic_commander_id": analytic_commander_id,
                "display_name": display_name,
                "canonical_wikipedia_url": canonical_url,
                "source_commander_id": " | ".join(source_ids),
                "identity_source": "linked_wikipedia_url" if linked_identity else "normalized_raw_name",
                "identity_reliability": identity_reliability,
                "canonicalization_rule": canonicalization_rule,
                "is_linked_identity": "1" if linked_identity else "0",
                "is_raw_name_only": "1" if not linked_identity else "0",
                "is_suspect_identity": "1" if suspect else "0",
            }
        )

    bridge = pd.DataFrame(bridge_rows)
    write_csv(derived_dir / "commander_identity_bridge.csv", bridge)

    battles_indexed = battles.set_index("battle_id")
    eligibility_indexed = eligibility.set_index("battle_id")
    bridge_indexed = bridge.set_index("analytic_commander_id")

    annotated_rows: list[dict[str, Any]] = []
    for row in commanders.to_dict(orient="records"):
        battle_row = battles_indexed.loc[row["battle_id"]]
        eligibility_row = eligibility_indexed.loc[row["battle_id"]]
        bridge_row = bridge_indexed.loc[row["analytic_commander_id"]]
        outcome_category, inference_method, inference_confidence = derive_outcome_category(
            row["battle_result_for_commander"],
            battle_row["scoring_result_type"],
            battle_row["scoring_result_raw"],
            row["side"],
            battle_row,
        )
        annotated_rows.append(
            {
                "analytic_commander_id": row["analytic_commander_id"],
                "display_name": bridge_row["display_name"],
                "canonical_wikipedia_url": bridge_row["canonical_wikipedia_url"],
                "source_commander_id": row["source_commander_id"],
                "identity_source": row["identity_source"],
                "identity_reliability": bridge_row["identity_reliability"],
                "is_linked_identity": bridge_row["is_linked_identity"],
                "is_raw_name_only": bridge_row["is_raw_name_only"],
                "is_suspect_identity": bridge_row["is_suspect_identity"],
                "battle_id": row["battle_id"],
                "battle_name": battle_row["battle_name"],
                "wikipedia_title": battle_row["wikipedia_title"],
                "page_type": battle_row["page_type"],
                "battle_type": battle_row["battle_type"],
                "war_name": battle_row["war_name"],
                "analytic_year": battle_row["analytic_year"],
                "analytic_year_confidence": battle_row["analytic_year_confidence"],
                "era_bucket": battle_row["era_bucket"],
                "conflict_key": battle_row["conflict_key"],
                "hierarchy_overlap_key": battle_row["hierarchy_overlap_key"],
                "side": row["side"],
                "belligerent": row["belligerent"],
                "opposing_commander_names_raw": row["opposing_commander_names_raw"],
                "result_type": battle_row["result_type"],
                "result_raw": battle_row["result_raw"],
                "battle_result_for_commander_raw": row["battle_result_for_commander"],
                "page_result_raw": battle_row["result_raw"],
                "page_result_type": battle_row["result_type"],
                "scoring_result_raw": battle_row["scoring_result_raw"],
                "scoring_result_type": battle_row["scoring_result_type"],
                "scoring_result_source": battle_row["scoring_result_source"],
                "presence_credit": "1.0",
                "outcome_credit_fraction": "0.000000",
                "outcome_category": outcome_category,
                "outcome_inference_method": inference_method,
                "outcome_inference_confidence": inference_confidence,
                "eligible_strict": eligibility_row["strict_gate_include"],
                "eligible_balanced": eligibility_row["balanced_gate_include"],
                "page_type_confidence": eligibility_row["page_type_confidence"],
                "extraction_confidence": eligibility_row["extraction_confidence"],
                "exclude_reason_flags": eligibility_row["exclude_reason_flags"],
            }
        )

    annotated = pd.DataFrame(annotated_rows)
    if annotated.duplicated(subset=["analytic_commander_id", "battle_id"]).any():
        collapsed_rows: list[dict[str, Any]] = []
        for _, group in annotated.groupby(["analytic_commander_id", "battle_id"], sort=False):
            base = group.iloc[0].to_dict()
            unique_sides = sorted(set(group["side"]))
            base["source_commander_id"] = " | ".join(sorted(set(group["source_commander_id"])))
            base["belligerent"] = " | ".join(sorted(set(value for value in group["belligerent"] if normalize_space(value))))
            base["opposing_commander_names_raw"] = " | ".join(
                sorted(set(value for value in group["opposing_commander_names_raw"] if normalize_space(value)))
            )
            if len(unique_sides) > 1:
                base["side"] = "multiple_sides"
                base["battle_result_for_commander_raw"] = ""
                base["outcome_category"] = "unknown"
                base["outcome_inference_method"] = "ambiguous_multi_side_commander"
                base["outcome_inference_confidence"] = "low"
                base["eligible_strict"] = "0"
                base["eligible_balanced"] = "0"
                existing_flags = [flag for flag in base["exclude_reason_flags"].split(" | ") if flag]
                existing_flags.append("ambiguous_multi_side_commander")
                base["exclude_reason_flags"] = join_flags(existing_flags)
            collapsed_rows.append(base)
        annotated = pd.DataFrame(collapsed_rows)

    annotated = apply_commander_verification_overrides(output_root, annotated)
    annotated = apply_commander_outcome_overrides(output_root, annotated)
    annotated = apply_split_outcome_credit(annotated)
    annotated = apply_page_weights(annotated)
    annotated["known_outcome_flag"] = annotated["outcome_category"].ne("unknown").astype(int).astype(str)

    write_csv(derived_dir / "commander_engagements_annotated.csv", annotated)

    battle_opponent_entities: dict[tuple[str, str], list[str]] = {}
    for battle_row in battles.to_dict(orient="records"):
        side_entities = {
            "side_a": extract_belligerent_entities(battle_row["belligerent_1_raw"]),
            "side_b": extract_belligerent_entities(battle_row["belligerent_2_raw"]),
            "side_c": extract_belligerent_entities(battle_row["belligerent_3_raw"]),
            "side_d": [],
        }
        for side in ("side_a", "side_b", "side_c", "side_d"):
            opponents: list[str] = []
            for other_side, entities in side_entities.items():
                if other_side != side:
                    opponents.extend(entities)
            battle_opponent_entities[(battle_row["battle_id"], side)] = sorted(dict.fromkeys(opponents))

    opponent_rows: list[dict[str, Any]] = []
    for row in annotated.to_dict(orient="records"):
        for opponent in battle_opponent_entities.get((row["battle_id"], row["side"]), []):
            opponent_rows.append(
                {
                    "analytic_commander_id": row["analytic_commander_id"],
                    "display_name": row["display_name"],
                    "opponent_key": slugify(opponent),
                    "opponent_entity": opponent,
                    "engagement_count_all": 1,
                    "engagement_count_strict": 1 if row["eligible_strict"] == "1" else 0,
                    "weighted_presence_model_b": float(row["page_weight_model_b"]),
                    "reliability": "medium_low",
                }
            )

    if opponent_rows:
        opponent_profile = (
            pd.DataFrame(opponent_rows)
            .groupby(
                ["analytic_commander_id", "display_name", "opponent_key", "opponent_entity", "reliability"],
                as_index=False,
            )
            .agg(
                engagement_count_all=("engagement_count_all", "sum"),
                engagement_count_strict=("engagement_count_strict", "sum"),
                weighted_presence_model_b=("weighted_presence_model_b", "sum"),
            )
        )
    else:
        opponent_profile = pd.DataFrame(
            columns=[
                "analytic_commander_id",
                "display_name",
                "opponent_key",
                "opponent_entity",
                "reliability",
                "engagement_count_all",
                "engagement_count_strict",
                "weighted_presence_model_b",
            ]
        )
    write_csv(derived_dir / "commander_opponent_profile.csv", opponent_profile)

    page_type_order = ["battle_article", "operation_article", "campaign_article", "war_conflict_article"]
    era_order = [
        "ancient",
        "medieval",
        "early_modern",
        "revolutionary_napoleonic",
        "long_nineteenth_century",
        "world_wars",
        "cold_war",
        "contemporary",
        "unknown",
    ]
    outcome_categories = [
        "decisive_victory",
        "victory",
        "tactical_victory",
        "pyrrhic_victory",
        "indecisive",
        "draw",
        "stalemate",
        "disputed",
        "defeat",
        "major_defeat",
        "unknown",
    ]
    opponent_breadth_map = opponent_profile.groupby("analytic_commander_id")["opponent_key"].nunique().to_dict()

    summary_rows: list[dict[str, Any]] = []
    outcome_rows: list[dict[str, Any]] = []
    page_type_rows: list[dict[str, Any]] = []
    era_rows: list[dict[str, Any]] = []
    ranking_rows: list[dict[str, Any]] = []

    for analytic_commander_id, group in annotated.groupby("analytic_commander_id", sort=False):
        bridge_row = bridge_indexed.loc[analytic_commander_id]
        strict = group.loc[group["eligible_strict"].eq("1")].copy()
        known = strict.loc[strict["outcome_category"].ne("unknown")].copy()
        battle_known = known.loc[known["page_type"].eq("battle_article")].copy()
        all_years = sorted({int(value) for value in group["analytic_year"] if normalize_space(value)})
        strict_years = sorted({int(value) for value in strict["analytic_year"] if normalize_space(value)})
        years_for_span = strict_years or all_years
        first_year = str(years_for_span[0]) if years_for_span else ""
        last_year = str(years_for_span[-1]) if years_for_span else ""
        active_span = str((years_for_span[-1] - years_for_span[0]) if len(years_for_span) >= 2 else 0) if years_for_span else ""
        nonwar_group = group.loc[group["page_type"].isin(["battle_article", "operation_article", "campaign_article"])]
        nonwar_strict = strict.loc[strict["page_type"].isin(["battle_article", "operation_article", "campaign_article"])]
        all_nonwar_years = sorted({int(value) for value in nonwar_group["analytic_year"] if normalize_space(value)})
        strict_nonwar_years = sorted({int(value) for value in nonwar_strict["analytic_year"] if normalize_space(value)})
        years_for_nonwar_span = strict_nonwar_years or all_nonwar_years or years_for_span
        first_nonwar_year = str(years_for_nonwar_span[0]) if years_for_nonwar_span else ""
        last_nonwar_year = str(years_for_nonwar_span[-1]) if years_for_nonwar_span else ""
        active_nonwar_span = (
            str((years_for_nonwar_span[-1] - years_for_nonwar_span[0]) if len(years_for_nonwar_span) >= 2 else 0)
            if years_for_nonwar_span
            else ""
        )

        low_conf_mask = (
            group["page_type_confidence"].map(parse_float).fillna(0).lt(0.67)
            | group["extraction_confidence"].map(parse_float).fillna(0).lt(0.6)
        )
        linked_share = float((group["is_linked_identity"] == "1").mean()) if len(group) else 0.0
        medium_share = float((group["identity_reliability"] == "medium").mean()) if len(group) else 0.0

        missing_flags: list[str] = []
        if bridge_row["is_raw_name_only"] == "1":
            missing_flags.append("raw_identity_only")
        if bridge_row["is_suspect_identity"] == "1":
            missing_flags.append("suspect_identity")
        if not years_for_span:
            missing_flags.append("missing_analytic_year")
        if known.empty:
            missing_flags.append("no_known_outcomes")
        if analytic_commander_id not in opponent_breadth_map:
            missing_flags.append("no_opponent_entities")

        summary_rows.append(
            {
                "analytic_commander_id": analytic_commander_id,
                "display_name": bridge_row["display_name"],
                "canonical_wikipedia_url": bridge_row["canonical_wikipedia_url"],
                "identity_reliability": bridge_row["identity_reliability"],
                "is_linked_identity": bridge_row["is_linked_identity"],
                "is_raw_name_only": bridge_row["is_raw_name_only"],
                "is_suspect_identity": bridge_row["is_suspect_identity"],
                "total_engagements_all": len(group),
                "total_engagements_strict": len(strict),
                "total_battle_pages_strict": int(strict["page_type"].eq("battle_article").sum()),
                "total_war_pages_strict": int(strict["page_type"].eq("war_conflict_article").sum()),
                "total_campaign_pages_strict": int(strict["page_type"].eq("campaign_article").sum()),
                "total_operation_pages_strict": int(strict["page_type"].eq("operation_article").sum()),
                "first_analytic_year": first_year,
                "last_analytic_year": last_year,
                "active_span_years": active_span,
                "first_active_year_nonwar": first_nonwar_year,
                "last_active_year_nonwar": last_nonwar_year,
                "active_span_years_nonwar": active_nonwar_span,
                "distinct_conflicts_all": int(group["conflict_key"].nunique()),
                "distinct_conflicts_strict": int(strict["conflict_key"].nunique()),
                "distinct_opponents_strict": int(opponent_breadth_map.get(analytic_commander_id, 0)),
                "linked_identity_share": f"{linked_share:.6f}",
                "medium_identity_share": f"{medium_share:.6f}",
                "low_confidence_page_share": f"{float(low_conf_mask.mean() if len(group) else 0.0):.6f}",
                "missing_data_flags": join_flags(missing_flags),
            }
        )

        outcome_counter = Counter(strict["outcome_category"])
        for category in outcome_categories:
            outcome_counter.setdefault(category, 0)
        known_scores = {
            mode: [OUTCOME_SCORE_MAPS[mode][value] for value in known["outcome_category"] if value in OUTCOME_SCORE_MAPS[mode]]
            for mode in OUTCOME_SCORE_MAPS
        }
        strict_count = len(strict)
        known_count = len(known)
        outcome_rows.append(
            {
                "analytic_commander_id": analytic_commander_id,
                "display_name": bridge_row["display_name"],
                "eligible_strict_engagement_count": strict_count,
                "known_outcome_count": known_count,
                "known_outcome_share": f"{(known_count / strict_count) if strict_count else 0.0:.6f}",
                **{f"count_{category}": int(outcome_counter[category]) for category in outcome_categories},
                **{
                    f"share_{category}": f"{(outcome_counter[category] / strict_count) if strict_count else 0.0:.6f}"
                    for category in outcome_categories
                },
                "mean_conservative_score": safe_mean(known_scores["conservative"]),
                "mean_balanced_score": safe_mean(known_scores["balanced"]),
                "mean_aggressive_score": safe_mean(known_scores["aggressive"]),
                "outcome_evidence_reliability_band": outcome_reliability_band(known_count),
            }
        )

        page_type_row = {
            "analytic_commander_id": analytic_commander_id,
            "display_name": bridge_row["display_name"],
            "engagements_all": len(group),
            "engagements_strict": len(strict),
            "weighted_presence_model_a": f"{strict['page_weight_model_a'].astype(float).sum():.6f}",
            "weighted_presence_model_b": f"{strict['page_weight_model_b'].astype(float).sum():.6f}",
            "weighted_presence_model_c": f"{strict['page_weight_model_c'].astype(float).sum():.6f}",
        }
        all_page_type_counts = group["page_type"].value_counts().to_dict()
        strict_page_type_counts = strict["page_type"].value_counts().to_dict()
        for page_type in page_type_order:
            all_count = int(all_page_type_counts.get(page_type, 0))
            strict_count_pt = int(strict_page_type_counts.get(page_type, 0))
            page_type_row[f"count_all_{page_type}"] = all_count
            page_type_row[f"share_all_{page_type}"] = f"{(all_count / len(group)) if len(group) else 0.0:.6f}"
            page_type_row[f"count_strict_{page_type}"] = strict_count_pt
            page_type_row[f"share_strict_{page_type}"] = f"{(strict_count_pt / len(strict)) if len(strict) else 0.0:.6f}"
        page_type_rows.append(page_type_row)

        era_counts = strict["era_bucket"].value_counts().to_dict()
        era_row = {
            "analytic_commander_id": analytic_commander_id,
            "display_name": bridge_row["display_name"],
            "engagements_strict": len(strict),
        }
        for bucket in era_order:
            count = int(era_counts.get(bucket, 0))
            era_row[f"count_{bucket}"] = count
            era_row[f"share_{bucket}"] = f"{(count / len(strict)) if len(strict) else 0.0:.6f}"
        non_unknown_counts = {bucket: count for bucket, count in era_counts.items() if bucket != "unknown" and count > 0}
        era_row["primary_era_bucket"] = max(non_unknown_counts.items(), key=lambda item: item[1])[0] if non_unknown_counts else "unknown"
        era_row["multi_era_flag"] = "1" if len(non_unknown_counts) > 1 else "0"
        era_rows.append(era_row)

        conservative_scores = known_scores["conservative"]
        balanced_scores = known_scores["balanced"]
        aggressive_scores = known_scores["aggressive"]
        non_defeat_known = known.loc[~known["outcome_category"].isin(["defeat", "major_defeat"])]
        overlap_rate = (
            float(
                strict.loc[strict["page_type"].ne("battle_article"), "hierarchy_overlap_penalty"]
                .map(float)
                .lt(1.0)
                .mean()
            )
            if strict.loc[strict["page_type"].ne("battle_article")].shape[0]
            else 0.0
        )
        feature_flags: list[str] = []
        if bridge_row["is_raw_name_only"] == "1":
            feature_flags.append("raw_identity_only")
        if bridge_row["is_suspect_identity"] == "1":
            feature_flags.append("suspect_identity")
        if len(strict) < 5:
            feature_flags.append("sparse_participation")
        if len(known) < 3:
            feature_flags.append("low_outcome_evidence")
        if float(low_conf_mask.mean() if len(group) else 0.0) > 0.5:
            feature_flags.append("high_low_confidence_share")

        ranking_rows.append(
            {
                "analytic_commander_id": analytic_commander_id,
                "display_name": bridge_row["display_name"],
                "canonical_wikipedia_url": bridge_row["canonical_wikipedia_url"],
                "identity_reliability": bridge_row["identity_reliability"],
                "is_linked_identity": bridge_row["is_linked_identity"],
                "is_suspect_identity": bridge_row["is_suspect_identity"],
                "model_a_eligible": "1" if ((bridge_row["is_linked_identity"] == "1") and strict["page_type"].isin(["battle_article", "operation_article"]).any()) else "0",
                "model_b_eligible": "1" if ((bridge_row["is_linked_identity"] == "1") and len(strict) > 0) else "0",
                "model_c_eligible": "1" if ((bridge_row["is_linked_identity"] == "1") and strict["page_type"].eq("battle_article").any()) else "0",
                "default_ranking_eligible": "1"
                if (
                    bridge_row["is_linked_identity"] == "1"
                    and bridge_row["is_suspect_identity"] == "0"
                    and strict["page_type"].eq("battle_article").sum() >= 5
                    and len(battle_known) >= 3
                )
                else "0",
                "high_confidence_participation_count": int(strict.loc[strict["identity_reliability"].eq("high")].shape[0]),
                "eligible_engagement_count_strict": len(strict),
                "eligible_battle_count_strict": int(strict["page_type"].eq("battle_article").sum()),
                "eligible_operation_count_strict": int(strict["page_type"].eq("operation_article").sum()),
                "eligible_campaign_count_strict": int(strict["page_type"].eq("campaign_article").sum()),
                "eligible_war_count_strict": int(strict["page_type"].eq("war_conflict_article").sum()),
                "weighted_presence_model_a": f"{strict['page_weight_model_a'].astype(float).sum():.6f}",
                "weighted_presence_model_b": f"{strict['page_weight_model_b'].astype(float).sum():.6f}",
                "weighted_presence_model_c": f"{strict['page_weight_model_c'].astype(float).sum():.6f}",
                "conflict_breadth_strict": int(strict["conflict_key"].nunique()),
                "page_type_diversity_strict": int(strict["page_type"].nunique()),
                "era_diversity_strict": int(strict.loc[strict["era_bucket"].ne("unknown"), "era_bucket"].nunique()),
                "first_analytic_year": first_year,
                "last_analytic_year": last_year,
                "active_span_years": active_span,
                "linked_identity_share": f"{linked_share:.6f}",
                "known_outcome_count_strict": len(known),
                "known_outcome_share_strict": f"{(len(known) / len(strict)) if len(strict) else 0.0:.6f}",
                "mean_outcome_conservative": safe_mean(conservative_scores),
                "mean_outcome_balanced": safe_mean(balanced_scores),
                "mean_outcome_aggressive": safe_mean(aggressive_scores),
                "non_defeat_share_strict": f"{(len(non_defeat_known) / len(known)) if len(known) else 0.0:.6f}",
                "outcome_variance_balanced": safe_variance(balanced_scores),
                "capped_participation_intensity": f"{math.log1p(len(strict)):.6f}",
                "overlap_rate_strict_nonbattle": f"{overlap_rate:.6f}",
                "opponent_breadth_strict": int(opponent_breadth_map.get(analytic_commander_id, 0)),
                "feature_quality_flags": join_flags(feature_flags),
            }
        )

    commander_summary = pd.DataFrame(summary_rows)
    commander_outcomes = pd.DataFrame(outcome_rows)
    commander_page_types = pd.DataFrame(page_type_rows)
    commander_eras = pd.DataFrame(era_rows)
    commander_features = pd.DataFrame(ranking_rows)

    write_csv(derived_dir / "commander_engagement_summary.csv", commander_summary)
    write_csv(derived_dir / "commander_outcome_profile.csv", commander_outcomes)
    write_csv(derived_dir / "commander_page_type_profile.csv", commander_page_types)
    write_csv(derived_dir / "commander_era_profile.csv", commander_eras)
    write_csv(derived_dir / "commander_ranking_features.csv", commander_features)

    metrics = {
        "source": {
            "retained_pages": int(len(battles)),
            "commander_rows": int(len(commanders)),
            "commander_master_rows": int(len(master)),
        },
        "derived": {
            "engagement_eligibility_rows": int(len(eligibility)),
            "identity_bridge_rows": int(len(bridge)),
            "annotated_rows": int(len(annotated)),
            "opponent_profile_rows": int(len(opponent_profile)),
            "commander_summary_rows": int(len(commander_summary)),
            "commander_features_rows": int(len(commander_features)),
        },
        "eligibility": {
            "strict_included_pages": int(eligibility["strict_gate_include"].eq("1").sum()),
            "balanced_included_pages": int(eligibility["balanced_gate_include"].eq("1").sum()),
            "likely_false_positive_pages": int(eligibility["likely_false_positive"].eq("1").sum()),
            "pages_with_unresolved_year_anomaly": int(eligibility["exclude_reason_flags"].str.contains("unresolved_year_anomaly", regex=False).sum()),
        },
        "identities": {
            "linked_identities": int(bridge["is_linked_identity"].eq("1").sum()),
            "raw_name_only_identities": int(bridge["is_raw_name_only"].eq("1").sum()),
            "suspect_identities": int(bridge["is_suspect_identity"].eq("1").sum()),
        },
        "outcomes": {
            "strict_known_outcome_rows": int(
                annotated.loc[
                    annotated["eligible_strict"].eq("1") & annotated["outcome_category"].ne("unknown")
                ].shape[0]
            ),
            "strict_known_outcome_commanders": int(
                annotated.loc[
                    annotated["eligible_strict"].eq("1") & annotated["outcome_category"].ne("unknown")
                ]["analytic_commander_id"].nunique()
            ),
            "default_ranking_eligible_commanders": int(commander_features["default_ranking_eligible"].eq("1").sum()),
        },
        "validation": {
            "eligibility_unique_battle_ids": bool(eligibility["battle_id"].is_unique),
            "bridge_unique_commander_ids": bool(bridge["analytic_commander_id"].is_unique),
            "annotated_unique_commander_battle_pairs": bool(
                not annotated.duplicated(subset=["analytic_commander_id", "battle_id"]).any()
            ),
        },
    }
    (derived_dir / "scoring_build_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description="Build scoring-stage derived tables from the frozen dataset.")
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("outputs_cleaned_2026-04-21_fullpopulation_authoritative"),
        help="Frozen output directory containing battles_clean.csv and related files.",
    )
    args = parser.parse_args()
    metrics = build_package(args.output_root)
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
