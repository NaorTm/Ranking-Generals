from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


DEFAULT_SNAPSHOT = Path("outputs_improved_2026-04-24_ranking_model_upgrade")


def num(value: object, default: float = 0.0) -> float:
    value = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    if pd.isna(value):
        return default
    return float(value)


def tier_for_row(row: pd.Series) -> tuple[str, str, int, str]:
    trust_rank = num(row.get("rank_hierarchical_trust_v2"), 999999.0)
    battle_rank = num(row.get("rank_battle_only_baseline"), 999999.0)
    stability_score = num(row.get("stability_score"), 0.0)
    known = num(row.get("known_outcome_count"), num(row.get("known_outcome_count_strict"), 0.0))
    known_share = num(row.get("known_outcome_share"), num(row.get("known_outcome_share_strict"), 0.0))
    higher_level_share = num(row.get("higher_level_share"), 0.0)
    battle_count = num(row.get("battle_count"), num(row.get("eligible_battle_count_strict"), 0.0))
    campaign_count = num(row.get("campaign_count"), num(row.get("eligible_campaign_count_strict"), 0.0))
    war_count = num(row.get("war_count"), num(row.get("eligible_war_count_strict"), 0.0))
    siege_event_share = num(row.get("siege_event_share"), 0.0)
    page_class = str(row.get("page_type_profile_class") or "")
    commander_name = str(row.get("display_name") or row.get("commander_name") or "")

    if siege_event_share >= 0.35 or "Vauban" in commander_name:
        return (
            "tier_d_strong_narrow_category",
            "Tier D, strong but narrow-category performer",
            4,
            "Strong record is concentrated in siege or engineering-style events, so it should be interpreted as category-specific rather than generic field-command dominance.",
        )

    if (
        trust_rank <= 25
        and stability_score >= 68
        and known >= 10
        and known_share >= 0.60
        and higher_level_share <= 0.35
    ):
        return (
            "tier_a_robust_elite",
            "Tier A, robust elite",
            1,
            "High trust-first rank, strong cross-model stability, substantial known-outcome evidence, and limited high-level page dependence.",
        )

    if trust_rank <= 50 and stability_score >= 52:
        return (
            "tier_b_elite_model_sensitive",
            "Tier B, elite but model-sensitive",
            2,
            "High trust-first rank with meaningful support, but exact placement is sensitive to model assumptions or evidence mix.",
        )

    if trust_rank <= 100 and (known >= 5 or known_share >= 0.50):
        return (
            "tier_c_high_performer_evidence_caveats",
            "Tier C, high performer with evidence caveats",
            3,
            "Top-100 trust-first placement, but the case needs caveats around evidence volume, model stability, or page-type dependence.",
        )

    if battle_rank <= 100 and (battle_count >= 5 or "battle" in page_class):
        return (
            "tier_d_strong_narrow_category",
            "Tier D, strong but narrow-category performer",
            4,
            "Stronger in a narrower battlefield-oriented view than in the full interpretive model.",
        )

    if trust_rank <= 150 or campaign_count + war_count > battle_count:
        return (
            "tier_e_historically_important_scoring_sensitive",
            "Tier E, historically important but scoring-sensitive",
            5,
            "Historically visible or ranked in the upper band, but interpretation is sensitive to broad pages, limited evidence, or model assumptions.",
        )

    return (
        "unclassified",
        "Unclassified",
        99,
        "Outside the currently interpreted tier bands.",
    )


def assign_tiers(snapshot_dir: Path) -> pd.DataFrame:
    sensitivity = pd.read_csv(snapshot_dir / "RANKING_RESULTS_SENSITIVITY.csv")
    stability = pd.read_csv(snapshot_dir / "derived_scoring" / "commander_model_stability.csv")
    features = pd.read_csv(snapshot_dir / "derived_scoring" / "commander_ranking_features.csv")
    annotated = pd.read_csv(snapshot_dir / "derived_scoring" / "commander_engagements_annotated.csv")

    annotated["eligible_strict"] = pd.to_numeric(annotated["eligible_strict"], errors="coerce").fillna(0)
    strict = annotated[annotated["eligible_strict"].eq(1)].copy()
    strict["siege_event"] = strict["battle_name"].fillna("").str.contains(
        "siege",
        case=False,
        regex=False,
    )
    siege_rollup = (
        strict.groupby("analytic_commander_id")
        .agg(strict_rows=("battle_id", "count"), siege_rows=("siege_event", "sum"))
        .reset_index()
    )
    siege_rollup["siege_event_share"] = siege_rollup.apply(
        lambda row: row["siege_rows"] / row["strict_rows"] if row["strict_rows"] else 0.0,
        axis=1,
    )

    merged = sensitivity.merge(
        stability[
            [
                "analytic_commander_id",
                "stability_score",
                "stability_category",
                "rank_stddev",
                "rank_iqr",
                "top_25_count",
                "top_50_count",
                "top_100_count",
            ]
        ],
        on="analytic_commander_id",
        how="left",
    )
    merged = merged.merge(
        features[
            [
                "analytic_commander_id",
                "known_outcome_count_strict",
                "known_outcome_share_strict",
                "eligible_battle_count_strict",
                "eligible_campaign_count_strict",
                "eligible_war_count_strict",
                "feature_quality_flags",
            ]
        ],
        on="analytic_commander_id",
        how="left",
    )
    merged = merged.merge(
        siege_rollup[["analytic_commander_id", "siege_event_share"]],
        on="analytic_commander_id",
        how="left",
    )

    rows: list[dict[str, object]] = []
    for _, row in merged.iterrows():
        tier_key, tier_label, tier_sort, tier_reason = tier_for_row(row)
        rows.append(
            {
                "analytic_commander_id": row["analytic_commander_id"],
                "commander_name": row["display_name"],
                "canonical_wikipedia_url": row.get("canonical_wikipedia_url", ""),
                "rank_hierarchical_trust_v2": row.get("rank_hierarchical_trust_v2"),
                "score_hierarchical_trust_v2": row.get("score_hierarchical_trust_v2"),
                "tier_key": tier_key,
                "tier_label": tier_label,
                "tier_sort": tier_sort,
                "tier_reason": tier_reason,
                "stability_score": row.get("stability_score"),
                "stability_category": row.get("stability_category"),
                "known_outcome_count": row.get("known_outcome_count"),
                "known_outcome_share": row.get("known_outcome_share"),
                "higher_level_share": row.get("higher_level_share"),
                "page_type_profile_class": row.get("page_type_profile_class"),
                "feature_quality_flags": row.get("feature_quality_flags"),
            }
        )

    output = pd.DataFrame(rows)
    output["rank_hierarchical_trust_v2"] = pd.to_numeric(
        output["rank_hierarchical_trust_v2"],
        errors="coerce",
    )
    return output.sort_values(["tier_sort", "rank_hierarchical_trust_v2", "commander_name"])


def main() -> None:
    parser = argparse.ArgumentParser(description="Assign interpretive commander tiers.")
    parser.add_argument("--snapshot-dir", type=Path, default=DEFAULT_SNAPSHOT)
    args = parser.parse_args()

    output = assign_tiers(args.snapshot_dir)
    target = args.snapshot_dir / "derived_scoring" / "commander_tiers.csv"
    target.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(target, index=False)
    print(f"Wrote {len(output)} rows to {target}")


if __name__ == "__main__":
    main()
