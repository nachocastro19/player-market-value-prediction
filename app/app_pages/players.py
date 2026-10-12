# -------------------------------------------------------------------------
# AI USAGE CITATION
# Tool: ChatGPT (OpenAI, 2026)
# Prompt (summary): Build a Streamlit player-discovery page with
# branded visuals, player coverage metrics, and reusable badge images.
# Usage: Used AI assistance for the page layout and image handling.
# -------------------------------------------------------------------------

from __future__ import annotations

import base64
from io import BytesIO

import pandas as pd
import streamlit as st
from PIL import Image

from app_config import (
    BRAND_WORDMARK,
    CURRENT_SEASON_DATA_REFRESH_DATE,
    LEAGUE_BADGES,
    TEAM_BADGES,
)
from player_comparison import build_comparison_table, format_vertical_comparison
from player_data import (
    LEAGUE_LABELS,
    build_players_dataframe,
    normalize_search_text,
    selectable_players,
)


with st.spinner("Loading player data and predictions…", show_time=True):
    from prediction_engine import df as inference_df


@st.cache_data(max_entries=256, show_spinner=False)
def badge_data_url(image_path: str, size: int = 36) -> str | None:
    """Return a compact, consistently sized badge for filters and tables."""
    if not image_path:
        return None

    try:
        with Image.open(image_path) as source:
            badge = source.convert("RGBA")
            badge.thumbnail((size, size), Image.Resampling.LANCZOS)
            canvas = Image.new("RGBA", (size, size), (255, 255, 255, 0))
            offset = (
                (size - badge.width) // 2,
                (size - badge.height) // 2,
            )
            canvas.alpha_composite(badge, offset)

            buffer = BytesIO()
            canvas.save(buffer, format="WEBP", quality=90, method=6)
    except (OSError, ValueError):
        return None

    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/webp;base64,{encoded}"


def clear_club_filter() -> None:
    st.session_state["discovery_clubs"] = []


def clear_filters() -> None:
    st.session_state["discovery_search"] = ""
    st.session_state["discovery_leagues"] = []
    st.session_state["discovery_clubs"] = []
    st.session_state["discovery_positions"] = []


players_df = selectable_players(build_players_dataframe(inference_df))
league_badge_urls = {
    league: badge_data_url(str(badge_path))
    for league, badge_path in LEAGUE_BADGES.items()
}
league_filter_labels = {
    league: (
        f"![{LEAGUE_LABELS[league]} logo]({league_badge_urls[league]}) "
        f"{LEAGUE_LABELS[league]}"
    )
    for league in LEAGUE_LABELS
}

with st.container(horizontal_alignment="center", gap="small"):
    wordmark_svg = BRAND_WORDMARK.read_text(encoding="utf-8")
    if st.context.theme.type != "dark":
        wordmark_svg = (
            wordmark_svg.replace("rgb(255,255,255)", "#0B1320")
            .replace("rgb(199,206,216)", "#667085")
            .replace("rgb(200,210,217)", "#667085")
        )
    st.image(
        wordmark_svg,
        width=340,
        alt="TransferLens - Football Value Intelligence",
    )
    st.badge(
        "2026/27 season",
        icon=":material/calendar_month:",
        color="blue",
    )
    st.title(
        "See what drives player value",
        text_alignment="center",
    )
    st.markdown(
        "Explore player performance, projected market values, and comparable "
        "profiles across Europe’s top five leagues.",
        text_alignment="center",
    )
    st.caption(
        "Data refreshed "
        f"{CURRENT_SEASON_DATA_REFRESH_DATE.day} "
        f"{CURRENT_SEASON_DATA_REFRESH_DATE:%B %Y}"
    )

coverage_columns = st.columns(4)
coverage_columns[0].metric(
    "Players",
    f"{len(players_df):,}",
    icon=":material/groups:",
    border=True,
)
coverage_columns[1].metric(
    "Clubs",
    f'{players_df["team"].nunique():,}',
    icon=":material/shield:",
    border=True,
)
coverage_columns[2].metric(
    "Leagues",
    f'{players_df["league"].nunique():,}',
    icon=":material/public:",
    border=True,
)
coverage_columns[3].metric(
    "Projection horizon",
    "June 2027",
    icon=":material/event_upcoming:",
    border=True,
)

# -------------------------------------------------------------------------
# AI USAGE CITATION
# Tool: ChatGPT (OpenAI, 2026)
# Prompt (summary): Add searchable league, club, and position
# filters and a player table to the Streamlit discovery page.
# Usage: Used AI assistance for interactive filters and table presentation.
# -------------------------------------------------------------------------

