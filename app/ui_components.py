"""Reusable presentation helpers for the Streamlit application."""

from __future__ import annotations

from typing import Any

import altair as alt
import pandas as pd
import pycountry
import streamlit as st


COUNTRY_CODE_ALIASES = {
    "England": "GB",
    "Scotland": "GB",
    "Wales": "GB",
    "Northern Ireland": "GB",
    "Kosovo": "XK",
    "DR Congo": "CD",
    "Congo": "CG",
    "Cote d'Ivoire": "CI",
    "Türkiye": "TR",
    "The Gambia": "GM",
    "Southern Sudan": "SS",
    "Chinese Taipei": "TW",
    "Hongkong": "HK",
    "Neukaledonien": "NC",
    "Korea, South": "KR",
    "Korea, North": "KP",
}

POSITION_PITCH_COORDINATES = {
    "Goalkeeper": (8, 34, "GK"),
    "Centre-Back": (24, 34, "CB"),
    "Left-Back": (29, 13, "LB"),
    "Right-Back": (29, 55, "RB"),
    "Defensive Midfield": (42, 34, "DM"),
    "Central Midfield": (53, 34, "CM"),
    "Attacking Midfield": (64, 34, "AM"),
    "Left Midfield": (55, 13, "LM"),
    "Right Midfield": (55, 55, "RM"),
    "Left Winger": (78, 13, "LW"),
    "Right Winger": (78, 55, "RW"),
    "Second Striker": (78, 34, "SS"),
    "Centre-Forward": (89, 34, "CF"),
}

POSITION_FALLBACK_COORDINATES = {
    "Goalkeeper": (8, 34, "GK"),
    "Defender": (27, 34, "DEF"),
    "Midfield": (53, 34, "MID"),
    "Attack": (84, 34, "ATT"),
}


def format_eur(value: Any) -> str:
    """Format an amount in euros for compact display."""
    if pd.isna(value):
        return "N/A"

    amount = float(value)
    if amount >= 1_000_000:
        return f"€{amount / 1_000_000:.1f}M"
    if amount >= 1_000:
        return f"€{amount / 1_000:.0f}K"
    return f"€{amount:,.0f}"


def safe_int(value: Any, default: int = 0) -> int:
    """Convert nullable numeric values to display-safe integers."""
    if pd.isna(value):
        return default
    return int(round(float(value)))


def season_label(season_start: Any) -> str:
    """Return a football season label such as ``2026/27``."""
    year = safe_int(season_start)
    return f"{year}/{str(year + 1)[-2:]}"


def get_country_code(country_name: Any) -> str | None:
    """Resolve Transfermarkt country names to ISO alpha-2 codes."""
    if pd.isna(country_name):
        return None

    normalized_name = str(country_name).strip()
    if normalized_name in COUNTRY_CODE_ALIASES:
        return COUNTRY_CODE_ALIASES[normalized_name]

    try:
        return pycountry.countries.lookup(normalized_name).alpha_2
    except LookupError:
        return None


# -------------------------------------------------------------------------
# AI USAGE CITATION
# Tool: ChatGPT (OpenAI, 2026)
# Prompt (summary): Draw a football pitch in the Streamlit app
# and mark a player's position using Altair.
# Usage: Used AI assistance for the pitch visualization.
# -------------------------------------------------------------------------

