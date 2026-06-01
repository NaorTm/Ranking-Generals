from __future__ import annotations

import unittest

import pandas as pd

from build_scoring_framework_package import (
    canonicalize_wikipedia_url,
    contains_negative_target,
    contains_result_token,
    derive_outcome_category,
    derive_scoring_result_fields,
    extract_match_tokens,
    infer_winner_side,
    join_flags,
    make_id,
    parse_float,
)


class ScoringFrameworkTests(unittest.TestCase):
    def test_derive_scoring_result_fields_repairs_citation_fused_victory(self) -> None:
        raw, normalized, result_type, source = derive_scoring_result_fields(
            "Roman victoryDaryaee 2010",
            "",
            "unknown",
        )

        self.assertEqual(raw, "Roman victory Daryaee 2010")
        self.assertEqual(normalized, "Victory")
        self.assertEqual(result_type, "victory")
        self.assertEqual(source, "sanitized_result_raw")

    def test_derive_scoring_result_fields_preserves_stored_known_type(self) -> None:
        raw, normalized, result_type, source = derive_scoring_result_fields(
            "Messy raw text",
            "Defeat",
            "defeat",
        )

        self.assertEqual(raw, "Messy raw text")
        self.assertEqual(normalized, "Defeat")
        self.assertEqual(result_type, "defeat")
        self.assertEqual(source, "stored")

    def test_derive_scoring_result_fields_applies_scoring_specific_override(self) -> None:
        raw, normalized, result_type, source = derive_scoring_result_fields(
            "Allied operational success",
            "",
            "unknown",
        )

        self.assertEqual(raw, "Allied operational success")
        self.assertEqual(normalized, "Tactical Victory")
        self.assertEqual(result_type, "tactical_victory")
        self.assertEqual(source, "scoring_specific_override")

    def test_token_matching_uses_word_boundaries_and_negative_targets(self) -> None:
        self.assertTrue(contains_result_token("roman victory", "roman"))
        self.assertFalse(contains_result_token("postroman victory", "roman"))
        self.assertTrue(contains_negative_target("anti-swedish coalition victory", "swedish"))
        self.assertTrue(contains_negative_target("victory against sweden", "sweden"))

    def test_extract_match_tokens_adds_aliases_and_deduplicates(self) -> None:
        tokens = extract_match_tokens("United States | USA | Denmark-Norway")

        self.assertIn("united states", tokens)
        self.assertIn("american", tokens)
        self.assertIn("dano-norwegian", tokens)
        self.assertEqual(len(tokens), len(set(tokens)))

    def test_infer_winner_side_handles_anti_target_result(self) -> None:
        battle = pd.Series(
            {
                "belligerent_1_raw": "Sweden",
                "belligerent_2_raw": "Denmark-Norway; Saxony",
                "commander_side_a_raw": "Charles XII",
                "commander_side_b_raw": "Frederick IV",
                "page_type": "battle_article",
                "battle_name": "Example battle",
                "wikipedia_title": "Example battle",
            }
        )

        winner, method = infer_winner_side("Anti-Swedish coalition victory", "victory", battle)

        self.assertEqual(winner, "side_b")
        self.assertEqual(method, "negated_target_match")

    def test_derive_outcome_category_maps_winner_and_loser_sides(self) -> None:
        battle = pd.Series(
            {
                "belligerent_1_raw": "France",
                "belligerent_2_raw": "Austria",
                "commander_side_a_raw": "French commander",
                "commander_side_b_raw": "Austrian commander",
                "page_type": "battle_article",
                "battle_name": "Example battle",
                "wikipedia_title": "Example battle",
            }
        )

        winner = derive_outcome_category("", "decisive_victory", "French decisive victory", "side_a", battle)
        loser = derive_outcome_category("", "decisive_victory", "French decisive victory", "side_b", battle)

        self.assertEqual(winner, ("decisive_victory", "inferred_unique_belligerent_match", "medium"))
        self.assertEqual(loser, ("major_defeat", "inferred_unique_belligerent_match", "medium"))

    def test_derive_outcome_category_returns_unknown_for_ambiguous_result(self) -> None:
        battle = pd.Series(
            {
                "belligerent_1_raw": "Red forces",
                "belligerent_2_raw": "Blue forces",
                "page_type": "battle_article",
                "battle_name": "Example battle",
                "wikipedia_title": "Example battle",
            }
        )

        self.assertEqual(
            derive_outcome_category("", "victory", "Victory", "side_a", battle),
            ("unknown", "unknown", "low"),
        )

    def test_small_helpers_handle_malformed_input_deterministically(self) -> None:
        self.assertIsNone(parse_float("not-a-number"))
        self.assertEqual(parse_float(" 3.5 "), 3.5)
        self.assertEqual(
            canonicalize_wikipedia_url("https://en.wikipedia.org/wiki/Alexander the Great/"),
            "https://en.wikipedia.org/wiki/Alexander_the_Great",
        )
        self.assertEqual(make_id("cmd", "same-key"), make_id("cmd", "same-key"))
        self.assertEqual(join_flags(["b", "", "a", "b"]), "a | b")


if __name__ == "__main__":
    unittest.main()
