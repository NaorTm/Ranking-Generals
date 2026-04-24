from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parent


MODEL_KEYS = [
    "baseline_conservative",
    "battle_only_baseline",
    "hierarchical_trust_v2",
    "hierarchical_weighted",
    "hierarchical_full_credit",
    "hierarchical_equal_split",
    "hierarchical_broader_eligibility",
]

MODEL_LABELS = {
    "baseline_conservative": "Conservative baseline",
    "battle_only_baseline": "Battle-only baseline",
    "hierarchical_trust_v2": "Trust-first v2",
    "hierarchical_weighted": "Hierarchical weighted",
    "hierarchical_full_credit": "Hierarchical full-credit (diagnostic)",
    "hierarchical_equal_split": "Hierarchical equal-split",
    "hierarchical_broader_eligibility": "Hierarchical broader-eligibility",
}

INTERPRETIVE_ERA_MAP = {
    "ancient": "ancient",
    "medieval": "medieval",
    "early_modern": "early_modern",
    "revolutionary_napoleonic": "modern",
    "long_nineteenth_century": "modern",
    "world_wars": "modern",
    "cold_war": "modern",
    "contemporary": "contemporary",
}

OUTCOME_GROUP_MAP = {
    "victory_family": [
        "decisive_victory",
        "victory",
        "tactical_victory",
        "pyrrhic_victory",
    ],
    "indecisive_family": [
        "indecisive",
        "draw",
        "stalemate",
        "disputed",
    ],
    "defeat_family": ["defeat", "major_defeat"],
    "unknown": ["unknown"],
}


def load_csv(snapshot_dir: Path, name: str) -> pd.DataFrame:
    return pd.read_csv(snapshot_dir / name)


def load_scoring_csv(snapshot_dir: Path, name: str) -> pd.DataFrame:
    return pd.read_csv(snapshot_dir / "derived_scoring" / name)


def load_optional_csv(snapshot_dir: Path, name: str) -> pd.DataFrame:
    path = snapshot_dir / name
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def to_numeric(df: pd.DataFrame, columns: list[str]) -> None:
    for column in columns:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")


def clean_value(value: Any) -> Any:
    if pd.isna(value):
        return None
    if isinstance(value, (pd.Timestamp,)):
        return value.isoformat()
    if isinstance(value, (int, float)):
        return float(value) if isinstance(value, float) else value
    return str(value)


def split_flags(value: Any) -> list[str]:
    text = "" if pd.isna(value) else str(value).strip()
    if not text:
        return []
    return [part.strip() for part in text.split("|") if part.strip()]


def interpretive_era(primary_era_bucket: str | None) -> str:
    if not primary_era_bucket:
        return "modern"
    return INTERPRETIVE_ERA_MAP.get(primary_era_bucket, "modern")


def model_field(key: str, suffix: str) -> str:
    return f"{suffix}_{key}" if suffix == "rank" else f"{suffix}_{key}"


