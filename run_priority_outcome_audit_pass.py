from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parent
BASE_SNAPSHOT = ROOT / "outputs_cleaned_2026-04-21_fullverification_authoritative"
DEFAULT_OUTPUT = ROOT / "outputs_cleaned_2026-04-21_outcomeaudit_authoritative"
PRIORITY_FORCE_INCLUDE = ["Napoleon Bonaparte", "Khalid ibn al-Walid"]
MAX_AUDITED_COMMANDERS = 15

OUTCOME_OVERRIDE_SPECS: list[dict[str, str]] = [
    {
        "display_name": "Suleiman the Magnificent",
        "battle_name": "Siege of Vienna (1529)",
        "new_outcome_category": "defeat",
        "override_justification": "Retained page result states Habsburg victory while Suleiman is attached to the Ottoman side.",
        "override_evidence_basis": "page_result_raw=Habsburg victory",
    },
    {
        "display_name": "Suleiman the Magnificent",
        "battle_name": "Siege of Corfu (1537)",
        "new_outcome_category": "defeat",
        "override_justification": "Retained page result states Venetian victory and explicitly notes the Ottomans failed to capture Corfu.",
        "override_evidence_basis": "page_result_raw=Venetian victory Ottomans fail to capture Corfu.",
    },
    {
        "display_name": "Suleiman the Magnificent",
        "battle_name": "Siege of Maribor (1532)",
        "new_outcome_category": "defeat",
        "override_justification": "Retained page result states Habsburg victory while Suleiman is on the opposing Ottoman side.",
        "override_evidence_basis": "page_result_raw=Habsburg victory",
    },
    {
        "display_name": "Suleiman the Magnificent",
        "battle_name": "Siege of Kőszeg",
        "new_outcome_category": "indecisive",
        "override_justification": "Retained page result says the defenders prevented the Ottoman advance into Vienna, which is a non-win for Suleiman but not expressed as a direct enemy victory.",
        "override_evidence_basis": "page_result_raw=The Defenders prevented the Ottoman advance into Vienna",
    },
    {
        "display_name": "Nader Shah",
        "battle_name": "Siege of Mosul (1743)",
        "new_outcome_category": "defeat",
        "override_justification": "Retained page result states Ottoman victory and negotiated Persian withdrawal.",
        "override_evidence_basis": "page_result_raw=Ottoman victory Siege suspended Negotiated Persian withdrawal",
    },
    {
        "display_name": "Flavius Aetius",
        "battle_name": "Battle of Rimini (432)",
        "new_outcome_category": "defeat",
        "override_justification": "Retained page result states Bonifacius was victorious while Aetius is attached to the opposing side.",
        "override_evidence_basis": "page_result_raw=Bonifacius victorious, but mortally wounded",
    },
    {
        "display_name": "Mehmed II",
        "battle_name": "Siege of Krujë (1450)",
        "new_outcome_category": "defeat",
        "override_justification": "Retained page result states Albanian victory while Mehmed II is attached to the Ottoman side.",
        "override_evidence_basis": "page_result_raw=Albanian victory",
    },
    {
        "display_name": "Mehmed II",
        "battle_name": "Siege of Krujë (1466–1467)",
        "new_outcome_category": "defeat",
        "override_justification": "Retained page result states Albanian-Venetian victory while Mehmed II is attached to the Ottoman side.",
        "override_evidence_basis": "page_result_raw=Albanian-Venetian victory",
    },
    {
        "display_name": "Robert E. Lee",
        "battle_name": "Battle of Malvern Hill",
        "new_outcome_category": "defeat",
        "override_justification": "Retained page result states Union victory while Lee is attached to the Confederate side.",
        "override_evidence_basis": "page_result_raw=Union victory",
    },
    {
        "display_name": "Robert E. Lee",
        "battle_name": "Battle of South Mountain",
        "new_outcome_category": "defeat",
        "override_justification": "Retained page result states Union victory while Lee is attached to the Confederate side.",
        "override_evidence_basis": "page_result_raw=Union victory",
    },
    {
        "display_name": "Robert E. Lee",
        "battle_name": "Siege of Fort Pulaski",
        "new_outcome_category": "defeat",
        "override_justification": "Retained page result states Union victory while Lee is attached to the Confederate side.",
        "override_evidence_basis": "page_result_raw=Union victory",
    },
    {
        "display_name": "Robert E. Lee",
        "battle_name": "Second Battle of Rappahannock Station",
        "new_outcome_category": "defeat",
        "override_justification": "Retained page result states Union victory while Lee is attached to the Confederate side.",
        "override_evidence_basis": "page_result_raw=Union victory",
    },
    {
        "display_name": "Robert E. Lee",
        "battle_name": "Battle of Darbytown and New Market Roads",
        "new_outcome_category": "defeat",
        "override_justification": "Retained page result states Union victory while Lee is attached to the Confederate side.",
        "override_evidence_basis": "page_result_raw=Union victory",
    },
    {
        "display_name": "Robert E. Lee",
        "battle_name": "Siege of Petersburg",
        "new_outcome_category": "defeat",
        "override_justification": "Retained page result states Union victory while Lee is attached to the Confederate side.",
        "override_evidence_basis": "page_result_raw=Union victory",
    },
    {
        "display_name": "Robert E. Lee",
        "battle_name": "Battle of Appomattox Court House",
        "new_outcome_category": "defeat",
        "override_justification": "Retained page result states Union victory and surrender of the Army of Northern Virginia while Lee is attached to the Confederate side.",
        "override_evidence_basis": "page_result_raw=Union victory surrender of the Army of Northern Virginia De facto end of the Civil War",
    },
    {
        "display_name": "Robert E. Lee",
        "battle_name": "Battle of White Oak Road",
        "new_outcome_category": "defeat",
        "override_justification": "Retained page result states Union victory while Lee is attached to the Confederate side.",
        "override_evidence_basis": "page_result_raw=Union victory",
    },
    {
        "display_name": "Robert E. Lee",
        "battle_name": "Third Battle of Petersburg",
        "new_outcome_category": "defeat",
        "override_justification": "Retained page result states Union victory and the end of the siege while Lee is attached to the Confederate side.",
        "override_evidence_basis": "page_result_raw=Union victory: End of the Siege of Petersburg and opening of the Appomattox Campaign...",
    },
    {
        "display_name": "Joseph Stalin",
        "battle_name": "Islamic rebellion in Xinjiang (1937)",
        "new_outcome_category": "defeat",
        "override_justification": "Retained page result states provincial government victory while Stalin is attached to the Soviet-backed opposing side.",
        "override_evidence_basis": "page_result_raw=Provincial government victory",
    },
    {
        "display_name": "William Halsey Jr.",
        "battle_name": "Operation Ke",
        "new_outcome_category": "defeat",
        "override_justification": "Retained page result states Japanese operational success while Halsey is attached to the Allied side.",
        "override_evidence_basis": "page_result_raw=Japanese operational success",
    },
    {
        "display_name": "Khalid ibn al-Walid",
        "battle_name": "Siege of Ta'if",
        "new_outcome_category": "indecisive",
        "override_justification": "Retained page result is explicitly inconclusive, so the row should be a non-win rather than unresolved.",
        "override_evidence_basis": "page_result_raw=Inconclusive",
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a focused retained-page outcome audit pass on top-priority commanders.")
    parser.add_argument("--base-snapshot", type=Path, default=BASE_SNAPSHOT, help="Current verified snapshot to audit from.")
    parser.add_argument("--output-snapshot", type=Path, default=DEFAULT_OUTPUT, help="Destination snapshot for the outcome-audit pass.")
    return parser.parse_args()


def run_checked(command: list[str]) -> None:
    subprocess.run(command, check=True)


def load_frame(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str).fillna("")


def write_csv(path: Path, frame: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, encoding="utf-8-sig", quoting=csv.QUOTE_MINIMAL)


def select_audited_commanders(priority: pd.DataFrame) -> list[str]:
    manual = priority.loc[priority["manual_outcome_audit_priority"].eq("yes")].copy()
    manual["risk_score_num"] = pd.to_numeric(manual["risk_score"], errors="coerce").fillna(0)
    manual["current_trust_rank_num"] = pd.to_numeric(manual["current_trust_rank"], errors="coerce").fillna(999999)
    manual = manual.sort_values(["risk_score_num", "current_trust_rank_num"], ascending=[False, True])
    audited = manual["display_name"].head(MAX_AUDITED_COMMANDERS).tolist()
    for name in PRIORITY_FORCE_INCLUDE:
        if name not in audited:
            audited.append(name)
    return audited


def resolve_override_rows(annotated: pd.DataFrame, audited_names: set[str]) -> pd.DataFrame:
    rows: list[dict[str, str]] = []
    for spec in OUTCOME_OVERRIDE_SPECS:
        if spec["display_name"] not in audited_names:
            continue
        match = annotated.loc[
            annotated["display_name"].eq(spec["display_name"]) & annotated["battle_name"].eq(spec["battle_name"])
        ].copy()
        if match.empty:
            raise RuntimeError(f"Override target not found: {spec['display_name']} / {spec['battle_name']}")
        if len(match) != 1:
            raise RuntimeError(f"Override target is not unique: {spec['display_name']} / {spec['battle_name']}")
        row = match.iloc[0]
        rows.append(
            {
                "analytic_commander_id": row["analytic_commander_id"],
                "display_name": row["display_name"],
                "canonical_wikipedia_url": row["canonical_wikipedia_url"],
                "battle_id": row["battle_id"],
                "battle_name": row["battle_name"],
                "wikipedia_title": row["wikipedia_title"],
                "side": row["side"],
                "belligerent": row["belligerent"],
                "old_outcome_category": row["outcome_category"],
                "new_outcome_category": spec["new_outcome_category"],
                "page_result_raw": row["page_result_raw"],
                "page_result_type": row["page_result_type"],
                "override_justification": spec["override_justification"],
                "override_evidence_basis": spec["override_evidence_basis"],
            }
        )
    return pd.DataFrame(rows)


def strict_summary(annotated: pd.DataFrame, display_name: str) -> dict[str, str]:
    strict = annotated.loc[
        annotated["display_name"].eq(display_name) & annotated["eligible_strict"].astype(str).eq("1")
    ].copy()
    page_counter = Counter()
    outcome_counter = Counter()
    for value in strict["page_type"]:
        key = {
            "battle_article": "B",
            "operation_article": "O",
            "campaign_article": "C",
            "war_conflict_article": "W",
        }.get(value, "O")
        page_counter[key] += 1
    for value in strict["outcome_category"]:
        outcome_counter[value] += 1
    known_outcome_count = int(strict["outcome_category"].ne("unknown").sum())
    return {
        "strict_engagement_count": str(len(strict)),
        "page_type_mix": f"B={page_counter.get('B', 0)}; O={page_counter.get('O', 0)}; C={page_counter.get('C', 0)}; W={page_counter.get('W', 0)}",
        "known_outcome_count": str(known_outcome_count),
        "outcome_profile": "V={}; D={}; N={}; U={}".format(
            outcome_counter.get("victory", 0),
            outcome_counter.get("defeat", 0) + outcome_counter.get("major_defeat", 0),
            outcome_counter.get("indecisive", 0)
            + outcome_counter.get("draw", 0)
            + outcome_counter.get("stalemate", 0)
            + outcome_counter.get("disputed", 0),
            outcome_counter.get("unknown", 0),
        ),
        "remaining_unknown_count": str(outcome_counter.get("unknown", 0)),
    }


def classify_group(changed_rows: int, rank_before: float | None, rank_after: float | None, tier_before: str, tier_after: str, confidence_before: str, confidence_after: str, remaining_unknown: int) -> str:
    if changed_rows == 0:
        return "no_material_change"
    rank_delta = abs((rank_after or 0.0) - (rank_before or 0.0)) if rank_before is not None and rank_after is not None else 0.0
    unresolved = remaining_unknown > 0 and confidence_after in {"caution", "moderate"}
    if unresolved and (changed_rows >= 2 or rank_delta >= 3 or tier_before != tier_after):
        return "still_unresolved_needs_manual_judgment"
    if changed_rows >= 3 or rank_delta >= 5 or tier_before != tier_after or confidence_before != confidence_after:
        return "major_correction"
    return "modest_correction"


def to_float(value: str) -> float | None:
    try:
        return float(value)
    except ValueError:
        return None


def build_commander_summary(
    audited_names: list[str],
    priority: pd.DataFrame,
    before_summary: pd.DataFrame,
    after_summary: pd.DataFrame,
    before_annotated: pd.DataFrame,
    after_annotated: pd.DataFrame,
    overrides: pd.DataFrame,
) -> pd.DataFrame:
    priority_lookup = priority.set_index("display_name").to_dict(orient="index")
    before_lookup = before_summary.set_index("display_name").to_dict(orient="index")
    after_lookup = after_summary.set_index("display_name").to_dict(orient="index")
    changed_counts = overrides.groupby("display_name").size().to_dict()
    rows: list[dict[str, str]] = []
    for name in audited_names:
        before_meta = before_lookup.get(name, {})
        after_meta = after_lookup.get(name, {})
        priority_meta = priority_lookup.get(name, {})
        strict_before = strict_summary(before_annotated, name)
        strict_after = strict_summary(after_annotated, name)
        rank_before = to_float(before_meta.get("rank_hierarchical_trust_v2", ""))
        rank_after = to_float(after_meta.get("rank_hierarchical_trust_v2", ""))
        group = classify_group(
            changed_rows=int(changed_counts.get(name, 0)),
            rank_before=rank_before,
            rank_after=rank_after,
            tier_before=before_meta.get("trust_tier_v2", ""),
            tier_after=after_meta.get("trust_tier_v2", ""),
            confidence_before=before_meta.get("trust_confidence_v2", ""),
            confidence_after=after_meta.get("trust_confidence_v2", ""),
            remaining_unknown=int(strict_after["remaining_unknown_count"]),
        )
        rows.append(
            {
                "display_name": name,
                "current_priority_rank_before_pass": priority_meta.get("current_trust_rank", ""),
                "inflation_risk_band_before_pass": priority_meta.get("inflation_risk_band", ""),
                "verification_sensitivity_before_pass": priority_meta.get("verification_sensitivity", ""),
                "strict_engagement_count_before": strict_before["strict_engagement_count"],
                "strict_engagement_count_after": strict_after["strict_engagement_count"],
                "page_type_mix_before": strict_before["page_type_mix"],
                "page_type_mix_after": strict_after["page_type_mix"],
                "known_outcome_count_before": strict_before["known_outcome_count"],
                "known_outcome_count_after": strict_after["known_outcome_count"],
                "outcome_profile_before": strict_before["outcome_profile"],
                "outcome_profile_after": strict_after["outcome_profile"],
                "rank_hierarchical_trust_v2_before": before_meta.get("rank_hierarchical_trust_v2", ""),
                "rank_hierarchical_trust_v2_after": after_meta.get("rank_hierarchical_trust_v2", ""),
                "rank_hierarchical_weighted_before": before_meta.get("rank_hierarchical_weighted", ""),
                "rank_hierarchical_weighted_after": after_meta.get("rank_hierarchical_weighted", ""),
                "trust_tier_before": before_meta.get("trust_tier_v2", ""),
                "trust_tier_after": after_meta.get("trust_tier_v2", ""),
                "trust_confidence_before": before_meta.get("trust_confidence_v2", ""),
                "trust_confidence_after": after_meta.get("trust_confidence_v2", ""),
                "changed_row_count": str(changed_counts.get(name, 0)),
                "remaining_unknown_count_after": strict_after["remaining_unknown_count"],
                "outcome_audit_group": group,
            }
        )
    return pd.DataFrame(rows)


def build_memo(summary: pd.DataFrame, changed_rows: pd.DataFrame, before_summary: pd.DataFrame, after_summary: pd.DataFrame) -> str:
    groups = summary.groupby("outcome_audit_group")["display_name"].apply(list).to_dict()
    materially_overrated = summary.loc[
        summary["outcome_audit_group"].isin(["major_correction", "still_unresolved_needs_manual_judgment"])
        & summary["changed_row_count"].astype(int).gt(0),
        "display_name",
    ].tolist()
    stable = summary.loc[summary["outcome_audit_group"].eq("no_material_change"), "display_name"].tolist()
    top_before = before_summary.sort_values("rank_hierarchical_trust_v2", key=lambda s: pd.to_numeric(s, errors="coerce")).head(10)["display_name"].tolist()
    top_after = after_summary.sort_values("rank_hierarchical_trust_v2", key=lambda s: pd.to_numeric(s, errors="coerce")).head(10)["display_name"].tolist()
    lines = [
        "# Priority Outcome Audit Memo",
        "",
        "## Grouped Results",
        "",
        f"- no material change: {', '.join(groups.get('no_material_change', [])) or 'none'}",
        f"- modest correction: {', '.join(groups.get('modest_correction', [])) or 'none'}",
        f"- major correction: {', '.join(groups.get('major_correction', [])) or 'none'}",
        f"- still unresolved / needs manual judgment: {', '.join(groups.get('still_unresolved_needs_manual_judgment', [])) or 'none'}",
        "",
        "## Highest-Impact Cases",
        "",
        f"- materially overrated because of favorable or unresolved outcome labeling: {', '.join(materially_overrated) or 'none'}",
        f"- stable even after outcome review: {', '.join(stable) or 'none'}",
        "",
        "## Headline Tier Effect",
        "",
        f"- top 10 before: {', '.join(top_before)}",
        f"- top 10 after: {', '.join(top_after)}",
        "- headline takeaway: the core top tier remains broadly intact, but outcome tightening reduces the margin for several model-sensitive commanders and weakens Suleiman's clean-record edge.",
        "",
        "## Changed Rows",
        "",
    ]
    for row in changed_rows.to_dict(orient="records"):
        lines.append(
            f"- {row['display_name']} / {row['battle_name']}: {row['old_outcome_category']} -> {row['new_outcome_category']} ({row['override_justification']})"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    base_snapshot = args.base_snapshot.resolve()
    output_snapshot = args.output_snapshot.resolve()
    if output_snapshot.exists():
        shutil.rmtree(output_snapshot)
    shutil.copytree(base_snapshot, output_snapshot)

    priority = load_frame(base_snapshot / "verification" / "TOP200_OUTCOME_AUDIT_PRIORITY.csv")
    audited_names = select_audited_commanders(priority)
    before_annotated = load_frame(base_snapshot / "derived_scoring" / "commander_engagements_annotated.csv")
    before_summary = load_frame(base_snapshot / "TOP_COMMANDERS_SUMMARY.csv")
    override_rows = resolve_override_rows(before_annotated, set(audited_names))
    write_csv(output_snapshot / "verification" / "verified_outcome_overrides.csv", override_rows)

    run_checked([sys.executable, "build_scoring_framework_package.py", "--output-root", str(output_snapshot)])
    run_checked([sys.executable, "build_ranking_package.py", "--output-root", str(output_snapshot)])
    run_checked([sys.executable, "build_interpretive_layer.py", "--snapshot-dir", str(output_snapshot)])
    run_checked(
        [
            sys.executable,
            "build_ranking_dashboard.py",
            "--snapshot-dir",
            str(output_snapshot),
            "--asset-source-dir",
            str(base_snapshot / "dashboard"),
        ]
    )
    run_checked([sys.executable, "generate_ranking_validation_v2.py", "--snapshot-dir", str(output_snapshot)])

    after_annotated = load_frame(output_snapshot / "derived_scoring" / "commander_engagements_annotated.csv")
    after_summary = load_frame(output_snapshot / "TOP_COMMANDERS_SUMMARY.csv")

    changed_rows = after_annotated.loc[after_annotated["outcome_override_applied"].eq("1")].copy()
    changed_rows = changed_rows[
        [
            "display_name",
            "canonical_wikipedia_url",
            "battle_id",
            "battle_name",
            "wikipedia_title",
            "page_type",
            "side",
            "belligerent",
            "outcome_category_pre_override",
            "outcome_category",
            "page_result_type",
            "page_result_raw",
            "outcome_override_justification",
            "outcome_override_evidence_basis",
        ]
    ].rename(
        columns={
            "outcome_category_pre_override": "old_outcome_category",
            "outcome_category": "new_outcome_category",
            "outcome_override_justification": "override_justification",
            "outcome_override_evidence_basis": "override_evidence_basis",
        }
    )
    write_csv(output_snapshot / "verification" / "PRIORITY_OUTCOME_AUDIT_CHANGED_ROWS.csv", changed_rows)

    summary = build_commander_summary(
        audited_names=audited_names,
        priority=priority,
        before_summary=before_summary,
        after_summary=after_summary,
        before_annotated=before_annotated,
        after_annotated=after_annotated,
        overrides=changed_rows,
    )
    write_csv(output_snapshot / "verification" / "PRIORITY_OUTCOME_AUDIT_COMMANDER_SUMMARY.csv", summary)

    affected = summary.loc[summary["changed_row_count"].astype(int).gt(0)].copy()
    write_csv(output_snapshot / "verification" / "PRIORITY_OUTCOME_AUDIT_AFFECTED_MOVEMENT.csv", affected)

    memo = build_memo(summary, changed_rows, before_summary, after_summary)
    memo_path = output_snapshot / "verification" / "PRIORITY_OUTCOME_AUDIT_MEMO.md"
    memo_path.write_text(memo, encoding="utf-8")

    summary_payload = {
        "base_snapshot": str(base_snapshot),
        "output_snapshot": str(output_snapshot),
        "audited_commander_count": int(len(summary)),
        "audited_commanders": audited_names,
        "changed_row_count": int(len(changed_rows)),
        "changed_commander_count": int(summary["changed_row_count"].astype(int).gt(0).sum()),
        "group_counts": summary["outcome_audit_group"].value_counts().to_dict(),
    }
    (output_snapshot / "verification" / "PRIORITY_OUTCOME_AUDIT_SUMMARY.json").write_text(
        json.dumps(summary_payload, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
