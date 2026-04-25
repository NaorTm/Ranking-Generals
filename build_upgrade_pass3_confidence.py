from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

from build_scoring_framework_package import OUTCOME_SCORE_MAPS


DEFAULT_SNAPSHOT = Path("outputs_improved_2026-04-24_upgrade_pass3_confidence")
DEFAULT_ITERATIONS = 200
DEFAULT_SEED = 20260424
MODELS = [
    "hierarchical_trust_v2",
    "hierarchical_weighted",
    "baseline_conservative",
    "battle_only_baseline",
    "hierarchical_trust_v2_high_level_capped",
    "hierarchical_trust_v2_eligibility_filtered",
]
CAP_BROAD_SHARE = 0.40


def snapshot_file(snapshot_dir: Path, relative_name: str) -> Path:
    path = snapshot_dir / relative_name
    if path.exists():
        return path
    gzip_path = snapshot_dir / f"{relative_name}.gz"
    if gzip_path.exists():
        return gzip_path
    return path


def confidence_category(width_80: float) -> str:
    if width_80 <= 10:
        return "narrow"
    if width_80 <= 30:
        return "moderate"
    if width_80 <= 100:
        return "wide"
    return "very_wide"


def capped_adjustment_factor(broad_share: float, cap: float = CAP_BROAD_SHARE) -> float:
    broad_share = max(0.0, min(1.0, float(broad_share)))
    non_broad = 1.0 - broad_share
    if broad_share <= cap:
        return 1.0
    if non_broad <= 0:
        return 0.0
    allowed_broad = min(broad_share, (cap / (1.0 - cap)) * non_broad)
    return max(0.0, min(1.0, non_broad + allowed_broad))


def original_model_table(snapshot_dir: Path) -> pd.DataFrame:
    sensitivity = pd.read_csv(snapshot_dir / "RANKING_RESULTS_SENSITIVITY.csv")
    capped = pd.read_csv(snapshot_dir / "RANKING_RESULTS_HIERARCHICAL_TRUST_V2_HIGH_LEVEL_CAPPED.csv")
    filtered = pd.read_csv(snapshot_dir / "RANKING_RESULTS_HIERARCHICAL_TRUST_V2_ELIGIBILITY_FILTERED.csv")
    rows: list[dict[str, object]] = []

    for model in ["hierarchical_trust_v2", "hierarchical_weighted", "baseline_conservative", "battle_only_baseline"]:
        rank_col = f"rank_{model}"
        score_col = f"score_{model}"
        for _, row in sensitivity[["analytic_commander_id", "display_name", rank_col, score_col]].dropna(subset=[rank_col]).iterrows():
            rows.append(
                {
                    "analytic_commander_id": row["analytic_commander_id"],
                    "commander_name": row["display_name"],
                    "model_name": model,
                    "original_rank": int(row[rank_col]),
                    "original_score": float(row[score_col]),
                }
            )
    for _, row in capped.iterrows():
        rows.append(
            {
                "analytic_commander_id": row["analytic_commander_id"],
                "commander_name": row["display_name"],
                "model_name": "hierarchical_trust_v2_high_level_capped",
                "original_rank": int(row["rank_high_level_capped"]),
                "original_score": float(row["score_high_level_capped"]),
            }
        )
    for _, row in filtered.iterrows():
        rows.append(
            {
                "analytic_commander_id": row["analytic_commander_id"],
                "commander_name": row["display_name"],
                "model_name": "hierarchical_trust_v2_eligibility_filtered",
                "original_rank": int(row["rank_eligibility_filtered"]),
                "original_score": float(row["score_normalized"]),
            }
        )
    return pd.DataFrame(rows)


