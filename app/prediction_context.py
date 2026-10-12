# -------------------------------------------------------------------------
# AI USAGE CITATION
# Tool: ChatGPT (OpenAI, 2026)
# Prompt (summary): Show whether a player's prediction uses a
# previous market value and format the available valuation date for display.
# Usage: Used AI assistance for the prediction-context helper.
# -------------------------------------------------------------------------

"""Human-readable context for a player's production prediction."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

import pandas as pd


@dataclass(frozen=True)
class PredictionContext:
    previous_valuation_date: str
    prediction_basis: str
    has_history: bool


def prediction_context(player: Mapping[str, Any]) -> PredictionContext:
    """Describe whether the estimate uses a prior recorded market value."""
    has_history = pd.notna(player["previous_market_value_in_eur"])

    valuation_date = pd.to_datetime(
        player.get("valuation_date"), errors="coerce"
    )
    date_label = (
        valuation_date.strftime("%d %b %Y")
        if has_history and pd.notna(valuation_date)
        else "No previous value available"
        if not has_history
        else "Date unavailable"
    )

    return PredictionContext(
        previous_valuation_date=date_label,
        prediction_basis=(
            "Past valuation + player data"
            if has_history
            else "Player data only"
        ),
        has_history=has_history,
    )
