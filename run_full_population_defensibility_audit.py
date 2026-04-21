from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(r"C:\Users\gameo\OneDrive\Desktop\test")
BASE_SNAPSHOT = ROOT / "outputs_cleaned_2026-04-21_top200defensibility_authoritative"
OUTPUT_SNAPSHOT = ROOT / "outputs_cleaned_2026-04-21_fullpopulation_authoritative"

NEUTRAL_PREFIX_RULES: list[tuple[str, str, str]] = [
    ("inconclusive", "indecisive", "Retained page result is explicitly inconclusive."),
    ("status quo ante bellum", "stalemate", "Retained page result is explicitly status quo ante bellum."),
    ("ceasefire", "indecisive", "Retained page result is explicitly a ceasefire."),
    ("truce", "indecisive", "Retained page result is explicitly a truce."),
]

FACTION_ALIAS_RULES: list[tuple[str, set[str]]] = [
    ("union", {"union", "federal", "american", "usa", "united", "states"}),
    ("confederate", {"confederate", "confederacy"}),
    ("axis", {"axis", "german", "japanese", "italian"}),
    ("ottoman", {"ottoman", "turkish", "turco"}),
    ("habsburg", {"habsburg", "austrian", "austria"}),
    ("soviet", {"soviet", "russian", "ussr"}),
    ("french", {"french", "france"}),
    ("muslim", {"muslim", "rashidun", "caliphate", "islamic"}),
    ("parliamentarian", {"parliamentarian", "parliament"}),
    ("royalist", {"royalist", "royalists"}),
    ("crusader", {"crusader", "crusaders"}),
    ("macedonian", {"macedonian", "macedon"}),
    ("communist", {"communist", "communists"}),
    ("nationalist", {"nationalist", "nationalists", "kuomintang"}),
    ("rebel", {"rebel", "rebels"}),
    ("cossack", {"cossack", "cossacks"}),
    ("carthaginian", {"carthaginian", "carthage"}),
    ("sasanian", {"sasanian", "persian", "iranian"}),
    ("jin", {"jin"}),
    ("saudi", {"saudi", "arabia"}),
    ("serbian", {"serbian", "serbia"}),
    ("afghan", {"afghan", "afghanistan", "durrani"}),
    ("syrian", {"syrian", "syria"}),
    ("bulgarian", {"bulgarian", "bulgaria"}),
    ("sikh", {"sikh", "sikhs"}),
    ("mongol", {"mongol", "mongols"}),
    ("japanese", {"japanese", "japan"}),
    ("albanian", {"albanian", "albania"}),
    ("russian", {"russian", "russia"}),
    ("bolshevik", {"bolshevik", "bolsheviks"}),
    ("u.s.", {"american", "usa", "united", "states"}),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a full-population corrective audit over the ranked commander universe.")
    parser.add_argument("--base-snapshot", type=Path, default=BASE_SNAPSHOT)
    parser.add_argument("--output-snapshot", type=Path, default=OUTPUT_SNAPSHOT)
    return parser.parse_args()


def run_checked(command: list[str]) -> None:
    subprocess.run(command, check=True)


def load_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str).fillna("")


def write_csv(path: Path, frame: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, encoding="utf-8-sig", quoting=csv.QUOTE_MINIMAL)


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def to_float(value: Any) -> float | None:
    text = normalize_text(value)
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def token_set(value: str) -> set[str]:
    return {token for token in re.sub(r"[^a-z0-9]+", " ", value.lower()).split() if len(token) >= 3}


def select_ranked_names(base_snapshot: Path) -> list[str]:
    ranking = load_csv(base_snapshot / "RANKING_RESULTS_SENSITIVITY.csv")
    ranking["rank_hierarchical_trust_v2_num"] = pd.to_numeric(ranking["rank_hierarchical_trust_v2"], errors="coerce")
    ranking = ranking.loc[ranking["rank_hierarchical_trust_v2_num"].notna() & ranking["rank_hierarchical_trust_v2_num"].gt(0)]
    ranking = ranking.sort_values(["rank_hierarchical_trust_v2_num", "display_name"], ascending=[True, True])
    return ranking["display_name"].tolist()


