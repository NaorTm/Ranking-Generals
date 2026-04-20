from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd

from build_ranking_package import prepare_rows
from generate_post_commander_reports import (
    generate_analytical_tables_spec,
    generate_ranking_comparison_report,
    generate_scoring_framework,
    generate_scoring_readiness_report,
    generate_top_commander_profiles,
    numeric,
)


ROOT = Path(r"C:\Users\gameo\OneDrive\Desktop\test")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str).fillna("")


def write_text(path: Path, content: str) -> None:
    path.write_text(content.strip() + "\n", encoding="utf-8")


def fmt_int(value: Any) -> str:
    try:
        return f"{int(round(float(value))):,}"
    except Exception:
        return "NA"


def fmt_float(value: Any, digits: int = 1) -> str:
    try:
        return f"{float(value):.{digits}f}"
    except Exception:
        return "NA"


def fmt_delta(new_value: Any, old_value: Any) -> str:
    try:
        delta = float(new_value) - float(old_value)
    except Exception:
        return "NA"
    if delta > 0:
        return f"+{int(round(delta)):,}"
    if delta < 0:
        return f"-{int(round(abs(delta))):,}"
    return "0"


def inline_names(names: list[str], limit: int | None = None) -> str:
    if limit is not None:
        names = names[:limit]
    names = [name for name in names if str(name).strip()]
    wrapped = [f"`{name}`" for name in names]
    if not wrapped:
        return "`none`"
    if len(wrapped) == 1:
        return wrapped[0]
    if len(wrapped) == 2:
        return f"{wrapped[0]} and {wrapped[1]}"
    return f"{', '.join(wrapped[:-1])}, and {wrapped[-1]}"


def top_names(snapshot_dir: Path, filename: str, limit: int = 5) -> list[str]:
    frame = read_csv(snapshot_dir / filename)
    return frame["display_name"].head(limit).tolist()


def row_by_name(frame: pd.DataFrame, name: str) -> pd.Series:
    matches = frame[frame["display_name"].eq(name)]
    if matches.empty:
        return pd.Series(dtype=object)
    return matches.iloc[0]