def render_position_pitch(
    position: Any,
    sub_position: Any,
    player_name: str,
) -> None:
    """Render a compact tactical pitch with the player's primary position."""
    position_name = "" if pd.isna(position) else str(position)
    sub_position_name = "" if pd.isna(sub_position) else str(sub_position)
    marker_x, marker_y, marker_label = POSITION_PITCH_COORDINATES.get(
        sub_position_name,
        POSITION_FALLBACK_COORDINATES.get(
            position_name,
            (53, 34, "POS"),
        ),
    )

    x_encoding = alt.X(
        "x:Q",
        scale=alt.Scale(domain=[-3, 108]),
        axis=None,
    )
    y_encoding = alt.Y(
        "y:Q",
        scale=alt.Scale(domain=[0, 68], reverse=True),
        axis=None,
    )

    pitch_background = (
        alt.Chart(pd.DataFrame([{"x": 0, "x2": 105, "y": 0, "y2": 68}]))
        .mark_rect(
            color="#12633f",
            stroke="#f5fbf7",
            strokeWidth=2,
            tooltip=False,
        )
        .encode(
            x=x_encoding,
            x2="x2:Q",
            y=y_encoding,
            y2="y2:Q",
        )
    )
    pitch_glow = (
        alt.Chart(pd.DataFrame([{"x": 0, "x2": 105, "y": 0, "y2": 68}]))
        .mark_rect(
            fillOpacity=0,
            stroke="#2deb78",
            strokeWidth=5,
            opacity=0.22,
            tooltip=False,
        )
        .encode(
            x=x_encoding,
            x2="x2:Q",
            y=y_encoding,
            y2="y2:Q",
        )
    )

    pitch_lines = pd.DataFrame(
        [
            {"x": 52.5, "x2": 52.5, "y": 0, "y2": 68},
            {"x": 0, "x2": 16.5, "y": 13.8, "y2": 13.8},
            {"x": 16.5, "x2": 16.5, "y": 13.8, "y2": 54.2},
            {"x": 0, "x2": 16.5, "y": 54.2, "y2": 54.2},
            {"x": 0, "x2": 5.5, "y": 24.8, "y2": 24.8},
            {"x": 5.5, "x2": 5.5, "y": 24.8, "y2": 43.2},
            {"x": 0, "x2": 5.5, "y": 43.2, "y2": 43.2},
            {"x": 88.5, "x2": 105, "y": 13.8, "y2": 13.8},
            {"x": 88.5, "x2": 88.5, "y": 13.8, "y2": 54.2},
            {"x": 88.5, "x2": 105, "y": 54.2, "y2": 54.2},
            {"x": 99.5, "x2": 105, "y": 24.8, "y2": 24.8},
            {"x": 99.5, "x2": 99.5, "y": 24.8, "y2": 43.2},
            {"x": 99.5, "x2": 105, "y": 43.2, "y2": 43.2},
        ]
    )
    markings = (
        alt.Chart(pitch_lines)
        .mark_rule(
            color="#f5fbf7",
            strokeWidth=1.2,
            opacity=0.9,
            tooltip=False,
        )
        .encode(
            x=x_encoding,
            x2="x2:Q",
            y=y_encoding,
            y2="y2:Q",
        )
    )

    pitch_spots = pd.DataFrame(
        [
            {"x": 11, "y": 34, "kind": "spot"},
            {"x": 52.5, "y": 34, "kind": "centre"},
            {"x": 94, "y": 34, "kind": "spot"},
        ]
    )
    spots = (
        alt.Chart(pitch_spots)
        .mark_circle(
            size=18,
            color="#f5fbf7",
            opacity=0.95,
            tooltip=False,
        )
        .encode(x=x_encoding, y=y_encoding)
    )
    centre_circle = (
        alt.Chart(pd.DataFrame([{"x": 52.5, "y": 34}]))
        .mark_circle(
            size=1_250,
            fillOpacity=0,
            stroke="#f5fbf7",
            strokeWidth=1.2,
            opacity=0.9,
            tooltip=False,
        )
        .encode(x=x_encoding, y=y_encoding)
    )

    marker_data = pd.DataFrame(
        [{"x": marker_x, "y": marker_y, "label": marker_label}]
    )
    marker_glow_outer = (
        alt.Chart(marker_data)
        .mark_circle(
            size=1_150,
            color="#2deb78",
            opacity=0.10,
            tooltip=False,
        )
        .encode(x=x_encoding, y=y_encoding)
    )
    marker_glow_inner = (
        alt.Chart(marker_data)
        .mark_circle(
            size=720,
            color="#2deb78",
            opacity=0.24,
            tooltip=False,
        )
        .encode(x=x_encoding, y=y_encoding)
    )
    marker = (
        alt.Chart(marker_data)
        .mark_circle(
            size=390,
            color="#2deb78",
            stroke="#ffffff",
            strokeWidth=2,
            tooltip=False,
        )
        .encode(x=x_encoding, y=y_encoding)
    )
    marker_text = (
        alt.Chart(marker_data)
        .mark_text(
            color="#0b1320",
            fontSize=10,
            fontWeight="bold",
            baseline="middle",
            tooltip=False,
        )
        .encode(x=x_encoding, y=y_encoding, text="label:N")
    )

    pitch = (
        alt.layer(
            pitch_background,
            pitch_glow,
            markings,
            centre_circle,
            spots,
            marker_glow_outer,
            marker_glow_inner,
            marker,
            marker_text,
        )
        .properties(height=132)
        .configure_view(stroke=None)
    )

    st.caption("Primary position", text_alignment="center")
    st.markdown(
        f"**{sub_position_name or position_name or 'Position unavailable'}**",
        text_alignment="center",
    )
    st.altair_chart(
        pitch,
        alt=f"{player_name} primary position: {sub_position_name or position_name}",
        key=f"position_pitch_{player_name}",
    )
    st.caption("Attacking direction →", text_alignment="center")


