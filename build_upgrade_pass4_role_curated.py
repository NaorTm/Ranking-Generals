from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

import numpy as np
import pandas as pd

from build_scoring_framework_package import OUTCOME_SCORE_MAPS


PARENT_SNAPSHOT = Path("outputs_improved_2026-04-24_upgrade_pass3_confidence")
DEFAULT_SNAPSHOT = Path("outputs_improved_2026-04-24_upgrade_pass4_role_curated")

BROAD_PAGE_TYPES = {
    "operation_article",
    "campaign_article",
    "war_conflict_article",
    "invasion_article",
    "conquest_article",
    "uprising_or_revolt_article",
    "broad_conflict_article",
}
BATTLE_SIEGE_PAGE_TYPES = {"battle_article", "naval_battle_article", "siege_article"}

ROLE_WEIGHTS = {
    "overall_commander": 1.00,
    "principal_field_commander": 0.85,
    "coalition_commander": 0.70,
    "naval_commander": 0.75,
    "siege_engineer_or_specialist": 0.70,
    "wing_or_corps_commander": 0.55,
    "staff_or_planning_role": 0.45,
    "subordinate_commander": 0.35,
    "nominal_or_political_leader": 0.20,
    "unclear_role": 0.40,
}

ROLE_SCORE_COLUMNS = {
    "overall_commander": "score_from_overall_command",
    "principal_field_commander": "score_from_principal_field_command",
    "subordinate_commander": "score_from_subordinate_command",
    "coalition_commander": "score_from_coalition_command",
    "siege_engineer_or_specialist": "score_from_siege_engineering",
    "naval_commander": "score_from_naval_command",
    "staff_or_planning_role": "score_from_staff_or_planning",
    "nominal_or_political_leader": "score_from_nominal_or_political",
    "unclear_role": "score_from_unclear_role",
    "wing_or_corps_commander": "score_from_wing_or_corps_command",
}

