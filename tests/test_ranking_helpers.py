from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from assign_commander_tiers import tier_for_row
from build_ranking_package import page_profile_class, percentile_score, trust_confidence_label, trust_tier_v2
from compute_model_stability import compute_stability


class RankingHelperTests(unittest.TestCase):
    def test_percentile_score_handles_single_and_ties(self) -> None:
        self.assertEqual(percentile_score(pd.Series([42])).tolist(), [100.0])

        tied = percentile_score(pd.Series([10, 10, 30]))

        self.assertEqual(tied.round(6).tolist(), [50.0, 50.0, 100.0])

    def test_trust_confidence_label_applies_caution_for_explicit_risks(self) -> None:
        label = trust_confidence_label(
            known_outcome_count=30,
            total_battle_pages=20,
            rank_range=8,
            higher_level_share=0.20,
            caution_flags="thin_battle_anchor",
        )

        self.assertEqual(label, "caution")

    def test_trust_tier_v2_requires_stable_high_confidence_for_core(self) -> None:
        self.assertEqual(
            trust_tier_v2(
                trust_rank=8,
                confidence_label="high",
                top25_appearances=4,
                rank_range=20,
            ),
            "robust_elite_core",
        )
        self.assertEqual(
            trust_tier_v2(
                trust_rank=8,
                confidence_label="moderate",
                top25_appearances=4,
                rank_range=20,
            ),
            "high_confidence_upper_band",
        )

    def test_page_profile_class_prioritizes_battle_dominance(self) -> None:
        self.assertEqual(page_profile_class(0.72, 0.10, 0.10, 0.08), "battle_dominant")
        self.assertEqual(page_profile_class(0.20, 0.10, 0.30, 0.25), "war_campaign_heavy")
        self.assertEqual(page_profile_class(0.30, 0.45, 0.20, 0.05), "operation_heavy")
        self.assertEqual(page_profile_class(0.40, 0.20, 0.20, 0.20), "mixed_profile")

    def test_tier_for_row_keeps_siege_specialists_out_of_generic_elite(self) -> None:
        row = pd.Series(
            {
                "display_name": "Vauban",
                "rank_hierarchical_trust_v2": 5,
                "rank_battle_only_baseline": 5,
                "stability_score": 95,
                "known_outcome_count": 30,
                "known_outcome_share": 0.90,
                "higher_level_share": 0.10,
                "siege_event_share": 0.50,
            }
        )

        key, label, sort_order, reason = tier_for_row(row)

        self.assertEqual(key, "tier_d_strong_narrow_category")
        self.assertIn("narrow-category", label)
        self.assertEqual(sort_order, 4)
        self.assertIn("category-specific", reason)

    def test_tier_for_row_identifies_robust_elite(self) -> None:
        row = pd.Series(
            {
                "display_name": "Example Commander",
                "rank_hierarchical_trust_v2": 10,
                "rank_battle_only_baseline": 20,
                "stability_score": 80,
                "known_outcome_count": 12,
                "known_outcome_share": 0.75,
                "higher_level_share": 0.20,
                "siege_event_share": 0.0,
            }
        )

        self.assertEqual(tier_for_row(row)[0], "tier_a_robust_elite")

    def test_compute_stability_skips_unranked_rows_and_sorts_deterministically(self) -> None:
        with tempfile.TemporaryDirectory() as raw_root:
            snapshot_dir = Path(raw_root)
            frame = pd.DataFrame(
                [
                    {
                        "analytic_commander_id": "cmd_b",
                        "display_name": "Beta",
                        "canonical_wikipedia_url": "https://example.test/beta",
                        "rank_hierarchical_trust_v2": 2,
                        "rank_hierarchical_weighted": 2,
                        "rank_baseline_conservative": 4,
                        "score_hierarchical_trust_v2": 90,
                        "score_hierarchical_weighted": 88,
                    },
                    {
                        "analytic_commander_id": "cmd_a",
                        "display_name": "Alpha",
                        "canonical_wikipedia_url": "https://example.test/alpha",
                        "rank_hierarchical_trust_v2": 1,
                        "rank_hierarchical_weighted": 3,
                        "rank_baseline_conservative": 5,
                        "score_hierarchical_trust_v2": 92,
                        "score_hierarchical_weighted": 87,
                    },
                    {
                        "analytic_commander_id": "cmd_empty",
                        "display_name": "No Rank",
                        "canonical_wikipedia_url": "",
                    },
                ]
            )
            frame.to_csv(snapshot_dir / "RANKING_RESULTS_SENSITIVITY.csv", index=False)

            output = compute_stability(snapshot_dir)

            self.assertEqual(output["commander_name"].tolist(), ["Alpha", "Beta"])
            self.assertEqual(output["trusted_models_present_count"].tolist(), [3, 3])
            self.assertTrue((output["stability_score"] > 0).all())


if __name__ == "__main__":
    unittest.main()
