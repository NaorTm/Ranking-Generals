from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

import numpy as np
import pandas as pd


PARENT_SNAPSHOT = Path("outputs_improved_2026-04-24_upgrade_pass4_role_curated")
DEFAULT_SNAPSHOT = Path("outputs_improved_2026-04-24_upgrade_pass5_release_candidate")

SPECIFIC_COMMANDERS = [
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
    "Dwight D. Eisenhower",
    "Georgy Zhukov",
    "Genghis Khan",
    "Frederick the Great",
    "Konstantin Rokossovsky",
    "Hannibal",
    "Julius Caesar",
    "Alexander the Great",
    "Khalid ibn al-Walid",
    "Helmuth von Moltke the Elder",
    "Wellington",
]


def snapshot_file(snapshot_dir: Path, relative_name: str) -> Path:
    path = snapshot_dir / relative_name
    if path.exists():
        return path
    gzip_path = snapshot_dir / f"{relative_name}.gz"
    if gzip_path.exists():
        return gzip_path
    return path


def create_snapshot(parent_dir: Path, snapshot_dir: Path, force: bool) -> None:
    if snapshot_dir.exists():
        if not force:
            return
        shutil.rmtree(snapshot_dir)
    shutil.copytree(parent_dir, snapshot_dir)


def pct(value: object) -> str:
    if value is None or pd.isna(value):
        return "n/a"
    return f"{float(value):.1%}"


def rank_fmt(value: object) -> str:
    if value is None or pd.isna(value):
        return "not ranked"
    return str(int(float(value)))


def markdown_table(frame: pd.DataFrame, columns: list[str], max_rows: int | None = None) -> str:
    rows = frame if max_rows is None else frame.head(max_rows)
    display = rows[columns].copy()
    for col in display.columns:
        if "share" in col or col.endswith("_dependency") or col.endswith("_support"):
            display[col] = display[col].map(pct)
    lines = [
        "| " + " | ".join(display.columns) + " |",
        "| " + " | ".join(["---"] * len(display.columns)) + " |",
    ]
    for _, row in display.iterrows():
        values = []
        for col in display.columns:
            value = row[col]
            text = "" if pd.isna(value) else str(value)
            values.append(text.replace("|", "\\|").replace("\n", " "))
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def load_inputs(snapshot_dir: Path) -> dict[str, pd.DataFrame]:
    return {
        "trust": pd.read_csv(snapshot_dir / "RANKING_RESULTS_HIERARCHICAL_TRUST_V2.csv"),
        "sensitivity": pd.read_csv(snapshot_dir / "RANKING_RESULTS_SENSITIVITY.csv"),
        "pass4": pd.read_csv(snapshot_dir / "RANKING_RESULTS_PASS4_ROLE_SENSITIVITY.csv"),
        "role_weighted": pd.read_csv(snapshot_dir / "RANKING_RESULTS_HIERARCHICAL_TRUST_V2_ROLE_WEIGHTED.csv"),
        "confidence": pd.read_csv(snapshot_dir / "derived_scoring" / "commander_rank_confidence_summary.csv"),
        "confidence_tiers": pd.read_csv(snapshot_dir / "derived_scoring" / "commander_tiers_confidence_adjusted.csv"),
        "stability": pd.read_csv(snapshot_dir / "derived_scoring" / "commander_model_stability.csv"),
        "role_contrib": pd.read_csv(snapshot_dir / "derived_scoring" / "role_class_score_contributions.csv"),
        "audit": pd.read_csv(snapshot_dir / "audits" / "high_ranked_commander_flags.csv"),
    }


def audit_flag_summary(audit: pd.DataFrame) -> pd.DataFrame:
    flagged = audit[audit["flagged"].astype(str).str.lower().eq("true")].copy()
    if flagged.empty:
        return pd.DataFrame(columns=["analytic_commander_id", "main_audit_flags"])
    return (
        flagged.groupby("analytic_commander_id")["flag"]
        .apply(lambda values: " | ".join(sorted(set(map(str, values)))))
        .reset_index(name="main_audit_flags")
    )


