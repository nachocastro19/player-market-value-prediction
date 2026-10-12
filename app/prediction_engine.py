import json
import joblib
import numpy as np
import pandas as pd
import shap
import streamlit as st


from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_PATH = (
    BASE_DIR
    / "data"
    / "processed"
    / "current_season_inference_2026_27.csv"
)

METADATA_PATH = (
    BASE_DIR
    / "models"
    / "production_metadata.json"
)

MODEL_WITHOUT_HISTORY_PATH = (
    BASE_DIR
    / "models"
    / "xgb_without_history_production.joblib"
)

MODEL_WITH_HISTORY_PATH = (
    BASE_DIR
    / "models"
    / "xgb_with_history_production.joblib"
)

# -------------------------------------------------------------------------
# AI USAGE CITATION
# Tool: ChatGPT (OpenAI, 2026)
# Prompt (summary): Load and cache the current-season data,
# production models, and feature metadata for a Streamlit app.
# Usage: Used AI assistance for resource loading and caching.
# -------------------------------------------------------------------------

@st.cache_data
def load_inference_data(path):
    """Load the static inference dataset once per app process."""
    return pd.read_csv(path)


@st.cache_resource
def load_model_resources(
    metadata_path,
    model_without_history_path,
    model_with_history_path,
):
    """Load metadata and fitted model pipelines as shared resources."""
    with open(metadata_path, "r", encoding="utf-8") as file:
        loaded_metadata = json.load(file)

    return (
        loaded_metadata,
        joblib.load(model_without_history_path),
        joblib.load(model_with_history_path),
    )


df = load_inference_data(DATA_PATH)


def _player_matches(identifier):
    """Find a player by legacy Transfermarkt ID or fallback source code key."""
    key = str(identifier)
    if key.startswith("fb-"):
        return df["player_code_fb"].astype("string").eq(key[3:])

    try:
        numeric_id = float(identifier)
    except (TypeError, ValueError):
        return df["player_id"].astype("string").eq(key)
    return df["player_id"].eq(numeric_id)

(
    metadata,
    model_without_history,
    model_with_history,
) = load_model_resources(
    METADATA_PATH,
    MODEL_WITHOUT_HISTORY_PATH,
    MODEL_WITH_HISTORY_PATH,
)

FEATURES_WITHOUT_HISTORY = (
    metadata["features_without_history"]
)

FEATURES_WITH_HISTORY = (
    metadata["features_with_history"]
)

# -------------------------------------------------------------------------
# AI USAGE CITATION
# Tool: ChatGPT (OpenAI, 2026)
# Prompt (summary): Route players with a previous valuation to
# the history model and other players to the fallback model, then return euros.
# Usage: Used AI assistance to adapt the notebook prediction logic for the app.
# -------------------------------------------------------------------------

def predict_market_value(input_df):
    """
    Route each player to the correct production model
    and return predicted market value in euros.
    """

    data = input_df.copy()

    # Previous market value available -> history model
    history_mask = (
        data["previous_market_value_in_eur"].notna()
    )

    log_predictions = pd.Series(
        index=data.index,
        dtype=float
    )

    # With-history model
    if history_mask.any():

        X_history = data.loc[
            history_mask,
            FEATURES_WITH_HISTORY
        ]

        log_predictions.loc[history_mask] = (
            model_with_history.predict(X_history)
        )

    # Without-history model
    no_history_mask = ~history_mask

    if no_history_mask.any():

        X_no_history = data.loc[
            no_history_mask,
            FEATURES_WITHOUT_HISTORY
        ]

        log_predictions.loc[no_history_mask] = (
            model_without_history.predict(X_no_history)
        )

    # Inverse target transformation
    predictions = np.expm1(log_predictions)

    return predictions.clip(lower=0)


df["baseline_projected_market_value_in_eur"] = (
    predict_market_value(df)
    .round()
    .astype("Int64")
)