MANUAL_COMMANDER_OVERRIDES: dict[str, tuple[str, float, str, str]] = {
    "Alexander Suvorov": (
        "overall_commander",
        0.95,
        "manual_seed_top_case",
        "Direct field-command case with battle-dominant support.",
    ),
    "Maurice, Prince of Orange": (
        "overall_commander",
        0.85,
        "manual_seed_top_case",
        "Active commander and military reformer; role is eligible but partly institutional/campaign-level.",
    ),
    "Napoleon Bonaparte": (
        "overall_commander",
        0.95,
        "manual_seed_top_case",
        "Direct operational and field command; do not treat him as merely political.",
    ),
    "Subutai": (
        "principal_field_commander",
        0.80,
        "manual_seed_top_case",
        "Genuine senior operational commander; some high-level pages remain role-sensitive.",
    ),
    "Sébastien Le Prestre, Marquis of Vauban": (
        "siege_engineer_or_specialist",
        0.95,
        "manual_seed_top_case",
        "Primarily siege-engineering and fortification specialist; strong category-specific case.",
    ),
    "Jean Lannes": (
        "principal_field_commander",
        0.90,
        "manual_seed_top_case",
        "Direct Napoleonic field commander with battle-level support.",
    ),
    "Louis-Nicolas Davout": (
        "principal_field_commander",
        0.90,
        "manual_seed_top_case",
        "Direct field commander with strong battle/corps-command evidence.",
    ),
    "Douglas MacArthur": (
        "coalition_commander",
        0.75,
        "manual_seed_top_case",
        "Senior theater/coalition commander; role is real but high-level and staff-structure sensitive.",
    ),
    "Charles XIV John": (
        "coalition_commander",
        0.75,
        "manual_seed_top_case",
        "Senior coalition/operational command case; exact rank remains coalition-credit sensitive.",
    ),
    "Ivan Paskevich": (
        "overall_commander",
        0.85,
        "manual_seed_top_case",
        "Genuine operational/field commander, but confidence interval remains wide.",
    ),
    "Dwight D. Eisenhower": (
        "coalition_commander",
        0.90,
        "manual_seed_requested_case",
        "Supreme Allied commander; real command responsibility, mostly coalition/theater-level.",
    ),
    "Georgy Zhukov": (
        "overall_commander",
        0.90,
        "manual_seed_requested_case",
        "Senior field and operational commander with direct command responsibility.",
    ),
    "Genghis Khan": (
        "overall_commander",
        0.90,
        "manual_seed_requested_case",
        "Ruler and genuine field/operational commander; not a nominal-only monarch case.",
    ),
    "Frederick the Great": (
        "overall_commander",
        0.95,
        "manual_seed_requested_case",
        "Ruler but direct battlefield commander; no blanket ruler penalty.",
    ),
    "Konstantin Rokossovsky": (
        "overall_commander",
        0.85,
        "manual_seed_requested_case",
        "Senior operational commander with direct army/front command responsibility.",
    ),
    "Horatio Nelson": (
        "naval_commander",
        0.95,
        "manual_seed_previous_top_case",
        "Naval commander; should be evaluated as direct naval command, not generic battle command.",
    ),
    "Yi Sun-sin": (
        "naval_commander",
        0.95,
        "manual_seed_previous_top_case",
        "Naval commander with direct operational command.",
    ),
    "Louis XIV": (
        "nominal_or_political_leader",
        0.75,
        "manual_seed_suspicious_case",
        "Monarch/head-of-state profile; requires stronger direct-command evidence before headline use.",
    ),
    "Qianlong Emperor": (
        "nominal_or_political_leader",
        0.80,
        "manual_seed_suspicious_case",
        "Monarch profile with broad-page dependency; treat as nominal unless direct command is curated.",
    ),
    "Maria Theresa": (
        "nominal_or_political_leader",
        0.85,
        "manual_seed_suspicious_case",
        "Political/monarchical leadership case, not direct commander evidence in this snapshot.",
    ),
    "Leonid Brezhnev": (
        "nominal_or_political_leader",
        0.90,
        "manual_seed_suspicious_case",
        "Political head-of-state case, not a rankable direct commander in this framework.",
    ),
    "Lê Duẩn": (
        "nominal_or_political_leader",
        0.90,
        "manual_seed_suspicious_case",
        "Political leadership case with no direct field-command support.",
    ),
    "Phạm Văn Đồng": (
        "nominal_or_political_leader",
        0.90,
        "manual_seed_suspicious_case",
        "Political leadership case with no direct field-command support.",
    ),
    "Hulusi Akar": (
        "staff_or_planning_role",
        0.80,
        "manual_seed_suspicious_case",
        "Modern officeholder/staff case in the current data, not field-command evidence.",
    ),
    "Ashfaq Parvez Kayani": (
        "staff_or_planning_role",
        0.80,
        "manual_seed_suspicious_case",
        "Army-chief/staff profile without battle/siege command support in this snapshot.",
    ),
}


def snapshot_file(snapshot_dir: Path, relative_name: str) -> Path:
    path = snapshot_dir / relative_name
    if path.exists():
        return path
    gzip_path = snapshot_dir / f"{relative_name}.gz"
    if gzip_path.exists():
        return gzip_path
    return path


def pct(value: float | int | None) -> str:
    if value is None or pd.isna(value):
        return "n/a"
    return f"{float(value):.1%}"


def safe_rank_column(frame: pd.DataFrame, source_col: str, target_col: str) -> pd.DataFrame:
    if source_col in frame.columns:
        frame[target_col] = frame[source_col]
    return frame


def create_snapshot(parent_dir: Path, snapshot_dir: Path, force: bool) -> None:
    if snapshot_dir.exists():
        if not force:
            return
        shutil.rmtree(snapshot_dir)
    shutil.copytree(parent_dir, snapshot_dir)


def load_inputs(snapshot_dir: Path) -> dict[str, pd.DataFrame]:
    return {
        "annotated": pd.read_csv(snapshot_file(snapshot_dir, "derived_scoring/commander_engagements_annotated.csv")),
        "trust": pd.read_csv(snapshot_dir / "RANKING_RESULTS_HIERARCHICAL_TRUST_V2.csv"),
        "capped": pd.read_csv(snapshot_dir / "RANKING_RESULTS_HIERARCHICAL_TRUST_V2_HIGH_LEVEL_CAPPED.csv"),
        "filtered": pd.read_csv(snapshot_dir / "RANKING_RESULTS_HIERARCHICAL_TRUST_V2_ELIGIBILITY_FILTERED.csv"),
        "confidence_tiers": pd.read_csv(snapshot_dir / "derived_scoring" / "commander_tiers_confidence_adjusted.csv"),
        "confidence_summary": pd.read_csv(snapshot_dir / "derived_scoring" / "commander_rank_confidence_summary.csv"),
        "stability": pd.read_csv(snapshot_dir / "derived_scoring" / "commander_model_stability.csv"),
        "page_contrib": pd.read_csv(snapshot_dir / "derived_scoring" / "page_type_score_contributions.csv"),
        "eligibility": pd.read_csv(snapshot_dir / "audits" / "commander_strict_eligibility_audit.csv"),
    }


