from __future__ import annotations

import argparse
import csv
import hashlib
import json
import logging
import math
import multiprocessing as mp
import re
import threading
import time
from collections import Counter, defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from queue import Empty
from typing import Any, Iterable
from urllib.parse import quote, unquote, urljoin, urlparse

import dateparser
import pandas as pd
import requests
from bs4 import BeautifulSoup
from dateparser.search import search_dates
from rapidfuzz import fuzz
from tqdm import tqdm


WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"
WIKIPEDIA_BASE = "https://en.wikipedia.org"
ROOT_TITLE = "Lists of battles"
USER_AGENT = "HistoricalBattleDatasetBot/0.1 (research dataset construction; local execution)"
NOW_UTC = datetime.now(timezone.utc)
THREAD_LOCAL = threading.local()

CONTENT_NAMESPACES = {
    "Talk:",
    "User:",
    "User talk:",
    "Wikipedia:",
    "Wikipedia talk:",
    "File:",
    "File talk:",
    "MediaWiki:",
    "Template:",
    "Help:",
    "Category:",
    "Portal:",
    "Draft:",
    "Book:",
    "Education Program:",
    "TimedText:",
    "Module:",
    "Gadget:",
    "Special:",
}

LIST_KEYWORDS = {"list", "lists", "timeline", "chronology", "outline", "index"}
LIST_TITLE_PATTERNS = (
    "list of battles",
    "lists of battles",
    "battles of ",
    "timeline of ",
    "chronology of ",
    "military history of ",
    "battles in ",
    "battles by ",
)
BATTLE_CONTEXT_KEYWORDS = {
    "battle",
    "battles",
    "siege",
    "sieges",
    "naval battle",
    "naval battles",
    "military operation",
    "military operations",
    "engagement",
    "engagements",
    "warfare",
    "conflict",
    "conflicts",
    "war",
    "wars",
}
BATTLE_TITLE_KEYWORDS = {
    "battle",
    "siege",
    "operation",
    "skirmish",
    "raid",
    "campaign",
    "engagement",
    "massacre",
    "assault",
    "expedition",
    "landing",
    "offensive",
    "uprising",
    "rebellion",
    "mutiny",
    "combat",
}
WAR_CONFLICT_TITLE_KEYWORDS = {
    "war",
    "wars",
    "conflict",
    "conflicts",
    "insurgency",
    "insurgencies",
    "rebellion",
    "rebellions",
}
CAMPAIGN_OPERATION_TITLE_KEYWORDS = {
    "campaign",
    "campaigns",
    "operation",
    "operations",
    "offensive",
    "offensives",
    "expedition",
    "expeditions",
    "theater",
    "theatre",
    "front",
}
BROAD_MILITARY_TITLE_KEYWORDS = BATTLE_TITLE_KEYWORDS | WAR_CONFLICT_TITLE_KEYWORDS | CAMPAIGN_OPERATION_TITLE_KEYWORDS
BATTLE_CATEGORY_KEYWORDS = {
    "battles",
    "sieges",
    "military operations",
    "naval battles",
    "conflicts",
    "campaigns",
    "engagements",
}
WAR_CATEGORY_KEYWORDS = {
    "wars",
    "conflicts",
    "insurgencies",
    "rebellions",
    "civil wars",
}
CAMPAIGN_CATEGORY_KEYWORDS = {
    "campaigns",
    "operations",
    "offensives",
    "military operations",
}
GENERIC_COMMANDER_TOKENS = {
    "unknown",
    "none",
    "n/a",
    "various",
    "multiple commanders",
    "several commanders",
    "commander",
    "commanders",
    "leaders",
    "pow",
    "kia",
    "mia",
    "wia",
    "detailed list",
    "cubicularius",
}
NON_PERSON_COMMANDER_KEYWORDS = {
    "division",
    "regiment",
    "corps",
    "army",
    "fleet",
    "force",
    "forces",
    "police",
    "committee",
    "council",
    "government",
    "battalion",
    "brigade",
    "squad",
    "squads",
    "air commodore",
    "commander-in-chief",
    "general officer commanding",
    "officer commanding",
    "high commissioners",
    "killed in action",
    "admiral",
    "commander",
    "police force",
    "security forces",
    "night squads",
    "military",
}
BIOGRAPHY_CATEGORY_KEYWORDS = {"births", "deaths", "people", "biographies"}
WAR_PAGE_KEYWORDS = {" war", "wars", "conflict", "insurgency", "civil war"}
NON_BATTLE_PAGE_HINTS = {
    "division",
    "regiment",
    "corps",
    "army",
    "personnel",
    "biography",
    "military history",
    "aviation",
}
SUPPORT_PAGE_TITLE_HINTS = {
    "bibliography",
    "order of battle",
    "orders of battle",
    "casualties of",
    "combatants of",
    "prisoner of war",
    "prisoners of war",
    "military casualties",
    "military equipment",
    "uniforms",
    "awards",
    "medals",
    "aftermath",
    "veterans",
    "demobilization",
    "reparations",
}
RETAINED_ENGAGEMENT_HINTS = {
    "battle",
    "siege",
    "skirmish",
    "raid",
    "massacre",
    "campaign",
    "operation",
    "offensive",
    "war",
    "conflict",
    "insurgency",
    "rebellion",
    "uprising",
    "theater",
    "theatre",
    "front",
}
CATEGORY_DISCOVERY_ROOTS = [
    "Battles",
    "Sieges",
    "Naval battles",
    "Wars",
    "Conflicts",
    "Military operations",
    "Campaigns",
    "Raids",
    "Rebellions",
    "Uprisings",
    "Massacres",
]
CATEGORY_DISCOVERY_KEYWORDS = {
    "battle",
    "battles",
    "siege",
    "sieges",
    "naval battles",
    "war",
    "wars",
    "conflict",
    "conflicts",
    "campaign",
    "campaigns",
    "military operations",
    "operation",
    "operations",
    "raid",
    "raids",
    "rebellion",
    "rebellions",
    "uprising",
    "uprisings",
    "massacre",
    "massacres",
    "insurgency",
    "insurgencies",
    "theatre",
    "theater",
    "front",
}
CATEGORY_REJECT_KEYWORDS = {
    "lists",
    "bibliography",
    "casualties",
    "combatants",
    "military units",
    "weapons",
    "equipment",
    "uniforms",
    "films",
    "novels",
    "games",
    "video games",
    "songs",
    "albums",
    "people",
    "biographies",
}
RESULT_KEYWORDS = (
    "victory",
    "defeat",
    "stalemate",
    "indecisive",
    "draw",
    "repulsed",
    "repelled",
    "captured",
    "suppressed",
    "overran",
)
DATE_HINT_PATTERN = re.compile(
    r"\b(?:\d{1,2}\s+[A-Z][a-z]+\s+\d{3,4}|[A-Z][a-z]+\s+\d{1,2},\s+\d{3,4}|[A-Z][a-z]+\s+\d{3,4}|\d{3,4}\s*[–-]\s*\d{3,4})\b"
)
COMMANDER_PREFIX_PATTERN = re.compile(
    r"^(?:general|gen\.?|lt\. gen\.?|major general|brigadier|brig\.?|admiral|rear admiral|vice admiral|marshal|field marshal|colonel|col\.?|captain|capt\.?)\s+",
    re.I,
)
SECTION_HEADERS = {
    "belligerents": "belligerents",
    "commanders and leaders": "commanders",
    "commanders": "commanders",
    "strength": "strength",
    "casualties and losses": "casualties",
    "casualties": "casualties",
}
SOURCE_FAMILY_PATTERNS: list[tuple[str, tuple[str, ...]]] = [
    ("period_based", ("ancient", "classical", "medieval", "early modern", "modern", "contemporary", "century")),
    ("war_conflict_based", (" war", " wars", " conflict", " conflicts", " rebellion", " rebellions", " insurgency", " insurgencies")),
    ("region_based", ("in africa", "in asia", "in europe", "in the americas", "in the middle east", "of africa", "of asia", "of europe", "by geographic area")),
    ("participant_based", ("involving", "by participant", "by country", "by empire", "by state")),
    ("battle_type_based", ("siege", "naval", "operation", "raid", "massacre", "casualty", "commander")),
]
BENCHMARK_TITLES = [
    "Battle of Thermopylae",
    "Battle of Gaugamela",
    "Punic Wars",
    "Battle of Hastings",
    "Siege of Jerusalem (1099)",
    "Hundred Years' War",
    "Battle of Lepanto",
    "Thirty Years' War",
    "Battle of Blenheim",
    "Napoleonic Wars",
    "Battle of Waterloo",
    "American Civil War",
    "World War II",
    "Battle of Midway",
    "Battle of Stalingrad",
    "Gulf War",
    "Battle of Kyiv (2022)",
    "Russo-Ukrainian War",
]
ROW_LABEL_MAP = {
    "part of": "war_name",
    "conflict": "war_name",
    "date": "date_raw",
    "location": "location_raw",
    "result": "result_raw",
    "belligerents": "belligerents",
    "commanders and leaders": "commanders",
    "commanders": "commanders",
    "strength": "strength",
    "casualties and losses": "casualties",
    "casualties": "casualties",
}
RESULT_PATTERNS = [
    ("pyrrhic_victory", re.compile(r"\bpyrrhic victory\b", re.I)),
    ("decisive_victory", re.compile(r"\bdecisive .*victory\b|\bdecisive victory\b", re.I)),
    ("tactical_victory", re.compile(r"\btactical .*victory\b|\btactical victory\b", re.I)),
    ("draw", re.compile(r"\bdraw\b", re.I)),
    ("stalemate", re.compile(r"\bstalemate\b", re.I)),
    ("indecisive", re.compile(r"\bindecisive\b", re.I)),
    ("disputed", re.compile(r"\bdisputed\b|\bdispute\b", re.I)),
    ("victory", re.compile(r"\bvictory\b", re.I)),
    ("defeat", re.compile(r"\bdefeat\b|\bdefeated\b", re.I)),
]


@dataclass
class PipelineConfig:
    output_dir: Path
    cache_dir: Path
    save_json: bool
    max_root_links: int | None
    max_list_pages: int | None
    max_battle_pages: int | None
    request_timeout: int
    request_sleep: float
    reuse_cache: bool
    category_depth: int = 1
    full_fetch_workers: int = 6
    full_fetch_batch_size: int = 200
    page_task_timeout: int = 180
    fuzzy_merge_threshold: int = 97


class WikipediaClient:
    def __init__(self, config: PipelineConfig) -> None:
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})

    def api_get(self, params: dict[str, Any]) -> dict[str, Any]:
        final_params = {"format": "json", "formatversion": 2, **params}
        cache_key = hashlib.sha1(
            json.dumps(final_params, sort_keys=True, ensure_ascii=True).encode("utf-8")
        ).hexdigest()
        cache_path = self.config.cache_dir / f"{cache_key}.json"
        if self.config.reuse_cache and cache_path.exists():
            return json.loads(cache_path.read_text(encoding="utf-8"))

        last_error: Exception | None = None
        payload: dict[str, Any] | None = None
        for attempt in range(6):
            response = self.session.get(WIKIPEDIA_API, params=final_params, timeout=self.config.request_timeout)
            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                delay = float(retry_after) if retry_after and retry_after.isdigit() else max(1.0, self.config.request_sleep * 10)
                delay *= attempt + 1
                time.sleep(delay)
                last_error = requests.HTTPError(f"429 rate limit for params={final_params}")
                continue
            try:
                response.raise_for_status()
                payload = response.json()
                break
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                time.sleep(max(0.5, self.config.request_sleep * (attempt + 1)))
        if payload is None:
            raise last_error or RuntimeError("Failed to fetch MediaWiki API response.")

        cache_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        if self.config.request_sleep:
            time.sleep(self.config.request_sleep)
        return payload

    def fetch_page_metadata(self, title: str) -> dict[str, Any]:
        query_payload = self.api_get(
            {
                "action": "query",
                "titles": title,
                "redirects": 1,
                "prop": "info|coordinates|pageprops|categories",
                "inprop": "url",
                "cllimit": "max",
            }
        )
        page = query_payload["query"]["pages"][0]
        categories = [cat["title"].replace("Category:", "", 1) for cat in page.get("categories", [])]
        return {
            "title": page.get("title", title),
            "pageid": page.get("pageid"),
            "fullurl": page.get("fullurl") or wikipedia_url_for_title(page.get("title", title)),
            "categories": categories,
            "coordinates": page.get("coordinates", []),
            "pageprops": page.get("pageprops", {}),
        }

    def fetch_page_metadata_batch(self, titles: list[str], chunk_size: int = 25) -> dict[str, dict[str, Any]]:
        results: dict[str, dict[str, Any]] = {}
        for chunk in chunked(titles, chunk_size):
            query_payload = self.api_get(
                {
                    "action": "query",
                    "titles": "|".join(chunk),
                    "redirects": 1,
                    "prop": "info|categories",
                    "inprop": "url",
                    "cllimit": "max",
                }
            )
            query_block = query_payload.get("query", {})
            alias_map: dict[str, set[str]] = defaultdict(set)
            for item in query_block.get("normalized", []):
                alias_map[item.get("to", "")].add(item.get("from", ""))
            for item in query_block.get("redirects", []):
                alias_map[item.get("to", "")].add(item.get("from", ""))
            for page in query_block.get("pages", []):
                page_title = page.get("title", "")
                if not page_title:
                    continue
                categories = [cat["title"].replace("Category:", "", 1) for cat in page.get("categories", [])]
                record = {
                    "title": page_title,
                    "pageid": page.get("pageid"),
                    "fullurl": page.get("fullurl") or wikipedia_url_for_title(page_title),
                    "categories": categories,
                    "coordinates": [],
                    "pageprops": {},
                }
                results[page_title] = record
                for alias in alias_map.get(page_title, set()):
                    if alias:
                        results[alias] = record
            for title in chunk:
                if title not in results:
                    results[title] = {
                        "title": title,
                        "pageid": None,
                        "fullurl": wikipedia_url_for_title(title),
                        "categories": [],
                        "coordinates": [],
                        "pageprops": {},
                    }
        return results

    def fetch_category_members(self, category_title: str) -> list[dict[str, Any]]:
        members: list[dict[str, Any]] = []
        params: dict[str, Any] = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": category_title if category_title.startswith("Category:") else f"Category:{category_title}",
            "cmtype": "page|subcat",
            "cmlimit": "max",
        }
        while True:
            payload = self.api_get(params)
            members.extend(payload.get("query", {}).get("categorymembers", []))
            continuation = payload.get("continue", {})
            if not continuation:
                break
            params.update(continuation)
        return members

    def fetch_page_bundle(self, title: str, include_query_metadata: bool = True) -> dict[str, Any]:
        parse_payload = self.api_get(
            {
                "action": "parse",
                "page": title,
                "redirects": 1,
                "prop": "text|categories|links|displaytitle|sections",
            }
        )
        parse_block = parse_payload.get("parse")
        if not parse_block:
            raise ValueError(f"Unable to parse page: {title}")

        resolved_title = parse_block["title"]
        metadata = {
            "title": resolved_title,
            "pageid": parse_block.get("pageid"),
            "fullurl": wikipedia_url_for_title(resolved_title),
            "categories": parse_categories_from_parse_block(parse_block),
            "coordinates": [],
            "pageprops": {},
        }
        if include_query_metadata:
            metadata.update(self.fetch_page_metadata(resolved_title))
        return {
            "title": metadata["title"],
            "pageid": metadata["pageid"],
            "fullurl": metadata["fullurl"],
            "categories": metadata["categories"] or parse_categories_from_parse_block(parse_block),
            "displaytitle": BeautifulSoup(parse_block.get("displaytitle", resolved_title), "html.parser").get_text(
                " ", strip=True
            ),
            "html": parse_block["text"],
            "sections": parse_block.get("sections", []),
            "links": parse_block.get("links", []),
            "coordinates": metadata["coordinates"],
            "pageprops": metadata["pageprops"],
            "fetched_at": NOW_UTC.isoformat(),
        }

    def fetch_page_wikitext_bundle(self, title: str) -> dict[str, Any]:
        query_payload = self.api_get(
            {
                "action": "query",
                "titles": title,
                "redirects": 1,
                "prop": "revisions|info|coordinates|pageprops|categories",
                "rvslots": "main",
                "rvprop": "content",
                "inprop": "url",
                "cllimit": "max",
            }
        )
        page = query_payload["query"]["pages"][0]
        revisions = page.get("revisions", [])
        wikitext = ""
        if revisions:
            revision = revisions[0]
            slots = revision.get("slots", {})
            main_slot = slots.get("main", {})
            wikitext = main_slot.get("content", "") or revision.get("content", "")
        categories = [cat["title"].replace("Category:", "", 1) for cat in page.get("categories", [])]
        resolved_title = page.get("title", title)
        return {
            "title": resolved_title,
            "pageid": page.get("pageid"),
            "fullurl": page.get("fullurl") or wikipedia_url_for_title(resolved_title),
            "categories": categories,
            "coordinates": page.get("coordinates", []),
            "pageprops": page.get("pageprops", {}),
            "wikitext": wikitext,
            "fetched_at": NOW_UTC.isoformat(),
        }


