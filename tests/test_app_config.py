# -------------------------------------------------------------------------
# AI USAGE CITATION
# Tool: ChatGPT (OpenAI, 2026)
# Prompt (summary): Configure league and club badges for the
# Streamlit app's current player dataset.
# Usage: These tests check the AI-assisted badge configuration and coverage.
# -------------------------------------------------------------------------

from pathlib import Path

import pandas as pd

from app_config import LEAGUE_LOGO_FOLDERS, TEAM_BADGES, TEAM_LOGO_ROOT


DATA_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "processed"
    / "current_season_inference_2026_27.csv"
)


def test_team_badges_cover_dataset_and_all_five_league_logos():
    clubs = pd.read_csv(DATA_PATH, usecols=["league", "team"]).drop_duplicates()
    dataset_clubs = set(
        clubs[["league", "team"]].itertuples(index=False, name=None)
    )

    mapped_paths = set(TEAM_BADGES.values())
    available_paths = {
        path
        for folder in LEAGUE_LOGO_FOLDERS.values()
        for path in (TEAM_LOGO_ROOT / folder).glob("*.png")
    }

    assert len(dataset_clubs) == 96
    assert set(TEAM_BADGES) == dataset_clubs
    assert len(mapped_paths) == 96
    assert mapped_paths == available_paths
    assert all(path.is_file() for path in mapped_paths)
