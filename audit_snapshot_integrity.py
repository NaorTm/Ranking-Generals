from __future__ import annotations

import argparse
import csv
import gzip
import json
import math
import re
import sys
from pathlib import Path
from typing import Any


DEFAULT_SNAPSHOT = Path("outputs_cleaned_2026-04-21_fullpopulation_authoritative")
CORE_CSVS = [
    "battles_clean.csv",
    "battle_commanders.csv",
    "commanders_master.csv",
    "derived_scoring/commander_identity_bridge.csv",
    "derived_scoring/commander_engagements_annotated.csv",
    "derived_scoring/commander_ranking_features.csv",
    "RANKING_RESULTS_HIERARCHICAL_TRUST_V2.csv",
    "RANKING_RESULTS_HIERARCHICAL.csv",
    "RANKING_RESULTS_BASELINE.csv",
    "RANKING_RESULTS_SENSITIVITY.csv",
    "TOP_COMMANDERS_SUMMARY.csv",
]
REQUIRED_FILES = [
    *CORE_CSVS,
    "derived_scoring/scoring_build_metrics.json",
    "RANKING_BUILD_METRICS.json",
    "MODEL_REGRESSION_CHECKS.json",
    "dashboard/dashboard_data.js",
    "dashboard_qa_summary.json",
    "SCORING_FRAMEWORK.md",
    "FINAL_SYSTEM_TRUST_ASSESSMENT.md",
]
UPGRADE_FILES = [
    "derived_scoring/commander_model_stability.csv",
    "derived_scoring/commander_tiers.csv",
    "derived_scoring/page_type_score_contributions.csv",
    "audits/high_ranked_commander_flags.csv",
]
CONFIDENCE_FILES = [
    "derived_scoring/bootstrap_rank_confidence.csv",
    "derived_scoring/commander_rank_confidence_summary.csv",
    "derived_scoring/commander_tiers_confidence_adjusted.csv",
    "reports/UPGRADE_PASS_3_CONFIDENCE_REPORT.md",
]
ROLE_FILES = [
    "verification/verified_command_role_classification.csv",
    "derived_scoring/role_class_score_contributions.csv",
    "RANKING_RESULTS_HIERARCHICAL_TRUST_V2_ROLE_WEIGHTED.csv",
    "RANKING_RESULTS_PASS4_ROLE_SENSITIVITY.csv",
    "reports/UPGRADE_PASS_4_ROLE_CLASSIFICATION_REPORT.md",
]
SYNTHESIS_FILES = [
    "FINAL_UPGRADED_SYSTEM_ASSESSMENT.md",
    "RANKING_RESULTS_SYNTHESIS_TIERED.csv",
    "ROBUST_ELITE_CORE.md",
    "CAVEATED_HIGH_RANKED_COMMANDERS.md",
    "DASHBOARD_RELEASE_METADATA.json",
    "RELEASE_CANDIDATE_CHECKLIST.md",
]


def resolve_snapshot_file(snapshot_dir: Path, relative_name: str) -> Path:
    path = snapshot_dir / relative_name
    if path.exists():
        return path
    gzip_path = snapshot_dir / f"{relative_name}.gz"
    if gzip_path.exists():
        return gzip_path
    return path


