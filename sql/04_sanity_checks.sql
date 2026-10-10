-- ============================================================
-- SANITY CHECKS
-- ============================================================


-- ============================================================
-- 0. MODEL SCOPE
-- ============================================================

CREATE OR REPLACE TEMP VIEW model_games AS
SELECT *
FROM games
WHERE season BETWEEN 2020 AND 2025
  AND competition_id IN (
      'GB1', -- Premier League
      'ES1', -- LaLiga
      'IT1', -- Serie A
      'L1',  -- Bundesliga
      'FR1'  -- Ligue 1
  );


CREATE OR REPLACE TEMP VIEW model_players AS
SELECT DISTINCT a.player_id
FROM appearances a
JOIN model_games g
    ON a.game_id = g.game_id;


-- ============================================================
-- 1. PLAYER ATTRIBUTE CHECKS
-- ============================================================


-- ------------------------------------------------------------
-- 1A. Height
-- Hard-invalid: <= 0
-- Suspicious: < 150 cm or > 210 cm
-- ------------------------------------------------------------

SELECT
    COUNT(*) AS total_model_players,
    COUNT(*) FILTER (
        WHERE p.height_in_cm <= 0
    ) AS invalid_height,
    COUNT(*) FILTER (
        WHERE p.height_in_cm < 150
           OR p.height_in_cm > 210
    ) AS suspicious_height,
    MIN(p.height_in_cm) AS min_height_cm,
    MAX(p.height_in_cm) AS max_height_cm
FROM model_players mp
JOIN players p
    ON mp.player_id = p.player_id
WHERE p.height_in_cm IS NOT NULL;

-- ------------------------------------------------------------
-- 1B. Player age during appearances
-- Suspicious: younger than 15 or older than 45
-- ------------------------------------------------------------

WITH player_ages AS (
    SELECT
        a.player_id,
        p.name,
        a.date,
        FLOOR(
            DATE_DIFF(
                'day',
                CAST(p.date_of_birth AS DATE),
                a.date
            ) / 365.25
        ) AS age
    FROM appearances a
    JOIN model_games g
        ON a.game_id = g.game_id
    JOIN players p
        ON a.player_id = p.player_id
    WHERE p.date_of_birth IS NOT NULL
)
SELECT
    MIN(age) AS min_age,
    MAX(age) AS max_age,
    COUNT(*) FILTER (
        WHERE age < 15
    ) AS appearances_age_under_15,
    COUNT(*) FILTER (
        WHERE age > 45
    ) AS appearances_age_over_45
FROM player_ages;

-- ------------------------------------------------------------
-- 1C. Position values
-- ------------------------------------------------------------

SELECT
    position,
    COUNT(*) AS players
FROM players p
JOIN model_players mp
    ON p.player_id = mp.player_id
GROUP BY position
ORDER BY players DESC;

-- Sub-position values

SELECT
    sub_position,
    COUNT(*) AS players
FROM players p
JOIN model_players mp
    ON p.player_id = mp.player_id
GROUP BY sub_position
ORDER BY players DESC;

-- Preferred foot values

SELECT
    foot,
    COUNT(*) AS players
FROM players p
JOIN model_players mp
    ON p.player_id = mp.player_id
GROUP BY foot
ORDER BY players DESC;

-- ============================================================
-- 2. APPEARANCE SANITY CHECKS
-- ============================================================

-- ------------------------------------------------------------
-- 2A. Numeric performance variables
-- ------------------------------------------------------------

SELECT
    COUNT(*) AS total_model_appearances,
    COUNT(*) FILTER (
        WHERE a.minutes_played < 0
    ) AS negative_minutes,
    COUNT(*) FILTER (
        WHERE a.minutes_played > 90
    ) AS minutes_over_90,
    COUNT(*) FILTER (
        WHERE a.goals < 0
    ) AS negative_goals,
    COUNT(*) FILTER (
        WHERE a.assists < 0
    ) AS negative_assists,
    COUNT(*) FILTER (
        WHERE a.yellow_cards < 0
    ) AS negative_yellow_cards,
    COUNT(*) FILTER (
        WHERE a.red_cards < 0
    ) AS negative_red_cards,
    MAX(a.minutes_played) AS max_minutes,
    MAX(a.goals) AS max_goals,
    MAX(a.assists) AS max_assists,
    MAX(a.yellow_cards) AS max_yellow_cards,
    MAX(a.red_cards) AS max_red_cards
