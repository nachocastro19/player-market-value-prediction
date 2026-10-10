"""Build a small, position-aware comparison from discovery data."""

from __future__ import annotations

import pandas as pd

from player_data import LEAGUE_LABELS, serialize_player_id


MIN_MINUTES_FOR_PER_90 = 90

METRIC_LABELS = {
    "goals_per_90": "Goals / 90",
    "assists_per_90": "Assists / 90",
    "contributions_per_90": "Goal contributions / 90",
    "yellow_cards_per_90": "Yellow cards / 90",
    "clean_sheet_rate": "Projected clean-sheet rate",
}


def _millions(value: object) -> float | None:
    return None if pd.isna(value) else float(value) / 1_000_000


def _per_90(count: object, minutes: object) -> float | None:
    """Use observed season totals, suppressing rates from under 90 minutes."""
    if pd.isna(count) or pd.isna(minutes) or float(minutes) < MIN_MINUTES_FOR_PER_90:
        return None
    return float(count) * 90 / float(minutes)


def _similarity_features(players: pd.DataFrame, position: str) -> pd.DataFrame:
    """Build a small set of current-season profile features by position."""
    minutes = pd.to_numeric(players["current_minutes"], errors="coerce")
    features = pd.DataFrame(index=players.index)
    features["age"] = pd.to_numeric(players["age_at_valuation"], errors="coerce")
    features["minutes"] = minutes

    if position == "Goalkeeper":
        features["clean_sheet_rate"] = pd.to_numeric(
            players["clean_sheet_rate"], errors="coerce"
        )
    else:
        for source, feature in (
            ("current_goals", "goals_per_90"),
            ("current_assists", "assists_per_90"),
        ):
            counts = pd.to_numeric(players[source], errors="coerce")
            features[feature] = (counts * 90 / minutes).where(
                minutes >= MIN_MINUTES_FOR_PER_90
            )

        if position == "Defender":
            yellow_cards = pd.to_numeric(
                players["current_yellow_cards"], errors="coerce"
            )
            features["yellow_cards_per_90"] = (
                yellow_cards * 90 / minutes
            ).where(minutes >= MIN_MINUTES_FOR_PER_90)
            features["clean_sheet_rate"] = pd.to_numeric(
                players["clean_sheet_rate"], errors="coerce"
            )

    return features


def find_similar_players(
    players: pd.DataFrame,
    player_id: object,
    top_n: int = 3,
) -> pd.DataFrame:
    """Find same-position peers by standardized age, workload, and output.

    Current and predicted market values are intentionally excluded from the
    distance so the peer list is based on player profile rather than price.
    """
    identity_column = "player_key" if "player_key" in players else "player_id"
    selected_rows = players.loc[players[identity_column] == player_id]
    if selected_rows.empty or top_n < 1:
        return players.iloc[0:0].copy()

    selected = selected_rows.iloc[0]
    position = selected.get("position")
    if pd.isna(position):
        return players.iloc[0:0].copy()
    position = str(position)

    candidates = (
        players.loc[players["position"].astype(str) == position]
        .drop_duplicates(identity_column)
        .loc[lambda frame: frame[identity_column] != player_id]
        .reset_index(drop=True)
    )
    if candidates.empty:
        return candidates

    # A broad group such as Midfield contains very different roles. Prefer an
    # exact sub-position whenever there are enough peers to fill the display.
    sub_position = selected.get("sub_position")
    if pd.notna(sub_position):
        role_candidates = candidates.loc[
            candidates["sub_position"].astype(str) == str(sub_position)
        ]
        if len(role_candidates) >= top_n:
            candidates = role_candidates.reset_index(drop=True)

    candidate_features = _similarity_features(candidates, position)
    selected_features = _similarity_features(
        selected_rows.iloc[[0]].reset_index(drop=True),
        position,
    )
    usable = candidate_features.notna().sum(axis=1) >= 2
    candidates = candidates.loc[usable].reset_index(drop=True)
    candidate_features = candidate_features.loc[usable].reset_index(drop=True)
    if candidates.empty or selected_features.notna().sum(axis=1).iloc[0] < 2:
        return players.iloc[0:0].copy()

    combined = pd.concat(
        [candidate_features, selected_features],
        ignore_index=True,
    )
    means = combined.mean().fillna(0)
    scales = combined.std(ddof=0).replace(0, 1).fillna(1)
    scaled = (combined - means) / scales
    distances = (
        scaled.iloc[:-1]
        .sub(scaled.iloc[-1], axis="columns")
        .pow(2)
        .mean(axis=1)
        .pow(0.5)
    )

    candidates["similarity_distance"] = distances.to_numpy()
    return candidates.sort_values("similarity_distance").head(top_n).reset_index(drop=True)


def _position_metric_keys(positions: set[str]) -> tuple[str, ...]:
    if positions == {"Attack"}:
        return ("goals_per_90", "assists_per_90", "contributions_per_90")
    if positions == {"Midfield"}:
        return ("assists_per_90", "contributions_per_90", "goals_per_90")
    if positions == {"Defender"}:
        return ("contributions_per_90", "yellow_cards_per_90", "clean_sheet_rate")
    if positions == {"Goalkeeper"}:
        return ("clean_sheet_rate",)
    return ("goals_per_90", "assists_per_90", "contributions_per_90")