# -------------------------------------------------------------------------
# AI USAGE CITATION
# Tool: ChatGPT (OpenAI, 2026)
# Prompt (summary): Apply user-selected season assumptions to a
# player, recalculate dependent features, and predict the scenario value.
# Usage: Used AI assistance for the scenario feature and prediction logic.
# -------------------------------------------------------------------------

def build_scenario(
    player_row,
    changes=None,
):
    """
    Build an end-of-season scenario for one player.

    User-editable features can be overridden through `changes`.
    Derived model features are recalculated automatically.
    Static/historical features remain unchanged.
    """

    row = player_row.copy()
    changes = changes or {}

    EDITABLE_FIELDS = {
        # Main player performance
        "projected_games",
        "projected_minutes",
        "projected_goals",
        "projected_assists",

        # Discipline
        "projected_yellow_cards",
        "projected_red_cards",

        # Defensive / clean sheet context
        "total_clean_sheets",

        # Team context
        "club_goals_scored",
        "club_goals_conceded",
        "avg_points_per_game",

        # Season context
        "clubs_played_for_season",

        # Transfer scenario
        "transfers_during_season",
        "days_since_last_transfer",
    }

    unknown_fields = (
        set(changes)
        - EDITABLE_FIELDS
    )

    if unknown_fields:
        raise ValueError(
            f"Unsupported scenario fields: "
            f"{sorted(unknown_fields)}"
        )

    # ----------------------------------------
    # APPLY USER OVERRIDES
    # ----------------------------------------

    for field, value in changes.items():
        if value is not None:
            row[field] = value

    # ----------------------------------------
    # VALIDATION - PLAYER PERFORMANCE
    # ----------------------------------------

    non_negative_fields = [
        "projected_games",
        "projected_minutes",
        "projected_goals",
        "projected_assists",
        "projected_yellow_cards",
        "projected_red_cards",
        "total_clean_sheets",
        "club_goals_scored",
        "club_goals_conceded",
        "clubs_played_for_season",
    ]

    for field in non_negative_fields:
        if (
            field in row
            and pd.notna(row[field])
            and row[field] < 0
        ):
            raise ValueError(
                f"{field} cannot be negative."
            )

    # End-of-season totals cannot be below
    # stats already achieved.
    minimum_checks = {
        "projected_games": "current_games",
        "projected_minutes": "current_minutes",
        "projected_goals": "current_goals",
        "projected_assists": "current_assists",
        "projected_yellow_cards": "current_yellow_cards",
        "projected_red_cards": "current_red_cards",
    }

    for projected_col, current_col in minimum_checks.items():

        if (
            projected_col in row
            and current_col in row
            and pd.notna(row[projected_col])
            and pd.notna(row[current_col])
            and row[projected_col] < row[current_col]
        ):
            raise ValueError(
                f"{projected_col} cannot be lower than "
                f"the player's current value "
                f"({row[current_col]})."
            )

    # Player appearances cannot exceed league games
    if (
        pd.notna(row["projected_games"])
        and pd.notna(row["full_season_games"])
        and row["projected_games"]
        > row["full_season_games"]
    ):
        raise ValueError(
            "Projected games cannot exceed "
            "full-season league games."
        )

    # Minutes cannot exceed games x 90
    if (
        pd.notna(row["projected_minutes"])
        and pd.notna(row["projected_games"])
        and row["projected_minutes"]
        > row["projected_games"] * 90
    ):
        raise ValueError(
            "Projected minutes cannot exceed "
            "projected games × 90."
        )

    # Clean sheets cannot exceed appearances
    if (
        pd.notna(row["total_clean_sheets"])
        and pd.notna(row["projected_games"])
        and row["total_clean_sheets"]
        > row["projected_games"]
    ):
        raise ValueError(
            "Clean sheets cannot exceed projected games."
        )

    # Points per game must be possible
    if (
        pd.notna(row["avg_points_per_game"])
        and not (
            0 <= row["avg_points_per_game"] <= 3
        )
    ):
        raise ValueError(
            "Average points per game must be between 0 and 3."
        )

    # ----------------------------------------
    # MAP PROJECTION -> MODEL TOTALS
    # ----------------------------------------

    row["total_games_played_season"] = (
        row["projected_games"]
    )

    row["total_minutes_played"] = (
        row["projected_minutes"]
    )

    row["total_goals"] = (
        row["projected_goals"]
    )

    row["total_assists"] = (
        row["projected_assists"]
    )

    row["total_yellow_cards"] = (
        row["projected_yellow_cards"]
    )

    row["total_red_cards"] = (
        row["projected_red_cards"]
    )

    # club_games_played stays fixed:
    # 34 or 38 depending on league
    row["club_games_played"] = (
        row["full_season_games"]
    )

    # ----------------------------------------
    # DERIVED CLEAN-SHEET RATE
    # ----------------------------------------

    if (
        pd.notna(row["total_games_played_season"])
        and row["total_games_played_season"] > 0
        and pd.notna(row["total_clean_sheets"])
    ):
        row["clean_sheet_rate"] = (
            row["total_clean_sheets"]
            / row["total_games_played_season"]
        )
    else:
        row["clean_sheet_rate"] = np.nan

    # ----------------------------------------
    # DERIVED PER-90 FEATURES
    # Historical training rule: >= 900 min
    # ----------------------------------------

    minutes = row["total_minutes_played"]

    if pd.isna(minutes) or minutes < 900:

        row["goals_per_90_min"] = np.nan
        row["assists_per_90_min"] = np.nan
        row["goal_contributions_per_90_min"] = np.nan
        row["yellow_cards_per_90_min"] = np.nan
        row["red_cards_per_90_min"] = np.nan

    else:

        row["goals_per_90_min"] = (
            row["total_goals"]
            * 90
            / minutes
        )

        row["assists_per_90_min"] = (
            row["total_assists"]
            * 90
            / minutes
        )

        row["goal_contributions_per_90_min"] = (
            (
                row["total_goals"]
                + row["total_assists"]
            )
            * 90
            / minutes
        )

        row["yellow_cards_per_90_min"] = (
            row["total_yellow_cards"]
            * 90
            / minutes
        )

        row["red_cards_per_90_min"] = (
            row["total_red_cards"]
            * 90
            / minutes
        )

    # ----------------------------------------
    # TRANSFER FEATURES
    # ----------------------------------------

    transfers = row.get(
        "transfers_during_season",
        np.nan,
    )

    if pd.notna(transfers):

        if transfers < 0:
            raise ValueError(
                "Transfers during season cannot be negative."
            )

        transfers = int(transfers)

        # Any simulated transfer means:
        # player definitely has transfer history.
        if transfers > 0:

            row["has_previous_transfer"] = 1

            base_total = player_row.get(
                "total_previous_transfers",
                np.nan,
            )

            if pd.notna(base_total):
                row["total_previous_transfers"] = (
                    base_total + transfers
                )

            if pd.isna(
                row.get(
                    "days_since_last_transfer",
                    np.nan,
                )
            ):
                raise ValueError(
                    "Specify days since last transfer "
                    "when simulating a transfer."
                )

    return row

