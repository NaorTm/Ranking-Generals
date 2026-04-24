from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


DEFAULT_SNAPSHOT = Path("outputs_improved_2026-04-24_upgrade_pass2_role_highlevel")

BROAD_PAGE_TYPES = {
    "operation_article",
    "campaign_article",
    "war_conflict_article",
    "invasion_article",
    "conquest_article",
    "uprising_or_revolt_article",
    "broad_conflict_article",
}
BATTLE_OR_SIEGE_PAGE_TYPES = {"battle_article", "naval_battle_article", "siege_article"}
CAP_BROAD_SHARE = 0.40
TOP100_BROAD_THRESHOLD = 0.40
WEAK_BATTLE_SIEGE_THRESHOLD = 0.35

# Manual first-pass review for commanders that are 100% broad-page dependent.
# This is intentionally conservative and should be replaced by a curated role file later.
MANUAL_ROLE_OVERRIDES = {
    "Abu Mohammad al-Julani": (
        "ambiguous_or_hybrid_political_military_leader",
        "ambiguous_requires_review",
        False,
        "Hybrid insurgent/political-military leader with no battle/siege contribution in this snapshot; keep only as caveated operational sensitivity until role evidence is curated.",
    ),
    "Hulusi Akar": (
        "modern_officeholder_or_staff_leader",
        "staff_or_planning_only",
        True,
        "Modern chief/minister profile represented only through high-level pages; not enough field-command evidence for headline ranking.",
    ),
    "Lê Duẩn": (
        "political_leader",
        "political_or_nominal_only",
        True,
        "Political leadership case with 100% broad-page dependency; exclude from headline commander ranking unless direct command evidence is added.",
    ),
    "Ghiath Dalla": (
        "modern_operational_commander_uncurated",
        "ambiguous_requires_review",
        False,
        "Modern commander represented only by operation pages; requires role verification before headline use.",
    ),
    "Ashfaq Parvez Kayani": (
        "modern_officeholder_or_staff_leader",
        "staff_or_planning_only",
        True,
        "Army-chief/staff-office profile with no battle/siege support in this snapshot; exclude from headline ranking unless field command is verified.",
    ),
    "Phạm Văn Đồng": (
        "political_leader",
        "political_or_nominal_only",
        True,
        "Political leadership case with 100% broad-page dependency; exclude from headline commander ranking.",
    ),
    "Đỗ Cao Trí": (
        "genuine_military_commander_operational",
        "eligible_operational_commander",
        False,
        "Military commander profile, but current support is entirely high-level; keep as operational sensitivity with caveat.",
    ),
    "Jonas Savimbi": (
        "ambiguous_or_hybrid_political_military_leader",
        "ambiguous_requires_review",
        False,
        "Political-military insurgent leader represented only by broad pages; requires role and event-level verification.",
    ),
    "Leonid Brezhnev": (
        "political_leader",
        "political_or_nominal_only",
        True,
        "Political head-of-state profile with no battle/siege command support; exclude from headline ranking.",
    ),
    "Mikhail Frunze": (
        "genuine_military_commander_and_theorist",
        "eligible_operational_commander",
        False,
        "Military commander/theorist profile, but this snapshot supports him only through high-level pages; keep as caveated operational sensitivity.",
    ),
    "Hakimullah Mehsud": (
        "ambiguous_or_hybrid_political_military_leader",
        "ambiguous_requires_review",
        False,
        "Militant leader represented only by operation pages; requires command-role verification.",
    ),
    "Hjalmar Siilasvuo": (
        "genuine_military_commander_operational",
        "eligible_operational_commander",
        False,
        "Genuine military commander, but current score is operation/war-page only; keep as caveated operational sensitivity.",
    ),
    "Qianlong Emperor": (
        "monarch_or_political_leader",
        "political_or_nominal_only",
        True,
        "Monarch profile with 100% broad-page dependency; exclude from headline ranking unless direct field command is verified.",
    ),
    "Italo Gariboldi": (
        "genuine_military_commander_operational",
        "eligible_operational_commander",
        False,
        "Military commander profile, but current evidence is high-level only; keep as caveated operational sensitivity.",
    ),
    "Lothar Rendulic": (
        "genuine_military_commander_operational",
        "eligible_operational_commander",
        False,
        "Military commander profile, but current contribution is entirely high-level; keep as caveated operational sensitivity.",
    ),
    "Maria Theresa": (
        "monarch_or_political_leader",
        "political_or_nominal_only",
        True,
        "Political/monarchical leadership case with no battle/siege command support; exclude from headline ranking.",
    ),
    "Gusztáv Jány": (
        "genuine_military_commander_operational",
        "eligible_operational_commander",
        False,
        "Military commander profile, but current support is high-level only; keep as caveated operational sensitivity.",
    ),
    "Karl-Adolf Hollidt": (
        "genuine_military_commander_operational",
        "eligible_operational_commander",
        False,
        "Military commander profile, but current support is operation-page only; keep as caveated operational sensitivity.",
    ),
}