def run_bootstrap(snapshot_dir: Path, iterations: int, seed: int) -> tuple[pd.DataFrame, dict[str, object]]:
    start = time.time()
    annotated = pd.read_csv(snapshot_file(snapshot_dir, "derived_scoring/commander_engagements_annotated.csv"))
    for column in [
        "eligible_strict",
        "page_weight_model_b",
        "outcome_credit_fraction",
        "known_outcome_flag",
        "analytic_year",
    ]:
        annotated[column] = pd.to_numeric(annotated[column], errors="coerce").fillna(0.0)
    annotated["valid_side_flag"] = annotated["side"].isin({"side_a", "side_b", "side_c", "side_d"}).astype(float)
    annotated["outcome_score_balanced"] = annotated["outcome_category"].map(OUTCOME_SCORE_MAPS["balanced"]).fillna(0.0)
    annotated["outcome_score_conservative"] = annotated["outcome_category"].map(OUTCOME_SCORE_MAPS["conservative"]).fillna(0.0)
    annotated["battle_flag"] = annotated["page_type"].eq("battle_article").astype(float)
    annotated["operation_flag"] = annotated["page_type"].eq("operation_article").astype(float)
    annotated["campaign_flag"] = annotated["page_type"].eq("campaign_article").astype(float)
    annotated["war_flag"] = annotated["page_type"].eq("war_conflict_article").astype(float)
    annotated["battle_weight"] = annotated["eligible_strict"] * annotated["battle_flag"]
    annotated["hier_weight"] = annotated["eligible_strict"] * annotated["page_weight_model_b"]
    annotated["year_num"] = pd.to_numeric(annotated["analytic_year"], errors="coerce").fillna(0.0)

    id_to_name = (
        annotated[["analytic_commander_id", "display_name"]]
        .drop_duplicates("analytic_commander_id")
        .set_index("analytic_commander_id")["display_name"]
        .to_dict()
    )
    eligibility = pd.read_csv(snapshot_dir / "audits" / "commander_strict_eligibility_audit.csv")
    excluded_ids = set(
        eligibility.loc[
            eligibility["exclude_from_headline_ranking"].astype(str).str.lower().eq("true"),
            "analytic_commander_id",
        ]
    )

    battle_ids = np.array(sorted(annotated["battle_id"].dropna().unique()))
    battle_id_to_pos = {battle_id: idx for idx, battle_id in enumerate(battle_ids)}
    annotated["battle_pos"] = annotated["battle_id"].map(battle_id_to_pos).astype(int)
    rng = np.random.default_rng(seed)
    records: list[pd.DataFrame] = []
    original = original_model_table(snapshot_dir)
    original_ids_by_model = {
        model: set(original.loc[original["model_name"].eq(model), "analytic_commander_id"])
        for model in MODELS
    }

    def percentile(values: pd.Series) -> pd.Series:
        if values.empty:
            return values
        return values.rank(method="average", pct=True) * 100.0

    def compute_fast_model(sample: pd.DataFrame, model: str) -> pd.DataFrame:
        if model in {"baseline_conservative", "battle_only_baseline"}:
            weight_col = "battle_weight"
            outcome_col = "outcome_score_conservative"
            active = sample[sample[weight_col].gt(0)].copy()
        else:
            weight_col = "hier_weight"
            outcome_col = "outcome_score_balanced"
            active = sample[sample[weight_col].gt(0)].copy()

        if active.empty:
            return pd.DataFrame(columns=["analytic_commander_id", "commander_name", "rank", "score"])

        active["sample_weight"] = active["bootstrap_count"] * active[weight_col]
        active["outcome_mass"] = active["sample_weight"] * active["outcome_credit_fraction"]
        active["weighted_outcome_value"] = active["outcome_mass"] * active[outcome_col]
        active["known_mass"] = active["bootstrap_count"] * active["known_outcome_flag"]
        active["battle_mass"] = active["bootstrap_count"] * active["battle_flag"]
        active["nonbattle_presence"] = active["sample_weight"] * (1.0 - active["battle_flag"])

        grouped = active.groupby("analytic_commander_id", sort=False).agg(
            engagement_count=("bootstrap_count", "sum"),
            battle_count=("battle_mass", "sum"),
            known_outcome_count=("known_mass", "sum"),
            presence_mass=("sample_weight", "sum"),
            nonbattle_presence_mass=("nonbattle_presence", "sum"),
            outcome_weight_sum=("outcome_mass", "sum"),
            weighted_outcome_value=("weighted_outcome_value", "sum"),
            conflict_breadth=("conflict_key", "nunique"),
            first_year=("year_num", "min"),
            last_year=("year_num", "max"),
        ).reset_index()
        grouped["outcome_mean"] = grouped["weighted_outcome_value"] / grouped["outcome_weight_sum"].replace({0: np.nan})
        grouped["outcome_mean"] = grouped["outcome_mean"].fillna(0.0)
        grouped["outcome_shrunk"] = grouped["outcome_mean"] * (
            grouped["known_outcome_count"] / (grouped["known_outcome_count"] + 5.0)
        )
        grouped["known_outcome_share"] = grouped["known_outcome_count"] / grouped["engagement_count"].clip(lower=1)
        grouped["higher_level_share"] = grouped["nonbattle_presence_mass"] / grouped["presence_mass"].replace({0: np.nan})
        grouped["higher_level_share"] = grouped["higher_level_share"].fillna(0.0)
        grouped["active_span_years"] = (grouped["last_year"] - grouped["first_year"]).clip(lower=0, upper=60)
        grouped["scale_raw"] = np.log1p(grouped["engagement_count"])
        grouped["known_raw"] = np.log1p(grouped["known_outcome_count"])
        grouped["scope_raw"] = np.log1p(grouped["conflict_breadth"])
        grouped["temporal_raw"] = np.log1p(grouped["active_span_years"])
        grouped["centrality_raw"] = np.log1p(grouped["presence_mass"])
        grouped["evidence_raw"] = grouped["known_outcome_share"]

        model_ids = original_ids_by_model[model]
        if model == "hierarchical_trust_v2_high_level_capped":
            model_ids = original_ids_by_model["hierarchical_trust_v2_high_level_capped"]
        elif model == "hierarchical_trust_v2_eligibility_filtered":
            model_ids = original_ids_by_model["hierarchical_trust_v2_eligibility_filtered"]
        grouped = grouped[grouped["analytic_commander_id"].isin(model_ids)].copy()
        if grouped.empty:
            return pd.DataFrame(columns=["analytic_commander_id", "commander_name", "rank", "score"])

        grouped["component_outcome"] = percentile(grouped["outcome_shrunk"])
        grouped["component_scale"] = percentile(grouped["scale_raw"])
        grouped["component_known"] = percentile(grouped["known_raw"])
        grouped["component_scope"] = percentile(grouped["scope_raw"])
        grouped["component_temporal"] = percentile(grouped["temporal_raw"])
        grouped["component_centrality"] = percentile(grouped["centrality_raw"])
        grouped["component_evidence"] = percentile(grouped["evidence_raw"])

        if model in {"baseline_conservative", "battle_only_baseline"}:
            grouped["score"] = 0.75 * grouped["component_outcome"] + 0.25 * grouped["component_scale"]
        elif model == "hierarchical_weighted":
            grouped["score"] = (
                0.45 * grouped["component_outcome"]
                + 0.20 * grouped["component_scope"]
                + 0.15 * grouped["component_temporal"]
                + 0.10 * grouped["component_centrality"]
                + 0.10 * grouped["component_evidence"]
            )
        else:
            grouped["score"] = (
                0.32 * grouped["component_outcome"]
                + 0.18 * grouped["component_known"]
                + 0.18 * grouped["component_scope"]
                + 0.12 * grouped["component_temporal"]
                + 0.10 * grouped["component_centrality"]
                + 0.10 * grouped["component_evidence"]
            )
            if model == "hierarchical_trust_v2_high_level_capped":
                grouped["score"] = grouped["score"] * grouped["higher_level_share"].map(capped_adjustment_factor)

        grouped["commander_name"] = grouped["analytic_commander_id"].map(id_to_name)
        grouped = grouped.sort_values(["score", "outcome_shrunk", "engagement_count", "commander_name"], ascending=[False, False, False, True]).reset_index(drop=True)
        grouped["rank"] = range(1, len(grouped) + 1)
        return grouped[["analytic_commander_id", "commander_name", "rank", "score"]]

    for iteration in range(1, iterations + 1):
        sampled = rng.choice(battle_ids, size=len(battle_ids), replace=True)
        count_array = np.bincount([battle_id_to_pos[battle_id] for battle_id in sampled], minlength=len(battle_ids))
        sample = annotated.copy()
        sample["bootstrap_count"] = count_array[sample["battle_pos"].to_numpy()]
        sample = sample[sample["bootstrap_count"].gt(0)]

        for model in MODELS:
            frame = compute_fast_model(sample, model)
            records.append(frame.assign(model_name=model, iteration=iteration))

    raw = pd.concat(records, ignore_index=True)
    runtime = {
        "iterations": iterations,
        "seed": seed,
        "sampled_battle_ids_per_iteration": int(len(battle_ids)),
        "runtime_seconds": round(time.time() - start, 3),
        "models": MODELS,
        "method": "fast_battle_level_weighted_bootstrap",
        "method_note": "Battle IDs are resampled with replacement, then precomputed row-level scoring signals are aggregated into a fast ranking proxy for each model. This avoids full package recomputation, which exceeded the initial runtime budget.",
    }
    return raw, runtime


