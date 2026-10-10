import json
from pathlib import Path

import pandas as pd
from streamlit.testing.v1 import AppTest


APP_PATH = Path(__file__).resolve().parents[1] / "app" / "app.py"


def test_player_discovery_is_the_default_page():
    app = AppTest.from_file(str(APP_PATH), default_timeout=30).run()

    assert not app.exception
    assert (
        app.title[0].value
        == "See what drives player value"
    )
    assert any(
        "TransferLens" in image.proto.imgs[0].alt
        for image in app.image
    )
    assert [metric.label for metric in app.metric[:4]] == [
        "Players",
        "Clubs",
        "Leagues",
        "Projection horizon",
    ]
    assert app.text_input[0].label == "Search player"
    assert app.multiselect[0].label == "Club"
    assert app.multiselect[1].label == "Choose two or three players"
    assert app.multiselect[1].value == []
    assert [control.label for control in app.get("pills")] == [
        "League",
        "Position",
    ]
    assert len(app.dataframe) == 1
    table = app.dataframe[0].value
    assert list(table.columns[:5]) == [
        "player",
        "club_badge",
        "club",
        "league_badge",
        "league",
    ]
    assert table["club_badge"].str.startswith(
        "data:image/webp;base64,"
    ).all()
    assert table["league_badge"].str.startswith(
        "data:image/webp;base64,"
    ).all()
    assert table["player"].str.startswith("player?player=").all()
    assert any(
        "2,070 players" in caption.value
        for caption in app.caption
    )
    assert any("player?player=fb-bil-nsongo#" in value for value in table["player"])
    assert any(
        "player?player=fb-yeremay-hernandez#" in value
        for value in table["player"]
    )
    assert not any(
        "AI usage disclosure" in caption.value
        for caption in app.caption
    )


def test_discovery_compares_selected_players_without_changing_the_main_table():
    app = AppTest.from_file(str(APP_PATH), default_timeout=30).run()
    app.text_input[1].set_value("jose maria gimenez").run(timeout=30)
    assert not app.exception
    assert len(app.multiselect[1].options) == 1
    assert "Gim" in app.multiselect[1].options[0]
    app.text_input[1].set_value("").run(timeout=30)
    data_path = APP_PATH.parents[1] / "data" / "processed" / "current_season_inference_2026_27.csv"
    players = pd.read_csv(data_path)
    attackers = (
        players.loc[
            (players["position"] == "Attack")
            & (players["current_minutes"] >= 90)
            & players["player_id"].notna()
        ]
        .drop_duplicates("player_id")
        .head(2)
    )
    ids = [str(int(player_id)) for player_id in attackers["player_id"]]
    comparison_keys = [ids[0], "fb-bil-nsongo"]

    app.multiselect[1].set_value(comparison_keys).run(timeout=30)

    assert not app.exception
    assert app.multiselect[1].value == comparison_keys
    assert len(app.table) == 1
    comparison = app.table[0].value.set_index("Metric")
    assert comparison.loc["Photo"].iloc[0].startswith("![")
    assert comparison.loc["Photo"].iloc[1] == "\u2014"
    assert comparison.loc["Club"].notna().all()
    assert comparison.loc["League"].isin(
        ["Premier League", "La Liga", "Ligue 1", "Bundesliga", "Serie A"]
    ).all()
    assert "Projected end-of-season value" in comparison.index
    assert "Goals / 90" in comparison.index
    assert any("player?player=fb-bil-nsongo" in column for column in comparison.columns)
    assert len(app.dataframe) == 1
    assert len(app.dataframe[0].value) == 2_070

    app.text_input[0].set_value("unlikely_player_search_term").run(timeout=30)
    assert not app.exception
    assert app.multiselect[1].value == comparison_keys
    assert len(app.table) == 1
    assert len(app.dataframe) == 0


def test_player_search_matches_names_without_accents():
    app = AppTest.from_file(str(APP_PATH), default_timeout=30).run()

    app.text_input[0].set_value("jose maria gimenez").run(timeout=30)

    assert not app.exception
    assert len(app.dataframe) == 1
    table = app.dataframe[0].value
    assert len(table) == 1
    assert "player?player=250845#" in table.iloc[0]["player"]


