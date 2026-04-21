from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


ROOT = Path(r"C:\Users\gameo\OneDrive\Desktop\test")


MODEL_RANK_COLUMNS = [
    "rank_baseline_conservative",
    "rank_battle_only_baseline",
    "rank_hierarchical_trust_v2",
    "rank_hierarchical_weighted",
    "rank_hierarchical_full_credit",
    "rank_hierarchical_equal_split",
    "rank_hierarchical_broader_eligibility",
]
TRUSTED_MODEL_RANK_COLUMNS = [
    "rank_baseline_conservative",
    "rank_battle_only_baseline",
    "rank_hierarchical_trust_v2",
    "rank_hierarchical_weighted",
    "rank_hierarchical_equal_split",
    "rank_hierarchical_broader_eligibility",
]


def load_csv(snapshot_dir: Path, name: str) -> pd.DataFrame:
    return pd.read_csv(snapshot_dir / name)


def to_numeric(df: pd.DataFrame, columns: Iterable[str]) -> None:
    for column in columns:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")


def fmt_rank(value: float | int | None) -> str:
    if pd.isna(value):
        return "NA"
    return str(int(round(float(value))))


def fmt_float(value: float | int | None, digits: int = 1) -> str:
    if pd.isna(value):
        return "NA"
    return f"{float(value):.{digits}f}"


def safe_text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and np.isnan(value):
        return ""
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def trusted_rank_metrics(frame: pd.DataFrame) -> pd.DataFrame:
    ranks = frame[TRUSTED_MODEL_RANK_COLUMNS].apply(pd.to_numeric, errors="coerce")
    return pd.DataFrame(
        {
            "best_rank": ranks.min(axis=1),
            "worst_rank": ranks.max(axis=1),
            "rank_range": ranks.max(axis=1) - ranks.min(axis=1),
            "mean_rank": ranks.mean(axis=1),
            "top10_appearances": (ranks <= 10).sum(axis=1),
            "top25_appearances": (ranks <= 25).sum(axis=1),
            "trusted_models_eligible_count": ranks.notna().sum(axis=1),
        }
    )


def rank_signature(row: pd.Series) -> str:
    labels = [
        ("B0", row["rank_baseline_conservative"]),
        ("B1", row["rank_battle_only_baseline"]),
        ("HT", row["rank_hierarchical_trust_v2"]),
        ("H", row["rank_hierarchical_weighted"]),
        ("HF", row["rank_hierarchical_full_credit"]),
        ("HE", row["rank_hierarchical_equal_split"]),
        ("HB", row["rank_hierarchical_broader_eligibility"]),
    ]
    return ", ".join(f"{label}={fmt_rank(value)}" for label, value in labels)


def interpretive_era(bucket: str) -> str:
    mapping = {
        "ancient": "ancient",
        "medieval": "medieval",
        "early_modern": "early_modern",
        "revolutionary_napoleonic": "modern",
        "long_nineteenth_century": "modern",
        "world_wars": "modern",
        "cold_war": "modern",
        "contemporary": "contemporary",
    }
    return mapping.get(bucket, "modern")


def contains_flag(flags: str, token: str) -> bool:
    return token in safe_text(flags).split(";")


def sensitivity_driver(row: pd.Series) -> str:
    drivers: list[str] = []

    if contains_flag(row["caution_flags"], "higher_level_dependent"):
        drivers.append("higher_level_page_dependency")

    if pd.notna(row["battle_vs_hier_gap"]) and row["battle_vs_hier_gap"] >= 100:
        drivers.append("higher_level_page_dependency")

    if pd.notna(row["baseline_vs_hier_gap"]) and row["baseline_vs_hier_gap"] >= 75:
        drivers.append("higher_level_page_dependency")

    if pd.notna(row["battle_vs_hier_gap"]) and row["battle_vs_hier_gap"] <= -50:
        drivers.append("battle_specialist_profile")

    if pd.notna(row["baseline_vs_hier_gap"]) and row["baseline_vs_hier_gap"] <= -50:
        drivers.append("battle_specialist_profile")

    if pd.notna(row["full_credit_gain"]) and abs(row["full_credit_gain"]) >= 50:
        drivers.append("credit_rule_dependency")

    if not drivers:
        return "mixed_model_sensitivity"

    unique_drivers = list(dict.fromkeys(drivers))
    return unique_drivers[0] if len(unique_drivers) == 1 else "mixed_model_sensitivity"