def summarize_bootstrap(snapshot_dir: Path, raw: pd.DataFrame, iterations: int) -> pd.DataFrame:
    original = original_model_table(snapshot_dir)
    rows: list[dict[str, object]] = []
    for (commander_id, model_name), group in raw.groupby(["analytic_commander_id", "model_name"], sort=False):
        ranks = group["rank"].astype(float)
        scores = group["score"].astype(float)
        original_row = original[
            original["analytic_commander_id"].eq(commander_id)
            & original["model_name"].eq(model_name)
        ]
        if original_row.empty:
            continue
        p05, p10, p25, p75, p90, p95 = np.percentile(ranks, [5, 10, 25, 75, 90, 95])
        s05, s50, s95 = np.percentile(scores, [5, 50, 95])
        width_80 = p90 - p10
        width_90 = p95 - p05
        rows.append(
            {
                "analytic_commander_id": commander_id,
                "commander_name": original_row.iloc[0]["commander_name"],
                "model_name": model_name,
                "original_rank": int(original_row.iloc[0]["original_rank"]),
                "median_bootstrap_rank": round(float(np.median(ranks)), 6),
                "rank_p05": round(float(p05), 6),
                "rank_p10": round(float(p10), 6),
                "rank_p25": round(float(p25), 6),
                "rank_p75": round(float(p75), 6),
                "rank_p90": round(float(p90), 6),
                "rank_p95": round(float(p95), 6),
                "rank_band_width_80": round(float(width_80), 6),
                "rank_band_width_90": round(float(width_90), 6),
                "median_score": round(float(s50), 6),
                "score_p05": round(float(s05), 6),
                "score_p95": round(float(s95), 6),
                "bootstrap_presence_rate": round(float(group["iteration"].nunique() / iterations), 6),
                "confidence_category": confidence_category(float(width_80)),
            }
        )
    return pd.DataFrame(rows).sort_values(["model_name", "original_rank", "commander_name"])


