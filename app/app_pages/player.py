# -------------------------------------------------------------------------
# AI USAGE CITATION
# Tool: ChatGPT (OpenAI, 2026)
# Prompt (summary): Build a Streamlit player-detail page with
# player routing, profile data, valuation context, and cached explanations.
# Usage: Used AI assistance for the page structure and state handling.
# -------------------------------------------------------------------------

import pandas as pd
import streamlit as st

from app_config import LEAGUE_BADGES, TEAM_BADGES
from player_data import (
    LEAGUE_LABELS,
    build_players_dataframe,
    normalize_search_text,
    resolve_player_key,
    selectable_players,
    serialize_player_key,
)
from prediction_context import prediction_context
from player_comparison import find_similar_players
from ui_components import (
    display_compact_shap_drivers,
    display_market_value_comparison,
    display_shap_drivers,
    format_eur,
    get_country_code,
    render_stat_metric,
    render_stat_rankings,
    render_position_pitch,
    render_trajectory_metric,
    safe_int,
    season_label,
)

with st.spinner("Loading player data and prediction models…", show_time=True):
    from prediction_engine import (
        df as inference_df,
        explain_baseline_by_player_id,
        explain_scenario_by_player_id,
        predict_scenario_by_player_id,
    )


@st.cache_data(max_entries=2_000, show_spinner=False)
def get_baseline_explanation(player_id):
    """Cache the player-specific explanation that never changes by scenario."""
    return explain_baseline_by_player_id(player_id)


@st.cache_data(max_entries=512, show_spinner=False)
def get_scenario_explanation(player_id, changes_items):
    """Cache bounded scenario explanations using a hashable changes tuple."""
    return explain_scenario_by_player_id(
        player_id,
        changes=dict(changes_items),
    )


# Keep the engine's cached source dataframe immutable from the UI's perspective.
players_df = build_players_dataframe(inference_df)
players_df = selectable_players(players_df)
player_options = players_df.sort_values("player")
player_labels = {
    row["player_key"]: f'{row["player"]} — {row["team"]}'
    for _, row in player_options.iterrows()
}
player_keys = player_options["player_key"].tolist()

raw_player_id = st.query_params.get("player")
routed_player_key = resolve_player_key(raw_player_id, player_keys)
route_state_key = "deep_dive_synced_route"

if raw_player_id != st.session_state.get(route_state_key):
    st.session_state["deep_dive_player"] = routed_player_key
    st.session_state["deep_dive_search"] = ""
    st.session_state[route_state_key] = raw_player_id

st.title("Player deep dive", icon=":material/person_search:")
st.caption(
    "Review a player's current profile, end-of-season projection, custom scenarios, and model drivers."
)

player_search = st.text_input(
    "Search player",
    type="search",
    placeholder="Search by player name or club (accents optional)",
    icon=":material/search:",
    live="300ms",
    key="deep_dive_search",
    persist_state="page",
)
normalized_search = normalize_search_text(player_search).strip()
filtered_player_keys = [
    player_key
    for player_key in player_keys
    if normalized_search
    in normalize_search_text(player_labels[player_key])
]
current_selection = st.session_state.get("deep_dive_player")
if current_selection is not None and current_selection not in filtered_player_keys:
    st.session_state.pop("deep_dive_player", None)

selected_player_key = st.selectbox(
    "Choose player",
    options=filtered_player_keys,
    index=(
        filtered_player_keys.index(routed_player_key)
        if routed_player_key in filtered_player_keys
        else None
    ),
    format_func=player_labels.__getitem__,
    placeholder="Search by player name or club…",
    key="deep_dive_player",
    persist_state="page",
)

if selected_player_key is None:
    if raw_player_id is not None:
        st.warning(
            "That player link is not available in the current dataset.",
            icon=":material/link_off:",
        )
    st.info(
        "Choose a player above, or use Player discovery to filter and compare the full dataset.",
        icon=":material/person_search:",
    )
    if st.button(
        "Browse all players",
        icon=":material/groups:",
        type="primary",
    ):
        st.switch_page("app_pages/players.py")

    st.stop()

selected_player_url_id = str(selected_player_key)
if raw_player_id != selected_player_url_id:
    st.query_params["player"] = selected_player_url_id
    st.session_state[route_state_key] = selected_player_url_id

