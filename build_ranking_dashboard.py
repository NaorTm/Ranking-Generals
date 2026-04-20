from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(r"C:\Users\gameo\OneDrive\Desktop\test")


MODEL_KEYS = [
    "baseline_conservative",
    "battle_only_baseline",
    "hierarchical_weighted",
    "hierarchical_full_credit",
    "hierarchical_equal_split",
    "hierarchical_broader_eligibility",
]

MODEL_LABELS = {
    "baseline_conservative": "Conservative baseline",
    "battle_only_baseline": "Battle-only baseline",
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

    commander_ids = set(sensitivity["analytic_commander_id"])
    outcome_profile = outcome_profile[outcome_profile["analytic_commander_id"].isin(commander_ids)]
    page_type_profile = page_type_profile[page_type_profile["analytic_commander_id"].isin(commander_ids)]
    era_profile = era_profile[era_profile["analytic_commander_id"].isin(commander_ids)]
    ranking_features = ranking_features[ranking_features["analytic_commander_id"].isin(commander_ids)]

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
                "robustnessCategory": clean_value(row.get("interpretive_group")) or "other_ranked",
                "dominantSensitivityDriver": clean_value(row.get("dominant_sensitivity_driver")) or "mixed_model_sensitivity",
                "interpretiveReason": clean_value(row.get("interpretive_reason")),
                "cautionFlags": split_flags(row.get("caution_flags")) or split_flags(row.get("summary_caution_flags")),
                "featureQualityFlags": split_flags(row.get("feature_quality_flags")),
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
                },
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
                "rankHierarchical": clean_value(row.get("rank_hierarchical_weighted")),
                "rankSignature": clean_value(row.get("rank_signature")),
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

    metadata = {
        "snapshot": snapshot_dir.name,
        "generatedFrom": [
            "derived_scoring/commander_ranking_features.csv",
            "derived_scoring/commander_outcome_profile.csv",
            "derived_scoring/commander_page_type_profile.csv",
            "derived_scoring/commander_era_profile.csv",
            "RANKING_RESULTS_BASELINE.csv",
            "RANKING_RESULTS_BATTLE_ONLY.csv",
            "RANKING_RESULTS_HIERARCHICAL.csv",
            "RANKING_RESULTS_SENSITIVITY.csv",
            "TOP_COMMANDERS_SUMMARY.csv",
            "TOP_TIER_CLASSIFICATION.csv",
            "ERA_ELITE_SHORTLIST.csv",
            "MODEL_SENSITIVITY_AUDIT.csv",
        ],
        "models": [{"key": key, "label": MODEL_LABELS[key]} for key in MODEL_KEYS],
        "counts": {
            "commanderCount": len(commanders),
            "robustEliteCount": int(counts_by_group.get("robust_elite", 0)),
            "strongModelSensitiveCount": int(counts_by_group.get("strong_but_model_sensitive", 0)),
            "cautionCount": int(counts_by_group.get("caution_likely_artifact", 0)),
            "otherRankedCount": int(counts_by_group.get("other_ranked", 0)),
        },
        "countsByInterpretiveEra": {str(k): int(v) for k, v in counts_by_era.items()},
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
- model ranks and normalized scores across five trusted ranking variants plus one diagnostic full-credit variant
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
        default=Path("outputs_final_2026-04-05"),
        help="Snapshot directory containing rebuilt scoring, ranking, and interpretive outputs.",
    )
    parser.add_argument(
        "--asset-source-dir",
        type=Path,
        default=Path("outputs_final_2026-04-05") / "dashboard",
        help="Source dashboard asset directory to copy static assets from.",
    )
    args = parser.parse_args()

    dataset = build_dashboard_dataset(args.snapshot_dir)
    copy_dashboard_assets(args.snapshot_dir, args.asset_source_dir)
    write_data_js(args.snapshot_dir, dataset)
    write_technical_note(args.snapshot_dir, dataset)


if __name__ == "__main__":
    main()