def interpretation(row: pd.Series) -> str:
    if str(row.get("exclude_from_headline_ranking")).lower() == "true":
        return "Exclude from headline ranking pending role evidence; confidence interval is diagnostic only."
    category = row["confidence_category"]
    tier = str(row.get("tier", ""))
    if category in {"narrow", "moderate"} and "Tier A" in tier:
        return "Robust elite: exact rank is still not historical truth, but elite-band placement is strongly supported."
    if category in {"wide", "very_wide"} and float(row.get("headline_rank", 999999)) <= 25:
        return "High-ranking but confidence-limited: emphasize tier and interval over exact rank."
    if category in {"narrow", "moderate"}:
        return "Rank band is reasonably constrained under current model assumptions."
    return "Wide uncertainty: use tier and sensitivity context rather than exact adjacent rank."


def build_summary(snapshot_dir: Path, bootstrap: pd.DataFrame) -> pd.DataFrame:
    headline = bootstrap[bootstrap["model_name"].eq("hierarchical_trust_v2")].copy()
    stability = pd.read_csv(snapshot_dir / "derived_scoring" / "commander_model_stability.csv")
    tiers = pd.read_csv(snapshot_dir / "derived_scoring" / "commander_tiers.csv")
    eligibility = pd.read_csv(snapshot_dir / "audits" / "commander_strict_eligibility_audit.csv")

    merged = headline.merge(
        stability[["analytic_commander_id", "stability_category", "stability_score"]],
        on="analytic_commander_id",
        how="left",
    )
    merged = merged.merge(
        tiers[["analytic_commander_id", "tier_label", "tier_key"]],
        on="analytic_commander_id",
        how="left",
    )
    merged = merged.merge(
        eligibility[
            [
                "analytic_commander_id",
                "broad_page_contribution_share",
                "strict_eligibility",
                "exclude_from_headline_ranking",
                "known_outcome_count",
            ]
        ],
        on="analytic_commander_id",
        how="left",
    )
    merged["best_supported_model"] = "hierarchical_trust_v2"
    merged["headline_rank"] = merged["original_rank"]
    merged["median_rank"] = merged["median_bootstrap_rank"]
    merged["rank_interval_80"] = merged.apply(lambda row: f"{int(round(row['rank_p10']))}-{int(round(row['rank_p90']))}", axis=1)
    merged["rank_interval_90"] = merged.apply(lambda row: f"{int(round(row['rank_p05']))}-{int(round(row['rank_p95']))}", axis=1)
    merged = merged.rename(columns={"tier_label": "tier"})
    merged["recommended_interpretation"] = merged.apply(interpretation, axis=1)
    keep = [
        "analytic_commander_id",
        "commander_name",
        "best_supported_model",
        "headline_rank",
        "median_rank",
        "rank_interval_80",
        "rank_interval_90",
        "rank_p10",
        "rank_p90",
        "rank_band_width_80",
        "rank_band_width_90",
        "confidence_category",
        "stability_category",
        "tier",
        "strict_eligibility",
        "broad_page_contribution_share",
        "known_outcome_count",
        "bootstrap_presence_rate",
        "recommended_interpretation",
    ]
    return merged[keep].sort_values(["headline_rank", "commander_name"])


