from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path
from typing import Any
from urllib.parse import quote, unquote, urlparse

import pandas as pd


WIKIPEDIA_BASE = "https://en.wikipedia.org/wiki/"
NONWAR_PAGE_TYPES = {"battle_article", "campaign_article", "operation_article"}
BROAD_PAGE_PATTERNS = (
    " wars",
    " war ",
    "campaigns",
    "rebellions",
    "revolts",
    "uprisings",
    "expeditions",
    "operations",
)
CAMPAIGN_BROAD_PATTERNS = (
    "campaign",
    "campaigns",
    "expedition",
    "expeditions",
    "operations",
    "offensive",
    "invasion",
)


def canonicalize_wikipedia_url(url: Any) -> str:
    text = "" if url is None else str(url).strip()
    if not text:
        return ""
    parsed = urlparse(text)
    path = unquote(parsed.path)
    if path.startswith("/wiki/"):
        title = path[len("/wiki/") :].replace("_", " ")
        return f"{WIKIPEDIA_BASE}{quote(title.replace(' ', '_'))}"
    return text.rstrip("/")


def safe_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def parse_year(value: Any) -> float | None:
    text = safe_text(value)
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def split_flags(value: Any) -> list[str]:
    text = safe_text(value)
    if not text:
        return []
    parts = re.split(r"[|;]", text)
    return [part.strip() for part in parts if part.strip()]


def join_flags(flags: list[str]) -> str:
    return "|".join(sorted(dict.fromkeys(flag for flag in flags if flag)))


def title_is_broad(title: str) -> bool:
    lowered = safe_text(title).lower()
    return any(token in lowered for token in BROAD_PAGE_PATTERNS)


def title_is_broad_campaign(title: str) -> bool:
    lowered = safe_text(title).lower()
    return any(token in lowered for token in CAMPAIGN_BROAD_PATTERNS)


def title_mentions_commander(title: str, display_name: str) -> bool:
    title_lower = safe_text(title).lower()
    name_lower = safe_text(display_name).lower()
    if not title_lower or not name_lower:
        return False
    if name_lower in title_lower:
        return True
    tokens = [token for token in re.split(r"[^a-z0-9]+", name_lower) if token and token not in {"the", "of", "and"}]
    return any(len(token) >= 5 and token in title_lower for token in tokens[:3])


def load_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str).fillna("")


def audit_stage_ok(summary_path: Path, expected_rows: int) -> bool:
    if not summary_path.exists():
        return False
    try:
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    rows_checked = int(summary.get("rows_checked") or summary.get("master_rows_checked") or 0)
    return rows_checked >= expected_rows


