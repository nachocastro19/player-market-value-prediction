from ui_components import (
    _ranking_badge_color,
    format_eur,
    prepare_market_value_chart_data,
    season_label,
)


def test_market_value_chart_omits_missing_current_value():
    chart_data = prepare_market_value_chart_data(
        current_value=None,
        baseline_value=1_000_000,
        scenario_value=1_250_000,
    )

    assert chart_data["stage"].tolist() == ["Baseline", "Your scenario"]
    assert chart_data["display_value"].tolist() == ["€1.0M", "€1.2M"]


def test_display_helpers_derive_labels():
    assert season_label(2026) == "2026/27"
    assert format_eur(None) == "N/A"
    assert format_eur(750_000) == "€750K"


def test_ranking_badge_color_bands():
    assert _ranking_badge_color(3) == "green"
    assert _ranking_badge_color(10) == "blue"
    assert _ranking_badge_color(25) == "orange"
    assert _ranking_badge_color(26) == "gray"
