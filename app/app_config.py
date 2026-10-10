"""Static paths and display configuration for the Streamlit app."""

from datetime import date
from pathlib import Path


APP_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = APP_DIR.parent
TEAM_LOGO_ROOT = PROJECT_ROOT / "external" / "football-logos" / "logos"
VISUAL_IDENTITY_ROOT = APP_DIR / "visual_identity"
BRAND_MARK = VISUAL_IDENTITY_ROOT / "transferlens_mark_universal.png"
BRAND_WORDMARK = VISUAL_IDENTITY_ROOT / "new_svg_header.svg"
# Refresh date recorded from current_season_predictions_2026_27.csv.
CURRENT_SEASON_DATA_REFRESH_DATE = date(2026, 10, 4)

LEAGUE_BADGES = {
    "ENG-Premier League": APP_DIR / "assets" / "premier_league.png",
    "ESP-La Liga": APP_DIR / "assets" / "LaLiga.png",
    "ITA-Serie A": APP_DIR / "assets" / "SerieA.png",
    "GER-Bundesliga": APP_DIR / "assets" / "bundesliga.png",
    "FRA-Ligue 1": APP_DIR / "assets" / "ligue1.png",
}

LEAGUE_LOGO_FOLDERS = {
    "ENG-Premier League": "England - Premier League",
    "ESP-La Liga": "Spain - LaLiga",
    "FRA-Ligue 1": "France - Ligue 1",
    "GER-Bundesliga": "Germany - Bundesliga",
    "ITA-Serie A": "Italy - Serie A",
}

