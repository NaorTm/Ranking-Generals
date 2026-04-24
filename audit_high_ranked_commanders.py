from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


DEFAULT_SNAPSHOT = Path("outputs_improved_2026-04-24_ranking_model_upgrade")
HIGH_LEVEL_PAGE_TYPES = {"operation_article", "campaign_article", "war_conflict_article"}


def num(value: object, default: float = 0.0) -> float:
    value = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    if pd.isna(value):
        return default
    return float(value)


def bool_text(value: bool) -> str:
    return "true" if value else "false"


def add_flag(
    rows: list[dict[str, object]],
    commander: pd.Series,
    flag: str,
    flagged: bool,
    supporting_value: float,
    explanation: str,
) -> None:
    rows.append(
        {
            "analytic_commander_id": commander["analytic_commander_id"],
            "commander_name": commander["display_name"],
            "rank_hierarchical_trust_v2": commander.get("rank_hierarchical_trust_v2"),
            "flag": flag,
            "flagged": bool_text(flagged),
            "supporting_value": round(float(supporting_value), 6),
            "explanation": explanation,
        }
    )


def build_commander_rollups(snapshot_dir: Path) -> pd.DataFrame:
    sensitivity = pd.read_csv(snapshot_dir / "RANKING_RESULTS_SENSITIVITY.csv")
    stability = pd.read_csv(snapshot_dir / "derived_scoring" / "commander_model_stability.csv")
    features = pd.read_csv(snapshot_dir / "derived_scoring" / "commander_ranking_features.csv")
    page_contrib = pd.read_csv(snapshot_dir / "derived_scoring" / "page_type_score_contributions.csv")
    annotated = pd.read_csv(snapshot_dir / "derived_scoring" / "commander_engagements_annotated.csv")

    for column in [
        "rank_hierarchical_trust_v2",
        "rank_battle_only_baseline",
        "rank_range",
        "known_outcome_count",
        "known_outcome_share",
        "higher_level_share",
    ]:
        if column in sensitivity.columns:
            sensitivity[column] = pd.to_numeric(sensitivity[column], errors="coerce")

    page_contrib["share_of_total_score"] = pd.to_numeric(
        page_contrib["share_of_total_score"],
        errors="coerce",
    ).fillna(0.0)
    page_pivot = (
        page_contrib.pivot_table(
            index="analytic_commander_id",
            columns="page_type",
            values="share_of_total_score",
            aggfunc="sum",
            fill_value=0.0,
        )
        .reset_index()
        .rename_axis(None, axis=1)
    )
    page_pivot["high_level_score_share"] = sum(
        page_pivot[column] if column in page_pivot.columns else 0.0
        for column in HIGH_LEVEL_PAGE_TYPES
    )

    for column in [
        "eligible_strict",
        "same_side_known_outcome_count",
        "known_outcome_flag",
        "outcome_override_applied",
    ]:
        annotated[column] = pd.to_numeric(annotated[column], errors="coerce").fillna(0.0)

    strict = annotated[annotated["eligible_strict"].eq(1)].copy()
    strict["coalition_event"] = strict["same_side_known_outcome_count"].ge(4).astype(int)
    strict["split_sensitive_event"] = strict["same_side_known_outcome_count"].ge(3).astype(int)
    strict["siege_event"] = strict["battle_name"].fillna("").str.contains("siege", case=False, regex=False).astype(int)
    rollup = (
        strict.groupby("analytic_commander_id")
        .agg(
            strict_rows=("battle_id", "count"),
            coalition_rows=("coalition_event", "sum"),
            split_sensitive_rows=("split_sensitive_event", "sum"),
            siege_rows=("siege_event", "sum"),
            max_same_side_known_outcome_count=("same_side_known_outcome_count", "max"),
            outcome_override_rows=("outcome_override_applied", "sum"),
        )
        .reset_index()
    )
    for source, target in [
        ("coalition_rows", "coalition_row_share"),
        ("split_sensitive_rows", "split_sensitive_row_share"),
        ("siege_rows", "siege_row_share"),
        ("outcome_override_rows", "outcome_override_share"),
    ]:
        rollup[target] = rollup.apply(
            lambda row: row[source] / row["strict_rows"] if row["strict_rows"] else 0.0,
            axis=1,
        )

    merged = sensitivity.merge(stability, on="analytic_commander_id", how="left")
    merged = merged.merge(
        features[
            [
                "analytic_commander_id",
                "identity_reliability",
                "is_suspect_identity",
                "is_linked_identity",
                "eligible_battle_count_strict",
                "eligible_campaign_count_strict",
                "eligible_war_count_strict",
                "feature_quality_flags",
            ]
        ],
        on="analytic_commander_id",
        how="left",
    )
    merged = merged.merge(page_pivot, on="analytic_commander_id", how="left")
    merged = merged.merge(rollup, on="analytic_commander_id", how="left")
    return merged


