# -------------------------------------------------------------------------
# AI USAGE CITATION
# Tool: ChatGPT (OpenAI, 2026)
# Prompt (summary): Add position-aware player comparisons with
# relevant performance rates and a side-by-side display.
# Usage: These tests check the AI-assisted comparison rules and formatting.
# -------------------------------------------------------------------------

import pandas as pd
import pytest

from player_comparison import build_comparison_table, format_vertical_comparison


def _player(
    player_id: int,
    name: str,
    position: str,
    minutes: int,
    goals: int = 0,
    assists: int = 0,
    previous_value: int | None = 10_000_000,
) -> dict:
    return {
        "player_id": player_id,
        "player": name,
        "image_url": f"https://example.com/{player_id}.jpg",
        "team": f"Club {player_id}",
        "league": "ENG-Premier League",
        "position": position,
        "previous_market_value_in_eur": previous_value,
        "baseline_projected_market_value_in_eur": 12_000_000,
        "current_minutes": minutes,
        "current_goals": goals,
        "current_assists": assists,
        "current_yellow_cards": 1,
        "clean_sheet_rate": 0.25,
    }


def test_attacker_comparison_uses_current_per_90_and_minutes_floor():
    players = pd.DataFrame(
        [
            _player(1, "Forward A", "Attack", 450, goals=3, assists=2),
            _player(2, "Forward B", "Attack", 45, goals=1),
        ]
    )

    comparison, note = build_comparison_table(players)
    rows = comparison.set_index("player_id")

    assert rows.loc[1, "player"] == "Forward A"
    assert rows.loc[1, "image_url"] == "https://example.com/1.jpg"
    assert rows.loc[1, "team"] == "Club 1"
    assert rows.loc[1, "league"] == "ENG-Premier League"
    assert rows.loc[1, "position"] == "Attack"
    assert rows.loc[1, "current_value_m"] == 10
    assert rows.loc[1, "projected_value_m"] == 12
    assert rows.loc[1, "projected_change_m"] == 2
    assert rows.loc[1, "minutes"] == 450
    assert rows.loc[1, "goals_per_90"] == pytest.approx(0.6)
    assert rows.loc[1, "assists_per_90"] == pytest.approx(0.4)
    assert rows.loc[1, "contributions_per_90"] == pytest.approx(1)
    assert pd.isna(rows.loc[2, "goals_per_90"])
    assert "below 90 minutes" in note


def test_defender_comparison_labels_projected_clean_sheets_separately():
    players = pd.DataFrame(
        [
            _player(1, "Defender A", "Defender", 450, assists=1),
            _player(2, "Defender B", "Defender", 450, previous_value=None),
        ]
    )

    comparison, note = build_comparison_table(players)
    rows = comparison.set_index("player_id")

    assert "yellow_cards_per_90" in rows.columns
    assert rows.loc[1, "clean_sheet_rate"] == pytest.approx(0.25)
    assert pd.isna(rows.loc[2, "current_value_m"])
    assert pd.isna(rows.loc[2, "projected_change_m"])
    assert "end-of-season projection" in note


def test_goalkeeper_and_mixed_position_comparisons_are_honest_about_coverage():
    goalkeepers = pd.DataFrame(
        [
            _player(1, "Keeper A", "Goalkeeper", 450),
            _player(2, "Keeper B", "Goalkeeper", 450),
        ]
    )
    goalkeepers_table, goalkeepers_note = build_comparison_table(goalkeepers)

    assert "clean_sheet_rate" in goalkeepers_table.columns
    assert "goals_per_90" not in goalkeepers_table.columns
    assert "Save statistics are not available" in goalkeepers_note

    mixed = pd.DataFrame(
        [
            _player(1, "Keeper A", "Goalkeeper", 450),
            _player(3, "Forward C", "Attack", 450),
        ]
    )
    mixed_table, mixed_note = build_comparison_table(mixed)

    assert "goals_per_90" in mixed_table.columns
    assert "Different positions" in mixed_note


def test_comparison_requires_two_or_three_distinct_ids():
    three_players = pd.DataFrame(
        [
            _player(1, "A", "Attack", 450),
            _player(2, "B", "Attack", 450),
            _player(3, "C", "Attack", 450),
        ]
    )
    comparison, _ = build_comparison_table(three_players)
    assert len(comparison) == 3

    one_player = pd.DataFrame([_player(1, "A", "Attack", 450)])
    with pytest.raises(ValueError, match="two or three"):
        build_comparison_table(one_player)

    duplicate_ids = pd.DataFrame(
        [_player(1, "A", "Attack", 450), _player(1, "A", "Attack", 450)]
    )
    with pytest.raises(ValueError, match="unique player_id"):
        build_comparison_table(duplicate_ids)


def test_vertical_comparison_preserves_photos_club_league_and_metric_rows():
    players = pd.DataFrame(
        [
            _player(1, "Forward A", "Attack", 450, goals=3, assists=2),
            _player(2, "Forward B", "Attack", 45, goals=1),
        ]
    )
    comparison, _ = build_comparison_table(players)
    vertical = format_vertical_comparison(comparison).set_index("Metric")

    first = "[Forward A](player?player=1)"
    second = "[Forward B](player?player=2)"
    assert vertical.loc["Photo", first] == "![Forward A](https://example.com/1.jpg)"
    assert vertical.loc["Club", first] == "Club 1"
    assert vertical.loc["League", first] == "Premier League"
    assert vertical.loc["Current value", first] == "€10.0M"
    assert vertical.loc["Projected end-of-season value", first] == "€12.0M"
    assert vertical.loc["Projected change", first] == "€+2.0M"
    assert vertical.loc["Minutes played this season", first] == "450"
    assert vertical.loc["Goals / 90", first] == "0.60"
    assert vertical.loc["Goals / 90", second] == "—"