def read_csv(path: Path) -> list[dict[str, str]]:
    opener = gzip.open if path.suffix == ".gz" else Path.open
    with opener(path, "rt", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def parse_dashboard_data(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    prefix = "window.DASHBOARD_DATA="
    text = text.strip()
    if not text.startswith(prefix):
        raise ValueError("dashboard_data.js does not start with window.DASHBOARD_DATA=")
    if text.endswith(";"):
        text = text[:-1]
    return json.loads(text[len(prefix):])


def numeric(value: str, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, **details: Any) -> None:
    checks.append({"name": name, "pass": bool(passed), **details})


def top_names(rows: list[dict[str, str]], count: int = 10) -> list[str]:
    return [row["display_name"] for row in rows[:count]]


def audit(
    snapshot_dir: Path,
    require_upgrade_files: bool = False,
    require_confidence_files: bool = False,
    require_role_files: bool = False,
    require_synthesis_files: bool = False,
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    required_files = [
        *REQUIRED_FILES,
        *(UPGRADE_FILES if require_upgrade_files else []),
        *(CONFIDENCE_FILES if require_confidence_files else []),
        *(ROLE_FILES if require_role_files else []),
        *(SYNTHESIS_FILES if require_synthesis_files else []),
    ]
    missing_files = [name for name in required_files if not resolve_snapshot_file(snapshot_dir, name).exists()]
    add_check(checks, "required_files_exist", not missing_files, missing_files=missing_files)
    if missing_files:
        return {
            "snapshot": snapshot_dir.name,
            "status": "FAIL",
            "checks": checks,
            "warnings": warnings,
        }

    battles = read_csv(snapshot_dir / "battles_clean.csv")
    commanders = read_csv(snapshot_dir / "battle_commanders.csv")
    excluded = read_csv(snapshot_dir / "derived_scoring" / "scoring_excluded_commander_rows.csv")
    bridge = read_csv(snapshot_dir / "derived_scoring" / "commander_identity_bridge.csv")
    annotated = read_csv(resolve_snapshot_file(snapshot_dir, "derived_scoring/commander_engagements_annotated.csv"))
    features = read_csv(snapshot_dir / "derived_scoring" / "commander_ranking_features.csv")
    sensitivity = read_csv(snapshot_dir / "RANKING_RESULTS_SENSITIVITY.csv")
    trust = read_csv(snapshot_dir / "RANKING_RESULTS_HIERARCHICAL_TRUST_V2.csv")
    hierarchical = read_csv(snapshot_dir / "RANKING_RESULTS_HIERARCHICAL.csv")
    baseline = read_csv(snapshot_dir / "RANKING_RESULTS_BASELINE.csv")
    scoring_metrics = read_json(snapshot_dir / "derived_scoring" / "scoring_build_metrics.json")
    ranking_metrics = read_json(snapshot_dir / "RANKING_BUILD_METRICS.json")
    validation = read_json(snapshot_dir / "MODEL_REGRESSION_CHECKS.json")
    dashboard_qa = read_json(snapshot_dir / "dashboard_qa_summary.json")
    dashboard = parse_dashboard_data(snapshot_dir / "dashboard" / "dashboard_data.js")

    battle_ids = [row["battle_id"] for row in battles]
    battle_id_set = set(battle_ids)
    bridge_ids = [row["analytic_commander_id"] for row in bridge]
    bridge_id_set = set(bridge_ids)
    feature_ids = {row["analytic_commander_id"] for row in features}
    annotated_pairs = [(row["analytic_commander_id"], row["battle_id"]) for row in annotated]

    add_check(checks, "battle_ids_unique", len(battle_ids) == len(battle_id_set), rows=len(battle_ids), unique=len(battle_id_set))
    add_check(checks, "bridge_ids_unique", len(bridge_ids) == len(bridge_id_set), rows=len(bridge_ids), unique=len(bridge_id_set))
    add_check(checks, "annotated_commander_battle_pairs_unique", len(annotated_pairs) == len(set(annotated_pairs)), rows=len(annotated_pairs), unique=len(set(annotated_pairs)))

    missing_commander_battles = [row["battle_id"] for row in commanders if row.get("battle_id") not in battle_id_set]
    missing_annotated_battles = [row["battle_id"] for row in annotated if row.get("battle_id") not in battle_id_set]
    missing_annotated_bridge = [row["analytic_commander_id"] for row in annotated if row.get("analytic_commander_id") not in bridge_id_set]
    missing_features_bridge = sorted(feature_ids - bridge_id_set)
    add_check(checks, "battle_commanders_reference_existing_battles", not missing_commander_battles, missing_count=len(missing_commander_battles))
    add_check(checks, "annotated_rows_reference_existing_battles", not missing_annotated_battles, missing_count=len(missing_annotated_battles))
    add_check(checks, "annotated_rows_reference_existing_bridge_ids", not missing_annotated_bridge, missing_count=len(missing_annotated_bridge))
    add_check(checks, "features_reference_existing_bridge_ids", not missing_features_bridge, missing_count=len(missing_features_bridge))

    expected_scoring_rows = len(commanders) - len(excluded)
    add_check(
        checks,
        "scoring_metrics_match_row_counts",
        scoring_metrics["source"]["retained_pages"] == len(battles)
        and scoring_metrics["source"]["commander_rows"] == expected_scoring_rows
        and scoring_metrics["derived"]["annotated_rows"] == len(annotated)
        and scoring_metrics["derived"]["identity_bridge_rows"] == len(bridge),
        retained_pages=len(battles),
        raw_commander_rows=len(commanders),
        excluded_commander_rows=len(excluded),
        expected_scored_commander_rows=expected_scoring_rows,
        metrics=scoring_metrics["source"],
    )

    unknown_nonzero = [
        row
        for row in annotated
        if row.get("outcome_category") == "unknown" and numeric(row.get("outcome_credit_fraction", "")) != 0.0
    ]
    add_check(checks, "unknown_outcomes_have_zero_split_credit", not unknown_nonzero, rows=len(unknown_nonzero))

    known_groups: dict[tuple[str, str], int] = {}
    for row in annotated:
        side = row.get("side", "")
        if side in {"side_a", "side_b", "side_c", "side_d"} and row.get("outcome_category") != "unknown":
            key = (row.get("battle_id", ""), side)
            known_groups[key] = known_groups.get(key, 0) + 1
    bad_known_split = []
    for row in annotated:
        side = row.get("side", "")
        if side not in {"side_a", "side_b", "side_c", "side_d"} or row.get("outcome_category") == "unknown":
            continue
        expected = 1.0 / math.sqrt(known_groups[(row.get("battle_id", ""), side)])
        actual = numeric(row.get("outcome_credit_fraction", ""))
        if abs(actual - expected) > 0.00001:
            bad_known_split.append(
                {
                    "battle_id": row.get("battle_id"),
                    "side": side,
                    "display_name": row.get("display_name"),
                    "expected": round(expected, 6),
                    "actual": actual,
                }
            )
            if len(bad_known_split) >= 10:
                break
    add_check(checks, "known_split_credit_uses_known_same_side_denominator", not bad_known_split, samples=bad_known_split)

    add_check(
        checks,
        "ranking_metrics_match_csv_tops",
        top_names(baseline) == top_names(ranking_metrics["top_baseline"])
        and top_names(trust) == top_names(ranking_metrics["top_trust_v2"])
        and top_names(hierarchical) == top_names(ranking_metrics["top_hierarchical"]),
        baseline_top=top_names(baseline),
        trust_top=top_names(trust),
        hierarchical_top=top_names(hierarchical),
    )

    dashboard_count = dashboard["metadata"]["counts"]["commanderCount"]
    dashboard_first = dashboard["commanders"][0]["name"] if dashboard.get("commanders") else None
    add_check(
        checks,
        "dashboard_data_matches_ranking",
        dashboard["metadata"]["snapshot"] == snapshot_dir.name
        and dashboard_count == len(sensitivity)
        and dashboard_first == trust[0]["display_name"],
        dashboard_snapshot=dashboard["metadata"].get("snapshot"),
        dashboard_count=dashboard_count,
        sensitivity_rows=len(sensitivity),
        dashboard_first=dashboard_first,
        trust_first=trust[0]["display_name"],
    )

    if require_upgrade_files:
        stability = read_csv(snapshot_dir / "derived_scoring" / "commander_model_stability.csv")
        tiers = read_csv(snapshot_dir / "derived_scoring" / "commander_tiers.csv")
        page_contributions = read_csv(snapshot_dir / "derived_scoring" / "page_type_score_contributions.csv")
        high_rank_flags = read_csv(snapshot_dir / "audits" / "high_ranked_commander_flags.csv")
        top100_ids = {
            row["analytic_commander_id"]
            for row in trust
            if 0 < numeric(row.get("rank", row.get("rank_hierarchical_trust_v2", "")), 999999) <= 100
        }
        if not top100_ids:
            top100_ids = {row["analytic_commander_id"] for row in trust[:100]}
        stability_ids = {
            row["analytic_commander_id"]
            for row in stability
            if row.get("stability_category") and row.get("stability_score")
        }
        tier_ids = {
            row["analytic_commander_id"]
            for row in tiers
            if row.get("tier_label") and row.get("tier_key") and row.get("tier_key") != "unclassified"
        }
        page_contribution_ids = {row["analytic_commander_id"] for row in page_contributions}
        audit_flag_ids = {row["analytic_commander_id"] for row in high_rank_flags}
        dashboard_by_id = {row.get("id"): row for row in dashboard.get("commanders", [])}
        dashboard_top100_missing_upgrade = []
        for commander_id in sorted(top100_ids):
            commander = dashboard_by_id.get(commander_id, {})
            if not commander.get("tier") or not commander.get("stability") or "auditFlags" not in commander:
                dashboard_top100_missing_upgrade.append(commander_id)

        add_check(
            checks,
            "top100_have_stability_metadata",
            top100_ids <= stability_ids,
            missing_count=len(top100_ids - stability_ids),
            missing_ids=sorted(top100_ids - stability_ids)[:20],
        )
        add_check(
            checks,
            "top100_have_interpretive_tiers",
            top100_ids <= tier_ids,
            missing_count=len(top100_ids - tier_ids),
            missing_ids=sorted(top100_ids - tier_ids)[:20],
        )
        add_check(
            checks,
            "top100_have_page_type_contributions",
            top100_ids <= page_contribution_ids,
            missing_count=len(top100_ids - page_contribution_ids),
            missing_ids=sorted(top100_ids - page_contribution_ids)[:20],
        )
        add_check(
            checks,
            "top100_have_high_rank_audit_rows",
            top100_ids <= audit_flag_ids,
            missing_count=len(top100_ids - audit_flag_ids),
            missing_ids=sorted(top100_ids - audit_flag_ids)[:20],
        )
        add_check(
            checks,
            "dashboard_contains_upgrade_metadata",
            not dashboard_top100_missing_upgrade
            and "derived_scoring/commander_model_stability.csv" in dashboard["metadata"].get("generatedFrom", [])
            and "derived_scoring/commander_tiers.csv" in dashboard["metadata"].get("generatedFrom", [])
            and "derived_scoring/page_type_score_contributions.csv" in dashboard["metadata"].get("generatedFrom", [])
            and "audits/high_ranked_commander_flags.csv" in dashboard["metadata"].get("generatedFrom", []),
            missing_count=len(dashboard_top100_missing_upgrade),
            missing_ids=dashboard_top100_missing_upgrade[:20],
            generated_from=dashboard["metadata"].get("generatedFrom", []),
        )

        diagnostic_headline = dashboard["metadata"].get("headlineModel") == "hierarchical_full_credit"
        add_check(
            checks,
            "diagnostic_full_credit_not_headline",
            not diagnostic_headline,
            headline_model=dashboard["metadata"].get("headlineModel"),
        )

    if require_confidence_files:
        confidence = read_csv(snapshot_dir / "derived_scoring" / "commander_rank_confidence_summary.csv")
        adjusted = read_csv(snapshot_dir / "derived_scoring" / "commander_tiers_confidence_adjusted.csv")
        bootstrap = read_csv(snapshot_dir / "derived_scoring" / "bootstrap_rank_confidence.csv")
        top100_ids = {
            row["analytic_commander_id"]
            for row in trust
            if 0 < numeric(row.get("rank", row.get("rank_hierarchical_trust_v2", "")), 999999) <= 100
        }
        confidence_ids = {
            row["analytic_commander_id"]
            for row in confidence
            if row.get("confidence_category") and row.get("rank_interval_80")
        }
        adjusted_ids = {
            row["analytic_commander_id"]
            for row in adjusted
            if row.get("confidence_adjusted_tier") and row.get("confidence_adjusted_tier_key")
        }
        bootstrap_headline_ids = {
            row["analytic_commander_id"]
            for row in bootstrap
            if row.get("model_name") == "hierarchical_trust_v2"
        }
        dashboard_by_id = {row.get("id"): row for row in dashboard.get("commanders", [])}
        dashboard_missing_confidence = []
        for commander_id in sorted(top100_ids):
            commander = dashboard_by_id.get(commander_id, {})
            if not commander.get("rankConfidence") or not commander.get("confidenceAdjustedTier"):
                dashboard_missing_confidence.append(commander_id)
        add_check(
            checks,
            "top100_have_bootstrap_confidence",
            top100_ids <= confidence_ids <= bootstrap_headline_ids,
            missing_count=len(top100_ids - confidence_ids),
            missing_ids=sorted(top100_ids - confidence_ids)[:20],
        )
        add_check(
            checks,
            "top100_have_confidence_adjusted_tiers",
            top100_ids <= adjusted_ids,
            missing_count=len(top100_ids - adjusted_ids),
            missing_ids=sorted(top100_ids - adjusted_ids)[:20],
        )
        add_check(
            checks,
            "dashboard_contains_confidence_metadata",
            not dashboard_missing_confidence
            and "derived_scoring/commander_rank_confidence_summary.csv" in dashboard["metadata"].get("generatedFrom", [])
            and "derived_scoring/commander_tiers_confidence_adjusted.csv" in dashboard["metadata"].get("generatedFrom", []),
            missing_count=len(dashboard_missing_confidence),
            missing_ids=dashboard_missing_confidence[:20],
            generated_from=dashboard["metadata"].get("generatedFrom", []),
        )

    if require_role_files:
        role_contrib = read_csv(snapshot_dir / "derived_scoring" / "role_class_score_contributions.csv")
        role_sensitivity = read_csv(snapshot_dir / "RANKING_RESULTS_PASS4_ROLE_SENSITIVITY.csv")
        role_file = read_csv(snapshot_dir / "verification" / "verified_command_role_classification.csv")
        top100_ids = {
            row["analytic_commander_id"]
            for row in trust
            if 0 < numeric(row.get("rank", row.get("rank_hierarchical_trust_v2", "")), 999999) <= 100
        }
        role_contrib_ids = {row["analytic_commander_id"] for row in role_contrib}
        role_sensitivity_ids = {row["analytic_commander_id"] for row in role_sensitivity}
        role_pair_count = len({(row.get("analytic_commander_id"), row.get("battle_id")) for row in role_file})
        valid_roles = {
            "overall_commander",
            "principal_field_commander",
            "wing_or_corps_commander",
            "subordinate_commander",
            "coalition_commander",
            "siege_engineer_or_specialist",
            "naval_commander",
            "staff_or_planning_role",
            "nominal_or_political_leader",
            "unclear_role",
        }
        invalid_roles = sorted({row.get("role_class") for row in role_file} - valid_roles)
        dashboard_by_id = {row.get("id"): row for row in dashboard.get("commanders", [])}
        dashboard_missing_role = []
        for commander_id in sorted(top100_ids):
            commander = dashboard_by_id.get(commander_id, {})
            if not commander.get("roleSensitivity") or not commander.get("roleContribution"):
                dashboard_missing_role.append(commander_id)
        add_check(
            checks,
            "top100_have_role_contributions",
            top100_ids <= role_contrib_ids,
            missing_count=len(top100_ids - role_contrib_ids),
            missing_ids=sorted(top100_ids - role_contrib_ids)[:20],
        )
        add_check(
            checks,
            "top100_have_role_sensitivity",
            top100_ids <= role_sensitivity_ids,
            missing_count=len(top100_ids - role_sensitivity_ids),
            missing_ids=sorted(top100_ids - role_sensitivity_ids)[:20],
        )
        add_check(
            checks,
            "role_file_covers_annotated_pairs",
            role_pair_count == len(annotated_pairs),
            role_pairs=role_pair_count,
            annotated_pairs=len(annotated_pairs),
        )
        add_check(checks, "role_classes_valid", not invalid_roles, invalid_roles=invalid_roles)
        add_check(
            checks,
            "dashboard_contains_role_metadata",
            not dashboard_missing_role
            and "derived_scoring/role_class_score_contributions.csv" in dashboard["metadata"].get("generatedFrom", [])
            and "RANKING_RESULTS_PASS4_ROLE_SENSITIVITY.csv" in dashboard["metadata"].get("generatedFrom", []),
            missing_count=len(dashboard_missing_role),
            missing_ids=dashboard_missing_role[:20],
            generated_from=dashboard["metadata"].get("generatedFrom", []),
        )

    if require_synthesis_files:
        synthesis = read_csv(snapshot_dir / "RANKING_RESULTS_SYNTHESIS_TIERED.csv")
        release_metadata = read_json(snapshot_dir / "DASHBOARD_RELEASE_METADATA.json")
        top100_ids = {
            row["analytic_commander_id"]
            for row in trust
            if 0 < numeric(row.get("rank", row.get("rank_hierarchical_trust_v2", "")), 999999) <= 100
        }
        synthesis_ids = {
            row["analytic_commander_id"]
            for row in synthesis
            if row.get("synthesis_tier") and row.get("recommended_interpretation")
        }
        dashboard_by_id = {row.get("id"): row for row in dashboard.get("commanders", [])}
        dashboard_missing_synthesis = []
        for commander_id in sorted(top100_ids):
            commander = dashboard_by_id.get(commander_id, {})
            if not commander.get("synthesis"):
                dashboard_missing_synthesis.append(commander_id)
        add_check(
            checks,
            "top100_have_synthesis_tiers",
            top100_ids <= synthesis_ids,
            missing_count=len(top100_ids - synthesis_ids),
            missing_ids=sorted(top100_ids - synthesis_ids)[:20],
        )
        add_check(
            checks,
            "dashboard_contains_synthesis_metadata",
            not dashboard_missing_synthesis
            and "RANKING_RESULTS_SYNTHESIS_TIERED.csv" in dashboard["metadata"].get("generatedFrom", [])
            and dashboard["metadata"].get("recommendedHeadlineView") == "tiered_synthesis",
            missing_count=len(dashboard_missing_synthesis),
            missing_ids=dashboard_missing_synthesis[:20],
            recommended_headline_view=dashboard["metadata"].get("recommendedHeadlineView"),
            generated_from=dashboard["metadata"].get("generatedFrom", []),
        )
        add_check(
            checks,
            "release_metadata_points_to_snapshot",
            release_metadata.get("current_snapshot") == snapshot_dir.name
            and release_metadata.get("recommended_headline_view") == "tiered_synthesis",
            current_snapshot=release_metadata.get("current_snapshot"),
            recommended_headline_view=release_metadata.get("recommended_headline_view"),
        )

    validation_failures = {
        name: result
        for name, result in validation.get("checks", {}).items()
        if not result.get("pass")
    }
    add_check(checks, "model_validation_passes", not validation_failures, failures=validation_failures)
    add_check(checks, "dashboard_qa_passes", bool(dashboard_qa.get("all_checks_passed")), all_checks_passed=dashboard_qa.get("all_checks_passed"))

    nan_hits = []
    for rel_path in CORE_CSVS:
        for line_number, row in enumerate(read_csv(resolve_snapshot_file(snapshot_dir, rel_path)), start=2):
            for column, value in row.items():
                if isinstance(value, str) and value.strip().lower() == "nan":
                    nan_hits.append({"file": rel_path, "line": line_number, "column": column})
                    if len(nan_hits) >= 10:
                        break
            if len(nan_hits) >= 10:
                break
    add_check(checks, "no_literal_nan_in_core_csvs", not nan_hits, samples=nan_hits)

    current_docs = ["SCORING_FRAMEWORK.md", "FINAL_SYSTEM_TRUST_ASSESSMENT.md", "dashboard_qa_summary.json"]
    stale_refs = []
    for rel_path in current_docs:
        text = (snapshot_dir / rel_path).read_text(encoding="utf-8-sig")
        for token in [
            r"C:\Users\gameo\OneDrive\Desktop\test",
            "outputs_cleaned_2026-04-12_coalitionhardening_authoritative",
            "outputs_cleaned_2026-04-11_globaltrust_authoritative",
            "outputs_final_2026-04-05",
        ]:
            if token in text:
                stale_refs.append({"file": rel_path, "token": token})
    add_check(checks, "current_docs_do_not_point_to_stale_snapshots", not stale_refs, stale_refs=stale_refs)

    historical_ref_files = []
    for path in snapshot_dir.rglob("*"):
        if path.is_file() and path.suffix.lower() in {".md", ".json"} and path.name != "plotly.min.js":
            text = path.read_text(encoding="utf-8-sig")
            if re.search(r"C:\\Users\\gameo\\OneDrive\\Desktop\\test|outputs_cleaned_2026-04-1[012]_", text):
                historical_ref_files.append(str(path.relative_to(snapshot_dir)))
    if historical_ref_files:
        warnings.append(
            {
                "name": "historical_reports_reference_older_snapshots",
                "count": len(historical_ref_files),
                "sample": historical_ref_files[:20],
            }
        )

    failed = [check for check in checks if not check["pass"]]
    return {
        "snapshot": snapshot_dir.name,
        "status": "PASS" if not failed else "FAIL",
        "failed_check_count": len(failed),
        "checks": checks,
        "warnings": warnings,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit current snapshot DB, ranking, and dashboard integrity.")
    parser.add_argument("--snapshot-dir", type=Path, default=DEFAULT_SNAPSHOT)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument(
        "--require-upgrade-files",
        action="store_true",
        help="Require improved-snapshot stability, tier, page-type contribution, and high-rank audit outputs.",
    )
    parser.add_argument(
        "--require-confidence-files",
        action="store_true",
        help="Require Pass 3 bootstrap confidence outputs and dashboard confidence metadata.",
    )
    parser.add_argument(
        "--require-role-files",
        action="store_true",
        help="Require Pass 4 command-role classification outputs and dashboard role metadata.",
    )
    parser.add_argument(
        "--require-synthesis-files",
        action="store_true",
        help="Require Pass 5 release-candidate synthesis outputs and dashboard synthesis metadata.",
    )
    args = parser.parse_args()

    summary = audit(
        args.snapshot_dir,
        require_upgrade_files=args.require_upgrade_files,
        require_confidence_files=args.require_confidence_files,
        require_role_files=args.require_role_files,
        require_synthesis_files=args.require_synthesis_files,
    )
    output_path = args.output or args.snapshot_dir / "SNAPSHOT_INTEGRITY_AUDIT.json"
    output_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if summary["status"] != "PASS":
        sys.exit(1)


if __name__ == "__main__":
    main()