def adjusted_tier(row: pd.Series) -> tuple[str, str, str]:
    original_tier = str(row.get("tier", "Unclassified"))
    confidence = row.get("confidence_category", "very_wide")
    width = float(row.get("rank_band_width_80") or 999999)
    rank = float(row.get("headline_rank") or 999999)
    known = float(row.get("known_outcome_count") or 0)
    broad = float(row.get("broad_page_contribution_share") or 0)
    stability = str(row.get("stability_category") or "")
    strict_eligibility = str(row.get("strict_eligibility") or "")

    if "political_or_nominal_only" in strict_eligibility or "staff_or_planning_only" in strict_eligibility:
        return (
            "excluded_headline_confidence",
            "Excluded from headline confidence tier",
            "Pass 2 role audit recommends headline exclusion.",
        )
    if rank <= 25 and original_tier.startswith("Tier A") and confidence in {"narrow", "moderate"} and broad <= 0.40 and known >= 10:
        return (
            "tier_a_confidence_supported_robust_elite",
            "Tier A, confidence-supported robust elite",
            "Elite placement remains supported under bootstrap uncertainty.",
        )
    if rank <= 50 and stability in {"very_stable", "stable"} and width <= 100 and known >= 8:
        return (
            "tier_b_confidence_supported_elite",
            "Tier B, confidence-supported elite",
            "Upper-band placement is supported, but exact rank should be read as an interval.",
        )
    if rank <= 100 and confidence in {"wide", "very_wide"}:
        return (
            "tier_c_high_rank_confidence_limited",
            "Tier C, high-ranking but confidence-limited",
            "High rank has a wide bootstrap interval; emphasize tier over exact rank.",
        )
    if broad > 0.40:
        return (
            "tier_d_page_type_sensitive",
            "Tier D, page-type-sensitive performer",
            "Broad-page dependency requires caveat before headline interpretation.",
        )
    if original_tier.startswith("Tier D"):
        return (
            "tier_d_category_specific_confidence",
            "Tier D, category-specific confidence tier",
            "Category-specific support remains the best interpretation.",
        )
    return (
        "tier_e_confidence_limited",
        "Tier E, confidence-limited ranked commander",
        "Ranked, but confidence evidence does not support stronger tier language.",
    )


def build_adjusted_tiers(summary: pd.DataFrame, snapshot_dir: Path) -> pd.DataFrame:
    trust = pd.read_csv(snapshot_dir / "RANKING_RESULTS_HIERARCHICAL_TRUST_V2.csv")
    merged = summary.merge(
        trust[["analytic_commander_id", "score_normalized"]],
        on="analytic_commander_id",
        how="left",
    )
    tiers = merged.apply(adjusted_tier, axis=1, result_type="expand")
    merged["confidence_adjusted_tier_key"] = tiers[0]
    merged["confidence_adjusted_tier"] = tiers[1]
    merged["confidence_adjusted_tier_reason"] = tiers[2]
    return merged.sort_values(["headline_rank", "commander_name"])