def pct(value: float) -> str:
    return f"{value:.1%}"


def load_snapshot(snapshot_dir: Path) -> dict[str, pd.DataFrame]:
    return {
        "trust": pd.read_csv(snapshot_dir / "RANKING_RESULTS_HIERARCHICAL_TRUST_V2.csv"),
        "sensitivity": pd.read_csv(snapshot_dir / "RANKING_RESULTS_SENSITIVITY.csv"),
        "contrib": pd.read_csv(snapshot_dir / "derived_scoring" / "page_type_score_contributions.csv"),
        "annotated": pd.read_csv(snapshot_dir / "derived_scoring" / "commander_engagements_annotated.csv"),
        "tiers": pd.read_csv(snapshot_dir / "derived_scoring" / "commander_tiers.csv"),
        "stability": pd.read_csv(snapshot_dir / "derived_scoring" / "commander_model_stability.csv"),
    }


def build_contribution_rollup(contrib: pd.DataFrame, annotated: pd.DataFrame) -> pd.DataFrame:
    contrib["share_of_total_score"] = pd.to_numeric(contrib["share_of_total_score"], errors="coerce").fillna(0.0)
    wide = (
        contrib.pivot_table(
            index=["analytic_commander_id", "display_name"],
            columns="page_type",
            values="share_of_total_score",
            aggfunc="sum",
            fill_value=0.0,
        )
        .reset_index()
        .rename_axis(None, axis=1)
    )
    for page_type in sorted(BROAD_PAGE_TYPES | BATTLE_OR_SIEGE_PAGE_TYPES):
        if page_type not in wide.columns:
            wide[page_type] = 0.0
    wide["broad_page_contribution_share"] = sum(wide[col] for col in BROAD_PAGE_TYPES if col in wide)
    wide["battle_siege_page_contribution_share"] = sum(wide[col] for col in BATTLE_OR_SIEGE_PAGE_TYPES if col in wide)

    annotated["eligible_strict"] = pd.to_numeric(annotated["eligible_strict"], errors="coerce").fillna(0)
    strict = annotated[annotated["eligible_strict"].eq(1)].copy()
    strict["siege_event"] = strict["battle_name"].fillna("").str.contains("siege", case=False, regex=False)
    siege = (
        strict.groupby("analytic_commander_id")
        .agg(strict_engagement_rows=("battle_id", "count"), siege_rows=("siege_event", "sum"))
        .reset_index()
    )
    siege["siege_row_share"] = siege.apply(
        lambda row: row["siege_rows"] / row["strict_engagement_rows"] if row["strict_engagement_rows"] else 0.0,
        axis=1,
    )
    return wide.merge(siege, on="analytic_commander_id", how="left")


def classify_commander(row: pd.Series) -> tuple[str, str, bool, str]:
    name = str(row["display_name"])
    broad = float(row.get("broad_page_contribution_share") or 0.0)
    battle_siege = float(row.get("battle_siege_page_contribution_share") or 0.0)
    siege_share = float(row.get("siege_row_share") or 0.0)
    battle_count = float(row.get("battle_count") or 0.0)
    known = float(row.get("known_outcome_count") or 0.0)

    if name in MANUAL_ROLE_OVERRIDES:
        return MANUAL_ROLE_OVERRIDES[name]

    if siege_share >= 0.35:
        return (
            "genuine_siege_or_engineering_commander",
            "eligible_siege_or_engineering_commander",
            False,
            "Substantial siege-event support; keep as eligible but category-specific.",
        )
    if broad >= 0.999 and battle_siege <= 0.001:
        return (
            "ambiguous_high_level_only_case",
            "ambiguous_requires_review",
            False,
            "100% broad-page dependency with no battle/siege contribution; requires role verification before headline interpretation.",
        )
    if broad > 0.70 and battle_siege < 0.30:
        return (
            "high_level_operational_case",
            "eligible_operational_commander",
            False,
            "Mostly high-level operational evidence; keep only as caveated sensitivity until event-level support improves.",
        )
    if battle_count >= 5 and known >= 3:
        return (
            "genuine_field_commander",
            "eligible_field_commander",
            False,
            "Battle/siege support and known-outcome evidence are sufficient for headline sensitivity inclusion.",
        )
    if broad > 0.40:
        return (
            "high_level_mixed_case",
            "ambiguous_requires_review",
            False,
            "Broad-page share is high enough to require caveat or additional role verification.",
        )
    return (
        "genuine_field_commander",
        "eligible_field_commander",
        False,
        "No major Pass 2 eligibility concern detected from current page-type evidence.",
    )


