-- ============================================================
-- GAMES BY SEASON
-- ============================================================

SELECT
    season,
    COUNT(*) AS games,
    COUNT(DISTINCT competition_id) AS competitions,
    COUNT(DISTINCT home_club_id) AS home_clubs,
    COUNT(DISTINCT away_club_id) AS away_clubs
FROM games
GROUP BY season
ORDER BY season;


-- ============================================================
-- APPEARANCES BY SEASON
-- ============================================================

SELECT
    g.season,
    COUNT(*) AS appearance_rows,
    COUNT(DISTINCT a.player_id) AS players,
    COUNT(DISTINCT a.game_id) AS games,
    COUNT(DISTINCT a.player_club_id) AS clubs
FROM appearances a
JOIN games g
    ON a.game_id = g.game_id
GROUP BY g.season
ORDER BY g.season;


-- ============================================================
-- PLAYER VALUATIONS BY YEAR
-- ============================================================

SELECT
    EXTRACT(YEAR FROM date) AS year,
    COUNT(*) AS valuations,
    COUNT(DISTINCT player_id) AS players
FROM player_valuations
GROUP BY year
ORDER BY year;


-- ============================================================
-- TRANSFERS BY YEAR
-- ============================================================

SELECT
    EXTRACT(YEAR FROM transfer_date) AS year,
    COUNT(*) AS transfers,
    COUNT(DISTINCT player_id) AS players
FROM transfers
GROUP BY year
ORDER BY year;


-- ============================================================
-- DATE RANGES
-- ============================================================

SELECT
    MIN(date) AS min_date,
    MAX(date) AS max_date
FROM games;

SELECT
    MIN(date) AS min_date,
    MAX(date) AS max_date
FROM appearances;

SELECT
    MIN(date) AS min_date,
    MAX(date) AS max_date
FROM player_valuations;

SELECT
    MIN(transfer_date) AS min_date,
    MAX(transfer_date) AS max_date
FROM transfers;

-- ============================================================
-- INSPECTION FOR TOP 5 LEAGUES
-- ============================================================

SELECT
    competition_id,
    name,
    type,
    sub_type,
    country_name
FROM competitions
WHERE LOWER(name) IN (
    'premier-league',
    'laliga',
    'bundesliga',
    'serie-a',
    'ligue-1'
)
ORDER BY country_name;

SELECT
    g.season,
    g.competition_id,
    COUNT(DISTINCT g.game_id) AS games,
    COUNT(DISTINCT a.player_id) AS players,
    COUNT(a.appearance_id) AS appearance_rows
FROM games g
LEFT JOIN appearances a
    ON g.game_id = a.game_id
WHERE g.competition_id IN (
	'GB1', -- Premier League
	'FR1', -- Ligue 1
	'L1', -- Bundesliga
	'IT1', -- Serie A
	'ES1' -- LaLiga
)
AND g.season >= 2020
GROUP BY
    g.season,
    g.competition_id
ORDER BY
    g.season,
    g.competition_id;