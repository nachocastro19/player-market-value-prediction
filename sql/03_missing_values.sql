-- ============================================================
-- 03_MISSING_VALUES.SQL
-- Missing-values analysis for the Transfermarkt project
-- ============================================================
-- Planned model scope:
--   Seasons: 2020/21 to 2025/26 (season values 2020-2025)
--   Leagues: Premier League, LaLiga, Serie A, Bundesliga, Ligue 1
-- ============================================================

-- ============================================================
-- 0. REUSABLE MODEL-SCOPE VIEWS
-- ============================================================

CREATE OR REPLACE TEMP VIEW model_games AS
SELECT
    game_id,
    season,
    competition_id
FROM games
WHERE season BETWEEN 2020 AND 2025
  AND competition_id IN ('GB1', 'ES1', 'IT1', 'L1', 'FR1');


CREATE OR REPLACE TEMP VIEW model_players AS
SELECT DISTINCT
    a.player_id
FROM appearances a
JOIN model_games mg
    ON a.game_id = mg.game_id
WHERE a.player_id IS NOT NULL;


-- ============================================================
-- 1. PLAYERS
-- ============================================================

-- 1A. General source-table missingness
SELECT
    COUNT(*) AS total_player_rows,
    COUNT(*) FILTER (WHERE date_of_birth IS NULL) AS missing_date_of_birth,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE date_of_birth IS NULL) / COUNT(*),
        2
    ) AS pct_missing_date_of_birth,
    COUNT(*) FILTER (WHERE position IS NULL) AS missing_position,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE position IS NULL) / COUNT(*),
        2
    ) AS pct_missing_position,
    COUNT(*) FILTER (WHERE sub_position IS NULL) AS missing_sub_position,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE sub_position IS NULL) / COUNT(*),
        2
    ) AS pct_missing_sub_position,
    COUNT(*) FILTER (WHERE foot IS NULL) AS missing_foot,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE foot IS NULL) / COUNT(*),
        2
    ) AS pct_missing_foot,
    COUNT(*) FILTER (WHERE height_in_cm IS NULL) AS missing_height_in_cm,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE height_in_cm IS NULL) / COUNT(*),
        2
    ) AS pct_missing_height_in_cm
FROM players;


-- 1B. Missingness restricted to players in the planned model population
SELECT
    COUNT(*) AS total_model_players,
    COUNT(*) FILTER (WHERE p.date_of_birth IS NULL) AS missing_date_of_birth,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE p.date_of_birth IS NULL) / COUNT(*),
        2
    ) AS pct_missing_date_of_birth,
    COUNT(*) FILTER (WHERE p.position IS NULL) AS missing_position,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE p.position IS NULL) / COUNT(*),
        2
    ) AS pct_missing_position,
    COUNT(*) FILTER (WHERE p.sub_position IS NULL) AS missing_sub_position,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE p.sub_position IS NULL) / COUNT(*),
        2
    ) AS pct_missing_sub_position,
    COUNT(*) FILTER (WHERE p.foot IS NULL) AS missing_foot,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE p.foot IS NULL) / COUNT(*),
        2
    ) AS pct_missing_foot,
    COUNT(*) FILTER (WHERE p.height_in_cm IS NULL) AS missing_height_in_cm,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE p.height_in_cm IS NULL) / COUNT(*),
        2
    ) AS pct_missing_height_in_cm
FROM model_players mp
JOIN players p
    ON mp.player_id = p.player_id;


-- ============================================================
-- 2. APPEARANCES
-- ============================================================

-- 2A. General source-table missingness
SELECT
    COUNT(*) AS total_appearance_rows,
    COUNT(*) FILTER (WHERE player_id IS NULL) AS missing_player_id,
    COUNT(*) FILTER (WHERE game_id IS NULL) AS missing_game_id,
    COUNT(*) FILTER (WHERE player_club_id IS NULL) AS missing_player_club_id,
    COUNT(*) FILTER (WHERE competition_id IS NULL) AS missing_competition_id,
    COUNT(*) FILTER (WHERE minutes_played IS NULL) AS missing_minutes_played,
    COUNT(*) FILTER (WHERE goals IS NULL) AS missing_goals,
    COUNT(*) FILTER (WHERE assists IS NULL) AS missing_assists,
    COUNT(*) FILTER (WHERE yellow_cards IS NULL) AS missing_yellow_cards,
    COUNT(*) FILTER (WHERE red_cards IS NULL) AS missing_red_cards
FROM appearances;


-- 2B. Missingness restricted to appearances in the planned model scope
SELECT
    COUNT(*) AS total_model_appearance_rows,
    COUNT(*) FILTER (WHERE a.player_id IS NULL) AS missing_player_id,
    COUNT(*) FILTER (WHERE a.game_id IS NULL) AS missing_game_id,
    COUNT(*) FILTER (WHERE a.player_club_id IS NULL) AS missing_player_club_id,
    COUNT(*) FILTER (WHERE a.competition_id IS NULL) AS missing_competition_id,
    COUNT(*) FILTER (WHERE a.minutes_played IS NULL) AS missing_minutes_played,
    COUNT(*) FILTER (WHERE a.goals IS NULL) AS missing_goals,
    COUNT(*) FILTER (WHERE a.assists IS NULL) AS missing_assists,
    COUNT(*) FILTER (WHERE a.yellow_cards IS NULL) AS missing_yellow_cards,
    COUNT(*) FILTER (WHERE a.red_cards IS NULL) AS missing_red_cards
