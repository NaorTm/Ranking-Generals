from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parent
HEADLINE_NAMES = [
    "Napoleon Bonaparte",
    "Alexander Suvorov",
    "Jean Lannes",
    "Louis-Nicolas Davout",
    "Khalid ibn al-Walid",
    "Suleiman the Magnificent",
]


def load_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str).fillna("")


def safe_int(value: Any, default: int = 0) -> int:
    text = "" if value is None else str(value).strip()
    if not text:
        return default
    try:
        return int(round(float(text)))
    except ValueError:
        return default


def safe_float(value: Any, default: float = 0.0) -> float:
    text = "" if value is None else str(value).strip()
    if not text:
        return default
    try:
        return float(text)
    except ValueError:
        return default


def safe_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def parse_outcome_summary(text: str) -> dict[str, int]:
    values = {"V": 0, "D": 0, "N": 0, "U": 0}
    for key, raw in re.findall(r"([VDNU])=(\d+)", safe_text(text)):
        values[key] = safe_int(raw)
    return values


def parse_page_mix(text: str) -> dict[str, int]:
    values = {"B": 0, "O": 0, "C": 0, "W": 0}
    for key, raw in re.findall(r"([BOCW])=(\d+)", safe_text(text)):
        values[key] = safe_int(raw)
    return values


def join_nonempty(values: list[str]) -> str:
    return "; ".join([value for value in values if value])


def top_names(frame: pd.DataFrame, count: int) -> str:
    names = frame["display_name"].tolist()[:count]
    return ", ".join(f"`{name}`" for name in names) if names else "`none`"


