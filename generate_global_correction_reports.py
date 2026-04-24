from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parent
OLD_SNAPSHOT = ROOT / "outputs_cleaned_2026-04-10_secondpass_authoritative"
NEW_SNAPSHOT = ROOT / "outputs_cleaned_2026-04-11_globaltrust_authoritative"


def load_csv(root: Path, name: str) -> pd.DataFrame:
    return pd.read_csv(root / name, dtype=str).fillna("")


def load_json(root: Path, name: str) -> dict[str, Any]:
    return json.loads((root / name).read_text(encoding="utf-8"))


def abs_link(path: Path, label: str | None = None) -> str:
    label = label or path.name
    return f"[{label}]({path.as_posix()})"


def bullet_lines(items: list[str]) -> list[str]:
    return [f"- {item}" for item in items]


def fmt_int(value: Any) -> str:
    try:
        return f"{int(value):,}"
    except Exception:
        return str(value)


def fmt_float(value: Any) -> str:
    try:
        return f"{float(value):.1f}"
    except Exception:
        return str(value)


def top_names(frame: pd.DataFrame, n: int = 10) -> list[str]:
    return frame.head(n)["display_name"].tolist()


def rank_lookup(frame: pd.DataFrame, column: str) -> dict[str, float]:
    subset = frame[["display_name", column]].copy()
    subset[column] = pd.to_numeric(subset[column], errors="coerce")
    subset = subset.dropna(subset=[column])
    return dict(zip(subset["display_name"], subset[column]))


