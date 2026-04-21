from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


SANITY_COMMANDERS = [
    "Alexander Suvorov",
    "Napoleon Bonaparte",
    "Jean Lannes",
    "Suleiman the Magnificent",
]


def load_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str).fillna("")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate before/after audit files for the conservative DB hardening pass.")
    parser.add_argument("--old-snapshot", type=Path, required=True)
    parser.add_argument("--new-snapshot", type=Path, required=True)
    args = parser.parse_args()

    old_battles = load_csv(args.old_snapshot / "battles_clean.csv")
    new_battles = load_csv(args.new_snapshot / "battles_clean.csv")
    year_changes = old_battles[["battle_id", "battle_name", "year", "date_raw"]].merge(
        new_battles[["battle_id", "battle_name", "year", "date_raw"]],
        on="battle_id",
        suffixes=("_old", "_new"),
        how="inner",
    )
    year_changes = year_changes.loc[year_changes["year_old"] != year_changes["year_new"]].copy()

    recovery_audit_path = args.new_snapshot / "commander_recovery_audit.csv"
    recovery_audit = load_csv(recovery_audit_path) if recovery_audit_path.exists() else pd.DataFrame()

    old_top = load_csv(args.old_snapshot / "TOP_COMMANDERS_SUMMARY.csv")
    new_top = load_csv(args.new_snapshot / "TOP_COMMANDERS_SUMMARY.csv")

    before_after = (
        old_top.loc[old_top["display_name"].isin(SANITY_COMMANDERS), [
            "display_name",
            "total_engagements_strict",
            "known_outcome_count",
        ]]
        .rename(
            columns={
                "total_engagements_strict": "engagements_strict_old",
                "known_outcome_count": "known_outcome_count_old",
            }
        )
        .merge(
            new_top.loc[new_top["display_name"].isin(SANITY_COMMANDERS), [
                "display_name",
                "total_engagements_strict",
                "known_outcome_count",
            ]].rename(
                columns={
                    "total_engagements_strict": "engagements_strict_new",
                    "known_outcome_count": "known_outcome_count_new",
                }
            ),
            on="display_name",
            how="outer",
        )
        .merge(
            old_top.loc[old_top["display_name"].isin(SANITY_COMMANDERS), [
                "display_name",
                "rank_baseline_conservative",
                "rank_hierarchical_weighted",
            ]].rename(
                columns={
                    "rank_baseline_conservative": "rank_baseline_old",
                    "rank_hierarchical_weighted": "rank_hierarchical_old",
                }
            ),
            on="display_name",
            how="left",
        )
        .merge(
            new_top.loc[new_top["display_name"].isin(SANITY_COMMANDERS), [
                "display_name",
                "rank_baseline_conservative",
                "rank_hierarchical_weighted",
            ]].rename(
                columns={
                    "rank_baseline_conservative": "rank_baseline_new",
                    "rank_hierarchical_weighted": "rank_hierarchical_new",
                }
            ),
            on="display_name",
            how="left",
        )
        .sort_values("display_name")
    )

    output_dir = args.new_snapshot
    year_changes.to_csv(output_dir / "CONSERVATIVE_HARDENING_YEAR_CHANGES.csv", index=False, encoding="utf-8-sig")
    before_after.to_csv(output_dir / "CONSERVATIVE_HARDENING_SANITY_COMPARISON.csv", index=False, encoding="utf-8-sig")

    summary = {
        "old_snapshot": str(args.old_snapshot),
        "new_snapshot": str(args.new_snapshot),
        "year_corrections": int(len(year_changes)),
        "recovered_commander_rows": int(len(recovery_audit)),
        "pages_touched_by_recovery": int(recovery_audit["battle_id"].nunique()) if not recovery_audit.empty else 0,
        "sanity_commanders": SANITY_COMMANDERS,
    }
    (output_dir / "CONSERVATIVE_HARDENING_SUMMARY.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