def build_eligibility_audit(snapshot: dict[str, pd.DataFrame]) -> pd.DataFrame:
    trust = snapshot["trust"].copy()
    rollup = build_contribution_rollup(snapshot["contrib"].copy(), snapshot["annotated"].copy())
    tiers = snapshot["tiers"][["analytic_commander_id", "tier_label"]].copy()
    stability = snapshot["stability"][["analytic_commander_id", "stability_category", "stability_score"]].copy()

    merged = trust.merge(rollup.drop(columns=["display_name"], errors="ignore"), on="analytic_commander_id", how="left")
    merged = merged.merge(tiers, on="analytic_commander_id", how="left")
    merged = merged.merge(stability, on="analytic_commander_id", how="left")

    rows: list[dict[str, object]] = []
    for _, row in merged.iterrows():
        role_category, strict_eligibility, exclude, rationale = classify_commander(row)
        broad = float(row.get("broad_page_contribution_share") or 0.0)
        battle_siege = float(row.get("battle_siege_page_contribution_share") or 0.0)
        weak_battle = battle_siege < WEAK_BATTLE_SIEGE_THRESHOLD
        recommended_action = "retain"
        if exclude:
            recommended_action = "exclude_from_headline_ranking"
        elif broad >= 0.999:
            recommended_action = "role_review_before_headline_use"
        elif broad > TOP100_BROAD_THRESHOLD:
            recommended_action = "add_high_level_page_caveat"
        elif weak_battle and float(row.get("rank") or 999999) <= 100:
            recommended_action = "add_weak_battle_siege_support_caveat"

        rows.append(
            {
                "analytic_commander_id": row["analytic_commander_id"],
                "commander_name": row["display_name"],
                "rank_hierarchical_trust_v2": int(row["rank"]),
                "score_hierarchical_trust_v2": row["score_normalized"],
                "tier": row.get("tier_label"),
                "stability_category": row.get("stability_category"),
                "known_outcome_count": row.get("known_outcome_count"),
                "engagement_count": row.get("engagement_count"),
                "battle_count": row.get("battle_count"),
                "broad_page_contribution_share": round(broad, 6),
                "battle_siege_page_contribution_share": round(battle_siege, 6),
                "siege_row_share": round(float(row.get("siege_row_share") or 0.0), 6),
                "provisional_role_category": role_category,
                "strict_eligibility": strict_eligibility,
                "exclude_from_headline_ranking": bool(exclude),
                "weak_battle_siege_support": bool(weak_battle),
                "recommended_action": recommended_action,
                "rationale": rationale,
            }
        )
    return pd.DataFrame(rows).sort_values("rank_hierarchical_trust_v2")


def capped_adjustment_factor(broad_share: float, cap: float = CAP_BROAD_SHARE) -> float:
    broad_share = max(0.0, min(1.0, float(broad_share)))
    non_broad = 1.0 - broad_share
    if broad_share <= cap:
        return 1.0
    if non_broad <= 0:
        return 0.0
    allowed_broad = min(broad_share, (cap / (1.0 - cap)) * non_broad)
    return max(0.0, min(1.0, non_broad + allowed_broad))