FROM appearances a
JOIN model_games g
    ON a.game_id = g.game_id;

-- ------------------------------------------------------------
-- 2B. Appearance date must match game date
-- ------------------------------------------------------------

SELECT
    COUNT(*) AS total_model_appearances,
    COUNT(*) FILTER (
        WHERE a.date <> g.date
    ) AS date_mismatches
FROM appearances a
JOIN model_games g
    ON a.game_id = g.game_id;

-- ------------------------------------------------------------
-- 2C. Appearance competition must match game competition
-- ------------------------------------------------------------

SELECT
    COUNT(*) AS total_model_appearances,
    COUNT(*) FILTER (
        WHERE a.competition_id <> g.competition_id
    ) AS competition_mismatches
FROM appearances a
JOIN model_games g
    ON a.game_id = g.game_id;

-- ------------------------------------------------------------
-- 2D. Player club must be one of the two clubs playing
-- ------------------------------------------------------------

SELECT
    COUNT(*) AS total_model_appearances,
    COUNT(*) FILTER (
        WHERE a.player_club_id <> g.home_club_id
          AND a.player_club_id <> g.away_club_id
    ) AS invalid_player_club
FROM appearances a
JOIN model_games g
    ON a.game_id = g.game_id;

-- ============================================================
-- 3. GAME SANITY CHECKS
-- ============================================================

-- ------------------------------------------------------------
-- 3A. Basic game logic
-- ------------------------------------------------------------

SELECT
    COUNT(*) AS total_model_games,
    COUNT(*) FILTER (
        WHERE home_club_id = away_club_id
    ) AS same_home_and_away_club,
    COUNT(*) FILTER (
        WHERE home_club_goals < 0
    ) AS negative_home_goals,
    COUNT(*) FILTER (
        WHERE away_club_goals < 0
    ) AS negative_away_goals,
    COUNT(*) FILTER (
        WHERE home_club_position < 1
           OR home_club_position > 20
    ) AS suspicious_home_position,
    COUNT(*) FILTER (
        WHERE away_club_position < 1
           OR away_club_position > 20
    ) AS suspicious_away_position,
    MAX(home_club_goals) AS max_home_goals,
    MAX(away_club_goals) AS max_away_goals
FROM model_games;

-- ============================================================
-- 4. CLUB_GAME CONSISTENCY CHECKS
-- ============================================================

-- ------------------------------------------------------------
-- 4A. Basic numeric / identifier logic
-- ------------------------------------------------------------

SELECT
    COUNT(*) AS total_model_club_game_rows,
    COUNT(*) FILTER (
        WHERE cg.club_id = cg.opponent_id
    ) AS same_club_and_opponent,
    COUNT(*) FILTER (
        WHERE cg.own_goals < 0
    ) AS negative_own_goals,
    COUNT(*) FILTER (
        WHERE cg.opponent_goals < 0
    ) AS negative_opponent_goals,
    COUNT(*) FILTER (
        WHERE cg.is_win NOT IN (0, 1)
    ) AS invalid_is_win
FROM club_games cg
JOIN model_games g
    ON cg.game_id = g.game_id;

-- ------------------------------------------------------------
-- 4B. is_win must agree with score
-- ------------------------------------------------------------

SELECT
    COUNT(*) AS total_model_club_game_rows,
    COUNT(*) FILTER (
        WHERE cg.own_goals > cg.opponent_goals
          AND cg.is_win <> 1
    ) AS win_flag_missing_for_wins,
    COUNT(*) FILTER (
        WHERE cg.own_goals <= cg.opponent_goals
          AND cg.is_win <> 0
    ) AS win_flag_incorrect_for_non_wins
FROM club_games cg
JOIN model_games g
    ON cg.game_id = g.game_id;

-- ------------------------------------------------------------
-- 4C. Club / opponent IDs must match home-away game IDs
-- ------------------------------------------------------------

SELECT
    COUNT(*) AS total_model_club_game_rows,
    COUNT(*) FILTER (
        WHERE NOT (
            (cg.club_id = g.home_club_id
             AND cg.opponent_id = g.away_club_id)
            OR
            (cg.club_id = g.away_club_id
             AND cg.opponent_id = g.home_club_id)
        )
    ) AS club_game_id_mismatches