player = (
    players_df.loc[
        players_df["player_key"].eq(selected_player_key)
    ]
    .iloc[0]
    .copy()
)
context = prediction_context(player)
display_season = season_label(player["season"])
projection_year = safe_int(player["season"]) + 1


player_key = str(selected_player_key).replace(".", "_")
baseline_defaults = {
    "games": safe_int(player["projected_games"]),
    "minutes": safe_int(player["projected_minutes"]),
    "goals": safe_int(player["projected_goals"]),
    "assists": safe_int(player["projected_assists"]),
    "yellow_cards": safe_int(player["projected_yellow_cards"]),
    "red_cards": safe_int(player["projected_red_cards"]),
    "clean_sheets": safe_int(player["total_clean_sheets"]),
    "club_goals_scored": safe_int(player["club_goals_scored"]),
    "club_goals_conceded": safe_int(player["club_goals_conceded"]),
    "avg_points_per_game": (
        float(player["avg_points_per_game"])
        if pd.notna(player["avg_points_per_game"])
        else 0.0
    ),
    "clubs_played": safe_int(
        player["clubs_played_for_season"],
        default=1,
    ),
}

# -------------------------------------------------------------------------
# AI USAGE CITATION
# Tool: ChatGPT (OpenAI, 2026)
# Prompt (summary): Keep scenario inputs and results separate
# for each player and restore baseline values when the user resets the form.
# Usage: Used AI assistance for Streamlit scenario session state.
# -------------------------------------------------------------------------

scenario_state_key = f"{player_key}_submitted_scenario"
scenario_result_key = f"{player_key}_scenario_result"
driver_view_key = f"{player_key}_driver_view"
st.session_state.setdefault(scenario_state_key, None)
st.session_state.setdefault(scenario_result_key, None)


def reset_scenario():
    for field, value in baseline_defaults.items():
        st.session_state[f"{player_key}_{field}"] = value

    st.session_state[f"{player_key}_transfer_enabled"] = False
    st.session_state[f"{player_key}_transfers_during"] = 1
    st.session_state[f"{player_key}_days_since_transfer"] = 90
    st.session_state[scenario_state_key] = None
    st.session_state[scenario_result_key] = None
    st.session_state[driver_view_key] = "Baseline projection"


submitted_changes = st.session_state[scenario_state_key]

nationality = player["country_of_citizenship"]
country_code = get_country_code(nationality)
has_nationality = pd.notna(nationality) and bool(str(nationality).strip())
has_player_photo = (
    pd.notna(player["image_url"])
    and bool(str(player["image_url"]).strip())
)
age_value = (
    safe_int(player["age_at_valuation"])
    if pd.notna(player["age_at_valuation"])
    else "Unavailable"
)
latest_value_label = (
    format_eur(player["previous_market_value_in_eur"])
    if pd.notna(player["previous_market_value_in_eur"])
    else "Not recorded"
)
league_badge = LEAGUE_BADGES.get(player["league"])
team_badge = TEAM_BADGES.get((player["league"], player["team"]))
league_name = LEAGUE_LABELS.get(player["league"], player["league"])

with st.container(border=True):
    profile_col, valuation_col, pitch_col = st.columns(
        [3.7, 3.25, 1.55],
        vertical_alignment="center",
        gap="large",
    )
    with profile_col:
        photo_col, identity_col = st.columns(
            [0.9, 2.8],
            vertical_alignment="top",
            gap="medium",
        )
        with photo_col:
            if has_player_photo:
                st.image(
                    player["image_url"],
                    width=120,
                    alt=f'{player["player"]} profile photo',
                )
            else:
                initials = "".join(
                    part[0]
                    for part in str(player["player"]).split()[:2]
                    if part
                ).upper()
                with st.container(border=True):
                    st.markdown(f"## {initials or '—'}")
                    st.caption("Photo unavailable")
        with identity_col:
            st.subheader(player["player"])
            with st.container(
                horizontal=True,
                vertical_alignment="center",
                gap="small",
                wrap=False,
            ):
                if team_badge is not None and team_badge.exists():
                    st.image(
                        str(team_badge),
                        width=40,
                        alt=f'{player["team"]} club badge',
                    )
                st.markdown(
                    f'**{player["team"]}**',
                    width="content",
                    wrap=False,
                )
            if has_nationality:
                with st.container(
                    horizontal=True,
                    vertical_alignment="center",
                    gap="small",
                    wrap=False,
                ):
                    if country_code:
                        st.image(
                            f"https://flagcdn.com/w80/{country_code.lower()}.png",
                            width=40,
                            alt=f"Flag of {nationality}",
                        )
                    st.markdown(
                        f"**{nationality}**",
                        width="content",
                        wrap=False,
                    )
            else:
                st.caption("Nationality unavailable")
            with st.container(
                horizontal=True,
                vertical_alignment="center",
                gap="small",
                wrap=False,
            ):
                if league_badge is not None and league_badge.exists():
                    st.image(
                        str(league_badge),
                        width=40,
                        alt=f"{league_name} badge",
                    )
                st.markdown(
                    f"**{league_name}** · {player['position']}",
                    width="content",
                    wrap=False,
                )
    with valuation_col:
        with st.container(
            horizontal=True,
            horizontal_alignment="center",
            vertical_alignment="center",
            gap="medium",
            wrap=True,
        ):
            st.metric(
                "Latest market value",
                latest_value_label,
                width="content",
            )
            st.metric(
                f"Projected June {projection_year}",
                format_eur(
                    player["baseline_projected_market_value_in_eur"]
                ),
                width="content",
            )
            st.metric(
                "Age",
                age_value,
                width="content",
            )
    with pitch_col:
        render_position_pitch(
            position=player["position"],
            sub_position=player["sub_position"],
            player_name=player["player"],
        )