def wikipedia_url_for_title(title: str) -> str:
    return f"{WIKIPEDIA_BASE}/wiki/{quote(title.replace(' ', '_'))}"


def normalize_space(value: str | None) -> str:
    if not value:
        return ""
    value = re.sub(r"\[\d+\]", "", value)
    value = value.replace("\xa0", " ")
    return re.sub(r"\s+", " ", value).strip()


def slugify(value: str) -> str:
    value = unquote(value).replace("_", " ")
    value = normalize_space(value)
    value = re.sub(r"[^\w\s-]", "", value, flags=re.UNICODE)
    return re.sub(r"[-\s]+", "-", value.lower()).strip("-")


def has_meta_namespace(title: str) -> bool:
    return any(title.startswith(prefix) for prefix in CONTENT_NAMESPACES)


def canonicalize_title_from_href(href: str) -> str:
    path = urlparse(href).path
    if not path.startswith("/wiki/"):
        return ""
    title = path.split("/wiki/", 1)[1]
    title = unquote(title).split("#", 1)[0]
    return title.replace("_", " ")


def parse_categories_from_parse_block(parse_block: dict[str, Any]) -> list[str]:
    categories: list[str] = []
    for category in parse_block.get("categories", []):
        raw_value = category.get("category") or category.get("name") or category.get("title") or ""
        cleaned = normalize_space(str(raw_value)).replace("Category:", "", 1)
        if cleaned:
            categories.append(cleaned)
    return categories


def remove_wikitext_comments_and_refs(text: str) -> str:
    cleaned = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    cleaned = re.sub(r"<ref\b[^>/]*/>", "", cleaned, flags=re.I)
    cleaned = re.sub(r"<ref\b[^>]*>.*?</ref>", "", cleaned, flags=re.I | re.S)
    return cleaned


def extract_balanced_wikitext_block(text: str, start_index: int, open_token: str = "{{", close_token: str = "}}") -> tuple[str, int]:
    depth = 0
    index = start_index
    while index < len(text):
        if text.startswith(open_token, index):
            depth += 1
            index += len(open_token)
            continue
        if text.startswith(close_token, index):
            depth -= 1
            index += len(close_token)
            if depth == 0:
                return text[start_index:index], index
            continue
        index += 1
    return text[start_index:], len(text)


def split_top_level_wikitext(value: str, delimiter: str) -> list[str]:
    parts: list[str] = []
    current: list[str] = []
    template_depth = 0
    link_depth = 0
    index = 0
    while index < len(value):
        if value.startswith("{{", index):
            template_depth += 1
            current.append("{{")
            index += 2
            continue
        if value.startswith("}}", index):
            template_depth = max(0, template_depth - 1)
            current.append("}}")
            index += 2
            continue
        if value.startswith("[[", index):
            link_depth += 1
            current.append("[[")
            index += 2
            continue
        if value.startswith("]]", index):
            link_depth = max(0, link_depth - 1)
            current.append("]]")
            index += 2
            continue
        if value[index] == delimiter and template_depth == 0 and link_depth == 0:
            parts.append("".join(current))
            current = []
            index += 1
            continue
        current.append(value[index])
        index += 1
    parts.append("".join(current))
    return parts


def render_wikitext_template(name: str, params: list[str]) -> str:
    lower = normalize_space(name).lower()
    unnamed = [normalize_space(param) for param in params if normalize_space(param) and "=" not in param]
    if lower.startswith(("flag", "flagicon")):
        return unnamed[0] if unnamed else ""
    if lower in {"plainlist", "flatlist", "ubl", "unbulleted list", "hlist", "bulleted list"}:
        return "\n".join(unnamed)
    if lower in {"small", "nowrap", "nobr", "abbr", "lang", "translit", "ill", "tooltip"}:
        return unnamed[-1] if unnamed else ""
    if "date" in lower and unnamed:
        return " ".join(unnamed[:3])
    if unnamed:
        return " ".join(unnamed[:3])
    return ""


def replace_simple_wikitext_templates(text: str, max_passes: int = 12) -> str:
    template_pattern = re.compile(r"\{\{([^{}]+)\}\}")
    previous = text
    for _ in range(max_passes):
        updated = template_pattern.sub(
            lambda match: render_wikitext_template(
                split_top_level_wikitext(match.group(1), "|")[0],
                split_top_level_wikitext(match.group(1), "|")[1:],
            ),
            previous,
        )
        if updated == previous:
            return updated
        previous = updated
    return previous


def extract_wikilinks_from_wikitext(text: str) -> list[dict[str, str]]:
    links: list[dict[str, str]] = []
    seen: set[str] = set()
    for match in re.finditer(r"\[\[([^|\]#]+)(?:#[^\]|]+)?(?:\|([^\]]+))?\]\]", text):
        title = normalize_space(match.group(1)).replace("_", " ")
        label = normalize_space(match.group(2) or title)
        if not title or has_meta_namespace(title):
            continue
        key = f"{title}|{label}"
        if key in seen:
            continue
        seen.add(key)
        links.append(
            {
                "title": title,
                "text": label,
                "url": wikipedia_url_for_title(title),
            }
        )
    return links


def strip_wikitext_markup(text: str, preserve_newlines: bool = False) -> str:
    working = remove_wikitext_comments_and_refs(text or "")
    working = working.replace("<br />", "\n").replace("<br/>", "\n").replace("<br>", "\n")
    working = re.sub(r"</?(?:small|span|div|includeonly|onlyinclude|noinclude)[^>]*>", "", working, flags=re.I)
    working = replace_simple_wikitext_templates(working)
    working = re.sub(r"\[\[([^|\]#]+)(?:#[^\]|]+)?\|([^\]]+)\]\]", r"\2", working)
    working = re.sub(r"\[\[([^|\]#]+)(?:#[^\]|]+)?\]\]", r"\1", working)
    working = re.sub(r"\[https?://[^\s\]]+\s+([^\]]+)\]", r"\1", working)
    working = re.sub(r"https?://\S+", "", working)
    working = re.sub(r"''+", "", working)
    working = re.sub(r"^\s*[*#;:]+\s*", "", working, flags=re.M)
    working = re.sub(r"\{\|.*?\|\}", "", working, flags=re.S)
    working = re.sub(r"<[^>]+>", "", working)
    if preserve_newlines:
        lines = [normalize_space(line) for line in working.splitlines()]
        lines = [line for line in lines if line]
        return "\n".join(lines)
    return normalize_space(working.replace("\n", " "))


def extract_wikitext_lead(text: str) -> str:
    working = remove_wikitext_comments_and_refs(text)
    while True:
        stripped = working.lstrip()
        if not stripped.startswith("{{"):
            break
        offset = len(working) - len(stripped)
        _block, end_index = extract_balanced_wikitext_block(stripped, 0)
        working = stripped[end_index:]
        if offset:
            working = working
    lead = re.split(r"^\s*=+\s*[^=\n]+\s*=+\s*$", working, maxsplit=1, flags=re.M)[0]
    return strip_wikitext_markup(lead)


def find_infobox_wikitext(text: str) -> str:
    match = re.search(r"\{\{\s*Infobox\b", text, flags=re.I)
    if not match:
        return ""
    block, _end_index = extract_balanced_wikitext_block(text, match.start())
    return block


def parse_wikitext_template_params(template_text: str) -> tuple[str, dict[str, str]]:
    if not template_text:
        return "", {}
    inner = template_text[2:-2] if template_text.startswith("{{") and template_text.endswith("}}") else template_text
    parts = split_top_level_wikitext(inner, "|")
    if not parts:
        return "", {}
    template_name = normalize_space(parts[0])
    params: dict[str, str] = {}
    positional_index = 1
    for part in parts[1:]:
        split_part = split_top_level_wikitext(part, "=")
        if len(split_part) >= 2:
            key = normalize_space(split_part[0]).lower().replace("_", "")
            value = "=".join(split_part[1:])
            params[key] = value.strip()
        else:
            params[str(positional_index)] = part.strip()
            positional_index += 1
    return template_name, params


def build_wikitext_side_values(params: dict[str, str], stems: tuple[str, ...]) -> list[dict[str, Any]]:
    grouped: dict[int, list[str]] = defaultdict(list)
    for key, value in params.items():
        normalized_key = key.lower().replace("_", "")
        for stem in stems:
            match = re.fullmatch(rf"{stem}([123])([a-z]?)", normalized_key)
            if match:
                grouped[int(match.group(1))].append(value)
                break
    rows: list[dict[str, Any]] = []
    for side_number in sorted(grouped):
        side_key = f"side_{chr(96 + side_number)}"
        raw_blocks = [strip_wikitext_markup(value, preserve_newlines=True) for value in grouped[side_number]]
        raw_text = "\n".join(block for block in raw_blocks if block)
        rows.append(
            {
                "side": side_key,
                "raw_text": raw_text,
                "raw_html": "",
                "segments": [line for line in raw_text.splitlines() if line],
                "links": [link for value in grouped[side_number] for link in extract_wikilinks_from_wikitext(value)],
            }
        )
    return rows


def parse_infobox_wikitext(wikitext: str) -> dict[str, Any]:
    template_text = find_infobox_wikitext(wikitext)
    if not template_text:
        return {"present": False, "fields": {}, "template_name": ""}

    template_name, params = parse_wikitext_template_params(template_text)
    fields: dict[str, Any] = {}
    war_name = params.get("partof") or params.get("conflict") or ""
    if war_name:
        fields["war_name"] = strip_wikitext_markup(war_name)
    date_raw = params.get("date") or params.get("dates") or ""
    if date_raw:
        fields["date_raw"] = strip_wikitext_markup(date_raw)
    location_raw = params.get("location") or params.get("place") or ""
    if location_raw:
        fields["location_raw"] = strip_wikitext_markup(location_raw)
    result_raw = params.get("result") or params.get("outcome") or ""
    if result_raw:
        fields["result_raw"] = strip_wikitext_markup(result_raw)
    fields["belligerents"] = build_wikitext_side_values(params, ("combatant", "belligerent"))
    fields["commanders"] = build_wikitext_side_values(params, ("commander",))
    fields["strength"] = build_wikitext_side_values(params, ("strength",))
    fields["casualties"] = build_wikitext_side_values(params, ("casualties", "losses"))
    return {"present": True, "fields": fields, "template_name": template_name}


def chunked(items: list[str], size: int) -> Iterable[list[str]]:
    for index in range(0, len(items), size):
        yield items[index : index + size]


def get_thread_local_client(config: PipelineConfig) -> WikipediaClient:
    client = getattr(THREAD_LOCAL, "wiki_client", None)
    if client is None:
        client = WikipediaClient(config)
        THREAD_LOCAL.wiki_client = client
    return client


def fetch_page_bundle_worker(title: str, config: PipelineConfig) -> tuple[str, dict[str, Any]]:
    client = get_thread_local_client(config)
    return title, client.fetch_page_bundle(title, include_query_metadata=False)


def classify_source_family(title: str) -> str:
    lower = title.lower()
    if re.search(r"\b(before|after)\s+\d{2,4}\b", lower) or re.search(r"\b\d{2,4}\s*[â€“-]\s*\d{2,4}\b", lower):
        return "period_based"
    for family, patterns in SOURCE_FAMILY_PATTERNS:
        if any(pattern in lower for pattern in patterns):
            return family
    if any(keyword in lower for keyword in LIST_KEYWORDS):
        return "list_misc"
    return "general_military"


def is_support_military_page_title(title: str) -> bool:
    lower = title.lower()
    if any(phrase in lower for phrase in SUPPORT_PAGE_TITLE_HINTS):
        return True
    if "order of battle" in lower or "orders of battle" in lower:
        return True
    return False


def is_relevant_category_title(title: str) -> bool:
    lower = normalize_space(title.replace("Category:", "", 1)).lower()
    if not lower:
        return False
    if any(keyword in lower for keyword in CATEGORY_REJECT_KEYWORDS):
        return False
    return any(keyword in lower for keyword in CATEGORY_DISCOVERY_KEYWORDS)


def categorize_fetch_error(exc: Exception) -> str:
    message = normalize_space(str(exc)).lower()
    if "429" in message or "rate limit" in message or "too many requests" in message:
        return "rate_limit"
    if "403" in message or "protected" in message or "permission" in message:
        return "protection"
    if "missingtitle" in message or "unable to parse page" in message or "404" in message:
        return "missing_or_unavailable"
    return "fetch_error"


def extract_internal_links(node: BeautifulSoup) -> list[dict[str, str]]:
    results: list[dict[str, str]] = []
    seen: set[str] = set()
    for anchor in node.select('a[href^="/wiki/"]'):
        href = anchor.get("href", "")
        title = anchor.get("title") or canonicalize_title_from_href(href)
        title = normalize_space(title)
        if not title or title.startswith("Edit section"):
            continue
        if has_meta_namespace(title):
            continue
        key = f"{title}|{href}"
        if key in seen:
            continue
        seen.add(key)
        results.append(
            {
                "title": title,
                "href": urljoin(WIKIPEDIA_BASE, href.split("#", 1)[0]),
                "text": normalize_space(anchor.get_text(" ", strip=True)),
            }
        )
    return results


def page_text(soup: BeautifulSoup) -> str:
    content = soup.select_one("div.mw-parser-output")
    if not content:
        return normalize_space(soup.get_text(" ", strip=True))
    for tag in content.select("table.infobox, div.navbox, table.navbox, div.reflist, span.mw-editsection"):
        tag.decompose()
    return normalize_space(content.get_text(" ", strip=True))


def text_contains_battle_context(text: str) -> bool:
    lower = text.lower()
    return any(term in lower for term in BATTLE_CONTEXT_KEYWORDS)


def top_level_link_count(soup: BeautifulSoup) -> int:
    content = soup.select_one("div.mw-parser-output")
    if not content:
        return 0
    count = 0
    for child in content.find_all(["li", "tr"], recursive=False):
        count += len(child.select('a[href^="/wiki/"]'))
    return count


def is_probable_list_page(title: str, categories: Iterable[str], text: str, soup: BeautifulSoup | None = None) -> bool:
    lower = title.lower()
    category_blob = " | ".join(categories).lower()
    title_match = any(pattern in lower for pattern in LIST_TITLE_PATTERNS)
    if title_match:
        return True
    if any(keyword in lower for keyword in LIST_KEYWORDS) and text_contains_battle_context(lower):
        return True
    if any(keyword in category_blob for keyword in ("lists of battles", "battle-related lists", "military history lists")):
        return True
    if any(keyword in lower for keyword in LIST_KEYWORDS) and text_contains_battle_context(category_blob):
        return True
    if lower.startswith("list of ") and any(term in lower for term in ("military", "war", "battle", "siege", "conflict")):
        return True
    if soup is not None and text_contains_battle_context(text) and top_level_link_count(soup) >= 30:
        return True
    return False


def has_battle_infobox_signature(soup: BeautifulSoup) -> bool:
    infobox = soup.select_one("table.infobox")
    if not infobox:
        return False
    infobox_text = normalize_space(infobox.get_text(" ", strip=True)).lower()
    return any(token in infobox_text for token in ("belligerents", "commanders and leaders", "casualties and losses"))