def broad_share_rollup(page_contrib: pd.DataFrame) -> pd.DataFrame:
    page_contrib = page_contrib.copy()
    page_contrib["share_of_total_score"] = pd.to_numeric(
        page_contrib["share_of_total_score"], errors="coerce"
    ).fillna(0.0)
    broad = (
        page_contrib[page_contrib["page_type"].isin(BROAD_PAGE_TYPES)]
        .groupby("analytic_commander_id", as_index=False)["share_of_total_score"]
        .sum()
        .rename(columns={"share_of_total_score": "broad_page_contribution_share"})
    )
    battle_siege = (
        page_contrib[page_contrib["page_type"].isin(BATTLE_SIEGE_PAGE_TYPES)]
        .groupby("analytic_commander_id", as_index=False)["share_of_total_score"]
        .sum()
        .rename(columns={"share_of_total_score": "battle_siege_page_contribution_share"})
    )
    return broad.merge(battle_siege, on="analytic_commander_id", how="outer").fillna(0.0)


def curation_scope(inputs: dict[str, pd.DataFrame]) -> set[str]:
    trust = inputs["trust"]
    stability = inputs["stability"]
    confidence = inputs["confidence_summary"]
    broad = broad_share_rollup(inputs["page_contrib"])
    ids: set[str] = set(trust.nsmallest(100, "rank")["analytic_commander_id"])
    ids |= set(
        stability.sort_values(["rank_stddev", "rank_iqr"], ascending=False)
        .head(50)["analytic_commander_id"]
    )
    ids |= set(broad.sort_values("broad_page_contribution_share", ascending=False).head(50)["analytic_commander_id"])
    ids |= set(confidence.sort_values("rank_band_width_80", ascending=False).head(50)["analytic_commander_id"])
    for frame, rank_col in [
        (trust, "rank"),
        (inputs["capped"], "rank_high_level_capped"),
        (inputs["filtered"], "rank_eligibility_filtered"),
    ]:
        ids |= set(frame.nsmallest(10, rank_col)["analytic_commander_id"])
    return ids


def classify_role(row: pd.Series, scope_ids: set[str], excluded_ids: set[str]) -> tuple[str, float, str, str]:
    name = str(row.get("display_name") or "")
    page_type = str(row.get("page_type") or "")
    same_side = pd.to_numeric(row.get("same_side_known_outcome_count"), errors="coerce")
    same_side = 0 if pd.isna(same_side) else int(same_side)
    commander_id = str(row.get("analytic_commander_id") or "")

    if name in MANUAL_COMMANDER_OVERRIDES:
        role_class, confidence, source, notes = MANUAL_COMMANDER_OVERRIDES[name]
        if role_class == "siege_engineer_or_specialist" and page_type == "naval_battle_article":
            return "naval_commander", 0.80, source, "Manual commander override adjusted for naval page type."
        return role_class, confidence, source, notes

    if commander_id in excluded_ids:
        return (
            "nominal_or_political_leader",
            0.65,
            "eligibility_audit_exclusion",
            "Pass 2 eligibility audit recommends headline exclusion; treat as nominal/political unless curated otherwise.",
        )
    if page_type == "naval_battle_article":
        return "naval_commander", 0.70, "heuristic_page_type", "Naval battle article; inferred naval command role."
    if page_type == "siege_article":
        return (
            "siege_engineer_or_specialist",
            0.65,
            "heuristic_page_type",
            "Siege article; inferred siege or specialist command role pending manual review.",
        )
    if page_type == "battle_article":
        if same_side >= 4:
            return (
                "wing_or_corps_commander",
                0.55,
                "heuristic_same_side_density",
                "Battle page with many same-side commanders; inferred wing/corps-level or shared command.",
            )
        return (
            "principal_field_commander",
            0.65,
            "heuristic_page_type",
            "Battle article; inferred direct field command pending manual role verification.",
        )
    if page_type in {"operation_article", "campaign_article", "invasion_article", "conquest_article"}:
        if same_side >= 4:
            return (
                "coalition_commander",
                0.50,
                "heuristic_high_level_density",
                "High-level page with dense same-side command; inferred coalition/shared command.",
            )
        return (
            "overall_commander" if commander_id in scope_ids else "unclear_role",
            0.50 if commander_id in scope_ids else 0.35,
            "heuristic_high_level_page",
            "High-level operational page; command role needs source-level verification.",
        )
    if page_type in {"war_conflict_article", "uprising_or_revolt_article", "broad_conflict_article"}:
        return (
            "coalition_commander" if same_side >= 4 and commander_id in scope_ids else "unclear_role",
            0.45 if commander_id in scope_ids else 0.30,
            "heuristic_broad_page",
            "War/broad-conflict page; role is ambiguous without curated body evidence.",
        )
    return "unclear_role", 0.30, "heuristic_fallback", "No page-type role signal available."