def build_dashboard_dataset(snapshot_dir: Path) -> dict[str, Any]:
    sensitivity = load_csv(snapshot_dir, "RANKING_RESULTS_SENSITIVITY.csv")
    summary = load_csv(snapshot_dir, "TOP_COMMANDERS_SUMMARY.csv")
    classification = load_csv(snapshot_dir, "TOP_TIER_CLASSIFICATION.csv")
    era_shortlist = load_csv(snapshot_dir, "ERA_ELITE_SHORTLIST.csv")
    audit = load_csv(snapshot_dir, "MODEL_SENSITIVITY_AUDIT.csv")
    outcome_profile = load_scoring_csv(snapshot_dir, "commander_outcome_profile.csv")
    page_type_profile = load_scoring_csv(snapshot_dir, "commander_page_type_profile.csv")
    era_profile = load_scoring_csv(snapshot_dir, "commander_era_profile.csv")
    ranking_features = load_scoring_csv(snapshot_dir, "commander_ranking_features.csv")
    model_stability = load_optional_csv(snapshot_dir, "derived_scoring/commander_model_stability.csv")
    commander_tiers = load_optional_csv(snapshot_dir, "derived_scoring/commander_tiers.csv")
    page_type_contributions = load_optional_csv(snapshot_dir, "derived_scoring/page_type_score_contributions.csv")
    high_ranked_flags = load_optional_csv(snapshot_dir, "audits/high_ranked_commander_flags.csv")
    rank_confidence = load_optional_csv(snapshot_dir, "derived_scoring/commander_rank_confidence_summary.csv")
    confidence_adjusted_tiers = load_optional_csv(snapshot_dir, "derived_scoring/commander_tiers_confidence_adjusted.csv")

    sensitivity_numeric = [
        "best_rank",
        "worst_rank",
        "rank_range",
        "mean_rank",
        "std_rank",
        "top10_appearances",
        "top25_appearances",
        "top50_appearances",
        "models_eligible_count",
    ]
    for model in MODEL_KEYS:
        sensitivity_numeric.extend([f"rank_{model}", f"score_{model}"])
    to_numeric(sensitivity, sensitivity_numeric)
    to_numeric(
        summary,
        [
            "rank_baseline_conservative",
            "rank_battle_only_baseline",
            "rank_hierarchical_trust_v2",
            "rank_hierarchical_weighted",
            "rank_hierarchical_full_credit",
            "rank_hierarchical_equal_split",
            "rank_hierarchical_broader_eligibility",
            "score_baseline_conservative",
            "score_hierarchical_trust_v2",
            "score_hierarchical_weighted",
            "total_engagements_strict",
            "total_battle_pages_strict",
            "distinct_conflicts_strict",
            "distinct_opponents_strict",
            "known_outcome_count",
        ],
    )
    to_numeric(
        classification,
        [
            "best_rank",
            "worst_rank",
            "rank_range",
            "mean_rank",
            "top10_appearances",
            "top25_appearances",
            "known_outcome_count",
            "total_engagements_strict",
            "total_battle_pages_strict",
            "distinct_conflicts_strict",
        ]
        + [f"rank_{model}" for model in MODEL_KEYS],
    )
    to_numeric(
        outcome_profile,
        [
            "eligible_strict_engagement_count",
            "known_outcome_count",
            "known_outcome_share",
            "mean_conservative_score",
            "mean_balanced_score",
            "mean_aggressive_score",
        ]
        + [f"count_{name}" for name in ["decisive_victory", "victory", "tactical_victory", "pyrrhic_victory", "indecisive", "draw", "stalemate", "disputed", "defeat", "major_defeat", "unknown"]]
        + [f"share_{name}" for name in ["decisive_victory", "victory", "tactical_victory", "pyrrhic_victory", "indecisive", "draw", "stalemate", "disputed", "defeat", "major_defeat", "unknown"]],
    )
    to_numeric(
        page_type_profile,
        [
            "engagements_all",
            "engagements_strict",
            "weighted_presence_model_a",
            "weighted_presence_model_b",
            "weighted_presence_model_c",
            "count_strict_battle_article",
            "share_strict_battle_article",
            "count_strict_operation_article",
            "share_strict_operation_article",
            "count_strict_campaign_article",
            "share_strict_campaign_article",
            "count_strict_war_conflict_article",
            "share_strict_war_conflict_article",
        ],
    )
    to_numeric(
        era_profile,
        [
            "engagements_strict",
            "count_ancient",
            "count_medieval",
            "count_early_modern",
            "count_revolutionary_napoleonic",
            "count_long_nineteenth_century",
            "count_world_wars",
            "count_cold_war",
            "count_contemporary",
            "count_unknown",
            "share_ancient",
            "share_medieval",
            "share_early_modern",
            "share_revolutionary_napoleonic",
            "share_long_nineteenth_century",
            "share_world_wars",
            "share_cold_war",
            "share_contemporary",
            "share_unknown",
        ],
    )
    to_numeric(
        ranking_features,
        [
            "high_confidence_participation_count",
            "eligible_engagement_count_strict",
            "eligible_battle_count_strict",
            "eligible_operation_count_strict",
            "eligible_campaign_count_strict",
            "eligible_war_count_strict",
            "weighted_presence_model_a",
            "weighted_presence_model_b",
            "weighted_presence_model_c",
            "conflict_breadth_strict",
            "page_type_diversity_strict",
            "era_diversity_strict",
            "first_analytic_year",
            "last_analytic_year",
            "active_span_years",
            "known_outcome_count_strict",
            "known_outcome_share_strict",
            "mean_outcome_conservative",
            "mean_outcome_balanced",
            "mean_outcome_aggressive",
            "non_defeat_share_strict",
            "outcome_variance_balanced",
            "capped_participation_intensity",
            "overlap_rate_strict_nonbattle",
            "opponent_breadth_strict",
        ],
    )
    if not model_stability.empty:
        to_numeric(
            model_stability,
            [
                "models_present_count",
                "trusted_models_present_count",
                "best_rank",
                "worst_rank",
                "median_rank",
                "mean_rank",
                "rank_stddev",
                "rank_iqr",
                "top_10_count",
                "top_25_count",
                "top_50_count",
                "top_100_count",
                "stability_score",
            ],
        )
    if not commander_tiers.empty:
        to_numeric(
            commander_tiers,
            [
                "rank_hierarchical_trust_v2",
                "score_hierarchical_trust_v2",
                "tier_sort",
                "stability_score",
                "known_outcome_count",
                "known_outcome_share",
                "higher_level_share",
            ],
        )
    if not page_type_contributions.empty:
        to_numeric(
            page_type_contributions,
            [
                "raw_score_contribution",
                "weighted_score_contribution",
                "absolute_weighted_score_contribution",
                "weighted_presence",
                "share_of_total_score",
                "known_outcome_rows",
                "unknown_outcome_rows",
                "engagement_rows",
            ],
        )
    if not high_ranked_flags.empty:
        to_numeric(high_ranked_flags, ["rank_hierarchical_trust_v2", "supporting_value"])
    if not rank_confidence.empty:
        to_numeric(
            rank_confidence,
            [
                "headline_rank",
                "median_rank",
                "rank_p10",
                "rank_p90",
                "rank_band_width_80",
                "rank_band_width_90",
                "broad_page_contribution_share",
                "known_outcome_count",
                "bootstrap_presence_rate",
            ],
        )
    if not confidence_adjusted_tiers.empty:
        to_numeric(
            confidence_adjusted_tiers,
            [
                "headline_rank",
                "median_rank",
                "rank_p10",
                "rank_p90",
                "rank_band_width_80",
                "rank_band_width_90",
                "bootstrap_presence_rate",
                "score_normalized",
            ],
        )

    commander_ids = set(sensitivity["analytic_commander_id"])
    outcome_profile = outcome_profile[outcome_profile["analytic_commander_id"].isin(commander_ids)]
    page_type_profile = page_type_profile[page_type_profile["analytic_commander_id"].isin(commander_ids)]
    era_profile = era_profile[era_profile["analytic_commander_id"].isin(commander_ids)]
    ranking_features = ranking_features[ranking_features["analytic_commander_id"].isin(commander_ids)]
    if not model_stability.empty:
        model_stability = model_stability[model_stability["analytic_commander_id"].isin(commander_ids)]
    if not commander_tiers.empty:
        commander_tiers = commander_tiers[commander_tiers["analytic_commander_id"].isin(commander_ids)]
    if not page_type_contributions.empty:
        page_type_contributions = page_type_contributions[
            page_type_contributions["analytic_commander_id"].isin(commander_ids)
        ]
    if not high_ranked_flags.empty:
        high_ranked_flags = high_ranked_flags[high_ranked_flags["analytic_commander_id"].isin(commander_ids)]
    if not rank_confidence.empty:
        rank_confidence = rank_confidence[rank_confidence["analytic_commander_id"].isin(commander_ids)]
    if not confidence_adjusted_tiers.empty:
        confidence_adjusted_tiers = confidence_adjusted_tiers[
            confidence_adjusted_tiers["analytic_commander_id"].isin(commander_ids)
        ]

    stability_by_id = {
        row["analytic_commander_id"]: {
            "score": clean_value(row.get("stability_score")),
            "category": clean_value(row.get("stability_category")),
            "modelsPresentCount": clean_value(row.get("models_present_count")),
            "trustedModelsPresentCount": clean_value(row.get("trusted_models_present_count")),
            "bestRank": clean_value(row.get("best_rank")),
            "worstRank": clean_value(row.get("worst_rank")),
            "medianRank": clean_value(row.get("median_rank")),
            "meanRank": clean_value(row.get("mean_rank")),
            "rankStddev": clean_value(row.get("rank_stddev")),
            "rankIqr": clean_value(row.get("rank_iqr")),
            "top10Count": clean_value(row.get("top_10_count")),
            "top25Count": clean_value(row.get("top_25_count")),
            "top50Count": clean_value(row.get("top_50_count")),
            "top100Count": clean_value(row.get("top_100_count")),
        }
        for _, row in model_stability.iterrows()
    } if not model_stability.empty else {}
    tier_by_id = {
        row["analytic_commander_id"]: {
            "key": clean_value(row.get("tier_key")),
            "label": clean_value(row.get("tier_label")),
            "sort": clean_value(row.get("tier_sort")),
            "reason": clean_value(row.get("tier_reason")),
        }
        for _, row in commander_tiers.iterrows()
    } if not commander_tiers.empty else {}
    page_contributions_by_id: dict[str, list[dict[str, Any]]] = {}
    if not page_type_contributions.empty:
        for commander_id, group in page_type_contributions.groupby("analytic_commander_id"):
            group = group.sort_values("share_of_total_score", ascending=False)
            page_contributions_by_id[commander_id] = [
                {
                    "pageType": clean_value(row.get("page_type")),
                    "rawScoreContribution": clean_value(row.get("raw_score_contribution")),
                    "weightedScoreContribution": clean_value(row.get("weighted_score_contribution")),
                    "shareOfTotalScore": clean_value(row.get("share_of_total_score")),
                    "knownOutcomeRows": clean_value(row.get("known_outcome_rows")),
                    "unknownOutcomeRows": clean_value(row.get("unknown_outcome_rows")),
                    "engagementRows": clean_value(row.get("engagement_rows")),
                }
                for _, row in group.iterrows()
            ]
    audit_flags_by_id: dict[str, list[dict[str, Any]]] = {}
    if not high_ranked_flags.empty:
        flagged = high_ranked_flags[
            high_ranked_flags["flagged"].astype(str).str.lower().eq("true")
        ].copy()
        for commander_id, group in flagged.groupby("analytic_commander_id"):
            audit_flags_by_id[commander_id] = [
                {
                    "flag": clean_value(row.get("flag")),
                    "supportingValue": clean_value(row.get("supporting_value")),
                    "explanation": clean_value(row.get("explanation")),
                }
                for _, row in group.sort_values("flag").iterrows()
            ]
    rank_confidence_by_id = {
        row["analytic_commander_id"]: {
            "headlineRank": clean_value(row.get("headline_rank")),
            "medianRank": clean_value(row.get("median_rank")),
            "rankInterval80": clean_value(row.get("rank_interval_80")),
            "rankInterval90": clean_value(row.get("rank_interval_90")),
            "rankP10": clean_value(row.get("rank_p10")),
            "rankP90": clean_value(row.get("rank_p90")),
            "rankBandWidth80": clean_value(row.get("rank_band_width_80")),
            "rankBandWidth90": clean_value(row.get("rank_band_width_90")),
            "confidenceCategory": clean_value(row.get("confidence_category")),
            "bootstrapPresenceRate": clean_value(row.get("bootstrap_presence_rate")),
            "recommendedInterpretation": clean_value(row.get("recommended_interpretation")),
        }
        for _, row in rank_confidence.iterrows()
    } if not rank_confidence.empty else {}
    confidence_tier_by_id = {
        row["analytic_commander_id"]: {
            "key": clean_value(row.get("confidence_adjusted_tier_key")),
            "label": clean_value(row.get("confidence_adjusted_tier")),
            "reason": clean_value(row.get("confidence_adjusted_tier_reason")),
        }
        for _, row in confidence_adjusted_tiers.iterrows()
    } if not confidence_adjusted_tiers.empty else {}

    summary = summary.rename(columns={column: f"summary_{column}" for column in summary.columns})
    classification = classification.rename(
        columns={
            "display_name": "classification_display_name",
            "canonical_wikipedia_url": "classification_canonical_wikipedia_url",
            "primary_era_bucket": "classification_primary_era_bucket",
            "caution_flags": "classification_caution_flags",
        }
    )

    merged = sensitivity.merge(
        summary,
        left_on="canonical_wikipedia_url",
        right_on="summary_canonical_wikipedia_url",
        how="left",
    )
    merged = merged.merge(
        classification[
            [
                "classification_display_name",
                "classification_canonical_wikipedia_url",
                "interpretive_group",
                "dominant_sensitivity_driver",
                "interpretive_reason",
            ]
        ],
        left_on=["display_name", "canonical_wikipedia_url"],
        right_on=["classification_display_name", "classification_canonical_wikipedia_url"],
        how="left",
    )
    merged = merged.merge(
        outcome_profile.drop(columns=["display_name"]),
        on="analytic_commander_id",
        how="left",
    )
    merged = merged.merge(
        page_type_profile.drop(columns=["display_name"]),
        on="analytic_commander_id",
        how="left",
    )
    merged = merged.merge(
        era_profile.drop(columns=["display_name"]),
        on="analytic_commander_id",
        how="left",
    )
    merged = merged.merge(
        ranking_features.drop(columns=["display_name", "canonical_wikipedia_url"], errors="ignore"),
        on="analytic_commander_id",
        how="left",
    )

    commanders: list[dict[str, Any]] = []
    for _, row in merged.iterrows():
        commander_id = clean_value(row.get("analytic_commander_id"))
        stability_info = stability_by_id.get(row.get("analytic_commander_id"), {})
        tier_info = tier_by_id.get(row.get("analytic_commander_id"), {})
        audit_flags = audit_flags_by_id.get(row.get("analytic_commander_id"), [])
        page_contributions = page_contributions_by_id.get(row.get("analytic_commander_id"), [])
        rank_confidence_info = rank_confidence_by_id.get(row.get("analytic_commander_id"), {})
        confidence_tier_info = confidence_tier_by_id.get(row.get("analytic_commander_id"), {})
        primary_era_bucket = (
            clean_value(row.get("primary_era_bucket"))
            or clean_value(row.get("primary_era_bucket_x"))
            or clean_value(row.get("summary_primary_era_bucket"))
            or clean_value(row.get("primary_era_bucket_y"))
        )
        ranks = {model: clean_value(row.get(f"rank_{model}")) for model in MODEL_KEYS}
        scores = {model: clean_value(row.get(f"score_{model}")) for model in MODEL_KEYS}

        page_counts = {
            "battle": clean_value(row.get("count_strict_battle_article")) or 0,
            "operation": clean_value(row.get("count_strict_operation_article")) or 0,
            "campaign": clean_value(row.get("count_strict_campaign_article")) or 0,
            "war": clean_value(row.get("count_strict_war_conflict_article")) or 0,
        }
        page_shares = {
            "battle": clean_value(row.get("share_strict_battle_article")) or 0,
            "operation": clean_value(row.get("share_strict_operation_article")) or 0,
            "campaign": clean_value(row.get("share_strict_campaign_article")) or 0,
            "war": clean_value(row.get("share_strict_war_conflict_article")) or 0,
        }
        higher_level_share = (
            float(page_shares["operation"])
            + float(page_shares["campaign"])
            + float(page_shares["war"])
        )

        outcome_counts_raw = {
            "decisive_victory": clean_value(row.get("count_decisive_victory")) or 0,
            "victory": clean_value(row.get("count_victory")) or 0,
            "tactical_victory": clean_value(row.get("count_tactical_victory")) or 0,
            "pyrrhic_victory": clean_value(row.get("count_pyrrhic_victory")) or 0,
            "indecisive": clean_value(row.get("count_indecisive")) or 0,
            "draw": clean_value(row.get("count_draw")) or 0,
            "stalemate": clean_value(row.get("count_stalemate")) or 0,
            "disputed": clean_value(row.get("count_disputed")) or 0,
            "defeat": clean_value(row.get("count_defeat")) or 0,
            "major_defeat": clean_value(row.get("count_major_defeat")) or 0,
            "unknown": clean_value(row.get("count_unknown")) or 0,
        }
        outcome_shares_raw = {
            key: clean_value(row.get(f"share_{key}")) or 0 for key in outcome_counts_raw
        }

        grouped_outcomes: dict[str, dict[str, float]] = {}
        for group_name, keys in OUTCOME_GROUP_MAP.items():
            grouped_outcomes[group_name] = {
                "count": float(sum(float(outcome_counts_raw.get(key, 0) or 0) for key in keys)),
                "share": float(sum(float(outcome_shares_raw.get(key, 0) or 0) for key in keys)),
            }

        era_counts = {
            "ancient": clean_value(row.get("count_ancient")) or 0,
            "medieval": clean_value(row.get("count_medieval")) or 0,
            "early_modern": clean_value(row.get("count_early_modern")) or 0,
            "revolutionary_napoleonic": clean_value(row.get("count_revolutionary_napoleonic")) or 0,
            "long_nineteenth_century": clean_value(row.get("count_long_nineteenth_century")) or 0,
            "world_wars": clean_value(row.get("count_world_wars")) or 0,
            "cold_war": clean_value(row.get("count_cold_war")) or 0,
            "contemporary": clean_value(row.get("count_contemporary")) or 0,
            "unknown": clean_value(row.get("count_unknown")) or 0,
        }
        era_shares = {
            "ancient": clean_value(row.get("share_ancient")) or 0,
            "medieval": clean_value(row.get("share_medieval")) or 0,
            "early_modern": clean_value(row.get("share_early_modern")) or 0,
            "revolutionary_napoleonic": clean_value(row.get("share_revolutionary_napoleonic")) or 0,
            "long_nineteenth_century": clean_value(row.get("share_long_nineteenth_century")) or 0,
            "world_wars": clean_value(row.get("share_world_wars")) or 0,
            "cold_war": clean_value(row.get("share_cold_war")) or 0,
            "contemporary": clean_value(row.get("share_contemporary")) or 0,
            "unknown": clean_value(row.get("share_unknown")) or 0,
        }

        baseline_rank = row.get("rank_baseline_conservative")
        trust_rank = row.get("rank_hierarchical_trust_v2")
        hierarchical_rank = row.get("rank_hierarchical_weighted")
        battle_rank = row.get("rank_battle_only_baseline")
        full_credit_rank = row.get("rank_hierarchical_full_credit")
        broader_rank = row.get("rank_hierarchical_broader_eligibility")

        commanders.append(
            {
                "id": clean_value(row.get("analytic_commander_id")),
                "name": clean_value(row.get("display_name")),
                "url": clean_value(row.get("canonical_wikipedia_url")),
                "primaryEraBucket": primary_era_bucket,
                "interpretiveEra": interpretive_era(primary_era_bucket),
                "pageTypeProfileClass": clean_value(row.get("page_type_profile_class")),
                "stabilityLabel": clean_value(row.get("stability_label")) or clean_value(row.get("summary_stability_label")),
                "stabilityCategory": stability_info.get("category"),
                "stabilityScore": stability_info.get("score"),
                "tier": tier_info,
                "rankConfidence": rank_confidence_info,
                "confidenceAdjustedTier": confidence_tier_info,
                "robustnessCategory": clean_value(row.get("interpretive_group")) or "other_ranked",
                "trustConfidence": clean_value(row.get("summary_trust_confidence_v2")) or clean_value(row.get("trust_confidence_v2")),
                "trustHeadlineReason": clean_value(row.get("summary_trust_headline_reason_v2")) or clean_value(row.get("trust_headline_reason_v2")),
                "dominantSensitivityDriver": clean_value(row.get("dominant_sensitivity_driver")) or "mixed_model_sensitivity",
                "interpretiveReason": clean_value(row.get("interpretive_reason")),
                "cautionFlags": split_flags(row.get("caution_flags")) or split_flags(row.get("summary_caution_flags")),
                "featureQualityFlags": split_flags(row.get("feature_quality_flags")),
                "auditFlags": audit_flags,
                "modelsEligibleCount": clean_value(row.get("models_eligible_count")) or 0,
                "bestRank": clean_value(row.get("best_rank")),
                "worstRank": clean_value(row.get("worst_rank")),
                "rankRange": clean_value(row.get("rank_range")),
                "meanRank": clean_value(row.get("mean_rank")),
                "stdRank": clean_value(row.get("std_rank")),
                "top10Appearances": clean_value(row.get("top10_appearances")) or 0,
                "top25Appearances": clean_value(row.get("top25_appearances")) or 0,
                "top50Appearances": clean_value(row.get("top50_appearances")) or 0,
                "engagementCount": clean_value(row.get("summary_total_engagements_strict"))
                or clean_value(row.get("eligible_engagement_count_strict"))
                or clean_value(row.get("engagements_strict"))
                or 0,
                "battleCount": clean_value(row.get("summary_total_battle_pages_strict"))
                or clean_value(row.get("eligible_battle_count_strict"))
                or page_counts["battle"],
                "knownOutcomeCount": clean_value(row.get("summary_known_outcome_count"))
                or clean_value(row.get("known_outcome_count_strict"))
                or clean_value(row.get("known_outcome_count")),
                "knownOutcomeShare": clean_value(row.get("summary_known_outcome_share"))
                or clean_value(row.get("known_outcome_share_strict")),
                "distinctConflicts": clean_value(row.get("summary_distinct_conflicts_strict"))
                or clean_value(row.get("conflict_breadth_strict")),
                "distinctOpponents": clean_value(row.get("summary_distinct_opponents_strict"))
                or clean_value(row.get("opponent_breadth_strict")),
                "activeSpanYears": clean_value(row.get("active_span_years")),
                "cappedParticipationIntensity": clean_value(row.get("capped_participation_intensity")),
                "overlapRate": clean_value(row.get("overlap_rate_strict_nonbattle")),
                "ranks": ranks,
                "scores": scores,
                "pageTypes": {
                    "counts": page_counts,
                    "shares": page_shares,
                    "higherLevelShare": higher_level_share,
                    "contributions": page_contributions,
                },
                "stability": stability_info,
                "outcomes": {
                    "counts": outcome_counts_raw,
                    "shares": outcome_shares_raw,
                    "grouped": grouped_outcomes,
                    "evidenceReliabilityBand": clean_value(row.get("outcome_evidence_reliability_band")),
                },
                "eras": {
                    "counts": era_counts,
                    "shares": era_shares,
                    "primary": clean_value(row.get("primary_era_bucket")) or primary_era_bucket,
                    "multiEra": bool(clean_value(row.get("multi_era_flag")) or False),
                },
                "modelDependence": {
                    "trustVsHierarchicalRankGap": clean_value(
                        (trust_rank - hierarchical_rank)
                        if pd.notna(trust_rank) and pd.notna(hierarchical_rank)
                        else None
                    ),
                    "battleVsHierarchicalRankGap": clean_value(
                        (battle_rank - hierarchical_rank)
                        if pd.notna(battle_rank) and pd.notna(hierarchical_rank)
                        else None
                    ),
                    "baselineVsHierarchicalRankGap": clean_value(
                        (baseline_rank - hierarchical_rank)
                        if pd.notna(baseline_rank) and pd.notna(hierarchical_rank)
                        else None
                    ),
                    "fullCreditGain": clean_value(
                        (hierarchical_rank - full_credit_rank)
                        if pd.notna(hierarchical_rank) and pd.notna(full_credit_rank)
                        else None
                    ),
                    "broaderEligibilityGain": clean_value(
                        (hierarchical_rank - broader_rank)
                        if pd.notna(hierarchical_rank) and pd.notna(broader_rank)
                        else None
                    ),
                },
            }
        )

    classification_rows = []
    for _, row in classification.iterrows():
        classification_rows.append(
            {
                "displayName": clean_value(row.get("classification_display_name")) or clean_value(row.get("display_name")),
                "canonicalWikipediaUrl": clean_value(row.get("classification_canonical_wikipedia_url")) or clean_value(row.get("canonical_wikipedia_url")),
                "interpretiveGroup": clean_value(row.get("interpretive_group")),
                "primaryEraBucket": clean_value(row.get("classification_primary_era_bucket")) or clean_value(row.get("primary_era_bucket")),
                "bestRank": clean_value(row.get("best_rank")),
                "worstRank": clean_value(row.get("worst_rank")),
                "rankRange": clean_value(row.get("rank_range")),
                "meanRank": clean_value(row.get("mean_rank")),
                "top25Appearances": clean_value(row.get("top25_appearances")),
                "trustConfidence": clean_value(row.get("trust_confidence_v2")),
                "dominantSensitivityDriver": clean_value(row.get("dominant_sensitivity_driver")),
                "interpretiveReason": clean_value(row.get("interpretive_reason")),
            }
        )

    era_shortlist_rows = []
    for _, row in era_shortlist.iterrows():
        era_shortlist_rows.append(
            {
                "requestedEra": clean_value(row.get("requested_era")),
                "supportBand": clean_value(row.get("support_band")),
                "displayName": clean_value(row.get("display_name")),
                "canonicalWikipediaUrl": clean_value(row.get("canonical_wikipedia_url")),
                "primaryEraBucket": clean_value(row.get("primary_era_bucket")),
                "bestRank": clean_value(row.get("best_rank")),
                "meanRank": clean_value(row.get("mean_rank")),
                "top25Appearances": clean_value(row.get("top25_appearances")),
                "rankBaseline": clean_value(row.get("rank_baseline_conservative")),
                "rankTrustV2": clean_value(row.get("rank_hierarchical_trust_v2")),
                "rankHierarchical": clean_value(row.get("rank_hierarchical_weighted")),
                "rankSignature": clean_value(row.get("rank_signature")),
                "trustConfidence": clean_value(row.get("trust_confidence_v2")),
                "stabilityLabel": clean_value(row.get("stability_label")),
                "cautionFlags": split_flags(row.get("caution_flags")),
                "recommendationNote": clean_value(row.get("recommendation_note")),
                "caveatNote": clean_value(row.get("caveat_note")),
            }
        )

    audit_rows = []
    for _, row in audit.iterrows():
        audit_rows.append(
            {
                "displayName": clean_value(row.get("display_name")),
                "canonicalWikipediaUrl": clean_value(row.get("canonical_wikipedia_url")),
                "primaryEraBucket": clean_value(row.get("primary_era_bucket")),
                "bestRank": clean_value(row.get("best_rank")),
                "worstRank": clean_value(row.get("worst_rank")),
                "rankRange": clean_value(row.get("rank_range")),
                "ranks": {model: clean_value(row.get(f"rank_{model}")) for model in MODEL_KEYS},
                "trustConfidence": clean_value(row.get("trust_confidence_v2")),
                "stabilityLabel": clean_value(row.get("stability_label")),
                "cautionFlags": split_flags(row.get("caution_flags")),
                "dominantSensitivityDriver": clean_value(row.get("dominant_sensitivity_driver")),
                "auditNote": clean_value(row.get("audit_note")),
            }
        )

    counts_by_group = (
        pd.Series([commander["robustnessCategory"] for commander in commanders])
        .value_counts(dropna=False)
        .to_dict()
    )
    counts_by_era = (
        pd.Series([commander["interpretiveEra"] for commander in commanders])
        .value_counts(dropna=False)
        .to_dict()
    )
    counts_by_tier = (
        pd.Series([commander.get("tier", {}).get("label") or "Unclassified" for commander in commanders])
        .value_counts(dropna=False)
        .to_dict()
    )
    counts_by_stability = (
        pd.Series([commander.get("stabilityCategory") or "unknown" for commander in commanders])
        .value_counts(dropna=False)
        .to_dict()
    )

    generated_from = [
        "derived_scoring/commander_ranking_features.csv",
        "derived_scoring/commander_outcome_profile.csv",
        "derived_scoring/commander_page_type_profile.csv",
        "derived_scoring/commander_era_profile.csv",
        "RANKING_RESULTS_BASELINE.csv",
        "RANKING_RESULTS_BATTLE_ONLY.csv",
        "RANKING_RESULTS_HIERARCHICAL_TRUST_V2.csv",
        "RANKING_RESULTS_HIERARCHICAL.csv",
        "RANKING_RESULTS_SENSITIVITY.csv",
        "TOP_COMMANDERS_SUMMARY.csv",
        "TOP_TIER_CLASSIFICATION.csv",
        "ERA_ELITE_SHORTLIST.csv",
        "MODEL_SENSITIVITY_AUDIT.csv",
    ]
    for optional_source, frame in [
        ("derived_scoring/commander_model_stability.csv", model_stability),
        ("derived_scoring/commander_tiers.csv", commander_tiers),
        ("derived_scoring/page_type_score_contributions.csv", page_type_contributions),
        ("audits/high_ranked_commander_flags.csv", high_ranked_flags),
        ("derived_scoring/commander_rank_confidence_summary.csv", rank_confidence),
        ("derived_scoring/commander_tiers_confidence_adjusted.csv", confidence_adjusted_tiers),
    ]:
        if not frame.empty:
            generated_from.append(optional_source)

    metadata = {
        "snapshot": snapshot_dir.name,
        "headlineModel": "hierarchical_trust_v2",
        "generatedFrom": generated_from,
        "models": [{"key": key, "label": MODEL_LABELS[key]} for key in MODEL_KEYS],
        "counts": {
            "commanderCount": len(commanders),
            "robustEliteCount": int(counts_by_group.get("robust_elite_core", 0)),
            "strongModelSensitiveCount": int(counts_by_group.get("strong_upper_tier", 0)),
            "cautionCount": int(counts_by_group.get("model_sensitive_band", 0)),
            "otherRankedCount": int(counts_by_group.get("other_ranked", 0)),
        },
        "countsByInterpretiveEra": {str(k): int(v) for k, v in counts_by_era.items()},
        "countsByTier": {str(k): int(v) for k, v in counts_by_tier.items()},
        "countsByStability": {str(k): int(v) for k, v in counts_by_stability.items()},
    }

    return {
        "metadata": metadata,
        "commanders": commanders,
        "topTierClassification": classification_rows,
        "eraShortlist": era_shortlist_rows,
        "sensitivityAudit": audit_rows,
    }