def write_text(path: Path, text: str) -> None:
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def build_reports() -> None:
    old_scoring_metrics = load_json(OLD_SNAPSHOT / "derived_scoring", "scoring_build_metrics.json")
    new_scoring_metrics = load_json(NEW_SNAPSHOT / "derived_scoring", "scoring_build_metrics.json")
    old_ranking_metrics = load_json(OLD_SNAPSHOT, "RANKING_BUILD_METRICS.json")
    new_ranking_metrics = load_json(NEW_SNAPSHOT, "RANKING_BUILD_METRICS.json")
    new_dashboard_qa = load_json(NEW_SNAPSHOT, "dashboard_qa_summary.json")

    old_annotated = load_csv(OLD_SNAPSHOT / "derived_scoring", "commander_engagements_annotated.csv")
    new_annotated = load_csv(NEW_SNAPSHOT / "derived_scoring", "commander_engagements_annotated.csv")
    old_sensitivity = load_csv(OLD_SNAPSHOT, "RANKING_RESULTS_SENSITIVITY.csv")
    new_sensitivity = load_csv(NEW_SNAPSHOT, "RANKING_RESULTS_SENSITIVITY.csv")
    old_baseline = load_csv(OLD_SNAPSHOT, "RANKING_RESULTS_BASELINE.csv")
    new_baseline = load_csv(NEW_SNAPSHOT, "RANKING_RESULTS_BASELINE.csv")
    old_battle_only = load_csv(OLD_SNAPSHOT, "RANKING_RESULTS_BATTLE_ONLY.csv")
    new_battle_only = load_csv(NEW_SNAPSHOT, "RANKING_RESULTS_BATTLE_ONLY.csv")
    old_hier = load_csv(OLD_SNAPSHOT, "RANKING_RESULTS_HIERARCHICAL.csv")
    new_hier = load_csv(NEW_SNAPSHOT, "RANKING_RESULTS_HIERARCHICAL.csv")
    new_summary = load_csv(NEW_SNAPSHOT, "TOP_COMMANDERS_SUMMARY.csv")
    new_classification = load_csv(NEW_SNAPSHOT, "TOP_TIER_CLASSIFICATION.csv")
    new_bridge = load_csv(NEW_SNAPSHOT / "derived_scoring", "commander_identity_bridge.csv")
    new_excluded = load_csv(NEW_SNAPSHOT / "derived_scoring", "scoring_excluded_commander_rows.csv")
    new_eligibility = load_csv(NEW_SNAPSHOT / "derived_scoring", "engagement_eligibility.csv")
    new_features = load_csv(NEW_SNAPSHOT / "derived_scoring", "commander_ranking_features.csv")
    new_page_profile = load_csv(NEW_SNAPSHOT / "derived_scoring", "commander_page_type_profile.csv")
    new_outcome_profile = load_csv(NEW_SNAPSHOT / "derived_scoring", "commander_outcome_profile.csv")
    new_era_profile = load_csv(NEW_SNAPSHOT / "derived_scoring", "commander_era_profile.csv")
    new_opponent_profile = load_csv(NEW_SNAPSHOT / "derived_scoring", "commander_opponent_profile.csv")

    old_unknown = old_annotated["outcome_category"].eq("unknown").sum()
    new_unknown = new_annotated["outcome_category"].eq("unknown").sum()
    old_known = len(old_annotated) - old_unknown
    new_known = len(new_annotated) - new_unknown

    sanitized_rows = new_annotated.loc[new_annotated["scoring_result_source"].eq("sanitized_result_raw")].copy()
    sanitized_pages = sanitized_rows["battle_id"].nunique()
    sanitized_commanders = sanitized_rows["analytic_commander_id"].nunique()

    unknown_rows = new_annotated.loc[new_annotated["outcome_category"].eq("unknown")].copy()
    coalition_unknown = unknown_rows.loc[
        unknown_rows["scoring_result_raw"].str.contains(
            r"\b(?:coalition|allied|allies|alliance|combined|anti[- ])\b",
            case=False,
            regex=True,
            na=False,
        )
    ].copy()
    generic_victory_unknown = unknown_rows.loc[
        unknown_rows["scoring_result_raw"].str.fullmatch(r"(?i)victory")
    ].copy()
    generic_defeat_unknown = unknown_rows.loc[
        unknown_rows["scoring_result_raw"].str.fullmatch(r"(?i)defeat")
    ].copy()

    for column in ["rank", "higher_level_share", "known_outcome_share"]:
        new_hier[column] = pd.to_numeric(new_hier[column], errors="coerce")
    structural_risk = new_hier.loc[
        (new_hier["higher_level_share"] >= 0.5) & (new_hier["known_outcome_share"] < 0.4)
    ].copy()
    structural_risk_top100 = structural_risk.loc[structural_risk["rank"] <= 100].copy()

    old_baseline_rank = rank_lookup(old_sensitivity, "rank_baseline_conservative")
    new_baseline_rank = rank_lookup(new_sensitivity, "rank_baseline_conservative")
    old_battle_rank = rank_lookup(old_sensitivity, "rank_battle_only_baseline")
    new_battle_rank = rank_lookup(new_sensitivity, "rank_battle_only_baseline")
    old_hier_rank = rank_lookup(old_sensitivity, "rank_hierarchical_weighted")
    new_hier_rank = rank_lookup(new_sensitivity, "rank_hierarchical_weighted")

    suspicious_names = [
        "Qasem Soleimani",
        "Nelson A. Miles",
        "Suhayl al-Hasan",
        "William Halsey Jr.",
        "Idriss Déby",
        "Valery Gerasimov",
        "Flavius Aetius",
        "Petar Bojović",
    ]

    top_baseline_old = top_names(old_baseline)
    top_baseline_new = top_names(new_baseline)
    top_battle_old = top_names(old_battle_only)
    top_battle_new = top_names(new_battle_only)
    top_hier_old = top_names(old_hier)
    top_hier_new = top_names(new_hier)

    summary_lookup = new_summary.set_index("display_name").to_dict(orient="index")
    robust_names = new_classification.loc[
        new_classification["interpretive_group"].eq("robust_elite"), "display_name"
    ].tolist()
    strong_names = new_classification.loc[
        new_classification["interpretive_group"].eq("strong_but_model_sensitive"), "display_name"
    ].tolist()
    caution_names = new_classification.loc[
        new_classification["interpretive_group"].eq("caution_likely_artifact"), "display_name"
    ].tolist()

    def profile_section(names: list[str], title: str) -> list[str]:
        lines = [f"## {title}", ""]
        for name in names:
            row = summary_lookup.get(name)
            if not row:
                continue
            lines.extend(
                [
                    f"### {name}",
                    "",
                    f"- Snapshot: baseline `{row.get('rank_baseline_conservative', '') or 'NA'}`, battle-only `{row.get('rank_battle_only_baseline', '') or 'NA'}`, hierarchical `{row.get('rank_hierarchical_weighted', '') or 'NA'}`.",
                    f"- Why it matters: `{row.get('total_engagements_strict', '')}` strict engagements, `{row.get('total_battle_pages_strict', '')}` strict battle pages, `{row.get('distinct_conflicts_strict', '')}` distinct conflicts, `{row.get('known_outcome_count', '')}` known outcomes.",
                    f"- Exposure and caveats: `{row.get('page_type_exposure_summary', '')}`. `{row.get('outcome_profile_summary', '')}`. Stability `{row.get('stability_label', '')}`. {row.get('caution_flags', '') or 'No explicit caution flag.'}",
                    "",
                ]
            )
        return lines

    scoring_framework = "\n".join(
        [
            "# Scoring Framework",
            "",
            "## Scope",
            "",
            f"This scoring layer is synchronized to `{NEW_SNAPSHOT.name}` and supersedes `{OLD_SNAPSHOT.name}` for downstream ranking work.",
            "",
            "## Authoritative Inputs",
            "",
            f"- {abs_link(NEW_SNAPSHOT / 'battles_clean.csv')}",
            f"- {abs_link(NEW_SNAPSHOT / 'battle_commanders.csv')}",
            f"- {abs_link(NEW_SNAPSHOT / 'commanders_master.csv')}",
            f"- {abs_link(NEW_SNAPSHOT / 'derived_scoring' / 'scoring_excluded_commander_rows.csv')}",
            "",
            "## Core Rules",
            "",
            "- The analytic unit is one validated `analytic_commander_id x battle_id` row.",
            "- Unknown outcomes remain missing evidence in split-credit models, not denominator-weighted zeros.",
            "- Same-side outcome credit keeps the inherited `sqrt_same_side_split` rule.",
            "- This pass adds scoring-only sanitization for citation-fused page result text and excludes the last audited non-person identity leak.",
            "",
            "## Current Scale",
            "",
            f"- retained pages: `{fmt_int(new_scoring_metrics['source']['retained_pages'])}`",
            f"- commander rows entering scoring after exclusion: `{fmt_int(new_scoring_metrics['source']['commander_rows'])}`",
            f"- commander master rows entering scoring: `{fmt_int(new_scoring_metrics['source']['commander_master_rows'])}`",
            f"- identity bridge rows: `{fmt_int(new_scoring_metrics['derived']['identity_bridge_rows'])}`",
            f"- annotated commander-engagement rows: `{fmt_int(new_scoring_metrics['derived']['annotated_rows'])}`",
            f"- strict known-outcome rows: `{fmt_int(new_scoring_metrics['outcomes']['strict_known_outcome_rows'])}`",
            f"- default conservative ranking cohort: `{fmt_int(new_scoring_metrics['outcomes']['default_ranking_eligible_commanders'])}`",
            "",
            "## Bottom Line",
            "",
            f"The scoring layer in `{NEW_SNAPSHOT.name}` is the current authoritative foundation for ranking rebuilds.",
        ]
    )

    analytical_tables_spec = "\n".join(
        [
            "# Analytical Tables Spec",
            "",
            f"All derived scoring tables live under {abs_link(NEW_SNAPSHOT / 'derived_scoring', 'derived_scoring')}.",
            "",
            "## Table Notes",
            "",
            f"- `engagement_eligibility.csv`: {fmt_int(len(new_eligibility))} rows, one per page.",
            f"- `commander_identity_bridge.csv`: {fmt_int(len(new_bridge))} rows, one per analytic commander identity.",
            f"- `commander_engagements_annotated.csv`: {fmt_int(len(new_annotated))} rows, one per commander-page pair after dedupe.",
            f"- `commander_outcome_profile.csv`: {fmt_int(len(new_outcome_profile))} rows.",
            f"- `commander_page_type_profile.csv`: {fmt_int(len(new_page_profile))} rows.",
            f"- `commander_era_profile.csv`: {fmt_int(len(new_era_profile))} rows.",
            f"- `commander_opponent_profile.csv`: {fmt_int(len(new_opponent_profile))} rows.",
            f"- `commander_ranking_features.csv`: {fmt_int(len(new_features))} rows.",
            "",
            "## New Audit Columns",
            "",
            "- `scoring_result_raw`",
            "- `scoring_result_type`",
            "- `scoring_result_source`",
            "",
            "These make the scoring-stage outcome correction path auditable without rewriting source provenance.",
        ]
    )

    scoring_readiness = "\n".join(
        [
            "# Scoring Readiness Report",
            "",
            "## Current State",
            "",
            f"The scoring-stage foundation is built on `{NEW_SNAPSHOT.name}`.",
            "",
            f"- source retained pages: `{fmt_int(new_scoring_metrics['source']['retained_pages'])}`",
            f"- source commander rows after exclusion: `{fmt_int(new_scoring_metrics['source']['commander_rows'])}`",
            f"- source commander master rows after exclusion: `{fmt_int(new_scoring_metrics['source']['commander_master_rows'])}`",
            f"- strict-eligible pages: `{fmt_int(new_scoring_metrics['eligibility']['strict_included_pages'])}`",
            f"- balanced-eligible pages: `{fmt_int(new_scoring_metrics['eligibility']['balanced_included_pages'])}`",
            f"- annotated commander-engagement rows: `{fmt_int(new_scoring_metrics['derived']['annotated_rows'])}`",
            f"- default conservative ranking cohort: `{fmt_int(new_scoring_metrics['outcomes']['default_ranking_eligible_commanders'])}` commanders",
            "",
            "## This Pass Changed",
            "",
            f"- known outcome rows: `{fmt_int(old_known)}` -> `{fmt_int(new_known)}`",
            f"- unknown outcome rows: `{fmt_int(old_unknown)}` -> `{fmt_int(new_unknown)}`",
            f"- sanitized result fallback affected `{fmt_int(sanitized_pages)}` pages, `{fmt_int(len(sanitized_rows))}` commander rows, and `{fmt_int(sanitized_commanders)}` commanders",
            f"- scoring exclusions now remove `{fmt_int(len(new_excluded))}` confirmed non-person commander rows",
            "",
            "## Trust Judgment",
            "",
            "- `hierarchical_weighted` remains the most trustworthy single ranking model.",
            "- `baseline_conservative` is cleaner, but still battle-specialist heavy.",
            "- `hierarchical_full_credit` remains diagnostic, not definitive.",
        ]
    )

    ranking_comparison = "\n".join(
        [
            "# Ranking Comparison Report",
            "",
            f"This ranking package is built from `{NEW_SNAPSHOT.name}` and supersedes `{OLD_SNAPSHOT.name}`.",
            "",
            f"- baseline leader: `{new_ranking_metrics['top_baseline'][0]['display_name']}`",
            f"- battle-only leader: `{top_battle_new[0]}`",
            f"- hierarchical leader: `{new_ranking_metrics['top_hierarchical'][0]['display_name']}`",
            "",
            f"- baseline old top 10: `{', '.join(top_baseline_old)}`",
            f"- baseline new top 10: `{', '.join(top_baseline_new)}`",
            f"- hierarchical old top 10: `{', '.join(top_hier_old)}`",
            f"- hierarchical new top 10: `{', '.join(top_hier_new)}`",
            "",
            "The baseline moved materially after the scoring fix. The hierarchical leader did not change.",
        ]
    )

    top_profiles = "\n".join(
        [
            "# Top Commanders Profiles",
            "",
            f"This profile set is synchronized to `{NEW_SNAPSHOT.name}`.",
            "",
            *profile_section(robust_names[:8], "Robust Core"),
            *profile_section(strong_names[:8], "Strong But Model-Sensitive"),
            *profile_section(caution_names[:6], "Caution / Audit Cases"),
        ]
    )

    global_audit = "\n".join(
        [
            "# Global Ranking Trust Audit",
            "",
            f"This pass audited the full commander population in `{OLD_SNAPSHOT.name}` and rebuilt the affected analytics in `{NEW_SNAPSHOT.name}`.",
            "",
            "## Issue Families",
            "",
            f"- Confirmed global bug fixed: citation-fused result strings. Scope fixed: `{fmt_int(sanitized_pages)}` pages, `{fmt_int(len(sanitized_rows))}` commander rows, `{fmt_int(sanitized_commanders)}` commanders.",
            f"- Confirmed global data-quality fix: ranked non-person leakage. Scope fixed: `{fmt_int(len(new_excluded))}` excluded commander rows across `{fmt_int(new_excluded['battle_id'].nunique())}` battles.",
            f"- Residual coalition/allied ambiguity: `{fmt_int(len(coalition_unknown))}` commander rows on `{fmt_int(coalition_unknown['battle_id'].nunique())}` pages.",
            f"- Residual generic one-sided result strings: `{fmt_int(len(generic_victory_unknown) + len(generic_defeat_unknown))}` commander rows on `{fmt_int(generic_victory_unknown['battle_id'].nunique() + generic_defeat_unknown['battle_id'].nunique())}` page-level occurrences.",
            f"- Residual hierarchical structural risk: `{fmt_int(len(structural_risk))}` ranked commanders, including `{fmt_int(len(structural_risk_top100))}` in the top 100.",
            "",
            "## Judgment",
            "",
            "- Remaining problems are now mostly bounded ambiguity classes plus one still-open hierarchical design tradeoff.",
            "- The system is globally more trustworthy than the second-pass snapshot.",
        ]
    )

    implementation = "\n".join(
        [
            "# Global Correction Pass Report",
            "",
            "## Snapshot Lineage",
            "",
            f"- starting analytics snapshot: `{OLD_SNAPSHOT.name}`",
            f"- superseding analytics snapshot: `{NEW_SNAPSHOT.name}`",
            "",
            "## Logic Changed",
            "",
            "- `build_scoring_framework_package.py`: added scoring-only result-text sanitization and fallback outcome normalization.",
            "- `build_scoring_framework_package.py`: extended explicit non-person exclusion to remove `Al-Masdar News` from scoring and ranking inputs.",
            "- No ranking-formula rewrite was applied in this pass; the model layer was rebuilt on top of the corrected scoring outputs.",
            "",
            "## Rebuilt Outputs",
            "",
            *bullet_lines(
                [
                    abs_link(NEW_SNAPSHOT / "derived_scoring" / "commander_engagements_annotated.csv"),
                    abs_link(NEW_SNAPSHOT / "RANKING_RESULTS_BASELINE.csv"),
                    abs_link(NEW_SNAPSHOT / "RANKING_RESULTS_HIERARCHICAL.csv"),
                    abs_link(NEW_SNAPSHOT / "RANKING_RESULTS_SENSITIVITY.csv"),
                    abs_link(NEW_SNAPSHOT / "TOP_TIER_CLASSIFICATION.csv"),
                    abs_link(NEW_SNAPSHOT / "MODEL_SENSITIVITY_AUDIT.csv"),
                    abs_link(NEW_SNAPSHOT / "dashboard" / "dashboard_data.js"),
                    abs_link(NEW_SNAPSHOT / "dashboard_qa_summary.json"),
                ]
            ),
            "",
            "## Not Rebuilt",
            "",
            "- The battle and commander base CSVs were not re-extracted or replaced in this pass.",
        ]
    )

    impact_lines = [
        "# Global Ranking Impact Report",
        "",
        "## Population-Level Effect",
        "",
        f"- annotated commander-engagement rows: `{fmt_int(len(old_annotated))}` -> `{fmt_int(len(new_annotated))}`",
        f"- known-outcome rows: `{fmt_int(old_known)}` -> `{fmt_int(new_known)}`",
        f"- unknown-outcome rows: `{fmt_int(old_unknown)}` -> `{fmt_int(new_unknown)}`",
        f"- conservative baseline cohort: `{fmt_int(old_ranking_metrics['model_rows']['baseline_conservative'])}` -> `{fmt_int(new_ranking_metrics['model_rows']['baseline_conservative'])}`",
        f"- hierarchical cohort: `{fmt_int(old_ranking_metrics['model_rows']['hierarchical_weighted'])}` -> `{fmt_int(new_ranking_metrics['model_rows']['hierarchical_weighted'])}`",
        f"- dashboard ranked commanders: `{fmt_int(load_json(OLD_SNAPSHOT, 'dashboard_qa_summary.json')['expected']['commander_count'])}` -> `{fmt_int(new_dashboard_qa['expected']['commander_count'])}`",
        "",
        "## Leader Changes",
        "",
        f"- baseline leader: `{old_ranking_metrics['top_baseline'][0]['display_name']}` -> `{new_ranking_metrics['top_baseline'][0]['display_name']}`",
        f"- hierarchical leader: `{old_ranking_metrics['top_hierarchical'][0]['display_name']}` -> `{new_ranking_metrics['top_hierarchical'][0]['display_name']}`",
        "",
        "## Suspicious-Leader Movement",
        "",
    ]
    for name in suspicious_names:
        old_h = old_hier_rank.get(name)
        new_hv = new_hier_rank.get(name)
        old_b = old_battle_rank.get(name)
        new_b = new_battle_rank.get(name)
        if old_h is None and new_hv is None:
            continue
        impact_lines.append(
            f"- `{name}`: hierarchical `{fmt_float(old_h) if old_h is not None else 'NA'}` -> `{fmt_float(new_hv) if new_hv is not None else 'NA'}`; battle-only `{fmt_float(old_b) if old_b is not None else 'NA'}` -> `{fmt_float(new_b) if new_b is not None else 'NA'}`"
        )
    impact_lines.extend(
        [
            "",
            "## Model Trust Judgment",
            "",
            "- `hierarchical_weighted` is still the most trustworthy single model.",
            "- `baseline_conservative` improved, but remains battle-specialist heavy.",
            "- `hierarchical_full_credit` remains the least trustworthy ranking view.",
        ]
    )
    global_impact = "\n".join(impact_lines)

    residual_risks = "\n".join(
        [
            "# Residual Ranking Risks",
            "",
            f"- Coalition/allied ambiguity remains on `{fmt_int(len(coalition_unknown))}` commander rows across `{fmt_int(coalition_unknown['battle_id'].nunique())}` pages.",
            f"- Generic one-sided result strings remain on `{fmt_int(len(generic_victory_unknown) + len(generic_defeat_unknown))}` commander rows and are still not safely auto-resolved.",
            f"- High higher-level / low-evidence structural risk remains for `{fmt_int(len(structural_risk))}` ranked commanders, including `{', '.join(structural_risk_top100['display_name'].tolist())}` in the top 100.",
            "- Coverage imbalance across Wikipedia page density remains a real limitation.",
            "",
            "## What To Trust",
            "",
            "- The cleaned battle and commander layers.",
            "- The corrected scoring outputs in this snapshot.",
            "- The robust-elite interpretive group and the top hierarchical core.",
            "",
            "## What To Treat Cautiously",
            "",
            "- `hierarchical_full_credit` as a headline ranking source.",
            "- Exact ordering inside the model-sensitive band.",
            "- High-rank commanders already classified as `caution_likely_artifact`.",
        ]
    )

    write_text(NEW_SNAPSHOT / "SCORING_FRAMEWORK.md", scoring_framework)
    write_text(NEW_SNAPSHOT / "ANALYTICAL_TABLES_SPEC.md", analytical_tables_spec)
    write_text(NEW_SNAPSHOT / "SCORING_READINESS_REPORT.md", scoring_readiness)
    write_text(NEW_SNAPSHOT / "RANKING_COMPARISON_REPORT.md", ranking_comparison)
    write_text(NEW_SNAPSHOT / "TOP_COMMANDERS_PROFILES.md", top_profiles)
    write_text(NEW_SNAPSHOT / "GLOBAL_RANKING_TRUST_AUDIT.md", global_audit)
    write_text(NEW_SNAPSHOT / "GLOBAL_CORRECTION_PASS_REPORT.md", implementation)
    write_text(NEW_SNAPSHOT / "GLOBAL_RANKING_IMPACT_REPORT.md", global_impact)
    write_text(NEW_SNAPSHOT / "RESIDUAL_RANKING_RISKS.md", residual_risks)


if __name__ == "__main__":
    build_reports()
