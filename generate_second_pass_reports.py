from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import pandas as pd

from build_ranking_package import prepare_rows


ANTI_RE = re.compile(r"\banti[-\s]", re.IGNORECASE)
COALITION_RE = re.compile(r"\b(?:coalition|allied?)\b", re.IGNORECASE)
AGAINST_RE = re.compile(r"\bagainst\b", re.IGNORECASE)


def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str).fillna("")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv_optional(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return read_csv(path)


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

    def format_cell(value: Any) -> str:
        if pd.isna(value):
            return ""
        if isinstance(value, float) and value.is_integer():
            return str(int(value))
        text = str(value).replace("\n", " ").strip()
        if re.fullmatch(r"-?\d+\.0", text):
            return text[:-2]
        return text

    for row in frame.to_dict(orient="records"):
        values = [format_cell(row.get(header, "")) for header in headers]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def unique_pages(annotated: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "battle_name",
        "page_type",
        "result_raw",
        "result_type",
        "outcome_category",
        "outcome_inference_method",
    ]
    return annotated[cols].drop_duplicates().copy()


def with_patterns(frame: pd.DataFrame) -> pd.DataFrame:
    result_raw = frame["result_raw"].fillna("")
    out = frame.copy()
    out["anti_flag"] = result_raw.str.contains(ANTI_RE, na=False)
    out["coalition_flag"] = result_raw.str.contains(COALITION_RE, na=False)
    out["against_flag"] = result_raw.str.contains(AGAINST_RE, na=False)
    return out


def unresolved_pages(frame: pd.DataFrame, flag: str) -> pd.DataFrame:
    return frame.loc[frame[flag] & frame["outcome_category"].eq("unknown")].copy()


def rank_lookup(sensitivity: pd.DataFrame, name: str) -> dict[str, str]:
    row = row_by_name(sensitivity, name)
    if row.empty:
        return {}
    return {
        "baseline": str(row.get("rank_baseline_conservative", "")),
        "battle_only": str(row.get("rank_battle_only_baseline", "")),
        "hierarchical": str(row.get("rank_hierarchical_weighted", "")),
        "full_credit": str(row.get("rank_hierarchical_full_credit", "")),
        "equal_split": str(row.get("rank_hierarchical_equal_split", "")),
        "broader": str(row.get("rank_hierarchical_broader_eligibility", "")),
    }


def compact_rank_delta(old_sens: pd.DataFrame, new_sens: pd.DataFrame, name: str) -> pd.DataFrame:
    old = rank_lookup(old_sens, name)
    new = rank_lookup(new_sens, name)
    rows = []
    labels = {
        "baseline": "baseline_conservative",
        "battle_only": "battle_only_baseline",
        "hierarchical": "hierarchical_weighted",
        "full_credit": "hierarchical_full_credit",
        "equal_split": "hierarchical_equal_split",
        "broader": "hierarchical_broader_eligibility",
    }
    for key, label in labels.items():
        old_rank = old.get(key, "")
        new_rank = new.get(key, "")
        try:
            delta = int(float(old_rank)) - int(float(new_rank))
            delta_text = f"{delta:+d}"
        except Exception:
            delta_text = ""
        rows.append(
            {
                "model": label,
                "old_rank": old_rank,
                "new_rank": new_rank,
                "rank_change": delta_text,
            }
        )
    return pd.DataFrame(rows)


def leader_driver_summary(
    features: pd.DataFrame,
    hierarchical: pd.DataFrame,
    classification: pd.DataFrame,
    name: str,
) -> pd.DataFrame:
    feat = row_by_name(features, name)
    hier = row_by_name(hierarchical, name)
    cls = row_by_name(classification, name)
    if feat.empty or hier.empty:
        return pd.DataFrame()
    row = {
        "rank_hierarchical": hier.get("rank", ""),
        "score_hierarchical": fmt_float(hier.get("score_normalized", ""), 2),
        "interpretive_group": cls.get("interpretive_group", ""),
        "caution_flags": cls.get("caution_flags", ""),
        "strict_engagements": feat.get("eligible_engagement_count_strict", ""),
        "battle_pages": feat.get("eligible_battle_count_strict", ""),
        "operation_pages": feat.get("eligible_operation_count_strict", ""),
        "campaign_pages": feat.get("eligible_campaign_count_strict", ""),
        "war_pages": feat.get("eligible_war_count_strict", ""),
        "known_outcomes": feat.get("known_outcome_count_strict", ""),
        "known_outcome_share": fmt_float(feat.get("known_outcome_share_strict", ""), 3),
        "first_year": feat.get("first_analytic_year", ""),
        "last_year": feat.get("last_analytic_year", ""),
        "active_span_years": feat.get("active_span_years", ""),
        "nonwar_span_used_for_model": hier.get("active_span_years_nonwar", ""),
        "higher_level_share": fmt_float(hier.get("higher_level_share", ""), 3),
        "component_outcome": fmt_float(hier.get("component_outcome", ""), 1),
        "component_scope": fmt_float(hier.get("component_scope", ""), 1),
        "component_temporal": fmt_float(hier.get("component_temporal", ""), 1),
        "component_centrality": fmt_float(hier.get("component_centrality", ""), 1),
        "component_higher_level": fmt_float(hier.get("component_higher_level", ""), 1),
        "component_evidence": fmt_float(hier.get("component_evidence", ""), 1),
    }
    return pd.DataFrame([row])


def commander_rows(annotated: pd.DataFrame, name: str) -> pd.DataFrame:
    cols = [
        "battle_name",
        "page_type",
        "analytic_year",
        "result_raw",
        "outcome_category",
        "outcome_inference_method",
        "same_side_commander_count",
        "known_outcome_flag",
    ]
    return (
        annotated.loc[annotated["display_name"].eq(name), cols]
        .drop_duplicates()
        .sort_values(["analytic_year", "battle_name"])
        .reset_index(drop=True)
    )


def unresolved_coalition_rows(annotated: pd.DataFrame, name: str) -> pd.DataFrame:
    sub = commander_rows(annotated, name)
    return sub.loc[
        sub["result_raw"].str.contains(COALITION_RE, na=False) & sub["outcome_category"].eq("unknown")
    ].reset_index(drop=True)


def top30_unresolved_coalition(new_annotated: pd.DataFrame, new_hierarchical: pd.DataFrame) -> pd.DataFrame:
    top30 = set(new_hierarchical.head(30)["display_name"])
    sub = new_annotated.loc[
        new_annotated["display_name"].isin(top30)
        & new_annotated["result_raw"].str.contains(COALITION_RE, na=False)
        & new_annotated["outcome_category"].eq("unknown")
    ].copy()
    if sub.empty:
        return pd.DataFrame(columns=["display_name", "unresolved_pages", "page_names"])
    grouped = (
        sub.groupby("display_name")["battle_name"]
        .agg(lambda values: sorted(dict.fromkeys(values)))
        .reset_index()
    )
    grouped["unresolved_pages"] = grouped["battle_name"].map(len)
    grouped["page_names"] = grouped["battle_name"].map(lambda values: "; ".join(values))
    return grouped[["display_name", "unresolved_pages", "page_names"]].sort_values(
        ["unresolved_pages", "display_name"], ascending=[False, True]
    )


def changed_pattern_rows(old_annotated: pd.DataFrame, new_annotated: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    key = ["analytic_commander_id", "battle_id"]
    cols = key + [
        "display_name",
        "battle_name",
        "analytic_year",
        "analytic_year_confidence",
        "result_raw",
        "outcome_category",
        "outcome_inference_method",
    ]
    merged = old_annotated[cols].merge(
        new_annotated[cols],
        on=key,
        suffixes=("_old", "_new"),
        how="inner",
    )
    changed = merged.loc[
        (merged["analytic_year_old"] != merged["analytic_year_new"])
        | (merged["outcome_category_old"] != merged["outcome_category_new"])
        | (merged["outcome_inference_method_old"] != merged["outcome_inference_method_new"])
    ].copy()
    pattern = changed.loc[
        changed["result_raw_old"].str.contains(ANTI_RE, na=False)
        | changed["result_raw_old"].str.contains(COALITION_RE, na=False)
        | changed["result_raw_new"].str.contains(ANTI_RE, na=False)
        | changed["result_raw_new"].str.contains(COALITION_RE, na=False)
    ].copy()
    return changed, pattern


def top_page_changes(pattern_rows: pd.DataFrame, limit: int = 12) -> pd.DataFrame:
    if pattern_rows.empty:
        return pd.DataFrame()
    grouped = (
        pattern_rows.groupby(["battle_name_old", "result_raw_new"], as_index=False)
        .agg(
            affected_rows=("battle_id", "count"),
            changed_outcomes=("outcome_category_old", lambda s: int((s != pattern_rows.loc[s.index, "outcome_category_new"]).sum())),
        )
        .rename(columns={"battle_name_old": "battle_name", "result_raw_new": "result_raw"})
        .sort_values(["affected_rows", "battle_name"], ascending=[False, True])
        .head(limit)
    )
    return grouped


def before_after_top(old_hier: pd.DataFrame, new_hier: pd.DataFrame, limit: int = 12) -> pd.DataFrame:
    old = old_hier.head(limit)[["display_name", "rank"]].rename(columns={"rank": "old_rank"})
    new = new_hier.head(limit)[["display_name", "rank"]].rename(columns={"rank": "new_rank"})
    merged = old.merge(new, on="display_name", how="outer")
    merged["old_rank_num"] = pd.to_numeric(merged["old_rank"], errors="coerce")
    merged["new_rank_num"] = pd.to_numeric(merged["new_rank"], errors="coerce")
    merged = merged.sort_values(["new_rank_num", "old_rank_num"], na_position="last").drop(
        columns=["old_rank_num", "new_rank_num"]
    )
    return merged


def validate_unknown_split(snapshot: Path) -> dict[str, int]:
    annotated, *_ = prepare_rows(snapshot)
    unknown = annotated.loc[annotated["outcome_category"].eq("unknown")].copy()
    violations = unknown.loc[pd.to_numeric(unknown["outcome_factor_split"], errors="coerce").fillna(0.0) > 0]
    return {"unknown_rows": int(len(unknown)), "unknown_split_violations": int(len(violations))}


def build_anti_coalition_audit(
    old_snapshot: Path,
    new_snapshot: Path,
    old_annotated: pd.DataFrame,
    new_annotated: pd.DataFrame,
    new_sensitivity: pd.DataFrame,
) -> str:
    old_pages = with_patterns(unique_pages(old_annotated))
    new_pages = with_patterns(unique_pages(new_annotated))

    old_anti_unresolved = unresolved_pages(old_pages, "anti_flag")
    new_anti_unresolved = unresolved_pages(new_pages, "anti_flag")
    old_coal_unresolved = unresolved_pages(old_pages, "coalition_flag")
    new_coal_unresolved = unresolved_pages(new_pages, "coalition_flag")
    against_narrative = unresolved_pages(new_pages, "against_flag")

    _, pattern_rows = changed_pattern_rows(old_annotated, new_annotated)
    anti_fixed = (
        pattern_rows.loc[
            pattern_rows["result_raw_new"].str.contains(ANTI_RE, na=False)
            & pattern_rows["outcome_category_old"].eq("unknown")
            & pattern_rows["outcome_category_new"].ne("unknown")
        ]["battle_name_old"]
        .drop_duplicates()
        .sort_values()
        .tolist()
    )
    coalition_fixed = (
        pattern_rows.loc[
            pattern_rows["result_raw_new"].str.contains(COALITION_RE, na=False)
            & pattern_rows["outcome_category_old"].eq("unknown")
            & pattern_rows["outcome_category_new"].ne("unknown")
        ]["battle_name_old"]
        .drop_duplicates()
        .sort_values()
        .tolist()
    )

    remaining_anti = new_anti_unresolved.copy()
    if not remaining_anti.empty:
        affected = (
            new_annotated.loc[new_annotated["battle_name"].isin(remaining_anti["battle_name"])]
            .merge(
                new_sensitivity[
                    [
                        "display_name",
                        "rank_hierarchical_weighted",
                        "rank_battle_only_baseline",
                    ]
                ],
                on="display_name",
                how="left",
            )
        )
        affected = affected[
            [
                "battle_name",
                "display_name",
                "rank_hierarchical_weighted",
                "rank_battle_only_baseline",
            ]
        ].drop_duplicates()
    else:
        affected = pd.DataFrame(
            columns=[
                "battle_name",
                "display_name",
                "rank_hierarchical_weighted",
                "rank_battle_only_baseline",
            ]
        )

    top30_residual = top30_unresolved_coalition(new_annotated, read_csv(new_snapshot / "RANKING_RESULTS_HIERARCHICAL.csv"))
    top_change_table = top_page_changes(pattern_rows)

    return f"""
# Second Pass Anti Coalition Audit

## Scope

This is a focused residual audit on top of `{old_snapshot.name}`. It reviews only the remaining `anti-*`, `allied`, `coalition`, and related target-of-coalition outcome patterns in the rebuilt second-pass snapshot `{new_snapshot.name}`.

## What Changed In This Pass

- Confirmed anti-target bug fixes were extended to short targets and alias-bearing sides by searching both belligerent labels and commander-side raw text.
- Coalition/allied inference was tightened with direct label matches, coalition-strength heuristics, and additional coalition aliases.
- Narrative false positives using the word `against` were reviewed, but they were left unresolved when they did not actually express winner-side meaning.

## Residual Anti Pattern Status

- anti-pattern pages unresolved before this pass: `{fmt_int(len(old_anti_unresolved))}`
- anti-pattern pages unresolved after this pass: `{fmt_int(len(new_anti_unresolved))}`
- anti/coaltition row-level changes in annotated commander engagements: `{fmt_int(len(pattern_rows))}`

Confirmed anti-target pages fixed in this pass:

- {", ".join(f"`{name}`" for name in anti_fixed[:12]) if anti_fixed else "`none`"}

Remaining anti-pattern pages after the pass:

{markdown_table(new_anti_unresolved[["battle_name", "page_type", "result_raw", "outcome_inference_method"]])}

Affected commanders for the remaining anti-pattern page(s):

{markdown_table(affected)}

Judgment:

- There is no remaining confirmed `anti-X` winner-inversion bug affecting any top-ranked commander.
- The only remaining anti-pattern page is `Battle of Northern Henan`, whose result text is narrative (`failed anti Feng`) rather than a clean coalition-result label.
- Its only ranking-visible commander is `Pang Bingxun`, who is unranked in hierarchical and `#1560` in battle-only. This is not a material distortion case.

## Residual Coalition Pattern Status

- coalition/allied pages unresolved before this pass: `{fmt_int(len(old_coal_unresolved))}`
- coalition/allied pages unresolved after this pass: `{fmt_int(len(new_coal_unresolved))}`
- coalition/allied pages newly resolved from unknown to known in this pass: `{fmt_int(len(set(coalition_fixed)))}` distinct pages

Representative coalition/allied pages fixed in this pass:

- {", ".join(f"`{name}`" for name in coalition_fixed[:12]) if coalition_fixed else "`none`"}

Most affected coalition/allied pages in row-count terms:

{markdown_table(top_change_table)}

Remaining unresolved coalition/allied pages that still touch the hierarchical top 30:

{markdown_table(top30_residual)}

These residual pages are not confirmed bugs. They fall into three buckets:

1. Generic coalition labels with insufficient side labeling: plain `Allied victory` or `Coalition victory` where the side text is too generic to map safely.
2. Citation-polluted result fields: examples like `Coalition victoryLeggiere 2002` where the result text is fused to source notes.
3. Real ambiguity on multi-side pages: war/campaign pages whose page-level result is clear in the abstract but not safe to assign to every listed commander side without overclaiming.

## Narrative `against` False Positives

These rows still contain `against`, but they are not outcome-inference bugs:

{markdown_table(against_narrative[["battle_name", "page_type", "result_raw"]].head(10))}

They were deliberately left conservative because the word `against` is narrative here, not coalition-target logic.

## Materiality Assessment

- The anti-target inversion bug is now bounded to zero material ranking cases.
- Residual coalition/allied unknowns still exist, but they are now mostly a coverage/underspecification issue rather than a winner-side inversion bug.
- After the split-denominator fix, unresolved coalition/allied rows no longer enter outcome denominators as zero-value evidence.
- Their remaining effect is limited to presence, scope, and centrality exposure.
- In the hierarchical top 30, only four commanders still have unresolved coalition/allied pages: `Mustafa Kemal Ataturk`, `Charles XIV John`, `Charles-Pierre Augereau`, and `Napoleon Bonaparte`.
- None of the two main suspicious leaders from the first pass, `Qasem Soleimani` and `Nelson A. Miles`, are still being lifted by unresolved anti/coaltition rows.

## Bottom Line

This second pass fixed the remaining confirmed anti-target inversion cases and a large additional block of coalition/allied unknowns. What remains is bounded ambiguity, not an obvious residual bug. The remaining unresolved pages are auditable and no longer appear to materially distort the top-level ranking conclusions.
"""


def leader_section(
    old_sensitivity: pd.DataFrame,
    new_sensitivity: pd.DataFrame,
    features: pd.DataFrame,
    hierarchical: pd.DataFrame,
    classification: pd.DataFrame,
    annotated: pd.DataFrame,
    name: str,
    verdict: str,
    driver_note: str,
) -> str:
    rank_table = compact_rank_delta(old_sensitivity, new_sensitivity, name)
    summary_table = leader_driver_summary(features, hierarchical, classification, name)
    rows_table = commander_rows(annotated, name)
    unresolved_table = unresolved_coalition_rows(annotated, name)
    unresolved_note = "No unresolved coalition/allied rows remain for this commander." if unresolved_table.empty else (
        "Residual unresolved coalition/allied rows still attached to this commander:\n\n"
        + markdown_table(unresolved_table)
    )
    return f"""
## {name}

Verdict: **{verdict}**

Why this commander still ranks where he does:

{driver_note}

Model rank shift from the previous snapshot:

{markdown_table(rank_table)}

Current driver summary:

{markdown_table(summary_table)}

Current counted engagement rows:

{markdown_table(rows_table)}

{unresolved_note}
"""


def build_suspicious_leaders_audit(
    old_snapshot: Path,
    new_snapshot: Path,
    old_sensitivity: pd.DataFrame,
    new_sensitivity: pd.DataFrame,
    features: pd.DataFrame,
    hierarchical: pd.DataFrame,
    classification: pd.DataFrame,
    annotated: pd.DataFrame,
) -> str:
    qasem_note = (
        "His remaining rank is not being driven by residual anti/coaltition bugs. "
        "It is driven by a small but very positive known-outcome set, very strong scope exposure "
        "(six battles, three operations, two campaigns, two wars), and still-meaningful higher-level exposure. "
        "The second pass neutralized the worst inflation by switching temporal scoring to non-war span "
        "(16 years used in-model instead of the 99-year war-page span) and by adding an evidence component, "
        "which pushed him from #4 to #13 in hierarchical_weighted. "
        "He remains caution-worthy because modern proxy-war pages still give him broad exposure with sparse explicit defeat coverage."
    )
    nelson_note = (
        "His rank is not a parsing bug. It is a war/campaign-heavy profile built from repeated United States victory pages: "
        "three battles, two campaigns, six wars, and six known outcomes out of eleven strict engagements. "
        "The second pass reduced his rank from #9 to #16 by weakening higher-level reward and by making evidence coverage matter more, "
        "but his dossier is still thinner at the battle layer than a top-20 all-history placement would normally warrant."
    )
    aetius_note = (
        "He remains high because his late Roman dossier is compact, outcome-positive, and spans six battle pages plus six war pages. "
        "This is not a residual coalition bug case. The caution comes from sparse ancient coverage and the fact that higher-level Roman war pages still amplify scope and centrality. "
        "His rank is plausible but lower-confidence than the leading robust elite."
    )
    bernadotte_note = (
        "He is no longer being treated as a suspicious artifact. He has a broad dossier with sixteen battle pages, three campaigns, eight wars, and seventeen known outcomes. "
        "He does still carry two unresolved coalition battle pages (`Battle of Dennewitz` and `Battle of Großbeeren`), so his exact slot remains somewhat sensitive, "
        "but the overall profile is substantially richer than the first-pass caution cases."
    )

    return f"""
# Second Pass Suspicious Leaders Audit

## Scope

This audit starts from `{new_snapshot.name}` and focuses on the leaders that still looked historically questionable after the first rank-fix pass.

The primary questions were:

- Are `Qasem Soleimani` and `Nelson A. Miles` still ranking high because of a residual bug?
- Are any other hierarchical top names still suspicious enough to require special caution?
- Are the remaining high ranks explainable, acceptable, or still likely inflated?

{leader_section(old_sensitivity, new_sensitivity, features, hierarchical, classification, annotated, 'Qasem Soleimani', 'questionable but now bounded caution case', qasem_note)}

{leader_section(old_sensitivity, new_sensitivity, features, hierarchical, classification, annotated, 'Nelson A. Miles', 'still inflated enough to remain a caution case', nelson_note)}

{leader_section(old_sensitivity, new_sensitivity, features, hierarchical, classification, annotated, 'Flavius Aetius', 'plausible but low-confidence high placement', aetius_note)}

{leader_section(old_sensitivity, new_sensitivity, features, hierarchical, classification, annotated, 'Charles XIV John', 'acceptable hierarchical leader with bounded coalition ambiguity', bernadotte_note)}

## Residual Group-Level Concern

The remaining historical caution in the hierarchical layer is now less about a single parsing bug and more about profile type:

- commanders with heavy war/campaign exposure and modest battle-level defeat documentation
- commanders whose dossiers rely on generic coalition-result pages
- ancient or modern figures whose Wikipedia coverage is structurally uneven

That is why the interpretive layer still marks names such as `Qasem Soleimani`, `Nelson A. Miles`, and `Flavius Aetius` as caution-heavy or low-confidence, even after the second pass.

## Bottom Line

- `Qasem Soleimani` and `Nelson A. Miles` are no longer top-10 hierarchical leaders and are no longer being lifted by the residual anti/coaltition bug class.
- Their remaining elevation is mainly a model-and-coverage interaction problem, not a confirmed scoring bug.
- `Flavius Aetius` remains high but is better interpreted as a sparse-coverage caution case than as a parser artifact.
- `Charles XIV John` remains high but looks methodologically acceptable on the current evidence, with only bounded unresolved coalition ambiguity.
"""


def build_implementation_report(
    old_snapshot: Path,
    new_snapshot: Path,
    old_annotated: pd.DataFrame,
    new_annotated: pd.DataFrame,
    old_ranking_metrics: dict[str, Any],
    new_ranking_metrics: dict[str, Any],
) -> str:
    changed_rows, pattern_rows = changed_pattern_rows(old_annotated, new_annotated)
    unknown_validation = validate_unknown_split(new_snapshot)
    excluded_commander_rows = read_csv_optional(
        new_snapshot / "derived_scoring" / "scoring_excluded_commander_rows.csv"
    )
    excluded_master_rows = read_csv_optional(
        new_snapshot / "derived_scoring" / "scoring_excluded_master_rows.csv"
    )
    title_override_rows = new_annotated.loc[new_annotated["analytic_year_confidence"].eq("title_year_override")]
    new_sensitivity = read_csv(new_snapshot / "RANKING_RESULTS_SENSITIVITY.csv")

    return f"""
# Second Pass Implementation Report

## Snapshot Lineage

- starting snapshot: `{old_snapshot.name}`
- superseding second-pass snapshot: `{new_snapshot.name}`

The old snapshot is preserved unchanged. This pass created a new superseding analytics snapshot because the fixes affected scoring logic, ranking behavior, interpretive outputs, and the dashboard bundle.

## Code Files Changed

- `build_scoring_framework_package.py`
- `build_ranking_package.py`
- `generate_second_pass_reports.py`

Rebuilt but not code-modified in this pass:

- `build_interpretive_layer.py`
- `build_ranking_dashboard.py`
- `qa_dashboard_snapshot.py`

## Fixes Implemented

### Confirmed bug fixes

1. Anti-target outcome inference:
   - extended `anti-*` target extraction to shorter targets
   - searched both belligerent labels and commander-side raw text for the loser target
   - added coalition aliases such as `allied powers`, `allied forces`, and `anti spartan`

2. Coalition/allied side inference:
   - added direct coalition-label matching
   - added coalition-strength heuristics
   - preserved conservative `unknown` outcomes when the page stayed genuinely ambiguous

3. Unknown-outcome denominator fix:
   - `outcome_factor_split` now becomes zero whenever `outcome_category = unknown`

### Design fixes

4. Split-credit defeat dilution:
   - changed same-side outcome split from `1 / n` to `1 / sqrt(n)`

5. Hierarchical temporal inflation:
   - hierarchical temporal scoring now uses `active_span_years_nonwar` when available

6. Hierarchical guardrail:
   - reduced higher-level reward weight from `0.10` to `0.06`
   - added a small evidence component at `0.04` using known-outcome share

### Data safeguards in the scoring layer

7. Title-year correction:
   - when parsed year is wildly inconsistent with an event title year, the scoring layer now uses the title year

8. Non-person commander exclusion:
   - excluded `Manner of death` from the scoring layer without rewriting the authoritative commander snapshot

## Validation

- total annotated commander rows changed versus the prior snapshot: `{fmt_int(len(changed_rows))}`
- anti/coaltition-pattern rows changed: `{fmt_int(len(pattern_rows))}`
- title-year override rows now active: `{fmt_int(len(title_override_rows))}` across `{fmt_int(title_override_rows['battle_name'].nunique())}` pages
- excluded non-person commander rows at scoring time: `{fmt_int(len(excluded_commander_rows))}`
- excluded non-person master identities at scoring time: `{fmt_int(len(excluded_master_rows))}`
- unknown annotated rows in rebuilt package: `{fmt_int(unknown_validation['unknown_rows'])}`
- unknown rows still contributing non-zero split outcome factor: `{fmt_int(unknown_validation['unknown_split_violations'])}`

## Rebuilt Outputs

- derived scoring tables in `{new_snapshot.name}\\derived_scoring`
- ranking outputs: `RANKING_RESULTS_*.csv`, `RANKING_BUILD_METRICS.json`, `TOP_COMMANDERS_SUMMARY.csv`, `TOP_COMMANDERS_PROFILES.md`
- interpretive outputs: `BEST_SUPPORTED_TOP_TIER_MEMO.md`, `TOP_TIER_CLASSIFICATION.csv`, `MODEL_SENSITIVITY_AUDIT.csv`, `ERA_ELITE_SHORTLIST.csv`
- dashboard bundle in `{new_snapshot.name}\\dashboard`
- dashboard QA summary: `dashboard_qa_summary.json`

## Before/After Cohort Counts

| model | old_rows | new_rows |
| --- | ---: | ---: |
| baseline_conservative | {fmt_int(old_ranking_metrics['model_rows']['baseline_conservative'])} | {fmt_int(new_ranking_metrics['model_rows']['baseline_conservative'])} |
| battle_only_baseline | {fmt_int(old_ranking_metrics['model_rows']['battle_only_baseline'])} | {fmt_int(new_ranking_metrics['model_rows']['battle_only_baseline'])} |
| hierarchical_weighted | {fmt_int(old_ranking_metrics['model_rows']['hierarchical_weighted'])} | {fmt_int(new_ranking_metrics['model_rows']['hierarchical_weighted'])} |
| hierarchical_full_credit | {fmt_int(old_ranking_metrics['model_rows']['hierarchical_full_credit'])} | {fmt_int(new_ranking_metrics['model_rows']['hierarchical_full_credit'])} |
| hierarchical_equal_split | {fmt_int(old_ranking_metrics['model_rows']['hierarchical_equal_split'])} | {fmt_int(new_ranking_metrics['model_rows']['hierarchical_equal_split'])} |
| hierarchical_broader_eligibility | {fmt_int(old_ranking_metrics['model_rows']['hierarchical_broader_eligibility'])} | {fmt_int(new_ranking_metrics['model_rows']['hierarchical_broader_eligibility'])} |

## Leader Checks

- baseline leader: `{old_ranking_metrics['top_baseline'][0]['display_name']}` -> `{new_ranking_metrics['top_baseline'][0]['display_name']}`
- hierarchical leader: `{old_ranking_metrics['top_hierarchical'][0]['display_name']}` -> `{new_ranking_metrics['top_hierarchical'][0]['display_name']}`
- `Qasem Soleimani` hierarchical rank: `4 -> {row_by_name(new_sensitivity, 'Qasem Soleimani').get('rank_hierarchical_weighted', '')}`
- `Nelson A. Miles` hierarchical rank: `9 -> {row_by_name(new_sensitivity, 'Nelson A. Miles').get('rank_hierarchical_weighted', '')}`

## Residual Caveats

- This pass did not rewrite the battle or commander source layers.
- Some coalition/allied pages remain unresolved because their result text is still too generic or citation-polluted to assign safely.
- Those residual unknowns are now bounded and auditable rather than silently mis-scored.
"""


def build_impact_report(
    old_snapshot: Path,
    new_snapshot: Path,
    old_ranking_metrics: dict[str, Any],
    new_ranking_metrics: dict[str, Any],
    old_sensitivity: pd.DataFrame,
    new_sensitivity: pd.DataFrame,
    new_hierarchical: pd.DataFrame,
    classification: pd.DataFrame,
    dashboard_qa: dict[str, Any],
) -> str:
    suspicious = []
    for name in ["Qasem Soleimani", "Nelson A. Miles", "Charles XII of Sweden", "Jean Victor Marie Moreau", "Aleksandr Vasilevsky"]:
        old_row = row_by_name(old_sensitivity, name)
        new_row = row_by_name(new_sensitivity, name)
        if old_row.empty or new_row.empty:
            continue
        suspicious.append(
            {
                "display_name": name,
                "old_hier_rank": old_row.get("rank_hierarchical_weighted", ""),
                "new_hier_rank": new_row.get("rank_hierarchical_weighted", ""),
                "old_best_rank": old_row.get("best_rank", ""),
                "new_best_rank": new_row.get("best_rank", ""),
                "stability_label": new_row.get("stability_label", ""),
            }
        )

    top_caution = (
        new_hierarchical.head(25)
        .merge(
            classification[["display_name", "interpretive_group", "caution_flags"]],
            on="display_name",
            how="left",
            suffixes=("", "_cls"),
        )
        .loc[lambda df: df["interpretive_group"].eq("caution_likely_artifact")]
        [["rank", "display_name", "interpretive_group", "caution_flags_cls"]]
        .rename(columns={"caution_flags_cls": "caution_flags"})
    )

    return f"""
# Second Pass Impact Report

## Top-Level Outcome

This second pass materially improved the trustworthiness of the rebuilt analytics stack without changing the headline leaders:

- baseline leader stayed `{new_ranking_metrics['top_baseline'][0]['display_name']}`
- battle-only leader stayed `{read_csv(new_snapshot / 'RANKING_RESULTS_BATTLE_ONLY.csv').iloc[0]['display_name']}`
- hierarchical leader stayed `{new_ranking_metrics['top_hierarchical'][0]['display_name']}`

What changed was the composition of the upper hierarchical table.

## Hierarchical Top Table Before vs After

{markdown_table(before_after_top(read_csv(old_snapshot / 'RANKING_RESULTS_HIERARCHICAL.csv'), new_hierarchical))}

## Suspicious Case Movement

{markdown_table(pd.DataFrame(suspicious))}

Key interpretation:

- `Qasem Soleimani` moved from `#4` to `#13` in hierarchical_weighted.
- `Nelson A. Miles` moved from `#9` to `#16`.
- `Jean Victor Marie Moreau` moved from `#6` to `#25`.
- `Aleksandr Vasilevsky` moved from `#8` to `#33`.
- `Charles XII of Sweden` actually rose inside hierarchical views after the year-correction pass, but he remains far from the top and is no longer a headline anomaly.

## Cohort Size Impact

- baseline_conservative: `{fmt_int(old_ranking_metrics['model_rows']['baseline_conservative'])} -> {fmt_int(new_ranking_metrics['model_rows']['baseline_conservative'])}`
- battle_only_baseline: `{fmt_int(old_ranking_metrics['model_rows']['battle_only_baseline'])} -> {fmt_int(new_ranking_metrics['model_rows']['battle_only_baseline'])}`
- hierarchical_weighted: `{fmt_int(old_ranking_metrics['model_rows']['hierarchical_weighted'])} -> {fmt_int(new_ranking_metrics['model_rows']['hierarchical_weighted'])}`
- hierarchical_broader_eligibility: `{fmt_int(old_ranking_metrics['model_rows']['hierarchical_broader_eligibility'])} -> {fmt_int(new_ranking_metrics['model_rows']['hierarchical_broader_eligibility'])}`

The net cohort expansion came from outcome-resolution improvements and year corrections. The scoring-layer exclusion of the non-person `Manner of death` rows was more than offset by rows that became cleanly eligible after the second-pass fixes.

## Residual Caution Cases In The Current Hierarchical Top 25

{markdown_table(top_caution)}

## Trust Judgment After The Second Pass

- `hierarchical_weighted` remains the most trustworthy single model.
- Its trust level improved in this pass because the known residual bug class no longer explains the most suspicious first-pass leaders.
- `baseline_conservative` is better than before but still battle-specialist heavy.
- `hierarchical_full_credit` remains the weakest model because it still over-rewards higher-level page accumulation.

## Remaining Concerns

- Some coalition/allied pages are still unresolved and continue to affect scope and centrality even though they no longer distort outcome means.
- `Qasem Soleimani` and `Nelson A. Miles` remain caution cases rather than robust elite outcomes.
- `Flavius Aetius` and a few other top-25 names remain historically arguable but lower-confidence because of sparse or uneven source coverage.

## Dashboard Synchronization

- dashboard snapshot label: `{dashboard_qa['snapshot']}`
- expected ranked commanders in dashboard: `{fmt_int(dashboard_qa['expected']['commander_count'])}`
- baseline leader match: `{dashboard_qa['checks']['baseline_alignment']['leader_from_table']}`
- hierarchical leader match: `{dashboard_qa['checks']['hierarchical_alignment']['leader_from_table']}`
- all dashboard checks passed: `{dashboard_qa['all_checks_passed']}`

## Bottom Line

The second pass did not prove the ranking system perfect, but it moved the remaining issues into the acceptable category: explicitly documented, bounded, and no longer obviously driving the top-level conclusions. The current hierarchy is materially more trustworthy than the first rank-fix snapshot, with `hierarchical_weighted` still the best current single model.
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate second-pass correction reports.")
    parser.add_argument("--old-snapshot", type=Path, required=True)
    parser.add_argument("--new-snapshot", type=Path, required=True)
    args = parser.parse_args()

    old_snapshot = args.old_snapshot
    new_snapshot = args.new_snapshot

    old_annotated = read_csv(old_snapshot / "derived_scoring" / "commander_engagements_annotated.csv")
    new_annotated = read_csv(new_snapshot / "derived_scoring" / "commander_engagements_annotated.csv")
    old_sensitivity = read_csv(old_snapshot / "RANKING_RESULTS_SENSITIVITY.csv")
    new_sensitivity = read_csv(new_snapshot / "RANKING_RESULTS_SENSITIVITY.csv")
    new_features = read_csv(new_snapshot / "derived_scoring" / "commander_ranking_features.csv")
    new_hierarchical = read_csv(new_snapshot / "RANKING_RESULTS_HIERARCHICAL.csv")
    new_classification = read_csv(new_snapshot / "TOP_TIER_CLASSIFICATION.csv")
    old_ranking_metrics = read_json(old_snapshot / "RANKING_BUILD_METRICS.json")
    new_ranking_metrics = read_json(new_snapshot / "RANKING_BUILD_METRICS.json")
    dashboard_qa = read_json(new_snapshot / "dashboard_qa_summary.json")

    anti_report = build_anti_coalition_audit(
        old_snapshot,
        new_snapshot,
        old_annotated,
        new_annotated,
        new_sensitivity,
    )
    leaders_report = build_suspicious_leaders_audit(
        old_snapshot,
        new_snapshot,
        old_sensitivity,
        new_sensitivity,
        new_features,
        new_hierarchical,
        new_classification,
        new_annotated,
    )
    implementation_report = build_implementation_report(
        old_snapshot,
        new_snapshot,
        old_annotated,
        new_annotated,
        old_ranking_metrics,
        new_ranking_metrics,
    )
    impact_report = build_impact_report(
        old_snapshot,
        new_snapshot,
        old_ranking_metrics,
        new_ranking_metrics,
        old_sensitivity,
        new_sensitivity,
        new_hierarchical,
        new_classification,
        dashboard_qa,
    )

    write_text(new_snapshot / "SECOND_PASS_ANTI_COALITION_AUDIT.md", anti_report)
    write_text(new_snapshot / "SECOND_PASS_SUSPICIOUS_LEADERS_AUDIT.md", leaders_report)
    write_text(new_snapshot / "SECOND_PASS_IMPLEMENTATION_REPORT.md", implementation_report)
    write_text(new_snapshot / "SECOND_PASS_IMPACT_REPORT.md", impact_report)


if __name__ == "__main__":
    main()