def classify_page(title: str, categories: Iterable[str], soup: BeautifulSoup, text: str) -> dict[str, Any]:
    lower = title.lower()
    category_blob = " | ".join(categories).lower()
    infobox = soup.select_one("table.infobox")
    infobox_text = normalize_space(infobox.get_text(" ", strip=True)).lower() if infobox else ""
    infobox_classes = " ".join(infobox.get("class", [])) if infobox else ""
    explicit_battle_title = any(keyword in lower for keyword in ("battle", "siege", "skirmish", "raid", "massacre", "engagement", "assault", "landing", "combat"))
    explicit_campaign_title = any(keyword in lower for keyword in ("campaign", "campaigns", "expedition", "expeditions", "theater", "theatre", "front"))
    explicit_operation_title = any(keyword in lower for keyword in ("operation", "operations", "offensive", "offensives"))
    explicit_war_title = any(token in lower for token in WAR_PAGE_KEYWORDS) or any(keyword in lower for keyword in WAR_CONFLICT_TITLE_KEYWORDS)
    reasons: list[str] = []
    battle_score = 0
    campaign_score = 0
    war_score = 0
    biography_score = 0
    list_score = 0
    non_battle_score = 0

    if is_probable_list_page(title, categories, text, soup):
        list_score += 4
        reasons.append("list-page signals")
    if any(keyword in lower for keyword in BATTLE_TITLE_KEYWORDS):
        battle_score += 2
        reasons.append("battle-like title")
    if any(keyword in category_blob for keyword in BATTLE_CATEGORY_KEYWORDS):
        battle_score += 3
        reasons.append("battle categories")
    if has_battle_infobox_signature(soup):
        battle_score += 4
        reasons.append("battle infobox structure")
    if is_support_military_page_title(title):
        non_battle_score += 6
        reasons.append("support/reference military page")
    if any(keyword in lower for keyword in CAMPAIGN_OPERATION_TITLE_KEYWORDS) or any(keyword in category_blob for keyword in CAMPAIGN_CATEGORY_KEYWORDS):
        campaign_score += 3
        reasons.append("campaign signals")
    if explicit_war_title:
        war_score += 3
        reasons.append("war/conflict title")
    if any(token in category_blob for token in WAR_CATEGORY_KEYWORDS) and not has_battle_infobox_signature(soup):
        war_score += 2
        reasons.append("war/conflict categories")
    if any(token in category_blob for token in BIOGRAPHY_CATEGORY_KEYWORDS) or ("births" in category_blob and "deaths" in category_blob):
        biography_score += 4
        reasons.append("biography categories")
    if any(token in lower for token in NON_BATTLE_PAGE_HINTS) and not has_battle_infobox_signature(soup):
        non_battle_score += 3
        reasons.append("non-battle military hints")
    if "person" in infobox_classes or "biography" in infobox_classes or "infobox person" in infobox_text:
        biography_score += 5
    if "infobox military unit" in infobox_text:
        non_battle_score += 4

    operation_signal = any(token in lower for token in ("operation", "operations", "offensive", "offensives")) or any(
        token in category_blob for token in ("operations", "offensives", "military operations")
    )

    if list_score >= max(battle_score, campaign_score, war_score, biography_score, non_battle_score):
        page_type = "list_page"
        accepted = False
    elif biography_score >= max(battle_score, campaign_score, war_score, non_battle_score):
        page_type = "biography_page"
        accepted = False
    elif non_battle_score >= max(battle_score, campaign_score, war_score):
        page_type = "non_battle_military_page"
        accepted = False
    elif explicit_war_title and not explicit_battle_title:
        page_type = "war_conflict_article"
        accepted = True
    elif explicit_operation_title and not explicit_battle_title:
        page_type = "operation_article"
        accepted = True
    elif explicit_campaign_title and not explicit_battle_title:
        page_type = "campaign_article"
        accepted = True
    elif operation_signal and campaign_score >= max(battle_score, war_score, 2):
        page_type = "operation_article"
        accepted = True
    elif has_battle_infobox_signature(soup) or explicit_battle_title or battle_score >= max(campaign_score, war_score, 3):
        page_type = "battle_article"
        accepted = True
    elif campaign_score >= max(battle_score, war_score, 2):
        page_type = "campaign_article"
        accepted = True
    elif war_score >= 2:
        page_type = "war_conflict_article"
        accepted = True
    else:
        page_type = "uncertain_military_page"
        accepted = False

    max_score = max(battle_score, campaign_score, war_score, biography_score, list_score, non_battle_score, 1)
    confidence = round(min(1.0, max_score / 6), 2)
    return {
        "page_type": page_type,
        "accepted": accepted,
        "confidence": confidence,
        "reasons": " | ".join(dict.fromkeys(reasons)) or "weak classification signal",
        "battle_score": battle_score,
    }


def classify_metadata_page(title: str, categories: Iterable[str]) -> dict[str, Any]:
    if is_support_military_page_title(title):
        return {
            "page_type": "non_battle_military_page",
            "accepted": False,
            "confidence": 0.9,
            "reasons": "support/reference military page title",
            "battle_score": 0,
        }
    classification = classify_page(title=title, categories=categories, soup=BeautifulSoup("", "html.parser"), text="")
    if classification["accepted"]:
        return classification
    lower = title.lower()
    if any(keyword in lower for keyword in ("battle", "siege", "skirmish", "raid", "massacre")):
        return {
            "page_type": "battle_article",
            "accepted": True,
            "confidence": max(classification["confidence"], 0.45),
            "reasons": merge_pipe_values(classification["reasons"], "battle-like title only"),
            "battle_score": classification.get("battle_score", 0),
        }
    if any(keyword in lower for keyword in ("war", "conflict", "insurgency", "rebellion")):
        return {
            "page_type": "war_conflict_article",
            "accepted": True,
            "confidence": max(classification["confidence"], 0.4),
            "reasons": merge_pipe_values(classification["reasons"], "war/conflict-like title only"),
            "battle_score": classification.get("battle_score", 0),
        }
    if any(keyword in lower for keyword in ("campaign", "operation", "offensive", "expedition")):
        page_type = "operation_article" if any(keyword in lower for keyword in ("operation", "offensive")) else "campaign_article"
        return {
            "page_type": page_type,
            "accepted": True,
            "confidence": max(classification["confidence"], 0.4),
            "reasons": merge_pipe_values(classification["reasons"], "campaign/operation-like title only"),
            "battle_score": classification.get("battle_score", 0),
        }
    return classification


def infer_battle_type(title: str, categories: Iterable[str]) -> str:
    title_blob = title.lower()
    category_blob = " ".join(categories).lower()
    blob = f"{title_blob} {category_blob}"
    if "siege" in title_blob or "siege" in category_blob:
        return "siege"
    if "naval battle" in blob or "naval" in category_blob or ("sea" in title_blob and "battle" in title_blob):
        return "naval_battle"
    if any(token in title_blob for token in ("operation", "offensive")):
        return "operation"
    if any(token in title_blob for token in ("campaign", "theater", "theatre", "front", "expedition")):
        return "campaign_like_engagement"
    if "raid" in blob:
        return "raid"
    if "rebellion" in blob or "revolt" in blob or "uprising" in blob:
        return "uprising"
    if "skirmish" in blob:
        return "skirmish"
    if "massacre" in blob:
        return "massacre"
    if any(token in title_blob for token in ("battle", "engagement", "landing", "assault", "combat")):
        return "land_battle"
    if " war" in f" {title_blob}" or "wars" in title_blob or "conflict" in title_blob or "insurgency" in title_blob:
        return "war_conflict"
    return "land_battle"


def summarize_text_segments(cell: BeautifulSoup) -> list[str]:
    raw = cell.get_text("\n", strip=True)
    parts = [normalize_space(piece) for piece in raw.splitlines()]
    return [part for part in parts if part]


def extract_link_targets(cell: BeautifulSoup) -> list[dict[str, str]]:
    targets = []
    seen: set[str] = set()
    for anchor in cell.select('a[href^="/wiki/"]'):
        if anchor.find_parent("span", class_="flagicon"):
            continue
        if anchor.find("img"):
            continue
        href = anchor.get("href", "")
        title = anchor.get("title") or canonicalize_title_from_href(href)
        title = normalize_space(title)
        if not title or has_meta_namespace(title):
            continue
        key = f"{title}|{href}"
        if key in seen:
            continue
        seen.add(key)
        targets.append(
            {
                "title": title,
                "text": normalize_space(anchor.get_text(" ", strip=True)) or title,
                "url": urljoin(WIKIPEDIA_BASE, href.split("#", 1)[0]),
            }
        )
    return targets


def parse_side_values(cells: list[BeautifulSoup]) -> list[dict[str, Any]]:
    sides: list[dict[str, Any]] = []
    for index, cell in enumerate(cells, start=1):
        sides.append(
            {
                "side": f"side_{chr(96 + index)}",
                "raw_text": normalize_space(cell.get_text("\n", strip=True)),
                "raw_html": str(cell),
                "segments": summarize_text_segments(cell),
                "links": extract_link_targets(cell),
            }
        )
    return sides


def parse_infobox(soup: BeautifulSoup) -> dict[str, Any]:
    table = soup.select_one("table.infobox")
    if not table:
        return {"present": False, "fields": {}}

    fields: dict[str, Any] = {}
    current_section: str | None = None
    for row in table.find_all("tr"):
        cells = row.find_all(["th", "td"], recursive=False)
        if not cells:
            cells = row.find_all(["th", "td"])
        if not cells:
            continue
        texts = [normalize_space(cell.get_text(" ", strip=True)) for cell in cells]
        if len(cells) == 1:
            header_text = texts[0].lower()
            if header_text.startswith("part of "):
                fields["war_name"] = normalize_space(re.sub(r"^part of\s+", "", texts[0], flags=re.I))
                continue
            if header_text in SECTION_HEADERS:
                current_section = SECTION_HEADERS[header_text]
            continue

        header = row.find("th", recursive=False)
        data_cells = row.find_all("td", recursive=False)
        if header and data_cells:
            label = normalize_space(header.get_text(" ", strip=True)).lower()
            mapped = ROW_LABEL_MAP.get(label)
            if mapped in {"belligerents", "commanders", "strength", "casualties"}:
                fields[mapped] = parse_side_values(data_cells)
                current_section = None
                continue
            if mapped:
                fields[mapped] = normalize_space(" | ".join(cell.get_text(" ", strip=True) for cell in data_cells))
                current_section = None
                continue

        if current_section in {"belligerents", "commanders", "strength", "casualties"}:
            td_cells = row.find_all("td", recursive=False)
            if td_cells:
                fields[current_section] = parse_side_values(td_cells)
                current_section = None

    return {"present": True, "fields": fields}


def parse_year_and_dates(date_raw: str) -> dict[str, Any]:
    date_raw = normalize_space(date_raw)
    if not date_raw:
        return {
            "date_raw": "",
            "start_date": "",
            "end_date": "",
            "year": "",
            "century": "",
            "date_parse_confidence": 0.0,
        }

    cleaned = re.sub(r"\([^)]*\)", "", date_raw)
    year_matches = re.findall(r"(?<!\d)(\d{3,4})(?!\d)", cleaned)
    explicit_start_year = int(year_matches[0]) if year_matches else ""
    explicit_end_year = int(year_matches[-1]) if year_matches else explicit_start_year
    parts = re.split(r"\s+to\s+|[–—-]", cleaned, maxsplit=1)
    start_candidate = normalize_space(parts[0]) if parts else cleaned
    end_candidate = normalize_space(parts[1]) if len(parts) > 1 else start_candidate
    settings = {"PREFER_DAY_OF_MONTH": "first", "DATE_ORDER": "DMY"}
    start_dt = dateparser.parse(start_candidate, settings=settings)
    end_dt = dateparser.parse(end_candidate, settings=settings)
    if explicit_start_year and str(explicit_start_year) not in start_candidate:
        start_dt = dateparser.parse(f"{start_candidate} {explicit_start_year}", settings=settings) or start_dt
    if explicit_end_year and str(explicit_end_year) not in end_candidate:
        end_dt = dateparser.parse(f"{end_candidate} {explicit_end_year}", settings=settings) or end_dt
    start_date = start_dt.date().isoformat() if start_dt else ""
    end_date = end_dt.date().isoformat() if end_dt else ""
    parsed_year = explicit_start_year or (start_dt.year if start_dt else "")
    century = math.floor((int(parsed_year) - 1) / 100) + 1 if parsed_year else ""
    confidence = 0.25
    if explicit_start_year:
        confidence += 0.25
    if start_date:
        confidence += 0.25
    if end_date:
        confidence += 0.25
    return {
        "date_raw": date_raw,
        "start_date": start_date,
        "end_date": end_date,
        "year": parsed_year,
        "century": century,
        "date_parse_confidence": round(confidence, 2),
    }


def repair_year_from_title_context(title: str, parsed_year: Any) -> Any:
    title = normalize_space(title)
    if not title:
        return parsed_year
    try:
        parsed_year_int = int(parsed_year) if parsed_year not in {"", None} else None
    except (TypeError, ValueError):
        parsed_year_int = None

    title_year_matches = [int(value) for value in re.findall(r"\((\d{3,4})\)", title)]
    if parsed_year_int is None:
        if len(title_year_matches) == 1:
            return title_year_matches[0]
        return parsed_year

    if parsed_year_int > 2100 and len(title_year_matches) == 1:
        title_year = title_year_matches[0]
        if 1 <= title_year <= 2100:
            return title_year
    return parsed_year


def normalize_result(result_raw: str) -> tuple[str, str]:
    result_raw = normalize_space(result_raw)
    if not result_raw:
        return "", "unknown"
    result_type = "unknown"
    for candidate_type, pattern in RESULT_PATTERNS:
        if pattern.search(result_raw):
            result_type = candidate_type
            break
    if result_type.endswith("victory"):
        result_normalized = "Victory"
    elif result_type == "defeat":
        result_normalized = "Defeat"
    elif result_type in {"draw", "stalemate", "indecisive", "disputed"}:
        result_normalized = result_type.replace("_", " ").title()
    else:
        result_normalized = "Unknown"
    return result_normalized, result_type


def parse_numeric_range(raw_value: str) -> dict[str, Any]:
    raw_value = normalize_space(raw_value)
    if not raw_value:
        return {"raw": "", "min": "", "max": "", "midpoint": "", "confidence": 0.0}
    numbers = [int(match.replace(",", "")) for match in re.findall(r"\b\d[\d,]*\b", raw_value)]
    if not numbers:
        return {"raw": raw_value, "min": "", "max": "", "midpoint": "", "confidence": 0.0}
    min_value = min(numbers)
    max_value = max(numbers)
    midpoint = round((min_value + max_value) / 2) if len(numbers) >= 2 else min_value
    confidence = 0.8 if len(numbers) <= 2 else 0.55
    return {
        "raw": raw_value,
        "min": min_value,
        "max": max_value,
        "midpoint": midpoint,
        "confidence": confidence,
    }


def clean_name(raw_name: str) -> str:
    name = normalize_space(raw_name)
    name = re.sub(r"\([^)]*\)", "", name)
    name = re.sub(r"\[[^\]]+\]", "", name)
    name = COMMANDER_PREFIX_PATTERN.sub("", name)
    name = re.sub(r"[†‡#*?]+", "", name)
    name = re.sub(r"\b(c\.|ca\.)\b", "", name, flags=re.I)
    return normalize_space(name)


def is_generic_commander_value(name: str) -> bool:
    lower = clean_name(name).lower()
    if not lower:
        return True
    if len(re.findall(r"[a-zà-öø-ÿ]", lower)) < 2:
        return True
    if lower in GENERIC_COMMANDER_TOKENS:
        return True
    if any(keyword in lower for keyword in NON_PERSON_COMMANDER_KEYWORDS):
        return True
    if lower.endswith(":") or lower in {"list", "left flank", "right flank", "centre", "center", "other command", "wia"}:
        return True
    if any(char.isdigit() for char in lower) and not re.search(r"\b(i|ii|iii|iv|v|vi|vii|viii|ix|x)\b", lower):
        return True
    if len(lower.split()) == 1 and lower in {"attacker", "defender"}:
        return True
    return False


def split_raw_commander_text(raw_text: str) -> list[str]:
    if not raw_text:
        return []
    working = raw_text.replace("•", "\n").replace(";", "\n")
    parts = [clean_name(part) for part in working.splitlines()]
    parts = [part for part in parts if part]
    if len(parts) == 1 and "," in parts[0]:
        comma_parts = [clean_name(part) for part in parts[0].split(",")]
        if len(comma_parts) > 1:
            parts = [part for part in comma_parts if part]
    deduped: list[str] = []
    seen: set[str] = set()
    for part in parts:
        key = part.lower()
        if key not in seen:
            seen.add(key)
            deduped.append(part)
    return deduped


def extract_commander_entries(side_cell: dict[str, Any]) -> list[dict[str, str]]:
    linked_names = []
    for link in side_cell.get("links", []):
        candidate = clean_name(link["title"])
        if not candidate or is_generic_commander_value(candidate):
            continue
        linked_names.append(
            {
                "raw_name": candidate,
                "normalized_name": candidate,
                "wikipedia_url": link["url"],
                "identity_confidence": "high",
                "identity_resolution_method": "linked_article",
            }
        )
    if linked_names:
        return linked_names

    raw_names = split_raw_commander_text(side_cell.get("raw_text", ""))
    entries = []
    for raw_name in raw_names:
        if is_generic_commander_value(raw_name):
            continue
        entries.append(
            {
                "raw_name": raw_name,
                "normalized_name": clean_name(raw_name),
                "wikipedia_url": "",
                "identity_confidence": "medium",
                "identity_resolution_method": "cleaned_raw_text",
            }
        )
    return entries


def split_raw_commander_text(raw_text: str) -> list[str]:
    if not raw_text:
        return []
    working = raw_text.replace("â€¢", "\n").replace("•", "\n").replace(";", "\n").replace(" / ", "\n")
    working = re.sub(r"\s+\band\b\s+", "\n", working, flags=re.I)
    parts = [clean_name(part) for part in working.splitlines()]
    parts = [part for part in parts if part]
    if len(parts) == 1 and "," in parts[0]:
        comma_parts = [clean_name(part) for part in parts[0].split(",")]
        if len(comma_parts) > 1:
            parts = [part for part in comma_parts if part]
    deduped: list[str] = []
    seen: set[str] = set()
    for part in parts:
        key = part.lower()
        if key not in seen:
            seen.add(key)
            deduped.append(part)
    return deduped


def link_matches_segment(link: dict[str, str], segment: str) -> bool:
    segment_lower = segment.lower()
    link_names = {clean_name(link.get("title", "")).lower(), clean_name(link.get("text", "")).lower()}
    return any(name and name in segment_lower for name in link_names)