# The inference data uses shortened club names, while the logo repository uses
# official display names. Keep the relationship explicit so missing or renamed
# clubs are caught by tests instead of being silently fuzzy-matched at runtime.
TEAM_LOGO_FILES = {
    ("ENG-Premier League", "Arsenal"): "Arsenal FC.png",
    ("ENG-Premier League", "Aston Villa"): "Aston Villa.png",
    ("ENG-Premier League", "Bournemouth"): "AFC Bournemouth.png",
    ("ENG-Premier League", "Brentford"): "Brentford FC.png",
    ("ENG-Premier League", "Brighton"): "Brighton & Hove Albion.png",
    ("ENG-Premier League", "Chelsea"): "Chelsea FC.png",
    ("ENG-Premier League", "Coventry City"): "Coventry City.png",
    ("ENG-Premier League", "Crystal Palace"): "Crystal Palace.png",
    ("ENG-Premier League", "Everton"): "Everton FC.png",
    ("ENG-Premier League", "Fulham"): "Fulham FC.png",
    ("ENG-Premier League", "Hull City"): "Hull City.png",
    ("ENG-Premier League", "Ipswich Town"): "Ipswich Town.png",
    ("ENG-Premier League", "Leeds United"): "Leeds United.png",
    ("ENG-Premier League", "Liverpool"): "Liverpool FC.png",
    ("ENG-Premier League", "Manchester City"): "Manchester City.png",
    ("ENG-Premier League", "Manchester Utd"): "Manchester United.png",
    ("ENG-Premier League", "Newcastle"): "Newcastle United.png",
    ("ENG-Premier League", "Nottingham"): "Nottingham Forest.png",
    ("ENG-Premier League", "Sunderland"): "Sunderland AFC.png",
    ("ENG-Premier League", "Tottenham"): "Tottenham Hotspur.png",
    ("ESP-La Liga", "Alavés"): "Deportivo Alavés.png",
    ("ESP-La Liga", "Athletic Club"): "Athletic Bilbao.png",
    ("ESP-La Liga", "Atlético Madrid"): "Atlético de Madrid.png",
    ("ESP-La Liga", "Barcelona"): "FC Barcelona.png",
    ("ESP-La Liga", "Celta Vigo"): "Celta de Vigo.png",
    ("ESP-La Liga", "Dep. A Coruña"): "Deportivo A Coruña.png",
    ("ESP-La Liga", "Elche"): "Elche CF.png",
    ("ESP-La Liga", "Espanyol"): "RCD Espanyol Barcelona.png",
    ("ESP-La Liga", "Getafe"): "Getafe CF.png",
    ("ESP-La Liga", "Levante"): "Levante UD.png",
    ("ESP-La Liga", "Málaga"): "Málaga CF.png",
    ("ESP-La Liga", "Osasuna"): "CA Osasuna.png",
    ("ESP-La Liga", "Racing Sant"): "Racing Santander.png",
    ("ESP-La Liga", "Rayo Vallecano"): "Rayo Vallecano.png",
    ("ESP-La Liga", "Real Betis"): "Real Betis Balompié.png",
    ("ESP-La Liga", "Real Madrid"): "Real Madrid.png",
    ("ESP-La Liga", "Real Sociedad"): "Real Sociedad.png",
    ("ESP-La Liga", "Sevilla"): "Sevilla FC.png",
    ("ESP-La Liga", "Valencia"): "Valencia CF.png",
    ("ESP-La Liga", "Villarreal"): "Villarreal CF.png",
    ("FRA-Ligue 1", "Angers"): "Angers SCO.png",
    ("FRA-Ligue 1", "Auxerre"): "AJ Auxerre.png",
    ("FRA-Ligue 1", "Brest"): "Stade Brestois 29.png",
    ("FRA-Ligue 1", "Le Havre"): "Le Havre AC.png",
    ("FRA-Ligue 1", "Le Mans"): "Le Mans FC.png",
    ("FRA-Ligue 1", "Lens"): "RC Lens.png",
    ("FRA-Ligue 1", "Lille"): "LOSC Lille.png",
    ("FRA-Ligue 1", "Lorient"): "FC Lorient.png",
    ("FRA-Ligue 1", "Lyon"): "Olympique Lyon.png",
    ("FRA-Ligue 1", "Marseille"): "Olympique Marseille.png",
    ("FRA-Ligue 1", "Monaco"): "AS Monaco.png",
    ("FRA-Ligue 1", "Nice"): "OGC Nice.png",
    ("FRA-Ligue 1", "Paris FC"): "Paris FC.png",
    ("FRA-Ligue 1", "Paris SG"): "Paris Saint-Germain.png",
    ("FRA-Ligue 1", "Rennes"): "Stade Rennais FC.png",
    ("FRA-Ligue 1", "Strasbourg"): "RC Strasbourg Alsace.png",
    ("FRA-Ligue 1", "Toulouse"): "FC Toulouse.png",
    ("FRA-Ligue 1", "Troyes"): "ESTAC Troyes.png",
    ("GER-Bundesliga", "Augsburg"): "FC Augsburg.png",
    ("GER-Bundesliga", "Bayern Munich"): "Bayern Munich.png",
    ("GER-Bundesliga", "Dortmund"): "Borussia Dortmund.png",
    ("GER-Bundesliga", "Elversberg"): "SV 07 Elversberg.png",
    ("GER-Bundesliga", "Frankfurt"): "Eintracht Frankfurt.png",
    ("GER-Bundesliga", "Freiburg"): "SC Freiburg.png",
    ("GER-Bundesliga", "Gladbach"): "Borussia Mönchengladbach.png",
    ("GER-Bundesliga", "Hamburger SV"): "Hamburger SV.png",
    ("GER-Bundesliga", "Hoffenheim"): "TSG 1899 Hoffenheim.png",
    ("GER-Bundesliga", "Köln"): "1.FC Köln.png",
    ("GER-Bundesliga", "Leverkusen"): "Bayer 04 Leverkusen.png",
    ("GER-Bundesliga", "Mainz 05"): "1.FSV Mainz 05.png",
    ("GER-Bundesliga", "Paderborn 07"): "SC Paderborn 07.png",
    ("GER-Bundesliga", "RB Leipzig"): "RB Leipzig.png",
    ("GER-Bundesliga", "Schalke 04"): "FC Schalke 04.png",
    ("GER-Bundesliga", "Stuttgart"): "VfB Stuttgart.png",
    ("GER-Bundesliga", "Union Berlin"): "1.FC Union Berlin.png",
    ("GER-Bundesliga", "Werder Bremen"): "SV Werder Bremen.png",
    ("ITA-Serie A", "Atalanta"): "Atalanta BC.png",
    ("ITA-Serie A", "Bologna"): "Bologna FC 1909.png",
    ("ITA-Serie A", "Cagliari"): "Cagliari Calcio.png",
    ("ITA-Serie A", "Como"): "Como 1907.png",
    ("ITA-Serie A", "Fiorentina"): "ACF Fiorentina.png",
    ("ITA-Serie A", "Frosinone"): "Frosinone Calcio.png",
    ("ITA-Serie A", "Genoa"): "Genoa CFC.png",
    ("ITA-Serie A", "Inter"): "Inter Milan.png",
    ("ITA-Serie A", "Juventus"): "Juventus FC.png",
    ("ITA-Serie A", "Lazio"): "SS Lazio.png",
    ("ITA-Serie A", "Lecce"): "US Lecce.png",
    ("ITA-Serie A", "Milan"): "AC Milan.png",
    ("ITA-Serie A", "Monza"): "AC Monza.png",
    ("ITA-Serie A", "Napoli"): "SSC Napoli.png",
    ("ITA-Serie A", "Parma"): "Parma Calcio 1913.png",
    ("ITA-Serie A", "Roma"): "AS Roma.png",
    ("ITA-Serie A", "Sassuolo"): "US Sassuolo.png",
    ("ITA-Serie A", "Torino"): "Torino FC.png",
    ("ITA-Serie A", "Udinese"): "Udinese Calcio.png",
    ("ITA-Serie A", "Venezia"): "Venezia FC.png",
}

TEAM_BADGES = {
    key: TEAM_LOGO_ROOT / LEAGUE_LOGO_FOLDERS[key[0]] / filename
    for key, filename in TEAM_LOGO_FILES.items()
}