def predict_scenario_by_player_id(
    player_id,
    changes=None,
):

    matches = df.loc[_player_matches(player_id)]

    if matches.empty:
        raise ValueError(
            f"Player {player_id} not found."
        )

    player = matches.iloc[0].copy()

    scenario = build_scenario(
        player_row=player,
        changes=changes,
    )

    scenario_df = pd.DataFrame(
        [scenario]
    )

    predicted_value = (
        predict_market_value(
            scenario_df
        )
        .iloc[0]
    )

    return {
        "player_id": player_id,
        "player_key": str(player_id),
        "player": player["player"],
        "team": player["team"],
        "previous_market_value_in_eur": (
            player[
                "previous_market_value_in_eur"
            ]
        ),
        "baseline_projected_market_value_in_eur": (
            player[
                "baseline_projected_market_value_in_eur"
            ]
        ),
        "scenario_projected_market_value_in_eur": (
            round(predicted_value)
        ),
    }

# -------------------------------------------------------------------------
# AI USAGE CITATION
# Tool: ChatGPT (OpenAI, 2026)
# Prompt (summary): Explain a player's production prediction
# with SHAP and map encoded model features back to readable feature names.
# Usage: Used AI assistance for the app's local explanation pipeline.
# -------------------------------------------------------------------------