def interpretive_reason(row: pd.Series, category: str) -> str:
    if category == "robust_elite_core":
        return (
            f"Anchors the headline trust tier with broad cross-model support; rank range "
            f"{fmt_rank(row['rank_range'])} and repeated top-tier placement across trusted models."
        )

    driver = row["dominant_sensitivity_driver"]
    if category == "strong_upper_tier":
        if driver == "battle_specialist_profile":
            return (
                "Belongs near the top, but battle-dominant models are more favorable than broader hierarchical views."
            )
        if driver == "higher_level_page_dependency":
            return (
                "Belongs in the upper tier, but higher-level war/campaign pages still provide a meaningful share of the support."
            )
        if driver == "credit_rule_dependency":
            return (
                "Upper-tier signal is strong, but attribution rules still move the placement materially."
            )
        return "Upper-tier signal is strong, but the exact placement still depends on model structure."

    if category == "high_confidence_upper_band":
        if driver == "battle_specialist_profile":
            return (
                "Strong case with real support, but battle-dominant models remain noticeably more favorable than broader views."
            )
        if driver == "higher_level_page_dependency":
            return (
                "Strong case with meaningful support, but operations, campaigns, or war-level pages still boost the result materially."
            )
        if driver == "credit_rule_dependency":
            return (
                "Support is real, but attribution rules still change the final placement enough to keep this outside the headline core."
            )
        return "Support is meaningful, but the exact placement still depends on model structure."

    parts: list[str] = []
    if driver == "higher_level_page_dependency" or contains_flag(row["caution_flags"], "higher_level_dependent"):
        parts.append("Higher-level war/campaign/operation pages are doing substantial work.")
    if pd.notna(row["full_credit_gain"]) and row["full_credit_gain"] >= 50:
        parts.append("Full-presence credit sharply boosts the rank.")
    if pd.notna(row["battle_vs_hier_gap"]) and row["battle_vs_hier_gap"] >= 200:
        parts.append("Battle-only restrictions cause a severe collapse.")
    if pd.notna(row["baseline_vs_hier_gap"]) and row["baseline_vs_hier_gap"] >= 150:
        parts.append("The commander is not competitive in the strict baseline cohort.")
    if pd.notna(row["full_credit_gain"]) and row["full_credit_gain"] <= -100:
        parts.append("The full-credit variant produces an unusually large negative shock.")
    if not parts:
        parts.append("The placement is too model-dependent to treat as a strong all-model conclusion.")
    return " ".join(parts)


def era_recommendation_note(row: pd.Series, band: str) -> str:
    era_name = row["requested_era"].replace("_", " ")
    if band == "robust_elite_core":
        return (
            f"Best-supported {era_name} candidate; rank signature {row['rank_signature']}."
        )
    if band == "strong_upper_tier":
        return (
            f"Belongs in the era shortlist, but the case depends on model choice; rank signature {row['rank_signature']}."
        )
    if band == "high_confidence_upper_band":
        return (
            f"Strong {era_name} signal with meaningful support, but not yet part of the headline core; rank signature {row['rank_signature']}."
        )
    return (
        f"Useful as an audit case for the era, not as a secure top-tier conclusion; rank signature {row['rank_signature']}."
    )