st.subheader("Explore players", icon=":material/manage_search:")
with st.container(border=True):
    search_col, club_col = st.columns([1.15, 1], vertical_alignment="bottom")
    with search_col:
        player_search = st.text_input(
            "Search player",
            type="search",
            placeholder="Search by player name…",
            icon=":material/search:",
            live="300ms",
            key="discovery_search",
            persist_state="session",
        )

    league_col, position_col = st.columns([1.25, 1])
    with league_col:
        league_options = list(LEAGUE_LABELS)
        selected_leagues = st.pills(
            "League",
            options=league_options,
            format_func=league_filter_labels.__getitem__,
            selection_mode="multi",
            key="discovery_leagues",
            on_change=clear_club_filter,
            persist_state="session",
            width="stretch",
        )

    club_source = players_df
    if selected_leagues:
        club_source = club_source.loc[
            club_source["league"].isin(selected_leagues)
        ]
    club_options = sorted(club_source["team"].dropna().unique().tolist())

    with club_col:
        selected_clubs = st.multiselect(
            "Club",
            options=club_options,
            placeholder="All clubs",
            key="discovery_clubs",
            persist_state="session",
        )

    with position_col:
        position_options = sorted(
            players_df["position"].dropna().unique().tolist()
        )
        selected_positions = st.pills(
            "Position",
            options=position_options,
            selection_mode="multi",
            key="discovery_positions",
            persist_state="session",
            width="stretch",
        )

    st.button(
        "Clear filters",
        icon=":material/filter_alt_off:",
        type="tertiary",
        on_click=clear_filters,
    )

filtered = players_df
if player_search:
    normalized_search = normalize_search_text(player_search).strip()
    filtered = filtered.loc[
        filtered["player"]
        .map(normalize_search_text)
        .str.contains(normalized_search, regex=False, na=False)
    ]
if selected_leagues:
    filtered = filtered.loc[filtered["league"].isin(selected_leagues)]
if selected_clubs:
    filtered = filtered.loc[filtered["team"].isin(selected_clubs)]
if selected_positions:
    filtered = filtered.loc[filtered["position"].isin(selected_positions)]

filtered = filtered.sort_values(
    ["league", "team", "baseline_projected_market_value_in_eur", "player"],
    ascending=[True, True, False, True],
    na_position="last",
).reset_index(drop=True)

st.caption(f"**{len(filtered):,} players** match the current filters.")

if filtered.empty:
    st.info(
        "No players match these filters. Broaden the search or remove a filter.",
        icon=":material/search_off:",
    )
