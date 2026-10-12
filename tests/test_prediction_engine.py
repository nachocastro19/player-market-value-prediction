# -------------------------------------------------------------------------
# AI USAGE CITATION
# Tool: ChatGPT (OpenAI, 2026)
# Prompt (summary): Route predictions between the production
# models and recalculate features when a user changes scenario inputs.
# Usage: These tests check the AI-assisted prediction and scenario logic.
# -------------------------------------------------------------------------

import numpy as np
import pandas as pd
import pytest

import prediction_engine as engine


def test_build_scenario_recalculates_derived_features():
    player = engine.df.loc[engine.df["player_id"].notna()].iloc[0].copy()
    games = max(int(player["current_games"]), 20)
    minutes = max(int(player["current_minutes"]), 1_800)
    minutes = min(minutes, games * 90)

    scenario = engine.build_scenario(
        player,
        changes={
            "projected_games": games,
            "projected_minutes": minutes,
            "projected_goals": 10,
            "projected_assists": 5,
        },
    )

    assert scenario["total_games_played_season"] == games
    assert scenario["total_minutes_played"] == minutes
    assert scenario["total_goals"] == 10
    assert scenario["goals_per_90_min"] == pytest.approx(10 * 90 / minutes)
    assert scenario["goal_contributions_per_90_min"] == pytest.approx(
        15 * 90 / minutes
    )


def test_build_scenario_rejects_impossible_minutes():
    player = engine.df.loc[engine.df["player_id"].notna()].iloc[0].copy()

    with pytest.raises(ValueError, match="projected games × 90"):
        engine.build_scenario(
            player,
            changes={
                "projected_games": 10,
                "projected_minutes": 901,
            },
        )


def test_no_history_player_uses_fallback_model():
    player = engine.df.loc[
        engine.df["player_id"].notna()
        & engine.df["previous_market_value_in_eur"].isna()
    ].iloc[0]

    result = engine.predict_scenario_by_player_id(player["player_id"])

    assert np.isfinite(result["scenario_projected_market_value_in_eur"])
    assert result["scenario_projected_market_value_in_eur"] >= 0
    assert pd.isna(result["previous_market_value_in_eur"])


def test_player_without_transfermarkt_id_can_be_predicted_by_fallback_code():
    player = engine.df.loc[engine.df["player_code_fb"] == "bil-nsongo"].iloc[0]

    result = engine.predict_scenario_by_player_id("fb-bil-nsongo")

    assert result["player"] == player["player"]
    assert result["player_key"] == "fb-bil-nsongo"
    assert np.isfinite(result["scenario_projected_market_value_in_eur"])
    assert pd.isna(result["previous_market_value_in_eur"])