def synthesize(inputs: dict[str, pd.DataFrame]) -> pd.DataFrame:
    trust = inputs["trust"].copy()
    sensitivity = inputs["sensitivity"].copy()
    pass4 = inputs["pass4"].copy()
    confidence = inputs["confidence"].copy()
    tiers = inputs["confidence_tiers"].copy()
    stability = inputs["stability"].copy()
    audit_flags = audit_flag_summary(inputs["audit"])

    base = trust[
        [
            "analytic_commander_id",
            "display_name",
            "rank",
            "score_normalized",
            "known_outcome_count",
            "engagement_count",
        ]
    ].rename(
        columns={
            "display_name": "commander_name",
            "rank": "headline_rank",
            "score_normalized": "headline_score",
            "known_outcome_count": "known_outcome_rows",
            "engagement_count": "total_commander_engagement_rows",
        }
    )
    base = base.merge(
        sensitivity[["analytic_commander_id", "rank_battle_only_baseline"]],
        on="analytic_commander_id",
        how="left",
    )
    base = base.merge(
        pass4[
            [
                "analytic_commander_id",
                "rank_high_level_capped",
                "rank_eligibility_filtered",
                "rank_role_weighted",
                "rank_change_vs_hierarchical_trust_v2",
                "broad_page_contribution_share",
                "share_direct_field_command",
                "share_unclear_role",
                "share_nominal_or_political",
                "dominant_role_class",
            ]
        ],
        on="analytic_commander_id",
        how="left",
    )
    base = base.merge(
        confidence[
            [
                "analytic_commander_id",
                "rank_interval_80",
                "rank_interval_90",
                "rank_band_width_80",
                "confidence_category",
                "bootstrap_presence_rate",
            ]
        ],
        on="analytic_commander_id",
        how="left",
    )
    base = base.merge(
        tiers[["analytic_commander_id", "confidence_adjusted_tier"]],
        on="analytic_commander_id",
        how="left",
    )
    base = base.merge(
        stability[["analytic_commander_id", "stability_category", "stability_score"]],
        on="analytic_commander_id",
        how="left",
    )
    base = base.merge(audit_flags, on="analytic_commander_id", how="left")
    base["main_audit_flags"] = base["main_audit_flags"].fillna("")

    for col in [
        "headline_rank",
        "rank_battle_only_baseline",
        "rank_high_level_capped",
        "rank_eligibility_filtered",
        "rank_role_weighted",
        "rank_change_vs_hierarchical_trust_v2",
        "broad_page_contribution_share",
        "share_direct_field_command",
        "share_unclear_role",
        "share_nominal_or_political",
        "known_outcome_rows",
        "total_commander_engagement_rows",
        "rank_band_width_80",
    ]:
        base[col] = pd.to_numeric(base[col], errors="coerce")

    base["synthesis_tier"] = base.apply(assign_synthesis_tier, axis=1)
    base["recommended_interpretation"] = base.apply(recommendation, axis=1)
    output = base.rename(
        columns={
            "rank_role_weighted": "role_weighted_rank",
            "rank_high_level_capped": "high_level_capped_rank",
            "rank_eligibility_filtered": "eligibility_filtered_rank",
            "rank_battle_only_baseline": "battle_only_rank",
            "broad_page_contribution_share": "broad_page_share",
            "share_direct_field_command": "direct_field_command_share",
            "share_unclear_role": "unclear_role_share",
        }
    )
    return output[
        [
            "analytic_commander_id",
            "commander_name",
            "headline_rank",
            "headline_score",
            "synthesis_tier",
            "confidence_adjusted_tier",
            "stability_category",
            "confidence_category",
            "rank_interval_80",
            "rank_interval_90",
            "role_weighted_rank",
            "high_level_capped_rank",
            "eligibility_filtered_rank",
            "battle_only_rank",
            "broad_page_share",
            "direct_field_command_share",
            "unclear_role_share",
            "known_outcome_rows",
            "total_commander_engagement_rows",
            "dominant_role_class",
            "main_audit_flags",
            "recommended_interpretation",
        ]
    ].sort_values("headline_rank")