def render_stat_metric(
    label: str,
    value: Any,
    caption: str,
) -> None:
    """Render one season statistic with native Streamlit elements."""
    with st.container(border=True):
        st.metric(label, value)
        st.caption(caption)


def _ranking_badge_color(rank: Any) -> str:
    """Return a theme-aware color band for a numeric ranking."""
    if pd.isna(rank):
        return "gray"

    numeric_rank = safe_int(rank)
    if numeric_rank <= 3:
        return "green"
    if numeric_rank <= 10:
        return "blue"
    if numeric_rank <= 25:
        return "orange"
    return "gray"


def _format_ranking(rank: Any) -> str:
    """Format a ranking without presenting missing values as rank zero."""
    return "N/A" if pd.isna(rank) else f"#{safe_int(rank)}"


def render_stat_rankings(
    label: str,
    league_rank: Any,
    top_5_league_rank: Any,
) -> None:
    """Render compact, emphasized rankings outside the KPI cards."""
    st.markdown(f"**{label}**")
    with st.container(horizontal=True, gap="small", wrap=True):
        st.badge(
            f"League ranking: {_format_ranking(league_rank)}",
            icon=":material/leaderboard:",
            color=_ranking_badge_color(league_rank),
            help=(
                "Rank among players in the player's domestic league. "
                "Top 3 is green, top 10 blue, and top 25 orange."
            ),
        )
        st.badge(
            f"Top 5 league ranking: {_format_ranking(top_5_league_rank)}",
            icon=":material/public:",
            color=_ranking_badge_color(top_5_league_rank),
            help=(
                "Rank among players across the five major European "
                "leagues in the dataset. Top 3 is green, top 10 blue, "
                "and top 25 orange."
            ),
        )


def render_trajectory_metric(
    label: str,
    current: Any,
    projected: Any,
) -> None:
    """Render current and projected season totals."""
    current_value = safe_int(current)
    projected_value = safe_int(projected)
    difference = projected_value - current_value

    with st.container(border=True):
        st.metric(
            label,
            f"{projected_value:,}",
            delta=f"{difference:+,} from current",
        )
        st.caption(f"Current: {current_value:,}")


def prepare_market_value_chart_data(
    current_value: Any,
    baseline_value: Any,
    scenario_value: Any,
) -> pd.DataFrame:
    """Build chart-ready market values, omitting unavailable valuations."""
    rows = []
    for order, (stage, value) in enumerate(
        (
            ("Current", current_value),
            ("Baseline", baseline_value),
            ("Your scenario", scenario_value),
        )
    ):
        if value is not None and pd.notna(value):
            amount = float(value)
            rows.append(
                {
                    "stage": stage,
                    "value": amount,
                    "display_value": format_eur(amount),
                    "order": order,
                }
            )

    return pd.DataFrame(rows)


# -------------------------------------------------------------------------
# AI USAGE CITATION
# Tool: ChatGPT (OpenAI, 2026)
# Prompt (summary): Display current, baseline, and scenario
# market values in a responsive visual comparison.
# Usage: Used AI assistance for the custom chart and its display states.
# -------------------------------------------------------------------------

