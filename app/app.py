# -------------------------------------------------------------------------
# AI USAGE CITATION
# Tool: ChatGPT (OpenAI, 2026)
# Prompt (summary): Set up a Streamlit app with shared branding
# and navigation between player discovery and player detail pages.
# Usage: Used AI assistance for the app entry point and page navigation.
# -------------------------------------------------------------------------

import streamlit as st

from app_config import BRAND_MARK


st.set_page_config(
    page_title="TransferLens | Football value intelligence",
    page_icon=str(BRAND_MARK),
    layout="wide",
)

st.logo(
    str(BRAND_MARK),
    size="large",
)

players_page = st.Page(
    "app_pages/players.py",
    title="Players",
    icon=":material/groups:",
    default=True,
)
player_page = st.Page(
    "app_pages/player.py",
    title="Player deep dive",
    icon=":material/person_search:",
)

navigation = st.navigation(
    [players_page, player_page],
    position="top",
)
navigation.run()