def infer_conservative_outcome(row: pd.Series) -> tuple[str, str, str] | None:
    if normalize_text(row["side"]) == "multiple_sides":
        return None

    raw = normalize_text(row["page_result_raw"])
    raw_lower = raw.lower()
    if not raw_lower:
        return None

    for prefix, outcome, justification in NEUTRAL_PREFIX_RULES:
        if raw_lower.startswith(prefix):
            return outcome, justification, f"page_result_raw={raw}"

    victory_mentions = raw_lower.count(" victory")
    operational_mentions = raw_lower.count(" operational success")
    if victory_mentions + operational_mentions != 1:
        return None
    if " first " in raw_lower or " second " in raw_lower:
        return None

    side_to_belligerent = {
        "side_a": normalize_text(row["belligerent_1_raw"]),
        "side_b": normalize_text(row["belligerent_2_raw"]),
        "side_c": normalize_text(row["belligerent_3_raw"]),
    }

    for label, aliases in FACTION_ALIAS_RULES:
        if raw_lower.startswith(f"{label} victory") or raw_lower.startswith(f"{label} operational success"):
            matched_sides = [
                side
                for side, belligerent in side_to_belligerent.items()
                if belligerent and token_set(belligerent).intersection(aliases)
            ]
            matched_sides = sorted(set(matched_sides))
            if len(matched_sides) != 1:
                return None
            winner_side = matched_sides[0]
            if normalize_text(row["side"]) == winner_side:
                justification = (
                    f"Retained page result begins with `{label}` and that label maps uniquely to the commander's side on the retained page."
                )
                return "victory", justification, f"page_result_raw={raw}"
            justification = (
                f"Retained page result begins with `{label}` and that label maps uniquely to the opposing side on the retained page."
            )
            return "defeat", justification, f"page_result_raw={raw}"

    return None


def is_conservative_override(old_outcome: str, new_outcome: str) -> bool:
    if old_outcome == new_outcome:
        return False
    if old_outcome == "unknown":
        return True
    if old_outcome == "victory" and new_outcome == "defeat":
        return True
    if old_outcome in {"indecisive", "stalemate"} and new_outcome == "defeat":
        return True
    return False