def test_deep_dive_picker_filters_accent_insensitively():
    app = AppTest.from_file(str(APP_PATH), default_timeout=30).run()
    app.switch_page("app_pages/player.py").run(timeout=30)

    app.text_input[0].set_value("jose maria gimenez").run(timeout=30)

    assert not app.exception
    assert app.selectbox[0].label == "Choose player"
    assert len(app.selectbox[0].options) == 1
    assert "Gim" in app.selectbox[0].options[0]


def test_player_deep_dive_starts_empty_and_runs_scenario():
    app = AppTest.from_file(str(APP_PATH), default_timeout=30).run()
    app.switch_page("app_pages/player.py").run(timeout=30)

    assert not app.exception
    assert app.title[0].value == "Player deep dive"
    assert app.text_input[0].label == "Search player"
    assert app.selectbox[0].label == "Choose player"
    assert app.selectbox[0].value is None
    assert any(
        "Choose a player above" in info.value
        for info in app.info
    )
    assert not any(
        "AI usage disclosure" in caption.value
        for caption in app.caption
    )

    app.selectbox[0].set_value("fb-bil-nsongo").run(timeout=30)
    assert not app.exception
    assert app.selectbox[0].value == "fb-bil-nsongo"
    assert any(element.value == "Bil Nsongo" for element in app.subheader)
    assert any("Photo unavailable" in caption.value for caption in app.caption)
    assert any("Nationality unavailable" in caption.value for caption in app.caption)
    assert not any(
        "Profile details unavailable in the source data" in caption.value
        for caption in app.caption
    )
    assert any(
        metric.label == "Latest market value" and metric.value == "Not recorded"
        for metric in app.metric
    )
    assert not any(
        "**nan**" in markdown.value.lower()
        for markdown in app.markdown
    )

    app.selectbox[0].select_index(0).run(timeout=30)

    assert not app.exception
    assert app.session_state["main_view"] == "Overview"
    assert any(
        "About this estimate" in markdown.value
        for markdown in app.markdown
    )
    assert any(
        "player, performance, and club data" in caption.value
        for caption in app.caption
    )
    assert not any(
        "Average error" in caption.value or "MAE" in caption.value
        for caption in app.caption
    )
    assert not any(
        "AI usage disclosure" in caption.value
        for caption in app.caption
    )
    assert any(
        "club badge" in image.proto.imgs[0].alt
        for image in app.image
    )
    assert any(
        "Top 5 league ranking" in markdown.value
        for markdown in app.markdown
    )
    assert any(
        markdown.value.startswith("**Premier League**")
        for markdown in app.markdown
    )
    assert not any(
        "ENG-Premier League" in markdown.value
        for markdown in app.markdown
    )
    assert len(app.get("vega_lite_chart")) == 1
    pitch_spec = app.get("vega_lite_chart")[0].proto.spec
    assert pitch_spec.count("#2deb78") >= 3
    pitch_layers = json.loads(pitch_spec)["layer"]
    assert all(
        layer["mark"].get("tooltip") is False
        for layer in pitch_layers
    )
    assert any(
        caption.value == "Attacking direction →"
        for caption in app.caption
    )

    app.session_state["main_view"] = "Scenario builder"
    app.run(timeout=30)

    assert not app.exception

    run_button = next(
        button for button in app.button if button.label == "Run scenario"
    )
    run_button.click()
    # AppTest doesn't model browser tab selection, so preserve the active tab
    # while submitting the form event.
    app.session_state["main_view"] = "Scenario builder"
    app.run(timeout=30)

    assert not app.exception

    drivers_button = next(
        button
        for button in app.button
        if button.label == "Explore model drivers"
    )
    drivers_button.click().run(timeout=30)

    assert not app.exception
    assert app.session_state["main_view"] == "Model drivers"

    explanation_selector = next(
        control
        for control in app.segmented_control
        if control.label == "Explain prediction"
    )
    assert explanation_selector.value == "Your scenario"

    explanation_selector.set_value("Baseline projection").run(timeout=30)

    assert not app.exception
    assert explanation_selector.value == "Baseline projection"