def build_role_classification(inputs: dict[str, pd.DataFrame]) -> pd.DataFrame:
    annotated = inputs["annotated"].copy()
    scope_ids = curation_scope(inputs)
    excluded_ids = set(
        inputs["eligibility"].loc[
            inputs["eligibility"]["exclude_from_headline_ranking"].astype(str).str.lower().eq("true"),
            "analytic_commander_id",
        ]
    )
    roles = annotated.apply(lambda row: classify_role(row, scope_ids, excluded_ids), axis=1, result_type="expand")
    roles.columns = ["role_class", "role_confidence", "role_source", "role_notes"]
    output = pd.concat(
        [
            annotated[
                [
                    "analytic_commander_id",
                    "display_name",
                    "battle_id",
                    "wikipedia_title",
                    "page_type",
                ]
            ].rename(columns={"display_name": "commander_name", "wikipedia_title": "page_title"}),
            roles,
        ],
        axis=1,
    )
    return output


def scoring_signal(annotated: pd.DataFrame) -> pd.Series:
    eligible = pd.to_numeric(annotated["eligible_strict"], errors="coerce").fillna(0.0)
    page_weight = pd.to_numeric(annotated["page_weight_model_b"], errors="coerce").fillna(0.0)
    credit = pd.to_numeric(annotated["outcome_credit_fraction"], errors="coerce").fillna(0.0)
    outcome = annotated["outcome_category"].map(OUTCOME_SCORE_MAPS["balanced"]).fillna(0.0)
    score_signal = (eligible * page_weight * credit * outcome).abs()
    presence_signal = eligible * page_weight
    return score_signal.where(score_signal.gt(0.0), presence_signal * 0.15)


def build_role_contributions(annotated: pd.DataFrame, role_file: pd.DataFrame) -> pd.DataFrame:
    keyed_roles = role_file[
        ["analytic_commander_id", "battle_id", "role_class", "role_confidence"]
    ].drop_duplicates(["analytic_commander_id", "battle_id"])
    rows = annotated.merge(keyed_roles, on=["analytic_commander_id", "battle_id"], how="left")
    rows["role_class"] = rows["role_class"].fillna("unclear_role")
    rows["role_confidence"] = pd.to_numeric(rows["role_confidence"], errors="coerce").fillna(0.30)
    rows["role_weight"] = rows["role_class"].map(ROLE_WEIGHTS).fillna(ROLE_WEIGHTS["unclear_role"])
    rows["role_score_signal"] = scoring_signal(rows)
    rows["role_weighted_score_signal"] = rows["role_score_signal"] * rows["role_weight"]

    pivot = (
        rows.pivot_table(
            index=["analytic_commander_id", "display_name"],
            columns="role_class",
            values="role_score_signal",
            aggfunc="sum",
            fill_value=0.0,
        )
        .reset_index()
        .rename_axis(None, axis=1)
    )
    for role in ROLE_WEIGHTS:
        if role not in pivot.columns:
            pivot[role] = 0.0
    output = pivot[["analytic_commander_id", "display_name"]].rename(columns={"display_name": "commander_name"})
    output["total_score"] = pivot[list(ROLE_WEIGHTS)].sum(axis=1)
    for role, column in ROLE_SCORE_COLUMNS.items():
        output[column] = pivot[role]
    output["share_unclear_role"] = np.where(
        output["total_score"].gt(0), output["score_from_unclear_role"] / output["total_score"], 0.0
    )
    output["share_nominal_or_political"] = np.where(
        output["total_score"].gt(0), output["score_from_nominal_or_political"] / output["total_score"], 0.0
    )
    direct_cols = [
        "score_from_overall_command",
        "score_from_principal_field_command",
        "score_from_wing_or_corps_command",
        "score_from_naval_command",
    ]
    output["share_direct_field_command"] = np.where(
        output["total_score"].gt(0), output[direct_cols].sum(axis=1) / output["total_score"], 0.0
    )

    weighted = (
        rows.groupby("analytic_commander_id", as_index=False)
        .agg(
            role_weighted_total=("role_weighted_score_signal", "sum"),
            role_unweighted_total=("role_score_signal", "sum"),
            mean_role_confidence=("role_confidence", "mean"),
        )
    )
    dominant = (
        rows.groupby(["analytic_commander_id", "role_class"], as_index=False)["role_score_signal"]
        .sum()
        .sort_values(["analytic_commander_id", "role_score_signal"], ascending=[True, False])
        .drop_duplicates("analytic_commander_id")
        .rename(columns={"role_class": "dominant_role_class", "role_score_signal": "dominant_role_score"})
    )
    output = output.merge(weighted, on="analytic_commander_id", how="left").merge(
        dominant[["analytic_commander_id", "dominant_role_class"]],
        on="analytic_commander_id",
        how="left",
    )
    output["role_adjustment_factor"] = np.where(
        output["role_unweighted_total"].gt(0),
        output["role_weighted_total"] / output["role_unweighted_total"],
        ROLE_WEIGHTS["unclear_role"],
    )
    return output