with st.container(border=True):
    st.markdown("**About this estimate**")
    valuation_date_col, basis_col = st.columns([1, 2], gap="medium")
    with valuation_date_col:
        st.caption("Date of last recorded value")
        st.markdown(f"**{context.previous_valuation_date}**")
    with basis_col:
        st.caption("What this estimate uses")
        st.badge(
            context.prediction_basis,
            color="blue",
        )
    basis_explanation = (
        "This estimate uses the previous market value alongside player, "
        "performance, and club data."
        if context.has_history
        else "No previous market value is available, so this estimate uses "
        "player, performance, and club data."
    )
    st.caption(basis_explanation)


overview_tab, scenario_tab, drivers_tab = st.tabs(
    ["Overview", "Scenario builder", "Model drivers"],
    key="main_view",
    on_change="rerun",
)


if overview_tab.open:
    with overview_tab:
        st.subheader(f"{display_season} season so far")
        games_col, minutes_col, goals_col, assists_col = st.columns(4)

        with games_col:
            render_stat_metric(
                "Games",
                safe_int(player["current_games"]),
                "Appearances this season",
            )
        with minutes_col:
            render_stat_metric(
                "Minutes",
                f'{safe_int(player["current_minutes"]):,}',
                "Minutes played",
            )
        with goals_col:
            render_stat_metric(
                "Goals",
                safe_int(player["current_goals"]),
                "Goals scored this season",
            )
        with assists_col:
            render_stat_metric(
                "Assists",
                safe_int(player["current_assists"]),
                "Assists this season",
            )

        with st.container(border=True):
            st.markdown("#### League rankings")
            st.caption(
                "Current goal and assist rankings in the domestic league "
                "and across the five major European leagues."
            )
            goals_rank_col, assists_rank_col = st.columns(2)
            with goals_rank_col:
                render_stat_rankings(
                    "Goals",
                    player["goals_league_rank"],
                    player["goals_top5_rank"],
                )
            with assists_rank_col:
                render_stat_rankings(
                    "Assists",
                    player["assists_league_rank"],
                    player["assists_top5_rank"],
                )

        st.subheader("Season trajectory")
        season_progress = (
            player["current_club_games_played"] / player["full_season_games"]
            if player["full_season_games"] > 0
            else 0
        )
        st.caption(
            f"{season_progress:.0%} of the league season played · "
            f"Baseline projection to the end of {display_season} based on current performance"
        )

        trajectory_columns = st.columns(4)
        trajectory_specs = (
            ("Games", "current_games", "projected_games"),
            ("Minutes", "current_minutes", "projected_minutes"),
            ("Goals", "current_goals", "projected_goals"),
            ("Assists", "current_assists", "projected_assists"),
        )
        for column, (label, current_field, projected_field) in zip(
            trajectory_columns,
            trajectory_specs,
        ):
            with column:
                render_trajectory_metric(
                    label,
                    player[current_field],
                    player[projected_field],
                )

        st.divider()
        st.subheader("Similar players")
        st.caption(
            "Closest profiles in the same position group and playing role, "
            "based on age, playing time, and current-season output. Market "
            "value is not used to find matches."
        )
        similar_players = find_similar_players(
            players_df,
            selected_player_key,
            top_n=3,
        )

        if similar_players.empty:
            st.info("There are not enough comparable profiles for this player yet.")
        else:
            peer_columns = st.columns(len(similar_players))
            for peer_column, (_, peer) in zip(
                peer_columns,
                similar_players.iterrows(),
            ):
                with peer_column:
                    with st.container(border=True):
                        image_url = peer.get("image_url")
                        if isinstance(image_url, str) and image_url.strip():
                            st.image(
                                image_url,
                                width=80,
                                alt=f'{peer["player"]} profile photo',
                            )

                        peer_url_id = serialize_player_key(peer)
                        st.markdown(
                            f'**[{peer["player"]}](player?player={peer_url_id})**'
                        )
                        st.caption(
                            f'{peer["team"]} · '
                            f'{peer["sub_position"] if pd.notna(peer["sub_position"]) else peer["position"]}'
                        )
                        st.markdown(
                            f'**{format_eur(peer["previous_market_value_in_eur"])}**'
                        )

                        age_text = (
                            f'{safe_int(peer["age_at_valuation"])} years old'
                            if pd.notna(peer["age_at_valuation"])
                            else "Age unavailable"
                        )
                        minutes = peer["current_minutes"]
                        if str(peer["position"]) == "Goalkeeper":
                            clean_sheet_rate = peer["clean_sheet_rate"]
                            performance_text = (
                                f'Clean-sheet rate {clean_sheet_rate:.0%}'
                                if pd.notna(clean_sheet_rate)
                                else "Clean-sheet rate unavailable"
                            )
                        elif pd.notna(minutes) and float(minutes) >= 90:
                            goals_per_90 = (
                                float(peer["current_goals"]) * 90 / float(minutes)
                                if pd.notna(peer["current_goals"])
                                else None
                            )
                            assists_per_90 = (
                                float(peer["current_assists"]) * 90 / float(minutes)
                                if pd.notna(peer["current_assists"])
                                else None
                            )
                            performance_text = (
                                f'Goals / 90 {goals_per_90:.2f}'
                                if goals_per_90 is not None
                                else "Goals / 90 unavailable"
                            )
                            if assists_per_90 is not None:
                                performance_text += f' · Assists / 90 {assists_per_90:.2f}'
                        else:
                            performance_text = "Per-90 rates unavailable (<90 minutes)"

                        st.caption(f"{age_text} · {performance_text}")