def display_market_value_comparison(
    current_value: Any,
    baseline_value: Any,
    scenario_value: Any,
) -> None:
    """Display a responsive horizontal market-value trajectory."""
    chart_data = prepare_market_value_chart_data(
        current_value,
        baseline_value,
        scenario_value,
    )

    values = chart_data["value"].tolist()
    value_min = min(values)
    value_max = max(values)
    spread = value_max - value_min
    if spread == 0:
        spread = max(value_max * 0.2, 1_000_000)

    chart_min = max(0, value_min - spread * 0.25)
    chart_max = value_max + spread * 0.25
    chart_range = max(chart_max - chart_min, 1)

    def marker_position(value: float) -> float:
        normalized = (value - chart_min) / chart_range
        return 7 + normalized * 86

    baseline_amount = float(baseline_value)
    scenario_amount = float(scenario_value)
    baseline_position = marker_position(baseline_amount)
    scenario_position = marker_position(scenario_amount)
    current_available = current_value is not None and pd.notna(current_value)
    current_amount = float(current_value) if current_available else None
    current_position = (
        marker_position(current_amount) if current_amount is not None else None
    )

    scenario_lane = "pmv-label-bottom-far" if (
        current_position is not None
        and abs(scenario_position - current_position) < 16
    ) else "pmv-label-bottom"

    current_marker = ""
    if current_amount is not None and current_position is not None:
        current_marker = f"""
        <div class="pmv-marker pmv-current" style="left:{current_position:.2f}%"></div>
        <div class="pmv-dot pmv-current" style="left:{current_position:.2f}%"></div>
        <div class="pmv-label pmv-label-bottom" style="left:{current_position:.2f}%">
            <span class="pmv-name">Current</span>
            <strong>{format_eur(current_amount)}</strong>
        </div>
        """

    accessible_summary = ", ".join(
        f'{row.stage}: {row.display_value}'
        for row in chart_data.itertuples()
    )

    st.html(
        f"""
        <style>
        .pmv-chart {{
            position: relative;
            min-height: 285px;
            margin: 0.25rem 0 0.5rem;
            overflow: hidden;
        }}
        .pmv-track {{
            position: absolute;
            top: 125px;
            left: 7%;
            right: 7%;
            height: 7px;
            border-radius: 999px;
            background: linear-gradient(90deg, #8f4b4b 0%, #6f745d 50%, #397044 100%);
            box-shadow: inset 0 0 0 1px rgba(128,128,128,.18), 0 2px 8px rgba(0,0,0,.16);
        }}
        .pmv-marker {{
            position: absolute;
            top: 98px;
            width: 3px;
            height: 62px;
            border-radius: 999px;
            transform: translateX(-50%);
        }}
        .pmv-dot {{
            position: absolute;
            top: 118px;
            width: 20px;
            height: 20px;
            border: 4px solid var(--background-color, #fff);
            border-radius: 50%;
            transform: translateX(-50%);
            box-shadow: 0 3px 10px rgba(0,0,0,.28);
        }}
        .pmv-current {{ background: #9aa3b2; }}
        .pmv-baseline {{ background: #4f8ef7; }}
        .pmv-scenario {{ background: #f2b84b; }}
        .pmv-dot.pmv-scenario {{
            top: 115px;
            width: 26px;
            height: 26px;
        }}
        .pmv-label {{
            position: absolute;
            width: min(145px, 28vw);
            transform: translateX(-50%);
            text-align: center;
            line-height: 1.25;
        }}
        .pmv-label-top {{ top: 12px; }}
        .pmv-label-bottom {{ top: 170px; }}
        .pmv-label-bottom-far {{ top: 222px; }}
        .pmv-label strong {{
            display: block;
            margin-top: 3px;
            font-size: clamp(1rem, 2vw, 1.35rem);
            white-space: nowrap;
        }}
        .pmv-label.pmv-scenario-label strong {{
            font-size: clamp(1.1rem, 2.2vw, 1.55rem);
        }}
        .pmv-name {{
            display: block;
            font-size: .7rem;
            font-weight: 700;
            letter-spacing: .07em;
            opacity: .68;
            text-transform: uppercase;
            white-space: nowrap;
        }}
        .pmv-baseline-text {{ color: #4f8ef7; opacity: 1; }}
        .pmv-scenario-text {{ color: #d89b24; opacity: 1; }}
        .pmv-range {{
            position: absolute;
            top: 145px;
            font-size: .68rem;
            opacity: .5;
        }}
        .pmv-range-left {{ left: 7%; }}
        .pmv-range-right {{ right: 7%; text-align: right; }}
        @media (max-width: 640px) {{
            .pmv-chart {{ min-height: 310px; }}
            .pmv-label {{ width: 110px; }}
            .pmv-label-bottom-far {{ top: 232px; }}
        }}
        </style>

        <div class="pmv-chart" role="img" aria-label="Market value comparison. {accessible_summary}">
            <div class="pmv-track"></div>
            {current_marker}

            <div class="pmv-marker pmv-baseline" style="left:{baseline_position:.2f}%"></div>
            <div class="pmv-dot pmv-baseline" style="left:{baseline_position:.2f}%"></div>
            <div class="pmv-label pmv-label-top" style="left:{baseline_position:.2f}%">
                <span class="pmv-name pmv-baseline-text">Baseline</span>
                <strong>{format_eur(baseline_amount)}</strong>
            </div>

            <div class="pmv-marker pmv-scenario" style="left:{scenario_position:.2f}%"></div>
            <div class="pmv-dot pmv-scenario" style="left:{scenario_position:.2f}%"></div>
            <div class="pmv-label {scenario_lane} pmv-scenario-label" style="left:{scenario_position:.2f}%">
                <span class="pmv-name pmv-scenario-text">Your scenario</span>
                <strong>{format_eur(scenario_amount)}</strong>
            </div>

            <span class="pmv-range pmv-range-left">{format_eur(chart_min)}</span>
            <span class="pmv-range pmv-range-right">{format_eur(chart_max)}</span>
        </div>
        """
    )

    if not current_available:
        st.caption(
            "No previous market valuation is available for this player. "
            "The fallback no-history model is used, so only baseline and scenario estimates are compared."
        )
        return

    baseline_change = (
        (baseline_amount - current_amount) / current_amount * 100
        if current_amount > 0
        else 0
    )
    scenario_change = (
        (scenario_amount - baseline_amount) / baseline_amount * 100
        if baseline_amount > 0
        else 0
    )
    st.caption(
        f"Baseline: {baseline_change:+.1f}% versus current · "
        f"Scenario: {scenario_change:+.1f}% versus baseline"
    )