def markdown_table(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "_none_"
    headers = list(frame.columns)
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in frame.to_dict(orient="records"):
        values = [str(row.get(header, "")).replace("\n", " ").strip() for header in headers]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def build_impl_report(
    old_snapshot: Path,
    new_snapshot: Path,
    old_annotated: pd.DataFrame,
    new_annotated: pd.DataFrame,
    validation: dict[str, Any],
) -> str:
    keys = ["analytic_commander_id", "battle_id"]
    merged = old_annotated[
        keys
        + [
            "display_name",
            "battle_name",
            "page_type",
            "result_raw",
            "side",
            "outcome_category",
            "outcome_inference_method",
            "outcome_credit_fraction",
            "known_outcome_flag",
        ]
    ].merge(
        new_annotated[
            keys
            + [
                "outcome_category",
                "outcome_inference_method",
                "outcome_credit_fraction",
                "known_outcome_flag",
            ]
        ],
        on=keys,
        suffixes=("_old", "_new"),
        how="inner",
    )
    anti = merged[merged["result_raw"].str.contains("anti-|against ", case=False, na=False)].copy()
    coalition = merged[
        merged["result_raw"].str.contains("coalition victory|allied victory|allies victory", case=False, na=False)
    ].copy()
    changed = merged[
        (merged["outcome_category_old"] != merged["outcome_category_new"])
        | (merged["outcome_credit_fraction_old"] != merged["outcome_credit_fraction_new"])
        | (merged["known_outcome_flag_old"] != merged["known_outcome_flag_new"])
    ].copy()

    charles_changes = changed[changed["display_name"].eq("Charles XII of Sweden")].copy()
    charles_table = markdown_table(
        charles_changes[
            [
                "battle_name",
                "page_type",
                "result_raw",
                "side",
                "outcome_category_old",
                "outcome_category_new",
                "outcome_inference_method_old",
                "outcome_inference_method_new",
                "outcome_credit_fraction_old",
                "outcome_credit_fraction_new",
            ]
        ].rename(
            columns={
                "outcome_category_old": "old_outcome",
                "outcome_category_new": "new_outcome",
                "outcome_inference_method_old": "old_method",
                "outcome_inference_method_new": "new_method",
                "outcome_credit_fraction_old": "old_credit",
                "outcome_credit_fraction_new": "new_credit",
            }
        )
    )

    anti_unknown = new_annotated[
        new_annotated["result_raw"].str.contains("anti-|against ", case=False, na=False)
        & new_annotated["outcome_category"].eq("unknown")
    ].copy()
    anti_unknown_examples = markdown_table(
        anti_unknown[
            ["battle_name", "display_name", "result_raw", "side", "outcome_inference_method"]
        ].head(8)
    )
    coalition_unknown = new_annotated[
        new_annotated["result_raw"].str.contains("coalition victory|allied victory|allies victory", case=False, na=False)
        & new_annotated["outcome_category"].eq("unknown")
    ].copy()

    return f"""
# Ranking Fix Implementation Report

## Scope

This is a targeted correction pass on top of `{old_snapshot.name}`. The old authoritative package is preserved unchanged. The corrected and rebuilt analytics snapshot is `{new_snapshot.name}`, which supersedes `{old_snapshot.name}` for scoring, ranking, interpretive, and dashboard outputs.

No battle-layer or commander-layer rebuild was performed in this pass. The authoritative data layer consumed here is the already-clean battle and commander snapshot copied forward into `{new_snapshot.name}`.

## Files Changed

- `build_scoring_framework_package.py`
- `build_ranking_package.py`
- `build_interpretive_layer.py`
- `generate_post_commander_reports.py`
- `generate_rankfix_reports.py`

## Fix 1: Outcome-Inference Bug For `anti-X` Results

Old incorrect behavior:

- Result strings like `Anti-Swedish coalition victory` could be interpreted as a Swedish victory because the old matcher treated the `Swedish` token as ordinary positive winner evidence.

Corrected behavior:

- `anti-X` / `against X` is now treated as loser-side evidence first.
- The corrected matcher resolves the winning side as the non-target side, preferring the unique opposing side and then the coalition side when available.
- This path now correctly handles Charles XII cases such as `Great Northern War` and `Siege of Stralsund (1711–1715)`.

Affected anti-target rows:

- anti-target rows in annotated commander engagements: `{fmt_int(len(anti))}`
- anti-target rows whose outcome changed: `{fmt_int((anti['outcome_category_old'] != anti['outcome_category_new']).sum())}`
- wrong `victory -> defeat` flips corrected: `{fmt_int(((anti['outcome_category_old'] == 'victory') & (anti['outcome_category_new'] == 'defeat')).sum())}`
- wrong `defeat -> victory` flips corrected: `{fmt_int(((anti['outcome_category_old'] == 'defeat') & (anti['outcome_category_new'] == 'victory')).sum())}`
- `unknown -> known` because the new matcher could now resolve the row: `{fmt_int(((anti['outcome_category_old'] == 'unknown') & (anti['outcome_category_new'] != 'unknown')).sum())}`
- `known -> unknown` because the new matcher refused to overclaim on unresolved aliases or ambiguous pages: `{fmt_int(((anti['outcome_category_old'] != 'unknown') & (anti['outcome_category_new'] == 'unknown')).sum())}`

## Fix 2: Unknown Outcomes No Longer Pollute Split-Credit Denominators

Old behavior:

- In split-credit models, `outcome_factor_split` was equal to `outcome_credit_fraction`, even when `outcome_category = unknown`.
- That meant unknown outcomes still sat in the denominator as zero-value evidence instead of being treated as missing evidence.

Corrected behavior:

- `outcome_factor_split` is now `outcome_credit_fraction * 1[outcome_category != 'unknown']`.

Validation:

- unknown annotated rows in the rebuilt package: `{fmt_int(validation['unknown_rows'])}`
- rows where unknown still contributes non-zero split outcome factor: `{fmt_int(validation['unknown_split_violations'])}`

## Fix 3: Defeat Dilution Under Split Credit

Old behavior:

- Same-side outcome credit used a strict `1 / side_count` split.
- On crowded pages, defeats were diluted so aggressively that a serious loss could become too weak relative to the commander’s victories.

Corrected behavior:

- Same-side outcome credit now uses `1 / sqrt(side_count)`.
- This still discounts crowded pages, but it no longer crushes defeats as hard as the old linear split.

Observed effect:

- commander engagement rows whose split credit changed: `{fmt_int((merged['outcome_credit_fraction_old'] != merged['outcome_credit_fraction_new']).sum())}`
- example: Charles XII at `Battle of Poltava` changed from `0.142857` to `0.377964`
- example: Charles XII at `Siege of Stralsund (1711–1715)` changed from `0.333333` to `0.577350`
- example: Charles XII at `Battle of Narva (1700)` changed from `0.333333` to `0.577350`

## Fix 4: Confirmed Charles XII Mis-Scoring

These corrections were produced by the fixed inference layer, not by manual hand-editing of battle rows:

{charles_table}

What changed materially for Charles XII:

- `Great Northern War`: `victory -> defeat`
- `Siege of Stralsund (1711–1715)`: `victory -> defeat`
- `Battle of Stresow`: `unknown -> defeat`
- `Siege of Fredriksten`: `unknown -> defeat`
- `Battle of Poltava`: still `defeat`, but its split-outcome weight increased materially under the new split rule

Known unresolved Charles XII caveat:

- `Battle of Malatitze` remains `unknown`; this pass did not guess an unsupported outcome.

## Rebuilt Outputs

- scoring docs and derived tables under `{new_snapshot.name}\\derived_scoring`
- ranking outputs: `RANKING_RESULTS_*.csv`, `RANKING_BUILD_METRICS.json`, `TOP_COMMANDERS_SUMMARY.csv`
- interpretive outputs: `TOP_TIER_CLASSIFICATION.csv`, `MODEL_SENSITIVITY_AUDIT.csv`, `ERA_ELITE_SHORTLIST.csv`, `BEST_SUPPORTED_TOP_TIER_MEMO.md`
- dashboard bundle: `{new_snapshot.name}\\dashboard`
- dashboard QA: `dashboard_qa_summary.json`

## Validation Summary

- total commander engagement rows with any outcome or credit change: `{fmt_int(len(changed))}`
- rows whose outcome category changed: `{fmt_int((merged['outcome_category_old'] != merged['outcome_category_new']).sum())}`
- rows whose known-outcome flag changed: `{fmt_int((merged['known_outcome_flag_old'] != merged['known_outcome_flag_new']).sum())}`
- coalition/allied outcome rows whose outcome changed: `{fmt_int((coalition['outcome_category_old'] != coalition['outcome_category_new']).sum())}`
- coalition/allied rows resolved from `unknown` to known outcome: `{fmt_int(((coalition['outcome_category_old'] == 'unknown') & (coalition['outcome_category_new'] != 'unknown')).sum())}`

## Residual Caveats

- The old `anti-X` inversion bug is fixed on the confirmed Charles XII pages and on many similar rows, but `{fmt_int(len(anti_unknown))}` anti-target rows still remain unresolved because of alias gaps or structurally ambiguous pages.
- Representative unresolved anti-target examples:

{anti_unknown_examples}

- Coalition/allied result strings improved substantially, but `{fmt_int(len(coalition_unknown))}` coalition/allied rows still remain unresolved in the rebuilt snapshot. Those rows were left conservative rather than guessed.
- This pass intentionally did not touch the battle or commander source layers. It corrected logic and downstream scoring behavior only.
"""


def build_impact_report(
    old_snapshot: Path,
    new_snapshot: Path,
    old_scoring: dict[str, Any],
    new_scoring: dict[str, Any],
    old_ranking: dict[str, Any],
    new_ranking: dict[str, Any],
    old_summary: pd.DataFrame,
    new_summary: pd.DataFrame,
    old_classification: pd.DataFrame,
    new_classification: pd.DataFrame,
    dashboard_qa: dict[str, Any],
) -> str:
    old_charles = row_by_name(old_summary, "Charles XII of Sweden")
    new_charles = row_by_name(new_summary, "Charles XII of Sweden")

    old_baseline = read_csv(old_snapshot / "RANKING_RESULTS_BASELINE.csv")
    new_baseline = read_csv(new_snapshot / "RANKING_RESULTS_BASELINE.csv")
    old_battle = read_csv(old_snapshot / "RANKING_RESULTS_BATTLE_ONLY.csv")
    new_battle = read_csv(new_snapshot / "RANKING_RESULTS_BATTLE_ONLY.csv")
    old_hier = read_csv(old_snapshot / "RANKING_RESULTS_HIERARCHICAL.csv")
    new_hier = read_csv(new_snapshot / "RANKING_RESULTS_HIERARCHICAL.csv")

    old_robust = set(old_classification.loc[old_classification["interpretive_group"].eq("robust_elite"), "display_name"])
    new_robust = set(new_classification.loc[new_classification["interpretive_group"].eq("robust_elite"), "display_name"])
    robust_added = sorted(new_robust - old_robust)
    robust_removed = sorted(old_robust - new_robust)

    suspicious_names = ["Qasem Soleimani", "Nelson A. Miles", "Charles XII of Sweden"]
    suspicious_rows = []
    for name in suspicious_names:
        row = row_by_name(new_classification, name)
        if not row.empty:
            suspicious_rows.append(
                {
                    "display_name": name,
                    "interpretive_group": row.get("interpretive_group", ""),
                    "best_rank": row.get("best_rank", ""),
                    "worst_rank": row.get("worst_rank", ""),
                    "dominant_sensitivity_driver": row.get("dominant_sensitivity_driver", ""),
                    "interpretive_reason": row.get("interpretive_reason", ""),
                }
            )
    suspicious_table = markdown_table(pd.DataFrame(suspicious_rows))

    return f"""
# Post Fix Ranking Impact Report

## Scope

This report compares the old authoritative ranking package in `{old_snapshot.name}` with the corrected ranking package in `{new_snapshot.name}`.

## Cohort Impact

- conservative baseline cohort: `{fmt_int(old_ranking['model_rows']['baseline_conservative'])}` -> `{fmt_int(new_ranking['model_rows']['baseline_conservative'])}` ({fmt_delta(new_ranking['model_rows']['baseline_conservative'], old_ranking['model_rows']['baseline_conservative'])})
- battle-only baseline cohort: `{fmt_int(old_ranking['model_rows']['battle_only_baseline'])}` -> `{fmt_int(new_ranking['model_rows']['battle_only_baseline'])}` ({fmt_delta(new_ranking['model_rows']['battle_only_baseline'], old_ranking['model_rows']['battle_only_baseline'])})
- hierarchical weighted cohort: `{fmt_int(old_ranking['model_rows']['hierarchical_weighted'])}` -> `{fmt_int(new_ranking['model_rows']['hierarchical_weighted'])}` ({fmt_delta(new_ranking['model_rows']['hierarchical_weighted'], old_ranking['model_rows']['hierarchical_weighted'])})
- broader-eligibility hierarchical cohort: `{fmt_int(old_ranking['model_rows']['hierarchical_broader_eligibility'])}` -> `{fmt_int(new_ranking['model_rows']['hierarchical_broader_eligibility'])}` ({fmt_delta(new_ranking['model_rows']['hierarchical_broader_eligibility'], old_ranking['model_rows']['hierarchical_broader_eligibility'])})
- ranked commanders shown in dashboard data: `2,127` -> `{fmt_int(dashboard_qa['expected']['commander_count'])}` ({fmt_delta(dashboard_qa['expected']['commander_count'], 2127)})

This cohort growth is expected: once many previously-unknown outcomes became valid outcomes, more commanders cleared battle/outcome gates.

## Charles XII Of Sweden

### Rank Impact

- `baseline_conservative`: `{fmt_int(old_charles.get('rank_baseline_conservative'))}` -> `{fmt_int(new_charles.get('rank_baseline_conservative'))}`
- `battle_only_baseline`: `{fmt_int(old_charles.get('rank_battle_only_baseline'))}` -> `{fmt_int(new_charles.get('rank_battle_only_baseline'))}`
- `hierarchical_weighted`: `{fmt_int(old_charles.get('rank_hierarchical_weighted'))}` -> `{fmt_int(new_charles.get('rank_hierarchical_weighted'))}`
- `hierarchical_full_credit`: `{fmt_int(old_charles.get('rank_hierarchical_full_credit'))}` -> `{fmt_int(new_charles.get('rank_hierarchical_full_credit'))}`
- `hierarchical_equal_split`: `{fmt_int(old_charles.get('rank_hierarchical_equal_split'))}` -> `{fmt_int(new_charles.get('rank_hierarchical_equal_split'))}`
- `hierarchical_broader_eligibility`: `{fmt_int(old_charles.get('rank_hierarchical_broader_eligibility'))}` -> `{fmt_int(new_charles.get('rank_hierarchical_broader_eligibility'))}`

### Outcome Profile Impact

- known outcomes: `{fmt_int(old_charles.get('known_outcome_count'))}` -> `{fmt_int(new_charles.get('known_outcome_count'))}`
- outcome summary: `{old_charles.get('outcome_profile_summary', 'NA')}` -> `{new_charles.get('outcome_profile_summary', 'NA')}`
- page-type exposure: `{new_charles.get('page_type_exposure_summary', 'NA')}`

### Interpretation

Charles XII was previously being flattered by a mix of wrong victories, unresolved defeats, and too-harsh linear split dilution on crowded pages. After the fixes:

- four important Charles rows moved in the historically expected direction
- his defeat count rose from `2` to `6`
- his baseline and battle-only placements stopped looking like obvious headline winners
- he remains a strong battle-dominant commander, but he is now clearly model-sensitive rather than baseline-proof

## Model-Level Impact

### Conservative Baseline

- old leader: `{old_baseline.iloc[0]['display_name']}`
- new leader: `{new_baseline.iloc[0]['display_name']}`
- old top 5: {inline_names(old_baseline['display_name'].head(5).tolist())}
- new top 5: {inline_names(new_baseline['display_name'].head(5).tolist())}

Judgment:

- This model improved materially because the Charles XII anomaly is gone.
- It is still battle-specialist heavy and should still be treated as a diagnostic battle-performance view, not a final all-time headline ranking.

### Battle-Only Baseline

- old leader: `{old_battle.iloc[0]['display_name']}`
- new leader: `{new_battle.iloc[0]['display_name']}`
- old top 5: {inline_names(old_battle['display_name'].head(5).tolist())}
- new top 5: {inline_names(new_battle['display_name'].head(5).tolist())}

Judgment:

- This model remains intentionally narrow and still rewards battle-specialist profiles very aggressively.
- It is useful as a stress test, but not as the single best answer to the overall research question.

### Hierarchical Weighted

- old leader: `{old_hier.iloc[0]['display_name']}`
- new leader: `{new_hier.iloc[0]['display_name']}`
- old top 5: {inline_names(old_hier['display_name'].head(5).tolist())}
- new top 5: {inline_names(new_hier['display_name'].head(5).tolist())}

Judgment:

- This remains the most trustworthy single ranking view in the package.
- It still needs interpretive caution because some historically suspicious higher-level beneficiaries remain high, especially `Qasem Soleimani` and `Nelson A. Miles`.

### Full-Credit / Equal-Split / Broader-Eligibility Views

- `hierarchical_full_credit` remains the least trustworthy model because it is still the most exposed to attribution inflation.
- `hierarchical_equal_split` is safer than full-credit, but still sensitive to page structure and higher-level exposure.
- `hierarchical_broader_eligibility` is useful for exploratory stress-testing, not for the headline conclusion layer.

## Interpretive Layer Impact

Robust-elite additions:

{chr(10).join(f"- `{name}`" for name in robust_added) if robust_added else "- none"}

Robust-elite removals:

{chr(10).join(f"- `{name}`" for name in robust_removed) if robust_removed else "- none"}

This is a real interpretive shift. The corrected system now leans more toward commanders whose records survive both stronger defeat treatment and the repaired outcome inference.

## Historically Suspicious Results That Still Remain

{suspicious_table}

Bottom line on residual plausibility issues:

- `Qasem Soleimani` remains a caution case even after the fixes; his very high hierarchical placement is still driven by higher-level exposure.
- `Nelson A. Miles` remains a caution case for the same reason.
- `Charles XII of Sweden` is no longer the obvious red flag he was before, but his profile is still highly model-sensitive and battle-dominant.

## Dashboard Synchronization

- dashboard snapshot label: `{dashboard_qa['checks']['header_metadata']['snapshot_label']}`
- baseline leader alignment: `{dashboard_qa['checks']['baseline_alignment']['leader_from_table']}`
- hierarchical leader alignment: `{dashboard_qa['checks']['hierarchical_alignment']['leader_from_table']}`
- all dashboard QA checks passed: `{dashboard_qa['all_checks_passed']}`
- console errors: `{fmt_int(dashboard_qa['checks']['console_clean']['console_error_count'])}`
- page errors: `{fmt_int(dashboard_qa['checks']['console_clean']['page_error_count'])}`

## Updated Trust Judgment

- `hierarchical_weighted` remains the most trustworthy single model.
- `baseline_conservative` is now materially better and no longer obviously broken by Charles XII, but it is still not a final all-time model.
- `battle_only_baseline` remains a useful battle-performance stress test.
- `hierarchical_full_credit` still needs revision before it should be trusted as a headline table.

## Final Judgment

The ranking system is more historically and methodologically sound than the previous authoritative package. The Charles XII anomaly was real, and it was driven by both a logic bug and design behavior. That issue is now materially corrected. The package is still not free of interpretive tension, but the remaining problems are now mostly model- and coverage-related caution cases, not the specific scoring defects identified in the audit.
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate rank-fix markdown reports and refreshed docs.")
    parser.add_argument(
        "--old-snapshot-dir",
        type=Path,
        default=Path("outputs_cleaned_2026-04-10_authoritative"),
    )
    parser.add_argument(
        "--new-snapshot-dir",
        type=Path,
        default=Path("outputs_cleaned_2026-04-10_rankfix_authoritative"),
    )
    args = parser.parse_args()

    old_snapshot = (ROOT / args.old_snapshot_dir).resolve()
    new_snapshot = (ROOT / args.new_snapshot_dir).resolve()

    old_scoring = read_json(old_snapshot / "derived_scoring" / "scoring_build_metrics.json")
    new_scoring = read_json(new_snapshot / "derived_scoring" / "scoring_build_metrics.json")
    old_ranking = read_json(old_snapshot / "RANKING_BUILD_METRICS.json")
    new_ranking = read_json(new_snapshot / "RANKING_BUILD_METRICS.json")
    commander_summary = read_json(new_snapshot / "commander_cleanup_summary.json")
    commander_audit = read_json(new_snapshot / "commander_postfix_audit" / "summary.json")
    dashboard_qa = read_json(new_snapshot / "dashboard_qa_summary.json")

    old_summary = read_csv(old_snapshot / "TOP_COMMANDERS_SUMMARY.csv")
    new_summary = read_csv(new_snapshot / "TOP_COMMANDERS_SUMMARY.csv")
    old_classification = numeric(
        read_csv(old_snapshot / "TOP_TIER_CLASSIFICATION.csv"),
        ["best_rank", "mean_rank", "rank_range", "top10_appearances", "top25_appearances"],
    )
    new_classification = numeric(
        read_csv(new_snapshot / "TOP_TIER_CLASSIFICATION.csv"),
        ["best_rank", "mean_rank", "rank_range", "top10_appearances", "top25_appearances"],
    )

    old_annotated = read_csv(old_snapshot / "derived_scoring" / "commander_engagements_annotated.csv")
    new_annotated = read_csv(new_snapshot / "derived_scoring" / "commander_engagements_annotated.csv")

    summary_numeric = numeric(
        new_summary.copy(),
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

    write_text(
        new_snapshot / "SCORING_FRAMEWORK.md",
        generate_scoring_framework(new_snapshot, new_scoring, commander_summary, commander_audit),
    )
    write_text(
        new_snapshot / "ANALYTICAL_TABLES_SPEC.md",
        generate_analytical_tables_spec(new_snapshot, new_snapshot / "derived_scoring"),
    )
    write_text(
        new_snapshot / "SCORING_READINESS_REPORT.md",
        generate_scoring_readiness_report(new_snapshot, new_scoring),
    )
    write_text(
        new_snapshot / "RANKING_COMPARISON_REPORT.md",
        generate_ranking_comparison_report(new_snapshot, new_classification),
    )
    write_text(
        new_snapshot / "TOP_COMMANDERS_PROFILES.md",
        generate_top_commander_profiles(new_snapshot, new_classification, summary_numeric),
    )

    prepared, _, _, _, _ = prepare_rows(new_snapshot)
    unknown_rows = prepared[prepared["outcome_category"].eq("unknown")]
    validation = {
        "unknown_rows": int(len(unknown_rows)),
        "unknown_split_violations": int((unknown_rows["outcome_factor_split"] != 0.0).sum()),
    }

    write_text(
        new_snapshot / "RANKING_FIX_IMPLEMENTATION_REPORT.md",
        build_impl_report(old_snapshot, new_snapshot, old_annotated, new_annotated, validation),
    )
    write_text(
        new_snapshot / "POST_FIX_RANKING_IMPACT_REPORT.md",
        build_impact_report(
            old_snapshot,
            new_snapshot,
            old_scoring,
            new_scoring,
            old_ranking,
            new_ranking,
            old_summary,
            new_summary,
            old_classification,
            new_classification,
            dashboard_qa,
        ),
    )


if __name__ == "__main__":
    main()