# -------------------------------------------------------------------------
# AI USAGE CITATION
# Tool: ChatGPT (OpenAI, 2026)
# Prompt (summary): Build a Streamlit scenario form for projected
# performance and show how submitted assumptions change the model estimate.
# Usage: Used AI assistance for form controls and scenario results.
# -------------------------------------------------------------------------

if scenario_tab.open:
    with scenario_tab:
        st.subheader("Scenario builder", icon=":material/science:")
        st.caption(
            "Build a custom end-of-season performance scenario and see its impact on the player's projected market value."
        )

        builder_col, result_col = st.columns([0.9, 1.4], gap="large")

        with builder_col:
            st.markdown("### Assumptions")
            st.caption("Inputs are applied together when you run the scenario.")
            st.button(
                "Reset to baseline",
                icon=":material/restart_alt:",
                on_click=reset_scenario,
                width="stretch",
            )

            with st.form(f"{player_key}_scenario_form"):
                st.markdown("#### Key performance")
                projected_games = st.number_input(
                    "Games",
                    min_value=safe_int(player["current_games"]),
                    max_value=safe_int(player["full_season_games"]),
                    value=baseline_defaults["games"],
                    step=1,
                    key=f"{player_key}_games",
                )
                projected_minutes = st.number_input(
                    "Minutes",
                    min_value=safe_int(player["current_minutes"]),
                    max_value=safe_int(player["full_season_games"]) * 90,
                    value=baseline_defaults["minutes"],
                    step=90,
                    key=f"{player_key}_minutes",
                )
                projected_goals = st.number_input(
                    "Goals",
                    min_value=safe_int(player["current_goals"]),
                    value=baseline_defaults["goals"],
                    step=1,
                    key=f"{player_key}_goals",
                )
                projected_assists = st.number_input(
                    "Assists",
                    min_value=safe_int(player["current_assists"]),
                    value=baseline_defaults["assists"],
                    step=1,
                    key=f"{player_key}_assists",
                )

                with st.expander("Advanced features", icon=":material/tune:"):
                    st.markdown("##### Discipline and defensive context")
                    projected_yellow_cards = st.number_input(
                        "Yellow cards",
                        min_value=safe_int(player["current_yellow_cards"]),
                        value=baseline_defaults["yellow_cards"],
                        step=1,
                        key=f"{player_key}_yellow_cards",
                    )
                    projected_red_cards = st.number_input(
                        "Red cards",
                        min_value=safe_int(player["current_red_cards"]),
                        value=baseline_defaults["red_cards"],
                        step=1,
                        key=f"{player_key}_red_cards",
                    )
                    total_clean_sheets = st.number_input(
                        "Clean sheets",
                        min_value=0,
                        max_value=safe_int(player["full_season_games"]),
                        value=baseline_defaults["clean_sheets"],
                        step=1,
                        key=f"{player_key}_clean_sheets",
                    )

                    st.markdown("##### Club performance")
                    club_goals_scored = st.number_input(
                        "Club goals scored",
                        min_value=0,
                        value=baseline_defaults["club_goals_scored"],
                        step=1,
                        key=f"{player_key}_club_goals_scored",
                    )
                    club_goals_conceded = st.number_input(
                        "Club goals conceded",
                        min_value=0,
                        value=baseline_defaults["club_goals_conceded"],
                        step=1,
                        key=f"{player_key}_club_goals_conceded",
                    )
                    avg_points_per_game = st.number_input(
                        "Average points per game",
                        min_value=0.0,
                        max_value=3.0,
                        value=baseline_defaults["avg_points_per_game"],
                        step=0.05,
                        format="%.2f",
                        key=f"{player_key}_avg_points_per_game",
                    )

                    st.markdown("##### Season and transfer context")
                    clubs_played = st.number_input(
                        "Clubs played for this season",
                        min_value=1,
                        max_value=5,
                        value=baseline_defaults["clubs_played"],
                        step=1,
                        key=f"{player_key}_clubs_played",
                    )
                    enable_transfer_scenario = st.checkbox(
                        "Model a transfer during the season",
                        key=f"{player_key}_transfer_enabled",
                    )
                    st.caption(
                        "Transfer values below are ignored unless the transfer option is selected."
                    )
                    transfers_during_season = st.number_input(
                        "Transfers during season",
                        min_value=1,
                        max_value=3,
                        value=1,
                        step=1,
                        key=f"{player_key}_transfers_during",
                    )
                    days_since_last_transfer = st.number_input(
                        "Days since last transfer",
                        min_value=0,
                        max_value=365,
                        value=90,
                        step=1,
                        key=f"{player_key}_days_since_transfer",
                    )

                submitted = st.form_submit_button(
                    "Run scenario",
                    icon=":material/play_arrow:",
                    type="primary",
                    width="stretch",
                )

            scenario_changes = {
                "projected_games": projected_games,
                "projected_minutes": projected_minutes,
                "projected_goals": projected_goals,
                "projected_assists": projected_assists,
                "projected_yellow_cards": projected_yellow_cards,
                "projected_red_cards": projected_red_cards,
                "total_clean_sheets": total_clean_sheets,
                "club_goals_scored": club_goals_scored,
                "club_goals_conceded": club_goals_conceded,
                "avg_points_per_game": avg_points_per_game,
                "clubs_played_for_season": clubs_played,
            }
            if enable_transfer_scenario:
                scenario_changes.update(
                    transfers_during_season=transfers_during_season,
                    days_since_last_transfer=days_since_last_transfer,
                )

            if submitted:
                st.session_state[scenario_state_key] = scenario_changes
                st.session_state[scenario_result_key] = None
                st.session_state[driver_view_key] = "Your scenario"
                submitted_changes = scenario_changes

        with result_col:
            with st.container(border=True):
                st.markdown("### Valuation impact")

                if submitted_changes is None:
                    st.info(
                        "Adjust the assumptions and select **Run scenario** to calculate a custom valuation.",
                        icon=":material/info:",
                    )
                    st.button(
                        "Explain the baseline projection",
                        icon=":material/analytics:",
                        on_click=lambda: st.session_state.update(
                            main_view="Model drivers"
                        ),
                        width="stretch",
                    )
                else:
                    try:
                        result = st.session_state[scenario_result_key]
                        if result is None:
                            with st.spinner(
                                "Calculating scenario…",
                                show_time=True,
                            ):
                                result = predict_scenario_by_player_id(
                                    player_id=selected_player_key,
                                    changes=submitted_changes,
                                )
                            st.session_state[scenario_result_key] = result

                        current_value = (
                            None
                            if pd.isna(player["previous_market_value_in_eur"])
                            else float(player["previous_market_value_in_eur"])
                        )
                        baseline_value = float(
                            result["baseline_projected_market_value_in_eur"]
                        )
                        scenario_value = float(
                            result["scenario_projected_market_value_in_eur"]
                        )

                        display_market_value_comparison(
                            current_value=current_value,
                            baseline_value=baseline_value,
                            scenario_value=scenario_value,
                        )
                        st.caption(
                            f'{submitted_changes["projected_games"]} games · '
                            f'{submitted_changes["projected_minutes"]:,} minutes · '
                            f'{submitted_changes["projected_goals"]} goals · '
                            f'{submitted_changes["projected_assists"]} assists'
                        )
                        st.button(
                            "Explore model drivers",
                            icon=":material/analytics:",
                            on_click=lambda: st.session_state.update(
                                main_view="Model drivers"
                            ),
                            type="primary",
                            width="stretch",
                        )
                    except ValueError as error:
                        st.error(str(error), icon=":material/error:")
                    except Exception:
                        st.error(
                            "The scenario could not be generated. Check the inputs and application logs.",
                            icon=":material/error:",
                        )