def build_role_weighted_ranking(
    trust: pd.DataFrame,
    role_contrib: pd.DataFrame,
    broad: pd.DataFrame,
    eligibility: pd.DataFrame,
) -> pd.DataFrame:
    ranking = trust.merge(role_contrib, on="analytic_commander_id", how="left")
    ranking = ranking.merge(broad, on="analytic_commander_id", how="left")
    ranking = ranking.merge(
        eligibility[
            [
                "analytic_commander_id",
                "strict_eligibility",
                "exclude_from_headline_ranking",
                "recommended_action",
            ]
        ],
        on="analytic_commander_id",
        how="left",
    )
    ranking["role_adjustment_factor"] = pd.to_numeric(
        ranking["role_adjustment_factor"], errors="coerce"
    ).fillna(ROLE_WEIGHTS["unclear_role"])
    ranking["mean_role_confidence"] = pd.to_numeric(
        ranking["mean_role_confidence"], errors="coerce"
    ).fillna(0.30)
    ranking["exclude_from_headline_ranking"] = ranking["exclude_from_headline_ranking"].astype(str).str.lower().eq("true")
    ranking["role_confidence_factor"] = 0.75 + (0.25 * ranking["mean_role_confidence"].clip(0.0, 1.0))
    ranking["role_eligibility_factor"] = np.where(ranking["exclude_from_headline_ranking"], 0.25, 1.0)
    ranking["score_role_weighted"] = (
        ranking["score_normalized"]
        * ranking["role_adjustment_factor"]
        * ranking["role_confidence_factor"]
        * ranking["role_eligibility_factor"]
    )
    ranking = ranking.sort_values(["score_role_weighted", "score_normalized"], ascending=[False, False]).reset_index(drop=True)
    ranking["rank_role_weighted"] = np.arange(1, len(ranking) + 1)
    ranking["rank_change_vs_hierarchical_trust_v2"] = ranking["rank_role_weighted"] - ranking["rank"]
    keep = [
        "rank",
        "rank_role_weighted",
        "rank_change_vs_hierarchical_trust_v2",
        "score_normalized",
        "score_role_weighted",
        "role_adjustment_factor",
        "mean_role_confidence",
        "dominant_role_class",
        "share_direct_field_command",
        "share_unclear_role",
        "share_nominal_or_political",
        "broad_page_contribution_share",
        "battle_siege_page_contribution_share",
        "strict_eligibility",
        "exclude_from_headline_ranking",
        "recommended_action",
    ]
    front = [col for col in trust.columns if col not in keep]
    return ranking[front + keep]