def commander_segments_from_cell(side_cell: dict[str, Any]) -> list[str]:
    segments = [clean_name(segment) for segment in side_cell.get("segments", []) if clean_name(segment)]
    if not segments:
        segments = split_raw_commander_text(side_cell.get("raw_text", ""))
    cleaned: list[str] = []
    seen: set[str] = set()
    for segment in segments:
        if is_generic_commander_value(segment):
            continue
        key = segment.lower()
        if key not in seen:
            seen.add(key)
            cleaned.append(segment)
    return cleaned


def extract_commander_entries(side_cell: dict[str, Any]) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    seen: set[str] = set()
    available_links = side_cell.get("links", [])
    for segment in commander_segments_from_cell(side_cell):
        matching_links = [link for link in available_links if link_matches_segment(link, segment)]
        if matching_links:
            for link in matching_links:
                normalized_name = clean_name(link["title"])
                raw_name = clean_name(link.get("text") or segment or link["title"])
                if not normalized_name or is_generic_commander_value(normalized_name):
                    continue
                key = f"{normalized_name.lower()}|{link['url']}"
                if key in seen:
                    continue
                seen.add(key)
                entries.append(
                    {
                        "raw_name": raw_name,
                        "normalized_name": normalized_name,
                        "wikipedia_url": link["url"],
                        "identity_confidence": "high",
                        "identity_resolution_method": "linked_article",
                    }
                )
        elif not available_links:
            normalized_name = clean_name(segment)
            if not normalized_name or is_generic_commander_value(normalized_name):
                continue
            key = f"{normalized_name.lower()}|"
            if key in seen:
                continue
            seen.add(key)
            entries.append(
                {
                    "raw_name": segment,
                    "normalized_name": normalized_name,
                    "wikipedia_url": "",
                    "identity_confidence": "medium",
                    "identity_resolution_method": "cleaned_segment_text",
                }
            )
    if entries:
        return entries

    for raw_name in split_raw_commander_text(side_cell.get("raw_text", "")):
        if is_generic_commander_value(raw_name):
            continue
        entries.append(
            {
                "raw_name": raw_name,
                "normalized_name": clean_name(raw_name),
                "wikipedia_url": "",
                "identity_confidence": "medium",
                "identity_resolution_method": "cleaned_raw_text",
            }
        )
    return entries


def build_source_record(
    title: str,
    url: str,
    page_type: str,
    crawl_parent: str,
    extraction_status: str,
    notes: str = "",
    discovery_root: str = "",
    source_family: str = "",
) -> dict[str, Any]:
    return {
        "page_title": title,
        "url": url,
        "page_type": page_type,
        "crawl_parent": crawl_parent,
        "discovery_root": discovery_root,
        "source_family": source_family,
        "extraction_status": extraction_status,
        "timestamp_utc": NOW_UTC.isoformat(),
        "notes": notes,
    }


def issue_record(
    page_title: str,
    source_url: str,
    issue_type: str,
    field_name: str,
    severity: str,
    message: str,
    raw_value: str = "",
) -> dict[str, Any]:
    return {
        "timestamp_utc": NOW_UTC.isoformat(),
        "page_title": page_title,
        "source_url": source_url,
        "issue_type": issue_type,
        "field_name": field_name,
        "severity": severity,
        "message": message,
        "raw_value": raw_value,
    }


def build_category_candidate_row(
    title: str,
    url: str,
    category_title: str,
    discovery_root: str,
    category_root: str,
) -> dict[str, Any]:
    return {
        "candidate_title": title,
        "candidate_url": url,
        "list_page_origin": category_title,
        "parent_source": category_title,
        "discovery_root": discovery_root,
        "source_family": "category_based",
        "anchor_text": "",
        "candidate_score": 2,
        "candidate_reason": f"categorymember from {category_root}",
    }


def extract_candidate_battle_links(
    list_title: str,
    soup: BeautifulSoup,
    discovery_root: str,
    source_family: str,
) -> list[dict[str, str]]:
    candidates: list[dict[str, str]] = []
    seen: set[str] = set()
    containers = soup.select(
        "div.mw-parser-output > ul > li, "
        "div.mw-parser-output > ol > li, "
        "div.mw-parser-output > table.wikitable tr, "
        "div.mw-parser-output > table.sortable tr, "
        "div.mw-parser-output > table tr, "
        "div.mw-parser-output > div.columns li"
    )
    for container in containers:
        links = extract_internal_links(container)
        if not links:
            continue
        for link in links:
            title = link["title"]
            accepted, reason, score = classify_candidate_link(link)
            if not accepted:
                continue
            key = title.lower()
            if key in seen:
                continue
            seen.add(key)
            candidates.append(
                {
                    "candidate_title": title,
                    "candidate_url": link["href"],
                    "list_page_origin": list_title,
                    "parent_source": list_title,
                    "discovery_root": discovery_root,
                    "source_family": source_family,
                    "anchor_text": link["text"],
                    "candidate_score": score,
                    "candidate_reason": reason,
                }
            )
    return candidates


def choose_side_result(side_key: str, result_type: str, result_raw: str, belligerents: dict[str, str]) -> str:
    if not result_type or result_type == "unknown":
        return "unknown"
    if result_type in {"draw", "stalemate", "indecisive", "disputed"}:
        return result_type
    result_lower = result_raw.lower()
    winner_side = ""
    for current_side, belligerent in belligerents.items():
        tokens = [token.strip() for token in re.split(r"[,/|]", belligerent) if token.strip()]
        for token in tokens:
            token_lower = token.lower()
            if len(token_lower) > 3 and token_lower in result_lower:
                winner_side = current_side
                break
        if winner_side:
            break
    if winner_side:
        return "victory" if side_key == winner_side else "defeat"
    return "unknown"


def extract_lead_paragraphs(soup: BeautifulSoup, limit: int = 3) -> list[str]:
    content = soup.select_one("div.mw-parser-output")
    if not content:
        return []
    paragraphs: list[str] = []
    for child in content.find_all(recursive=False):
        if child.name == "p":
            text = normalize_space(child.get_text(" ", strip=True))
            if text:
                paragraphs.append(text)
            if len(paragraphs) >= limit:
                break
        elif paragraphs and child.name in {"h2", "h3"}:
            break
    return paragraphs


def first_result_sentence(text: str) -> str:
    for sentence in re.split(r"(?<=[.!?])\s+", text):
        lower = sentence.lower()
        if any(keyword in lower for keyword in RESULT_KEYWORDS):
            return normalize_space(sentence)
    return ""


def fallback_result_from_text(soup: BeautifulSoup) -> str:
    lead_text = " ".join(extract_lead_paragraphs(soup, limit=4))
    result_sentence = first_result_sentence(lead_text)
    if result_sentence:
        return result_sentence
    content_text = page_text(BeautifulSoup(str(soup), "html.parser"))
    return first_result_sentence(content_text[:2000])


def fallback_date_from_text(title: str, soup: BeautifulSoup) -> str:
    lead_text = " ".join(extract_lead_paragraphs(soup, limit=3))
    if DATE_HINT_PATTERN.search(lead_text):
        return DATE_HINT_PATTERN.search(lead_text).group(0)
    search_hits = search_dates(lead_text, settings={"DATE_ORDER": "DMY"}) or []
    for raw_value, _parsed in search_hits:
        if re.search(r"\d{3,4}", raw_value):
            return normalize_space(raw_value)
    title_yearish = re.match(r"^(\d{3,4}(?:[–-]\d{2,4})?)", title)
    if title_yearish:
        return title_yearish.group(1)
    return ""


def classify_candidate_link(link: dict[str, str]) -> tuple[bool, str, int]:
    title = link["title"]
    lower = title.lower()
    score = 0
    reasons: list[str] = []
    if has_meta_namespace(title):
        return False, "meta namespace", 0
    if any(keyword in lower for keyword in LIST_KEYWORDS):
        return False, "list/meta title", 0
    if is_support_military_page_title(title):
        return False, "support/reference military page", 0
    if re.fullmatch(r"\d{3,4}(?:\s*bc|\s*bce|\s*ce)?", lower):
        return False, "year-only page", 0
    if any(keyword in lower for keyword in BROAD_MILITARY_TITLE_KEYWORDS):
        score += 3
        reasons.append("military-like title")
    if " of " in lower and any(keyword in lower for keyword in ("battle", "siege", "raid", "skirmish", "operation", "war", "campaign", "conflict")):
        score += 2
        reasons.append("military naming pattern")
    anchor_text = link.get("text", "").lower()
    if anchor_text and any(keyword in anchor_text for keyword in BROAD_MILITARY_TITLE_KEYWORDS):
        score += 1
        reasons.append("military-like anchor")
    if re.search(r"\bwar\b|\bcampaign\b|\bconflict\b|\boffensive\b", lower):
        score += 1
        reasons.append("war/campaign pattern")
    if score == 0 and re.match(r"^\d{3,4}", title):
        score += 1
        reasons.append("dated engagement title")
    return score >= 1, " | ".join(reasons) or "weak candidate signal", score


def build_battle_rows(
    page: dict[str, Any],
    origin_rows: list[dict[str, Any]],
    config: PipelineConfig,
    issues: list[dict[str, Any]],
    json_dir: Path,
    client: WikipediaClient,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None, list[dict[str, Any]], dict[str, Any]]:
    title = page["title"]
    url = page["fullurl"]
    soup = BeautifulSoup(page["html"], "html.parser")
    body_text = page_text(soup)
    classification = classify_page(title, page["categories"], soup, body_text)
    origins = sorted({row.get("list_page_origin", "") for row in origin_rows if row.get("list_page_origin")})
    parent_sources = sorted({row.get("parent_source", "") for row in origin_rows if row.get("parent_source")})
    discovery_roots = sorted({row.get("discovery_root", "") for row in origin_rows if row.get("discovery_root")})
    source_families = sorted({row.get("source_family", "") for row in origin_rows if row.get("source_family")})
    if not classification["accepted"]:
        issues.append(
            issue_record(
                title,
                url,
                "rejected_candidate",
                "page_type",
                "medium",
                f"Excluded as {classification['page_type']}: {classification['reasons']}.",
            )
        )
        return None, None, [], classification

    if not page.get("pageid"):
        try:
            metadata = client.fetch_page_metadata(title)
            page["title"] = metadata.get("title", page["title"])
            page["pageid"] = metadata.get("pageid")
            page["fullurl"] = metadata.get("fullurl", page["fullurl"])
            page["categories"] = metadata.get("categories") or page.get("categories", [])
            page["coordinates"] = metadata.get("coordinates", [])
            page["pageprops"] = metadata.get("pageprops", {})
            url = page["fullurl"]
        except Exception as exc:  # noqa: BLE001
            issues.append(
                issue_record(
                    title,
                    url,
                    "metadata_fetch_error",
                    "page_metadata",
                    "medium",
                    f"Failed to fetch query metadata after battle-page acceptance: {exc}",
                )
            )

    infobox = parse_infobox(soup)
    fields = infobox["fields"]
    coords = page.get("coordinates", [])
    coord = coords[0] if coords else {}
    battle_type = infer_battle_type(title, page["categories"])
    date_raw = fields.get("date_raw", "")
    if not date_raw:
        date_raw = fallback_date_from_text(title, soup)
    result_raw = fields.get("result_raw", "")
    if not result_raw:
        result_raw = fallback_result_from_text(soup)
    date_info = parse_year_and_dates(date_raw)
    result_normalized, result_type = normalize_result(result_raw)

    belligerent_sides = fields.get("belligerents", [])
    commander_sides = fields.get("commanders", [])
    strength_sides = fields.get("strength", [])
    casualty_sides = fields.get("casualties", [])

    belligerent_map = {entry["side"]: entry["raw_text"] for entry in belligerent_sides}
    commander_map = {entry["side"]: entry["raw_text"] for entry in commander_sides}
    strength_map = {entry["side"]: entry["raw_text"] for entry in strength_sides}
    casualty_map = {entry["side"]: entry["raw_text"] for entry in casualty_sides}

    extraction_score = 0.0
    extraction_score += 0.2 if infobox["present"] else 0.0
    extraction_score += 0.2 if result_raw else 0.0
    extraction_score += 0.2 if date_raw else 0.0
    extraction_score += 0.2 if commander_sides else 0.0
    extraction_score += 0.2 if belligerent_sides else 0.0

    battle_id = f"battle_{page['pageid']}" if page.get("pageid") else f"battle_title_{hashlib.sha1(title.encode('utf-8')).hexdigest()[:12]}"
    battle_name = page.get("displaytitle") or title
    battle_name_normalized = re.sub(r"\s*\([^)]*\)$", "", battle_name).strip()
    categories_joined = " | ".join(page["categories"])

    raw_row = {
        "battle_id": battle_id,
        "battle_name": battle_name,
        "wikipedia_title": title,
        "source_url": url,
        "date_raw": date_raw,
        "war_name_raw": fields.get("war_name", ""),
        "location_raw": fields.get("location_raw", ""),
        "result_raw": result_raw,
        "belligerent_1_raw": belligerent_map.get("side_a", ""),
        "belligerent_2_raw": belligerent_map.get("side_b", ""),
        "belligerent_3_raw": belligerent_map.get("side_c", ""),
        "commander_side_a_raw": commander_map.get("side_a", ""),
        "commander_side_b_raw": commander_map.get("side_b", ""),
        "commander_side_c_raw": commander_map.get("side_c", ""),
        "strength_side_a_raw": strength_map.get("side_a", ""),
        "strength_side_b_raw": strength_map.get("side_b", ""),
        "strength_side_c_raw": strength_map.get("side_c", ""),
        "casualties_side_a_raw": casualty_map.get("side_a", ""),
        "casualties_side_b_raw": casualty_map.get("side_b", ""),
        "casualties_side_c_raw": casualty_map.get("side_c", ""),
        "page_type": classification["page_type"],
        "page_type_confidence": classification["confidence"],
        "classification_notes": classification["reasons"],
        "acceptance_reason": classification["reasons"],
        "battle_type": battle_type,
        "infobox_present": infobox["present"],
        "text_length": len(body_text),
        "categories": categories_joined,
        "list_page_origin": " | ".join(origins),
        "parent_list_page": " | ".join(parent_sources),
        "discovery_root": " | ".join(discovery_roots),
        "source_family": " | ".join(source_families),
        "extraction_confidence": round(extraction_score, 2),
        "notes": "",
    }

    clean_row = {
        "battle_id": battle_id,
        "battle_name": battle_name,
        "battle_name_normalized": battle_name_normalized,
        "wikipedia_title": title,
        "source_url": url,
        **date_info,
        "war_name": fields.get("war_name", ""),
        "campaign_name": "",
        "location_raw": fields.get("location_raw", ""),
        "location_normalized": fields.get("location_raw", ""),
        "latitude": coord.get("lat", ""),
        "longitude": coord.get("lon", ""),
        "present_day_country": "",
        "result_raw": result_raw,
        "result_normalized": result_normalized,
        "result_type": result_type,
        "belligerent_1_raw": belligerent_map.get("side_a", ""),
        "belligerent_2_raw": belligerent_map.get("side_b", ""),
        "belligerent_3_raw": belligerent_map.get("side_c", ""),
        "commander_side_a_raw": commander_map.get("side_a", ""),
        "commander_side_b_raw": commander_map.get("side_b", ""),
        "commander_side_c_raw": commander_map.get("side_c", ""),
        "strength_side_a_raw": strength_map.get("side_a", ""),
        "strength_side_b_raw": strength_map.get("side_b", ""),
        "strength_side_c_raw": strength_map.get("side_c", ""),
        "casualties_side_a_raw": casualty_map.get("side_a", ""),
        "casualties_side_b_raw": casualty_map.get("side_b", ""),
        "casualties_side_c_raw": casualty_map.get("side_c", ""),
        "strength_side_a_min": parse_numeric_range(strength_map.get("side_a", "")).get("min", ""),
        "strength_side_a_max": parse_numeric_range(strength_map.get("side_a", "")).get("max", ""),
        "strength_side_b_min": parse_numeric_range(strength_map.get("side_b", "")).get("min", ""),
        "strength_side_b_max": parse_numeric_range(strength_map.get("side_b", "")).get("max", ""),
        "casualties_side_a_min": parse_numeric_range(casualty_map.get("side_a", "")).get("min", ""),
        "casualties_side_a_max": parse_numeric_range(casualty_map.get("side_a", "")).get("max", ""),
        "casualties_side_b_min": parse_numeric_range(casualty_map.get("side_b", "")).get("min", ""),
        "casualties_side_b_max": parse_numeric_range(casualty_map.get("side_b", "")).get("max", ""),
        "page_type": classification["page_type"],
        "page_type_confidence": classification["confidence"],
        "classification_notes": classification["reasons"],
        "acceptance_reason": classification["reasons"],
        "battle_type": battle_type,
        "infobox_present": infobox["present"],
        "text_length": len(body_text),
        "categories": categories_joined,
        "list_page_origin": " | ".join(origins),
        "parent_list_page": " | ".join(parent_sources),
        "discovery_root": " | ".join(discovery_roots),
        "source_family": " | ".join(source_families),
        "extraction_confidence": round(extraction_score, 2),
        "notes": "",
    }

    commanders_rows: list[dict[str, Any]] = []
    all_side_commanders: dict[str, list[str]] = defaultdict(list)
    for side_entry in commander_sides:
        commander_entries = extract_commander_entries(side_entry)
        all_side_commanders[side_entry["side"]] = [entry["raw_name"] for entry in commander_entries]

    for side_entry in commander_sides:
        side_key = side_entry["side"]
        commander_entries = extract_commander_entries(side_entry)
        if not commander_entries:
            issues.append(
                issue_record(
                    title,
                    url,
                    "missing_commanders",
                    "commanders",
                    "medium",
                    f"No parseable commanders extracted for {side_key}.",
                    side_entry.get("raw_text", ""),
                )
            )
            continue
        for commander in commander_entries:
            opposing_names = []
            for other_side, names in all_side_commanders.items():
                if other_side != side_key:
                    opposing_names.extend(names)
            side_result = choose_side_result(side_key, result_type, result_raw, belligerent_map)
            commanders_rows.append(
                {
                    "battle_id": battle_id,
                    "battle_name": battle_name,
                    "year": date_info.get("year", ""),
                    "war_name": fields.get("war_name", ""),
                    "commander_name_raw": commander["raw_name"],
                    "commander_name_normalized": commander["normalized_name"],
                    "commander_wikipedia_url": commander["wikipedia_url"],
                    "side": side_key,
                    "belligerent": belligerent_map.get(side_key, ""),
                    "battle_result_for_commander": side_result,
                    "role_in_battle": "",
                    "opposing_commander_names_raw": " | ".join(opposing_names),
                    "location_normalized": fields.get("location_raw", ""),
                    "strength_side_raw": strength_map.get(side_key, ""),
                    "strength_enemy_raw": " | ".join(
                        value for key, value in strength_map.items() if key != side_key and value
                    ),
                    "casualties_side_raw": casualty_map.get(side_key, ""),
                    "casualties_enemy_raw": " | ".join(
                        value for key, value in casualty_map.items() if key != side_key and value
                    ),
                    "source_url": url,
                    "parse_notes": "",
                    "identity_confidence": commander["identity_confidence"],
                }
            )

    if not date_raw:
        issues.append(issue_record(title, url, "missing_field", "date_raw", "medium", "Battle page is missing a parseable date field."))
    if not result_raw:
        issues.append(issue_record(title, url, "missing_field", "result_raw", "medium", "Battle page is missing a parseable result field."))
    if len(commanders_rows) > 16:
        issues.append(
            issue_record(
                title,
                url,
                "suspicious_commander_count",
                "commanders",
                "low",
                "Battle produced an unusually high commander count and should be reviewed.",
                str(len(commanders_rows)),
            )
        )

    if config.save_json:
        snapshot = {
            "page": page,
            "classification": classification,
            "raw_row": raw_row,
            "clean_row": clean_row,
            "commanders_rows": commanders_rows,
        }
        (json_dir / f"{slugify(title)}.json").write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")

    return raw_row, clean_row, commanders_rows, classification