def build_sensitivity_rankings(snapshot: dict[str, pd.DataFrame], eligibility: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    trust = snapshot["trust"].copy()
    ranking = trust.merge(
        eligibility[
            [
                "analytic_commander_id",
                "broad_page_contribution_share",
                "battle_siege_page_contribution_share",
                "strict_eligibility",
                "exclude_from_headline_ranking",
                "recommended_action",
            ]
        ],
        on="analytic_commander_id",
        how="left",
    )
    ranking["high_level_cap"] = CAP_BROAD_SHARE
    ranking["high_level_cap_adjustment_factor"] = ranking["broad_page_contribution_share"].map(capped_adjustment_factor)
    ranking["score_high_level_capped"] = ranking["score_normalized"] * ranking["high_level_cap_adjustment_factor"]
    capped = ranking.sort_values(["score_high_level_capped", "score_normalized"], ascending=[False, False]).copy()
    capped["rank_high_level_capped"] = range(1, len(capped) + 1)
    capped["rank_change_vs_hierarchical_trust_v2"] = capped["rank_high_level_capped"] - capped["rank"]

    filtered = ranking[~ranking["exclude_from_headline_ranking"].fillna(False)].copy()
    filtered = filtered.sort_values(["score_normalized", "rank"], ascending=[False, True])
    filtered["rank_eligibility_filtered"] = range(1, len(filtered) + 1)
    filtered["rank_change_vs_hierarchical_trust_v2"] = filtered["rank_eligibility_filtered"] - filtered["rank"]

    sensitivity = snapshot["sensitivity"].copy()
    sensitivity = sensitivity.merge(
        capped[["analytic_commander_id", "rank_high_level_capped", "score_high_level_capped", "rank_change_vs_hierarchical_trust_v2"]].rename(
            columns={"rank_change_vs_hierarchical_trust_v2": "rank_change_high_level_capped"}
        ),
        on="analytic_commander_id",
        how="left",
    )
    sensitivity = sensitivity.merge(
        filtered[["analytic_commander_id", "rank_eligibility_filtered", "rank_change_vs_hierarchical_trust_v2"]].rename(
            columns={"rank_change_vs_hierarchical_trust_v2": "rank_change_eligibility_filtered"}
        ),
        on="analytic_commander_id",
        how="left",
    )
    sensitivity = sensitivity.merge(
        eligibility[["analytic_commander_id", "strict_eligibility", "exclude_from_headline_ranking", "recommended_action"]],
        on="analytic_commander_id",
        how="left",
    )
    return capped, filtered, sensitivity


def md_table(df: pd.DataFrame, columns: list[str]) -> str:
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for _, row in df.iterrows():
        values = [str(row.get(column, "")).replace("|", "/").replace("\n", " ") for column in columns]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def build_report(snapshot_dir: Path, eligibility: pd.DataFrame, capped: pd.DataFrame, filtered: pd.DataFrame) -> str:
    top100_broad = eligibility[
        eligibility["rank_hierarchical_trust_v2"].le(100)
        & eligibility["broad_page_contribution_share"].gt(TOP100_BROAD_THRESHOLD)
    ].copy()
    broad100 = eligibility[eligibility["broad_page_contribution_share"].ge(0.999)].copy()
    weak_top = eligibility[
        eligibility["rank_hierarchical_trust_v2"].le(150)
        & eligibility["battle_siege_page_contribution_share"].lt(WEAK_BATTLE_SIEGE_THRESHOLD)
    ].copy()
    capped_movers = capped.sort_values("rank_change_vs_hierarchical_trust_v2", ascending=False).head(25).copy()
    excluded = eligibility[eligibility["exclude_from_headline_ranking"].eq(True)].copy()

    def prep(frame: pd.DataFrame) -> pd.DataFrame:
        out = frame.copy()
        for column in ["broad_page_contribution_share", "battle_siege_page_contribution_share", "siege_row_share"]:
            if column in out.columns:
                out[column] = out[column].map(lambda value: pct(float(value)) if pd.notna(value) else "NA")
        return out

    capped_report = capped_movers.merge(
        eligibility[["analytic_commander_id", "commander_name", "strict_eligibility", "recommended_action"]],
        on="analytic_commander_id",
        how="left",
        suffixes=("", "_eligibility"),
    )
    capped_report["broad_page_contribution_share"] = capped_report["broad_page_contribution_share"].map(lambda value: pct(float(value)))
    capped_report["rank"] = capped_report["rank"].astype(int)
    capped_report["rank_high_level_capped"] = capped_report["rank_high_level_capped"].astype(int)
    capped_report["rank_change_vs_hierarchical_trust_v2"] = capped_report["rank_change_vs_hierarchical_trust_v2"].astype(int)

    metadata = {
        "snapshot": snapshot_dir.name,
        "cap_broad_share": CAP_BROAD_SHARE,
        "ranked_commanders": int(len(eligibility)),
        "top100_broad_gt_40": int(len(top100_broad)),
        "ranked_100_percent_broad": int(len(broad100)),
        "high_ranked_weak_battle_siege": int(len(weak_top)),
        "exclude_from_headline_recommendations": int(len(excluded)),
        "capped_ranked_commanders": int(len(capped)),
        "eligibility_filtered_commanders": int(len(filtered)),
    }
    (snapshot_dir / "reports" / "UPGRADE_PASS_2_SUMMARY.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return f"""# Upgrade Pass 2 Commander Eligibility And High-Level Page Control Report

Snapshot reviewed: `{snapshot_dir.name}`

Status: sensitivity and audit pass only. `hierarchical_trust_v2` remains the headline model and is not replaced here.

## Summary

- Ranked commanders reviewed: `{len(eligibility)}`
- Top-100 commanders with broad-page share above 40%: `{len(top100_broad)}`
- Ranked commanders with 100% broad-page dependency: `{len(broad100)}`
- High-ranked commanders with weak battle/siege support: `{len(weak_top)}`
- Recommended headline exclusions from this pass: `{len(excluded)}`
- New sensitivity outputs: `RANKING_RESULTS_HIERARCHICAL_TRUST_V2_HIGH_LEVEL_CAPPED.csv`, `RANKING_RESULTS_HIERARCHICAL_TRUST_V2_ELIGIBILITY_FILTERED.csv`, `RANKING_RESULTS_PASS2_SENSITIVITY.csv`

## Method

Broad-page contribution is computed from `derived_scoring/page_type_score_contributions.csv`. Broad pages include operation, campaign, war/conflict, invasion, conquest, uprising/revolt, and broad-conflict style page types where present. Siege support is estimated from strict engagement titles containing `siege` because most siege events are currently encoded as `battle_article`.

The high-level capped model is a sensitivity view. It caps broad-page dominance at 40% by reducing score contribution when high-level pages dominate the existing trust-v2 score. Cases with 100% broad-page contribution receive zero capped score until battle/siege or verified operational evidence is added.

## Top 100 Commanders With Broad-Page Share Above 40%

{md_table(prep(top100_broad), ["rank_hierarchical_trust_v2", "commander_name", "tier", "stability_category", "known_outcome_count", "engagement_count", "broad_page_contribution_share", "battle_siege_page_contribution_share", "strict_eligibility", "recommended_action"])}

## All Ranked Commanders With 100% Broad-Page Dependency

{md_table(prep(broad100), ["rank_hierarchical_trust_v2", "commander_name", "known_outcome_count", "engagement_count", "broad_page_contribution_share", "battle_siege_page_contribution_share", "provisional_role_category", "strict_eligibility", "exclude_from_headline_ranking", "recommended_action", "rationale"])}

## High-Ranked Commanders With Weak Battle/Siege Support

High-ranked here means current trust-v2 rank 150 or better. Weak battle/siege support means less than 35% battle/siege contribution.

{md_table(prep(weak_top), ["rank_hierarchical_trust_v2", "commander_name", "known_outcome_count", "engagement_count", "broad_page_contribution_share", "battle_siege_page_contribution_share", "strict_eligibility", "recommended_action", "rationale"])}

## Largest Drops Under High-Level Page Cap

Positive movement means the commander drops after the high-level page cap is applied.

{md_table(capped_report, ["rank", "rank_high_level_capped", "rank_change_vs_hierarchical_trust_v2", "commander_name", "broad_page_contribution_share", "strict_eligibility", "recommended_action"])}

## Recommended Actions

- Exclude political or nominal-only leaders from headline ranking unless direct field, naval, siege, or verified operational command evidence is added.
- Keep genuine military commanders with high-level-only support only in operational sensitivity views until role and event-level evidence is curated.
- Add caveats to any top-100 commander whose broad-page share exceeds 40%.
- Do not promote the capped or eligibility-filtered outputs to headline status until role classification is manually reviewed.
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Upgrade Pass 2 role and high-level page sensitivity outputs.")
    parser.add_argument("--snapshot-dir", type=Path, default=DEFAULT_SNAPSHOT)
    args = parser.parse_args()

    snapshot_dir = args.snapshot_dir
    (snapshot_dir / "audits").mkdir(parents=True, exist_ok=True)
    (snapshot_dir / "reports").mkdir(parents=True, exist_ok=True)

    snapshot = load_snapshot(snapshot_dir)
    eligibility = build_eligibility_audit(snapshot)
    capped, filtered, sensitivity = build_sensitivity_rankings(snapshot, eligibility)

    eligibility.to_csv(snapshot_dir / "audits" / "commander_strict_eligibility_audit.csv", index=False)
    capped.to_csv(snapshot_dir / "RANKING_RESULTS_HIERARCHICAL_TRUST_V2_HIGH_LEVEL_CAPPED.csv", index=False)
    filtered.to_csv(snapshot_dir / "RANKING_RESULTS_HIERARCHICAL_TRUST_V2_ELIGIBILITY_FILTERED.csv", index=False)
    sensitivity.to_csv(snapshot_dir / "RANKING_RESULTS_PASS2_SENSITIVITY.csv", index=False)

    report = build_report(snapshot_dir, eligibility, capped, filtered)
    (snapshot_dir / "reports" / "UPGRADE_PASS_2_ROLE_HIGHLEVEL_REPORT.md").write_text(report, encoding="utf-8")
    print(f"Wrote Upgrade Pass 2 outputs under {snapshot_dir}")


if __name__ == "__main__":
    main()