def write_data_js(snapshot_dir: Path, dataset: dict[str, Any]) -> None:
    dashboard_dir = snapshot_dir / "dashboard"
    dashboard_dir.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(dataset, ensure_ascii=False, separators=(",", ":"))
    (dashboard_dir / "dashboard_data.js").write_text(
        f"window.DASHBOARD_DATA={payload};\n",
        encoding="utf-8",
    )


def write_technical_note(snapshot_dir: Path, dataset: dict[str, Any]) -> None:
    snapshot_name = snapshot_dir.name
    note = f"""# Ranking Dashboard Technical Note

This dashboard is wired directly to the authoritative snapshot in `{snapshot_name}`.

Primary source tables:

- `derived_scoring/commander_ranking_features.csv`
- `derived_scoring/commander_outcome_profile.csv`
- `derived_scoring/commander_page_type_profile.csv`
- `derived_scoring/commander_era_profile.csv`
- `RANKING_RESULTS_BASELINE.csv`
- `RANKING_RESULTS_BATTLE_ONLY.csv`
- `RANKING_RESULTS_HIERARCHICAL_TRUST_V2.csv`
- `RANKING_RESULTS_HIERARCHICAL.csv`
- `RANKING_RESULTS_SENSITIVITY.csv`
- `TOP_COMMANDERS_SUMMARY.csv`
- `TOP_TIER_CLASSIFICATION.csv`
- `ERA_ELITE_SHORTLIST.csv`
- `MODEL_SENSITIVITY_AUDIT.csv`

Build process:

1. `build_ranking_dashboard.py` reads the ranking and scoring CSVs from the authoritative snapshot.
2. It joins those tables on `analytic_commander_id` and `canonical_wikipedia_url`.
3. It emits one consolidated browser dataset at `dashboard/dashboard_data.js`.
4. The static dashboard in `dashboard/index.html` reads that in-browser dataset and renders all views client-side.

What is included in the browser dataset:

- one commander record per ranked commander appearing in `RANKING_RESULTS_SENSITIVITY.csv`
- model ranks and normalized scores across six ranking variants, with `hierarchical_trust_v2` as the headline trust-first view
- engagement, conflict, outcome, page-type, and era profile metrics
- robustness classification from `TOP_TIER_CLASSIFICATION.csv`
- era shortlist rows from `ERA_ELITE_SHORTLIST.csv`
- focused audit rows from `MODEL_SENSITIVITY_AUDIT.csv`

Runtime characteristics:

- no backend is required
- the dashboard is fully static and can be opened locally
- charts are rendered client-side with the bundled `plotly.min.js`

Current commander universe in the dashboard: `{dataset["metadata"]["counts"]["commanderCount"]}`
"""
    (snapshot_dir / "RANKING_DASHBOARD_TECHNICAL_NOTE.md").write_text(note, encoding="utf-8")