def build_verification_layer(
    snapshot_dir: Path,
    battle_audit_dir: Path | None = None,
    commander_audit_dir: Path | None = None,
) -> dict[str, Any]:
    verification_dir = snapshot_dir / "verification"
    verification_dir.mkdir(parents=True, exist_ok=True)

    battle_audit_dir = battle_audit_dir or (snapshot_dir / "postfix_audit")
    commander_audit_dir = commander_audit_dir or (snapshot_dir / "commander_postfix_audit")

    battles = load_csv(snapshot_dir / "battles_clean.csv")
    commanders = load_csv(snapshot_dir / "battle_commanders.csv")
    master = load_csv(snapshot_dir / "commanders_master.csv")
    annotated = load_csv(snapshot_dir / "derived_scoring" / "commander_engagements_annotated.csv")
    engagement_summary = load_csv(snapshot_dir / "derived_scoring" / "commander_engagement_summary.csv")

    battle_audit = load_csv(battle_audit_dir / "row_audit.csv") if (battle_audit_dir / "row_audit.csv").exists() else pd.DataFrame(columns=["battle_id", "status", "blockers"])
    commander_row_audit = load_csv(commander_audit_dir / "row_audit.csv") if (commander_audit_dir / "row_audit.csv").exists() else pd.DataFrame(columns=["battle_id", "commander_wikipedia_url", "commander_name_normalized", "status", "blockers"])
    commander_master_audit = load_csv(commander_audit_dir / "master_audit.csv") if (commander_audit_dir / "master_audit.csv").exists() else pd.DataFrame(columns=["wikipedia_page", "name_primary", "status", "blockers"])

    battle_blocker_map = {
        safe_text(row["battle_id"]): split_flags(row.get("blockers", ""))
        for _, row in battle_audit.iterrows()
        if safe_text(row.get("status")) == "blocker"
    }

    commander_blocker_url_keys = {
        (safe_text(row["battle_id"]), canonicalize_wikipedia_url(row.get("commander_wikipedia_url", ""))): split_flags(row.get("blockers", ""))
        for _, row in commander_row_audit.iterrows()
        if safe_text(row.get("status")) == "blocker" and canonicalize_wikipedia_url(row.get("commander_wikipedia_url", ""))
    }
    commander_blocker_name_keys = {
        (safe_text(row["battle_id"]), safe_text(row.get("commander_name_normalized", "")).lower()): split_flags(row.get("blockers", ""))
        for _, row in commander_row_audit.iterrows()
        if safe_text(row.get("status")) == "blocker"
    }

    master_blocker_urls = {
        canonicalize_wikipedia_url(row.get("wikipedia_page", "")): split_flags(row.get("blockers", ""))
        for _, row in commander_master_audit.iterrows()
        if safe_text(row.get("status")) == "blocker" and canonicalize_wikipedia_url(row.get("wikipedia_page", ""))
    }
    master_blocker_names = {
        safe_text(row.get("name_primary", "")).lower(): split_flags(row.get("blockers", ""))
        for _, row in commander_master_audit.iterrows()
        if safe_text(row.get("status")) == "blocker"
    }

    nonwar = annotated.loc[
        annotated["page_type"].isin(NONWAR_PAGE_TYPES)
        & annotated["analytic_year"].ne("")
        & annotated["eligible_strict"].eq("1")
    ].copy()
    if nonwar.empty:
        nonwar_window = pd.DataFrame(columns=["analytic_commander_id", "first_nonwar_year", "last_nonwar_year", "nonwar_anchor_count"])
    else:
        nonwar["analytic_year_num"] = pd.to_numeric(nonwar["analytic_year"], errors="coerce")
        nonwar_window = (
            nonwar.dropna(subset=["analytic_year_num"])
            .groupby("analytic_commander_id")
            .agg(
                first_nonwar_year=("analytic_year_num", "min"),
                last_nonwar_year=("analytic_year_num", "max"),
                nonwar_anchor_count=("analytic_year_num", "count"),
            )
            .reset_index()
        )

    annotated = annotated.merge(nonwar_window, on="analytic_commander_id", how="left")

    battle_anchor_by_overlap = (
        annotated.loc[
            annotated["page_type"].eq("battle_article")
            & annotated["eligible_strict"].eq("1")
        ]
        .groupby(["analytic_commander_id", "hierarchy_overlap_key"])
        .size()
        .to_dict()
    )

    summary_counts = (
        engagement_summary[["analytic_commander_id", "total_battle_pages_strict", "total_war_pages_strict", "total_campaign_pages_strict"]]
        .rename(
            columns={
                "total_battle_pages_strict": "summary_battle_pages_strict",
                "total_war_pages_strict": "summary_war_pages_strict",
                "total_campaign_pages_strict": "summary_campaign_pages_strict",
            }
        )
    )
    annotated = annotated.merge(summary_counts, on="analytic_commander_id", how="left")
    battle_anchor_by_year = (
        annotated.loc[
            annotated["page_type"].eq("battle_article")
            & annotated["eligible_strict"].eq("1")
            & annotated["analytic_year"].ne("")
        ]
        .groupby(["analytic_commander_id", "analytic_year"])
        .size()
        .to_dict()
    )

    structural_rows: list[dict[str, Any]] = []
    commander_status_counter: dict[str, int] = {}

    for _, row in annotated.iterrows():
        battle_id = safe_text(row["battle_id"])
        display_name = safe_text(row["display_name"])
        canonical_url = canonicalize_wikipedia_url(row.get("canonical_wikipedia_url", ""))
        page_type = safe_text(row["page_type"])
        title = safe_text(row["battle_name"])
        flags = split_flags(row.get("exclude_reason_flags", ""))

        battle_blockers = battle_blocker_map.get(battle_id, [])
        commander_blockers = commander_blocker_url_keys.get((battle_id, canonical_url), [])
        if not commander_blockers:
            commander_blockers = commander_blocker_name_keys.get((battle_id, display_name.lower()), [])
        master_blockers = master_blocker_urls.get(canonical_url, []) or master_blocker_names.get(display_name.lower(), [])

        if battle_blockers:
            flags.append("battle_row_blocker")
        if commander_blockers:
            flags.append("commander_row_blocker")
        if master_blockers:
            flags.append("commander_master_blocker")

        if safe_text(row.get("side")) == "multiple_sides" or "ambiguous_multi_side_commander" in split_flags(row.get("exclude_reason_flags", "")):
            flags.append("multi_side_ambiguity")

        analytic_year = parse_year(row.get("analytic_year"))
        first_nonwar_year = parse_year(row.get("first_nonwar_year"))
        last_nonwar_year = parse_year(row.get("last_nonwar_year"))
        overlap_key = safe_text(row.get("hierarchy_overlap_key"))
        overlap_battle_anchor_count = int(battle_anchor_by_overlap.get((safe_text(row["analytic_commander_id"]), overlap_key), 0))

        if page_type == "war_conflict_article" and analytic_year is not None and first_nonwar_year is not None and last_nonwar_year is not None:
            if analytic_year < first_nonwar_year - 5 or analytic_year > last_nonwar_year + 5:
                flags.append("commander_outside_page_chronology")

        if page_type != "battle_article" and overlap_battle_anchor_count > 0:
            flags.append("duplicate_hierarchy_credit")

        if page_type == "war_conflict_article" and title_is_broad(title):
            flags.append("commander_attached_to_too_broad_page")
            if overlap_battle_anchor_count > 0 or "commander_outside_page_chronology" in flags:
                flags.append("umbrella_war_inflation")

        same_year_battle_anchor_count = int(
            battle_anchor_by_year.get((safe_text(row["analytic_commander_id"]), safe_text(row.get("analytic_year"))), 0)
        )
        if page_type == "campaign_article":
            flags.append("campaign_page_not_core")
            if overlap_battle_anchor_count > 0 or same_year_battle_anchor_count > 0:
                flags.append("duplicate_hierarchy_credit")
                flags.append("same_year_campaign_overlap")
            if title_is_broad_campaign(title):
                flags.append("commander_attached_to_too_broad_page")
            if title_mentions_commander(title, display_name):
                flags.append("commander_named_campaign_duplicate")
            if "same_year_campaign_overlap" in flags and (
                "commander_named_campaign_duplicate" in flags
                or "commander_attached_to_too_broad_page" in flags
            ):
                flags.append("umbrella_war_inflation")

        status = "verified_core"
        action = "keep"
        if any(flag in flags for flag in ["battle_row_blocker", "commander_row_blocker", "commander_master_blocker"]):
            status = "quarantined"
            action = "quarantine"
        elif any(
            flag in flags
            for flag in [
                "commander_outside_page_chronology",
                "umbrella_war_inflation",
                "commander_named_campaign_duplicate",
            ]
        ):
            status = "structurally_suspect"
            action = "remove_from_ranking_only"
        elif any(
            flag in flags
            for flag in [
                "duplicate_hierarchy_credit",
                "commander_attached_to_too_broad_page",
                "campaign_page_not_core",
            ]
        ):
            status = "verified_broad"
            action = "downgrade"

        strict_include_override = "1" if status == "verified_core" else "0"
        balanced_include_override = "1" if status in {"verified_core", "verified_broad"} else "0"

        structural_rows.append(
            {
                "analytic_commander_id": safe_text(row["analytic_commander_id"]),
                "display_name": display_name,
                "canonical_wikipedia_url": canonical_url,
                "battle_id": battle_id,
                "battle_name": title,
                "page_type": page_type,
                "analytic_year": safe_text(row.get("analytic_year")),
                "first_nonwar_year": safe_text(row.get("first_nonwar_year")),
                "last_nonwar_year": safe_text(row.get("last_nonwar_year")),
                "overlap_battle_anchor_count": overlap_battle_anchor_count,
                "verification_status": status,
                "recommended_action": action,
                "verification_issue_flags": join_flags(flags),
                "strict_include_override": strict_include_override,
                "balanced_include_override": balanced_include_override,
            }
        )
        commander_status_counter[status] = commander_status_counter.get(status, 0) + 1

    structural_df = pd.DataFrame(structural_rows)
    structural_df.to_csv(verification_dir / "structural_row_flags.csv", index=False, encoding="utf-8-sig")

    commander_summary = (
        structural_df.groupby(["analytic_commander_id", "display_name", "canonical_wikipedia_url"], dropna=False)
        .agg(
            total_rows=("battle_id", "count"),
            verified_core_rows=("verification_status", lambda s: int((s == "verified_core").sum())),
            verified_broad_rows=("verification_status", lambda s: int((s == "verified_broad").sum())),
            structurally_suspect_rows=("verification_status", lambda s: int((s == "structurally_suspect").sum())),
            quarantined_rows=("verification_status", lambda s: int((s == "quarantined").sum())),
        )
        .reset_index()
    )
    commander_summary["dominant_verification_status"] = commander_summary.apply(
        lambda row: "quarantined"
        if row["quarantined_rows"] > 0
        else "structurally_suspect"
        if row["structurally_suspect_rows"] > 0
        else "verified_broad"
        if row["verified_broad_rows"] > 0
        else "verified_core",
        axis=1,
    )
    commander_summary.to_csv(verification_dir / "structural_commander_summary.csv", index=False, encoding="utf-8-sig")

    verified_commander_eligibility = structural_df[
        [
            "analytic_commander_id",
            "battle_id",
            "verification_status",
            "recommended_action",
            "verification_issue_flags",
            "strict_include_override",
            "balanced_include_override",
        ]
    ].copy()
    verified_commander_eligibility.to_csv(
        verification_dir / "verified_commander_ranking_eligibility.csv",
        index=False,
        encoding="utf-8-sig",
    )

    battle_status_rows: list[dict[str, Any]] = []
    for _, row in battles.iterrows():
        battle_id = safe_text(row["battle_id"])
        battle_blockers = battle_blocker_map.get(battle_id, [])
        status = "quarantined" if battle_blockers else "verified_core"
        battle_status_rows.append(
            {
                "battle_id": battle_id,
                "battle_name": safe_text(row["battle_name"]),
                "verification_status": status,
                "verification_issue_flags": join_flags(["battle_row_blocker", *battle_blockers]) if battle_blockers else "",
                "strict_gate_override": "0" if battle_blockers else "1",
                "balanced_gate_override": "0" if battle_blockers else "1",
            }
        )
    verified_battle_eligibility = pd.DataFrame(battle_status_rows)
    verified_battle_eligibility.to_csv(
        verification_dir / "verified_battle_eligibility.csv",
        index=False,
        encoding="utf-8-sig",
    )

    battle_audit_summary = json.loads((battle_audit_dir / "summary.json").read_text(encoding="utf-8")) if (battle_audit_dir / "summary.json").exists() else {}
    commander_audit_summary = json.loads((commander_audit_dir / "summary.json").read_text(encoding="utf-8")) if (commander_audit_dir / "summary.json").exists() else {}

    summary = {
        "snapshot": snapshot_dir.name,
        "battle_rows": int(len(battles)),
        "commander_rows": int(len(commanders)),
        "master_rows": int(len(master)),
        "annotated_rows": int(len(annotated)),
        "battle_audit_summary": battle_audit_summary,
        "commander_audit_summary": commander_audit_summary,
        "verification_status_counts": {
            key: int(value) for key, value in sorted(commander_status_counter.items())
        },
        "battle_verification_counts": {
            key: int(value)
            for key, value in verified_battle_eligibility["verification_status"].value_counts().to_dict().items()
        },
    }
    (verification_dir / "verification_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    manifest = {
        "snapshot": snapshot_dir.name,
        "sources": {
            "battle_audit_dir": str(battle_audit_dir),
            "commander_audit_dir": str(commander_audit_dir),
            "annotated_source": str(snapshot_dir / "derived_scoring" / "commander_engagements_annotated.csv"),
        },
        "outputs": {
            "verified_battle_eligibility": str(verification_dir / "verified_battle_eligibility.csv"),
            "verified_commander_ranking_eligibility": str(verification_dir / "verified_commander_ranking_eligibility.csv"),
            "structural_row_flags": str(verification_dir / "structural_row_flags.csv"),
            "structural_commander_summary": str(verification_dir / "structural_commander_summary.csv"),
            "verification_summary": str(verification_dir / "verification_summary.json"),
        },
    }
    (verification_dir / "verification_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Build verified ranking-eligibility layers from existing audit outputs.")
    parser.add_argument("--snapshot-dir", type=Path, required=True)
    parser.add_argument("--battle-audit-dir", type=Path, default=None)
    parser.add_argument("--commander-audit-dir", type=Path, default=None)
    args = parser.parse_args()

    summary = build_verification_layer(
        snapshot_dir=args.snapshot_dir,
        battle_audit_dir=args.battle_audit_dir,
        commander_audit_dir=args.commander_audit_dir,
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
