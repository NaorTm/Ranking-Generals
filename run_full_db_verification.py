from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd

from build_full_verification_layer import build_verification_layer
from build_interpretive_layer import build_frames, write_csvs, write_memo
from build_ranking_dashboard import (
    build_dashboard_dataset,
    copy_dashboard_assets,
    write_data_js,
    write_technical_note,
)
from build_ranking_package import build_rankings
from build_scoring_framework_package import build_package


ROOT = Path(__file__).resolve().parent
SANITY_NAMES = [
    "Napoleon Bonaparte",
    "Alexander Suvorov",
    "Suleiman the Magnificent",
    "Jean Lannes",
    "Louis-Nicolas Davout",
    "Khalid ibn al-Walid",
    "Douglas MacArthur",
    "Takeda Shingen",
]


def write_stage_state(verification_dir: Path, state: dict[str, object]) -> None:
    (verification_dir / "stage_state.json").write_text(json.dumps(state, indent=2), encoding="utf-8")


def read_stage_state(verification_dir: Path) -> dict[str, object]:
    path = verification_dir / "stage_state.json"
    if not path.exists():
        return {"stages": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def mark_stage_complete(verification_dir: Path, state: dict[str, object], stage_name: str, details: dict[str, object] | None = None) -> None:
    stages = state.setdefault("stages", {})
    stages[stage_name] = {"completed": True, "details": details or {}}
    write_stage_state(verification_dir, state)


def stage_completed(state: dict[str, object], stage_name: str) -> bool:
    return bool(state.get("stages", {}).get(stage_name, {}).get("completed"))


def copy_snapshot(base_snapshot: Path, output_snapshot: Path) -> None:
    if (output_snapshot / "battles_clean.csv").exists():
        return
    if output_snapshot.exists():
        shutil.rmtree(output_snapshot)
    shutil.copytree(base_snapshot, output_snapshot)


def copy_if_missing(source_dir: Path, target_dir: Path) -> None:
    if target_dir.exists() or not source_dir.exists():
        return
    shutil.copytree(source_dir, target_dir)


def run_subprocess(args: list[str], workdir: Path) -> None:
    subprocess.run(args, cwd=workdir, check=True)


def build_regression_summary(base_snapshot: Path, output_snapshot: Path) -> dict[str, object]:
    base_summary = pd.read_csv(base_snapshot / "TOP_COMMANDERS_SUMMARY.csv", dtype=str).fillna("")
    output_summary = pd.read_csv(output_snapshot / "TOP_COMMANDERS_SUMMARY.csv", dtype=str).fillna("")

    desired_cols = [
        "display_name",
        "rank_hierarchical_weighted",
        "rank_hierarchical_trust_v2",
        "trust_tier_v2",
        "trust_confidence_v2",
        "page_type_exposure_summary",
        "outcome_profile_summary",
        "known_outcome_count",
        "total_engagements_strict",
    ]
    for column in desired_cols:
        if column not in base_summary.columns:
            base_summary[column] = ""
        if column not in output_summary.columns:
            output_summary[column] = ""

    base_sanity = base_summary.loc[base_summary["display_name"].isin(SANITY_NAMES), desired_cols].copy()
    output_sanity = output_summary.loc[output_summary["display_name"].isin(SANITY_NAMES), desired_cols].copy()

    merged = base_sanity.merge(output_sanity, on="display_name", how="outer", suffixes=("_before", "_after"))
    merged.to_csv(output_snapshot / "verification" / "VERIFICATION_SANITY_COMPARISON.csv", index=False, encoding="utf-8-sig")

    verification_summary = json.loads((output_snapshot / "verification" / "verification_summary.json").read_text(encoding="utf-8"))
    validation_summary = json.loads((output_snapshot / "MODEL_REGRESSION_CHECKS.json").read_text(encoding="utf-8")) if (output_snapshot / "MODEL_REGRESSION_CHECKS.json").exists() else {}

    summary = {
        "base_snapshot": base_snapshot.name,
        "output_snapshot": output_snapshot.name,
        "verification_status_counts": verification_summary.get("verification_status_counts", {}),
        "validation_checks": validation_summary.get("checks", {}),
        "sanity_rows": int(len(merged)),
    }
    (output_snapshot / "verification" / "FULL_VERIFICATION_REGRESSION_SUMMARY.json").write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the full DB verification pipeline and rebuild a verified snapshot.")
    parser.add_argument(
        "--base-snapshot",
        type=Path,
        default=Path("outputs_cleaned_2026-04-21_conservativepatch_authoritative"),
    )
    parser.add_argument(
        "--output-snapshot",
        type=Path,
        default=Path("outputs_cleaned_2026-04-21_fullverification_authoritative"),
    )
    parser.add_argument(
        "--candidate-csv",
        type=Path,
        default=Path("outputs_final_2026-04-05/candidate_battle_pages.csv"),
    )
    args = parser.parse_args()

    base_snapshot = (ROOT / args.base_snapshot).resolve() if not args.base_snapshot.is_absolute() else args.base_snapshot
    output_snapshot = (ROOT / args.output_snapshot).resolve() if not args.output_snapshot.is_absolute() else args.output_snapshot
    verification_dir = output_snapshot / "verification"
    state = read_stage_state(verification_dir)
    if stage_completed(state, "copy_snapshot") and not (output_snapshot / "battles_clean.csv").exists():
        shutil.rmtree(output_snapshot, ignore_errors=True)
        state = {"stages": {}}

    if not stage_completed(state, "copy_snapshot"):
        copy_snapshot(base_snapshot, output_snapshot)
        verification_dir.mkdir(parents=True, exist_ok=True)
        state = read_stage_state(verification_dir)
        mark_stage_complete(verification_dir, state, "copy_snapshot", {"base_snapshot": str(base_snapshot)})

    if not stage_completed(state, "seed_audits"):
        copy_if_missing(base_snapshot / "postfix_audit", output_snapshot / "postfix_audit")
        copy_if_missing(base_snapshot / "commander_postfix_audit", output_snapshot / "commander_postfix_audit")
        if not (output_snapshot / "postfix_audit" / "row_audit.csv").exists():
            run_subprocess(
                [
                    sys.executable,
                    "audit_battles_clean_postfix.py",
                    "--csv",
                    str(output_snapshot / "battles_clean.csv"),
                    "--candidate-csv",
                    str((ROOT / args.candidate_csv).resolve() if not args.candidate_csv.is_absolute() else args.candidate_csv),
                    "--output-dir",
                    str(output_snapshot / "postfix_audit"),
                ],
                ROOT,
            )
        if not (output_snapshot / "commander_postfix_audit" / "row_audit.csv").exists():
            run_subprocess(
                [
                    sys.executable,
                    "audit_battle_commanders_postfix.py",
                    "--snapshot-dir",
                    str(output_snapshot),
                ],
                ROOT,
            )
        mark_stage_complete(
            verification_dir,
            state,
            "seed_audits",
            {
                "battle_audit_dir": str(output_snapshot / "postfix_audit"),
                "commander_audit_dir": str(output_snapshot / "commander_postfix_audit"),
            },
        )

    if not stage_completed(state, "verification_layer"):
        summary = build_verification_layer(
            snapshot_dir=output_snapshot,
            battle_audit_dir=output_snapshot / "postfix_audit",
            commander_audit_dir=output_snapshot / "commander_postfix_audit",
        )
        mark_stage_complete(verification_dir, state, "verification_layer", summary)

    if not stage_completed(state, "scoring"):
        metrics = build_package(output_snapshot)
        mark_stage_complete(verification_dir, state, "scoring", metrics)

    if not stage_completed(state, "ranking"):
        metrics = build_rankings(output_snapshot)
        mark_stage_complete(verification_dir, state, "ranking", metrics)

    if not stage_completed(state, "interpretive"):
        classification, audit, era_shortlist = build_frames(output_snapshot)
        write_csvs(output_snapshot, classification, audit, era_shortlist)
        write_memo(output_snapshot, classification, audit, era_shortlist)
        mark_stage_complete(
            verification_dir,
            state,
            "interpretive",
            {
                "classification_rows": int(len(classification)),
                "audit_rows": int(len(audit)),
                "era_shortlist_rows": int(len(era_shortlist)),
            },
        )

    if not stage_completed(state, "dashboard"):
        dataset = build_dashboard_dataset(output_snapshot)
        write_data_js(output_snapshot, dataset)
        write_technical_note(output_snapshot, dataset)
        copy_dashboard_assets(output_snapshot, base_snapshot / "dashboard")
        mark_stage_complete(
            verification_dir,
            state,
            "dashboard",
            {"commander_count": int(dataset["metadata"]["counts"]["commanderCount"])},
        )

    if not stage_completed(state, "validation"):
        run_subprocess([sys.executable, "generate_ranking_validation_v2.py", "--snapshot-dir", str(output_snapshot)], ROOT)
        summary = build_regression_summary(base_snapshot, output_snapshot)
        mark_stage_complete(verification_dir, state, "validation", summary)

    final_summary = {
        "base_snapshot": str(base_snapshot),
        "output_snapshot": str(output_snapshot),
        "verification_dir": str(verification_dir),
        "stages": read_stage_state(verification_dir).get("stages", {}),
    }
    (verification_dir / "FULL_VERIFICATION_RUN_SUMMARY.json").write_text(json.dumps(final_summary, indent=2), encoding="utf-8")
    print(json.dumps(final_summary, indent=2))


if __name__ == "__main__":
    main()
