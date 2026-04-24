from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


DEFAULT_SNAPSHOT = Path("outputs_improved_2026-04-24_ranking_model_upgrade")

ACTIVE_MODELS = [
    "hierarchical_trust_v2",
    "hierarchical_weighted",
    "baseline_conservative",
    "battle_only_baseline",
    "hierarchical_equal_split",
    "hierarchical_broader_eligibility",
    "hierarchical_full_credit",
]
TRUSTED_MODELS = [model for model in ACTIVE_MODELS if model != "hierarchical_full_credit"]


def numeric_series(values: list[float]) -> pd.Series:
    return pd.Series(values, dtype="float64").dropna()


def categorize_stability(score: float) -> str:
    if score >= 82:
        return "very_stable"
    if score >= 68:
        return "stable"
    if score >= 52:
        return "moderately_stable"
    if score >= 35:
        return "model_sensitive"
    return "highly_model_sensitive"


def compute_stability(snapshot_dir: Path) -> pd.DataFrame:
    sensitivity_path = snapshot_dir / "RANKING_RESULTS_SENSITIVITY.csv"
    sensitivity = pd.read_csv(sensitivity_path)

    rank_columns = [f"rank_{model}" for model in ACTIVE_MODELS]
    score_columns = [f"score_{model}" for model in ACTIVE_MODELS]
    for column in rank_columns + score_columns:
        if column in sensitivity.columns:
            sensitivity[column] = pd.to_numeric(sensitivity[column], errors="coerce")

    rows: list[dict[str, object]] = []
    for _, row in sensitivity.iterrows():
        trusted_ranks = numeric_series(
            [row.get(f"rank_{model}") for model in TRUSTED_MODELS if f"rank_{model}" in sensitivity.columns]
        )
        active_ranks = numeric_series(
            [row.get(f"rank_{model}") for model in ACTIVE_MODELS if f"rank_{model}" in sensitivity.columns]
        )
        active_scores = numeric_series(
            [row.get(f"score_{model}") for model in ACTIVE_MODELS if f"score_{model}" in sensitivity.columns]
        )
        diagnostic_full_credit_rank = row.get("rank_hierarchical_full_credit")

        rank_basis = trusted_ranks if not trusted_ranks.empty else active_ranks
        if rank_basis.empty:
            continue

        models_present_count = int(active_ranks.count())
        trusted_models_present_count = int(trusted_ranks.count())
        best_rank = float(rank_basis.min())
        worst_rank = float(rank_basis.max())
        median_rank = float(rank_basis.median())
        mean_rank = float(rank_basis.mean())
        rank_stddev = float(rank_basis.std(ddof=0)) if len(rank_basis) > 1 else 0.0
        rank_q25 = float(rank_basis.quantile(0.25))
        rank_q75 = float(rank_basis.quantile(0.75))
        rank_iqr = rank_q75 - rank_q25

        top_10_count = int((trusted_ranks <= 10).sum())
        top_25_count = int((trusted_ranks <= 25).sum())
        top_50_count = int((trusted_ranks <= 50).sum())
        top_100_count = int((trusted_ranks <= 100).sum())
        trusted_denominator = max(len(TRUSTED_MODELS), 1)

        normalized_models_present_count = trusted_models_present_count / trusted_denominator
        top_band_consistency = (
            0.45 * (top_10_count / trusted_denominator)
            + 0.30 * (top_25_count / trusted_denominator)
            + 0.15 * (top_50_count / trusted_denominator)
            + 0.10 * (top_100_count / trusted_denominator)
        )
        inverse_normalized_rank_stddev = 1.0 / (1.0 + (rank_stddev / 50.0))
        inverse_normalized_rank_iqr = 1.0 / (1.0 + (rank_iqr / 50.0))
        stability_score = 100.0 * (
            0.40 * normalized_models_present_count
            + 0.25 * top_band_consistency
            + 0.20 * inverse_normalized_rank_stddev
            + 0.15 * inverse_normalized_rank_iqr
        )

        rows.append(
            {
                "analytic_commander_id": row["analytic_commander_id"],
                "commander_name": row["display_name"],
                "canonical_wikipedia_url": row.get("canonical_wikipedia_url", ""),
                "models_present_count": models_present_count,
                "trusted_models_present_count": trusted_models_present_count,
                "best_rank": round(best_rank, 6),
                "worst_rank": round(worst_rank, 6),
                "median_rank": round(median_rank, 6),
                "mean_rank": round(mean_rank, 6),
                "rank_stddev": round(rank_stddev, 6),
                "rank_iqr": round(rank_iqr, 6),
                "top_10_count": top_10_count,
                "top_25_count": top_25_count,
                "top_50_count": top_50_count,
                "top_100_count": top_100_count,
                "diagnostic_full_credit_rank": round(float(diagnostic_full_credit_rank), 6)
                if pd.notna(diagnostic_full_credit_rank)
                else "",
                "median_score_across_models": round(float(active_scores.median()), 6) if not active_scores.empty else "",
                "score_stddev_across_models": round(float(active_scores.std(ddof=0)), 6)
                if len(active_scores) > 1
                else 0.0,
                "normalized_models_present_count": round(normalized_models_present_count, 6),
                "normalized_top_band_consistency": round(top_band_consistency, 6),
                "inverse_normalized_rank_stddev": round(inverse_normalized_rank_stddev, 6),
                "inverse_normalized_rank_iqr": round(inverse_normalized_rank_iqr, 6),
                "stability_score": round(stability_score, 6),
                "stability_category": categorize_stability(stability_score),
            }
        )

    output = pd.DataFrame(rows).sort_values(
        ["best_rank", "median_rank", "commander_name"],
        ascending=[True, True, True],
    )
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Compute cross-model commander stability metadata.")
    parser.add_argument("--snapshot-dir", type=Path, default=DEFAULT_SNAPSHOT)
    args = parser.parse_args()

    output = compute_stability(args.snapshot_dir)
    target = args.snapshot_dir / "derived_scoring" / "commander_model_stability.csv"
    target.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(target, index=False)
    print(f"Wrote {len(output)} rows to {target}")


if __name__ == "__main__":
    main()