def copy_dashboard_assets(snapshot_dir: Path, asset_source_dir: Path) -> None:
    dashboard_dir = snapshot_dir / "dashboard"
    dashboard_dir.mkdir(parents=True, exist_ok=True)

    for name in ["index.html", "app.js", "styles.css", "plotly.min.js", "README.md"]:
        source = asset_source_dir / name
        target = dashboard_dir / name
        if source.resolve() == target.resolve():
            continue
        if name in {"index.html", "README.md"}:
            text = source.read_text(encoding="utf-8")
            text = text.replace("outputs_final_2026-04-05", snapshot_dir.name)
            text = text.replace("outputs_cleaned_2026-04-10_authoritative", snapshot_dir.name)
            text = text.replace("outputs_cleaned_2026-04-11_globaltrust_authoritative", snapshot_dir.name)
            text = re.sub(r"outputs_cleaned_\d{4}-\d{2}-\d{2}_[A-Za-z0-9_]+", snapshot_dir.name, text)
            target.write_text(text, encoding="utf-8")
        else:
            shutil.copy2(source, target)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build dashboard bundle from a snapshot directory.")
    parser.add_argument(
        "--snapshot-dir",
        type=Path,
        default=Path("outputs_cleaned_2026-04-21_fullpopulation_authoritative"),
        help="Snapshot directory containing rebuilt scoring, ranking, and interpretive outputs.",
    )
    parser.add_argument(
        "--asset-source-dir",
        type=Path,
        default=Path("docs"),
        help="Source dashboard asset directory to copy static assets from.",
    )
    args = parser.parse_args()

    dataset = build_dashboard_dataset(args.snapshot_dir)
    copy_dashboard_assets(args.snapshot_dir, args.asset_source_dir)
    write_data_js(args.snapshot_dir, dataset)
    write_technical_note(args.snapshot_dir, dataset)


if __name__ == "__main__":
    main()