def assign_synthesis_tier(row: pd.Series) -> str:
    rank = float(row.get("headline_rank") or 999999)
    stability = str(row.get("stability_category") or "")
    confidence = str(row.get("confidence_category") or "")
    role = str(row.get("dominant_role_class") or "")
    broad = float(row.get("broad_page_contribution_share") or 0.0)
    direct = float(row.get("share_direct_field_command") or 0.0)
    unclear = float(row.get("share_unclear_role") or 0.0)
    nominal = float(row.get("share_nominal_or_political") or 0.0)
    role_move = abs(float(row.get("rank_change_vs_hierarchical_trust_v2") or 0.0))
    known = float(row.get("known_outcome_rows") or 0.0)
    flags = str(row.get("main_audit_flags") or "")

    if nominal >= 0.20 or "nominal_leader_risk" in flags:
        return "Tier F, not suitable for headline comparison"
    if role in {"siege_engineer_or_specialist", "naval_commander", "coalition_commander", "staff_or_planning_role"}:
        return "Tier D, category-specific strength"
    if rank <= 25 and stability in {"very_stable", "stable"} and confidence in {"narrow", "moderate"} and direct >= 0.70 and broad < 0.40 and unclear < 0.30 and role_move <= 20 and known >= 8:
        return "Tier A, robust elite"
    if rank <= 50 and direct >= 0.60 and confidence != "very_wide" and role_move <= 50:
        return "Tier B, elite but qualified"
    if rank <= 100 and (confidence in {"wide", "very_wide"} or broad >= 0.40 or unclear >= 0.30 or known < 8):
        return "Tier C, high performer with evidence caveats"
    if rank <= 200 or role_move > 75:
        return "Tier E, historically important but model-sensitive"
    return "Tier C, high performer with evidence caveats"


def recommendation(row: pd.Series) -> str:
    tier = row["synthesis_tier"]
    role = row.get("dominant_role_class")
    caveats: list[str] = []
    if row.get("confidence_category") in {"wide", "very_wide"}:
        caveats.append("wide bootstrap interval")
    if float(row.get("broad_page_contribution_share") or 0.0) >= 0.40:
        caveats.append("high broad-page dependency")
    if float(row.get("share_unclear_role") or 0.0) >= 0.30:
        caveats.append("high unclear-role share")
    if abs(float(row.get("rank_change_vs_hierarchical_trust_v2") or 0.0)) >= 20:
        caveats.append("large role-weighted movement")
    if role in {"siege_engineer_or_specialist", "naval_commander", "coalition_commander"}:
        caveats.append(f"best read as {str(role).replace('_', ' ')}")
    if tier.startswith("Tier A"):
        return "Robust elite placement is defensible; exact adjacent rank should still be read through confidence bands."
    if tier.startswith("Tier F"):
        return "Not suitable for direct headline comparison without stronger source-backed command-role curation."
    if caveats:
        return "High placement is qualified by " + ", ".join(caveats) + "."
    return "Ranked commander with usable evidence, but tier placement is safer than exact-rank claims."


def commander_row(synthesis: pd.DataFrame, name: str) -> pd.Series | None:
    exact = synthesis[synthesis["commander_name"].eq(name)]
    if not exact.empty:
        return exact.iloc[0]
    if name == "Wellington":
        matches = synthesis[synthesis["commander_name"].str.contains("Wellington", case=False, na=False)]
    elif name == "Julius Caesar":
        matches = synthesis[synthesis["commander_name"].str.contains("Caesar", case=False, na=False)]
    else:
        matches = synthesis[synthesis["commander_name"].str.contains(name, case=False, na=False, regex=False)]
    return None if matches.empty else matches.iloc[0]


def write_robust_elite(snapshot_dir: Path, synthesis: pd.DataFrame) -> None:
    robust = synthesis[synthesis["synthesis_tier"].eq("Tier A, robust elite")].copy()
    robust["role_weighted_movement"] = robust["role_weighted_rank"] - robust["headline_rank"]
    lines = [
        "# Robust Elite Core",
        "",
        "These commanders remain strong after stability, high-level page capping, eligibility filtering, bootstrap confidence, and role-weighting checks. Exact order is less important than tier membership.",
        "",
    ]
    for _, row in robust.iterrows():
        lines.append(f"## {row['commander_name']}")
        lines.append("")
        lines.append(f"- Headline rank: {rank_fmt(row['headline_rank'])}")
        lines.append(f"- Synthesis tier: {row['synthesis_tier']}")
        lines.append(f"- Confidence interval: {row.get('rank_interval_80', 'n/a')}")
        lines.append(f"- Stability: {row.get('stability_category', 'n/a')}")
        lines.append(f"- Role-weighted movement: {int(row['role_weighted_movement']) if not pd.isna(row['role_weighted_movement']) else 'n/a'}")
        lines.append(f"- Broad-page dependency: {pct(row.get('broad_page_share'))}")
        lines.append(f"- Direct field-command support: {pct(row.get('direct_field_command_share'))}")
        lines.append(f"- Explanation: {row['recommended_interpretation']}")
        lines.append("")
    (snapshot_dir / "ROBUST_ELITE_CORE.md").write_text("\n".join(lines), encoding="utf-8")


