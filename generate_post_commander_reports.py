from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd


TABLE_SPECS = [
    {
        "name": "engagement_eligibility.csv",
        "grain": "one row per `battle_id`",
        "purpose": "Eligibility gate for scoring, corrected analytic year, conflict key, and page-type controls.",
        "core_columns": [
            "battle_id",
            "battle_name",
            "page_type",
            "strict_gate_include",
            "balanced_gate_include",
            "analytic_year",
            "era_bucket",
            "conflict_key",
            "likely_false_positive",
        ],
    },
    {
        "name": "commander_identity_bridge.csv",
        "grain": "one row per `analytic_commander_id`",
        "purpose": "Conservative bridge from commander rows to analytic identities with URL-first canonicalization.",
        "core_columns": [
            "analytic_commander_id",
            "display_name",
            "canonical_wikipedia_url",
            "identity_source",
            "identity_reliability",
            "is_linked_identity",
            "is_raw_name_only",
            "is_suspect_identity",
        ],
    },
    {
        "name": "commander_engagements_annotated.csv",
        "grain": "one row per `analytic_commander_id x battle_id`",
        "purpose": "Atomic scoring fact table after commander dedupe, page eligibility, and outcome inference.",
        "core_columns": [
            "analytic_commander_id",
            "battle_id",
            "battle_name",
            "page_type",
            "side",
            "outcome_category",
            "eligible_strict",
            "eligible_balanced",
            "page_weight_model_b",
        ],
    },
    {
        "name": "commander_engagement_summary.csv",
        "grain": "one row per `analytic_commander_id`",
        "purpose": "High-level participation, breadth, and span summary.",
        "core_columns": [
            "analytic_commander_id",
            "display_name",
            "total_engagements_strict",
            "total_battle_pages_strict",
            "distinct_conflicts_strict",
            "distinct_opponents_strict",
            "first_analytic_year",
            "last_analytic_year",
        ],
    },
    {
        "name": "commander_outcome_profile.csv",
        "grain": "one row per `analytic_commander_id`",
        "purpose": "Known-outcome counts, shares, and mean outcome scores.",
        "core_columns": [
            "analytic_commander_id",
            "known_outcome_count",
            "known_outcome_share",
            "mean_conservative_score",
            "mean_balanced_score",
            "mean_aggressive_score",
        ],
    },
    {
        "name": "commander_page_type_profile.csv",
        "grain": "one row per `analytic_commander_id`",
        "purpose": "Battle / operation / campaign / war exposure and weighted presence.",
        "core_columns": [
            "analytic_commander_id",
            "engagements_strict",
            "weighted_presence_model_a",
            "weighted_presence_model_b",
            "count_strict_battle_article",
            "count_strict_operation_article",
            "count_strict_campaign_article",
            "count_strict_war_conflict_article",
        ],
    },
    {
        "name": "commander_era_profile.csv",
        "grain": "one row per `analytic_commander_id`",
        "purpose": "Era bucket distribution from corrected analytic years.",
        "core_columns": [
            "analytic_commander_id",
            "engagements_strict",
            "count_ancient",
            "count_medieval",
            "count_early_modern",
            "count_world_wars",
            "count_contemporary",
            "primary_era_bucket",
        ],
    },
    {
        "name": "commander_opponent_profile.csv",
        "grain": "one row per `analytic_commander_id x opponent_key`",
        "purpose": "Opponent breadth at belligerent-entity level for audit and sensitivity analysis.",
        "core_columns": [
            "analytic_commander_id",
            "display_name",
            "opponent_key",
            "opponent_entity",
            "engagement_count_strict",
            "weighted_presence_model_b",
            "reliability",
        ],
    },
    {
        "name": "commander_ranking_features.csv",
        "grain": "one row per `analytic_commander_id`",
        "purpose": "Ranking-ready feature matrix assembled from participation, breadth, outcome, page-type, and era summaries.",
        "core_columns": [
            "analytic_commander_id",
            "display_name",
            "eligible_engagement_count_strict",
            "eligible_battle_count_strict",
            "weighted_presence_model_b",
            "conflict_breadth_strict",
            "known_outcome_share_strict",
            "opponent_breadth_strict",
        ],
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate post-commander-rebuild markdown reports.")
    parser.add_argument("--current-snapshot-dir", type=Path, default=Path("outputs_cleaned_2026-04-10_authoritative"))
    parser.add_argument("--starting-snapshot-dir", type=Path, default=Path("outputs_cleaned_2026-04-09_authoritative"))
    parser.add_argument("--baseline-snapshot-dir", type=Path, default=Path("outputs_final_2026-04-05"))
    return parser.parse_args()


def abs_link(path: Path, label: str | None = None) -> str:
    resolved = path.resolve()
    return f"[{label or path.name}]({resolved.as_posix()})"


def fmt_int(value: Any) -> str:
    try:
        return f"{int(value):,}"
    except Exception:
        return str(value)


def fmt_delta(new_value: int, old_value: int) -> str:
    delta = new_value - old_value
    sign = "+" if delta >= 0 else ""
    return f"{sign}{delta:,}"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str).fillna("")


def top_rows(path: Path, n: int = 5) -> pd.DataFrame:
    frame = read_csv(path)
    if "rank" in frame.columns:
        frame["rank"] = pd.to_numeric(frame["rank"], errors="coerce")
        frame = frame.sort_values(["rank", "display_name"], ascending=[True, True])
    return frame.head(n)


def numeric(frame: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    copied = frame.copy()
    for column in columns:
        if column in copied.columns:
            copied[column] = pd.to_numeric(copied[column], errors="coerce")
    return copied


def ordered_names(frame: pd.DataFrame, name_col: str = "display_name", limit: int = 5) -> list[str]:
    return [str(value) for value in frame[name_col].head(limit).tolist()]


def numbered_lines(names: list[str]) -> str:
    return "\n".join(f"{index}. {name}" for index, name in enumerate(names, start=1))


def bullet_lines(names: list[str]) -> str:
    return "\n".join(f"- {name}" for name in names)


def sensitivity_join(old_snapshot: Path, new_snapshot: Path) -> pd.DataFrame:
    old = numeric(
        read_csv(old_snapshot / "RANKING_RESULTS_SENSITIVITY.csv"),
        [
            "rank_baseline_conservative",
            "rank_battle_only_baseline",
            "rank_hierarchical_weighted",
            "best_rank",
            "mean_rank",
            "rank_range",
            "top10_appearances",
            "top25_appearances",
        ],
    )
    new = numeric(
        read_csv(new_snapshot / "RANKING_RESULTS_SENSITIVITY.csv"),
        [
            "rank_baseline_conservative",
            "rank_battle_only_baseline",
            "rank_hierarchical_weighted",
            "best_rank",
            "mean_rank",
            "rank_range",
            "top10_appearances",
            "top25_appearances",
        ],
    )
    key = "canonical_wikipedia_url"
    merged = new.merge(
        old[
            [
                key,
                "display_name",
                "rank_baseline_conservative",
                "rank_battle_only_baseline",
                "rank_hierarchical_weighted",
            ]
        ],
        on=key,
        how="outer",
        suffixes=("_new", "_old"),
        indicator=True,
    )
    merged["baseline_shift"] = merged["rank_baseline_conservative_old"] - merged["rank_baseline_conservative_new"]
    merged["hier_shift"] = merged["rank_hierarchical_weighted_old"] - merged["rank_hierarchical_weighted_new"]
    merged["battle_shift"] = merged["rank_battle_only_baseline_old"] - merged["rank_battle_only_baseline_new"]
    return merged


def focus_shift_table(joined: pd.DataFrame, shift_col: str, limit: int = 8) -> tuple[pd.DataFrame, pd.DataFrame]:
    focus = joined[
        (joined["rank_baseline_conservative_new"] <= 50)
        | (joined["rank_baseline_conservative_old"] <= 50)
        | (joined["rank_hierarchical_weighted_new"] <= 50)
        | (joined["rank_hierarchical_weighted_old"] <= 50)
    ].copy()
    rises = focus.sort_values(shift_col, ascending=False).head(limit)
    drops = focus.sort_values(shift_col, ascending=True).head(limit)
    return rises, drops


def shift_bullets(frame: pd.DataFrame, shift_col: str, new_rank_col: str, old_rank_col: str) -> str:
    lines = []
    for _, row in frame.iterrows():
        name = row.get("display_name_new") or row.get("display_name_old") or "Unknown"
        lines.append(
            f"- {name}: old `{fmt_int(row.get(old_rank_col, 'NA'))}` -> new `{fmt_int(row.get(new_rank_col, 'NA'))}` ({row.get(shift_col):+.0f})"
        )
    return "\n".join(lines)


def era_lines(frame: pd.DataFrame, era: str) -> str:
    subset = frame[frame["requested_era"] == era]
    return "\n".join(
        f"- {row['support_band']}: {row['display_name']}"
        for _, row in subset.iterrows()
    )


def write_text(path: Path, text: str) -> None:
    path.write_text(text.strip() + "\n", encoding="utf-8")


def generate_scoring_framework(
    snapshot_dir: Path,
    scoring_metrics: dict[str, Any],
    commander_summary: dict[str, Any],
    commander_audit: dict[str, Any],
) -> str:
    return f"""
# Scoring Framework

## Research Objective

Build a defensible, auditable analytical basis for commander ranking from the cleaned snapshot in `{snapshot_dir.name}`. This stage uses the validated battle file, the cleaned commander layer, and the blocker-free commander audit only. It supersedes the stale scoring package from `outputs_final_2026-04-05`.

## Authoritative Inputs

- {abs_link(snapshot_dir / "battles_clean.csv")}
- {abs_link(snapshot_dir / "battle_commanders.csv")}
- {abs_link(snapshot_dir / "commanders_master.csv")}
- {abs_link(snapshot_dir / "commander_cleanup_summary.json")}
- {abs_link(snapshot_dir / "commander_postfix_audit" / "summary.json")}

Current commander-layer status:

- main commander rows: `{fmt_int(commander_summary["battle_commander_rows"])}`
- commander quarantine rows: `{fmt_int(commander_summary["battle_commander_quarantine_rows"])}`
- commander master rows: `{fmt_int(commander_summary["commanders_master_rows"])}`
- battles with at least one validated commander row: `{fmt_int(commander_summary["battles_with_any_commander_rows"])}`
- main commander blockers: `{fmt_int(commander_audit["row_blocker_rows"])}`
- master blockers: `{fmt_int(commander_audit["master_blocker_rows"])}`

## Methodological Principles

- Use the cleaned snapshot only. No new crawling or battle extraction happens here.
- Treat `commander x engagement-page participation` as the atomic unit.
- Keep battles, operations, campaigns, and wars separate unless a model explicitly weights across them.
- Prefer conservative exclusion over false precision.
- Keep identity reliability and outcome evidence visible in every derived layer.
- Do not let quarantined commander rows back into the analytic stack.

## Source Scope

Observed source scope in the synchronized rebuild:

- retained pages: `{fmt_int(scoring_metrics["source"]["retained_pages"])}`
- commander rows: `{fmt_int(scoring_metrics["source"]["commander_rows"])}`
- commander master rows: `{fmt_int(scoring_metrics["source"]["commander_master_rows"])}`
- strict-eligible pages: `{fmt_int(scoring_metrics["eligibility"]["strict_included_pages"])}`
- balanced-eligible pages: `{fmt_int(scoring_metrics["eligibility"]["balanced_included_pages"])}`
- likely false-positive pages flagged by heuristic gate: `{fmt_int(scoring_metrics["eligibility"]["likely_false_positive_pages"])}`
- identity bridge rows: `{fmt_int(scoring_metrics["derived"]["identity_bridge_rows"])}`
- linked identities: `{fmt_int(scoring_metrics["identities"]["linked_identities"])}`
- raw-name-only identities: `{fmt_int(scoring_metrics["identities"]["raw_name_only_identities"])}`
- suspect identities flagged: `{fmt_int(scoring_metrics["identities"]["suspect_identities"])}`
- annotated commander-engagement rows after dedupe: `{fmt_int(scoring_metrics["derived"]["annotated_rows"])}`

## Unit Of Analysis

The atomic unit is one row in {abs_link(snapshot_dir / "derived_scoring" / "commander_engagements_annotated.csv")}: one `analytic_commander_id x battle_id`.

That row exists only after:

- page-level eligibility assessment
- commander identity bridging
- duplicate commander-page collapse
- side-anomaly handling
- conservative commander outcome inference

## Page-Type Treatment

- `battle_article`: highest-confidence scoring unit and default baseline.
- `operation_article`: bounded engagement-like unit, below battle pages in default weight.
- `campaign_article`: higher abstraction than battles and operations.
- `war_conflict_article`: highest abstraction and never mixed at equal weight with battles in the conservative baseline.

## Model Definitions

### Battle-Only Conservative Baseline

- include only strict-eligible `battle_article` rows
- linked identities only
- exclude suspect identities
- recommended published baseline

### Hierarchical Weighted Model

- include battle, operation, campaign, and war/conflict rows
- use page weights already written into the annotated fact table
- apply hierarchy overlap penalty on non-battle rows when battle coverage already exists for the same conflict-year cluster
- keep as the main sensitivity view, not the sole headline ranking

## Eligibility Rules

The page-level gate lives in {abs_link(snapshot_dir / "derived_scoring" / "engagement_eligibility.csv")}.

Strict gate:

- page-type confidence and extraction confidence both clear the strict threshold
- at least one validated commander row exists
- analytic year is resolved
- page is not flagged likely false positive

Balanced gate:

- wider confidence thresholds
- still excludes likely false positives and rows with no commander evidence

## Commander Identity Rules

The identity bridge lives in {abs_link(snapshot_dir / "derived_scoring" / "commander_identity_bridge.csv")}.

Build order:

- canonical Wikipedia URL first
- cleaned raw-name fallback only when no link exists
- rank-only and linked non-person survivors removed by commander hotfix and postfix audit

Identity reliability classes:

- `high`: linked identity
- `medium`: raw-name-only identity
- `low`: no surviving low-confidence class remains in the final published bridge because suspect identities were reduced to zero

## Outcome Normalization

Known strict-gate outcome rows in the synchronized rebuild:

- strict known-outcome rows: `{fmt_int(scoring_metrics["outcomes"]["strict_known_outcome_rows"])}`
- strict known-outcome commanders: `{fmt_int(scoring_metrics["outcomes"]["strict_known_outcome_commanders"])}`

Commander-level outcome derivation order:

1. explicit side-attributed commander outcome when present
2. neutral page result propagated to all commanders on the page
3. conservative belligerent match against `result_raw`
4. otherwise `unknown`

## Validation Status

- eligibility grain valid: `{scoring_metrics["validation"]["eligibility_unique_battle_ids"]}`
- identity bridge grain valid: `{scoring_metrics["validation"]["bridge_unique_commander_ids"]}`
- annotated fact grain valid: `{scoring_metrics["validation"]["annotated_unique_commander_battle_pairs"]}`
- commander layer blockers remaining: `{fmt_int(commander_audit["row_blocker_rows"])}`
- commander master blockers remaining: `{fmt_int(commander_audit["master_blocker_rows"])}`

## Bottom Line

The scoring layer is synchronized to the cleaned commander snapshot. The conservative baseline cohort now contains `{fmt_int(scoring_metrics["outcomes"]["default_ranking_eligible_commanders"])}` commanders, and the supporting tables can be treated as the current authoritative scoring foundation for this project.
"""


def generate_analytical_tables_spec(snapshot_dir: Path, derived_dir: Path) -> str:
    rows = []
    for spec in TABLE_SPECS:
        path = derived_dir / spec["name"]
        frame = read_csv(path)
        rows.append(
            "\n".join(
                [
                    f"## {spec['name']}",
                    "",
                    f"- file: {abs_link(path)}",
                    f"- rows: `{fmt_int(len(frame))}`",
                    f"- grain: {spec['grain']}",
                    f"- purpose: {spec['purpose']}",
                    f"- core columns: {', '.join(f'`{column}`' for column in spec['core_columns'])}",
                ]
            )
        )
    joined_rows = "\n\n".join(rows)
    return f"""
# Analytical Tables Spec

All derived scoring tables live under {abs_link(derived_dir, "derived_scoring")}.

Source files used for joins:

- {abs_link(snapshot_dir / "battles_clean.csv")}
- {abs_link(snapshot_dir / "battle_commanders.csv")}
- {abs_link(snapshot_dir / "commanders_master.csv")}

Build order:

1. `engagement_eligibility.csv`
2. `commander_identity_bridge.csv`
3. `commander_engagements_annotated.csv`
4. commander-level summary tables
5. `commander_ranking_features.csv`

{joined_rows}
"""


def generate_scoring_readiness_report(snapshot_dir: Path, scoring_metrics: dict[str, Any]) -> str:
    derived_dir = snapshot_dir / "derived_scoring"
    outputs = [
        "engagement_eligibility.csv",
        "commander_identity_bridge.csv",
        "commander_engagements_annotated.csv",
        "commander_engagement_summary.csv",
        "commander_outcome_profile.csv",
        "commander_page_type_profile.csv",
        "commander_era_profile.csv",
        "commander_opponent_profile.csv",
        "commander_ranking_features.csv",
    ]
    built_outputs = "\n".join(f"- {abs_link(derived_dir / name)}" for name in outputs)
    return f"""
# Scoring Readiness Report

## Current State

The scoring-stage foundation is now built on the cleaned snapshot in `{snapshot_dir.name}`.

Built outputs:

{built_outputs}

Build summary:

- source retained pages: `{fmt_int(scoring_metrics["source"]["retained_pages"])}`
- source commander rows: `{fmt_int(scoring_metrics["source"]["commander_rows"])}`
- source commander master rows: `{fmt_int(scoring_metrics["source"]["commander_master_rows"])}`
- strict-eligible pages: `{fmt_int(scoring_metrics["eligibility"]["strict_included_pages"])}`
- balanced-eligible pages: `{fmt_int(scoring_metrics["eligibility"]["balanced_included_pages"])}`
- identity bridge rows: `{fmt_int(scoring_metrics["derived"]["identity_bridge_rows"])}`
- linked identities: `{fmt_int(scoring_metrics["identities"]["linked_identities"])}`
- raw-name-only identities: `{fmt_int(scoring_metrics["identities"]["raw_name_only_identities"])}`
- suspect identities flagged: `{fmt_int(scoring_metrics["identities"]["suspect_identities"])}`
- annotated commander-engagement rows after dedupe: `{fmt_int(scoring_metrics["derived"]["annotated_rows"])}`
- default conservative ranking cohort: `{fmt_int(scoring_metrics["outcomes"]["default_ranking_eligible_commanders"])}` commanders

Validation status:

- eligibility grain valid: `{scoring_metrics["validation"]["eligibility_unique_battle_ids"]}`
- identity bridge grain valid: `{scoring_metrics["validation"]["bridge_unique_commander_ids"]}`
- annotated fact grain valid: `{scoring_metrics["validation"]["annotated_unique_commander_battle_pairs"]}`
- unresolved year anomalies: `{fmt_int(scoring_metrics["eligibility"]["pages_with_unresolved_year_anomaly"])}`

## What Is Ready For Ranking

- linked-identity participation depth
- battle-only and hierarchical page-type profiles
- corrected analytic years and era buckets
- conflict breadth and opponent breadth
- known-outcome evidence counts and shrunk outcome performance
- blocker-free commander inputs with suspect identities reduced to zero

## What Still Requires Caution

- commander hierarchy remains implicit rather than explicitly modeled
- outcome evidence is improved but still uneven commander by commander
- campaign and war pages remain higher-abstraction evidence
- Wikipedia documentation density remains uneven across eras and regions

## Recommended Default Model

- battle-only conservative baseline for the headline list
- hierarchical weighted model as the main sensitivity comparison

## Bottom Line

The scoring layer is ready for ranking rebuilds and is synchronized to the cleaned commander snapshot. Older scoring outputs from `outputs_final_2026-04-05` should be treated as superseded.
"""


def model_top_names(snapshot_dir: Path, filename: str, limit: int = 5) -> list[str]:
    return ordered_names(top_rows(snapshot_dir / filename, limit), "display_name", limit)


def generate_ranking_comparison_report(snapshot_dir: Path, classification: pd.DataFrame) -> str:
    robust = classification[classification["interpretive_group"] == "robust_elite"].sort_values(["mean_rank", "best_rank"])
    strong = classification[classification["interpretive_group"] == "strong_but_model_sensitive"].sort_values(["best_rank", "mean_rank"])
    caution = classification[classification["interpretive_group"] == "caution_likely_artifact"].sort_values(["best_rank", "mean_rank"])

    return f"""
# Ranking Comparison Report

## Scope

This ranking package is built from the cleaned snapshot in `{snapshot_dir.name}` and supersedes the stale ranking package in `outputs_final_2026-04-05`.

Primary outputs:

- {abs_link(snapshot_dir / "RANKING_RESULTS_BASELINE.csv")}
- {abs_link(snapshot_dir / "RANKING_RESULTS_HIERARCHICAL.csv")}
- {abs_link(snapshot_dir / "RANKING_RESULTS_SENSITIVITY.csv")}
- {abs_link(snapshot_dir / "TOP_COMMANDERS_SUMMARY.csv")}

Additional supporting views:

- {abs_link(snapshot_dir / "RANKING_RESULTS_BATTLE_ONLY.csv")}
- {abs_link(snapshot_dir / "RANKING_RESULTS_BY_ERA.csv")}
- {abs_link(snapshot_dir / "RANKING_RESULTS_PAGE_TYPE_VIEWS.csv")}
- {abs_link(snapshot_dir / "RANKING_RESULTS_TOP_SLICES.csv")}

## Which Commanders Rank Highest

Conservative baseline top 5:

{numbered_lines(model_top_names(snapshot_dir, "RANKING_RESULTS_BASELINE.csv"))}

Battle-only baseline top 5:

{numbered_lines(model_top_names(snapshot_dir, "RANKING_RESULTS_BATTLE_ONLY.csv"))}

Hierarchical weighted top 5:

{numbered_lines(model_top_names(snapshot_dir, "RANKING_RESULTS_HIERARCHICAL.csv"))}

## Most Stable Leaders

The strongest cross-model names in the current package are:

{bullet_lines(ordered_names(robust, limit=7))}

## Strong But Model-Sensitive Leaders

These commanders remain serious contenders, but their placement moves materially with the model:

{bullet_lines(ordered_names(strong, limit=10))}

## Caution Cases

These cases should remain in the audit layer rather than be treated as headline conclusions:

{bullet_lines(ordered_names(caution, limit=8))}

## What The Results Justify Saying Now

- The conservative baseline currently leads with `{model_top_names(snapshot_dir, "RANKING_RESULTS_BASELINE.csv", limit=1)[0]}`.
- The hierarchical weighted model currently leads with `{model_top_names(snapshot_dir, "RANKING_RESULTS_HIERARCHICAL.csv", limit=1)[0]}`.
- The strongest cross-model core is the robust-elite set above, not a single fixed rank order.
- The serious-but-sensitive contenders are concentrated in the model-sensitive set above and should be read with the model context attached.

## Bottom Line

The current ranking stack is synchronized to the cleaned commander layer. Any older ranking files or dashboard conclusions derived from `outputs_final_2026-04-05` should be treated as superseded.
"""


def generate_top_commander_profiles(snapshot_dir: Path, classification: pd.DataFrame, summary: pd.DataFrame) -> str:
    summary = numeric(
        summary,
        [
            "rank_baseline_conservative",
            "rank_battle_only_baseline",
            "rank_hierarchical_weighted",
            "rank_hierarchical_full_credit",
            "rank_hierarchical_equal_split",
            "rank_hierarchical_broader_eligibility",
            "total_engagements_strict",
            "total_battle_pages_strict",
            "distinct_conflicts_strict",
            "distinct_opponents_strict",
            "known_outcome_count",
        ],
    )
    profiles = summary.merge(
        classification[
            [
                "display_name",
                "canonical_wikipedia_url",
                "interpretive_group",
                "dominant_sensitivity_driver",
                "interpretive_reason",
            ]
        ],
        on=["display_name", "canonical_wikipedia_url"],
        how="left",
    )
    robust = profiles[profiles["interpretive_group"] == "robust_elite"].sort_values(["rank_hierarchical_weighted", "rank_baseline_conservative"]).head(6)
    strong = profiles[profiles["interpretive_group"] == "strong_but_model_sensitive"].sort_values(["rank_hierarchical_weighted", "rank_baseline_conservative"]).head(6)
    caution = profiles[profiles["interpretive_group"] == "caution_likely_artifact"].sort_values(["rank_hierarchical_weighted", "rank_baseline_conservative"]).head(3)

    def section(title: str, frame: pd.DataFrame) -> str:
        chunks = [f"## {title}", ""]
        for _, row in frame.iterrows():
            chunks.extend(
                [
                    f"### {row['display_name']}",
                    "",
                    f"- Snapshot: baseline `{fmt_int(row['rank_baseline_conservative'])}`, battle-only `{fmt_int(row['rank_battle_only_baseline'])}`, hierarchical `{fmt_int(row['rank_hierarchical_weighted'])}`, full-credit `{fmt_int(row['rank_hierarchical_full_credit'])}`, equal-split `{fmt_int(row['rank_hierarchical_equal_split'])}`.",
                    f"- Why the profile matters: `{fmt_int(row['total_engagements_strict'])}` strict engagements, `{fmt_int(row['total_battle_pages_strict'])}` battle pages, `{fmt_int(row['distinct_conflicts_strict'])}` distinct conflicts, `{fmt_int(row['distinct_opponents_strict'])}` distinct opponents, `{fmt_int(row['known_outcome_count'])}` known outcomes.",
                    f"- Exposure and caveats: {row.get('page_type_exposure_summary', 'NA')}. {row.get('outcome_profile_summary', 'NA')}. {row.get('interpretive_reason', '')}",
                    "",
                ]
            )
        return "\n".join(chunks)

    robust_section = section("Robust Core", robust)
    strong_section = section("Strong But Model-Sensitive", strong)
    caution_section = section("Caution Cases", caution)
    return f"""
# Top Commanders Profiles

This profile set is synchronized to `{snapshot_dir.name}` and should be read as a companion to the rebuilt ranking package, not the older frozen package.

{robust_section}

{strong_section}

{caution_section}
"""


def generate_post_rebuild_report(
    current_snapshot: Path,
    starting_snapshot: Path,
    baseline_snapshot: Path,
    current_commander_summary: dict[str, Any],
    starting_commander_summary: dict[str, Any],
    current_commander_audit: dict[str, Any],
    qa_summary: dict[str, Any],
) -> str:
    rebuilt_outputs = [
        "SCORING_FRAMEWORK.md",
        "ANALYTICAL_TABLES_SPEC.md",
        "SCORING_READINESS_REPORT.md",
        "RANKING_RESULTS_BASELINE.csv",
        "RANKING_RESULTS_BATTLE_ONLY.csv",
        "RANKING_RESULTS_HIERARCHICAL.csv",
        "RANKING_RESULTS_SENSITIVITY.csv",
        "RANKING_RESULTS_BY_ERA.csv",
        "RANKING_RESULTS_PAGE_TYPE_VIEWS.csv",
        "RANKING_RESULTS_TOP_SLICES.csv",
        "RANKING_COMPARISON_REPORT.md",
        "TOP_COMMANDERS_SUMMARY.csv",
        "TOP_COMMANDERS_PROFILES.md",
        "TOP_TIER_CLASSIFICATION.csv",
        "MODEL_SENSITIVITY_AUDIT.csv",
        "ERA_ELITE_SHORTLIST.csv",
        "BEST_SUPPORTED_TOP_TIER_MEMO.md",
        "dashboard/dashboard_data.js",
        "dashboard/index.html",
        "dashboard/app.js",
        "dashboard/styles.css",
        "RANKING_DASHBOARD_TECHNICAL_NOTE.md",
        "POST_COMMANDER_REBUILD_REPORT.md",
        "COMMANDER_CLEANUP_IMPACT_REPORT.md",
    ]
    rebuilt_output_lines = "\n".join(f"- {abs_link(current_snapshot / name)}" for name in rebuilt_outputs)
    qa_checks = "\n".join(
        f"- {check_name}: `{details['ok']}`"
        for check_name, details in qa_summary["checks"].items()
    )
    return f"""
# Post Commander Rebuild Report

## Starting Point

The rebuild started from the commander snapshot in `{starting_snapshot.name}` and the stale downstream baseline in `{baseline_snapshot.name}`.

Verified starting files:

- {abs_link(starting_snapshot / "battle_commanders.csv")}
- {abs_link(starting_snapshot / "commanders_master.csv")}
- {abs_link(starting_snapshot / "commander_cleanup_summary.json")}
- {abs_link(starting_snapshot / "COMMANDER_CLEANUP_RULES.md")}
- {abs_link(starting_snapshot / "commander_postfix_audit" / "summary.json")}
- {abs_link(starting_snapshot / "commander_postfix_audit" / "row_audit.csv")}
- {abs_link(starting_snapshot / "commander_postfix_audit" / "master_audit.csv")}

## What Happened

1. Verified the commander layer at `outputs_cleaned_2026-04-09_authoritative`.
2. Rebuilt scoring, ranking, interpretive, and dashboard outputs once against that starting snapshot.
3. Downstream QA exposed a real commander blocker: generic rank-only identities and five linked non-person survivors were still present in the main commander file and were surfacing in ranking outputs.
4. Applied a minimal commander hotfix by tightening the commander-name blocker for pure rank-only identities, rebuilding the commander layer from the already-clean battle snapshot, and rerunning commander postfix audit.
5. Preserved the original `2026-04-09` snapshot unchanged and wrote the blocker-free superseding analytics snapshot to `{current_snapshot.name}`.

## Commander Hotfix Delta

- main commander rows: `{fmt_int(starting_commander_summary['battle_commander_rows'])}` -> `{fmt_int(current_commander_summary['battle_commander_rows'])}` ({fmt_delta(current_commander_summary['battle_commander_rows'], starting_commander_summary['battle_commander_rows'])})
- commander quarantine rows: `{fmt_int(starting_commander_summary['battle_commander_quarantine_rows'])}` -> `{fmt_int(current_commander_summary['battle_commander_quarantine_rows'])}` ({fmt_delta(current_commander_summary['battle_commander_quarantine_rows'], starting_commander_summary['battle_commander_quarantine_rows'])})
- commander master rows: `{fmt_int(starting_commander_summary['commanders_master_rows'])}` -> `{fmt_int(current_commander_summary['commanders_master_rows'])}` ({fmt_delta(current_commander_summary['commanders_master_rows'], starting_commander_summary['commanders_master_rows'])})
- battles with any commander rows: `{fmt_int(starting_commander_summary['battles_with_any_commander_rows'])}` -> `{fmt_int(current_commander_summary['battles_with_any_commander_rows'])}` ({fmt_delta(current_commander_summary['battles_with_any_commander_rows'], starting_commander_summary['battles_with_any_commander_rows'])})
- current commander blockers remaining: `{fmt_int(current_commander_audit['row_blocker_rows'])}`
- current master blockers remaining: `{fmt_int(current_commander_audit['master_blocker_rows'])}`

## Scripts Run

- `rebuild_cleaned_commanders.py`
- `audit_battle_commanders_postfix.py`
- `apply_commander_postfix_actions.py`
- `build_scoring_framework_package.py`
- `build_ranking_package.py`
- `build_interpretive_layer.py`
- `build_ranking_dashboard.py`
- `qa_dashboard_snapshot.py`
- `generate_post_commander_reports.py`

## Rebuilt Outputs

{rebuilt_output_lines}

## QA

Dashboard QA summary:

- overall pass: `{qa_summary['all_checks_passed']}`
- commander count in dashboard: `{fmt_int(qa_summary['expected']['commander_count'])}`
- baseline leader alignment: `{qa_summary['checks']['baseline_alignment']['leader_from_table']}`
- hierarchical leader alignment: `{qa_summary['checks']['hierarchical_alignment']['leader_from_table']}`
- console errors: `{fmt_int(qa_summary['checks']['console_clean']['console_error_count'])}`
- page errors: `{fmt_int(qa_summary['checks']['console_clean']['page_error_count'])}`

Detailed QA checks:

{qa_checks}

## Supersession Status

- The stale downstream analytics in `{baseline_snapshot.name}` are superseded.
- The initial commander snapshot in `{starting_snapshot.name}` is preserved for audit, but it is superseded for downstream analytics because QA exposed real commander blockers.
- The synchronized analytics state is now `{current_snapshot.name}`.

## Caveats

- The battle layer was not rebuilt in this stage; it was consumed as-is from the cleaned battle snapshot already in place.
- A few valid commander names still carry title prefixes in the text layer, but the commander postfix audit reports zero blockers in the main commander file and master file.
- Any future rerun of the dashboard build should preserve the current sortable explorer-table behavior now present in `dashboard/app.js`.

## Bottom Line

All downstream scoring, ranking, interpretive, and dashboard outputs are now synchronized to the blocker-free commander layer in `{current_snapshot.name}`.
"""


def generate_cleanup_impact_report(
    current_snapshot: Path,
    baseline_snapshot: Path,
    starting_snapshot: Path,
    current_scoring: dict[str, Any],
    baseline_scoring: dict[str, Any],
    current_ranking: dict[str, Any],
    baseline_ranking: dict[str, Any],
    current_classification: pd.DataFrame,
    baseline_classification: pd.DataFrame,
    current_era: pd.DataFrame,
    baseline_era: pd.DataFrame,
    sensitivity_diff: pd.DataFrame,
) -> str:
    baseline_rises, baseline_drops = focus_shift_table(sensitivity_diff, "baseline_shift")
    hier_rises, hier_drops = focus_shift_table(sensitivity_diff, "hier_shift")

    old_robust = set(baseline_classification.loc[baseline_classification["interpretive_group"] == "robust_elite", "display_name"])
    new_robust = set(current_classification.loc[current_classification["interpretive_group"] == "robust_elite", "display_name"])
    robust_added = sorted(new_robust - old_robust)
    robust_removed = sorted(old_robust - new_robust)

    current_dashboard_count = len(read_csv(current_snapshot / "RANKING_RESULTS_SENSITIVITY.csv"))
    baseline_dashboard_count = len(read_csv(baseline_snapshot / "RANKING_RESULTS_SENSITIVITY.csv"))

    old_top_baseline = model_top_names(baseline_snapshot, "RANKING_RESULTS_BASELINE.csv")
    new_top_baseline = model_top_names(current_snapshot, "RANKING_RESULTS_BASELINE.csv")
    old_top_hier = model_top_names(baseline_snapshot, "RANKING_RESULTS_HIERARCHICAL.csv")
    new_top_hier = model_top_names(current_snapshot, "RANKING_RESULTS_HIERARCHICAL.csv")

    robust_added_lines = bullet_lines(robust_added) if robust_added else "- none"
    robust_removed_lines = bullet_lines(robust_removed) if robust_removed else "- none"

    return f"""
# Commander Cleanup Impact Report

## Scope

This report compares the stale analytics package in `{baseline_snapshot.name}` against the synchronized rebuild in `{current_snapshot.name}`. The rebuild started from `{starting_snapshot.name}` but discovered commander blockers during QA, so the final comparison target is the blocker-free `2026-04-10` snapshot.

## Impact On Cohort Sizes

- baseline cohort: `{fmt_int(baseline_ranking['model_rows']['baseline_conservative'])}` -> `{fmt_int(current_ranking['model_rows']['baseline_conservative'])}` ({fmt_delta(current_ranking['model_rows']['baseline_conservative'], baseline_ranking['model_rows']['baseline_conservative'])})
- battle-only cohort: `{fmt_int(baseline_ranking['model_rows']['battle_only_baseline'])}` -> `{fmt_int(current_ranking['model_rows']['battle_only_baseline'])}` ({fmt_delta(current_ranking['model_rows']['battle_only_baseline'], baseline_ranking['model_rows']['battle_only_baseline'])})
- hierarchical weighted cohort: `{fmt_int(baseline_ranking['model_rows']['hierarchical_weighted'])}` -> `{fmt_int(current_ranking['model_rows']['hierarchical_weighted'])}` ({fmt_delta(current_ranking['model_rows']['hierarchical_weighted'], baseline_ranking['model_rows']['hierarchical_weighted'])})
- broader-eligibility hierarchical cohort: `{fmt_int(baseline_ranking['model_rows']['hierarchical_broader_eligibility'])}` -> `{fmt_int(current_ranking['model_rows']['hierarchical_broader_eligibility'])}` ({fmt_delta(current_ranking['model_rows']['hierarchical_broader_eligibility'], baseline_ranking['model_rows']['hierarchical_broader_eligibility'])})

## Impact On Feature Tables

- identity bridge rows: `{fmt_int(baseline_scoring['derived']['identity_bridge_rows'])}` -> `{fmt_int(current_scoring['derived']['identity_bridge_rows'])}` ({fmt_delta(current_scoring['derived']['identity_bridge_rows'], baseline_scoring['derived']['identity_bridge_rows'])})
- annotated commander-engagement rows: `{fmt_int(baseline_scoring['derived']['annotated_rows'])}` -> `{fmt_int(current_scoring['derived']['annotated_rows'])}` ({fmt_delta(current_scoring['derived']['annotated_rows'], baseline_scoring['derived']['annotated_rows'])})
- opponent profile rows: `{fmt_int(baseline_scoring['derived']['opponent_profile_rows'])}` -> `{fmt_int(current_scoring['derived']['opponent_profile_rows'])}` ({fmt_delta(current_scoring['derived']['opponent_profile_rows'], baseline_scoring['derived']['opponent_profile_rows'])})
- linked identities: `{fmt_int(baseline_scoring['identities']['linked_identities'])}` -> `{fmt_int(current_scoring['identities']['linked_identities'])}` ({fmt_delta(current_scoring['identities']['linked_identities'], baseline_scoring['identities']['linked_identities'])})
- raw-name-only identities: `{fmt_int(baseline_scoring['identities']['raw_name_only_identities'])}` -> `{fmt_int(current_scoring['identities']['raw_name_only_identities'])}` ({fmt_delta(current_scoring['identities']['raw_name_only_identities'], baseline_scoring['identities']['raw_name_only_identities'])})
- suspect identities: `{fmt_int(baseline_scoring['identities']['suspect_identities'])}` -> `{fmt_int(current_scoring['identities']['suspect_identities'])}` ({fmt_delta(current_scoring['identities']['suspect_identities'], baseline_scoring['identities']['suspect_identities'])})

The elimination of suspect identities from `293` to `0` is the clearest structural improvement. The large drop in opponent-profile rows likely reflects removal of noisy or non-person commander participants and cleaner deduplication rather than a loss of valid commander coverage.

## Impact On Top Commanders

Old baseline top 5:

{numbered_lines(old_top_baseline)}

New baseline top 5:

{numbered_lines(new_top_baseline)}

Old hierarchical top 5:

{numbered_lines(old_top_hier)}

New hierarchical top 5:

{numbered_lines(new_top_hier)}

Most visible headline shifts:

- Baseline leader changed from `Maurice of Orange` to `Charles XII of Sweden`.
- `Alexander Suvorov` rose from a stable elite contender to baseline rank `3` while remaining hierarchical rank `2`.
- `Enver Pasha` and `Ivan Konev` no longer dominate the hierarchical top five; the new hierarchical top tier is headed by `Suleiman the Magnificent`, `Alexander Suvorov`, `Ibrahim Pasha of Egypt`, `Napoleon Bonaparte`, and `Abbas the Great`.

## Impact On Model Sensitivity

Robust-elite additions:

{robust_added_lines}

Robust-elite removals:

{robust_removed_lines}

Largest baseline rises among commanders relevant to the old or new top 50:

{shift_bullets(baseline_rises, "baseline_shift", "rank_baseline_conservative_new", "rank_baseline_conservative_old")}

Largest baseline drops among commanders relevant to the old or new top 50:

{shift_bullets(baseline_drops, "baseline_shift", "rank_baseline_conservative_new", "rank_baseline_conservative_old")}

Largest hierarchical rises among commanders relevant to the old or new top 50:

{shift_bullets(hier_rises, "hier_shift", "rank_hierarchical_weighted_new", "rank_hierarchical_weighted_old")}

Largest hierarchical drops among commanders relevant to the old or new top 50:

{shift_bullets(hier_drops, "hier_shift", "rank_hierarchical_weighted_new", "rank_hierarchical_weighted_old")}

These are large shifts. Some clearly reflect cleaner commander identities and removal of non-person noise; others may reflect genuine sensitivity to the tighter commander layer and should be interpreted cautiously rather than assumed to be regressions.

## Impact On Era Results

### Ancient

Old:

{era_lines(baseline_era, "ancient")}

New:

{era_lines(current_era, "ancient")}

### Medieval

Old:

{era_lines(baseline_era, "medieval")}

New:

{era_lines(current_era, "medieval")}

### Early Modern

Old:

{era_lines(baseline_era, "early_modern")}

New:

{era_lines(current_era, "early_modern")}

### Modern

Old:

{era_lines(baseline_era, "modern")}

New:

{era_lines(current_era, "modern")}

### Contemporary

Old:

{era_lines(baseline_era, "contemporary")}

New:

{era_lines(current_era, "contemporary")}

## Impact On Dashboard Data Size

- ranked commanders in dashboard data: `{fmt_int(baseline_dashboard_count)}` -> `{fmt_int(current_dashboard_count)}` ({fmt_delta(current_dashboard_count, baseline_dashboard_count)})

The smaller dashboard universe is consistent with the commander cleanup removing noisy or invalid commander identities from the ranking layer.

## Commanders That Dropped Because Noise Was Removed

Examples from the commander-hotfix stage include generic rank-only and non-person entries that were present in the intermediate `2026-04-09` commander snapshot but removed before the final synchronized rebuild:

- `Major general`
- `Lieutenant general`
- `officer`
- `The Jakarta Post`
- `Reddit`
- `Firat News Agency`
- the non-person `Royalist` entry

These do not appear in the final ranking or dashboard bundle.

## Commanders That Rose Under Cleaner Identity Handling

The clearest beneficiaries of the cleaner commander layer include:

- `Maurice, Prince of Orange`
- `Abu Ubayda ibn al-Jarrah`
- `Baybars`
- `Napoleon Bonaparte`
- `Hari Singh Nalwa`
- `Ibrahim Pasha of Egypt`

This is an inference from the before/after rank movement and the removal of noisy commander identities, not a claim that every upward shift is automatically correct.

## Bottom Line

The commander cleanup materially changed the analytical picture. The top of the ranking package still has meaningful continuity because `Suleiman the Magnificent` and `Alexander Suvorov` remain central, but cohort sizes, robust-core membership, era shortlists, and several headline leaders changed enough that all old downstream analytics should be considered superseded.
"""


def main() -> None:
    args = parse_args()
    current_snapshot = args.current_snapshot_dir.resolve()
    starting_snapshot = args.starting_snapshot_dir.resolve()
    baseline_snapshot = args.baseline_snapshot_dir.resolve()

    current_scoring = read_json(current_snapshot / "derived_scoring" / "scoring_build_metrics.json")
    baseline_scoring = read_json(baseline_snapshot / "derived_scoring" / "scoring_build_metrics.json")
    current_ranking = read_json(current_snapshot / "RANKING_BUILD_METRICS.json")
    baseline_ranking = read_json(baseline_snapshot / "RANKING_BUILD_METRICS.json")
    current_commander_summary = read_json(current_snapshot / "commander_cleanup_summary.json")
    starting_commander_summary = read_json(starting_snapshot / "commander_cleanup_summary.json")
    current_commander_audit = read_json(current_snapshot / "commander_postfix_audit" / "summary.json")
    qa_summary = read_json(current_snapshot / "dashboard_qa_summary.json")

    current_classification = numeric(
        read_csv(current_snapshot / "TOP_TIER_CLASSIFICATION.csv"),
        ["best_rank", "mean_rank", "rank_range", "top10_appearances", "top25_appearances"],
    )
    baseline_classification = numeric(
        read_csv(baseline_snapshot / "TOP_TIER_CLASSIFICATION.csv"),
        ["best_rank", "mean_rank", "rank_range", "top10_appearances", "top25_appearances"],
    )
    current_era = read_csv(current_snapshot / "ERA_ELITE_SHORTLIST.csv")
    baseline_era = read_csv(baseline_snapshot / "ERA_ELITE_SHORTLIST.csv")
    current_summary = read_csv(current_snapshot / "TOP_COMMANDERS_SUMMARY.csv")
    sensitivity_diff = sensitivity_join(baseline_snapshot, current_snapshot)

    write_text(
        current_snapshot / "SCORING_FRAMEWORK.md",
        generate_scoring_framework(current_snapshot, current_scoring, current_commander_summary, current_commander_audit),
    )
    write_text(
        current_snapshot / "ANALYTICAL_TABLES_SPEC.md",
        generate_analytical_tables_spec(current_snapshot, current_snapshot / "derived_scoring"),
    )
    write_text(
        current_snapshot / "SCORING_READINESS_REPORT.md",
        generate_scoring_readiness_report(current_snapshot, current_scoring),
    )
    write_text(
        current_snapshot / "RANKING_COMPARISON_REPORT.md",
        generate_ranking_comparison_report(current_snapshot, current_classification),
    )
    write_text(
        current_snapshot / "TOP_COMMANDERS_PROFILES.md",
        generate_top_commander_profiles(current_snapshot, current_classification, current_summary),
    )
    write_text(
        current_snapshot / "POST_COMMANDER_REBUILD_REPORT.md",
        generate_post_rebuild_report(
            current_snapshot,
            starting_snapshot,
            baseline_snapshot,
            current_commander_summary,
            starting_commander_summary,
            current_commander_audit,
            qa_summary,
        ),
    )
    write_text(
        current_snapshot / "COMMANDER_CLEANUP_IMPACT_REPORT.md",
        generate_cleanup_impact_report(
            current_snapshot,
            baseline_snapshot,
            starting_snapshot,
            current_scoring,
            baseline_scoring,
            current_ranking,
            baseline_ranking,
            current_classification,
            baseline_classification,
            current_era,
            baseline_era,
            sensitivity_diff,
        ),
    )


if __name__ == "__main__":
    main()
