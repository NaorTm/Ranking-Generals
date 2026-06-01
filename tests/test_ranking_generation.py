from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from build_ranking_package import (
    aggregate_model_metrics,
    build_rankings,
    finalize_model_scores,
    trust_confidence_label,
    trust_tier_v2,
)
from build_scoring_framework_package import OUTCOME_SCORE_MAPS, PAGE_TYPE_WEIGHTS


def ranking_inputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    bridge = pd.DataFrame(
        [
            {
                "analytic_commander_id": "cmd_alpha",
                "display_name": "Alpha",
                "canonical_wikipedia_url": "https://example.test/alpha",
                "is_linked_identity": "1",
                "is_suspect_identity": "0",
            },
            {
                "analytic_commander_id": "cmd_beta",
                "display_name": "Beta",
                "canonical_wikipedia_url": "https://example.test/beta",
                "is_linked_identity": "1",
                "is_suspect_identity": "0",
            },
            {
                "analytic_commander_id": "cmd_gamma",
                "display_name": "Gamma",
                "canonical_wikipedia_url": "https://example.test/gamma",
                "is_linked_identity": "1",
                "is_suspect_identity": "0",
            },
        ]
    )
    summary = pd.DataFrame(
        [
            {
                "analytic_commander_id": row["analytic_commander_id"],
                "display_name": row["display_name"],
                "distinct_opponents_strict": 2,
                "active_span_years_nonwar": 10,
            }
            for row in bridge.to_dict(orient="records")
        ]
    )
    page_profile = bridge[["analytic_commander_id", "display_name"]].copy()
    outcome_profile = bridge[["analytic_commander_id", "display_name"]].copy()
    return bridge, summary, page_profile, outcome_profile


def metric_row(
    commander_id: str,
    *,
    engagement_count: int,
    battle_count: int,
    known_battle_outcome_count: int,
    outcome_mean: float,
    known_outcome_count: int | None = None,
    display_hint: str = "",
    higher_level_share: float = 0.0,
    known_outcome_share: float = 1.0,
) -> dict[str, object]:
    nonbattle_count = engagement_count - battle_count
    known_count = known_battle_outcome_count if known_outcome_count is None else known_outcome_count
    return {
        "analytic_commander_id": commander_id,
        "engagement_count": engagement_count,
        "battle_count": battle_count,
        "operation_count": nonbattle_count,
        "campaign_count": 0,
        "war_count": 0,
        "known_outcome_count": known_count,
        "known_battle_outcome_count": known_battle_outcome_count,
        "presence_mass": float(engagement_count),
        "battle_presence_mass": float(battle_count),
        "nonbattle_presence_mass": float(nonbattle_count),
        "outcome_weight_sum": float(max(known_battle_outcome_count, 1)),
        "weighted_outcome_value": outcome_mean * float(max(known_battle_outcome_count, 1)),
        "conflict_breadth": 2,
        "page_type_diversity": 1 if nonbattle_count == 0 else 2,
        "first_year": 1700,
        "last_year": 1710,
        "known_outcome_share": known_outcome_share,
        "known_battle_outcome_share": known_battle_outcome_count / max(battle_count, 1),
        "outcome_mean": outcome_mean,
        "active_span_years": 10,
        "higher_level_share": higher_level_share,
        "battle_share": battle_count / max(engagement_count, 1),
        "operation_share": nonbattle_count / max(engagement_count, 1),
        "campaign_share": 0.0,
        "war_share": 0.0,
        "era_diversity": 1,
        "primary_era_bucket": "early_modern",
        "feature_quality_flags": display_hint,
        "missing_data_flags": "",
    }