# ============================================
# SHAP EXPLANATIONS
# ============================================

_SHAP_EXPLAINERS = {}


FEATURE_LABELS = {
    "position": "Position",
    "sub_position": "Playing role",
    "foot": "Preferred foot",
    "competition_id": "League",
    "season": "Season",
    "age_at_valuation": "Age",
    "height_in_cm": "Height",

    "total_games_played_season": "Games played",
    "total_minutes_played": "Minutes played",

    "total_goals": "Goals",
    "goals_per_90_min": "Goals / 90",

    "total_assists": "Assists",
    "assists_per_90_min": "Assists / 90",
    "goal_contributions_per_90_min": "Goal contributions / 90",

    "total_yellow_cards": "Yellow cards",
    "yellow_cards_per_90_min": "Yellow cards / 90",

    "total_red_cards": "Red cards",
    "red_cards_per_90_min": "Red cards / 90",

    "total_clean_sheets": "Clean sheets",
    "clean_sheet_rate": "Clean-sheet rate",

    "clubs_played_for_season": "Clubs played for",

    "club_goals_scored": "Club goals scored",
    "club_goals_conceded": "Club goals conceded",
    "club_games_played": "Club games",
    "avg_points_per_game": "Club points / game",

    "total_previous_transfers": "Previous transfers",
    "transfers_during_season": "Transfers this season",
    "has_previous_transfer": "Transfer history",
    "days_since_last_transfer": "Days since last transfer",

    "log_previous_market_value": "Previous market value",
    "days_since_previous_valuation": "Time since previous valuation",
}

def _get_model_parts(input_df):
    """
    Select correct production pipeline and feature set.
    """

    if len(input_df) != 1:
        raise ValueError(
            "SHAP explanation currently expects one player."
        )

    has_history = (
        input_df.iloc[0][
            "previous_market_value_in_eur"
        ]
        is not None
        and pd.notna(
            input_df.iloc[0][
                "previous_market_value_in_eur"
            ]
        )
    )

    if has_history:
        pipeline = model_with_history
        features = FEATURES_WITH_HISTORY
        route = "with_history"

    else:
        pipeline = model_without_history
        features = FEATURES_WITHOUT_HISTORY
        route = "without_history"

    return pipeline, features, route

def _map_encoded_feature(
    encoded_name,
    original_features,
):
    """
    Map transformed / one-hot encoded feature names
    back to original production feature names.
    """

    clean_name = str(encoded_name)

    # Remove ColumnTransformer prefix:
    # e.g. categorical__position_Attack
    if "__" in clean_name:
        clean_name = clean_name.split("__", 1)[1]

    # Longest names first avoids ambiguous matches
    for feature in sorted(
        original_features,
        key=len,
        reverse=True,
    ):
        if (
            clean_name == feature
            or clean_name.startswith(
                f"{feature}_"
            )
        ):
            return feature

    return clean_name