else:
    visible_clubs = set(zip(filtered["league"], filtered["team"]))
    club_badge_urls = {
        key: badge_data_url(str(badge_path))
        for key, badge_path in TEAM_BADGES.items()
        if key in visible_clubs
    }
    table_df = pd.DataFrame(
        {
            "player": [
                (
                    f"player?player={player_key}"
                    f"#{player_name}"
                )
                for player_key, player_name in zip(
                    filtered["player_key"], filtered["player"]
                )
            ],
            "club_badge": [
                club_badge_urls.get((league, club))
                for league, club in zip(filtered["league"], filtered["team"])
            ],
            "club": filtered["team"],
            "league_badge": filtered["league"].map(league_badge_urls),
            "league": (
                filtered["league"]
                .map(LEAGUE_LABELS)
                .fillna(filtered["league"])
            ),
            "position": filtered["position"],
            "age": filtered["age_at_valuation"],
            "games": filtered["current_games"],
            "minutes": filtered["current_minutes"],
            "goals": filtered["current_goals"],
            "assists": filtered["current_assists"],
            "current_value_m": (
                filtered["previous_market_value_in_eur"] / 1_000_000
            ),
            "projected_value_m": (
                filtered["baseline_projected_market_value_in_eur"] / 1_000_000
            ),
            "projected_change_m": (
                filtered["baseline_projected_market_value_in_eur"]
                - filtered["previous_market_value_in_eur"]
            )
            / 1_000_000,
        }
    )

    st.dataframe(
        table_df,
        hide_index=True,
        height=640,
        row_height=46,
        lazy=True,
        key="players_table",
        alt=(
            f"Table of {len(filtered)} football players matching the selected filters, "
            "including current statistics and projected market values."
        ),
        column_config={
            "player": st.column_config.LinkColumn(
                "Player",
                help="Open the player deep dive",
                display_text=r".*#(.*)$",
                pinned=True,
                width=180,
                alignment="left",
            ),
            "club_badge": st.column_config.ImageColumn(
                "",
                width=46,
                help="Club badge",
            ),
            "club": st.column_config.TextColumn("Club", width=150),
            "league_badge": st.column_config.ImageColumn(
                "",
                width=46,
                help="League logo",
            ),
            "league": st.column_config.TextColumn("League", width=130),
            "position": st.column_config.TextColumn(
                "Position", width=90, alignment="center"
            ),
            "age": st.column_config.NumberColumn(
                "Age", format="%d", width=64, alignment="center"
            ),
            "games": st.column_config.NumberColumn(
                "Games", format="%d", width=72, alignment="center"
            ),
            "minutes": st.column_config.NumberColumn(
                "Minutes", format="localized", width=86, alignment="center"
            ),
            "goals": st.column_config.NumberColumn(
                "Goals", format="%d", width=68, alignment="center"
            ),
            "assists": st.column_config.NumberColumn(
                "Assists", format="%d", width=72, alignment="center"
            ),
            "current_value_m": st.column_config.NumberColumn(
                "Current value",
                help="Latest recorded market value, shown in millions of euros",
                format="€ %.1fM",
                width=124,
            ),
            "projected_value_m": st.column_config.NumberColumn(
                "Projected value",
                help=(
                    "Model projection for the end of the current season, "
                    "shown in millions of euros"
                ),
                format="€ %.1fM",
                width=132,
            ),
            "projected_change_m": st.column_config.NumberColumn(
                "Projected change",
                help=(
                    "Projected value minus current market value, shown in "
                    "millions of euros"
                ),
                format="€ %+.1fM",
                width=140,
            ),
        },
    )

st.space("medium")
# -------------------------------------------------------------------------
# AI USAGE CITATION
# Tool: ChatGPT (OpenAI, 2026)
# Prompt (summary): Let users search for and compare two or three
# players side by side without changing the discovery filters.
# Usage: Used AI assistance for the comparison controls and display.
# -------------------------------------------------------------------------

st.subheader("Compare players", icon=":material/compare_arrows:")
with st.container(border=True):
    st.caption(
        "Search all tracked players; discovery filters do not limit comparisons."
    )
    comparison_options = players_df.sort_values(
        ["player", "team", "player_key"]
    )
    comparison_labels = {
        row.player_id: f"{row.player} · {row.team} · {row.position}"
        for row in comparison_options.itertuples(index=False)
    }
    comparison_labels = {
        row["player_key"]: f"{row['player']} · {row['team']} · {row['position']}"
        for _, row in comparison_options.iterrows()
    }
    comparison_search = st.text_input(
        "Search players to compare",
        type="search",
        placeholder="Search by player name or club (accents optional)",
        icon=":material/search:",
        live="300ms",
        key="compare_player_search",
        persist_state="session",
    )
    selected_comparison_keys = st.session_state.get("compare_player_keys", [])
    if comparison_search:
        normalized_search = normalize_search_text(comparison_search).strip()
        matching_keys = comparison_options.loc[
            comparison_options.apply(
                lambda row: normalized_search
                in normalize_search_text(
                    f'{row["player"]} {row["team"]} {row["position"]}'
                ),
                axis=1,
            ),
            "player_key",
        ].tolist()
        comparison_option_keys = list(
            dict.fromkeys([*matching_keys, *selected_comparison_keys])
        )
    else:
        comparison_option_keys = comparison_options["player_key"].tolist()
    compared_player_keys = st.multiselect(
        "Choose two or three players",
        options=comparison_option_keys,
        format_func=comparison_labels.__getitem__,
        max_selections=3,
        placeholder="Search players by name or club…",
        filter_mode="contains",
        select_all=False,
        key="compare_player_keys",
        persist_state="session",
    )
    if len(compared_player_keys) < 2:
        st.caption("Select two or three players to see them side by side.")
    else:
        compared_players = (
            players_df.set_index("player_key")
            .loc[compared_player_keys]
            .reset_index()
        )
        comparison_table, comparison_note = build_comparison_table(compared_players)
        st.table(
            format_vertical_comparison(comparison_table),
            hide_index=True,
            border="horizontal",
            alt=(
                "Side-by-side comparison of selected players' photos, clubs, "
                "leagues, values and season statistics"
            ),
        )
        st.caption(comparison_note)