def build_pass4_sensitivity(
    trust: pd.DataFrame,
    capped: pd.DataFrame,
    filtered: pd.DataFrame,
    role_weighted: pd.DataFrame,
    confidence_tiers: pd.DataFrame,
) -> pd.DataFrame:
    base = trust[["analytic_commander_id", "display_name", "rank", "score_normalized"]].rename(
        columns={"rank": "rank_hierarchical_trust_v2", "score_normalized": "score_hierarchical_trust_v2"}
    )
    base = base.merge(
        capped[
            [
                "analytic_commander_id",
                "rank_high_level_capped",
                "score_high_level_capped",
                "broad_page_contribution_share",
                "battle_siege_page_contribution_share",
            ]
        ],
        on="analytic_commander_id",
        how="left",
    )
    base = base.merge(
        filtered[["analytic_commander_id", "rank_eligibility_filtered", "exclude_from_headline_ranking"]],
        on="analytic_commander_id",
        how="left",
    )
    base = base.merge(
        role_weighted[
            [
                "analytic_commander_id",
                "rank_role_weighted",
                "score_role_weighted",
                "rank_change_vs_hierarchical_trust_v2",
                "dominant_role_class",
                "share_direct_field_command",
                "share_unclear_role",
                "share_nominal_or_political",
                "role_adjustment_factor",
                "mean_role_confidence",
            ]
        ],
        on="analytic_commander_id",
        how="left",
    )
    base = base.merge(
        confidence_tiers[
            [
                "analytic_commander_id",
                "confidence_adjusted_tier",
                "confidence_category",
                "rank_band_width_80",
                "recommended_interpretation",
            ]
        ],
        on="analytic_commander_id",
        how="left",
    )
    rank_cols = ["rank_hierarchical_trust_v2", "rank_high_level_capped", "rank_eligibility_filtered", "rank_role_weighted"]
    base["best_rank_pass4_models"] = base[rank_cols].min(axis=1)
    base["worst_rank_pass4_models"] = base[rank_cols].max(axis=1)
    base["rank_range_pass4_models"] = base["worst_rank_pass4_models"] - base["best_rank_pass4_models"]
    return base.sort_values("rank_hierarchical_trust_v2")


def caveat(row: pd.Series) -> str:
    if float(row.get("share_nominal_or_political") or 0.0) >= 0.30:
        return "Nominal/political role share is high; headline interpretation needs curation."
    if float(row.get("share_unclear_role") or 0.0) >= 0.40:
        return "Unclear-role share is high; exact rank is role-sensitive."
    if float(row.get("broad_page_contribution_share") or 0.0) >= 0.40:
        return "High broad-page dependency; role-weighted interpretation is qualified."
    if str(row.get("dominant_role_class") or "") == "siege_engineer_or_specialist":
        return "Category-specific siege/engineering case rather than pure field ranking."
    if int(row.get("rank_change_vs_hierarchical_trust_v2") or 0) >= 20:
        return "Role weighting materially weakens exact rank."
    return "Role evidence supports ranking without a major Pass 4 caveat."


def status_label(row: pd.Series) -> str:
    movement = int(row.get("rank_change_vs_hierarchical_trust_v2") or 0)
    unclear = float(row.get("share_unclear_role") or 0.0)
    broad = float(row.get("broad_page_contribution_share") or 0.0)
    nominal = float(row.get("share_nominal_or_political") or 0.0)
    role = str(row.get("dominant_role_class") or "")
    if nominal >= 0.30 or movement >= 80:
        return "fragile"
    if role in {"siege_engineer_or_specialist", "naval_commander", "coalition_commander"}:
        return "qualified"
    if unclear >= 0.40 or broad >= 0.40 or movement >= 20:
        return "qualified"
    return "robust"


def case_note(name: str, row: pd.Series | None) -> str:
    if row is None:
        return f"- **{name}**: not found in the ranked Pass 4 sensitivity table."
    movement = int(row.get("rank_change_vs_hierarchical_trust_v2") or 0)
    if movement > 0:
        direction = f"drops {movement} places"
    elif movement < 0:
        direction = f"improves {abs(movement)} places"
    else:
        direction = "does not move"
    direct = pct(row.get("share_direct_field_command"))
    broad = pct(row.get("broad_page_contribution_share"))
    unclear = pct(row.get("share_unclear_role"))
    role = row.get("dominant_role_class")
    label = status_label(row)
    return (
        f"- **{name}**: dominant role `{role}`; direct field-command share {direct}, "
        f"broad-page share {broad}, unclear-role share {unclear}. The role-weighted model {direction}. "
        f"Interpret as **{label}**: {caveat(row)}"
    )