def build_frames(snapshot_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    sensitivity = load_csv(snapshot_dir, "RANKING_RESULTS_SENSITIVITY.csv")
    summary = load_csv(snapshot_dir, "TOP_COMMANDERS_SUMMARY.csv")

    to_numeric(
        sensitivity,
        MODEL_RANK_COLUMNS
        + [
            "best_rank",
            "worst_rank",
            "rank_range",
            "mean_rank",
            "top10_appearances",
            "top25_appearances",
        ],
    )
    to_numeric(
        summary,
        [
            "rank_baseline_conservative",
            "rank_battle_only_baseline",
            "rank_hierarchical_trust_v2",
            "rank_hierarchical_weighted",
            "rank_hierarchical_full_credit",
            "rank_hierarchical_equal_split",
            "rank_hierarchical_broader_eligibility",
            "total_engagements_strict",
            "total_battle_pages_strict",
            "distinct_conflicts_strict",
            "distinct_opponents_strict",
            "known_outcome_count",
            "score_baseline_conservative",
            "score_hierarchical_trust_v2",
            "score_hierarchical_weighted",
        ],
    )

    sensitivity["caution_flags"] = sensitivity["caution_flags"].fillna("")
    summary["caution_flags"] = summary["caution_flags"].fillna("")
    trusted_metrics = trusted_rank_metrics(sensitivity)
    for column in trusted_metrics.columns:
        sensitivity[column] = trusted_metrics[column]

    merged = sensitivity.merge(
        summary[
            [
                "display_name",
                "canonical_wikipedia_url",
                "primary_era_bucket",
                "total_engagements_strict",
                "total_battle_pages_strict",
                "distinct_conflicts_strict",
                "distinct_opponents_strict",
                "known_outcome_count",
                "rank_hierarchical_trust_v2",
                "score_hierarchical_trust_v2",
                "trust_tier_v2",
                "trust_confidence_v2",
                "trust_headline_reason_v2",
                "outcome_profile_summary",
                "page_type_exposure_summary",
                "stability_label",
                "caution_flags",
            ]
        ],
        on=["display_name", "canonical_wikipedia_url", "primary_era_bucket"],
        how="left",
        suffixes=("", "_summary"),
    )

    merged["caution_flags"] = merged["caution_flags"].fillna(merged["caution_flags_summary"]).fillna("")
    merged["battle_vs_hier_gap"] = (
        merged["rank_battle_only_baseline"] - merged["rank_hierarchical_weighted"]
    )
    merged["baseline_vs_hier_gap"] = (
        merged["rank_baseline_conservative"] - merged["rank_hierarchical_weighted"]
    )
    merged["full_credit_gain"] = (
        merged["rank_hierarchical_weighted"] - merged["rank_hierarchical_full_credit"]
    )
    merged["equal_split_gain"] = (
        merged["rank_hierarchical_weighted"] - merged["rank_hierarchical_equal_split"]
    )
    merged["dominant_sensitivity_driver"] = merged.apply(sensitivity_driver, axis=1)
    merged["interpretive_era"] = merged["primary_era_bucket"].map(interpretive_era)
    merged["rank_signature"] = merged.apply(rank_signature, axis=1)

    merged["interpretive_group"] = merged["trust_tier_v2"].fillna("outside_trust_headline")
    merged["interpretive_reason"] = merged["trust_headline_reason_v2"].fillna("")
    missing_reason_mask = merged["interpretive_reason"].eq("")
    merged.loc[missing_reason_mask, "interpretive_reason"] = merged.loc[missing_reason_mask].apply(
        lambda row: interpretive_reason(row, row["interpretive_group"])
        if row["interpretive_group"] != "outside_trust_headline"
        else interpretive_reason(row, "model_sensitive_band"),
        axis=1,
    )

    classification = merged[
        merged["interpretive_group"] != "outside_trust_headline"
    ].copy()
    classification["interpretive_group"] = pd.Categorical(
        classification["interpretive_group"],
        categories=[
            "robust_elite_core",
            "strong_upper_tier",
            "high_confidence_upper_band",
            "model_sensitive_band",
        ],
        ordered=True,
    )
    classification = classification.sort_values(
        by=["interpretive_group", "mean_rank", "best_rank", "display_name"]
    )

    audit_mask = (
        (merged["best_rank"] <= 100)
        & (
            (merged["rank_range"] >= 50)
            | (merged["full_credit_gain"].abs() >= 50)
            | (merged["battle_vs_hier_gap"].abs() >= 80)
            | (merged["baseline_vs_hier_gap"].abs() >= 80)
            | merged["caution_flags"].str.contains("higher_level_dependent", na=False)
            | ((merged["best_rank"] <= 5) & (merged["rank_range"] >= 30))
            | merged["interpretive_group"].eq("model_sensitive_band")
        )
    )

    audit = merged[audit_mask].copy()
    audit["audit_note"] = audit["interpretive_reason"]
    audit = audit.sort_values(by=["best_rank", "mean_rank", "display_name"]).head(20)

    era_rows: list[pd.Series] = []
    era_order = ["ancient", "medieval", "early_modern", "modern", "contemporary"]
    target_limits = {
        "ancient": 4,
        "medieval": 5,
        "early_modern": 6,
        "modern": 8,
        "contemporary": 4,
    }

    for era in era_order:
        candidates = merged[merged["interpretive_era"] == era].copy()
        robust = candidates[candidates["interpretive_group"] == "robust_elite_core"].sort_values(
            by=["mean_rank", "best_rank"]
        )
        strong = candidates[
            candidates["interpretive_group"] == "strong_upper_tier"
        ].sort_values(by=["best_rank", "top25_appearances", "mean_rank"], ascending=[True, False, True])
        high_confidence = candidates[
            candidates["interpretive_group"] == "high_confidence_upper_band"
        ].sort_values(by=["best_rank", "mean_rank"])
        tentative = candidates[
            (candidates["interpretive_group"] == "model_sensitive_band")
            & (candidates["best_rank"] <= 100)
        ].sort_values(by=["best_rank", "mean_rank"])

        chosen = pd.concat(
            [
                robust.head(target_limits[era]),
                strong.head(max(target_limits[era] - len(robust), 0)),
            ]
        )
        chosen = chosen.drop_duplicates(subset=["display_name", "canonical_wikipedia_url"])

        if len(chosen) < target_limits[era]:
            remaining_slots = target_limits[era] - len(chosen)
            fallback = pd.concat([tentative, high_confidence]).drop_duplicates(
                subset=["display_name", "canonical_wikipedia_url"]
            )
            fallback = fallback[
                ~fallback["display_name"].isin(chosen["display_name"])
            ].head(remaining_slots)
            chosen = pd.concat([chosen, fallback], ignore_index=True)

        chosen = chosen.copy()
        chosen["requested_era"] = era
        chosen["support_band"] = chosen["interpretive_group"]
        chosen["recommendation_note"] = chosen.apply(
            lambda row: era_recommendation_note(row, row["support_band"]), axis=1
        )
        chosen["caveat_note"] = chosen.apply(
            lambda row: row["interpretive_reason"]
            if row["interpretive_group"] != "model_sensitive_band"
            else "The era signal is still model-sensitive; treat this as a provisional inclusion rather than a headline conclusion.",
            axis=1,
        )
        era_rows.extend(chosen.to_dict(orient="records"))

    era_shortlist = pd.DataFrame(era_rows)
    era_shortlist = era_shortlist.sort_values(
        by=["requested_era", "support_band", "mean_rank", "best_rank", "display_name"]
    )

    return classification, audit, era_shortlist


def write_csvs(
    snapshot_dir: Path,
    classification: pd.DataFrame,
    audit: pd.DataFrame,
    era_shortlist: pd.DataFrame,
) -> None:
    classification_columns = [
        "display_name",
        "canonical_wikipedia_url",
        "primary_era_bucket",
        "interpretive_era",
        "interpretive_group",
        "trust_confidence_v2",
        "best_rank",
        "worst_rank",
        "rank_range",
        "mean_rank",
        "top10_appearances",
        "top25_appearances",
        *MODEL_RANK_COLUMNS,
        "known_outcome_count",
        "total_engagements_strict",
        "total_battle_pages_strict",
        "distinct_conflicts_strict",
        "page_type_exposure_summary",
        "stability_label",
        "caution_flags",
        "dominant_sensitivity_driver",
        "interpretive_reason",
    ]
    classification[classification_columns].to_csv(
        snapshot_dir / "TOP_TIER_CLASSIFICATION.csv", index=False
    )

    audit_columns = [
        "display_name",
        "canonical_wikipedia_url",
        "primary_era_bucket",
        "best_rank",
        "worst_rank",
        "rank_range",
        "trust_confidence_v2",
        *MODEL_RANK_COLUMNS,
        "known_outcome_count",
        "total_engagements_strict",
        "total_battle_pages_strict",
        "page_type_exposure_summary",
        "stability_label",
        "caution_flags",
        "dominant_sensitivity_driver",
        "audit_note",
    ]
    audit[audit_columns].to_csv(snapshot_dir / "MODEL_SENSITIVITY_AUDIT.csv", index=False)

    era_columns = [
        "requested_era",
        "support_band",
        "display_name",
        "canonical_wikipedia_url",
        "primary_era_bucket",
        "best_rank",
        "mean_rank",
        "top25_appearances",
        "rank_baseline_conservative",
        "rank_hierarchical_trust_v2",
        "rank_hierarchical_weighted",
        "rank_signature",
        "trust_confidence_v2",
        "stability_label",
        "caution_flags",
        "recommendation_note",
        "caveat_note",
    ]
    era_shortlist[era_columns].to_csv(snapshot_dir / "ERA_ELITE_SHORTLIST.csv", index=False)


def bullet_line(row: pd.Series) -> str:
    return (
        f"- `{row['display_name']}`: {row['interpretive_reason']} "
        f"Rank signature `{row['rank_signature']}`."
    )


def audit_line(row: pd.Series) -> str:
    return (
        f"- `{row['display_name']}`: best `{fmt_rank(row['best_rank'])}`, worst `{fmt_rank(row['worst_rank'])}`, "
        f"range `{fmt_rank(row['rank_range'])}`. {row['audit_note']} Rank signature `{row['rank_signature']}`."
    )


def era_lines(era_shortlist: pd.DataFrame, era: str) -> list[str]:
    subset = era_shortlist[era_shortlist["requested_era"] == era].copy()
    lines: list[str] = []
    for _, row in subset.iterrows():
        lines.append(
            f"- `{row['display_name']}` ({row['support_band']}): {row['recommendation_note']} {row['caveat_note']}"
        )
    return lines


def inline_name_list(names: list[str], limit: int | None = None) -> str:
    if limit is not None:
        names = names[:limit]
    names = [name for name in names if safe_text(name)]
    if not names:
        return "`none`"
    wrapped = [f"`{name}`" for name in names]
    if len(wrapped) == 1:
        return wrapped[0]
    if len(wrapped) == 2:
        return f"{wrapped[0]} and {wrapped[1]}"
    return f"{', '.join(wrapped[:-1])}, and {wrapped[-1]}"


def write_memo(snapshot_dir: Path, classification: pd.DataFrame, audit: pd.DataFrame, era_shortlist: pd.DataFrame) -> None:
    robust = classification[
        classification["interpretive_group"] == "robust_elite_core"
    ].sort_values(by=["mean_rank", "best_rank"])

    strong = classification[
        classification["interpretive_group"] == "strong_upper_tier"
    ].sort_values(by=["mean_rank", "best_rank"])

    caution = classification[
        classification["interpretive_group"] == "model_sensitive_band"
    ].sort_values(by=["best_rank", "mean_rank"])

    battle_specialists = strong[
        strong["dominant_sensitivity_driver"] == "battle_specialist_profile"
    ].head(5)
    broad_sensitive = strong[
        strong["dominant_sensitivity_driver"] != "battle_specialist_profile"
    ].head(6)

    caution_focus = caution.head(8)
    audit_focus = audit.head(12)
    robust_names = robust["display_name"].tolist()
    battle_specialist_names = battle_specialists["display_name"].tolist()
    broad_sensitive_names = broad_sensitive["display_name"].tolist()
    caution_names = caution_focus["display_name"].tolist()
    ancient_names = era_shortlist.loc[era_shortlist["requested_era"] == "ancient", "display_name"].tolist()
    medieval_names = era_shortlist.loc[era_shortlist["requested_era"] == "medieval", "display_name"].tolist()
    early_modern_names = era_shortlist.loc[era_shortlist["requested_era"] == "early_modern", "display_name"].tolist()
    modern_names = era_shortlist.loc[era_shortlist["requested_era"] == "modern", "display_name"].tolist()
    contemporary_names = era_shortlist.loc[era_shortlist["requested_era"] == "contemporary", "display_name"].tolist()

    memo_lines: list[str] = [
        "# Best-Supported Top Tier Memo",
        "",
        "## Scope",
        "",
        "This memo adds an interpretive layer on top of the completed ranking package. "
        "It does not rerun crawling, extraction, or framework design. The purpose is to separate "
        "the strongest model-robust conclusions from the rankings that remain materially dependent "
        "on page-type weighting, commander-credit rules, or broader-eligibility choices.",
        "",
        "The memo uses the following outputs as its evidence base:",
        "",
        "- `RANKING_RESULTS_BASELINE.csv`",
        "- `RANKING_RESULTS_HIERARCHICAL.csv`",
        "- `RANKING_RESULTS_SENSITIVITY.csv`",
        "- `TOP_COMMANDERS_SUMMARY.csv`",
        "",
        "Interpretive heuristics used here:",
        "",
        "- `Robust elite core`: the strongest all-model cluster and the safest headline tier.",
        "- `Strong upper tier`: belongs in the serious top discussion, but exact order still depends on model structure.",
        "- `High-confidence upper band`: supported and important, but not strong enough to be merged into the headline core.",
        "- `Model-sensitive band`: worth auditing and discussing, but too structurally sensitive to treat as a secure headline conclusion.",
        "",
        "These are interpretive categories layered on top of the existing ranking framework. They are meant to support judgment, not replace the underlying score tables.",
        "",
            "## Robust Elite Core",
        "",
        "This is the strongest cross-model core in the current package. These commanders stay near the top even when the model changes meaningfully.",
        "",
    ]

    memo_lines.extend(bullet_line(row) for _, row in robust.iterrows())
    memo_lines.extend(
        [
            "",
            f"The clearest current cross-model core is {inline_name_list(robust_names, limit=7)}. "
            "These names remain near the top under meaningfully different ranking assumptions, so the exact internal order should not be over-read more than the cluster itself.",
            "",
            "## Strong Upper Tier",
            "",
            "These commanders perform well enough to belong in the serious discussion, but the model structure affects how high they climb.",
            "",
            "### Battle-Specialist Leaders",
            "",
        ]
    )

    memo_lines.extend(bullet_line(row) for _, row in battle_specialists.iterrows())
    memo_lines.extend(
        [
            "",
            "These cases are not obvious artifacts. The main issue is that battle-only excellence does not necessarily survive once war-level and campaign-level pages are allowed to absorb some of the score.",
            "",
            "### Broad But Still Sensitive Contenders",
            "",
        ]
    )
    memo_lines.extend(bullet_line(row) for _, row in broad_sensitive.iterrows())
    memo_lines.extend(
        [
            "",
            f"The strongest names in this cluster are {inline_name_list(broad_sensitive_names, limit=6)}. "
            "They remain important contenders, but they are not as secure as the robust elite core and still need model-context qualification.",
            "",
            "## Model-Sensitive Band",
            "",
            "These are the cases where the current data structure appears to be doing too much of the work. They should stay in the audit layer, not in the headline conclusion layer.",
            "",
        ]
    )
    memo_lines.extend(bullet_line(row) for _, row in caution_focus.iterrows())
    memo_lines.extend(
        [
            "",
            f"The sharpest caution signals in this snapshot are {inline_name_list(caution_names, limit=8)}. "
            "These outcomes may still reflect real historical prominence, but the current package does not support treating them as robust all-time elite placements.",
            "",
            "## Focused Audit Of Model-Sensitive High-Rank Cases",
            "",
            "This is the short list of cases that deserve the most scrutiny before any public-facing interpretation.",
            "",
        ]
    )
    memo_lines.extend(audit_line(row) for _, row in audit_focus.iterrows())
    memo_lines.extend(
        [
            "",
            "The main audit pattern is clear:",
            "",
            f"- Some commanders are `battle specialists` in the current dataset. They excel in strict and battle-only models but fall sharply in hierarchical models. The clearest current examples are {inline_name_list(battle_specialist_names, limit=5)}.",
            "- Some commanders are `hierarchical beneficiaries`. They climb when operations, campaigns, and war pages are counted. `Enver Pasha`, `Ivan Konev`, `Aleksandr Vasilevsky`, `Mahmud II`, and `Nelson A. Miles` fit this pattern to different degrees.",
            "- Some commanders are `credit-rule beneficiaries`. They jump when full presence credit is used. `Qasem Soleimani`, `Saddam Hussein`, `Joseph Stalin`, and `Deng Xiaoping` are the clearest cases.",
            "- A few cases show `unusual attribution fragility` even without the higher-level-page flag. `Belisarius` is the most obvious example; the battle-based signal is strong, but one attribution variant produces a major shock.",
            "",
            "## Era-By-Era Elite Shortlist",
            "",
            "Requested era buckets are compressed as follows: `modern` here combines `revolutionary_napoleonic`, `long_nineteenth_century`, `world_wars`, and `cold_war`. "
            "This keeps the interpretive memo aligned with the requested era structure while preserving the original bucket labels in the supporting CSV.",
            "",
            "### Ancient",
            "",
        ]
    )

    memo_lines.extend(era_lines(era_shortlist, "ancient"))
    memo_lines.extend(
        [
            "",
            "Ancient evidence is meaningful but thinner and more abstraction-sensitive than early modern or modern evidence. "
            f"The current ancient shortlist is led by {inline_name_list(ancient_names, limit=3)}.",
            "",
            "### Medieval",
            "",
        ]
    )
    memo_lines.extend(era_lines(era_shortlist, "medieval"))
    memo_lines.extend(
        [
            "",
            f"The medieval shortlist is centered on {inline_name_list(medieval_names, limit=3)}. "
            "These remain powerful cases, but the cross-model stability inside that set still varies materially.",
            "",
            "### Early Modern",
            "",
        ]
    )
    memo_lines.extend(era_lines(era_shortlist, "early_modern"))
    memo_lines.extend(
        [
            "",
            f"The early modern shortlist is led by {inline_name_list(early_modern_names, limit=5)}. "
            "Several of the strongest early-modern cases are battle-heavy, so their exact standing still depends on whether the model stays battle-dominant or absorbs more higher-level pages.",
            "",
            "### Modern",
            "",
        ]
    )
    memo_lines.extend(era_lines(era_shortlist, "modern"))
    memo_lines.extend(
        [
            "",
            f"Modern evidence is the richest part of the current package. The most secure modern shortlist is {inline_name_list(modern_names, limit=5)}. "
            "The late-modern and Cold War end of this bucket is more abstraction-sensitive, so the exact order should stay in the interpretation layer rather than be treated as a clean headline ranking.",
            "",
            "### Contemporary",
            "",
        ]
    )
    memo_lines.extend(era_lines(era_shortlist, "contemporary"))
    memo_lines.extend(
        [
            "",
            f"The current contemporary shortlist is {inline_name_list(contemporary_names, limit=3)}. Contemporary results are thin, highly model-sensitive, and often depend on higher-level pages or sparse battle coverage. "
            "That means the contemporary shortlist should be treated as a weak provisional signal, not as a settled conclusion.",
            "",
            "## Bottom Line",
            "",
            f"The safest current statement is not a final all-time list. It is that the most defensible all-model core in this snapshot is {inline_name_list(robust_names, limit=7)}.",
            "",
            f"A second cluster remains historically important but model-sensitive: {inline_name_list(strong['display_name'].tolist(), limit=8)}. "
            "Those names belong in the serious discussion, but not yet in a single public-facing headline ranking without stronger qualification.",
            "",
            "The weakest claims are the ones driven by higher-level page weighting or by full-credit attribution. Those cases are visible in the package and should remain explicit audit items rather than be smoothed over.",
            "",
        ]
    )

    (snapshot_dir / "BEST_SUPPORTED_TOP_TIER_MEMO.md").write_text(
        "\n".join(memo_lines),
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Build interpretive outputs from ranking results.")
    parser.add_argument(
        "--snapshot-dir",
        type=Path,
        default=Path("outputs_final_2026-04-05"),
        help="Snapshot directory containing ranking outputs.",
    )
    args = parser.parse_args()

    classification, audit, era_shortlist = build_frames(args.snapshot_dir)
    write_csvs(args.snapshot_dir, classification, audit, era_shortlist)
    write_memo(args.snapshot_dir, classification, audit, era_shortlist)


if __name__ == "__main__":
    main()
