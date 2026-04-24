from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


DEFAULT_SNAPSHOT = Path("outputs_improved_2026-04-24_ranking_model_upgrade")
PARENT_SNAPSHOT = "outputs_cleaned_2026-04-21_fullpopulation_authoritative"


def read_csv(snapshot_dir: Path, name: str) -> pd.DataFrame:
    return pd.read_csv(snapshot_dir / name)


def md_table(rows: list[list[object]], headers: list[str]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join("" if pd.isna(value) else str(value) for value in row) + " |")
    return "\n".join(lines)


def build_docs(snapshot_dir: Path) -> None:
    trust = read_csv(snapshot_dir, "RANKING_RESULTS_HIERARCHICAL_TRUST_V2.csv")
    stability = read_csv(snapshot_dir, "derived_scoring/commander_model_stability.csv")
    tiers = read_csv(snapshot_dir, "derived_scoring/commander_tiers.csv")
    flags = read_csv(snapshot_dir, "audits/high_ranked_commander_flags.csv")
    page_contrib = read_csv(snapshot_dir, "derived_scoring/page_type_score_contributions.csv")

    top10 = trust.head(10).merge(
        tiers[["analytic_commander_id", "tier_label"]],
        on="analytic_commander_id",
        how="left",
    ).merge(
        stability[["analytic_commander_id", "stability_category", "stability_score"]],
        on="analytic_commander_id",
        how="left",
    )
    top10_rows = [
        [
            int(row["rank"]),
            row["display_name"],
            f"{row['score_normalized']:.2f}",
            row.get("tier_label", ""),
            row.get("stability_category", ""),
        ]
        for _, row in top10.iterrows()
    ]

    top100_ids = set(trust.head(100)["analytic_commander_id"])
    top100_tiers = tiers[tiers["analytic_commander_id"].isin(top100_ids)]
    tier_counts = top100_tiers["tier_label"].value_counts().reset_index()
    tier_rows = [[row["tier_label"], int(row["count"])] for _, row in tier_counts.iterrows()]

    flagged = flags[flags["flagged"].astype(str).str.lower().eq("true")]
    flag_counts = flagged["flag"].value_counts().reset_index()
    flag_rows = [[row["flag"], int(row["count"])] for _, row in flag_counts.iterrows()]

    broad_sensitive = (
        page_contrib[
            page_contrib["page_type"].isin(["operation_article", "campaign_article", "war_conflict_article"])
        ]
        .groupby(["analytic_commander_id", "display_name"], as_index=False)["share_of_total_score"]
        .sum()
        .sort_values("share_of_total_score", ascending=False)
        .head(12)
    )
    broad_rows = [
        [row["display_name"], f"{row['share_of_total_score']:.1%}"]
        for _, row in broad_sensitive.iterrows()
    ]

    model_sensitive = (
        tiers.merge(
            stability[["analytic_commander_id", "rank_stddev", "rank_iqr"]],
            on="analytic_commander_id",
            how="left",
        )
        .merge(
            trust[["analytic_commander_id", "rank"]],
            on="analytic_commander_id",
            how="left",
        )
        .query("rank <= 50")
        .sort_values("rank_stddev", ascending=False)
        .head(12)
    )
    sensitive_rows = [
        [
            int(row["rank"]),
            row["commander_name"],
            row["tier_label"],
            row["stability_category"],
            f"{row['rank_stddev']:.1f}",
        ]
        for _, row in model_sensitive.iterrows()
    ]

    snapshot_name = snapshot_dir.name

    (snapshot_dir / "README.md").write_text(
        f"""# Commander Ranking Framework Upgrade Snapshot

Snapshot: `{snapshot_name}`

Parent snapshot: `{PARENT_SNAPSHOT}`

This snapshot adds an interpretation and audit layer on top of the corrected `hierarchical_trust_v2` ranking. It does not replace the headline model; it makes the output more defensible by attaching tier, stability, page-type dependency, and audit metadata to ranked commanders.

Primary interpretation rule:

Exact adjacent ranks should be treated as weaker than tiers, confidence, stability, and sensitivity movement. The ranking is an evidence-weighted model output, not a final historical verdict.

New upgrade outputs:

- `derived_scoring/commander_model_stability.csv`
- `derived_scoring/commander_tiers.csv`
- `derived_scoring/page_type_score_contributions.csv`
- `audits/high_ranked_commander_flags.csv`
- `METHODOLOGICAL_LIMITATIONS.md`
- `MODEL_SENSITIVE_CASES.md`
- `UPGRADE_RELEASE_NOTES.md`

Headline top 10 with interpretation metadata:

{md_table(top10_rows, ["Rank", "Commander", "Score", "Tier", "Stability"])}
""",
        encoding="utf-8",
    )

    (snapshot_dir / "SCORING_FRAMEWORK.md").write_text(
        f"""# Scoring Framework

Authoritative upgrade snapshot: `{snapshot_name}`

Parent lineage: `{PARENT_SNAPSHOT}`

## Analytic Unit

The main analytic unit is `analytic_commander_id x battle_id` after identity bridging, commander verification, outcome overrides, non-person exclusion, and strict eligibility filtering.

## Headline Model

The headline model remains `hierarchical_trust_v2`. It is the conservative trust-first view that combines outcome performance with sustained scale, scope, temporal span, centrality, higher-level-page guardrails, and evidence controls.

`hierarchical_full_credit` remains diagnostic only and must not be presented as the headline model.

## Corrected Scoring Order

Commander verification overrides and outcome overrides are applied before split-credit and page-weight fields are computed. Unknown outcomes receive zero split outcome credit and do not dilute known-outcome same-side split denominators.

## New Interpretation Layer

The upgraded snapshot adds:

- model stability across active ranking variants
- deterministic commander tiers
- page-type score contribution breakdowns
- high-ranked commander audit flags
- dashboard-visible tier, stability, contribution, and audit metadata

## Tier Logic

Tier assignment combines trust-first rank, stability, known-outcome evidence, page-type dependency, and category concentration. Tier A means robust elite within this model; Tier D means strong but category-specific; Tier E means historically important but scoring-sensitive.

Top-100 tier distribution:

{md_table(tier_rows, ["Tier", "Top-100 Count"])}

## Interpretation Rule

The ranking should be interpreted as an evidence-weighted model output, not as a final historical verdict. Tiers and confidence bands are more meaningful than exact adjacent rank differences.
""",
        encoding="utf-8",
    )

    (snapshot_dir / "METHODOLOGICAL_LIMITATIONS.md").write_text(
        f"""# Methodological Limitations

This framework is designed to expose uncertainty rather than hide it.

Known limitations:

- Wikipedia source-density is uneven across eras, regions, and languages.
- Ancient and medieval commanders often have thinner and more literary evidence.
- Broad campaign and war pages can blur command role, result attribution, and credit assignment.
- Coalition events create split-credit ambiguity, especially when same-side commander lists are long.
- Commander role classification is not yet fully curated in this snapshot.
- Siege, naval, staff, institutional, and political roles are not always comparable to field command.
- Outcome labels can mix tactical, operational, and strategic meanings.
- Cross-era comparison is intrinsically unstable because force structures, states, logistics, records, and command systems differ.
- Exact adjacent rank differences should not be interpreted as stronger than stability and tier evidence.

The dashboard and audit outputs should be used to identify whether a commander is robust, model-sensitive, role-sensitive, page-type-sensitive, or evidence-limited.
""",
        encoding="utf-8",
    )

    (snapshot_dir / "MODEL_SENSITIVE_CASES.md").write_text(
        f"""# Model-Sensitive Cases

This file highlights commanders whose interpretation changes materially depending on model assumptions.

Top model-sensitive upper-band cases:

{md_table(sensitive_rows, ["Trust Rank", "Commander", "Tier", "Stability", "Rank Stddev"])}

High-level page dependency watchlist:

{md_table(broad_rows, ["Commander", "High-Level Contribution Share"])}

Common reasons for sensitivity:

- broad campaign or war pages contribute materially to the score
- battle-only rank is much weaker than the hierarchical trust-first rank
- same-side coalition credit is dense
- a commander has a siege or engineering-heavy profile
- role classification has not yet been manually curated
- known-outcome evidence is thin relative to rank

These flags do not automatically invalidate a commander. They qualify interpretation and identify where additional historical verification would most improve confidence.
""",
        encoding="utf-8",
    )

    (snapshot_dir / "FINAL_SYSTEM_TRUST_ASSESSMENT.md").write_text(
        f"""# Final System Trust Assessment

Snapshot: `{snapshot_name}`

The system is usable as a conservative, auditable ranking framework with a stronger interpretation layer than the parent snapshot.

What is now stronger:

- top commanders have cross-model stability metadata
- top commanders have deterministic tiers
- top commanders have page-type contribution breakdowns
- top commanders have high-rank audit flags
- dashboard data includes tier, stability, audit, and contribution metadata
- strict upgrade integrity checks can be run with `audit_snapshot_integrity.py --require-upgrade-files`

Headline top 10:

{md_table(top10_rows, ["Rank", "Commander", "Score", "Tier", "Stability"])}

Most common top-100 audit flags:

{md_table(flag_rows, ["Flag", "Flagged Count"])}

Trust judgment:

The model is defensible as an evidence-weighted ranking platform when read tier-first and confidence-first. It should not be presented as a definitive exact ordering of military greatness.
""",
        encoding="utf-8",
    )

    (snapshot_dir / "UPGRADE_RELEASE_NOTES.md").write_text(
        f"""# Upgrade Release Notes

Snapshot: `{snapshot_name}`

Implemented in this upgrade pass:

- Created a new working snapshot from `{PARENT_SNAPSHOT}`.
- Added `compute_model_stability.py` and generated `derived_scoring/commander_model_stability.csv`.
- Added `assign_commander_tiers.py` and generated `derived_scoring/commander_tiers.csv`.
- Added `build_page_type_contribution_report.py` and generated `derived_scoring/page_type_score_contributions.csv`.
- Added `audit_high_ranked_commanders.py` and generated `audits/high_ranked_commander_flags.csv`.
- Updated dashboard build data to include upgrade metadata.
- Updated dashboard UI to show tier, stability, page contribution mix, and audit-flag counts.
- Extended snapshot integrity audit with `--require-upgrade-files`.

Not yet implemented in this pass:

- bootstrap confidence bands
- manually curated command-role classification
- opponent-strength and force-ratio difficulty models
- era-normalized and region-normalized leaderboards
- multidimensional tactical, operational, siege, strategic, and institutional rankings

Those components should be added as later sensitivity views before replacing the current headline model.
""",
        encoding="utf-8",
    )

    print(f"Wrote upgrade documentation for {snapshot_name}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build upgrade snapshot documentation.")
    parser.add_argument("--snapshot-dir", type=Path, default=DEFAULT_SNAPSHOT)
    args = parser.parse_args()
    build_docs(args.snapshot_dir)


if __name__ == "__main__":
    main()