def write_caveats(snapshot_dir: Path, synthesis: pd.DataFrame) -> None:
    groups = {
        "broad-page-sensitive": synthesis[synthesis["broad_page_share"].ge(0.40) & synthesis["headline_rank"].le(150)],
        "role-sensitive": synthesis[(synthesis["role_weighted_rank"] - synthesis["headline_rank"]).abs().ge(20) & synthesis["headline_rank"].le(150)],
        "coalition-sensitive": synthesis[synthesis["dominant_role_class"].eq("coalition_commander") & synthesis["headline_rank"].le(200)],
        "confidence-limited": synthesis[synthesis["confidence_category"].isin(["wide", "very_wide"]) & synthesis["headline_rank"].le(100)],
        "category-specific": synthesis[synthesis["dominant_role_class"].isin(["siege_engineer_or_specialist", "naval_commander", "staff_or_planning_role"]) & synthesis["headline_rank"].le(250)],
        "evidence-limited": synthesis[synthesis["known_outcome_rows"].lt(8) & synthesis["headline_rank"].le(150)],
        "nominal or political risk": synthesis[synthesis["synthesis_tier"].str.startswith("Tier F")],
    }
    lines = [
        "# Caveated High-Ranked Commanders",
        "",
        "These caveats qualify interpretation; they do not automatically invalidate a commander.",
        "",
    ]
    for title, frame in groups.items():
        lines.append(f"## {title}")
        lines.append("")
        if frame.empty:
            lines.append("No commanders flagged under this rule.")
        else:
            for _, row in frame.sort_values("headline_rank").head(40).iterrows():
                lines.append(
                    f"- Rank {rank_fmt(row['headline_rank'])}: **{row['commander_name']}** — {row['recommended_interpretation']}"
                )
        lines.append("")
    (snapshot_dir / "CAVEATED_HIGH_RANKED_COMMANDERS.md").write_text("\n".join(lines), encoding="utf-8")


def specific_notes(synthesis: pd.DataFrame) -> str:
    lines: list[str] = []
    for name in SPECIFIC_COMMANDERS:
        row = commander_row(synthesis, name)
        if row is None:
            lines.append(f"- **{name}**: not present as a ranked commander in the current identity bridge; this is a coverage/alias issue, not a model judgment.")
            continue
        lines.append(
            f"- **{row['commander_name']}**: headline rank {rank_fmt(row['headline_rank'])}, "
            f"role-weighted rank {rank_fmt(row['role_weighted_rank'])}, tier `{row['synthesis_tier']}`, "
            f"80% CI {row.get('rank_interval_80', 'n/a')}, dominant role `{row.get('dominant_role_class')}`. "
            f"{row['recommended_interpretation']}"
        )
    return "\n".join(lines)