def build_override_frame(base_snapshot: Path, ranked_names: set[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    annotated = load_csv(base_snapshot / "derived_scoring" / "commander_engagements_annotated.csv")
    battles = load_csv(base_snapshot / "battles_clean.csv")
    annotated = annotated.merge(
        battles[["battle_id", "belligerent_1_raw", "belligerent_2_raw", "belligerent_3_raw"]],
        on="battle_id",
        how="left",
    )
    annotated = annotated.loc[
        annotated["display_name"].isin(ranked_names) & annotated["eligible_strict"].eq("1")
    ].copy()

    existing_override_path = base_snapshot / "verification" / "verified_outcome_overrides.csv"
    existing_overrides = load_csv(existing_override_path) if existing_override_path.exists() else pd.DataFrame()

    auto_rows: list[dict[str, str]] = []
    unresolved_rows: list[dict[str, str]] = []
    for _, row in annotated.iterrows():
        inferred = infer_conservative_outcome(row)
        if inferred is None:
            if row["outcome_category"] == "unknown" and normalize_text(row["page_result_raw"]):
                unresolved_rows.append(
                    {
                        "display_name": row["display_name"],
                        "canonical_wikipedia_url": row["canonical_wikipedia_url"],
                        "battle_id": row["battle_id"],
                        "battle_name": row["battle_name"],
                        "page_type": row["page_type"],
                        "side": row["side"],
                        "page_result_raw": row["page_result_raw"],
                        "current_outcome_category": row["outcome_category"],
                        "unresolved_reason": "retained_page_result_present_but_not_deterministic_under_conservative_rules",
                    }
                )
            continue

        new_outcome, justification, evidence_basis = inferred
        old_outcome = normalize_text(row["outcome_category"])
        if not is_conservative_override(old_outcome, new_outcome):
            continue

        auto_rows.append(
            {
                "analytic_commander_id": row["analytic_commander_id"],
                "display_name": row["display_name"],
                "canonical_wikipedia_url": row["canonical_wikipedia_url"],
                "battle_id": row["battle_id"],
                "battle_name": row["battle_name"],
                "wikipedia_title": row["wikipedia_title"],
                "side": row["side"],
                "belligerent": row["belligerent"],
                "old_outcome_category": old_outcome,
                "new_outcome_category": new_outcome,
                "page_result_raw": row["page_result_raw"],
                "page_result_type": row["page_result_type"],
                "override_justification": justification,
                "override_evidence_basis": evidence_basis,
                "override_source": "full_population_auto",
            }
        )

    auto_overrides = pd.DataFrame(auto_rows)
    if not existing_overrides.empty:
        existing_overrides = existing_overrides.copy()
        if "override_source" not in existing_overrides.columns:
            existing_overrides["override_source"] = "prior_outcome_audit"
        combined = pd.concat([existing_overrides, auto_overrides], ignore_index=True, sort=False)
    else:
        combined = auto_overrides.copy()

    if not combined.empty:
        combined = combined.sort_values(["display_name", "battle_name", "new_outcome_category"]).drop_duplicates(
            subset=["analytic_commander_id", "battle_id"],
            keep="last",
        )

    return combined.fillna(""), pd.DataFrame(unresolved_rows).fillna("")


def strict_summary(annotated: pd.DataFrame, display_name: str) -> dict[str, str]:
    strict = annotated.loc[
        annotated["display_name"].eq(display_name) & annotated["eligible_strict"].eq("1")
    ].copy()
    page_counter = Counter()
    outcome_counter = Counter(strict["outcome_category"])
    for page_type in strict["page_type"]:
        key = {
            "battle_article": "B",
            "operation_article": "O",
            "campaign_article": "C",
            "war_conflict_article": "W",
        }.get(page_type, "O")
        page_counter[key] += 1
    unknown_with_page_result = int(
        strict["outcome_category"].eq("unknown").astype(int)
        .mul(strict["page_result_raw"].map(lambda value: 1 if normalize_text(value) else 0))
        .sum()
    )
    return {
        "strict_engagement_count": str(len(strict)),
        "page_type_mix": f"B={page_counter.get('B', 0)}; O={page_counter.get('O', 0)}; C={page_counter.get('C', 0)}; W={page_counter.get('W', 0)}",
        "known_outcome_count": str(int(strict["outcome_category"].ne("unknown").sum())),
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
        "remaining_unknown_with_page_result": str(unknown_with_page_result),
    }


def classify_outcome_review(changed_rows: int, remaining_unknown_with_page_result: int) -> str:
    if changed_rows > 0:
        if remaining_unknown_with_page_result > 0:
            return "corrected_but_partially_unresolved"
        return "corrected"
    if remaining_unknown_with_page_result > 0:
        return "unresolved_after_review"
    return "confirmed_no_change"


def classify_stability(rank_before: float | None, rank_after: float | None, tier_before: str, tier_after: str, confidence_before: str, confidence_after: str) -> str:
    rank_delta = abs((rank_after or 0.0) - (rank_before or 0.0)) if rank_before is not None and rank_after is not None else 0.0
    if tier_before != tier_after or confidence_before != confidence_after or rank_delta >= 5:
        return "material_change"
    return "confirmed_stable_after_review"


def structural_classification(row: pd.Series) -> str:
    total_rows = max(int(normalize_text(row["total_rows"]) or "0"), 1)
    suspect_rows = int(normalize_text(row["structurally_suspect_rows"]) or "0")
    broad_rows = int(normalize_text(row["verified_broad_rows"]) or "0")
    verified_core_rows = int(normalize_text(row["verified_core_rows"]) or "0")
    dominant_status = normalize_text(row["dominant_verification_status"])
    suspect_share = suspect_rows / total_rows
    broad_share = broad_rows / total_rows
    if dominant_status == "structurally_suspect" and (suspect_rows >= 3 or suspect_share >= 0.4):
        return "high_priority_manual_concern"
    if verified_core_rows == 0 and total_rows >= 2:
        return "high_priority_manual_concern"
    if suspect_rows >= 1 or broad_rows >= 3 or broad_share >= 0.5:
        return "materially_inflated"
    if broad_rows >= 1:
        return "mildly_inflated"
    return "structurally_clean"


def dedupe_by_display_name(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty or "display_name" not in frame.columns:
        return frame
    working = frame.copy()
    for column in ["verified_core_rows", "total_rows", "known_outcome_count", "rank_hierarchical_trust_v2"]:
        if column in working.columns:
            working[f"__sort_{column}"] = pd.to_numeric(working[column], errors="coerce").fillna(-1)
    sort_columns = [column for column in working.columns if column.startswith("__sort_")]
    if sort_columns:
        working = working.sort_values(sort_columns, ascending=[False] * len(sort_columns))
    deduped = working.drop_duplicates(subset=["display_name"], keep="first").copy()
    drop_columns = [column for column in deduped.columns if column.startswith("__sort_")]
    return deduped.drop(columns=drop_columns, errors="ignore")


def build_commander_results(
    ranked_names: list[str],
    structural_summary: pd.DataFrame,
    before_summary: pd.DataFrame,
    after_summary: pd.DataFrame,
    before_annotated: pd.DataFrame,
    after_annotated: pd.DataFrame,
    changed_rows: pd.DataFrame,
    unresolved_rows: pd.DataFrame,
) -> pd.DataFrame:
    structural_lookup = dedupe_by_display_name(structural_summary).set_index("display_name").to_dict(orient="index")
    before_lookup = dedupe_by_display_name(before_summary).set_index("display_name").to_dict(orient="index")
    after_lookup = dedupe_by_display_name(after_summary).set_index("display_name").to_dict(orient="index")
    changed_counts = changed_rows.groupby("display_name").size().to_dict() if not changed_rows.empty else {}
    unresolved_counts = unresolved_rows.groupby("display_name").size().to_dict() if not unresolved_rows.empty else {}

    rows: list[dict[str, str]] = []
    for name in ranked_names:
        structural = structural_lookup.get(name, {})
        before_meta = before_lookup.get(name, {})
        after_meta = after_lookup.get(name, {})
        before_strict = strict_summary(before_annotated, name)
        after_strict = strict_summary(after_annotated, name)
        rows.append(
            {
                "display_name": name,
                "canonical_wikipedia_url": structural.get("canonical_wikipedia_url", before_meta.get("canonical_wikipedia_url", "")),
                "structural_classification": structural_classification(pd.Series(structural)) if structural else "structurally_clean",
                "dominant_verification_status": structural.get("dominant_verification_status", ""),
                "total_rows": structural.get("total_rows", ""),
                "verified_core_rows": structural.get("verified_core_rows", ""),
                "verified_broad_rows": structural.get("verified_broad_rows", ""),
                "structurally_suspect_rows": structural.get("structurally_suspect_rows", ""),
                "quarantined_rows": structural.get("quarantined_rows", ""),
                "outcome_review_status": classify_outcome_review(
                    changed_rows=int(changed_counts.get(name, 0)),
                    remaining_unknown_with_page_result=int(after_strict["remaining_unknown_with_page_result"]),
                ),
                "stability_after_review": classify_stability(
                    rank_before=to_float(before_meta.get("rank_hierarchical_trust_v2")),
                    rank_after=to_float(after_meta.get("rank_hierarchical_trust_v2")),
                    tier_before=normalize_text(before_meta.get("trust_tier_v2")),
                    tier_after=normalize_text(after_meta.get("trust_tier_v2")),
                    confidence_before=normalize_text(before_meta.get("trust_confidence_v2")),
                    confidence_after=normalize_text(after_meta.get("trust_confidence_v2")),
                ),
                "strict_engagement_count_before": before_strict["strict_engagement_count"],
                "strict_engagement_count_after": after_strict["strict_engagement_count"],
                "page_type_mix_before": before_strict["page_type_mix"],
                "page_type_mix_after": after_strict["page_type_mix"],
                "known_outcome_count_before": before_strict["known_outcome_count"],
                "known_outcome_count_after": after_strict["known_outcome_count"],
                "outcome_profile_before": before_strict["outcome_profile"],
                "outcome_profile_after": after_strict["outcome_profile"],
                "changed_row_count": str(changed_counts.get(name, 0)),
                "remaining_unknown_count_after": after_strict["remaining_unknown_count"],
                "remaining_unknown_with_page_result_after": after_strict["remaining_unknown_with_page_result"],
                "unresolved_row_count_after": str(unresolved_counts.get(name, 0)),
                "rank_hierarchical_trust_v2_before": before_meta.get("rank_hierarchical_trust_v2", ""),
                "rank_hierarchical_trust_v2_after": after_meta.get("rank_hierarchical_trust_v2", ""),
                "rank_hierarchical_weighted_before": before_meta.get("rank_hierarchical_weighted", ""),
                "rank_hierarchical_weighted_after": after_meta.get("rank_hierarchical_weighted", ""),
                "trust_tier_before": before_meta.get("trust_tier_v2", ""),
                "trust_tier_after": after_meta.get("trust_tier_v2", ""),
                "trust_confidence_before": before_meta.get("trust_confidence_v2", ""),
                "trust_confidence_after": after_meta.get("trust_confidence_v2", ""),
            }
        )
    return pd.DataFrame(rows)


def build_memo(results: pd.DataFrame, after_summary: pd.DataFrame) -> str:
    structural_counts = results["structural_classification"].value_counts().to_dict()
    outcome_counts = results["outcome_review_status"].value_counts().to_dict()
    stability_counts = results["stability_after_review"].value_counts().to_dict()
    top_after = after_summary.sort_values("rank_hierarchical_trust_v2", key=lambda s: pd.to_numeric(s, errors="coerce")).head(15)
    lines = [
        "# Full Population Defensibility Memo",
        "",
        "## Reviewed Universe",
        "",
        f"- ranked commanders reviewed: {len(results)}",
        f"- structurally clean: {structural_counts.get('structurally_clean', 0)}",
        f"- mildly inflated: {structural_counts.get('mildly_inflated', 0)}",
        f"- materially inflated: {structural_counts.get('materially_inflated', 0)}",
        f"- high-priority manual concern: {structural_counts.get('high_priority_manual_concern', 0)}",
        "",
        "## Outcome Review",
        "",
        f"- corrected: {outcome_counts.get('corrected', 0)}",
        f"- corrected but partially unresolved: {outcome_counts.get('corrected_but_partially_unresolved', 0)}",
        f"- unresolved after review: {outcome_counts.get('unresolved_after_review', 0)}",
        f"- confirmed no change: {outcome_counts.get('confirmed_no_change', 0)}",
        "",
        "## Stability",
        "",
        f"- confirmed stable after review: {stability_counts.get('confirmed_stable_after_review', 0)}",
        f"- material change: {stability_counts.get('material_change', 0)}",
        "",
        "## Final Trust-First Top Tier",
        "",
    ]
    for _, row in top_after.iterrows():
        lines.append(
            f"- rank {row['rank_hierarchical_trust_v2']}: {row['display_name']} ({row['trust_tier_v2']}, {row['trust_confidence_v2']})"
        )
    lines.append("")
    lines.append("## Residual Weaknesses")
    lines.append("")
    lines.append(
        "- Remaining weaknesses are concentrated in commanders whose retained pages still have non-deterministic result text, ambiguous side labeling, or structurally broad support that conservative rules refuse to over-interpret."
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    base_snapshot = args.base_snapshot.resolve()
    output_snapshot = args.output_snapshot.resolve()
    if output_snapshot.exists():
        shutil.rmtree(output_snapshot)
    shutil.copytree(base_snapshot, output_snapshot)

    ranked_names = select_ranked_names(base_snapshot)
    ranked_set = set(ranked_names)
    structural_summary = load_csv(base_snapshot / "verification" / "structural_commander_summary.csv")
    before_summary = load_csv(base_snapshot / "TOP_COMMANDERS_SUMMARY.csv")
    before_annotated = load_csv(base_snapshot / "derived_scoring" / "commander_engagements_annotated.csv")

    override_frame, unresolved_pre = build_override_frame(base_snapshot, ranked_set)
    write_csv(output_snapshot / "verification" / "verified_outcome_overrides.csv", override_frame)
    if not unresolved_pre.empty:
        write_csv(output_snapshot / "verification" / "FULL_POPULATION_UNRESOLVED_ROWS_PREBUILD.csv", unresolved_pre)

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

    after_summary = load_csv(output_snapshot / "TOP_COMMANDERS_SUMMARY.csv")
    after_annotated = load_csv(output_snapshot / "derived_scoring" / "commander_engagements_annotated.csv")

    changed_rows = after_annotated.loc[
        after_annotated["display_name"].isin(ranked_set) & after_annotated["outcome_override_applied"].eq("1")
    ].copy()
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
    write_csv(output_snapshot / "verification" / "FULL_POPULATION_CHANGED_ROWS.csv", changed_rows)

    unresolved_after = after_annotated.loc[
        after_annotated["display_name"].isin(ranked_set)
        & after_annotated["eligible_strict"].eq("1")
        & after_annotated["outcome_category"].eq("unknown")
        & after_annotated["page_result_raw"].map(lambda value: 1 if normalize_text(value) else 0).eq(1)
    ].copy()
    if not unresolved_after.empty:
        unresolved_after = unresolved_after[
            [
                "display_name",
                "canonical_wikipedia_url",
                "battle_id",
                "battle_name",
                "page_type",
                "side",
                "page_result_raw",
                "page_result_type",
                "outcome_inference_method",
                "outcome_inference_confidence",
            ]
        ]
    write_csv(output_snapshot / "verification" / "FULL_POPULATION_UNRESOLVED_ROWS.csv", unresolved_after)

    results = build_commander_results(
        ranked_names=ranked_names,
        structural_summary=structural_summary,
        before_summary=before_summary,
        after_summary=after_summary,
        before_annotated=before_annotated,
        after_annotated=after_annotated,
        changed_rows=changed_rows,
        unresolved_rows=unresolved_after,
    )
    write_csv(output_snapshot / "verification" / "FULL_POPULATION_COMMANDER_RESULTS.csv", results)
    write_csv(
        output_snapshot / "verification" / "FULL_POPULATION_AFFECTED_MOVEMENT.csv",
        results.loc[
            results["changed_row_count"].astype(int).gt(0)
            | results["stability_after_review"].eq("material_change")
            | results["outcome_review_status"].eq("unresolved_after_review")
            | results["outcome_review_status"].eq("corrected_but_partially_unresolved")
        ].copy(),
    )

    memo = build_memo(results, after_summary)
    (output_snapshot / "verification" / "FULL_POPULATION_MEMO.md").write_text(memo, encoding="utf-8")

    summary_payload = {
        "base_snapshot": str(base_snapshot),
        "output_snapshot": str(output_snapshot),
        "ranked_population_count": len(ranked_names),
        "changed_row_count": int(len(changed_rows)),
        "changed_commander_count": int(results["changed_row_count"].astype(int).gt(0).sum()),
        "outcome_review_status_counts": results["outcome_review_status"].value_counts().to_dict(),
        "stability_counts": results["stability_after_review"].value_counts().to_dict(),
        "structural_classification_counts": results["structural_classification"].value_counts().to_dict(),
    }
    (output_snapshot / "verification" / "FULL_POPULATION_SUMMARY.json").write_text(
        json.dumps(summary_payload, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
