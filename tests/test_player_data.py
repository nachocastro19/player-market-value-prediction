# -------------------------------------------------------------------------
# AI USAGE CITATION
# Tool: ChatGPT (OpenAI, 2026)
# Prompt (summary): Prepare player search and stable identifiers
# for discovery and detail pages in the Streamlit app.
# Usage: These tests check the AI-assisted search and player-key helpers.
# -------------------------------------------------------------------------

from pathlib import Path

import pandas as pd

from player_data import normalize_search_text, resolve_player_key, selectable_players


def test_search_normalization_ignores_accents_and_case():
    assert normalize_search_text("José María Giménez") == "jose maria gimenez"
    assert normalize_search_text("Yeremay Hernández") == "yeremay hernandez"


def test_missing_transfermarkt_ids_use_unique_fallback_player_codes():
    data_path = (
        Path(__file__).resolve().parents[1]
        / "data"
        / "processed"
        / "current_season_inference_2026_27.csv"
    )
    inference = pd.read_csv(data_path)
    players = selectable_players(inference)

    assert len(players) == 2_070
    assert players["player_key"].is_unique
    assert players["player_key"].str.startswith("fb-").sum() == 288

    for fallback_key, expected_name in (
        ("fb-bil-nsongo", "Bil Nsongo"),
        ("fb-yeremay-hernandez", "Yeremay Hernández"),
    ):
        match = players.loc[players["player_key"] == fallback_key]
        assert len(match) == 1
        assert match.iloc[0]["player"] == expected_name
        assert pd.isna(match.iloc[0]["player_id"])

    assert resolve_player_key("562742", players["player_key"].tolist()) == "562742"
    assert (
        resolve_player_key("fb-bil-nsongo", players["player_key"].tolist())
        == "fb-bil-nsongo"
    )