class RankingGenerationTests(unittest.TestCase):
    def write_tiny_build_rankings_fixture(self, output_root: Path) -> None:
        derived = output_root / "derived_scoring"
        derived.mkdir(parents=True)
        commanders = [
            ("cmd_alpha", "Alpha", "victory", "0"),
            ("cmd_beta", "Beta", "victory", "0"),
            ("cmd_gamma", "Gamma", "defeat", "0"),
            ("cmd_suspect", "Suspect", "victory", "1"),
        ]
        annotated_rows: list[dict[str, object]] = []
        summary_rows: list[dict[str, object]] = []
        bridge_rows: list[dict[str, object]] = []
        page_profile_rows: list[dict[str, object]] = []
        outcome_profile_rows: list[dict[str, object]] = []

        for commander_id, display_name, outcome_category, suspect_flag in commanders:
            for index in range(5):
                annotated_rows.append(
                    {
                        "analytic_commander_id": commander_id,
                        "display_name": display_name,
                        "battle_id": f"{commander_id}_battle_{index}",
                        "side": "side_a",
                        "eligible_strict": "1",
                        "eligible_balanced": "1",
                        "outcome_credit_fraction": "1",
                        "page_weight_model_b": "1",
                        "analytic_year": str(1700 + index),
                        "page_type": "battle_article",
                        "outcome_category": outcome_category,
                        "era_bucket": "early_modern",
                        "conflict_key": f"{commander_id}_conflict",
                        "hierarchy_overlap_key": f"{commander_id}_battle_{index}",
                        "battle_name": f"{display_name} battle {index}",
                    }
                )

            bridge_rows.append(
                {
                    "analytic_commander_id": commander_id,
                    "display_name": display_name,
                    "canonical_wikipedia_url": f"https://example.test/{commander_id}",
                    "is_linked_identity": "1",
                    "is_suspect_identity": suspect_flag,
                }
            )
            summary_rows.append(
                {
                    "analytic_commander_id": commander_id,
                    "display_name": display_name,
                    "total_engagements_strict": 5,
                    "total_battle_pages_strict": 5,
                    "total_war_pages_strict": 0,
                    "total_campaign_pages_strict": 0,
                    "total_operation_pages_strict": 0,
                    "distinct_conflicts_strict": 1,
                    "distinct_opponents_strict": 1,
                    "active_span_years_nonwar": 4,
                }
            )
            page_profile_rows.append(
                {
                    "analytic_commander_id": commander_id,
                    "display_name": display_name,
                }
            )
            outcome_profile_rows.append(
                {
                    "analytic_commander_id": commander_id,
                    "display_name": display_name,
                    "known_outcome_count": 5,
                    "known_outcome_share": 1.0,
                    "known_battle_outcome_count": 5,
                    "known_battle_outcome_share": 1.0,
                    "count_victory": 5 if outcome_category == "victory" else 0,
                    "count_decisive_victory": 0,
                    "count_tactical_victory": 0,
                    "count_pyrrhic_victory": 0,
                    "count_defeat": 5 if outcome_category == "defeat" else 0,
                    "count_major_defeat": 0,
                    "count_indecisive": 0,
                    "count_draw": 0,
                    "count_stalemate": 0,
                    "count_disputed": 0,
                    "count_unknown": 0,
                }
            )

        pd.DataFrame(annotated_rows).to_csv(derived / "commander_engagements_annotated.csv", index=False)
        pd.DataFrame(bridge_rows).to_csv(derived / "commander_identity_bridge.csv", index=False)
        pd.DataFrame(summary_rows).to_csv(derived / "commander_engagement_summary.csv", index=False)
        pd.DataFrame(page_profile_rows).to_csv(derived / "commander_page_type_profile.csv", index=False)
        pd.DataFrame(outcome_profile_rows).to_csv(derived / "commander_outcome_profile.csv", index=False)

    def write_mixed_page_type_build_rankings_fixture(self, output_root: Path) -> None:
        derived = output_root / "derived_scoring"
        derived.mkdir(parents=True)
        profiles = [
            (
                "cmd_battle",
                "Battle Commander",
                ["battle_article"] * 6,
                "0",
                "1",
            ),
            (
                "cmd_operation",
                "Operation Commander",
                ["battle_article"] * 3 + ["operation_article"] * 3,
                "0",
                "1",
            ),
            (
                "cmd_war",
                "War Commander",
                ["battle_article"] + ["war_conflict_article"] * 4,
                "0",
                "1",
            ),
            (
                "cmd_unlinked",
                "Unlinked Commander",
                ["battle_article"] * 6,
                "0",
                "0",
            ),
        ]
        annotated_rows: list[dict[str, object]] = []
        summary_rows: list[dict[str, object]] = []
        bridge_rows: list[dict[str, object]] = []
        page_profile_rows: list[dict[str, object]] = []
        outcome_profile_rows: list[dict[str, object]] = []

        for commander_id, display_name, page_types, suspect_flag, linked_flag in profiles:
            page_type_counts = pd.Series(page_types).value_counts().to_dict()
            for index, page_type in enumerate(page_types):
                annotated_rows.append(
                    {
                        "analytic_commander_id": commander_id,
                        "display_name": display_name,
                        "battle_id": f"{commander_id}_engagement_{index}",
                        "side": "side_a",
                        "eligible_strict": "1",
                        "eligible_balanced": "1",
                        "outcome_credit_fraction": "1",
                        "page_weight_model_b": str(PAGE_TYPE_WEIGHTS[page_type]),
                        "analytic_year": str(1800 + index),
                        "page_type": page_type,
                        "outcome_category": "victory",
                        "era_bucket": "revolutionary_napoleonic",
                        "conflict_key": f"{commander_id}_conflict_{index % 2}",
                        "hierarchy_overlap_key": f"{commander_id}_engagement_{index}",
                        "battle_name": f"{display_name} engagement {index}",
                    }
                )

            bridge_rows.append(
                {
                    "analytic_commander_id": commander_id,
                    "display_name": display_name,
                    "canonical_wikipedia_url": f"https://example.test/{commander_id}",
                    "is_linked_identity": linked_flag,
                    "is_suspect_identity": suspect_flag,
                }
            )
            summary_rows.append(
                {
                    "analytic_commander_id": commander_id,
                    "display_name": display_name,
                    "total_engagements_strict": len(page_types),
                    "total_battle_pages_strict": page_type_counts.get("battle_article", 0),
                    "total_war_pages_strict": page_type_counts.get("war_conflict_article", 0),
                    "total_campaign_pages_strict": page_type_counts.get("campaign_article", 0),
                    "total_operation_pages_strict": page_type_counts.get("operation_article", 0),
                    "distinct_conflicts_strict": 2,
                    "distinct_opponents_strict": 2,
                    "active_span_years_nonwar": len(page_types) - 1,
                }
            )
            page_profile_rows.append(
                {
                    "analytic_commander_id": commander_id,
                    "display_name": display_name,
                }
            )
            outcome_profile_rows.append(
                {
                    "analytic_commander_id": commander_id,
                    "display_name": display_name,
                    "known_outcome_count": len(page_types),
                    "known_outcome_share": 1.0,
                    "known_battle_outcome_count": page_type_counts.get("battle_article", 0),
                    "known_battle_outcome_share": 1.0 if page_type_counts.get("battle_article", 0) else 0.0,
                    "count_victory": len(page_types),
                    "count_decisive_victory": 0,
                    "count_tactical_victory": 0,
                    "count_pyrrhic_victory": 0,
                    "count_defeat": 0,
                    "count_major_defeat": 0,
                    "count_indecisive": 0,
                    "count_draw": 0,
                    "count_stalemate": 0,
                    "count_disputed": 0,
                    "count_unknown": 0,
                }
            )

        pd.DataFrame(annotated_rows).to_csv(derived / "commander_engagements_annotated.csv", index=False)
        pd.DataFrame(bridge_rows).to_csv(derived / "commander_identity_bridge.csv", index=False)
        pd.DataFrame(summary_rows).to_csv(derived / "commander_engagement_summary.csv", index=False)
        pd.DataFrame(page_profile_rows).to_csv(derived / "commander_page_type_profile.csv", index=False)
        pd.DataFrame(outcome_profile_rows).to_csv(derived / "commander_outcome_profile.csv", index=False)

    def test_build_rankings_end_to_end_with_tiny_temp_snapshot(self) -> None:
        required_outputs = {
            "RANKING_RESULTS_BASELINE.csv",
            "RANKING_RESULTS_BATTLE_ONLY.csv",
            "RANKING_RESULTS_HIERARCHICAL.csv",
            "RANKING_RESULTS_HIERARCHICAL_TRUST_V2.csv",
            "RANKING_RESULTS_SENSITIVITY.csv",
            "TOP_COMMANDERS_SUMMARY.csv",
            "TIERED_TRUST_V2.csv",
            "RANKING_BUILD_METRICS.json",
        }

        with tempfile.TemporaryDirectory() as raw_first, tempfile.TemporaryDirectory() as raw_second:
            first_root = Path(raw_first)
            second_root = Path(raw_second)
            self.write_tiny_build_rankings_fixture(first_root)
            self.write_tiny_build_rankings_fixture(second_root)

            first_metrics = build_rankings(first_root)
            second_metrics = build_rankings(second_root)

            self.assertTrue(required_outputs.issubset({path.name for path in first_root.iterdir()}))
            self.assertEqual(first_metrics["model_rows"]["baseline_conservative"], 3)
            self.assertEqual(first_metrics["model_rows"]["hierarchical_trust_v2"], 3)
            self.assertEqual(first_metrics, second_metrics)

            baseline = pd.read_csv(first_root / "RANKING_RESULTS_BASELINE.csv")
            sensitivity = pd.read_csv(first_root / "RANKING_RESULTS_SENSITIVITY.csv")
            top_summary = pd.read_csv(first_root / "TOP_COMMANDERS_SUMMARY.csv")
            metrics_json = json.loads((first_root / "RANKING_BUILD_METRICS.json").read_text(encoding="utf-8"))

            self.assertEqual(baseline["display_name"].tolist(), ["Alpha", "Beta", "Gamma"])
            self.assertEqual(baseline["rank"].tolist(), [1, 2, 3])
            self.assertNotIn("Suspect", baseline["display_name"].tolist())
            self.assertGreater(
                float(baseline.loc[baseline["display_name"].eq("Alpha"), "score_normalized"].iloc[0]),
                float(baseline.loc[baseline["display_name"].eq("Gamma"), "score_normalized"].iloc[0]),
            )

            expected_sensitivity_columns = {
                "rank_baseline_conservative",
                "rank_battle_only_baseline",
                "rank_hierarchical_trust_v2",
                "score_hierarchical_trust_v2",
                "trust_confidence_v2",
                "trust_tier_v2",
                "rank_range",
                "top25_appearances",
                "caution_flags",
            }
            self.assertTrue(expected_sensitivity_columns.issubset(set(sensitivity.columns)))
            self.assertEqual(sensitivity["display_name"].tolist(), ["Alpha", "Beta", "Gamma"])
            self.assertNotIn("Suspect", sensitivity["display_name"].tolist())
            self.assertEqual(top_summary["display_name"].tolist(), ["Alpha", "Beta", "Gamma"])
            self.assertEqual([row["display_name"] for row in metrics_json["top_baseline"]], ["Alpha", "Beta", "Gamma"])

            second_baseline = pd.read_csv(second_root / "RANKING_RESULTS_BASELINE.csv")
            second_sensitivity = pd.read_csv(second_root / "RANKING_RESULTS_SENSITIVITY.csv")
            self.assertEqual(baseline["display_name"].tolist(), second_baseline["display_name"].tolist())
            self.assertEqual(sensitivity["display_name"].tolist(), second_sensitivity["display_name"].tolist())

    def test_build_rankings_end_to_end_with_mixed_page_types(self) -> None:
        with tempfile.TemporaryDirectory() as raw_first, tempfile.TemporaryDirectory() as raw_second:
            first_root = Path(raw_first)
            second_root = Path(raw_second)
            self.write_mixed_page_type_build_rankings_fixture(first_root)
            self.write_mixed_page_type_build_rankings_fixture(second_root)

            first_metrics = build_rankings(first_root)
            second_metrics = build_rankings(second_root)

            self.assertEqual(first_metrics, second_metrics)
            self.assertEqual(first_metrics["model_rows"]["baseline_conservative"], 1)
            self.assertEqual(first_metrics["model_rows"]["battle_only_baseline"], 2)
            self.assertEqual(first_metrics["model_rows"]["hierarchical_trust_v2"], 3)

            baseline = pd.read_csv(first_root / "RANKING_RESULTS_BASELINE.csv")
            battle_only = pd.read_csv(first_root / "RANKING_RESULTS_BATTLE_ONLY.csv")
            trust = pd.read_csv(first_root / "RANKING_RESULTS_HIERARCHICAL_TRUST_V2.csv")
            sensitivity = pd.read_csv(first_root / "RANKING_RESULTS_SENSITIVITY.csv")
            tiered = pd.read_csv(first_root / "TIERED_TRUST_V2.csv")

            self.assertEqual(baseline["display_name"].tolist(), ["Battle Commander"])
            self.assertEqual(battle_only["display_name"].tolist(), ["Battle Commander", "Operation Commander"])
            self.assertNotIn("Unlinked Commander", sensitivity["display_name"].tolist())

            required_sensitivity_columns = {
                "rank_hierarchical_trust_v2",
                "rank_hierarchical_broader_eligibility",
                "score_hierarchical_trust_v2",
                "profile_hierarchical_trust_v2",
                "caution_hierarchical_trust_v2",
                "trust_confidence_v2",
                "trust_tier_v2",
                "higher_level_share",
                "known_battle_outcome_count",
            }
            self.assertTrue(required_sensitivity_columns.issubset(set(sensitivity.columns)))

            profiles = sensitivity.set_index("display_name")["page_type_profile_class"].to_dict()
            trust_specific_profiles = sensitivity.set_index("display_name")[
                "profile_hierarchical_trust_v2"
            ].to_dict()
            self.assertEqual(profiles["Battle Commander"], "battle_dominant")
            self.assertEqual(trust_specific_profiles["Operation Commander"], "operation_heavy")
            self.assertEqual(trust_specific_profiles["War Commander"], "war_campaign_heavy")

            war_row = sensitivity.set_index("display_name").loc["War Commander"]
            self.assertGreater(float(war_row["higher_level_share"]), 0.5)
            self.assertIn("higher_level_dependent", str(war_row["caution_flags"]))
            self.assertIn("thin_battle_anchor", str(war_row["caution_flags"]))
            self.assertEqual(war_row["trust_confidence_v2"], "caution")
            self.assertEqual(war_row["known_battle_outcome_count"], 1)

            trust_profiles = trust.set_index("display_name")["page_type_profile_class"].to_dict()
            self.assertEqual(trust_profiles["War Commander"], "war_campaign_heavy")
            self.assertIn("War Commander", tiered["display_name"].tolist())

            second_trust = pd.read_csv(second_root / "RANKING_RESULTS_HIERARCHICAL_TRUST_V2.csv")
            second_sensitivity = pd.read_csv(second_root / "RANKING_RESULTS_SENSITIVITY.csv")
            self.assertEqual(trust["display_name"].tolist(), second_trust["display_name"].tolist())
            self.assertEqual(sensitivity["display_name"].tolist(), second_sensitivity["display_name"].tolist())

    def test_aggregate_model_metrics_handles_unknown_and_malformed_values(self) -> None:
        annotated = pd.DataFrame(
            [
                {
                    "analytic_commander_id": "cmd_alpha",
                    "battle_id": "battle_1",
                    "page_weight_battle_only": "1",
                    "presence_factor_full": 1,
                    "presence_factor_split": 1,
                    "outcome_factor_full": 1,
                    "outcome_factor_split": 0.5,
                    "outcome_category": "victory",
                    "outcome_score_conservative": OUTCOME_SCORE_MAPS["conservative"]["victory"],
                    "page_type": "battle_article",
                    "era_bucket": "early_modern",
                    "conflict_key": "war_a",
                    "analytic_year_num": 1701,
                },
                {
                    "analytic_commander_id": "cmd_alpha",
                    "battle_id": "battle_2",
                    "page_weight_battle_only": "bad",
                    "presence_factor_full": 1,
                    "presence_factor_split": 1,
                    "outcome_factor_full": 1,
                    "outcome_factor_split": 1,
                    "outcome_category": "defeat",
                    "outcome_score_conservative": OUTCOME_SCORE_MAPS["conservative"]["defeat"],
                    "page_type": "battle_article",
                    "era_bucket": "unknown",
                    "conflict_key": "war_b",
                    "analytic_year_num": "not-a-year",
                },
                {
                    "analytic_commander_id": "cmd_beta",
                    "battle_id": "battle_3",
                    "page_weight_battle_only": "1",
                    "presence_factor_full": 1,
                    "presence_factor_split": 1,
                    "outcome_factor_full": 1,
                    "outcome_factor_split": 1,
                    "outcome_category": "unknown",
                    "outcome_score_conservative": 0.0,
                    "page_type": "operation_article",
                    "era_bucket": "medieval",
                    "conflict_key": "war_c",
                    "analytic_year_num": 1200,
                },
                {
                    "analytic_commander_id": "cmd_delta",
                    "battle_id": "battle_4",
                    "page_weight_battle_only": "1",
                    "presence_factor_full": 1,
                    "presence_factor_split": 1,
                    "outcome_factor_full": 1,
                    "outcome_factor_split": 1,
                    "outcome_category": "victory",
                    "outcome_score_conservative": OUTCOME_SCORE_MAPS["conservative"]["victory"],
                    "page_type": "battle_article",
                    "era_bucket": "early_modern",
                    "conflict_key": "war_d",
                    "analytic_year_num": "1700",
                },
                {
                    "analytic_commander_id": "cmd_delta",
                    "battle_id": "battle_5",
                    "page_weight_battle_only": "1",
                    "presence_factor_full": 1,
                    "presence_factor_split": 1,
                    "outcome_factor_full": 1,
                    "outcome_factor_split": 1,
                    "outcome_category": "victory",
                    "outcome_score_conservative": OUTCOME_SCORE_MAPS["conservative"]["victory"],
                    "page_type": "battle_article",
                    "era_bucket": "early_modern",
                    "conflict_key": "war_d",
                    "analytic_year_num": 1705,
                },
                {
                    "analytic_commander_id": "cmd_delta",
                    "battle_id": "battle_6",
                    "page_weight_battle_only": "1",
                    "presence_factor_full": 1,
                    "presence_factor_split": 1,
                    "outcome_factor_full": 1,
                    "outcome_factor_split": 1,
                    "outcome_category": "victory",
                    "outcome_score_conservative": OUTCOME_SCORE_MAPS["conservative"]["victory"],
                    "page_type": "battle_article",
                    "era_bucket": "early_modern",
                    "conflict_key": "war_d",
                    "analytic_year_num": None,
                },
                {
                    "analytic_commander_id": "cmd_delta",
                    "battle_id": "battle_7",
                    "page_weight_battle_only": "1",
                    "presence_factor_full": 1,
                    "presence_factor_split": 1,
                    "outcome_factor_full": 1,
                    "outcome_factor_split": 1,
                    "outcome_category": "victory",
                    "outcome_score_conservative": OUTCOME_SCORE_MAPS["conservative"]["victory"],
                    "page_type": "battle_article",
                    "era_bucket": "early_modern",
                    "conflict_key": "war_d",
                    "analytic_year_num": "not-a-year",
                },
                {
                    "analytic_commander_id": "cmd_delta",
                    "battle_id": "battle_8",
                    "page_weight_battle_only": "bad",
                    "presence_factor_full": 1,
                    "presence_factor_split": 1,
                    "outcome_factor_full": 1,
                    "outcome_factor_split": 1,
                    "outcome_category": "victory",
                    "outcome_score_conservative": OUTCOME_SCORE_MAPS["conservative"]["victory"],
                    "page_type": "battle_article",
                    "era_bucket": "early_modern",
                    "conflict_key": "war_d",
                    "analytic_year_num": "2400",
                },
            ]
        )

        metrics = aggregate_model_metrics(
            annotated,
            row_weight_col="page_weight_battle_only",
            outcome_mode="conservative",
            presence_mode="full",
            outcome_credit_mode="split",
        ).set_index("analytic_commander_id")

        self.assertEqual(metrics.loc["cmd_alpha", "engagement_count"], 1)
        self.assertEqual(metrics.loc["cmd_alpha", "known_outcome_count"], 1)
        self.assertAlmostEqual(metrics.loc["cmd_alpha", "outcome_mean"], OUTCOME_SCORE_MAPS["conservative"]["victory"])
        self.assertEqual(metrics.loc["cmd_beta", "known_outcome_count"], 0)
        self.assertEqual(metrics.loc["cmd_beta", "outcome_mean"], 0.0)
        self.assertEqual(metrics.loc["cmd_beta", "primary_era_bucket"], "medieval")
        self.assertEqual(metrics.loc["cmd_delta", "first_year"], 1700)
        self.assertEqual(metrics.loc["cmd_delta", "last_year"], 1705)
        self.assertEqual(metrics.loc["cmd_delta", "active_span_years"], 5)
        self.assertEqual(metrics.loc["cmd_delta", "engagement_count"], 4)

    def test_finalize_model_scores_tie_breaks_by_name_after_score_and_scale(self) -> None:
        bridge, summary, page_profile, outcome_profile = ranking_inputs()
        metrics = pd.DataFrame(
            [
                metric_row("cmd_beta", engagement_count=5, battle_count=5, known_battle_outcome_count=3, outcome_mean=0.6),
                metric_row("cmd_alpha", engagement_count=5, battle_count=5, known_battle_outcome_count=3, outcome_mean=0.6),
                metric_row("cmd_gamma", engagement_count=5, battle_count=5, known_battle_outcome_count=3, outcome_mean=0.2),
            ]
        )

        ranked = finalize_model_scores(
            metrics,
            bridge,
            summary,
            page_profile,
            outcome_profile,
            model_name="baseline_conservative",
            score_mode="conservative",
            cohort_rule="baseline",
        )

        self.assertEqual(ranked["display_name"].tolist(), ["Alpha", "Beta", "Gamma"])
        self.assertEqual(ranked["rank"].tolist(), [1, 2, 3])
        self.assertEqual(ranked.loc[0, "score_tier"], ranked.loc[1, "score_tier"])

    def test_finalize_model_scores_filters_unlinked_suspect_and_underqualified_rows(self) -> None:
        bridge, summary, page_profile, outcome_profile = ranking_inputs()
        bridge.loc[bridge["analytic_commander_id"].eq("cmd_beta"), "is_suspect_identity"] = "1"
        bridge.loc[bridge["analytic_commander_id"].eq("cmd_gamma"), "is_linked_identity"] = "0"
        metrics = pd.DataFrame(
            [
                metric_row("cmd_alpha", engagement_count=5, battle_count=5, known_battle_outcome_count=3, outcome_mean=0.6),
                metric_row("cmd_beta", engagement_count=5, battle_count=5, known_battle_outcome_count=3, outcome_mean=1.0),
                metric_row("cmd_gamma", engagement_count=5, battle_count=5, known_battle_outcome_count=3, outcome_mean=1.0),
            ]
        )

        ranked = finalize_model_scores(
            metrics,
            bridge,
            summary,
            page_profile,
            outcome_profile,
            model_name="baseline_conservative",
            score_mode="conservative",
            cohort_rule="baseline",
        )

        self.assertEqual(ranked["analytic_commander_id"].tolist(), ["cmd_alpha"])

    def test_hierarchical_trust_guardrail_adds_caution_flags_and_reduces_score(self) -> None:
        bridge, summary, page_profile, outcome_profile = ranking_inputs()
        metrics = pd.DataFrame(
            [
                metric_row(
                    "cmd_alpha",
                    engagement_count=5,
                    battle_count=1,
                    known_battle_outcome_count=1,
                    known_outcome_count=3,
                    outcome_mean=1.0,
                    higher_level_share=0.80,
                    known_outcome_share=0.20,
                ),
                metric_row(
                    "cmd_beta",
                    engagement_count=5,
                    battle_count=5,
                    known_battle_outcome_count=5,
                    outcome_mean=0.8,
                    higher_level_share=0.0,
                    known_outcome_share=1.0,
                ),
            ]
        )

        ranked = finalize_model_scores(
            metrics,
            bridge,
            summary,
            page_profile,
            outcome_profile,
            model_name="hierarchical_trust_v2",
            score_mode="balanced",
            cohort_rule="hierarchical",
        ).set_index("analytic_commander_id")

        self.assertLess(ranked.loc["cmd_alpha", "confidence_guardrail_factor"], 1.0)
        self.assertIn("higher_level_dependent", ranked.loc["cmd_alpha", "caution_flags"])
        self.assertIn("thin_battle_anchor", ranked.loc["cmd_alpha", "caution_flags"])

    def test_confidence_and_tier_boundaries_are_explicit(self) -> None:
        self.assertEqual(
            trust_confidence_label(
                known_outcome_count=24,
                total_battle_pages=15,
                rank_range=12,
                higher_level_share=0.55,
                caution_flags="",
            ),
            "very_high",
        )
        self.assertEqual(
            trust_confidence_label(
                known_outcome_count=16,
                total_battle_pages=10,
                rank_range=24,
                higher_level_share=0.90,
                caution_flags="",
            ),
            "high",
        )
        self.assertEqual(
            trust_tier_v2(
                trust_rank=25,
                confidence_label="high",
                top25_appearances=3,
                rank_range=50,
            ),
            "strong_upper_tier",
        )
        self.assertEqual(
            trust_tier_v2(
                trust_rank=100,
                confidence_label="caution",
                top25_appearances=0,
                rank_range=80,
            ),
            "model_sensitive_band",
        )


if __name__ == "__main__":
    unittest.main()