def build_battle_rows_from_wikitext(
    page: dict[str, Any],
    origin_rows: list[dict[str, Any]],
    config: PipelineConfig,
    issues: list[dict[str, Any]],
    json_dir: Path,
    client: WikipediaClient,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None, list[dict[str, Any]], dict[str, Any]]:
    title = page["title"]
    url = page["fullurl"]
    wikitext = page.get("wikitext", "") or ""
    lead_text = extract_wikitext_lead(wikitext)
    body_text = strip_wikitext_markup(wikitext)
    classification = classify_metadata_page(title, page.get("categories", []))
    origins = sorted({row.get("list_page_origin", "") for row in origin_rows if row.get("list_page_origin")})
    parent_sources = sorted({row.get("parent_source", "") for row in origin_rows if row.get("parent_source")})
    discovery_roots = sorted({row.get("discovery_root", "") for row in origin_rows if row.get("discovery_root")})
    source_families = sorted({row.get("source_family", "") for row in origin_rows if row.get("source_family")})
    if not classification["accepted"]:
        issues.append(
            issue_record(
                title,
                url,
                "rejected_candidate",
                "page_type",
                "medium",
                f"Excluded as {classification['page_type']}: {classification['reasons']}.",
            )
        )
        return None, None, [], classification

    infobox = parse_infobox_wikitext(wikitext)
    fields = infobox["fields"]
    coords = page.get("coordinates", [])
    coord = coords[0] if coords else {}
    battle_type = infer_battle_type(title, page.get("categories", []))
    date_raw = fields.get("date_raw", "")
    if not date_raw and lead_text:
        if DATE_HINT_PATTERN.search(lead_text):
            date_raw = DATE_HINT_PATTERN.search(lead_text).group(0)
        else:
            search_hits = search_dates(lead_text, settings={"DATE_ORDER": "DMY"}) or []
            for raw_value, _parsed in search_hits:
                if re.search(r"\d{3,4}", raw_value):
                    date_raw = normalize_space(raw_value)
                    break
    if not date_raw:
        title_yearish = re.match(r"^(\d{3,4}(?:[–-]\d{2,4})?)", title)
        if title_yearish:
            date_raw = title_yearish.group(1)
    result_raw = fields.get("result_raw", "")
    if not result_raw and lead_text:
        result_raw = first_result_sentence(lead_text)
    date_info = parse_year_and_dates(date_raw)
    result_normalized, result_type = normalize_result(result_raw)

    belligerent_sides = fields.get("belligerents", [])
    commander_sides = fields.get("commanders", [])
    strength_sides = fields.get("strength", [])
    casualty_sides = fields.get("casualties", [])

    belligerent_map = {entry["side"]: entry["raw_text"] for entry in belligerent_sides}
    commander_map = {entry["side"]: entry["raw_text"] for entry in commander_sides}
    strength_map = {entry["side"]: entry["raw_text"] for entry in strength_sides}
    casualty_map = {entry["side"]: entry["raw_text"] for entry in casualty_sides}

    extraction_score = 0.0
    extraction_score += 0.2 if infobox["present"] else 0.0
    extraction_score += 0.2 if result_raw else 0.0
    extraction_score += 0.2 if date_raw else 0.0
    extraction_score += 0.2 if commander_sides else 0.0
    extraction_score += 0.2 if belligerent_sides else 0.0

    battle_id = f"battle_{page['pageid']}" if page.get("pageid") else f"battle_title_{hashlib.sha1(title.encode('utf-8')).hexdigest()[:12]}"
    battle_name = title
    battle_name_normalized = re.sub(r"\s*\([^)]*\)$", "", battle_name).strip()
    categories_joined = " | ".join(page.get("categories", []))
    notes_value = "recovery_mode=fallback_wikitext"

    raw_row = {
        "battle_id": battle_id,
        "battle_name": battle_name,
        "wikipedia_title": title,
        "source_url": url,
        "date_raw": date_raw,
        "war_name_raw": fields.get("war_name", ""),
        "location_raw": fields.get("location_raw", ""),
        "result_raw": result_raw,
        "belligerent_1_raw": belligerent_map.get("side_a", ""),
        "belligerent_2_raw": belligerent_map.get("side_b", ""),
        "belligerent_3_raw": belligerent_map.get("side_c", ""),
        "commander_side_a_raw": commander_map.get("side_a", ""),
        "commander_side_b_raw": commander_map.get("side_b", ""),
        "commander_side_c_raw": commander_map.get("side_c", ""),
        "strength_side_a_raw": strength_map.get("side_a", ""),
        "strength_side_b_raw": strength_map.get("side_b", ""),
        "strength_side_c_raw": strength_map.get("side_c", ""),
        "casualties_side_a_raw": casualty_map.get("side_a", ""),
        "casualties_side_b_raw": casualty_map.get("side_b", ""),
        "casualties_side_c_raw": casualty_map.get("side_c", ""),
        "page_type": classification["page_type"],
        "page_type_confidence": classification["confidence"],
        "classification_notes": classification["reasons"],
        "acceptance_reason": merge_pipe_values(classification["reasons"], "fallback wikitext extraction"),
        "battle_type": battle_type,
        "infobox_present": infobox["present"],
        "text_length": len(body_text),
        "categories": categories_joined,
        "list_page_origin": " | ".join(origins),
        "parent_list_page": " | ".join(parent_sources),
        "discovery_root": " | ".join(discovery_roots),
        "source_family": " | ".join(source_families),
        "extraction_confidence": round(extraction_score, 2),
        "notes": notes_value,
    }

    clean_row = {
        "battle_id": battle_id,
        "battle_name": battle_name,
        "battle_name_normalized": battle_name_normalized,
        "wikipedia_title": title,
        "source_url": url,
        **date_info,
        "war_name": fields.get("war_name", ""),
        "campaign_name": "",
        "location_raw": fields.get("location_raw", ""),
        "location_normalized": fields.get("location_raw", ""),
        "latitude": coord.get("lat", ""),
        "longitude": coord.get("lon", ""),
        "present_day_country": "",
        "result_raw": result_raw,
        "result_normalized": result_normalized,
        "result_type": result_type,
        "belligerent_1_raw": belligerent_map.get("side_a", ""),
        "belligerent_2_raw": belligerent_map.get("side_b", ""),
        "belligerent_3_raw": belligerent_map.get("side_c", ""),
        "commander_side_a_raw": commander_map.get("side_a", ""),
        "commander_side_b_raw": commander_map.get("side_b", ""),
        "commander_side_c_raw": commander_map.get("side_c", ""),
        "strength_side_a_raw": strength_map.get("side_a", ""),
        "strength_side_b_raw": strength_map.get("side_b", ""),
        "strength_side_c_raw": strength_map.get("side_c", ""),
        "casualties_side_a_raw": casualty_map.get("side_a", ""),
        "casualties_side_b_raw": casualty_map.get("side_b", ""),
        "casualties_side_c_raw": casualty_map.get("side_c", ""),
        "strength_side_a_min": parse_numeric_range(strength_map.get("side_a", "")).get("min", ""),
        "strength_side_a_max": parse_numeric_range(strength_map.get("side_a", "")).get("max", ""),
        "strength_side_b_min": parse_numeric_range(strength_map.get("side_b", "")).get("min", ""),
        "strength_side_b_max": parse_numeric_range(strength_map.get("side_b", "")).get("max", ""),
        "casualties_side_a_min": parse_numeric_range(casualty_map.get("side_a", "")).get("min", ""),
        "casualties_side_a_max": parse_numeric_range(casualty_map.get("side_a", "")).get("max", ""),
        "casualties_side_b_min": parse_numeric_range(casualty_map.get("side_b", "")).get("min", ""),
        "casualties_side_b_max": parse_numeric_range(casualty_map.get("side_b", "")).get("max", ""),
        "page_type": classification["page_type"],
        "page_type_confidence": classification["confidence"],
        "classification_notes": classification["reasons"],
        "acceptance_reason": merge_pipe_values(classification["reasons"], "fallback wikitext extraction"),
        "battle_type": battle_type,
        "infobox_present": infobox["present"],
        "text_length": len(body_text),
        "categories": categories_joined,
        "list_page_origin": " | ".join(origins),
        "parent_list_page": " | ".join(parent_sources),
        "discovery_root": " | ".join(discovery_roots),
        "source_family": " | ".join(source_families),
        "extraction_confidence": round(extraction_score, 2),
        "notes": notes_value,
    }

    commanders_rows: list[dict[str, Any]] = []
    all_side_commanders: dict[str, list[str]] = defaultdict(list)
    for side_entry in commander_sides:
        commander_entries = extract_commander_entries(side_entry)
        all_side_commanders[side_entry["side"]] = [entry["raw_name"] for entry in commander_entries]

    for side_entry in commander_sides:
        side_key = side_entry["side"]
        commander_entries = extract_commander_entries(side_entry)
        if not commander_entries:
            issues.append(
                issue_record(
                    title,
                    url,
                    "missing_commanders",
                    "commanders",
                    "medium",
                    f"No parseable commanders extracted for {side_key}.",
                    side_entry.get("raw_text", ""),
                )
            )
            continue
        for commander in commander_entries:
            opposing_names = []
            for other_side, names in all_side_commanders.items():
                if other_side != side_key:
                    opposing_names.extend(names)
            side_result = choose_side_result(side_key, result_type, result_raw, belligerent_map)
            commanders_rows.append(
                {
                    "battle_id": battle_id,
                    "battle_name": battle_name,
                    "year": date_info.get("year", ""),
                    "war_name": fields.get("war_name", ""),
                    "commander_name_raw": commander["raw_name"],
                    "commander_name_normalized": commander["normalized_name"],
                    "commander_wikipedia_url": commander["wikipedia_url"],
                    "side": side_key,
                    "belligerent": belligerent_map.get(side_key, ""),
                    "battle_result_for_commander": side_result,
                    "role_in_battle": "",
                    "opposing_commander_names_raw": " | ".join(opposing_names),
                    "location_normalized": fields.get("location_raw", ""),
                    "strength_side_raw": strength_map.get(side_key, ""),
                    "strength_enemy_raw": " | ".join(
                        value for key, value in strength_map.items() if key != side_key and value
                    ),
                    "casualties_side_raw": casualty_map.get(side_key, ""),
                    "casualties_enemy_raw": " | ".join(
                        value for key, value in casualty_map.items() if key != side_key and value
                    ),
                    "source_url": url,
                    "parse_notes": notes_value,
                    "identity_confidence": commander["identity_confidence"],
                }
            )

    if not date_raw:
        issues.append(issue_record(title, url, "missing_field", "date_raw", "medium", "Battle page is missing a parseable date field."))
    if not result_raw:
        issues.append(issue_record(title, url, "missing_field", "result_raw", "medium", "Battle page is missing a parseable result field."))
    if len(commanders_rows) > 16:
        issues.append(
            issue_record(
                title,
                url,
                "suspicious_commander_count",
                "commanders",
                "low",
                "Battle produced an unusually high commander count and should be reviewed.",
                str(len(commanders_rows)),
            )
        )

    if config.save_json:
        snapshot = {
            "page": page,
            "classification": classification,
            "raw_row": raw_row,
            "clean_row": clean_row,
            "commanders_rows": commanders_rows,
        }
        (json_dir / f"{slugify(title)}.json").write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")

    return raw_row, clean_row, commanders_rows, classification


def extract_page_worker(
    title: str,
    origin_rows: list[dict[str, Any]],
    config: PipelineConfig,
    json_dir: Path,
    metadata_pageid: int | None,
    mode: str = "full",
) -> dict[str, Any]:
    client = get_thread_local_client(config)
    started_at = time.monotonic()
    try:
        fetch_started_at = time.monotonic()
        if mode == "fallback":
            page = client.fetch_page_wikitext_bundle(title)
        else:
            page = client.fetch_page_bundle(title, include_query_metadata=False)
        fetch_elapsed_ms = round((time.monotonic() - fetch_started_at) * 1000, 1)
    except Exception as exc:  # noqa: BLE001
        return {
            "title": title,
            "error_kind": categorize_fetch_error(exc),
            "error_message": str(exc),
            "attempt_mode": mode,
            "fetch_elapsed_ms": 0.0,
            "build_elapsed_ms": 0.0,
            "total_elapsed_ms": round((time.monotonic() - started_at) * 1000, 1),
            "page_size": 0,
            "resolved_title": title,
            "redirected": False,
        }

    resolved_title = page.get("title", title)
    if not page.get("pageid") and metadata_pageid:
        page["pageid"] = metadata_pageid

    local_issues: list[dict[str, Any]] = []
    build_started_at = time.monotonic()
    if mode == "fallback":
        raw_row, clean_row, commander_entries, page_classification = build_battle_rows_from_wikitext(
            page=page,
            origin_rows=origin_rows,
            config=config,
            issues=local_issues,
            json_dir=json_dir,
            client=client,
        )
        page_size = len(page.get("wikitext", ""))
    else:
        raw_row, clean_row, commander_entries, page_classification = build_battle_rows(
            page=page,
            origin_rows=origin_rows,
            config=config,
            issues=local_issues,
            json_dir=json_dir,
            client=client,
        )
        page_size = len(page.get("html", ""))
    build_elapsed_ms = round((time.monotonic() - build_started_at) * 1000, 1)
    return {
        "title": title,
        "page": page,
        "raw_row": raw_row,
        "clean_row": clean_row,
        "commander_entries": commander_entries,
        "page_classification": page_classification,
        "issues": local_issues,
        "error_kind": "",
        "error_message": "",
        "attempt_mode": mode,
        "fetch_elapsed_ms": fetch_elapsed_ms,
        "build_elapsed_ms": build_elapsed_ms,
        "total_elapsed_ms": round((time.monotonic() - started_at) * 1000, 1),
        "page_size": page_size,
        "resolved_title": resolved_title,
        "redirected": normalize_space(resolved_title) != normalize_space(title),
    }