def audit(snapshot_dir: Path, top_n: int) -> pd.DataFrame:
    commanders = build_commander_rollups(snapshot_dir)
    commanders["rank_hierarchical_trust_v2"] = pd.to_numeric(
        commanders["rank_hierarchical_trust_v2"],
        errors="coerce",
    )
    commanders = commanders[commanders["rank_hierarchical_trust_v2"].le(top_n)].copy()
    commanders = commanders.sort_values("rank_hierarchical_trust_v2")

    rows: list[dict[str, object]] = []
    role_file = snapshot_dir / "verification" / "verified_command_role_classification.csv"
    role_data_exists = role_file.exists()
    evidence_file = snapshot_dir / "derived_scoring" / "event_evidence_quality.csv"
    evidence_data_exists = evidence_file.exists()

    for _, commander in commanders.iterrows():
        rank = num(commander.get("rank_hierarchical_trust_v2"), 999999.0)
        known = num(commander.get("known_outcome_count"), 0.0)
        known_share = num(commander.get("known_outcome_share"), 0.0)
        high_level_share = num(commander.get("high_level_score_share"), num(commander.get("higher_level_share"), 0.0))
        battle_rank = num(commander.get("rank_battle_only_baseline"), 999999.0)
        rank_range = num(commander.get("rank_range"), num(commander.get("worst_rank"), 0.0) - num(commander.get("best_rank"), 0.0))
        coalition_share = num(commander.get("coalition_row_share"), 0.0)
        split_share = num(commander.get("split_sensitive_row_share"), 0.0)
        siege_share = num(commander.get("siege_row_share"), 0.0)
        campaign_share = num(commander.get("campaign_article"), 0.0)
        war_share = num(commander.get("war_conflict_article"), 0.0)
        override_share = num(commander.get("outcome_override_share"), 0.0)
        stability_category = str(commander.get("stability_category") or "")
        identity_reliability = str(commander.get("identity_reliability") or "")
        is_suspect_identity = num(commander.get("is_suspect_identity"), 0.0)
        battle_count = num(commander.get("eligible_battle_count_strict"), num(commander.get("battle_count"), 0.0))

        add_flag(
            rows,
            commander,
            "high_rank_low_known_rows",
            rank <= 100 and known < 8,
            known,
            f"Top-{top_n} commander has {known:.0f} known-outcome rows; low evidence volume weakens exact-rank confidence.",
        )
        add_flag(
            rows,
            commander,
            "high_rank_many_high_level_pages",
            high_level_share > 0.40,
            high_level_share,
            "More than 40 percent of measured contribution comes from operation, campaign, or war-level pages.",
        )
        add_flag(
            rows,
            commander,
            "high_rank_low_battle_only_score",
            rank <= 50 and battle_rank > 100,
            battle_rank,
            "Trust-first placement is much stronger than the battle-only baseline, suggesting dependence on non-battle evidence.",
        )
        add_flag(
            rows,
            commander,
            "large_model_rank_variance",
            rank_range > 50 or stability_category in {"model_sensitive", "highly_model_sensitive"},
            rank_range,
            "Rank spread across sensitivity models is large enough that adjacent exact rank should not be over-read.",
        )
        add_flag(
            rows,
            commander,
            "coalition_credit_heavy",
            coalition_share > 0.30,
            coalition_share,
            "Large share of strict rows involve four or more known same-side commanders, increasing coalition credit sensitivity.",
        )
        add_flag(
            rows,
            commander,
            "nominal_leader_risk",
            (not role_data_exists) and high_level_share > 0.45 and battle_count < 5,
            high_level_share,
            "Role classification is not yet available and the case is broad-page heavy with limited battle-level evidence.",
        )
        add_flag(
            rows,
            commander,
            "unclear_role_heavy",
            False,
            0.0,
            "Verified role classification file is not present in this snapshot, so unclear-role heaviness is not assessed in this audit pass.",
        )
        add_flag(
            rows,
            commander,
            "siege_engineering_specialist",
            siege_share > 0.35 or "Vauban" in str(commander.get("display_name")),
            siege_share,
            "Substantial siege-event footprint; field-command rank should be interpreted alongside siege-engineering category strength.",
        )
        add_flag(
            rows,
            commander,
            "campaign_page_sensitive",
            campaign_share > 0.25,
            campaign_share,
            "Campaign-page contribution share is high enough to affect interpretation.",
        )
        add_flag(
            rows,
            commander,
            "war_page_sensitive",
            war_share > 0.25,
            war_share,
            "War/conflict-page contribution share is high enough to affect interpretation.",
        )
        add_flag(
            rows,
            commander,
            "low_evidence_quality",
            (not evidence_data_exists and (known < 8 or known_share < 0.60)),
            known_share,
            "Event-level evidence-quality scoring is not yet present; low known-outcome density is used as the provisional risk signal.",
        )
        add_flag(
            rows,
            commander,
            "region_or_era_source_density_risk",
            str(commander.get("primary_era_bucket") or "").lower() in {"ancient", "medieval"} and known < 10,
            known,
            "Ancient/medieval cases with low known-outcome count are more exposed to uneven source-density risk.",
        )
        add_flag(
            rows,
            commander,
            "identity_merge_risk",
            is_suspect_identity > 0 or identity_reliability not in {"high", "medium"},
            is_suspect_identity,
            "Identity bridge is suspect, low reliability, or not confidently linked.",
        )
        add_flag(
            rows,
            commander,
            "outcome_override_sensitive",
            override_share > 0.20,
            override_share,
            "Large share of strict rows used outcome overrides; score depends on verified corrections.",
        )
        add_flag(
            rows,
            commander,
            "split_credit_sensitive",
            split_share > 0.30,
            split_share,
            "Large share of rows involve multi-commander same-side credit splitting.",
        )

    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit high-ranked commanders for interpretation risks.")
    parser.add_argument("--snapshot-dir", type=Path, default=DEFAULT_SNAPSHOT)
    parser.add_argument("--top-n", type=int, default=100)
    args = parser.parse_args()

    output = audit(args.snapshot_dir, args.top_n)
    target = args.snapshot_dir / "audits" / "high_ranked_commander_flags.csv"
    target.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(target, index=False)
    print(f"Wrote {len(output)} rows to {target}")


if __name__ == "__main__":
    main()