def build_comparison_table(players: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    """Return one row per player and a note about metric limitations."""
    if not 2 <= len(players) <= 3:
        raise ValueError("Choose two or three players to compare.")
    identity_column = "player_key" if "player_key" in players else "player_id"
    if players[identity_column].duplicated().any():
        raise ValueError(
            "Each compared player must have a unique player_id/player key."
        )

    positions = set(players["position"].dropna().astype(str))
    metric_keys = _position_metric_keys(positions)
    rows = []
    for player in players.itertuples(index=False):
        player = pd.Series(player._asdict())
        minutes = player["current_minutes"]
        goals = player["current_goals"]
        assists = player["current_assists"]
        current_value = _millions(player["previous_market_value_in_eur"])
        projected_value = _millions(player["baseline_projected_market_value_in_eur"])
        contributions = (
            goals + assists if pd.notna(goals) and pd.notna(assists) else None
        )
        metrics = {
            "goals_per_90": _per_90(goals, minutes),
            "assists_per_90": _per_90(assists, minutes),
            "contributions_per_90": _per_90(contributions, minutes),
            "yellow_cards_per_90": _per_90(player["current_yellow_cards"], minutes),
            "clean_sheet_rate": (
                None if pd.isna(player["clean_sheet_rate"])
                else float(player["clean_sheet_rate"])
            ),
        }
        rows.append(
            {
                "player_id": player["player_id"],
                "player_key": (
                    player["player_key"]
                    if "player_key" in player
                    else serialize_player_id(player["player_id"])
                ),
                "player": player["player"],
                "image_url": player.get("image_url"),
                "team": player["team"],
                "league": player["league"],
                "position": player["position"],
                "current_value_m": current_value,
                "projected_value_m": projected_value,
                "projected_change_m": (
                    projected_value - current_value
                    if current_value is not None and projected_value is not None
                    else None
                ),
                "minutes": None if pd.isna(minutes) else float(minutes),
                **{key: metrics[key] for key in metric_keys},
            }
        )

    notes = ["Per-90 stats use current-season totals and are hidden below 90 minutes."]
    if "clean_sheet_rate" in metric_keys:
        notes.append(
            "Clean-sheet rate comes from the end-of-season projection and "
            "reflects team context too."
        )
    if positions == {"Goalkeeper"}:
        notes.append("Save statistics are not available in this dataset.")
    elif len(positions) > 1:
        notes.append("Different positions make attacking rates less comparable.")

    return pd.DataFrame(rows), " ".join(notes)


def format_vertical_comparison(comparison: pd.DataFrame) -> pd.DataFrame:
    """Format player rows as a compact metric-by-player table for Streamlit."""
    metric_keys = [key for key in comparison.columns if key in METRIC_LABELS]
    metric_names = [
        "Photo",
        "Club",
        "League",
        "Position",
        "Current value",
        "Projected end-of-season value",
        "Projected change",
        "Minutes played this season",
        *(METRIC_LABELS[key] for key in metric_keys),
    ]
    columns: dict[str, list[str]] = {"Metric": metric_names}
    duplicate_names = comparison["player"].duplicated(keep=False)
    used_labels: set[str] = set()

    for position, (_, player) in enumerate(comparison.iterrows()):
        name = str(player["player"])
        label = f"{name} · {player['team']}" if duplicate_names.iloc[position] else name
        if label in used_labels:
            label = f"{label} ({serialize_player_id(player['player_id'])})"
        used_labels.add(label)
        player_key = (
            player["player_key"]
            if "player_key" in player and pd.notna(player["player_key"])
            else serialize_player_id(player["player_id"])
        )
        header = f"[{label}](player?player={player_key})"
        image_url = player["image_url"]
        values = {
            "Photo": (
                f"![{name}]({image_url})"
                if isinstance(image_url, str) and image_url
                else "—"
            ),
            "Club": str(player["team"]),
            "League": LEAGUE_LABELS.get(player["league"], str(player["league"])),
            "Position": str(player["position"]),
            "Current value": _display_millions(player["current_value_m"]),
            "Projected end-of-season value": _display_millions(
                player["projected_value_m"]
            ),
            "Projected change": _display_millions(
                player["projected_change_m"], signed=True
            ),
            "Minutes played this season": (
                "—" if pd.isna(player["minutes"]) else f"{player['minutes']:,.0f}"
            ),
            **{
                METRIC_LABELS[key]: _display_rate(
                    player[key], percentage=key == "clean_sheet_rate"
                )
                for key in metric_keys
            },
        }
        columns[header] = [values[name] for name in metric_names]

    return pd.DataFrame(columns)


def _display_millions(value: object, *, signed: bool = False) -> str:
    if pd.isna(value):
        return "—"
    return f"€{float(value):+,.1f}M" if signed else f"€{float(value):,.1f}M"


def _display_rate(value: object, *, percentage: bool = False) -> str:
    if pd.isna(value):
        return "—"
    return f"{float(value):.0%}" if percentage else f"{float(value):.2f}"
