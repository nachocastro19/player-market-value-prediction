# -------------------------------------------------------------------------
# AI USAGE CITATION
# Tool: ChatGPT (OpenAI, 2026)
# Prompt (summary, not verbatim): Prepare player data for the Streamlit app,
# including rankings, accent-insensitive search, and stable player links.
# Usage: Used AI assistance for the discovery data and identifier helpers.
# -------------------------------------------------------------------------

from __future__ import annotations

from collections.abc import Hashable
import unicodedata

import pandas as pd


LEAGUE_LABELS = {
    "ENG-Premier League": "Premier League",
    "ESP-La Liga": "La Liga",
    "FRA-Ligue 1": "Ligue 1",
    "GER-Bundesliga": "Bundesliga",
    "ITA-Serie A": "Serie A",
}


def normalize_search_text(value: object) -> str:
    """Normalize text for case- and accent-insensitive player searches."""
    decomposed = unicodedata.normalize("NFKD", str(value).casefold())
    return "".join(
        character
        for character in decomposed
        if not unicodedata.combining(character)
    )


def matches_player_search(value: object, query: object) -> bool:
    """Return whether a display value contains a normalized search query."""
    normalized_query = normalize_search_text(query).strip()
    return not normalized_query or normalized_query in normalize_search_text(value)


def build_players_dataframe(inference_df: pd.DataFrame) -> pd.DataFrame:
    """Add UI-only rankings without mutating the cached inference data."""
    return inference_df.assign(
        goals_league_rank=lambda frame: (
            frame.groupby("league")["current_goals"]
            .rank(method="min", ascending=False)
            .astype("Int64")
        ),
        goals_top5_rank=lambda frame: (
            frame["current_goals"]
            .rank(method="min", ascending=False)
            .astype("Int64")
        ),
        assists_league_rank=lambda frame: (
            frame.groupby("league")["current_assists"]
            .rank(method="min", ascending=False)
            .astype("Int64")
        ),
        assists_top5_rank=lambda frame: (
            frame["current_assists"]
            .rank(method="min", ascending=False)
            .astype("Int64")
        ),
    )


def selectable_players(players_df: pd.DataFrame) -> pd.DataFrame:
    """Return one row per player with a stable ID or fallback source code."""
    players = players_df.copy()
    has_player_id = players["player_id"].notna()
    has_fallback_code = (
        players["player_code_fb"].notna()
        & players["player_code_fb"].astype("string").str.strip().ne("")
    )
    players = players.loc[has_player_id | has_fallback_code].copy()
    players["player_key"] = players.apply(serialize_player_key, axis=1)
    return players.drop_duplicates("player_key").copy()


def serialize_player_id(player_id: Hashable) -> str:
    """Create a clean, stable player identifier for URLs."""
    try:
        numeric_id = float(player_id)
    except (TypeError, ValueError):
        return str(player_id)

    if numeric_id.is_integer():
        return str(int(numeric_id))
    return str(player_id)


def serialize_player_key(player: object) -> str:
    """Keep legacy ID URLs; use a namespaced source code when ID is absent."""
    player_id = player.get("player_id")
    if pd.notna(player_id):
        return serialize_player_id(player_id)

    player_code = player.get("player_code_fb")
    if pd.isna(player_code) or not str(player_code).strip():
        raise ValueError("A player needs a player_id or player_code_fb.")
    return f"fb-{str(player_code).strip()}"


def resolve_player_id(raw_player_id: object, player_ids: list[Hashable]) -> Hashable | None:
    """Match a legacy numeric ID or a fallback player key from a URL."""
    if raw_player_id is None:
        return None

    requested = str(raw_player_id)
    return next(
        (
            player_id
            for player_id in player_ids
            if serialize_player_id(player_id) == requested
            or str(player_id) == requested
        ),
        None,
    )


def resolve_player_key(raw_player_key: object, player_keys: list[Hashable]) -> Hashable | None:
    """Resolve a route key, retaining compatibility with numeric player IDs."""
    return resolve_player_id(raw_player_key, player_keys)
