import pandas as pd

from prediction_context import prediction_context


def test_with_history_context_shows_previous_valuation_date():
    context = prediction_context(
        {
            "previous_market_value_in_eur": 10_000_000,
            "valuation_date": "2026-06-03",
        }
    )

    assert context.has_history
    assert context.prediction_basis == "Past valuation + player data"
    assert context.previous_valuation_date == "03 Jun 2026"


def test_no_history_context_does_not_invent_valuation_date():
    context = prediction_context(
        {
            "previous_market_value_in_eur": pd.NA,
            "valuation_date": None,
        }
    )

    assert not context.has_history
    assert context.prediction_basis == "Player data only"
    assert context.previous_valuation_date == "No previous value available"