FROM club_games cg
JOIN model_games g
    ON cg.game_id = g.game_id;

-- ============================================================
-- 5. MARKET VALUE SANITY CHECKS
-- ============================================================

-- ------------------------------------------------------------
-- 5A. Market value distribution for model players
-- ------------------------------------------------------------

SELECT
    COUNT(*) AS valuation_rows,
    MIN(pv.market_value_in_eur) AS min_market_value,
    MAX(pv.market_value_in_eur) AS max_market_value,
    ROUND(
        QUANTILE_CONT(pv.market_value_in_eur, 0.50),
        0
    ) AS median_market_value,
    ROUND(
        QUANTILE_CONT(pv.market_value_in_eur, 0.95),
        0
    ) AS p95_market_value,
    ROUND(
        QUANTILE_CONT(pv.market_value_in_eur, 0.99),
        0
    ) AS p99_market_value,
    COUNT(*) FILTER (
        WHERE pv.market_value_in_eur < 0
    ) AS negative_market_values,
    COUNT(*) FILTER (
        WHERE pv.market_value_in_eur = 0
    ) AS zero_market_values
FROM player_valuations pv
JOIN model_players mp
    ON pv.player_id = mp.player_id;

-- ------------------------------------------------------------
-- 5B. Highest market values - manual check
-- ------------------------------------------------------------

SELECT
    pv.player_id,
    p.name,
    pv.date,
    pv.market_value_in_eur
FROM player_valuations pv
JOIN model_players mp
    ON pv.player_id = mp.player_id
JOIN players p
    ON pv.player_id = p.player_id
ORDER BY pv.market_value_in_eur DESC
LIMIT 20;

-- ============================================================
-- 6. TRANSFER SANITY CHECKS
-- ============================================================

-- ------------------------------------------------------------
-- 6A. Numeric / logical transfer values
-- ------------------------------------------------------------

SELECT
    COUNT(*) AS transfer_rows,
    COUNT(*) FILTER (
        WHERE t.transfer_fee < 0
    ) AS negative_transfer_fee,
    COUNT(*) FILTER (
        WHERE t.market_value_in_eur < 0
    ) AS negative_market_value,
    COUNT(*) FILTER (
        WHERE t.from_club_id = t.to_club_id
    ) AS same_origin_destination_club,
    COUNT(*) FILTER (
        WHERE t.transfer_date > DATE '2026-07-06'
    ) AS future_scheduled_transfers
FROM transfers t
JOIN model_players mp
    ON t.player_id = mp.player_id;

SELECT
    t.player_id,
    p.name,
    t.transfer_date,
    t.transfer_season,
    t.from_club_id,
    t.from_club_name,
    t.to_club_id,
    t.to_club_name,
    t.transfer_fee,
    t.market_value_in_eur
FROM transfers t
JOIN model_players mp
    ON t.player_id = mp.player_id
JOIN players p
    ON t.player_id = p.player_id
WHERE t.from_club_id = t.to_club_id;

-- ------------------------------------------------------------
-- 6B. Transfer fee distribution
-- Only rows where fee is known
-- ------------------------------------------------------------

SELECT
    COUNT(*) AS known_transfer_fee_rows,
    MIN(transfer_fee) AS min_transfer_fee,
    MAX(transfer_fee) AS max_transfer_fee,
    ROUND(
        QUANTILE_CONT(transfer_fee, 0.50),
        0
    ) AS median_transfer_fee,
    ROUND(
        QUANTILE_CONT(transfer_fee, 0.95),
        0
    ) AS p95_transfer_fee,
    ROUND(
        QUANTILE_CONT(transfer_fee, 0.99),
        0
    ) AS p99_transfer_fee
FROM transfers t
JOIN model_players mp
    ON t.player_id = mp.player_id
WHERE transfer_fee IS NOT NULL;

-- ------------------------------------------------------------
-- 6C. Largest transfer fees - manual check
-- ------------------------------------------------------------

SELECT
    t.player_id,
    p.name,
    t.transfer_date,
    t.from_club_name,
    t.to_club_name,
    t.transfer_fee,
    t.market_value_in_eur
FROM transfers t
JOIN model_players mp
    ON t.player_id = mp.player_id
JOIN players p
    ON t.player_id = p.player_id
WHERE t.transfer_fee IS NOT NULL
ORDER BY t.transfer_fee DESC
LIMIT 20;