def build_top200_audit(
    snapshot_dir: Path,
    before_snapshot_dir: Path,
    top_n: int = 200,
) -> dict[str, Any]:
    verification_dir = snapshot_dir / "verification"
    verification_dir.mkdir(parents=True, exist_ok=True)

    current = load_csv(snapshot_dir / "RANKING_RESULTS_SENSITIVITY.csv")
    before = load_csv(before_snapshot_dir / "RANKING_RESULTS_SENSITIVITY.csv")
    current_summary = load_csv(snapshot_dir / "TOP_COMMANDERS_SUMMARY.csv")
    before_summary = load_csv(before_snapshot_dir / "TOP_COMMANDERS_SUMMARY.csv")
    structural_commander = load_csv(verification_dir / "structural_commander_summary.csv")
    structural_rows = load_csv(verification_dir / "structural_row_flags.csv")
    current_annotated = load_csv(snapshot_dir / "derived_scoring" / "commander_engagements_annotated.csv")
    before_annotated = load_csv(before_snapshot_dir / "derived_scoring" / "commander_engagements_annotated.csv")

    current["rank_hierarchical_trust_v2_num"] = current["rank_hierarchical_trust_v2"].map(safe_float)
    current = current.loc[current["rank_hierarchical_trust_v2_num"] > 0].sort_values(
        ["rank_hierarchical_trust_v2_num", "display_name"],
        ascending=[True, True],
    ).head(top_n).copy()

    current = current.merge(
        current_summary[
            [
                "display_name",
                "canonical_wikipedia_url",
                "page_type_exposure_summary",
                "outcome_profile_summary",
            ]
        ],
        on=["display_name", "canonical_wikipedia_url"],
        how="left",
    )

    before_lookup = before[
        [
            "analytic_commander_id",
            "display_name",
            "canonical_wikipedia_url",
            "rank_hierarchical_weighted",
            "rank_hierarchical_trust_v2",
            "trust_tier_v2",
            "trust_confidence_v2",
            "total_engagements_strict",
            "known_outcome_count",
        ]
    ].copy()
    before_lookup = before_lookup.merge(
        before_summary[
            [
                "display_name",
                "canonical_wikipedia_url",
                "page_type_exposure_summary",
                "outcome_profile_summary",
            ]
        ],
        on=["display_name", "canonical_wikipedia_url"],
        how="left",
    )
    before_lookup = before_lookup.rename(
        columns={
            "rank_hierarchical_weighted": "rank_hierarchical_weighted_before",
            "rank_hierarchical_trust_v2": "rank_hierarchical_trust_v2_before",
            "trust_tier_v2": "trust_tier_v2_before",
            "trust_confidence_v2": "trust_confidence_v2_before",
            "total_engagements_strict": "total_engagements_strict_before",
            "known_outcome_count": "known_outcome_count_before",
            "page_type_exposure_summary": "page_type_exposure_summary_before",
            "outcome_profile_summary": "outcome_profile_summary_before",
        }
    )

    audit = current.merge(
        before_lookup,
        on=["analytic_commander_id", "display_name", "canonical_wikipedia_url"],
        how="left",
    ).merge(
        structural_commander,
        on=["analytic_commander_id", "display_name", "canonical_wikipedia_url"],
        how="left",
    )

    current_rows = (
        structural_rows.groupby(["display_name", "canonical_wikipedia_url"])
        .agg(
            structurally_suspect_row_count=("verification_status", lambda s: int((s == "structurally_suspect").sum())),
            verified_broad_row_count=("verification_status", lambda s: int((s == "verified_broad").sum())),
            quarantined_row_count=("verification_status", lambda s: int((s == "quarantined").sum())),
        )
        .reset_index()
    )
    audit = audit.merge(current_rows, on=["display_name", "canonical_wikipedia_url"], how="left")

    battle_breakdown_now = (
        current_annotated.loc[
            current_annotated["eligible_strict"].eq("1")
            & current_annotated["page_type"].eq("battle_article")
        ]
        .groupby(["display_name", "canonical_wikipedia_url"])
        .agg(
            battle_rows_now=("battle_id", "count"),
            battle_known_outcomes_now=("known_outcome_flag", lambda s: int((s == "1").sum())),
            battle_unknown_rows_now=("known_outcome_flag", lambda s: int((s != "1").sum())),
        )
        .reset_index()
    )
    battle_breakdown_before = (
        before_annotated.loc[
            before_annotated["eligible_strict"].eq("1")
            & before_annotated["page_type"].eq("battle_article")
        ]
        .groupby(["display_name", "canonical_wikipedia_url"])
        .agg(
            battle_rows_before=("battle_id", "count"),
            battle_known_outcomes_before=("known_outcome_flag", lambda s: int((s == "1").sum())),
            battle_unknown_rows_before=("known_outcome_flag", lambda s: int((s != "1").sum())),
        )
        .reset_index()
    )
    audit = audit.merge(battle_breakdown_now, on=["display_name", "canonical_wikipedia_url"], how="left")
    audit = audit.merge(battle_breakdown_before, on=["display_name", "canonical_wikipedia_url"], how="left")

    for column in [
        "total_rows",
        "verified_core_rows",
        "verified_broad_rows",
        "structurally_suspect_rows",
        "quarantined_rows",
        "structurally_suspect_row_count",
        "verified_broad_row_count",
        "quarantined_row_count",
        "battle_rows_now",
        "battle_known_outcomes_now",
        "battle_unknown_rows_now",
        "battle_rows_before",
        "battle_known_outcomes_before",
        "battle_unknown_rows_before",
        "rank_hierarchical_trust_v2",
        "rank_hierarchical_weighted",
        "rank_hierarchical_trust_v2_before",
        "rank_hierarchical_weighted_before",
        "known_outcome_count",
        "known_outcome_count_before",
        "total_engagements_strict",
        "total_engagements_strict_before",
    ]:
        if column not in audit.columns:
            audit[column] = ""

    risk_rows: list[dict[str, Any]] = []
    for _, row in audit.iterrows():
        current_rank = safe_int(row["rank_hierarchical_trust_v2"], 9999)
        weighted_rank_now = safe_int(row["rank_hierarchical_weighted"], 9999)
        trust_rank_before = safe_int(row["rank_hierarchical_trust_v2_before"], weighted_rank_now)
        weighted_rank_before = safe_int(row["rank_hierarchical_weighted_before"], weighted_rank_now)

        engagements_now = safe_int(row["total_engagements_strict"])
        engagements_before = safe_int(row["total_engagements_strict_before"])
        known_now = safe_int(row["known_outcome_count"])
        known_before = safe_int(row["known_outcome_count_before"])

        current_page_mix = parse_page_mix(row["page_type_exposure_summary"])
        before_page_mix = parse_page_mix(row["page_type_exposure_summary_before"])
        current_outcomes = parse_outcome_summary(row["outcome_profile_summary"])
        before_outcomes = parse_outcome_summary(row["outcome_profile_summary_before"])

        structural_suspect = safe_int(row["structurally_suspect_row_count"] or row["structurally_suspect_rows"])
        broad_rows = safe_int(row["verified_broad_row_count"] or row["verified_broad_rows"])
        total_rows = max(safe_int(row["total_rows"]), engagements_now, 1)
        suspect_share = structural_suspect / total_rows
        broad_share = broad_rows / total_rows

        trust_rank_delta = current_rank - trust_rank_before if trust_rank_before else 0
        weighted_rank_delta = weighted_rank_now - weighted_rank_before if weighted_rank_before else 0
        engagement_drop = max(engagements_before - engagements_now, 0)
        outcome_drop = max(known_before - known_now, 0)
        war_drop = max(before_page_mix["W"] - current_page_mix["W"], 0)
        campaign_drop = max(before_page_mix["C"] - current_page_mix["C"], 0)
        victory_drop = max(before_outcomes["V"] - current_outcomes["V"], 0)
        defeat_drop = max(before_outcomes["D"] - current_outcomes["D"], 0)

        structural_flags: list[str] = []
        outcome_flags: list[str] = []

        if structural_suspect > 0:
            structural_flags.append(f"{structural_suspect} structurally suspect rows")
        if broad_rows > 0:
            structural_flags.append(f"{broad_rows} downgraded broad rows")
        if war_drop > 0:
            structural_flags.append(f"war-page reduction {before_page_mix['W']}→{current_page_mix['W']}")
        if campaign_drop > 0:
            structural_flags.append(f"campaign reduction {before_page_mix['C']}→{current_page_mix['C']}")
        if engagement_drop >= 3:
            structural_flags.append(f"strict engagements reduced by {engagement_drop}")
        if abs(trust_rank_delta) >= 5 or abs(weighted_rank_delta) >= 5:
            structural_flags.append("rank moved materially after verification")

        if current_outcomes["D"] == 0 and current_outcomes["U"] >= 3 and current_rank <= 50:
            outcome_flags.append("clean record with unresolved battle outcomes")
        if victory_drop >= 3:
            outcome_flags.append(f"victory count dropped by {victory_drop}")
        if outcome_drop >= 3:
            outcome_flags.append(f"known outcomes dropped by {outcome_drop}")
        if safe_int(row["battle_unknown_rows_now"]) >= 3 and current_rank <= 50:
            outcome_flags.append("multiple surviving battle pages still unresolved")
        if safe_text := str(row.get("trust_confidence_v2", "")).strip().lower():
            if safe_text in {"moderate", "caution"} and current_rank <= 25:
                outcome_flags.append("headline rank with softened trust confidence")

        risk_score = 0
        risk_score += round(suspect_share * 50)
        risk_score += round(broad_share * 20)
        risk_score += min(engagement_drop, 8)
        risk_score += min(outcome_drop, 6)
        risk_score += min(victory_drop, 6)
        if abs(trust_rank_delta) >= 10 or abs(weighted_rank_delta) >= 10:
            risk_score += 5
        elif abs(trust_rank_delta) >= 5 or abs(weighted_rank_delta) >= 5:
            risk_score += 3
        if current_rank <= 10:
            risk_score += 3
        elif current_rank <= 25:
            risk_score += 2
        if current_outcomes["D"] == 0 and current_outcomes["U"] >= 3:
            risk_score += 3
        if row.get("trust_tier_v2", "") not in {"robust_elite_core", "strong_upper_tier"} and current_rank <= 25:
            risk_score += 3

        if (
            (current_rank <= 25 and (suspect_share >= 0.20 or engagement_drop >= 8))
            or (current_rank <= 15 and structural_suspect >= 5)
            or (current_rank <= 25 and len(outcome_flags) >= 2 and structural_suspect >= 2)
            or (current_rank <= 50 and row.get("trust_confidence_v2", "") in {"moderate", "caution"} and len(outcome_flags) >= 2)
        ):
            risk_band = "high_priority_manual_audit"
        elif (
            structural_suspect == 0
            and broad_rows <= 2
            and engagement_drop <= 3
            and outcome_drop <= 2
            and abs(trust_rank_delta) <= 5
            and abs(weighted_rank_delta) <= 5
            and len(outcome_flags) <= 1
        ):
            risk_band = "structurally_clean"
        elif (
            structural_suspect <= 3
            and suspect_share < 0.15
            and broad_share < 0.30
            and engagement_drop <= 5
            and len(outcome_flags) <= 2
            and abs(trust_rank_delta) < 10
            and abs(weighted_rank_delta) < 10
        ):
            risk_band = "mildly_inflated"
        else:
            risk_band = "materially_inflated"

        verification_sensitivity = "stable"
        if abs(trust_rank_delta) >= 10 or abs(weighted_rank_delta) >= 10 or engagement_drop >= 8:
            verification_sensitivity = "high"
        elif abs(trust_rank_delta) >= 4 or abs(weighted_rank_delta) >= 4 or engagement_drop >= 3 or broad_rows > 0:
            verification_sensitivity = "moderate"

        risk_rows.append(
            {
                "display_name": row["display_name"],
                "canonical_wikipedia_url": row["canonical_wikipedia_url"],
                "primary_era_bucket": row["primary_era_bucket"],
                "current_trust_rank": current_rank,
                "current_weighted_rank": weighted_rank_now,
                "trust_rank_before_verification": trust_rank_before if trust_rank_before != 9999 else "",
                "weighted_rank_before_verification": weighted_rank_before if weighted_rank_before != 9999 else "",
                "trust_rank_delta": trust_rank_delta if trust_rank_before != 9999 else "",
                "weighted_rank_delta": weighted_rank_delta if weighted_rank_before != 9999 else "",
                "trust_tier_current": row["trust_tier_v2"],
                "trust_tier_before_verification": row["trust_tier_v2_before"],
                "trust_confidence_current": row["trust_confidence_v2"],
                "trust_confidence_before_verification": row["trust_confidence_v2_before"],
                "strict_engagement_count_current": engagements_now,
                "strict_engagement_count_before_verification": engagements_before,
                "page_type_mix_current": row["page_type_exposure_summary"],
                "page_type_mix_before_verification": row["page_type_exposure_summary_before"],
                "known_outcome_count_current": known_now,
                "known_outcome_count_before_verification": known_before,
                "outcome_profile_current": row["outcome_profile_summary"],
                "outcome_profile_before_verification": row["outcome_profile_summary_before"],
                "structurally_suspect_rows": structural_suspect,
                "broad_or_downgraded_rows": broad_rows,
                "quarantined_rows": safe_int(row["quarantined_row_count"] or row["quarantined_rows"]),
                "verification_sensitivity": verification_sensitivity,
                "inflation_risk_band": risk_band,
                "risk_score": risk_score,
                "structural_risk_notes": join_nonempty(structural_flags),
                "outcome_risk_notes": join_nonempty(outcome_flags),
                "manual_outcome_audit_priority": "yes" if risk_band == "high_priority_manual_audit" or len(outcome_flags) >= 2 else "no",
            }
        )

    result = pd.DataFrame(risk_rows).sort_values(
        ["risk_score", "current_trust_rank", "display_name"],
        ascending=[False, True, True],
    )
    result.to_csv(verification_dir / "TOP200_VERIFICATION_AUDIT.csv", index=False, encoding="utf-8-sig")

    priority = result.loc[
        (result["manual_outcome_audit_priority"] == "yes")
        | result["inflation_risk_band"].isin(["materially_inflated", "high_priority_manual_audit"])
    ].copy()
    priority = priority.sort_values(["risk_score", "current_trust_rank"], ascending=[False, True])
    priority.to_csv(verification_dir / "TOP200_OUTCOME_AUDIT_PRIORITY.csv", index=False, encoding="utf-8-sig")

    affected = result.loc[
        result["inflation_risk_band"].ne("structurally_clean")
        | result["trust_rank_delta"].astype(str).ne("")
    ].copy()
    affected = affected.sort_values(["current_trust_rank", "risk_score"], ascending=[True, False])
    affected.to_csv(verification_dir / "TOP200_AFFECTED_MOVEMENT.csv", index=False, encoding="utf-8-sig")

    clean = result.loc[result["inflation_risk_band"] == "structurally_clean"].sort_values("current_trust_rank")
    mild = result.loc[result["inflation_risk_band"] == "mildly_inflated"].sort_values(["current_trust_rank", "risk_score"])
    material = result.loc[result["inflation_risk_band"] == "materially_inflated"].sort_values(["risk_score", "current_trust_rank"], ascending=[False, True])
    high_priority = result.loc[result["inflation_risk_band"] == "high_priority_manual_audit"].sort_values(["risk_score", "current_trust_rank"], ascending=[False, True])
    headline = result.loc[result["display_name"].isin(HEADLINE_NAMES)].sort_values("current_trust_rank")

    memo_lines = [
        "# Top 200 Verification Audit Memo",
        "",
        f"Audit base: `{snapshot_dir.name}`",
        f"Before-verification comparison base: `{before_snapshot_dir.name}`",
        "",
        "## Overall",
        "",
        f"- Top 200 commanders reviewed in the current verified trust ranking.",
        f"- Structurally clean: `{len(clean)}`",
        f"- Mildly inflated: `{len(mild)}`",
        f"- Materially inflated: `{len(material)}`",
        f"- High-priority for manual audit: `{len(high_priority)}`",
        "",
        "## Structurally Clean",
        "",
        f"The cleanest current top-end cases are {top_names(clean, 10)}.",
        "",
        "## Mildly Inflated",
        "",
        f"The main mild-inflation cluster is {top_names(mild, 12)}.",
        "",
        "## Materially Inflated",
        "",
        f"The strongest structural-inflation concerns are {top_names(material, 12)}.",
        "",
        "## High-Priority Manual Outcome Audit",
        "",
        f"The most important next outcome-review cases are {top_names(high_priority, 12)}.",
        "",
        "## Headline Figures",
        "",
    ]

    for _, row in headline.iterrows():
        memo_lines.append(
            f"- `{row['display_name']}`: `{row['inflation_risk_band']}`, rank `{row['current_trust_rank']}`, "
            f"tier `{row['trust_tier_current']}`, confidence `{row['trust_confidence_current']}`. "
            f"{join_nonempty([row['structural_risk_notes'], row['outcome_risk_notes']]) or 'No major audit warning flags.'}"
        )

    memo_lines.extend(
        [
            "",
            "## Bottom Line",
            "",
            "This audit is a global top-of-ranking review, not a Suleiman-only patch. "
            "Commanders in the clean bucket now look broadly defensible under the current verification layer, "
            "while the material and high-priority buckets are the cases where DB structure or outcome interpretation "
            "still appears capable of overstating current placement.",
            "",
        ]
    )
    (verification_dir / "TOP200_VERIFICATION_MEMO.md").write_text("\n".join(memo_lines), encoding="utf-8")

    summary = {
        "snapshot": snapshot_dir.name,
        "before_snapshot": before_snapshot_dir.name,
        "top_n": top_n,
        "risk_band_counts": result["inflation_risk_band"].value_counts().to_dict(),
        "headline_figures": headline[
            [
                "display_name",
                "current_trust_rank",
                "trust_tier_current",
                "trust_confidence_current",
                "inflation_risk_band",
            ]
        ].to_dict(orient="records"),
    }
    (verification_dir / "TOP200_VERIFICATION_SUMMARY.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a top-200 verification risk audit from the verified ranking snapshot.")
    parser.add_argument("--snapshot-dir", type=Path, required=True)
    parser.add_argument("--before-snapshot-dir", type=Path, required=True)
    parser.add_argument("--top-n", type=int, default=200)
    args = parser.parse_args()

    snapshot_dir = (ROOT / args.snapshot_dir).resolve() if not args.snapshot_dir.is_absolute() else args.snapshot_dir
    before_snapshot_dir = (ROOT / args.before_snapshot_dir).resolve() if not args.before_snapshot_dir.is_absolute() else args.before_snapshot_dir
    summary = build_top200_audit(snapshot_dir, before_snapshot_dir, top_n=args.top_n)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
