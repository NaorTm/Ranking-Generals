from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import pandas as pd

from build_scoring_framework_package import OUTCOME_SCORE_MAPS, PAGE_TYPE_WEIGHTS, join_flags, normalize_space


VALID_SIDES = {"side_a", "side_b", "side_c", "side_d"}
TRUSTED_SENSITIVITY_MODELS = [
    "baseline_conservative",
    "battle_only_baseline",
    "hierarchical_weighted",
    "hierarchical_equal_split",
    "hierarchical_broader_eligibility",
]
PRIMARY_ERA_ORDER = [
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


def percentile_score(series: pd.Series) -> pd.Series:
    series = pd.to_numeric(series, errors="coerce").fillna(0.0)
    if len(series) <= 1:
        return pd.Series([100.0] * len(series), index=series.index, dtype=float)
    return series.rank(method="average", pct=True) * 100.0


def tier_from_score(score: float) -> str:
    if score >= 90:
        return "elite"
    if score >= 80:
        return "very_strong"
    if score >= 70:
        return "strong"
    if score >= 60:
        return "solid"
    return "qualified"


def stability_label(model_count: int, rank_range: float) -> str:
    if model_count >= 4 and rank_range <= 10:
        return "core_stable"
    if model_count >= 4 and rank_range <= 20:
        return "stable"
    if model_count >= 3 and rank_range > 40:
        return "highly_model_sensitive"
    if model_count >= 2 and rank_range > 20:
        return "model_sensitive"
    return "limited_comparison"


def page_profile_class(battle_share: float, operation_share: float, campaign_share: float, war_share: float) -> str:
    if battle_share >= 0.70:
        return "battle_dominant"
    if (campaign_share + war_share) >= 0.50 and (campaign_share + war_share) > battle_share:
        return "war_campaign_heavy"
    if operation_share >= 0.40:
        return "operation_heavy"
    return "mixed_profile"


def safe_text(value: Any) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass
    text = normalize_space(value)
    return "" if text.lower() == "nan" else text


def write_csv(path: Path, frame: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, encoding="utf-8-sig")


def prepare_rows(output_root: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    base = output_root / "derived_scoring"
    annotated = pd.read_csv(base / "commander_engagements_annotated.csv", dtype=str).fillna("")
    bridge = pd.read_csv(base / "commander_identity_bridge.csv", dtype=str).fillna("")
    summary = pd.read_csv(base / "commander_engagement_summary.csv", dtype=str).fillna("")
    page_profile = pd.read_csv(base / "commander_page_type_profile.csv", dtype=str).fillna("")
    outcome_profile = pd.read_csv(base / "commander_outcome_profile.csv", dtype=str).fillna("")

    annotated["eligible_strict_flag"] = annotated["eligible_strict"].eq("1")
    annotated["eligible_balanced_flag"] = annotated["eligible_balanced"].eq("1")
    annotated["valid_side_flag"] = annotated["side"].isin(VALID_SIDES)
    annotated["outcome_credit_fraction_num"] = pd.to_numeric(
        annotated["outcome_credit_fraction"], errors="coerce"
    ).fillna(0.0)
    annotated["page_weight_model_b_num"] = pd.to_numeric(annotated["page_weight_model_b"], errors="coerce").fillna(0.0)
    annotated["analytic_year_num"] = pd.to_numeric(annotated["analytic_year"], errors="coerce")

    side_counts = (
        annotated.loc[annotated["valid_side_flag"]]
        .groupby(["battle_id", "side"])
        .size()
        .to_dict()
    )
    presence_split = []
    for row in annotated.to_dict(orient="records"):
        if row["side"] in VALID_SIDES:
            count = side_counts.get((row["battle_id"], row["side"]), 1)
            presence_split.append(1.0 / max(count, 1))
        else:
            presence_split.append(0.0)
    annotated["presence_factor_full"] = annotated["valid_side_flag"].astype(float)
    annotated["presence_factor_split"] = presence_split
    annotated["outcome_factor_full"] = (
        annotated["valid_side_flag"] & annotated["outcome_category"].ne("unknown")
    ).astype(float)
    annotated["outcome_factor_split"] = (
        annotated["outcome_credit_fraction_num"]
        * annotated["outcome_category"].ne("unknown").astype(float)
    )

    for mode, mapping in OUTCOME_SCORE_MAPS.items():
        annotated[f"outcome_score_{mode}"] = (
            annotated["outcome_category"].map(mapping).astype(float)
        )

    balanced_battle_overlap = set(
        zip(
            annotated.loc[
                annotated["eligible_balanced_flag"] & annotated["page_type"].eq("battle_article"),
                "analytic_commander_id",
            ],
            annotated.loc[
                annotated["eligible_balanced_flag"] & annotated["page_type"].eq("battle_article"),
                "hierarchy_overlap_key",
            ],
        )
    )
    balanced_weights = []
    battle_only_weights = []
    for row in annotated.to_dict(orient="records"):
        if row["eligible_balanced"] == "1":
            base_weight = PAGE_TYPE_WEIGHTS.get(row["page_type"], 0.0)
            penalty = 0.5 if row["page_type"] != "battle_article" and (
                row["analytic_commander_id"], row["hierarchy_overlap_key"]
            ) in balanced_battle_overlap else 1.0
            balanced_weights.append(base_weight * penalty)
        else:
            balanced_weights.append(0.0)
        battle_only_weights.append(1.0 if row["eligible_strict"] == "1" and row["page_type"] == "battle_article" else 0.0)
    annotated["page_weight_hier_balanced"] = balanced_weights
    annotated["page_weight_battle_only"] = battle_only_weights

    return annotated, bridge, summary, page_profile, outcome_profile


def aggregate_model_metrics(
    annotated: pd.DataFrame,
    row_weight_col: str,
    outcome_mode: str,
    presence_mode: str,
    outcome_credit_mode: str,
) -> pd.DataFrame:
    presence_factor_col = "presence_factor_full" if presence_mode == "full" else "presence_factor_split"
    outcome_factor_col = "outcome_factor_full" if outcome_credit_mode == "full" else "outcome_factor_split"
    outcome_col = f"outcome_score_{outcome_mode}"

    active = annotated.loc[pd.to_numeric(annotated[row_weight_col], errors="coerce").fillna(0.0) > 0].copy()
    active["row_weight"] = pd.to_numeric(active[row_weight_col], errors="coerce").fillna(0.0)
    active["presence_mass"] = active["row_weight"] * pd.to_numeric(active[presence_factor_col], errors="coerce").fillna(0.0)
    active["outcome_mass"] = active["row_weight"] * pd.to_numeric(active[outcome_factor_col], errors="coerce").fillna(0.0)
    active["known_outcome_flag_num"] = active["outcome_category"].ne("unknown").astype(int)
    active["weighted_outcome_value"] = active["outcome_mass"] * pd.to_numeric(active[outcome_col], errors="coerce").fillna(0.0)

    active["battle_flag"] = active["page_type"].eq("battle_article").astype(int)
    active["operation_flag"] = active["page_type"].eq("operation_article").astype(int)
    active["campaign_flag"] = active["page_type"].eq("campaign_article").astype(int)
    active["war_flag"] = active["page_type"].eq("war_conflict_article").astype(int)
    active["known_battle_flag"] = (
        active["page_type"].eq("battle_article") & active["outcome_category"].ne("unknown")
    ).astype(int)
    active["battle_presence_mass"] = active["presence_mass"] * active["battle_flag"]
    active["nonbattle_presence_mass"] = active["presence_mass"] * (1 - active["battle_flag"])
    active["era_bucket_known"] = active["era_bucket"].where(active["era_bucket"].ne("unknown"), "")

    grouped = active.groupby("analytic_commander_id", sort=False)
    metrics = grouped.agg(
        engagement_count=("battle_id", "size"),
        battle_count=("battle_flag", "sum"),
        operation_count=("operation_flag", "sum"),
        campaign_count=("campaign_flag", "sum"),
        war_count=("war_flag", "sum"),
        known_outcome_count=("known_outcome_flag_num", "sum"),
        known_battle_outcome_count=("known_battle_flag", "sum"),
        presence_mass=("presence_mass", "sum"),
        battle_presence_mass=("battle_presence_mass", "sum"),
        nonbattle_presence_mass=("nonbattle_presence_mass", "sum"),
        outcome_weight_sum=("outcome_mass", "sum"),
        weighted_outcome_value=("weighted_outcome_value", "sum"),
        conflict_breadth=("conflict_key", "nunique"),
        page_type_diversity=("page_type", "nunique"),
        first_year=("analytic_year_num", "min"),
        last_year=("analytic_year_num", "max"),
    ).reset_index()
    metrics["known_outcome_share"] = metrics["known_outcome_count"] / metrics["engagement_count"].clip(lower=1)
    metrics["known_battle_outcome_share"] = metrics["known_battle_outcome_count"] / metrics["battle_count"].clip(lower=1)
    metrics["outcome_mean"] = metrics["weighted_outcome_value"] / metrics["outcome_weight_sum"].replace({0: pd.NA})
    metrics["outcome_mean"] = pd.to_numeric(metrics["outcome_mean"], errors="coerce").fillna(0.0)
    metrics["active_span_years"] = (metrics["last_year"] - metrics["first_year"]).fillna(0)
    metrics["higher_level_share"] = metrics["nonbattle_presence_mass"] / metrics["presence_mass"].replace({0: pd.NA})
    metrics["higher_level_share"] = pd.to_numeric(metrics["higher_level_share"], errors="coerce").fillna(0.0)
    metrics["battle_share"] = metrics["battle_count"] / metrics["engagement_count"].clip(lower=1)
    metrics["operation_share"] = metrics["operation_count"] / metrics["engagement_count"].clip(lower=1)
    metrics["campaign_share"] = metrics["campaign_count"] / metrics["engagement_count"].clip(lower=1)
    metrics["war_share"] = metrics["war_count"] / metrics["engagement_count"].clip(lower=1)

    era_div = (
        active.loc[active["era_bucket_known"].ne("")]
        .groupby("analytic_commander_id")["era_bucket_known"]
        .nunique()
        .rename("era_diversity")
    )
    metrics = metrics.merge(era_div, on="analytic_commander_id", how="left")
    metrics["era_diversity"] = metrics["era_diversity"].fillna(0).astype(int)

    era_counts = (
        active.loc[active["era_bucket_known"].ne("")]
        .groupby(["analytic_commander_id", "era_bucket_known"])
        .size()
        .reset_index(name="n")
        .sort_values(["analytic_commander_id", "n", "era_bucket_known"], ascending=[True, False, True])
        .drop_duplicates(subset=["analytic_commander_id"])
        .rename(columns={"era_bucket_known": "primary_era_bucket"})
    )
    metrics = metrics.merge(era_counts[["analytic_commander_id", "primary_era_bucket"]], on="analytic_commander_id", how="left")
    metrics["primary_era_bucket"] = metrics["primary_era_bucket"].fillna("unknown")

    for column in ["first_year", "last_year", "active_span_years"]:
        metrics[column] = pd.to_numeric(metrics[column], errors="coerce").fillna(0).astype(int)
    return metrics


def finalize_model_scores(
    metrics: pd.DataFrame,
    bridge: pd.DataFrame,
    summary: pd.DataFrame,
    page_profile: pd.DataFrame,
    outcome_profile: pd.DataFrame,
    *,
    model_name: str,
    score_mode: str,
    cohort_rule: str,
) -> pd.DataFrame:
    frame = metrics.merge(bridge, on="analytic_commander_id", how="left")
    frame = frame.merge(summary, on=["analytic_commander_id", "display_name"], how="left", suffixes=("", "_summary"))
    frame = frame.merge(page_profile, on=["analytic_commander_id", "display_name"], how="left", suffixes=("", "_page"))
    frame = frame.merge(outcome_profile, on=["analytic_commander_id", "display_name"], how="left", suffixes=("", "_outcome"))

    frame["linked_ok"] = frame["is_linked_identity"].eq("1")
    frame["suspect_ok"] = frame["is_suspect_identity"].ne("1")

    if cohort_rule == "baseline":
        cohort_mask = (
            frame["linked_ok"]
            & frame["suspect_ok"]
            & (pd.to_numeric(frame["battle_count"], errors="coerce").fillna(0) >= 5)
            & (pd.to_numeric(frame["known_battle_outcome_count"], errors="coerce").fillna(0) >= 3)
        )
        frame["outcome_shrunk_raw"] = (
            pd.to_numeric(frame["outcome_mean"], errors="coerce").fillna(0)
            * (
                pd.to_numeric(frame["known_battle_outcome_count"], errors="coerce").fillna(0)
                / (pd.to_numeric(frame["known_battle_outcome_count"], errors="coerce").fillna(0) + 5.0)
            )
        )
        frame["depth_raw"] = pd.to_numeric(frame["battle_count"], errors="coerce").fillna(0).map(math.log1p)
        frame["reliability_raw"] = (
            0.7 * pd.to_numeric(frame["known_battle_outcome_share"], errors="coerce").fillna(0)
            + 0.3 * (pd.to_numeric(frame["known_battle_outcome_count"], errors="coerce").fillna(0).clip(upper=10) / 10.0)
        )
        eligible = frame.loc[cohort_mask].copy()
        eligible["component_outcome"] = percentile_score(eligible["outcome_shrunk_raw"])
        eligible["component_depth"] = percentile_score(eligible["depth_raw"])
        eligible["component_reliability"] = percentile_score(eligible["reliability_raw"])
        eligible["score_normalized"] = (
            0.60 * eligible["component_outcome"]
            + 0.25 * eligible["component_depth"]
            + 0.15 * eligible["component_reliability"]
        )
    elif cohort_rule == "battle_only":
        cohort_mask = (
            frame["linked_ok"]
            & frame["suspect_ok"]
            & (pd.to_numeric(frame["battle_count"], errors="coerce").fillna(0) >= 3)
            & (pd.to_numeric(frame["known_battle_outcome_count"], errors="coerce").fillna(0) >= 1)
        )
        frame["outcome_shrunk_raw"] = (
            pd.to_numeric(frame["outcome_mean"], errors="coerce").fillna(0)
            * (
                pd.to_numeric(frame["known_battle_outcome_count"], errors="coerce").fillna(0)
                / (pd.to_numeric(frame["known_battle_outcome_count"], errors="coerce").fillna(0) + 5.0)
            )
        )
        frame["depth_raw"] = pd.to_numeric(frame["battle_count"], errors="coerce").fillna(0).map(math.log1p)
        eligible = frame.loc[cohort_mask].copy()
        eligible["component_outcome"] = percentile_score(eligible["outcome_shrunk_raw"])
        eligible["component_depth"] = percentile_score(eligible["depth_raw"])
        eligible["score_normalized"] = 0.75 * eligible["component_outcome"] + 0.25 * eligible["component_depth"]
        eligible["component_reliability"] = ""
    else:
        cohort_mask = (
            frame["linked_ok"]
            & frame["suspect_ok"]
            & (pd.to_numeric(frame["engagement_count"], errors="coerce").fillna(0) >= 5)
            & (pd.to_numeric(frame["known_outcome_count"], errors="coerce").fillna(0) >= 3)
        )
        frame["outcome_shrunk_raw"] = (
            pd.to_numeric(frame["outcome_mean"], errors="coerce").fillna(0)
            * (
                pd.to_numeric(frame["known_outcome_count"], errors="coerce").fillna(0)
                / (pd.to_numeric(frame["known_outcome_count"], errors="coerce").fillna(0) + 5.0)
            )
        )
        frame["scope_conflict_raw"] = pd.to_numeric(frame["conflict_breadth"], errors="coerce").fillna(0).map(math.log1p)
        frame["scope_page_type_raw"] = pd.to_numeric(frame["page_type_diversity"], errors="coerce").fillna(0)
        frame["scope_era_raw"] = pd.to_numeric(frame["era_diversity"], errors="coerce").fillna(0)
        frame["temporal_raw"] = (
            pd.to_numeric(frame.get("active_span_years_nonwar", frame["active_span_years"]), errors="coerce")
            .fillna(pd.to_numeric(frame["active_span_years"], errors="coerce").fillna(0))
            .clip(upper=60)
            .map(math.log1p)
        )
        frame["centrality_raw"] = pd.to_numeric(frame["presence_mass"], errors="coerce").fillna(0).map(math.log1p)
        frame["higher_level_raw"] = pd.to_numeric(frame["nonbattle_presence_mass"], errors="coerce").fillna(0).map(math.log1p)
        frame["evidence_raw"] = (
            0.60 * pd.to_numeric(frame["known_outcome_share"], errors="coerce").fillna(0)
            + 0.40 * pd.to_numeric(frame["known_battle_outcome_share"], errors="coerce").fillna(0)
        )
        eligible = frame.loc[cohort_mask].copy()
        eligible["component_outcome"] = percentile_score(eligible["outcome_shrunk_raw"])
        eligible["component_scope_conflict"] = percentile_score(eligible["scope_conflict_raw"])
        eligible["component_scope_page_type"] = percentile_score(eligible["scope_page_type_raw"])
        eligible["component_scope_era"] = percentile_score(eligible["scope_era_raw"])
        eligible["component_scope"] = (
            eligible["component_scope_conflict"] + eligible["component_scope_page_type"] + eligible["component_scope_era"]
        ) / 3.0
        eligible["component_temporal"] = percentile_score(eligible["temporal_raw"])
        eligible["component_centrality"] = percentile_score(eligible["centrality_raw"])
        eligible["component_higher_level"] = percentile_score(eligible["higher_level_raw"])
        eligible["component_evidence"] = percentile_score(eligible["evidence_raw"])
        eligible["score_pre_guardrail"] = (
            0.45 * eligible["component_outcome"]
            + 0.20 * eligible["component_scope"]
            + 0.15 * eligible["component_temporal"]
            + 0.10 * eligible["component_centrality"]
            + 0.06 * eligible["component_higher_level"]
            + 0.04 * eligible["component_evidence"]
        )
        eligible["confidence_guardrail_factor"] = 1.0
        combo_mask = (
            pd.to_numeric(eligible["higher_level_share"], errors="coerce").fillna(0.0) >= 0.50
        ) & (
            pd.to_numeric(eligible["known_outcome_share"], errors="coerce").fillna(0.0) < 0.40
        )
        eligible.loc[combo_mask, "confidence_guardrail_factor"] = 0.95
        sparse_higher_level_mask = (
            pd.to_numeric(eligible["known_outcome_count"], errors="coerce").fillna(0.0) < 8.0
        ) & (
            pd.to_numeric(eligible["known_outcome_share"], errors="coerce").fillna(0.0) < 0.50
        ) & (
            pd.to_numeric(eligible["higher_level_share"], errors="coerce").fillna(0.0) >= 0.35
        )
        eligible.loc[sparse_higher_level_mask, "confidence_guardrail_factor"] = (
            eligible.loc[sparse_higher_level_mask, "confidence_guardrail_factor"].clip(upper=0.95)
        )
        thin_battle_anchor_mask = (
            pd.to_numeric(eligible["higher_level_share"], errors="coerce").fillna(0.0) >= 0.50
        ) & (
            pd.to_numeric(eligible["known_battle_outcome_count"], errors="coerce").fillna(0.0) < 2.0
        ) & (
            pd.to_numeric(eligible["battle_count"], errors="coerce").fillna(0.0) < 4.0
        )
        eligible.loc[thin_battle_anchor_mask, "confidence_guardrail_factor"] = (
            eligible.loc[thin_battle_anchor_mask, "confidence_guardrail_factor"].clip(upper=0.92)
        )
        eligible["score_normalized"] = (
            eligible["score_pre_guardrail"] * eligible["confidence_guardrail_factor"]
        )
        eligible["component_depth"] = ""
        eligible["component_reliability"] = ""

    eligible["page_type_profile_class"] = eligible.apply(
        lambda row: page_profile_class(
            float(row["battle_share"]),
            float(row["operation_share"]),
            float(row["campaign_share"]),
            float(row["war_share"]),
        ),
        axis=1,
    )
    eligible["score_tier"] = eligible["score_normalized"].map(tier_from_score)
    eligible = eligible.sort_values(
        ["score_normalized", "outcome_shrunk_raw", "engagement_count", "display_name"],
        ascending=[False, False, False, True],
    ).reset_index(drop=True)
    eligible["rank"] = range(1, len(eligible) + 1)
    eligible["model_name"] = model_name
    eligible["score_mode"] = score_mode
    eligible["cohort_rule"] = cohort_rule
    eligible["caution_flags"] = eligible.apply(
        lambda row: join_flags(
            [
                safe_text(row.get("feature_quality_flags", "")),
                safe_text(row.get("missing_data_flags", "")),
                "higher_level_dependent" if float(row.get("higher_level_share", 0) or 0) >= 0.50 else "",
                "higher_level_low_evidence_combo"
                if (
                    pd.notna(pd.to_numeric(row.get("higher_level_share", ""), errors="coerce"))
                    and pd.notna(pd.to_numeric(row.get("known_outcome_share", ""), errors="coerce"))
                    and float(pd.to_numeric(row.get("higher_level_share", ""), errors="coerce")) >= 0.50
                    and float(pd.to_numeric(row.get("known_outcome_share", ""), errors="coerce")) < 0.40
                )
                else "",
                "sparse_higher_level_evidence"
                if (
                    pd.notna(pd.to_numeric(row.get("known_outcome_count", ""), errors="coerce"))
                    and pd.notna(pd.to_numeric(row.get("known_outcome_share", ""), errors="coerce"))
                    and pd.notna(pd.to_numeric(row.get("higher_level_share", ""), errors="coerce"))
                    and float(pd.to_numeric(row.get("known_outcome_count", ""), errors="coerce")) < 8.0
                    and float(pd.to_numeric(row.get("known_outcome_share", ""), errors="coerce")) < 0.50
                    and float(pd.to_numeric(row.get("higher_level_share", ""), errors="coerce")) >= 0.35
                )
                else "",
                "thin_battle_anchor"
                if (
                    pd.notna(pd.to_numeric(row.get("higher_level_share", ""), errors="coerce"))
                    and pd.notna(pd.to_numeric(row.get("known_battle_outcome_count", ""), errors="coerce"))
                    and pd.notna(pd.to_numeric(row.get("battle_count", ""), errors="coerce"))
                    and float(pd.to_numeric(row.get("higher_level_share", ""), errors="coerce")) >= 0.50
                    and float(pd.to_numeric(row.get("known_battle_outcome_count", ""), errors="coerce")) < 2.0
                    and float(pd.to_numeric(row.get("battle_count", ""), errors="coerce")) < 4.0
                )
                else "",
            ]
        ),
        axis=1,
    )
    return eligible


def build_rankings(output_root: Path) -> dict[str, Any]:
    annotated, bridge, summary, page_profile, outcome_profile = prepare_rows(output_root)

    model_frames = {
        "baseline_conservative": finalize_model_scores(
            aggregate_model_metrics(
                annotated,
                row_weight_col="page_weight_battle_only",
                outcome_mode="conservative",
                presence_mode="full",
                outcome_credit_mode="split",
            ),
            bridge,
            summary,
            page_profile,
            outcome_profile,
            model_name="baseline_conservative",
            score_mode="conservative",
            cohort_rule="baseline",
        ),
        "battle_only_baseline": finalize_model_scores(
            aggregate_model_metrics(
                annotated,
                row_weight_col="page_weight_battle_only",
                outcome_mode="conservative",
                presence_mode="full",
                outcome_credit_mode="split",
            ),
            bridge,
            summary,
            page_profile,
            outcome_profile,
            model_name="battle_only_baseline",
            score_mode="conservative",
            cohort_rule="battle_only",
        ),
        "hierarchical_weighted": finalize_model_scores(
            aggregate_model_metrics(
                annotated,
                row_weight_col="page_weight_model_b_num",
                outcome_mode="balanced",
                presence_mode="full",
                outcome_credit_mode="split",
            ),
            bridge,
            summary,
            page_profile,
            outcome_profile,
            model_name="hierarchical_weighted",
            score_mode="balanced",
            cohort_rule="hierarchical",
        ),
        "hierarchical_full_credit": finalize_model_scores(
            aggregate_model_metrics(
                annotated,
                row_weight_col="page_weight_model_b_num",
                outcome_mode="balanced",
                presence_mode="full",
                outcome_credit_mode="full",
            ),
            bridge,
            summary,
            page_profile,
            outcome_profile,
            model_name="hierarchical_full_credit",
            score_mode="balanced",
            cohort_rule="hierarchical",
        ),
        "hierarchical_equal_split": finalize_model_scores(
            aggregate_model_metrics(
                annotated,
                row_weight_col="page_weight_model_b_num",
                outcome_mode="balanced",
                presence_mode="split",
                outcome_credit_mode="split",
            ),
            bridge,
            summary,
            page_profile,
            outcome_profile,
            model_name="hierarchical_equal_split",
            score_mode="balanced",
            cohort_rule="hierarchical",
        ),
        "hierarchical_broader_eligibility": finalize_model_scores(
            aggregate_model_metrics(
                annotated,
                row_weight_col="page_weight_hier_balanced",
                outcome_mode="balanced",
                presence_mode="full",
                outcome_credit_mode="split",
            ),
            bridge,
            summary,
            page_profile,
            outcome_profile,
            model_name="hierarchical_broader_eligibility",
            score_mode="balanced",
            cohort_rule="hierarchical",
        ),
    }

    baseline = model_frames["baseline_conservative"].copy()
    hierarchical = model_frames["hierarchical_weighted"].copy()
    battle_only = model_frames["battle_only_baseline"].copy()

    baseline_cols = [
        "rank",
        "score_normalized",
        "score_tier",
        "analytic_commander_id",
        "display_name",
        "canonical_wikipedia_url",
        "primary_era_bucket",
        "battle_count",
        "known_battle_outcome_count",
        "known_battle_outcome_share",
        "outcome_shrunk_raw",
        "component_outcome",
        "component_depth",
        "component_reliability",
        "conflict_breadth",
        "active_span_years",
        "page_type_profile_class",
        "caution_flags",
    ]
    hierarchical_cols = [
        "rank",
        "score_normalized",
        "score_tier",
        "analytic_commander_id",
        "display_name",
        "canonical_wikipedia_url",
        "primary_era_bucket",
        "engagement_count",
        "battle_count",
        "operation_count",
        "campaign_count",
        "war_count",
        "known_outcome_count",
        "known_outcome_share",
        "outcome_shrunk_raw",
        "component_outcome",
        "component_scope",
        "component_temporal",
        "component_centrality",
        "component_higher_level",
        "component_evidence",
        "active_span_years_nonwar",
        "higher_level_share",
        "page_type_profile_class",
        "caution_flags",
    ]
    write_csv(output_root / "RANKING_RESULTS_BASELINE.csv", baseline[baseline_cols])
    write_csv(output_root / "RANKING_RESULTS_HIERARCHICAL.csv", hierarchical[hierarchical_cols])
    write_csv(output_root / "RANKING_RESULTS_BATTLE_ONLY.csv", battle_only[baseline_cols])

    all_ids = sorted(set().union(*[set(frame["analytic_commander_id"]) for frame in model_frames.values()]))
    identity_lookup = bridge.set_index("analytic_commander_id")[["display_name", "canonical_wikipedia_url"]]
    sensitivity = pd.DataFrame({"analytic_commander_id": all_ids})
    sensitivity = sensitivity.merge(identity_lookup, on="analytic_commander_id", how="left")

    for model_name, frame in model_frames.items():
        subset = frame[["analytic_commander_id", "rank", "score_normalized", "score_tier", "primary_era_bucket", "page_type_profile_class", "caution_flags"]].copy()
        subset = subset.rename(
            columns={
                "rank": f"rank_{model_name}",
                "score_normalized": f"score_{model_name}",
                "score_tier": f"tier_{model_name}",
                "primary_era_bucket": f"primary_era_{model_name}",
                "page_type_profile_class": f"profile_{model_name}",
                "caution_flags": f"caution_{model_name}",
            }
        )
        sensitivity = sensitivity.merge(subset, on="analytic_commander_id", how="left")

    rank_cols = [column for column in sensitivity.columns if column.startswith("rank_")]
    ranks_numeric = sensitivity[rank_cols].apply(pd.to_numeric, errors="coerce")
    trusted_rank_cols = [f"rank_{model}" for model in TRUSTED_SENSITIVITY_MODELS]
    trusted_ranks_numeric = sensitivity[trusted_rank_cols].apply(pd.to_numeric, errors="coerce")
    sensitivity["models_eligible_count"] = trusted_ranks_numeric.notna().sum(axis=1)
    sensitivity["best_rank"] = trusted_ranks_numeric.min(axis=1)
    sensitivity["worst_rank"] = trusted_ranks_numeric.max(axis=1)
    sensitivity["rank_range"] = sensitivity["worst_rank"] - sensitivity["best_rank"]
    sensitivity["mean_rank"] = trusted_ranks_numeric.mean(axis=1)
    sensitivity["std_rank"] = trusted_ranks_numeric.std(axis=1).fillna(0.0)
    sensitivity["top10_appearances"] = (trusted_ranks_numeric <= 10).sum(axis=1)
    sensitivity["top25_appearances"] = (trusted_ranks_numeric <= 25).sum(axis=1)
    sensitivity["top50_appearances"] = (trusted_ranks_numeric <= 50).sum(axis=1)
    sensitivity["stability_label"] = sensitivity.apply(
        lambda row: stability_label(int(row["models_eligible_count"]), float(row["rank_range"]) if pd.notna(row["rank_range"]) else 999.0),
        axis=1,
    )
    sensitivity["primary_era_bucket"] = sensitivity.apply(
        lambda row: next(
            (safe_text(row[col]) for col in [c for c in sensitivity.columns if c.startswith("primary_era_")] if safe_text(row[col])),
            "unknown",
        ),
        axis=1,
    )
    sensitivity["page_type_profile_class"] = sensitivity.apply(
        lambda row: next(
            (safe_text(row[col]) for col in [c for c in sensitivity.columns if c.startswith("profile_")] if safe_text(row[col])),
            "mixed_profile",
        ),
        axis=1,
    )
    caution_cols = [column for column in sensitivity.columns if column.startswith("caution_")]
    sensitivity["caution_flags"] = sensitivity.apply(
        lambda row: join_flags([safe_text(row[column]) for column in caution_cols]),
        axis=1,
    )
    sensitivity = sensitivity.sort_values(["rank_baseline_conservative", "rank_hierarchical_weighted", "display_name"], ascending=[True, True, True])
    write_csv(output_root / "RANKING_RESULTS_SENSITIVITY.csv", sensitivity)

    top_ids = set()
    for model_name, frame in model_frames.items():
        if model_name not in TRUSTED_SENSITIVITY_MODELS:
            continue
        top_ids.update(frame.head(50)["analytic_commander_id"].tolist())
    top_summary = sensitivity.loc[sensitivity["analytic_commander_id"].isin(top_ids)].copy()
    top_summary = top_summary.merge(
        summary[
            [
                "analytic_commander_id",
                "total_engagements_strict",
                "total_battle_pages_strict",
                "total_war_pages_strict",
                "total_campaign_pages_strict",
                "total_operation_pages_strict",
                "distinct_conflicts_strict",
                "distinct_opponents_strict",
            ]
        ],
        on="analytic_commander_id",
        how="left",
    )
    top_summary = top_summary.merge(
        outcome_profile[
            [
                "analytic_commander_id",
                "known_outcome_count",
                "count_victory",
                "count_decisive_victory",
                "count_tactical_victory",
                "count_pyrrhic_victory",
                "count_defeat",
                "count_major_defeat",
                "count_indecisive",
                "count_draw",
                "count_stalemate",
                "count_disputed",
                "count_unknown",
            ]
        ],
        on="analytic_commander_id",
        how="left",
    )
    top_summary["outcome_profile_summary"] = top_summary.apply(
        lambda row: (
            f"V={int(float(row['count_victory'] or 0)) + int(float(row['count_decisive_victory'] or 0)) + int(float(row['count_tactical_victory'] or 0)) + int(float(row['count_pyrrhic_victory'] or 0))}; "
            f"D={int(float(row['count_defeat'] or 0)) + int(float(row['count_major_defeat'] or 0))}; "
            f"N={int(float(row['count_indecisive'] or 0)) + int(float(row['count_draw'] or 0)) + int(float(row['count_stalemate'] or 0)) + int(float(row['count_disputed'] or 0))}; "
            f"U={int(float(row['count_unknown'] or 0))}"
        ),
        axis=1,
    )
    top_summary["page_type_exposure_summary"] = top_summary.apply(
        lambda row: (
            f"B={row['total_battle_pages_strict']}; O={row['total_operation_pages_strict']}; "
            f"C={row['total_campaign_pages_strict']}; W={row['total_war_pages_strict']}"
        ),
        axis=1,
    )
    top_summary = top_summary.sort_values(["rank_baseline_conservative", "rank_hierarchical_weighted", "display_name"])
    keep_cols = [
        "display_name",
        "canonical_wikipedia_url",
        "primary_era_bucket",
        "rank_baseline_conservative",
        "rank_battle_only_baseline",
        "rank_hierarchical_weighted",
        "rank_hierarchical_full_credit",
        "rank_hierarchical_equal_split",
        "rank_hierarchical_broader_eligibility",
        "score_baseline_conservative",
        "score_hierarchical_weighted",
        "total_engagements_strict",
        "total_battle_pages_strict",
        "distinct_conflicts_strict",
        "distinct_opponents_strict",
        "known_outcome_count",
        "outcome_profile_summary",
        "page_type_exposure_summary",
        "page_type_profile_class",
        "stability_label",
        "caution_flags",
    ]
    write_csv(output_root / "TOP_COMMANDERS_SUMMARY.csv", top_summary[keep_cols])

    top_slices_rows = []
    for model_name, frame in model_frames.items():
        for size in (25, 50, 100):
            for _, row in frame.head(size).iterrows():
                top_slices_rows.append(
                    {
                        "model_name": model_name,
                        "slice_name": f"top_{size}",
                        "rank": int(row["rank"]),
                        "display_name": row["display_name"],
                        "primary_era_bucket": row["primary_era_bucket"],
                        "score_normalized": float(row["score_normalized"]),
                    }
                )
    write_csv(output_root / "RANKING_RESULTS_TOP_SLICES.csv", pd.DataFrame(top_slices_rows))

    era_rows = []
    for model_name, frame in {
        "baseline_conservative": baseline,
        "hierarchical_weighted": hierarchical,
    }.items():
        for era_bucket, group in frame.groupby("primary_era_bucket", sort=False):
            group = group.sort_values(["score_normalized", "rank"], ascending=[False, True]).reset_index(drop=True)
            for idx, row in group.iterrows():
                era_rows.append(
                    {
                        "model_name": model_name,
                        "era_bucket": era_bucket,
                        "rank_in_era": idx + 1,
                        "global_rank": int(row["rank"]),
                        "display_name": row["display_name"],
                        "score_normalized": float(row["score_normalized"]),
                        "page_type_profile_class": row["page_type_profile_class"],
                    }
                )
    write_csv(output_root / "RANKING_RESULTS_BY_ERA.csv", pd.DataFrame(era_rows))

    profile_rows = []
    for model_name, frame in {
        "baseline_conservative": baseline,
        "hierarchical_weighted": hierarchical,
    }.items():
        for profile_name, group in frame.groupby("page_type_profile_class", sort=False):
            group = group.sort_values(["score_normalized", "rank"], ascending=[False, True]).reset_index(drop=True)
            for idx, row in group.iterrows():
                profile_rows.append(
                    {
                        "model_name": model_name,
                        "page_type_profile_class": profile_name,
                        "rank_in_profile": idx + 1,
                        "global_rank": int(row["rank"]),
                        "display_name": row["display_name"],
                        "score_normalized": float(row["score_normalized"]),
                        "primary_era_bucket": row["primary_era_bucket"],
                    }
                )
    write_csv(output_root / "RANKING_RESULTS_PAGE_TYPE_VIEWS.csv", pd.DataFrame(profile_rows))

    metrics = {
        "model_rows": {name: int(len(frame)) for name, frame in model_frames.items()},
        "top_baseline": baseline.head(10)[["rank", "display_name", "score_normalized"]].to_dict(orient="records"),
        "top_hierarchical": hierarchical.head(10)[["rank", "display_name", "score_normalized"]].to_dict(orient="records"),
    }
    (output_root / "RANKING_BUILD_METRICS.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description="Build ranking outputs from the frozen scoring package.")
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("outputs_final_2026-04-05"),
        help="Frozen output directory containing derived_scoring tables.",
    )
    args = parser.parse_args()
    metrics = build_rankings(args.output_root)
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