def markdown_table(frame: pd.DataFrame, columns: list[str], max_rows: int | None = None) -> str:
    rows = frame if max_rows is None else frame.head(max_rows)
    display = rows[columns].copy()
    for col in display.columns:
        if col.startswith("share_") or col.endswith("_share") or col == "broad_page_contribution_share":
            display[col] = display[col].map(lambda value: pct(value))
    labels = list(display.columns)
    markdown = [
        "| " + " | ".join(labels) + " |",
        "| " + " | ".join(["---"] * len(labels)) + " |",
    ]
    for _, row in display.iterrows():
        values = []
        for label in labels:
            value = row[label]
            text = "" if pd.isna(value) else str(value)
            values.append(text.replace("|", "\\|").replace("\n", " "))
        markdown.append("| " + " | ".join(values) + " |")
    return "\n".join(markdown)


def write_report(snapshot_dir: Path, sensitivity: pd.DataFrame) -> None:
    reports_dir = snapshot_dir / "reports"
    reports_dir.mkdir(exist_ok=True)
    top50 = sensitivity.nsmallest(50, "rank_hierarchical_trust_v2").copy()
    top50["main_caveat"] = top50.apply(caveat, axis=1)
    drops = sensitivity.sort_values("rank_change_vs_hierarchical_trust_v2", ascending=False).head(25).copy()
    improves = sensitivity.sort_values("rank_change_vs_hierarchical_trust_v2", ascending=True).head(25).copy()
    unclear = sensitivity[
        (sensitivity["rank_hierarchical_trust_v2"] <= 150) & (sensitivity["share_unclear_role"] >= 0.40)
    ].sort_values(["share_unclear_role", "rank_hierarchical_trust_v2"], ascending=[False, True]).head(25)

    case_names = [
        "Alexander Suvorov",
        "Maurice, Prince of Orange",
        "Napoleon Bonaparte",
        "Subutai",
        "Sébastien Le Prestre, Marquis of Vauban",
        "Jean Lannes",
        "Louis-Nicolas Davout",
        "Douglas MacArthur",
        "Charles XIV John",
        "Ivan Paskevich",
        "Dwight D. Eisenhower",
        "Georgy Zhukov",
        "Genghis Khan",
        "Frederick the Great",
        "Konstantin Rokossovsky",
    ]
    by_name = {row["display_name"]: row for _, row in sensitivity.iterrows()}
    notes = "\n".join(case_note(name, by_name.get(name)) for name in case_names)

    robust = sensitivity[
        (sensitivity["rank_hierarchical_trust_v2"] <= 25)
        & (sensitivity["share_direct_field_command"] >= 0.70)
        & (sensitivity["share_unclear_role"] < 0.25)
        & (sensitivity["rank_change_vs_hierarchical_trust_v2"] <= 10)
    ]["display_name"].head(12).tolist()
    category_specific = sensitivity[
        (sensitivity["rank_hierarchical_trust_v2"] <= 100)
        & (sensitivity["dominant_role_class"].isin(["siege_engineer_or_specialist", "naval_commander", "coalition_commander"]))
    ]["display_name"].head(12).tolist()
    needs_curation = sensitivity[
        (sensitivity["rank_hierarchical_trust_v2"] <= 150)
        & ((sensitivity["share_unclear_role"] >= 0.40) | (sensitivity["share_nominal_or_political"] >= 0.20))
    ]["display_name"].head(12).tolist()

    report = f"""# Upgrade Pass 4 Role Classification Report

Snapshot: `{snapshot_dir.name}`

Parent snapshot: `{PARENT_SNAPSHOT.name}`

Headline model remains `hierarchical_trust_v2`. Pass 4 adds a role-aware sensitivity model and audit layer; it does not replace the headline ranking.

## Methodology

- Built `verification/verified_command_role_classification.csv` for every commander-engagement row.
- Used manual seed overrides for the current top commanders, prior top-list commanders, and Pass 2 suspicious political/staff cases.
- Used heuristic fallback classification from page type, same-side commander density, and Pass 2 eligibility flags.
- Applied initial role weights exactly as a sensitivity assumption, not as historical truth.
- Computed role score shares and a role-weighted sensitivity score from existing trust-v2 scores adjusted by role mix, role confidence, and Pass 2 headline exclusions.

## Top 50 Role Sensitivity

{markdown_table(top50, [
    "rank_hierarchical_trust_v2",
    "rank_role_weighted",
    "rank_change_vs_hierarchical_trust_v2",
    "display_name",
    "confidence_adjusted_tier",
    "dominant_role_class",
    "share_direct_field_command",
    "broad_page_contribution_share",
    "share_unclear_role",
    "main_caveat",
])}

## Specific Audit Notes

{notes}

## Largest Rank Drops After Role Weighting

{markdown_table(drops, [
    "rank_hierarchical_trust_v2",
    "rank_role_weighted",
    "rank_change_vs_hierarchical_trust_v2",
    "display_name",
    "dominant_role_class",
    "share_unclear_role",
    "share_nominal_or_political",
    "broad_page_contribution_share",
], 20)}

## Largest Improvements Or Credibility Gains

{markdown_table(improves, [
    "rank_hierarchical_trust_v2",
    "rank_role_weighted",
    "rank_change_vs_hierarchical_trust_v2",
    "display_name",
    "dominant_role_class",
    "share_direct_field_command",
    "broad_page_contribution_share",
], 20)}

## High-Rank, High-Unclear-Role Cases

{markdown_table(unclear, [
    "rank_hierarchical_trust_v2",
    "rank_role_weighted",
    "display_name",
    "dominant_role_class",
    "share_unclear_role",
    "broad_page_contribution_share",
    "confidence_adjusted_tier",
], 20)}

## Final Judgment

Role weighting improves interpretability because it separates direct field command, coalition/theater command, siege engineering, naval command, nominal political leadership, and unresolved role evidence. It does not prove a new historical order; it identifies where the exact rank depends on command-role assumptions.

Robust elite under Pass 4: {", ".join(robust) if robust else "none under the current strict rule"}.

Category-specific or role-qualified high performers: {", ".join(category_specific) if category_specific else "none flagged"}.

Commanders requiring stronger historical curation: {", ".join(needs_curation) if needs_curation else "none flagged"}.

Next priority: replace heuristic role labels with source-backed manual curation for the top 100 and for every commander whose role-weighted rank movement exceeds 20 places.
"""
    (reports_dir / "UPGRADE_PASS_4_ROLE_CLASSIFICATION_REPORT.md").write_text(report, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Upgrade Pass 4 curated role sensitivity outputs.")
    parser.add_argument("--parent-dir", type=Path, default=PARENT_SNAPSHOT)
    parser.add_argument("--snapshot-dir", type=Path, default=DEFAULT_SNAPSHOT)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    create_snapshot(args.parent_dir, args.snapshot_dir, args.force)
    inputs = load_inputs(args.snapshot_dir)

    role_file = build_role_classification(inputs)
    verification_dir = args.snapshot_dir / "verification"
    verification_dir.mkdir(exist_ok=True)
    role_file.to_csv(verification_dir / "verified_command_role_classification.csv", index=False)

    role_contrib = build_role_contributions(inputs["annotated"], role_file)
    derived_dir = args.snapshot_dir / "derived_scoring"
    derived_dir.mkdir(exist_ok=True)
    role_contrib.to_csv(derived_dir / "role_class_score_contributions.csv", index=False)

    broad = broad_share_rollup(inputs["page_contrib"])
    role_weighted = build_role_weighted_ranking(inputs["trust"], role_contrib, broad, inputs["eligibility"])
    role_weighted.to_csv(args.snapshot_dir / "RANKING_RESULTS_HIERARCHICAL_TRUST_V2_ROLE_WEIGHTED.csv", index=False)

    sensitivity = build_pass4_sensitivity(
        inputs["trust"],
        inputs["capped"],
        inputs["filtered"],
        role_weighted,
        inputs["confidence_tiers"],
    )
    sensitivity.to_csv(args.snapshot_dir / "RANKING_RESULTS_PASS4_ROLE_SENSITIVITY.csv", index=False)
    write_report(args.snapshot_dir, sensitivity)

    metadata = {
        "snapshot": args.snapshot_dir.name,
        "parent_snapshot": args.parent_dir.name,
        "role_weights": ROLE_WEIGHTS,
        "manual_override_count": len(MANUAL_COMMANDER_OVERRIDES),
        "classified_rows": int(len(role_file)),
        "role_weighted_rows": int(len(role_weighted)),
        "headline_model_replaced": False,
    }
    (args.snapshot_dir / "reports" / "UPGRADE_PASS_4_SUMMARY.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