# -------------------------------------------------------------------------
# AI USAGE CITATION
# Tool: ChatGPT (OpenAI, 2026)
# Prompt (summary): Let users inspect SHAP drivers for the
# baseline prediction or a submitted scenario on the player page.
# Usage: Used AI assistance for the explanation view and caching flow.
# -------------------------------------------------------------------------

if drivers_tab.open:
    with drivers_tab:
        st.subheader("Model drivers", icon=":material/analytics:")
        st.caption(
            "Understand which player, performance, and market factors push each prediction higher or lower."
        )

        driver_view = st.segmented_control(
            "Explain prediction",
            ["Baseline projection", "Your scenario"],
            default="Baseline projection",
            key=driver_view_key,
            width="stretch",
        )

        selected_shap = None
        if driver_view == "Your scenario" and submitted_changes is None:
            st.info(
                "Run a scenario in **Scenario builder** to explain a custom prediction.",
                icon=":material/science:",
            )
        else:
            try:
                if driver_view == "Baseline projection":
                    st.metric(
                        f"Baseline projection for June {projection_year}",
                        format_eur(
                            player["baseline_projected_market_value_in_eur"]
                        ),
                    )
                    st.caption(
                        "The strongest factors behind the model's default end-of-season projection."
                    )
                    with st.spinner("Explaining the baseline…", show_time=True):
                        selected_shap = get_baseline_explanation(
                            selected_player_key
                        )
                else:
                    result = st.session_state[scenario_result_key]
                    if result is None:
                        with st.spinner("Calculating scenario…", show_time=True):
                            result = predict_scenario_by_player_id(
                                player_id=selected_player_key,
                                changes=submitted_changes,
                            )
                        st.session_state[scenario_result_key] = result

                    st.metric(
                        "Scenario projection",
                        format_eur(
                            result["scenario_projected_market_value_in_eur"]
                        ),
                    )
                    st.caption(
                        "The strongest factors behind the prediction under your submitted assumptions."
                    )
                    changes_items = tuple(sorted(submitted_changes.items()))
                    with st.spinner("Explaining the scenario…", show_time=True):
                        selected_shap = get_scenario_explanation(
                            selected_player_key,
                            changes_items,
                        )

                display_compact_shap_drivers(selected_shap, top_n=5)
            except ValueError as error:
                st.error(str(error), icon=":material/error:")
            except Exception:
                st.error(
                    "The model explanation could not be generated. The valuation result is still valid.",
                    icon=":material/error:",
                )

        if selected_shap is not None:
            explanation_details = st.expander(
                "Detailed model explanation",
                icon=":material/manage_search:",
                on_change="rerun",
            )
            if explanation_details.open:
                with explanation_details:
                    st.caption(
                        "SHAP values describe feature contributions in the model's log-market-value prediction space."
                    )
                    display_shap_drivers(selected_shap, top_n=10)