def _shorten_driver_label(label: Any, max_length: int = 25) -> str:
    """Keep driver labels compact while preserving their full tooltip text."""
    text = str(label)
    if len(text) <= max_length:
        return text
    return f"{text[: max_length - 1].rstrip()}…"


def _format_feature_value(value: Any) -> str:
    """Format a SHAP feature value for a concise hover tooltip."""
    if value is None or pd.isna(value):
        return "Unavailable"
    if isinstance(value, (float, int)):
        return f"{value:,.2f}"
    return str(value)


# -------------------------------------------------------------------------
# AI USAGE CITATION
# Tool: ChatGPT (OpenAI, 2026)
# Prompt (summary): Show the strongest positive and negative
# SHAP drivers in compact and detailed Streamlit charts.
# Usage: Used AI assistance for driver selection and chart presentation.
# -------------------------------------------------------------------------

def _top_shap_drivers(shap_df: pd.DataFrame, top_n: int) -> pd.DataFrame:
    return (
        shap_df.nlargest(top_n, "abs_shap")
        .sort_values("shap_value")
        .assign(
            direction=lambda frame: frame["shap_value"].map(
                lambda value: "Pushes higher" if value >= 0 else "Pushes lower"
            ),
            display_label=lambda frame: frame["label"].map(
                _shorten_driver_label
            ),
        )
    )


def _shap_chart(shap_df: pd.DataFrame, top_n: int, height: int) -> alt.Chart:
    top = _top_shap_drivers(shap_df, top_n)

    return (
        alt.Chart(top)
        .mark_bar(cornerRadiusEnd=4)
        .encode(
            x=alt.X("shap_value:Q", title="Contribution in log-value space"),
            y=alt.Y("display_label:N", title=None, sort=None),
            color=alt.Color(
                "direction:N",
                title=None,
                scale=alt.Scale(
                    domain=["Pushes lower", "Pushes higher"],
                    range=["#EF5350", "#4CAF50"],
                ),
            ),
            tooltip=[
                alt.Tooltip("label:N", title="Feature"),
                alt.Tooltip("feature_value:N", title="Value"),
                alt.Tooltip("shap_value:Q", title="SHAP contribution", format=".3f"),
            ],
        )
        .properties(height=height)
    )


def display_compact_shap_drivers(
    shap_df: pd.DataFrame,
    top_n: int = 5,
) -> None:
    """Display the strongest local SHAP drivers."""
    if shap_df.empty:
        st.caption("No SHAP drivers available.")
        return

    top = _top_shap_drivers(shap_df, top_n).sort_values(
        "abs_shap",
        ascending=False,
    )
    with st.container(horizontal=True, wrap=True, gap="small"):
        for row in top.itertuples():
            positive = row.shap_value >= 0
            st.badge(
                _shorten_driver_label(row.label, max_length=21),
                icon=(
                    ":material/arrow_upward:"
                    if positive
                    else ":material/arrow_downward:"
                ),
                color="green" if positive else "red",
                help=(
                    f"**{row.label}**\n\n"
                    f"Feature value: `{_format_feature_value(row.feature_value)}`  \n"
                    f"Direction: **{row.direction.lower()}**  \n"
                    f"SHAP contribution: `{row.shap_value:+.3f}`"
                ),
            )

    st.caption("Hover over a driver tag or bar to see its full details.")

    st.altair_chart(
        _shap_chart(shap_df, top_n=top_n, height=220),
        width="stretch",
        alt="Horizontal bar chart of the strongest factors affecting the scenario valuation.",
    )


def display_shap_drivers(
    shap_df: pd.DataFrame,
    top_n: int = 10,
) -> None:
    """Display a detailed signed SHAP contribution chart."""
    if shap_df.empty:
        st.caption("No SHAP drivers available.")
        return

    st.altair_chart(
        _shap_chart(shap_df, top_n=top_n, height=360),
        width="stretch",
        alt="Horizontal bar chart showing positive and negative model contributions.",
    )