FROM appearances a
JOIN model_games mg
    ON a.game_id = mg.game_id;


-- ============================================================
-- 3. PLAYER VALUATIONS
-- ============================================================

-- 3C. Model players with no valuation history at all
-- This is a player-level coverage check.
SELECT
    COUNT(*) AS total_model_players,
    COUNT(*) FILTER (WHERE pv.player_id IS NULL) AS model_players_without_valuation_history,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE pv.player_id IS NULL) / COUNT(*),
        2
    ) AS pct_model_players_without_valuation_history
FROM model_players mp
LEFT JOIN (
    SELECT DISTINCT player_id
    FROM player_valuations
    WHERE player_id IS NOT NULL
) pv
    ON mp.player_id = pv.player_id;


-- ============================================================
-- 4. TRANSFERS
-- ============================================================

-- 4A. General source-table missingness
SELECT
    COUNT(*) AS total_transfer_rows,
    COUNT(*) FILTER (WHERE player_id IS NULL) AS missing_player_id,
    COUNT(*) FILTER (WHERE transfer_date IS NULL) AS missing_transfer_date,
    COUNT(*) FILTER (WHERE from_club_id IS NULL) AS missing_from_club_id,
    COUNT(*) FILTER (WHERE to_club_id IS NULL) AS missing_to_club_id,
    COUNT(*) FILTER (WHERE transfer_fee IS NULL) AS missing_transfer_fee,
    COUNT(*) FILTER (WHERE market_value_in_eur IS NULL) AS missing_market_value_in_eur_at_transfer
FROM transfers;


-- 4B. Existing transfer rows for players in the planned model population
-- INNER JOIN to measure missing fields only where a transfer record actually exists.
SELECT
    COUNT(*) AS total_model_player_transfer_rows,
    COUNT(DISTINCT t.player_id) AS model_players_with_transfer_records,
    COUNT(*) FILTER (WHERE t.transfer_date IS NULL) AS missing_transfer_date,
    COUNT(*) FILTER (WHERE t.from_club_id IS NULL) AS missing_from_club_id,
    COUNT(*) FILTER (WHERE t.to_club_id IS NULL) AS missing_to_club_id,
    COUNT(*) FILTER (WHERE t.transfer_fee IS NULL) AS missing_transfer_fee,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE t.transfer_fee IS NULL) / COUNT(*),
        2
    ) AS pct_missing_transfer_fee,
    COUNT(*) FILTER (WHERE t.market_value_in_eur IS NULL) AS missing_market_value_in_eur_at_transfer,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE t.market_value_in_eur IS NULL) / COUNT(*),
        2
    ) AS pct_missing_market_value_in_eur_at_transfer
FROM transfers t
JOIN model_players mp
    ON t.player_id = mp.player_id;


-- 4C. Model players with no transfer history at all
-- This is a player-level coverage check, not a row-level missingness check.
SELECT
    COUNT(*) AS total_model_players,
    COUNT(*) FILTER (WHERE t.player_id IS NULL) AS model_players_without_transfer_history,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE t.player_id IS NULL) / COUNT(*),
        2
    ) AS pct_model_players_without_transfer_history
FROM model_players mp
LEFT JOIN (
    SELECT DISTINCT player_id
    FROM transfers
    WHERE player_id IS NOT NULL
) t
    ON mp.player_id = t.player_id;


-- ============================================================
-- 5. CLUB GAMES
-- ============================================================

-- 5A. General source-table missingness
SELECT
    COUNT(*) AS total_club_game_rows,
    COUNT(*) FILTER (WHERE game_id IS NULL) AS missing_game_id,
    COUNT(*) FILTER (WHERE club_id IS NULL) AS missing_club_id,
    COUNT(*) FILTER (WHERE own_goals IS NULL) AS missing_own_goals,
    COUNT(*) FILTER (WHERE opponent_goals IS NULL) AS missing_opponent_goals,
    COUNT(*) FILTER (WHERE own_position IS NULL) AS missing_own_position,
    COUNT(*) FILTER (WHERE opponent_position IS NULL) AS missing_opponent_position,
    COUNT(*) FILTER (WHERE is_win IS NULL) AS missing_is_win
FROM club_games;


-- 5B. Missingness restricted to club-game rows in the planned model scope
SELECT
    COUNT(*) AS total_model_club_game_rows,
    COUNT(*) FILTER (WHERE cg.game_id IS NULL) AS missing_game_id,
    COUNT(*) FILTER (WHERE cg.club_id IS NULL) AS missing_club_id,
    COUNT(*) FILTER (WHERE cg.own_goals IS NULL) AS missing_own_goals,
    COUNT(*) FILTER (WHERE cg.opponent_goals IS NULL) AS missing_opponent_goals,
    COUNT(*) FILTER (WHERE cg.own_position IS NULL) AS missing_own_position,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE cg.own_position IS NULL) / COUNT(*),
        2
    ) AS pct_missing_own_position,
    COUNT(*) FILTER (WHERE cg.opponent_position IS NULL) AS missing_opponent_position,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE cg.opponent_position IS NULL) / COUNT(*),
        2
    ) AS pct_missing_opponent_position,
    COUNT(*) FILTER (WHERE cg.is_win IS NULL) AS missing_is_win
FROM club_games cg
JOIN model_games mg
    ON cg.game_id = mg.game_id;
