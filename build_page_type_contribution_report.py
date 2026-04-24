from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


DEFAULT_SNAPSHOT = Path("outputs_improved_2026-04-24_ranking_model_upgrade")

BALANCED_OUTCOME_SCORE = {
    "decisive_victory": 1.00,
    "victory": 0.80,
    "tactical_victory": 0.65,
    "pyrrhic_victory": 0.25,
    "indecisive": 0.00,
    "draw": 0.00,
    "stalemate": -0.05,
    "disputed": -0.10,
    "defeat": -0.80,
    "major_defeat": -1.00,
    "unknown": 0.00,
}


def build_report(snapshot_dir: Path) -> pd.DataFrame:
    annotated = pd.read_csv(snapshot_dir / "derived_scoring" / "commander_engagements_annotated.csv")
    for column in [
        "eligible_strict",
        "known_outcome_flag",
        "outcome_credit_fraction",
        "page_weight_model_b",
    ]:
        annotated[column] = pd.to_numeric(annotated[column], errors="coerce").fillna(0.0)

    annotated = annotated[annotated["eligible_strict"].eq(1)].copy()
    annotated["balanced_outcome_score"] = (
        annotated["outcome_category"].map(BALANCED_OUTCOME_SCORE).fillna(0.0)
    )
    annotated["raw_score_contribution"] = (
        annotated["outcome_credit_fraction"] * annotated["balanced_outcome_score"]
    )
    annotated["weighted_score_contribution"] = (
        annotated["raw_score_contribution"] * annotated["page_weight_model_b"]
    )
    annotated["weighted_presence"] = annotated["page_weight_model_b"]

    grouped = (
        annotated.groupby(["analytic_commander_id", "display_name", "page_type"], dropna=False)
        .agg(
            raw_score_contribution=("raw_score_contribution", "sum"),
            weighted_score_contribution=("weighted_score_contribution", "sum"),
            absolute_weighted_score_contribution=(
                "weighted_score_contribution",
                lambda values: values.abs().sum(),
            ),
            weighted_presence=("weighted_presence", "sum"),
            known_outcome_rows=("known_outcome_flag", "sum"),
            engagement_rows=("battle_id", "count"),
        )
        .reset_index()
    )

    unknown_counts = (
        annotated[annotated["outcome_category"].eq("unknown")]
        .groupby(["analytic_commander_id", "page_type"], dropna=False)
        .size()
        .rename("unknown_outcome_rows")
        .reset_index()
    )
    grouped = grouped.merge(
        unknown_counts,
        on=["analytic_commander_id", "page_type"],
        how="left",
    )
    grouped["unknown_outcome_rows"] = grouped["unknown_outcome_rows"].fillna(0).astype(int)

    totals = (
        grouped.groupby("analytic_commander_id")["absolute_weighted_score_contribution"]
        .sum()
        .rename("total_absolute_weighted_score_contribution")
        .reset_index()
    )
    grouped = grouped.merge(totals, on="analytic_commander_id", how="left")
    grouped["share_of_total_score"] = grouped.apply(
        lambda row: (
            row["absolute_weighted_score_contribution"]
            / row["total_absolute_weighted_score_contribution"]
        )
        if row["total_absolute_weighted_score_contribution"]
        else 0.0,
        axis=1,
    )

    numeric_columns = [
        "raw_score_contribution",
        "weighted_score_contribution",
        "absolute_weighted_score_contribution",
        "weighted_presence",
        "known_outcome_rows",
        "share_of_total_score",
    ]
    for column in numeric_columns:
        grouped[column] = pd.to_numeric(grouped[column], errors="coerce").fillna(0.0).round(6)

    grouped["known_outcome_rows"] = grouped["known_outcome_rows"].astype(int)
    grouped["engagement_rows"] = grouped["engagement_rows"].astype(int)
    return grouped.sort_values(
        ["analytic_commander_id", "share_of_total_score", "page_type"],
        ascending=[True, False, True],
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Build page-type score contribution diagnostics.")
    parser.add_argument("--snapshot-dir", type=Path, default=DEFAULT_SNAPSHOT)
    args = parser.parse_args()

    output = build_report(args.snapshot_dir)
    target = args.snapshot_dir / "derived_scoring" / "page_type_score_contributions.csv"
    target.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(target, index=False)
    print(f"Wrote {len(output)} rows to {target}")


if __name__ == "__main__":
    main()