def extract_page_process_target(
    result_queue: mp.Queue,
    title: str,
    origin_rows: list[dict[str, Any]],
    config: PipelineConfig,
    json_dir: Path,
    metadata_pageid: int | None,
    mode: str = "full",
) -> None:
    result_queue.put(extract_page_worker(title, origin_rows, config, json_dir, metadata_pageid, mode=mode))


def build_commanders_master(
    commanders_df: pd.DataFrame,
    threshold: int,
) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    issues: list[dict[str, Any]] = []
    if commanders_df.empty:
        columns = [
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
        return pd.DataFrame(columns=columns), issues

    resolved_rows = []
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in commanders_df.to_dict(orient="records"):
        wiki_url = row.get("commander_wikipedia_url") or ""
        normalized = clean_name(row.get("commander_name_normalized") or row.get("commander_name_raw") or "")
        key = f"url:{wiki_url}" if wiki_url else f"name:{normalized.lower()}"
        grouped[key].append(row)

    unresolved_no_url = [
        clean_name(value)
        for value in commanders_df.loc[
            commanders_df["commander_wikipedia_url"].fillna("") == "",
            "commander_name_normalized",
        ].tolist()
        if clean_name(value)
    ]
    unique_unresolved = sorted(set(unresolved_no_url))
    for left in unique_unresolved:
        for right in unique_unresolved:
            if left >= right:
                continue
            if fuzz.token_sort_ratio(left, right) >= threshold and left != right:
                issues.append(
                    issue_record(
                        page_title="",
                        source_url="",
                        issue_type="possible_commander_alias",
                        field_name="commander_name_normalized",
                        severity="low",
                        message=f"Possible duplicate commander names detected: '{left}' vs '{right}'.",
                    )
                )

    for key, rows in grouped.items():
        variants = sorted({clean_name(row["commander_name_raw"]) for row in rows if clean_name(row["commander_name_raw"])})
        wiki_url = rows[0].get("commander_wikipedia_url") or ""
        name_primary = clean_name(rows[0]["commander_name_normalized"])
        resolution_method = "linked_article" if wiki_url else "exact_cleaned_name"
        commander_id = f"cmd_{hashlib.sha1(key.encode('utf-8')).hexdigest()[:12]}"
        resolved_rows.append(
            {
                "commander_id": commander_id,
                "name_primary": name_primary,
                "name_variants": " | ".join(variants),
                "wikipedia_page": wiki_url,
                "birth_year": "",
                "death_year": "",
                "civilization_or_state": "",
                "era": "",
                "service_branch": "",
                "notes": "",
                "identity_resolution_method": resolution_method,
            }
        )

    return pd.DataFrame(resolved_rows), issues


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def percentage(part: int, whole: int) -> str:
    if not whole:
        return "0.0%"
    return f"{(part / whole) * 100:.1f}%"


def merge_pipe_values(*values: str) -> str:
    merged: list[str] = []
    seen: set[str] = set()
    for value in values:
        for item in [normalize_space(part) for part in value.split("|") if normalize_space(part)]:
            if item not in seen:
                seen.add(item)
                merged.append(item)
    return " | ".join(merged)


def split_pipe_values(value: str) -> list[str]:
    return [normalize_space(part) for part in str(value).split("|") if normalize_space(part)]


def counter_from_pipe_series(series: pd.Series) -> Counter:
    counts: Counter = Counter()
    for value in series.fillna("").tolist():
        for item in split_pipe_values(value):
            counts[item] += 1
    return counts


def build_benchmark_recall_rows(candidate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidate_df = pd.DataFrame(candidate_rows)
    if candidate_df.empty:
        return []
    deduped = candidate_df.sort_values(["candidate_title"]).drop_duplicates(subset=["candidate_title"])
    lookup = {row["candidate_title"]: row for row in deduped.to_dict(orient="records")}
    rows: list[dict[str, Any]] = []
    for title in BENCHMARK_TITLES:
        row = lookup.get(title)
        rows.append(
            {
                "title": title,
                "discovered": bool(row),
                "metadata_page_type": row.get("metadata_page_type", "") if row else "",
                "metadata_accepted": bool(row.get("metadata_accepted")) if row else False,
                "full_fetch_status": row.get("full_fetch_status", "") if row else "",
                "final_page_type": row.get("final_page_type", "") if row else "",
            }
        )
    return rows


def load_previous_run_metrics(output_dir: Path) -> dict[str, Any] | None:
    metrics_path = output_dir / "run_metrics.json"
    if metrics_path.exists():
        return json.loads(metrics_path.read_text(encoding="utf-8"))
    battles_path = output_dir / "battles_clean.csv"
    commanders_path = output_dir / "battle_commanders.csv"
    candidates_path = output_dir / "candidate_battle_pages.csv"
    issues_path = output_dir / "extraction_issues.csv"
    if not battles_path.exists() or not commanders_path.exists():
        return None
    battles_df = pd.read_csv(battles_path)
    commanders_df = pd.read_csv(commanders_path)
    candidates_df = pd.read_csv(candidates_path) if candidates_path.exists() else pd.DataFrame()
    issues_df = pd.read_csv(issues_path) if issues_path.exists() else pd.DataFrame()
    return {
        "battle_count": len(battles_df),
        "commander_row_count": len(commanders_df),
        "candidate_count": len(candidates_df),
        "with_commanders_pct": round((battles_df["battle_id"].isin(commanders_df["battle_id"]).sum() / len(battles_df) * 100), 1)
        if len(battles_df)
        else 0.0,
        "with_result_pct": round((battles_df["result_normalized"].fillna("").ne("").sum() / len(battles_df) * 100), 1)
        if len(battles_df)
        else 0.0,
        "with_year_pct": round((battles_df["year"].fillna("").astype(str).ne("").sum() / len(battles_df) * 100), 1)
        if len(battles_df)
        else 0.0,
        "unresolved_identity_pct": round((commanders_df["commander_wikipedia_url"].fillna("").eq("").sum() / len(commanders_df) * 100), 1)
        if len(commanders_df)
        else 0.0,
        "excluded_pages": int(issues_df["issue_type"].isin(["non_battle_candidate", "rejected_candidate"]).sum()) if not issues_df.empty else 0,
    }


def compute_run_metrics(
    battles_clean: pd.DataFrame,
    commanders: pd.DataFrame,
    commander_master: pd.DataFrame,
    issues_df: pd.DataFrame,
    candidate_rows: list[dict[str, Any]],
    sources_index: list[dict[str, Any]],
    coverage_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    candidate_df = pd.DataFrame(candidate_rows)
    sources_df = pd.DataFrame(sources_index).drop_duplicates()
    issue_counts = Counter(issues_df["issue_type"].tolist()) if not issues_df.empty else Counter()
    rejection_counts = Counter(
        issues_df.loc[issues_df["issue_type"].isin(["non_battle_candidate", "rejected_candidate"]), "message"].tolist()
    ) if not issues_df.empty else Counter()

    deduped_candidates = (
        candidate_df.sort_values(["candidate_title"]).drop_duplicates(subset=["candidate_title"]).copy()
        if not candidate_df.empty
        else pd.DataFrame()
    )

    battle_count = len(battles_clean)
    commander_count = len(commanders)
    duplicate_candidate_rows = len(candidate_df) - candidate_df["candidate_title"].nunique() if not candidate_df.empty else 0
    unresolved_commanders = commanders["commander_wikipedia_url"].fillna("").eq("").sum() if commander_count else 0
    with_commanders = int(battles_clean["battle_id"].isin(commanders["battle_id"]).sum()) if battle_count else 0
    with_results = int(battles_clean["result_normalized"].fillna("").ne("").sum()) if battle_count else 0
    with_year = int(battles_clean["year"].fillna("").astype(str).ne("").sum()) if battle_count else 0
    with_type = int(battles_clean["battle_type"].fillna("").ne("").sum()) if battle_count else 0

    metadata_fetched = int(deduped_candidates["metadata_fetch_status"].eq("classified").sum()) if not deduped_candidates.empty else 0
    metadata_accepted_total = int(deduped_candidates["metadata_accepted"].eq(True).sum()) if not deduped_candidates.empty else 0
    accepted_battle_pages = int(battles_clean["page_type"].eq("battle_article").sum()) if battle_count else 0
    accepted_war_pages = int(battles_clean["page_type"].eq("war_conflict_article").sum()) if battle_count else 0
    accepted_campaign_pages = int(battles_clean["page_type"].eq("campaign_article").sum()) if battle_count else 0
    accepted_operation_pages = int(battles_clean["page_type"].eq("operation_article").sum()) if battle_count else 0
    rejected_candidates = int(
        (
            deduped_candidates["metadata_fetch_status"].eq("classified")
            & deduped_candidates["metadata_accepted"].eq(False)
        ).sum()
    ) if not deduped_candidates.empty else 0
    rejected_after_full_fetch = int(deduped_candidates["full_fetch_status"].eq("rejected_after_full_fetch").sum()) if not deduped_candidates.empty else 0
    rate_limit_skips = int(
        deduped_candidates["metadata_fetch_status"].eq("rate_limit").sum()
        + deduped_candidates["full_fetch_status"].eq("rate_limit").sum()
    ) if not deduped_candidates.empty else 0
    protection_skips = int(
        deduped_candidates["metadata_fetch_status"].eq("protection").sum()
        + deduped_candidates["full_fetch_status"].eq("protection").sum()
    ) if not deduped_candidates.empty else 0
    error_skips = int(
        deduped_candidates["metadata_fetch_status"].isin(["fetch_error", "missing_or_unavailable"]).sum()
        + deduped_candidates["full_fetch_status"].isin(["fetch_error", "missing_or_unavailable"]).sum()
    ) if not deduped_candidates.empty else 0
    pending_after_run = int(deduped_candidates["full_fetch_status"].isin(["pending", "not_attempted"]).sum()) if not deduped_candidates.empty else 0
    fully_visited = int(
        deduped_candidates["full_fetch_status"].isin(
            ["accepted", "rejected_after_full_fetch", "fetch_error", "rate_limit", "protection", "missing_or_unavailable"]
        ).sum()
    ) if not deduped_candidates.empty else 0
    fully_extracted = int(
        deduped_candidates["full_fetch_status"].isin(["accepted", "rejected_after_full_fetch"]).sum()
    ) if not deduped_candidates.empty else 0
    not_visited_due_bound = int(deduped_candidates["full_fetch_status"].eq("not_visited_due_bound").sum()) if not deduped_candidates.empty else 0
    source_family_candidate_counts = (
        counter_from_pipe_series(deduped_candidates["source_family"]) if not deduped_candidates.empty else Counter()
    )
    source_family_accepted_counts = (
        counter_from_pipe_series(battles_clean["source_family"]) if battle_count else Counter()
    )
    final_page_type_breakdown = battles_clean["page_type"].value_counts(dropna=False).to_dict() if battle_count else {}
    battle_type_breakdown = battles_clean["battle_type"].value_counts(dropna=False).to_dict() if battle_count else {}
    pages_missing_commanders = battle_count - with_commanders
    pages_with_ambiguous_commanders = (
        int(commanders.loc[commanders["identity_confidence"].fillna("").ne("high"), "battle_id"].nunique())
        if commander_count and "identity_confidence" in commanders.columns
        else 0
    )
    benchmark_rows = build_benchmark_recall_rows(candidate_rows)
    benchmark_discovered = sum(1 for row in benchmark_rows if row["discovered"])
    benchmark_accepted = sum(1 for row in benchmark_rows if row["full_fetch_status"] == "accepted")

    return {
        "generated_at": NOW_UTC.isoformat(),
        "candidate_count": len(candidate_df),
        "unique_candidate_titles": deduped_candidates["candidate_title"].nunique() if not deduped_candidates.empty else 0,
        "candidate_pages_fetched": metadata_fetched,
        "metadata_accepted_total": metadata_accepted_total,
        "fully_extracted_pages": fully_extracted,
        "accepted_battle_pages": accepted_battle_pages,
        "accepted_war_conflict_pages": accepted_war_pages,
        "accepted_campaign_pages": accepted_campaign_pages,
        "accepted_operation_pages": accepted_operation_pages,
        "accepted_total_pages": battle_count,
        "excluded_pages": rejected_candidates + rejected_after_full_fetch,
        "excluded_by_reason": dict(rejection_counts),
        "rejected_non_battle_non_war": rejected_candidates + rejected_after_full_fetch,
        "skipped_due_errors": error_skips,
        "skipped_due_rate_limits": rate_limit_skips,
        "skipped_due_protection": protection_skips,
        "pending_after_run": pending_after_run,
        "not_visited_due_bound": not_visited_due_bound,
        "full_accepted_graph_extracted": metadata_accepted_total > 0 and metadata_accepted_total == fully_extracted,
        "battle_count": battle_count,
        "commander_row_count": commander_count,
        "commander_master_count": len(commander_master),
        "source_count": len(sources_df),
        "duplicate_candidate_rows": duplicate_candidate_rows,
        "duplicate_candidate_rate_pct": round((duplicate_candidate_rows / len(candidate_df) * 100), 1) if len(candidate_df) else 0.0,
        "discovered_graph_metadata_visit_pct": round((metadata_fetched / len(deduped_candidates) * 100), 1) if len(deduped_candidates) else 0.0,
        "discovered_graph_full_visit_pct": round((fully_visited / len(deduped_candidates) * 100), 1) if len(deduped_candidates) else 0.0,
        "with_commanders_count": with_commanders,
        "with_commanders_pct": round((with_commanders / battle_count * 100), 1) if battle_count else 0.0,
        "with_result_count": with_results,
        "with_result_pct": round((with_results / battle_count * 100), 1) if battle_count else 0.0,
        "with_year_count": with_year,
        "with_year_pct": round((with_year / battle_count * 100), 1) if battle_count else 0.0,
        "with_battle_type_count": with_type,
        "with_battle_type_pct": round((with_type / battle_count * 100), 1) if battle_count else 0.0,
        "unresolved_identity_count": int(unresolved_commanders),
        "unresolved_identity_pct": round((unresolved_commanders / commander_count * 100), 1) if commander_count else 0.0,
        "pages_missing_commanders": pages_missing_commanders,
        "pages_with_ambiguous_commanders": pages_with_ambiguous_commanders,
        "final_page_type_breakdown": final_page_type_breakdown,
        "battle_type_breakdown": battle_type_breakdown,
        "source_family_candidate_counts": dict(source_family_candidate_counts),
        "source_family_accepted_counts": dict(source_family_accepted_counts),
        "benchmark_rows": benchmark_rows,
        "benchmark_discovered": benchmark_discovered,
        "benchmark_accepted": benchmark_accepted,
        "coverage_context": coverage_context or {},
        "issue_counts": dict(issue_counts),
    }


def build_quality_report(
    battles_clean: pd.DataFrame,
    commanders: pd.DataFrame,
    commander_master: pd.DataFrame,
    issues_df: pd.DataFrame,
    candidate_rows: list[dict[str, Any]],
    sources_index: list[dict[str, Any]],
    output_path: Path,
    previous_metrics: dict[str, Any] | None = None,
    coverage_context: dict[str, Any] | None = None,
) -> None:
    metrics = compute_run_metrics(
        battles_clean,
        commanders,
        commander_master,
        issues_df,
        candidate_rows,
        sources_index,
        coverage_context=coverage_context,
    )
    manual_review = issues_df[issues_df["severity"].isin(["high", "medium"])][
        ["page_title", "issue_type", "field_name", "message"]
    ].head(50)
    coverage_context = metrics.get("coverage_context", {})
    list_pages = coverage_context.get("list_pages", [])
    period_lists = [row["title"] for row in list_pages if row.get("source_family") == "period_based"]
    war_lists = [row["title"] for row in list_pages if row.get("source_family") == "war_conflict_based"]
    region_lists = [row["title"] for row in list_pages if row.get("source_family") == "region_based"]
    participant_lists = [row["title"] for row in list_pages if row.get("source_family") == "participant_based"]
    type_lists = [row["title"] for row in list_pages if row.get("source_family") == "battle_type_based"]

    lines = [
        "# Data Quality Report",
        "",
        f"- Generated at: {metrics['generated_at']}",
        f"- Total links discovered: {metrics['candidate_count']}",
        f"- Unique candidate titles after title dedupe: {metrics['unique_candidate_titles']}",
        f"- Candidate pages actually fetched/classified: {metrics['candidate_pages_fetched']}",
        f"- Accepted candidates at metadata stage: {metrics['metadata_accepted_total']}",
        f"- Pages fully extracted after full fetch: {metrics['fully_extracted_pages']}",
        f"- Pages accepted as battle articles: {metrics['accepted_battle_pages']}",
        f"- Pages accepted as war/conflict articles: {metrics['accepted_war_conflict_pages']}",
        f"- Pages accepted as campaign articles: {metrics['accepted_campaign_pages']}",
        f"- Pages accepted as operation articles: {metrics['accepted_operation_pages']}",
        f"- Pages rejected as non-battle/non-war: {metrics['rejected_non_battle_non_war']}",
        f"- Pages skipped due to errors: {metrics['skipped_due_errors']}",
        f"- Pages skipped due to rate limits: {metrics['skipped_due_rate_limits']}",
        f"- Pages skipped due to protection: {metrics['skipped_due_protection']}",
        f"- Pages still pending or otherwise unclassified after full-fetch stage: {metrics['pending_after_run']}",
        f"- Pages not visited because of configured crawl bounds: {metrics['not_visited_due_bound']}",
        f"- Full accepted graph extracted: {'yes' if metrics['full_accepted_graph_extracted'] else 'no'}",
        f"- Accepted pages retained in clean dataset: {metrics['battle_count']}",
        f"- Commander-per-battle rows: {metrics['commander_row_count']}",
        f"- Unique commander master rows: {metrics['commander_master_count']}",
        f"- Source pages logged: {metrics['source_count']}",
        f"- Duplicate candidate rows: {metrics['duplicate_candidate_rows']} ({metrics['duplicate_candidate_rate_pct']:.1f}%)",
        f"- Discovered graph visited/classified at metadata stage: {metrics['discovered_graph_metadata_visit_pct']:.1f}%",
        f"- Discovered graph fully fetched/extracted: {metrics['discovered_graph_full_visit_pct']:.1f}%",
        f"- Battles with at least one commander extracted: {metrics['with_commanders_count']} ({metrics['with_commanders_pct']:.1f}%)",
        f"- Battles with normalized result: {metrics['with_result_count']} ({metrics['with_result_pct']:.1f}%)",
        f"- Battles with parsed year: {metrics['with_year_count']} ({metrics['with_year_pct']:.1f}%)",
        f"- Battles with battle type assigned: {metrics['with_battle_type_count']} ({metrics['with_battle_type_pct']:.1f}%)",
        f"- Commander rows with unresolved identity: {metrics['unresolved_identity_count']} ({metrics['unresolved_identity_pct']:.1f}%)",
        "",
        "## Coverage Audit",
        "",
        f"- Root pages used: {' | '.join(coverage_context.get('root_pages', [])) or ROOT_TITLE}",
        f"- Major sub-list families traversed: {', '.join(sorted({row.get('source_family', '') for row in list_pages if row.get('source_family')})) or 'none recorded'}",
        f"- Period-based lists traversed: {len(period_lists)}",
        f"- War/conflict-based lists traversed: {len(war_lists)}",
        f"- Region-based lists traversed: {len(region_lists)}",
        f"- Participant-based lists traversed: {len(participant_lists)}",
        f"- Battle-type lists traversed: {len(type_lists)}",
        f"- Category-based discovery used: {'yes' if coverage_context.get('category_discovery_used') else 'no'}",
        f"- Category pages traversed: {coverage_context.get('category_pages_traversed', 0)}",
        f"- Candidate pages by source family: {json.dumps(metrics['source_family_candidate_counts'], ensure_ascii=False)}",
        f"- Accepted pages by source family: {json.dumps(metrics['source_family_accepted_counts'], ensure_ascii=False)}",
    ]

    bounds = coverage_context.get("configured_bounds", {})
    blind_spots: list[str] = []
    if bounds.get("max_root_links") is not None or bounds.get("max_list_pages") is not None or bounds.get("max_candidate_pages") is not None:
        blind_spots.append(f"bounded crawl settings remained active: {json.dumps(bounds, ensure_ascii=False)}")
    if not coverage_context.get("category_discovery_used"):
        blind_spots.append("categorymember expansion was not used, so category-only military graph branches remain a blind spot")
    if metrics["skipped_due_rate_limits"]:
        blind_spots.append(f"rate limits skipped {metrics['skipped_due_rate_limits']} candidate pages")
    if metrics["not_visited_due_bound"]:
        blind_spots.append(f"{metrics['not_visited_due_bound']} accepted candidate pages were not fully fetched because of a configured candidate bound")
    if not blind_spots:
        blind_spots.append("no explicit blind spot flags were recorded, but completeness still depends on the linked list graph reachable from the chosen roots")
    lines.extend([f"- Blind spots: {'; '.join(blind_spots)}", "", "## Exclusion Reasons", ""])

    if metrics["excluded_by_reason"]:
        for reason, count in sorted(metrics["excluded_by_reason"].items(), key=lambda item: item[1], reverse=True):
            lines.append(f"- {count}: {reason}")
    else:
        lines.append("- No excluded pages were logged.")

    lines.extend(["", "## Final Page-Type Breakdown", ""])
    if metrics["final_page_type_breakdown"]:
        for page_type, count in sorted(metrics["final_page_type_breakdown"].items(), key=lambda item: (-item[1], item[0])):
            lines.append(f"- {page_type}: {count}")
    else:
        lines.append("- No retained page types were recorded.")

    lines.extend(["", "## Final Engagement-Type Breakdown", ""])
    if metrics["battle_type_breakdown"]:
        for battle_type, count in sorted(metrics["battle_type_breakdown"].items(), key=lambda item: (-item[1], item[0])):
            lines.append(f"- {battle_type}: {count}")
    else:
        lines.append("- No engagement-type counts were recorded.")

    lines.extend(["", "## Commander Coverage Summary", ""])
    lines.extend(
        [
            f"- Total commander rows: {metrics['commander_row_count']}",
            f"- Total unique commander identities: {metrics['commander_master_count']}",
            f"- Commander coverage across accepted pages: {metrics['with_commanders_count']} ({metrics['with_commanders_pct']:.1f}%)",
            f"- Pages still missing commanders: {metrics['pages_missing_commanders']}",
            f"- Pages with ambiguous or lower-confidence commander assignments: {metrics['pages_with_ambiguous_commanders']}",
            f"- Unresolved commander identity rate: {metrics['unresolved_identity_count']} ({metrics['unresolved_identity_pct']:.1f}%)",
        ]
    )

    lines.extend(["", "## Benchmark Recall", ""])
    for row in metrics["benchmark_rows"]:
        if row["discovered"]:
            lines.append(
                f"- {row['title']}: discovered=yes; metadata={row['metadata_page_type']}; full_fetch={row['full_fetch_status']}; final={row['final_page_type']}"
            )
        else:
            lines.append(f"- {row['title']}: discovered=no")

    lines.extend(["", "## Delta Vs Previous Run", ""])
    if previous_metrics:
        previous_battle_count = previous_metrics.get("battle_count", previous_metrics.get("accepted_total_pages", 0))
        previous_commander_count = previous_metrics.get("commander_row_count", 0)
        previous_candidate_count = previous_metrics.get("candidate_count", 0)
        previous_excluded = previous_metrics.get("excluded_pages", 0)
        previous_with_commanders = previous_metrics.get("with_commanders_pct", 0)
        previous_with_result = previous_metrics.get("with_result_pct", 0)
        previous_with_year = previous_metrics.get("with_year_pct", 0)
        previous_unresolved = previous_metrics.get("unresolved_identity_pct", 0)
        lines.extend(
            [
                f"- Battle/accepted-page count growth: {metrics['battle_count'] - previous_battle_count:+d} ({previous_battle_count} -> {metrics['battle_count']})",
                f"- Commander-row growth: {metrics['commander_row_count'] - previous_commander_count:+d} ({previous_commander_count} -> {metrics['commander_row_count']})",
                f"- Candidate discovery growth: {metrics['candidate_count'] - previous_candidate_count:+d} ({previous_candidate_count} -> {metrics['candidate_count']})",
                f"- False-positive exclusions change: {metrics['excluded_pages'] - previous_excluded:+d} ({previous_excluded} -> {metrics['excluded_pages']})",
                f"- Commander extraction coverage change: {metrics['with_commanders_pct'] - previous_with_commanders:+.1f} pts",
                f"- Result completeness change: {metrics['with_result_pct'] - previous_with_result:+.1f} pts",
                f"- Parsed-year completeness change: {metrics['with_year_pct'] - previous_with_year:+.1f} pts",
                f"- Unresolved identity rate change: {metrics['unresolved_identity_pct'] - previous_unresolved:+.1f} pts",
            ]
        )
    else:
        lines.append("- No previous run metrics were available for comparison.")

    lines.extend([
        "",
        "## Manual Review Queue",
        "",
    ])
    if manual_review.empty:
        lines.append("- No medium/high severity issues were generated in this run.")
    else:
        for row in manual_review.to_dict(orient="records"):
            title = row["page_title"] or "[cross-record issue]"
            lines.append(f"- {title}: {row['issue_type']} / {row['field_name']} - {row['message']}")
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def annotate_candidate_rows(candidate_rows: list[dict[str, Any]], candidate_statuses: dict[str, dict[str, Any]]) -> None:
    for row in candidate_rows:
        status = candidate_statuses.get(row["candidate_title"], {})
        row["metadata_fetch_status"] = status.get("metadata_fetch_status", "not_classified")
        row["metadata_page_type"] = status.get("metadata_page_type", "")
        row["metadata_page_type_confidence"] = status.get("metadata_confidence", "")
        row["metadata_acceptance_reason"] = status.get("metadata_reason", "")
        row["metadata_accepted"] = status.get("metadata_accepted", False)
        row["full_fetch_status"] = status.get("full_fetch_status", "not_attempted")
        row["final_page_type"] = status.get("final_page_type", "")
        row["final_acceptance_reason"] = status.get("final_reason", "")


def setup_logging(output_dir: Path) -> None:
    log_path = output_dir / "pipeline.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[logging.FileHandler(log_path, encoding="utf-8"), logging.StreamHandler()],
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a historical battle dataset from Wikipedia battle lists.")
    parser.add_argument("--output-dir", default="outputs", help="Directory for CSV outputs and reports.")
    parser.add_argument("--cache-dir", default=".cache/wiki_api", help="Directory for cached MediaWiki responses.")
    parser.add_argument("--max-root-links", type=int, default=None, help="Optional maximum number of root-page links to inspect.")
    parser.add_argument("--max-list-pages", type=int, default=None, help="Optional maximum number of list pages to crawl.")
    parser.add_argument("--max-candidate-pages", type=int, default=None, help="Optional maximum number of candidate pages to fully fetch after discovery/classification.")
    parser.add_argument("--max-battle-pages", type=int, default=None, help="Deprecated alias for --max-candidate-pages.")
    parser.add_argument("--category-depth", type=int, default=1, help="Depth for categorymember expansion from military-history root categories.")
    parser.add_argument("--full-fetch-workers", type=int, default=6, help="Worker count for parallel full-page fetches during extraction.")
    parser.add_argument("--full-fetch-batch-size", type=int, default=200, help="Number of accepted pages to submit to the worker pool at once.")
    parser.add_argument("--page-task-timeout", type=int, default=180, help="Hard wall-clock timeout in seconds for one page extraction worker.")
    parser.add_argument("--request-timeout", type=int, default=30, help="HTTP timeout in seconds.")
    parser.add_argument("--request-sleep", type=float, default=0.1, help="Sleep between live API requests.")
    parser.add_argument("--stop-after-metadata", action="store_true", help="Stop after discovery and metadata classification, then write candidate_battle_pages.csv.")
    parser.add_argument("--no-json", action="store_true", help="Disable page-level JSON snapshots.")
    parser.add_argument("--no-cache", action="store_true", help="Disable reuse of cached API responses.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    max_candidate_pages = args.max_candidate_pages if args.max_candidate_pages is not None else args.max_battle_pages
    output_dir = Path(args.output_dir).resolve()
    cache_dir = Path(args.cache_dir).resolve()
    json_dir = output_dir / "page_json"
    output_dir.mkdir(parents=True, exist_ok=True)
    cache_dir.mkdir(parents=True, exist_ok=True)
    if not args.no_json:
        json_dir.mkdir(parents=True, exist_ok=True)

    setup_logging(output_dir)
    logger = logging.getLogger("pipeline")
    previous_metrics = load_previous_run_metrics(output_dir)
    config = PipelineConfig(
        output_dir=output_dir,
        cache_dir=cache_dir,
        save_json=not args.no_json,
        max_root_links=args.max_root_links,
        max_list_pages=args.max_list_pages,
        max_battle_pages=max_candidate_pages,
        request_timeout=args.request_timeout,
        request_sleep=args.request_sleep,
        reuse_cache=not args.no_cache,
        category_depth=max(0, args.category_depth),
        full_fetch_workers=max(1, args.full_fetch_workers),
        full_fetch_batch_size=max(1, args.full_fetch_batch_size),
        page_task_timeout=max(30, args.page_task_timeout),
    )

    client = WikipediaClient(config)
    sources_index: list[dict[str, Any]] = []
    extraction_issues: list[dict[str, Any]] = []
    candidate_origins: dict[str, list[dict[str, Any]]] = defaultdict(list)
    candidate_rows: list[dict[str, Any]] = []
    candidate_statuses: dict[str, dict[str, Any]] = {}
    coverage_context: dict[str, Any] = {
        "root_pages": [ROOT_TITLE],
        "list_pages": [],
        "category_discovery_used": False,
        "configured_bounds": {
            "max_root_links": config.max_root_links,
            "max_list_pages": config.max_list_pages,
            "max_candidate_pages": config.max_battle_pages,
            "category_depth": config.category_depth,
        },
    }

    logger.info("Fetching root page: %s", ROOT_TITLE)
    root_page = client.fetch_page_bundle(ROOT_TITLE, include_query_metadata=False)
    root_soup = BeautifulSoup(root_page["html"], "html.parser")
    root_text = page_text(BeautifulSoup(root_page["html"], "html.parser"))
    sources_index.append(
        build_source_record(
            root_page["title"],
            root_page["fullurl"],
            "root_index",
            "",
            "ok",
            discovery_root=root_page["title"],
            source_family="root_index",
        )
    )

    root_links = extract_internal_links(root_soup)
    if config.max_root_links:
        root_links = root_links[: config.max_root_links]

    list_pages: list[dict[str, Any]] = []
    seen_list_titles: set[str] = set()
    visited_discovery_titles: set[str] = {root_page["title"]}
    discovery_queue: deque[tuple[str, str, str, str, str]] = deque()

    def queue_link_for_list_discovery(link_title: str, parent_title: str, href: str, discovery_root: str) -> None:
        lower = link_title.lower()
        if has_meta_namespace(link_title) or link_title in visited_discovery_titles:
            return
        if any(pattern in lower for pattern in LIST_TITLE_PATTERNS) or (
            any(keyword in lower for keyword in LIST_KEYWORDS) and text_contains_battle_context(lower)
        ):
            discovery_queue.append((link_title, parent_title, href, discovery_root, classify_source_family(link_title)))

    for link in root_links:
        queue_link_for_list_discovery(link["title"], ROOT_TITLE, link["href"], root_page["title"])

    logger.info("Inspecting up to %s root links and expanding list-page frontier", config.max_root_links)
    while discovery_queue and (not config.max_list_pages or len(list_pages) < config.max_list_pages):
        title, parent_title, href, discovery_root, queued_family = discovery_queue.popleft()
        if title in visited_discovery_titles:
            continue
        visited_discovery_titles.add(title)
        try:
            candidate_page = client.fetch_page_bundle(title, include_query_metadata=False)
        except Exception as exc:  # noqa: BLE001
            error_kind = categorize_fetch_error(exc)
            extraction_issues.append(
                issue_record(title, href, error_kind, "page", "high", f"Failed to fetch root/list-linked page: {exc}")
            )
            sources_index.append(
                build_source_record(
                    title,
                    href,
                    "unknown",
                    parent_title,
                    error_kind,
                    str(exc),
                    discovery_root=discovery_root,
                    source_family=queued_family,
                )
            )
            continue

        candidate_soup = BeautifulSoup(candidate_page["html"], "html.parser")
        candidate_text = page_text(BeautifulSoup(candidate_page["html"], "html.parser"))
        page_classification = classify_page(candidate_page["title"], candidate_page["categories"], candidate_soup, candidate_text)
        page_family = classify_source_family(candidate_page["title"])
        candidate_page["discovery_root"] = discovery_root
        candidate_page["source_family"] = page_family
        sources_index.append(
            build_source_record(
                candidate_page["title"],
                candidate_page["fullurl"],
                page_classification["page_type"],
                parent_title,
                "ok",
                page_classification["reasons"],
                discovery_root=discovery_root,
                source_family=page_family,
            )
        )
        if is_probable_list_page(candidate_page["title"], candidate_page["categories"], candidate_text, candidate_soup):
            if candidate_page["title"] not in seen_list_titles:
                seen_list_titles.add(candidate_page["title"])
                list_pages.append(candidate_page)
                coverage_context["list_pages"].append(
                    {
                        "title": candidate_page["title"],
                        "source_family": page_family,
                        "discovery_root": discovery_root,
                    }
                )
            for link in extract_internal_links(candidate_soup):
                queue_link_for_list_discovery(link["title"], candidate_page["title"], link["href"], discovery_root)

    if not list_pages and is_probable_list_page(root_page["title"], root_page["categories"], root_text, root_soup):
        root_page["discovery_root"] = root_page["title"]
        root_page["source_family"] = "root_index"
        list_pages.append(root_page)

    logger.info("Discovered %s list pages", len(list_pages))
    if not list_pages:
        raise SystemExit("No list pages were discovered. Adjust discovery heuristics or limits.")

    for list_page in tqdm(list_pages, desc="Extract battle candidates"):
        soup = BeautifulSoup(list_page["html"], "html.parser")
        candidates = extract_candidate_battle_links(
            list_title=list_page["title"],
            soup=soup,
            discovery_root=list_page.get("discovery_root", root_page["title"]),
            source_family=list_page.get("source_family", classify_source_family(list_page["title"])),
        )
        for candidate in candidates:
            candidate_origins[candidate["candidate_title"]].append(candidate)
            candidate_rows.append(candidate)

    def build_candidate_priority() -> dict[str, tuple[int, int]]:
        priority: dict[str, tuple[int, int]] = {}
        for row in candidate_rows:
            title = row["candidate_title"]
            previous_score, previous_count = priority.get(title, (0, 0))
            priority[title] = (max(previous_score, int(row.get("candidate_score", 0))), previous_count + 1)
        return priority

    def metadata_classify_titles(titles: list[str]) -> None:
        if not titles:
            return
        for chunk in tqdm(list(chunked(titles, 25)), desc="Classify candidates"):
            try:
                chunk_metadata = client.fetch_page_metadata_batch(chunk, chunk_size=25)
            except Exception as exc:  # noqa: BLE001
                error_kind = categorize_fetch_error(exc)
                for title in chunk:
                    origin_rows = candidate_origins[title]
                    parent_sources = sorted({row.get("parent_source", "") for row in origin_rows if row.get("parent_source")})
                    discovery_roots = sorted({row.get("discovery_root", "") for row in origin_rows if row.get("discovery_root")})
                    source_families = sorted({row.get("source_family", "") for row in origin_rows if row.get("source_family")})
                    candidate_statuses[title] = {
                        "metadata_fetch_status": error_kind,
                        "metadata_page_type": "unknown",
                        "metadata_confidence": 0.0,
                        "metadata_reason": str(exc),
                        "metadata_accepted": False,
                        "full_fetch_status": "not_attempted",
                        "final_page_type": "unknown",
                    }
                    sources_index.append(
                        build_source_record(
                            title,
                            wikipedia_url_for_title(title),
                            "unknown",
                            " | ".join(parent_sources),
                            error_kind,
                            str(exc),
                            discovery_root=" | ".join(discovery_roots),
                            source_family=" | ".join(source_families),
                        )
                    )
                continue

            for title in chunk:
                metadata = chunk_metadata.get(
                    title,
                    {
                        "title": title,
                        "pageid": None,
                        "fullurl": wikipedia_url_for_title(title),
                        "categories": [],
                        "coordinates": [],
                        "pageprops": {},
                    },
                )
                metadata_classification = classify_metadata_page(metadata["title"], metadata["categories"])
                origin_rows = candidate_origins[title]
                parent_sources = sorted({row.get("parent_source", "") for row in origin_rows if row.get("parent_source")})
                discovery_roots = sorted({row.get("discovery_root", "") for row in origin_rows if row.get("discovery_root")})
                source_families = sorted({row.get("source_family", "") for row in origin_rows if row.get("source_family")})
                candidate_statuses[title] = {
                    "metadata_fetch_status": "classified",
                    "metadata_page_type": metadata_classification["page_type"],
                    "metadata_confidence": metadata_classification["confidence"],
                    "metadata_reason": metadata_classification["reasons"],
                    "metadata_accepted": metadata_classification["accepted"],
                    "full_fetch_status": "pending" if metadata_classification["accepted"] else "skipped_rejected",
                    "final_page_type": metadata_classification["page_type"],
                    "source_url": metadata["fullurl"],
                    "pageid": metadata.get("pageid"),
                    "parent_source": " | ".join(parent_sources),
                    "discovery_root": " | ".join(discovery_roots),
                    "source_family": " | ".join(source_families),
                }
                sources_index.append(
                    build_source_record(
                        metadata["title"],
                        metadata["fullurl"],
                        metadata_classification["page_type"],
                        " | ".join(parent_sources),
                        "candidate_metadata_accepted" if metadata_classification["accepted"] else "candidate_metadata_rejected",
                        metadata_classification["reasons"],
                        discovery_root=" | ".join(discovery_roots),
                        source_family=" | ".join(source_families),
                    )
                )

    candidate_priority = build_candidate_priority()
    deduped_candidates = sorted(
        candidate_origins.keys(),
        key=lambda title: (
            -candidate_priority.get(title, (0, 0))[0],
            -candidate_priority.get(title, (0, 0))[1],
            title.lower(),
        ),
    )
    logger.info("Metadata-classifying %s deduplicated candidate pages", len(deduped_candidates))
    metadata_classify_titles(deduped_candidates)

    if config.category_depth >= 0:
        logger.info("Running category-based discovery from %s root categories (depth=%s)", len(CATEGORY_DISCOVERY_ROOTS), config.category_depth)
        coverage_context["category_discovery_used"] = True
        coverage_context["category_roots"] = CATEGORY_DISCOVERY_ROOTS.copy()
        coverage_context["category_pages"] = []
        category_queue: deque[tuple[str, int, str]] = deque(
            [(f"Category:{title}", 0, title) for title in CATEGORY_DISCOVERY_ROOTS]
        )
        visited_categories: set[str] = set()
        while category_queue:
            category_title, depth, category_root = category_queue.popleft()
            if category_title in visited_categories:
                continue
            visited_categories.add(category_title)
            try:
                members = client.fetch_category_members(category_title)
            except Exception as exc:  # noqa: BLE001
                error_kind = categorize_fetch_error(exc)
                extraction_issues.append(
                    issue_record(category_title, wikipedia_url_for_title(category_title), error_kind, "category", "medium", f"Failed to fetch category members: {exc}")
                )
                sources_index.append(
                    build_source_record(
                        category_title,
                        wikipedia_url_for_title(category_title),
                        "category_index",
                        category_root,
                        error_kind,
                        str(exc),
                        discovery_root=root_page["title"],
                        source_family="category_based",
                    )
                )
                continue

            sources_index.append(
                build_source_record(
                    category_title,
                    wikipedia_url_for_title(category_title),
                    "category_index",
                    category_root,
                    "ok",
                    f"category depth={depth}",
                    discovery_root=root_page["title"],
                    source_family="category_based",
                )
            )
            coverage_context["category_pages"].append(
                {
                    "title": category_title,
                    "depth": depth,
                    "category_root": category_root,
                }
            )

            for member in members:
                member_title = member.get("title", "")
                if not member_title:
                    continue
                namespace = int(member.get("ns", -1))
                if namespace == 14:
                    if depth < config.category_depth and is_relevant_category_title(member_title):
                        category_queue.append((member_title, depth + 1, category_root))
                    continue
                if namespace != 0:
                    continue
                synthetic_link = {
                    "title": member_title,
                    "href": wikipedia_url_for_title(member_title),
                    "text": "",
                }
                accepted, reason, score = classify_candidate_link(synthetic_link)
                if not accepted:
                    continue
                candidate = build_category_candidate_row(
                    title=member_title,
                    url=synthetic_link["href"],
                    category_title=category_title,
                    discovery_root=root_page["title"],
                    category_root=category_root,
                )
                candidate["candidate_score"] = score
                candidate["candidate_reason"] = reason
                candidate_origins[member_title].append(candidate)
                candidate_rows.append(candidate)

        coverage_context["category_pages_traversed"] = len(visited_categories)
        category_priority = build_candidate_priority()
        pending_category_titles = sorted(
            [title for title in candidate_origins.keys() if title not in candidate_statuses],
            key=lambda title: (
                -category_priority.get(title, (0, 0))[0],
                -category_priority.get(title, (0, 0))[1],
                title.lower(),
            ),
        )
        if pending_category_titles:
            logger.info("Metadata-classifying %s category-discovered candidate pages", len(pending_category_titles))
            metadata_classify_titles(pending_category_titles)

    candidate_priority = build_candidate_priority()
    deduped_candidates = sorted(
        candidate_origins.keys(),
        key=lambda title: (
            -candidate_priority.get(title, (0, 0))[0],
            -candidate_priority.get(title, (0, 0))[1],
            title.lower(),
        ),
    )

    accepted_candidate_buckets: dict[str, deque[str]] = defaultdict(deque)
    for title in deduped_candidates:
        status = candidate_statuses.get(title, {})
        if status.get("metadata_accepted"):
            accepted_candidate_buckets[status.get("metadata_page_type", "battle_article")].append(title)

    full_fetch_titles: list[str] = []
    page_type_order = ["battle_article", "war_conflict_article", "campaign_article", "operation_article"]
    while any(accepted_candidate_buckets.values()):
        progressed = False
        for page_type in page_type_order:
            if accepted_candidate_buckets[page_type]:
                full_fetch_titles.append(accepted_candidate_buckets[page_type].popleft())
                progressed = True
        for page_type, bucket in list(accepted_candidate_buckets.items()):
            if page_type not in page_type_order and bucket:
                full_fetch_titles.append(bucket.popleft())
                progressed = True
        if not progressed:
            break
    not_visited_due_bound_titles: list[str] = []
    if config.max_battle_pages and len(full_fetch_titles) > config.max_battle_pages:
        not_visited_due_bound_titles = full_fetch_titles[config.max_battle_pages :]
        full_fetch_titles = full_fetch_titles[: config.max_battle_pages]
        for title in not_visited_due_bound_titles:
            candidate_statuses[title]["full_fetch_status"] = "not_visited_due_bound"
    coverage_context["not_visited_due_bound"] = len(not_visited_due_bound_titles)

    annotate_candidate_rows(candidate_rows, candidate_statuses)
    write_csv(output_dir / "candidate_battle_pages.csv", candidate_rows)

    if args.stop_after_metadata:
        sources_df = pd.DataFrame(sources_index).drop_duplicates()
        sources_df.to_csv(output_dir / "sources_index.csv", index=False, encoding="utf-8-sig")
        issues_df = pd.DataFrame(extraction_issues).drop_duplicates() if extraction_issues else pd.DataFrame(
            columns=["timestamp_utc", "page_title", "source_url", "issue_type", "field_name", "severity", "message", "raw_value"]
        )
        issues_df.to_csv(output_dir / "extraction_issues.csv", index=False, encoding="utf-8-sig")
        logger.info("Stopped after metadata classification by request")
        logger.info("Candidate rows written: %s", len(candidate_rows))
        logger.info("Accepted pages queued for extraction: %s", len(full_fetch_titles) + len(not_visited_due_bound_titles))
        return

    logger.info("Processing %s accepted candidate pages for full extraction", len(full_fetch_titles))

    battles_raw_rows: list[dict[str, Any]] = []
    battles_clean_rows: list[dict[str, Any]] = []
    commander_rows: list[dict[str, Any]] = []
    seen_battle_ids: dict[str, int] = {}
    progress_bar = tqdm(total=len(full_fetch_titles), desc="Extract accepted pages")
    processed_titles = 0
    try:
        for batch_index, title_batch in enumerate(chunked(full_fetch_titles, config.full_fetch_batch_size), start=1):
            logger.info(
                "Starting full-fetch batch %s with %s pages (%s/%s processed so far)",
                batch_index,
                len(title_batch),
                processed_titles,
                len(full_fetch_titles),
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
                        merged_origins = merge_pipe_values(
                            battles_raw_rows[existing_index]["list_page_origin"],
                            clean_row["list_page_origin"],
                        )
                        battles_raw_rows[existing_index]["list_page_origin"] = merged_origins
                        battles_clean_rows[existing_index]["list_page_origin"] = merged_origins
                        battles_raw_rows[existing_index]["parent_list_page"] = merge_pipe_values(
                            battles_raw_rows[existing_index].get("parent_list_page", ""),
                            clean_row.get("parent_list_page", ""),
                        )
                        battles_clean_rows[existing_index]["parent_list_page"] = merge_pipe_values(
                            battles_clean_rows[existing_index].get("parent_list_page", ""),
                            clean_row.get("parent_list_page", ""),
                        )
                        battles_raw_rows[existing_index]["discovery_root"] = merge_pipe_values(
                            battles_raw_rows[existing_index].get("discovery_root", ""),
                            clean_row.get("discovery_root", ""),
                        )
                        battles_clean_rows[existing_index]["discovery_root"] = merge_pipe_values(
                            battles_clean_rows[existing_index].get("discovery_root", ""),
                            clean_row.get("discovery_root", ""),
                        )
                        battles_raw_rows[existing_index]["source_family"] = merge_pipe_values(
                            battles_raw_rows[existing_index].get("source_family", ""),
                            clean_row.get("source_family", ""),
                        )
                        battles_clean_rows[existing_index]["source_family"] = merge_pipe_values(
                            battles_clean_rows[existing_index].get("source_family", ""),
                            clean_row.get("source_family", ""),
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
                            candidate_statuses.get(title, {}).get("pageid"),
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
                "Completed full-fetch batch %s; processed %s/%s pages",
                batch_index,
                processed_titles,
                len(full_fetch_titles),
            )
    finally:
        progress_bar.close()

    annotate_candidate_rows(candidate_rows, candidate_statuses)
    write_csv(output_dir / "candidate_battle_pages.csv", candidate_rows)

    battles_raw_df = pd.DataFrame(battles_raw_rows)
    battles_clean_df = pd.DataFrame(battles_clean_rows)
    commander_df = pd.DataFrame(commander_rows)

    if not battles_clean_df.empty:
        duplicate_ids = battles_clean_df["battle_id"].duplicated().sum()
        if duplicate_ids:
            extraction_issues.append(
                issue_record("", "", "duplicate_battle_id", "battle_id", "high", f"Duplicate battle_id values detected: {duplicate_ids}")
            )

    commander_master_df, commander_master_issues = build_commanders_master(commander_df, config.fuzzy_merge_threshold)
    extraction_issues.extend(commander_master_issues)
    issues_df = pd.DataFrame(extraction_issues).drop_duplicates() if extraction_issues else pd.DataFrame(
        columns=["timestamp_utc", "page_title", "source_url", "issue_type", "field_name", "severity", "message", "raw_value"]
    )

    if not battles_raw_df.empty:
        battles_raw_df = battles_raw_df.sort_values(["battle_name", "source_url"])
    if not battles_clean_df.empty:
        battles_clean_df = battles_clean_df.sort_values(["year", "battle_name"], na_position="last")
    if not commander_df.empty:
        commander_df = commander_df.drop_duplicates(
            subset=["battle_id", "commander_name_normalized", "side", "source_url"]
        )
        commander_df = commander_df.sort_values(["commander_name_normalized", "year", "battle_name"], na_position="last")
    if not commander_master_df.empty:
        commander_master_df = commander_master_df.sort_values(["name_primary"])

    battles_raw_df.to_csv(output_dir / "battles_raw.csv", index=False, encoding="utf-8-sig")
    battles_clean_df.to_csv(output_dir / "battles_clean.csv", index=False, encoding="utf-8-sig")
    commander_df.to_csv(output_dir / "battle_commanders.csv", index=False, encoding="utf-8-sig")
    commander_master_df.to_csv(output_dir / "commanders_master.csv", index=False, encoding="utf-8-sig")
    issues_df.to_csv(output_dir / "extraction_issues.csv", index=False, encoding="utf-8-sig")
    sources_df = pd.DataFrame(sources_index).drop_duplicates()
    sources_df.to_csv(output_dir / "sources_index.csv", index=False, encoding="utf-8-sig")
    run_metrics = compute_run_metrics(
        battles_clean_df,
        commander_df,
        commander_master_df,
        issues_df,
        candidate_rows,
        sources_index,
        coverage_context=coverage_context,
    )
    (output_dir / "run_metrics.json").write_text(json.dumps(run_metrics, ensure_ascii=False, indent=2), encoding="utf-8")

    build_quality_report(
        battles_clean=battles_clean_df if not battles_clean_df.empty else pd.DataFrame(columns=["battle_id", "result_raw", "year", "battle_type"]),
        commanders=commander_df if not commander_df.empty else pd.DataFrame(columns=["battle_id", "commander_wikipedia_url"]),
        commander_master=commander_master_df if not commander_master_df.empty else pd.DataFrame(columns=["commander_id"]),
        issues_df=issues_df if not issues_df.empty else pd.DataFrame(columns=["severity", "page_title", "issue_type", "field_name", "message"]),
        candidate_rows=candidate_rows,
        sources_index=sources_index,
        output_path=output_dir / "data_quality_report.md",
        previous_metrics=previous_metrics,
        coverage_context=coverage_context,
    )

    logger.info("Pipeline complete")
    logger.info("Accepted pages extracted: %s", len(battles_clean_df))
    logger.info("Commander rows extracted: %s", len(commander_df))
    logger.info("Sources logged: %s", len(sources_index))


if __name__ == "__main__":
    main()