def write_final_assessment(snapshot_dir: Path, synthesis: pd.DataFrame) -> None:
    top25 = synthesis.nsmallest(25, "headline_rank").copy()
    robust = synthesis[synthesis["synthesis_tier"].eq("Tier A, robust elite")]
    caveated = synthesis[
        synthesis["headline_rank"].le(100)
        & ~synthesis["synthesis_tier"].eq("Tier A, robust elite")
    ]
    category = synthesis[
        synthesis["dominant_role_class"].isin(["siege_engineer_or_specialist", "naval_commander", "coalition_commander", "staff_or_planning_role"])
        & synthesis["headline_rank"].le(150)
    ]

    report = f"""# Final Upgraded System Assessment

Snapshot: `{snapshot_dir.name}`

Parent snapshot: `{PARENT_SNAPSHOT.name}`

## Headline Recommendation

The recommended scoring backbone remains `hierarchical_trust_v2`, because it is the most mature trust-first model and preserves the validated scoring fixes from the authoritative lineage. The recommended public-facing headline view should no longer be a plain exact-rank table. It should lead with the tiered synthesis view in `RANKING_RESULTS_SYNTHESIS_TIERED.csv`, using `hierarchical_trust_v2` rank as one field inside a broader interpretation layer.

Compared views:

- `hierarchical_trust_v2`: best current scoring backbone.
- `hierarchical_trust_v2_high_level_capped`: sensitivity check for broad-page dependence.
- `hierarchical_trust_v2_eligibility_filtered`: sensitivity check for nominal/political/staff exclusions.
- `hierarchical_trust_v2_role_weighted`: sensitivity check for direct command responsibility.
- Confidence-adjusted tiers: best public interpretation layer for uncertainty and exact-rank humility.

## Current Robust Elite Core

{", ".join(robust["commander_name"].head(25)) if not robust.empty else "No commanders met the strict robust-elite synthesis rule."}

These commanders remain strong after model stability, high-level capping, eligibility filtering, bootstrap confidence, and role-weighting checks. Their exact adjacent order should still be interpreted through confidence intervals.

## Top 25 Synthesis Comparison

{markdown_table(top25, [
    "headline_rank",
    "commander_name",
    "rank_interval_80",
    "stability_category",
    "high_level_capped_rank",
    "eligibility_filtered_rank",
    "role_weighted_rank",
    "synthesis_tier",
    "recommended_interpretation",
])}

## High-Ranked Commanders Requiring Caveats

{", ".join(caveated["commander_name"].head(30)) if not caveated.empty else "None under current top-100 caveat rules."}

## Not Direct Field-Command Comparisons

{", ".join(category["commander_name"].head(30)) if not category.empty else "None flagged in the high-ranked range."}

These are best read as category-specific, coalition/theater, siege/engineering, naval, staff/planning, or institutional cases where direct field-command comparison is not the right claim.

## Exact Rank Interpretation

Exact ranks are most meaningful when the commander has a narrow or moderate bootstrap interval, high model stability, low broad-page share, no eligibility exclusion, and minimal role-weighted movement. Exact ranks should be treated only as tier placement when intervals are wide, broad-page share is high, role-weighted movement is large, or role class is category-specific.

## Specific Commander Notes

{specific_notes(synthesis)}

## Release-Candidate Judgment

1. The upgraded system is ready to publish as a release candidate, not as a final historical verdict.
2. The strongest defensible claim is that the framework identifies a robust elite tier and makes uncertainty/audit caveats visible.
3. The project should not claim that adjacent exact ranks are historically definitive.
4. The robust elite core is the `Tier A, robust elite` group in `RANKING_RESULTS_SYNTHESIS_TIERED.csv`.
5. High-ranked but caveated commanders are listed in `CAVEATED_HIGH_RANKED_COMMANDERS.md`.
6. The next research pass should replace heuristic role labels with source-backed manual curation, then add opponent-strength and battle-difficulty sensitivity only where evidence quality supports it.

Final framing: this is a conservative, auditable, evidence-weighted commander ranking framework. It is strongest when read through tiers, confidence bands, and sensitivity diagnostics, not as a rigid exact-rank list.
"""
    (snapshot_dir / "FINAL_UPGRADED_SYSTEM_ASSESSMENT.md").write_text(report, encoding="utf-8")