def explain_prediction(input_df):
    """
    Generate aggregated local SHAP values for
    one model prediction.

    SHAP values are produced in the model's
    log-market-value prediction space.
    """

    pipeline, features, route = (
        _get_model_parts(input_df)
    )

    X = input_df[
        features
    ].copy()

    # Everything except final XGBoost estimator
    transformer = pipeline[:-1]

    # Final fitted estimator
    estimator = pipeline.steps[-1][1]

    X_transformed = transformer.transform(X)

    # SHAP works more reliably with one dense row.
    if hasattr(X_transformed, "toarray"):
        X_transformed = (
            X_transformed.toarray()
        )

    # Get transformed feature names
    try:
        transformed_names = (
            transformer
            .get_feature_names_out()
        )

    except Exception as exc:
        raise ValueError(
            "Could not retrieve transformed "
            "feature names from production pipeline."
        ) from exc

    # Cache one explainer per production model
    if route not in _SHAP_EXPLAINERS:
        _SHAP_EXPLAINERS[route] = (
            shap.TreeExplainer(
                estimator
            )
        )

    explainer = (
        _SHAP_EXPLAINERS[route]
    )

    explanation = explainer(
        X_transformed
    )

    shap_values = np.asarray(
        explanation.values
    )[0]

    # ----------------------------------------
    # MAP ENCODED FEATURES BACK TO ORIGINAL
    # ----------------------------------------

    rows = []

    for encoded_name, shap_value in zip(
        transformed_names,
        shap_values,
    ):

        original_feature = (
            _map_encoded_feature(
                encoded_name,
                features,
            )
        )

        rows.append(
            {
                "feature": original_feature,
                "shap_value": float(
                    shap_value
                ),
            }
        )

    shap_df = pd.DataFrame(rows)

    # One-hot encoded categories belonging to
    # the same original feature are summed.
    shap_df = (
        shap_df
        .groupby(
            "feature",
            as_index=False,
        )
        ["shap_value"]
        .sum()
    )

    shap_df["abs_shap"] = (
        shap_df["shap_value"].abs()
    )

    # Original feature value for display
    shap_df["feature_value"] = (
        shap_df["feature"].map(
            lambda feature:
            input_df.iloc[0].get(
                feature,
                np.nan,
            )
        )
    )

    shap_df["label"] = (
        shap_df["feature"].map(
            lambda feature:
            FEATURE_LABELS.get(
                feature,
                feature,
            )
        )
    )

    shap_df = (
        shap_df
        .sort_values(
            "abs_shap",
            ascending=False,
        )
        .reset_index(drop=True)
    )

    return shap_df


def explain_player_by_id(
    player_id,
    changes=None,
    ):
    """
    Return SHAP explanations for baseline
    and custom scenario.
    """

    matches = df.loc[_player_matches(player_id)]

    if matches.empty:
        raise ValueError(
            f"Player {player_id} not found."
        )

    player = matches.iloc[0].copy()

    # Baseline
    baseline_df = pd.DataFrame(
        [player]
    )

    baseline_explanation = (
        explain_prediction(
            baseline_df
        )
    )

    # Scenario
    scenario = build_scenario(
        player_row=player,
        changes=changes,
    )

    scenario_df = pd.DataFrame(
        [scenario]
    )

    scenario_explanation = (
        explain_prediction(
            scenario_df
        )
    )

    return (
        baseline_explanation,
        scenario_explanation,
    )


def explain_baseline_by_player_id(player_id):
    """Return the baseline SHAP explanation for one player."""
    matches = df.loc[_player_matches(player_id)]

    if matches.empty:
        raise ValueError(f"Player {player_id} not found.")

    baseline_df = pd.DataFrame([matches.iloc[0].copy()])
    return explain_prediction(baseline_df)


def explain_scenario_by_player_id(player_id, changes=None):
    """Return the SHAP explanation for one custom scenario."""
    matches = df.loc[_player_matches(player_id)]

    if matches.empty:
        raise ValueError(f"Player {player_id} not found.")

    player = matches.iloc[0].copy()
    scenario = build_scenario(player_row=player, changes=changes)
    return explain_prediction(pd.DataFrame([scenario]))


