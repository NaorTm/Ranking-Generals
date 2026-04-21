from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


SANITY_COMMANDERS = [
    "Napoleon Bonaparte",
    "Alexander Suvorov",
    "Jean Lannes",
    "Suleiman the Magnificent",
    "Louis-Nicolas Davout",
    "Khalid ibn al-Walid",
    "Douglas MacArthur",
    "Takeda Shingen",
]


NON_PERSON_TOKENS = [
    "news",
    "agency",
    "group",
    "mission",
    "media",
    "channel",
    "army",
    "wounded in action",
]


def load_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str).fillna("")


def to_numeric(df: pd.DataFrame, columns: list[str]) -> None:
    for column in columns:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate trust-first v2 validation outputs.")
    parser.add_argument("--snapshot-dir", type=Path, required=True)
    args = parser.parse_args()

    snapshot_dir = args.snapshot_dir
    summary = load_csv(snapshot_dir / "TOP_COMMANDERS_SUMMARY.csv")
    sensitivity = load_csv(snapshot_dir / "RANKING_RESULTS_SENSITIVITY.csv")
    trust = load_csv(snapshot_dir / "RANKING_RESULTS_HIERARCHICAL_TRUST_V2.csv")
    weighted = load_csv(snapshot_dir / "RANKING_RESULTS_HIERARCHICAL.csv")
    classification = load_csv(snapshot_dir / "TOP_TIER_CLASSIFICATION.csv")
    metrics = json.loads((snapshot_dir / "derived_scoring" / "scoring_build_metrics.json").read_text(encoding="utf-8"))

    to_numeric(
        summary,
        [
            "rank_hierarchical_trust_v2",
            "rank_hierarchical_weighted",
            "rank_baseline_conservative",
            "score_hierarchical_trust_v2",
            "score_hierarchical_weighted",
            "total_engagements_strict",
            "total_battle_pages_strict",
            "distinct_conflicts_strict",
            "known_outcome_count",
        ],
    )
    to_numeric(
        trust,
        [
            "rank",
            "score_normalized",
            "battle_count",
            "known_outcome_count",
            "known_battle_outcome_count",
            "higher_level_share",
        ],
    )
    to_numeric(weighted, ["rank", "score_normalized"])
    to_numeric(sensitivity, ["rank_range", "top25_appearances"])

    sanity = summary.loc[summary["display_name"].isin(SANITY_COMMANDERS), [
        "display_name",
        "rank_baseline_conservative",
        "rank_hierarchical_weighted",
        "rank_hierarchical_trust_v2",
        "score_hierarchical_weighted",
        "score_hierarchical_trust_v2",
        "trust_tier_v2",
        "trust_confidence_v2",
        "total_engagements_strict",
        "total_battle_pages_strict",
        "distinct_conflicts_strict",
        "known_outcome_count",
        "trust_headline_reason_v2",
    ]].copy()
    sanity["trust_minus_weighted_rank"] = sanity["rank_hierarchical_trust_v2"] - sanity["rank_hierarchical_weighted"]
    sanity = sanity.sort_values(["rank_hierarchical_trust_v2", "display_name"])
    sanity.to_csv(snapshot_dir / "RANKING_VALIDATION_V2.csv", index=False, encoding="utf-8-sig")

    trust_top10 = trust.head(10)
    weighted_top10 = weighted.head(10)
    trust_top10_names = set(trust_top10["display_name"])
    weighted_top10_names = set(weighted_top10["display_name"])
    top10_overlap = len(trust_top10_names & weighted_top10_names)

    non_person_hits = [
        name
        for name in trust["display_name"].tolist()
        if any(token in name.lower() for token in NON_PERSON_TOKENS)
    ]
    fragile_core = classification.loc[
        (classification["interpretive_group"] == "robust_elite_core")
        & (
            classification["caution_flags"].str.contains("higher_level_dependent", na=False)
            | classification["caution_flags"].str.contains("thin_battle_anchor", na=False)
        ),
        "display_name",
    ].tolist()

    regression = {
        "snapshot": snapshot_dir.name,
        "checks": {
            "strict_eligibility_preserved": {
                "pass": int(metrics["eligibility"]["strict_included_pages"]) >= 11640,
                "strict_included_pages": int(metrics["eligibility"]["strict_included_pages"]),
            },
            "non_person_leakage": {
                "pass": len(non_person_hits) == 0,
                "hits": non_person_hits[:10],
            },
            "top10_core_overlap": {
                "pass": top10_overlap >= 6,
                "overlap_count": top10_overlap,
                "trust_top10": trust_top10["display_name"].tolist(),
                "weighted_top10": weighted_top10["display_name"].tolist(),
            },
            "robust_core_not_higher_level_fragile": {
                "pass": len(fragile_core) == 0,
                "hits": fragile_core,
            },
        },
    }
    (snapshot_dir / "MODEL_REGRESSION_CHECKS.json").write_text(
        json.dumps(regression, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    memo_lines = [
        "# Sanity Case Memo",
        "",
        f"Snapshot: `{snapshot_dir.name}`",
        "",
        "## Trust-First V2 sanity cases",
        "",
    ]
    for _, row in sanity.iterrows():
        memo_lines.append(
            f"- `{row['display_name']}`: baseline `{int(row['rank_baseline_conservative']) if pd.notna(row['rank_baseline_conservative']) else 'NA'}`, "
            f"weighted `{int(row['rank_hierarchical_weighted']) if pd.notna(row['rank_hierarchical_weighted']) else 'NA'}`, "
            f"trust v2 `{int(row['rank_hierarchical_trust_v2']) if pd.notna(row['rank_hierarchical_trust_v2']) else 'NA'}`; "
            f"tier `{row['trust_tier_v2']}`, confidence `{row['trust_confidence_v2']}`. {row['trust_headline_reason_v2']}"
        )
    memo_lines.extend(
        [
            "",
            "## Regression checks",
            "",
            f"- Strict eligibility preserved: `{regression['checks']['strict_eligibility_preserved']['pass']}`",
            f"- Non-person leakage: `{regression['checks']['non_person_leakage']['pass']}`",
            f"- Top-10 overlap between weighted and trust v2: `{top10_overlap}`",
            f"- Robust core free of fragile higher-level anchors: `{regression['checks']['robust_core_not_higher_level_fragile']['pass']}`",
        ]
    )
    (snapshot_dir / "SANITY_CASE_MEMO.md").write_text("\n".join(memo_lines) + "\n", encoding="utf-8")

    print(json.dumps(regression, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