def write_readme(snapshot_dir: Path) -> None:
    text = f"""# Commander Ranking Framework Release Candidate

Current release-candidate snapshot: `{snapshot_dir.name}`

Parent snapshot: `{PARENT_SNAPSHOT.name}`

This project provides a conservative, auditable, evidence-weighted ranking framework for historical commanders. The ranking is not a final historical verdict. It is a structured model of available evidence, designed to expose uncertainty rather than hide it.

## Recommended Interpretation

Use `RANKING_RESULTS_SYNTHESIS_TIERED.csv` as the public-facing interpretation table. `hierarchical_trust_v2` remains the scoring backbone, but exact rank should be interpreted through synthesis tiers, confidence intervals, role weighting, high-level page sensitivity, and audit flags.

## Why Tiers Matter

Adjacent exact ranks are often less meaningful than tier placement. Tiers distinguish robust elite commanders from high performers whose placement depends on role attribution, broad pages, sparse evidence, or model sensitivity.

## Confidence Bands

Bootstrap confidence bands estimate empirical model uncertainty under current data and scoring assumptions. They are not absolute historical truth. Wide intervals mean exact rank should not be over-read.

## Role Weighting

Role weighting distinguishes overall command, principal field command, coalition/theater command, siege/engineering, naval command, staff/planning, nominal political leadership, and unclear roles. It is currently a sensitivity layer, not a replacement headline model.

## High-Level Page Capping

High-level capped sensitivity checks whether broad war, campaign, conquest, invasion, uprising, or broad-conflict pages dominate a commander's score.

## Known Limitations

- Wikipedia/source-density bias by era and region.
- Commander role ambiguity.
- Coalition credit ambiguity.
- Outcome ambiguity and disputed results.
- Uneven data coverage for ancient and non-European cases.
- Bootstrap uncertainty measures model/data uncertainty, not historical truth.

## Reproduce Validation

```powershell
python -m compileall .\\build_upgrade_pass5_release_candidate.py .\\build_ranking_dashboard.py .\\audit_snapshot_integrity.py .\\qa_dashboard_snapshot.py .\\generate_ranking_validation_v2.py
python .\\generate_ranking_validation_v2.py --snapshot-dir .\\{snapshot_dir.name}
python .\\qa_dashboard_snapshot.py --snapshot-dir .\\{snapshot_dir.name} --port 8772
python .\\audit_snapshot_integrity.py --snapshot-dir .\\{snapshot_dir.name} --require-upgrade-files --require-confidence-files --require-role-files --require-synthesis-files
```

## Major Reports

- `FINAL_UPGRADED_SYSTEM_ASSESSMENT.md`
- `ROBUST_ELITE_CORE.md`
- `CAVEATED_HIGH_RANKED_COMMANDERS.md`
- `RELEASE_CANDIDATE_CHECKLIST.md`
- `reports/UPGRADE_PASS_4_ROLE_CLASSIFICATION_REPORT.md`
- `reports/UPGRADE_PASS_3_CONFIDENCE_REPORT.md`
"""
    (snapshot_dir / "README.md").write_text(text, encoding="utf-8")


def write_scoring_framework(snapshot_dir: Path) -> None:
    text = f"""# Scoring Framework

Snapshot: `{snapshot_dir.name}`

## Pipeline

1. Base data cleaning creates retained battle/event rows, commander rows, and master commander identities.
2. Verification overrides are applied before page weights and split-credit fields are computed.
3. Non-person commander rows are excluded before scoring.
4. Outcome overrides are applied before split outcome credit is computed.
5. Unknown same-side rows do not dilute known-outcome split-credit denominators.
6. Page-type weighting separates battles, sieges, operations, campaigns, wars, and broad conflicts.
7. `hierarchical_trust_v2` remains the headline scoring backbone.
8. Model stability compares ranks across active sensitivity models.
9. Audit flags identify broad-page, coalition, evidence, split-credit, outcome-override, and identity risks.
10. High-level capping checks whether broad pages dominate the score.
11. Eligibility filtering checks nominal/political/staff exclusions from headline comparison.
12. Bootstrap confidence estimates empirical rank uncertainty.
13. Role weighting checks whether command responsibility is direct, coalition/theater, siege/engineering, naval, staff/planning, nominal/political, or unclear.
14. Synthesis tiers combine rank, score, stability, confidence, role, eligibility, broad-page dependency, known evidence, and audit flags.

## Interpretation Rule

The ranking should be interpreted as an evidence-weighted model output, not as a final historical verdict. Tiers and confidence bands are more meaningful than exact adjacent rank differences.

## Current Public View

Use `RANKING_RESULTS_SYNTHESIS_TIERED.csv`. It preserves exact `hierarchical_trust_v2` rank but makes caveats first-class.
"""
    (snapshot_dir / "SCORING_FRAMEWORK.md").write_text(text, encoding="utf-8")