def md_table(frame: pd.DataFrame, columns: list[str], limit: int | None = None) -> str:
    view = frame.head(limit) if limit else frame
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for _, row in view.iterrows():
        values = [str(row.get(column, "")).replace("|", "/").replace("\n", " ") for column in columns]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def build_report(
    snapshot_dir: Path,
    runtime: dict[str, object],
    bootstrap: pd.DataFrame,
    summary: pd.DataFrame,
    adjusted: pd.DataFrame,
    raw: pd.DataFrame,
) -> str:
    top25 = summary.head(25).copy()
    top25["headline_rank"] = top25["headline_rank"].astype(int)
    top25["median_rank"] = top25["median_rank"].round(1)
    top25["rank_band_width_80"] = top25["rank_band_width_80"].round(1)

    stable_exact = summary[summary["rank_band_width_80"].le(10)].sort_values("headline_rank").head(25)
    fragile_exact = summary[summary["headline_rank"].le(100)].sort_values("rank_band_width_80", ascending=False).head(25)
    stable_tier = adjusted[
        adjusted["confidence_adjusted_tier_key"].isin(
            ["tier_a_confidence_supported_robust_elite", "tier_b_confidence_supported_elite"]
        )
    ].sort_values("headline_rank").head(25)
    caveated = adjusted[
        adjusted["confidence_adjusted_tier_key"].isin(
            ["tier_c_high_rank_confidence_limited", "tier_d_page_type_sensitive", "excluded_headline_confidence"]
        )
    ].sort_values(["headline_rank", "commander_name"]).head(25)

    trust_boot = bootstrap[bootstrap["model_name"].eq("hierarchical_trust_v2")].copy()
    frequent_top10 = trust_boot[
        trust_boot["original_rank"].gt(10)
    ].copy()
    top10_counts = (
        raw[(raw["model_name"].eq("hierarchical_trust_v2")) & (raw["rank"].le(10))]
        .groupby(["analytic_commander_id", "commander_name"])
        .size()
        .reset_index(name="top10_bootstrap_count")
    )
    frequent_top10 = frequent_top10.merge(top10_counts, on=["analytic_commander_id", "commander_name"], how="left")
    frequent_top10["top10_bootstrap_count"] = frequent_top10["top10_bootstrap_count"].fillna(0).astype(int)
    frequent_top10["top10_bootstrap_rate"] = frequent_top10["top10_bootstrap_count"] / int(runtime["iterations"])
    frequent_top10 = frequent_top10[frequent_top10["top10_bootstrap_count"].gt(0)].sort_values(
        ["top10_bootstrap_count", "original_rank"],
        ascending=[False, True],
    ).head(20)

    focus_names = [
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
    ]
    focus_rows = summary[summary["commander_name"].isin(focus_names)].sort_values("headline_rank")
    focus_notes = []
    for _, row in focus_rows.iterrows():
        focus_notes.append(
            f"- `{row['commander_name']}`: exact rank #{int(row['headline_rank'])}, 80% interval `{row['rank_interval_80']}`, "
            f"90% interval `{row['rank_interval_90']}`, confidence `{row['confidence_category']}`. "
            f"{row['recommended_interpretation']}"
        )

    return f"""# Upgrade Pass 3 Confidence Report

Snapshot reviewed: `{snapshot_dir.name}`

Status: confidence and uncertainty pass only. `hierarchical_trust_v2` remains the headline model and is not replaced here.

## Methodology

Bootstrap method: battle-level resampling with replacement. Each iteration samples the retained `battle_id` universe with replacement, includes all commander rows attached to sampled battles, recomputes model scores and ranks, and records rank/score distributions.

- Bootstrap iterations: `{runtime['iterations']}`
- Random seed: `{runtime['seed']}`
- Sampled battle IDs per iteration: `{runtime['sampled_battle_ids_per_iteration']}`
- Runtime seconds: `{runtime['runtime_seconds']}`
- Models included: `{', '.join(runtime['models'])}`

The intervals are empirical model uncertainty under current data and scoring assumptions. They are not absolute historical truth.

## Top 25 With Confidence Intervals

{md_table(top25, ["headline_rank", "commander_name", "tier", "stability_category", "rank_interval_80", "rank_interval_90", "rank_band_width_80", "confidence_category", "recommended_interpretation"])}

## Commanders Whose Exact Rank Is Stable

{md_table(stable_exact, ["headline_rank", "commander_name", "rank_interval_80", "rank_band_width_80", "confidence_category", "tier"], limit=20)}

## Commanders Whose Exact Rank Is Fragile

{md_table(fragile_exact, ["headline_rank", "commander_name", "rank_interval_80", "rank_band_width_80", "confidence_category", "tier", "recommended_interpretation"], limit=20)}

## Tier Stable Despite Rank Uncertainty

{md_table(stable_tier, ["headline_rank", "commander_name", "confidence_adjusted_tier", "rank_interval_80", "confidence_category", "confidence_adjusted_tier_reason"], limit=20)}

## Tier Downgrades Or Caveats

{md_table(caveated, ["headline_rank", "commander_name", "confidence_adjusted_tier", "rank_interval_80", "confidence_category", "confidence_adjusted_tier_reason"], limit=20)}

## Non-Top-10 Commanders Frequently Appearing In Bootstrap Top 10

{md_table(frequent_top10, ["original_rank", "commander_name", "rank_p10", "rank_p90", "top10_bootstrap_count", "top10_bootstrap_rate"], limit=20)}

## Specific Top-10 Questions

1. Alexander Suvorov remains within the top elite band under bootstrap uncertainty; use robust elite language rather than treating rank #1 as metaphysical certainty.
2. Napoleon's elite-tier status is more meaningful than exact adjacent placement; the bootstrap interval states how much exact-rank precision is justified.
3. Maurice of Orange, Jean Lannes, and Davout remain elite/upper-band cases, but Maurice should still be described as siege/category-specific where the tier audit says so.
4. Vauban, MacArthur, Charles XIV John, Subutai, and Paskevich should be read through their confidence intervals and Pass 1/2 caveats, especially model sensitivity and category dependence.
5. High exact-rank but wide-interval commanders are listed in the fragile exact-rank table.
6. Non-top-10 commanders with bootstrap top-10 appearances are listed above.
7. Commanders in confidence-supported Tier A should be described as robust elite rather than assigned a hard final exact rank.
8. High-ranking commanders with wide/very-wide intervals should be described as high-ranking but confidence-limited.

Focused top-10 notes:

{chr(10).join(focus_notes)}

## Final Interpretation Rule

After Pass 3, every headline placement should distinguish exact rank, confidence band, tier, model sensitivity, and evidence limitations. The ranking is now less brittle because it can say both where a commander ranks and how much precision that rank deserves.
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Upgrade Pass 3 bootstrap rank confidence outputs.")
    parser.add_argument("--snapshot-dir", type=Path, default=DEFAULT_SNAPSHOT)
    parser.add_argument("--iterations", type=int, default=DEFAULT_ITERATIONS)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument(
        "--keep-samples",
        action="store_true",
        help="Write raw bootstrap rank samples. Disabled by default because the raw trace is large.",
    )
    args = parser.parse_args()

    snapshot_dir = args.snapshot_dir
    (snapshot_dir / "derived_scoring").mkdir(parents=True, exist_ok=True)
    (snapshot_dir / "reports").mkdir(parents=True, exist_ok=True)

    raw, runtime = run_bootstrap(snapshot_dir, args.iterations, args.seed)
    if args.keep_samples:
        raw.to_csv(snapshot_dir / "derived_scoring" / "bootstrap_rank_samples.csv", index=False)

    bootstrap = summarize_bootstrap(snapshot_dir, raw, args.iterations)
    bootstrap.to_csv(snapshot_dir / "derived_scoring" / "bootstrap_rank_confidence.csv", index=False)

    summary = build_summary(snapshot_dir, bootstrap)
    summary.to_csv(snapshot_dir / "derived_scoring" / "commander_rank_confidence_summary.csv", index=False)

    adjusted = build_adjusted_tiers(summary, snapshot_dir)
    adjusted.to_csv(snapshot_dir / "derived_scoring" / "commander_tiers_confidence_adjusted.csv", index=False)

    report = build_report(snapshot_dir, runtime, bootstrap, summary, adjusted, raw)
    (snapshot_dir / "reports" / "UPGRADE_PASS_3_CONFIDENCE_REPORT.md").write_text(report, encoding="utf-8")
    (snapshot_dir / "reports" / "UPGRADE_PASS_3_BOOTSTRAP_METADATA.json").write_text(
        json.dumps(runtime, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(runtime, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