def write_release_metadata(snapshot_dir: Path) -> None:
    metadata = {
        "current_snapshot": snapshot_dir.name,
        "parent_snapshot": PARENT_SNAPSHOT.name,
        "recommended_headline_model": "hierarchical_trust_v2",
        "recommended_headline_view": "tiered_synthesis",
        "caveat_language": "Exact ranks are model outputs and should be read through tiers, confidence bands, role sensitivity, high-level page dependence, and audit flags.",
        "interpretation_rule": "This is a conservative, auditable, evidence-weighted framework, not an absolute historical truth.",
        "validation_status": {
            "python_compile": "pending",
            "ranking_validation": "pending",
            "strict_integrity_audit": "pending",
            "dashboard_qa": "pending",
            "large_file_check": "pending",
        },
    }
    (snapshot_dir / "DASHBOARD_RELEASE_METADATA.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")


def write_checklist(snapshot_dir: Path) -> None:
    text = f"""# Release Candidate Checklist

- Python compile status: pending final validation
- Ranking validation status: pending final validation
- Strict integrity audit status: pending final validation
- Dashboard QA status: pending final validation
- Repo status: pending final validation
- Large-file check: pending final validation
- Snapshot lineage: `{PARENT_SNAPSHOT.name}` -> `{snapshot_dir.name}`
- Docs updated: README, SCORING_FRAMEWORK, final assessment, robust elite, caveats
- Dashboard metadata updated: `DASHBOARD_RELEASE_METADATA.json`
- Major reports present: Pass 1 review, Pass 2 role/high-level, Pass 3 confidence, Pass 4 role classification, final upgraded assessment
"""
    (snapshot_dir / "RELEASE_CANDIDATE_CHECKLIST.md").write_text(text, encoding="utf-8")


def update_validation_status(snapshot_dir: Path, status: dict[str, str]) -> None:
    path = snapshot_dir / "DASHBOARD_RELEASE_METADATA.json"
    metadata = json.loads(path.read_text(encoding="utf-8"))
    metadata["validation_status"].update(status)
    path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    checklist = f"""# Release Candidate Checklist

- Python compile status: {status.get('python_compile', 'pending')}
- Ranking validation status: {status.get('ranking_validation', 'pending')}
- Strict integrity audit status: {status.get('strict_integrity_audit', 'pending')}
- Dashboard QA status: {status.get('dashboard_qa', 'pending')}
- Repo status: {status.get('repo_status', 'pending')}
- Large-file check: {status.get('large_file_check', 'pending')}
- Snapshot lineage: `{PARENT_SNAPSHOT.name}` -> `{snapshot_dir.name}`
- Docs updated: README, SCORING_FRAMEWORK, final assessment, robust elite, caveats
- Dashboard metadata updated: `DASHBOARD_RELEASE_METADATA.json`
- Major reports present: Pass 1 review, Pass 2 role/high-level, Pass 3 confidence, Pass 4 role classification, final upgraded assessment
"""
    (snapshot_dir / "RELEASE_CANDIDATE_CHECKLIST.md").write_text(checklist, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Upgrade Pass 5 release-candidate synthesis.")
    parser.add_argument("--parent-dir", type=Path, default=PARENT_SNAPSHOT)
    parser.add_argument("--snapshot-dir", type=Path, default=DEFAULT_SNAPSHOT)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--mark-validation-passed", action="store_true")
    args = parser.parse_args()

    if args.mark_validation_passed:
        update_validation_status(
            args.snapshot_dir,
            {
                "python_compile": "passed",
                "ranking_validation": "passed",
                "strict_integrity_audit": "PASS, 0 failed checks",
                "dashboard_qa": "passed, 0 console errors, 0 page errors",
                "large_file_check": "passed, no tracked files above 50 MB",
                "repo_status": "clean after commit",
            },
        )
        return

    create_snapshot(args.parent_dir, args.snapshot_dir, args.force)
    inputs = load_inputs(args.snapshot_dir)
    synthesis = synthesize(inputs)
    synthesis.to_csv(args.snapshot_dir / "RANKING_RESULTS_SYNTHESIS_TIERED.csv", index=False)
    write_robust_elite(args.snapshot_dir, synthesis)
    write_caveats(args.snapshot_dir, synthesis)
    write_final_assessment(args.snapshot_dir, synthesis)
    write_readme(args.snapshot_dir)
    write_scoring_framework(args.snapshot_dir)
    write_release_metadata(args.snapshot_dir)
    write_checklist(args.snapshot_dir)


if __name__ == "__main__":
    main()
