-- ===========================================
-- MODELING DATASET VALIDATION
-- ===========================================

-- ===========================================
-- 1. DATASET SIZE AND GRAIN
-- ===========================================
SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT player_id) AS unique_players,
    COUNT(DISTINCT season) AS seasons
FROM modeling_dataset_v1;

SELECT
    player_id,
    season,
    COUNT(*) AS row_count
FROM modeling_dataset_v1
GROUP BY player_id, season
HAVING COUNT(*) > 1
ORDER BY row_count DESC;

-- ===========================================
-- 2. SEASON COVERAGE
-- ===========================================
SELECT
    season,
    COUNT(*) AS player_seasons,
    COUNT(DISTINCT player_id) AS unique_players
FROM modeling_dataset_v1
GROUP BY season
ORDER BY season;

-- ===========================================
-- 3. CRITICAL MISSING VALUES
-- ===========================================

SELECT
    COUNT(*) AS total_rows,
    COUNT(*) FILTER (
        WHERE target_market_value_in_eur IS NULL
    ) AS missing_target,
    COUNT(*) FILTER (
        WHERE age_at_valuation IS NULL
    ) AS missing_age,
    COUNT(*) FILTER (
        WHERE position IS NULL
    ) AS missing_position,
    COUNT(*) FILTER (
        WHERE sub_position IS NULL
    ) AS missing_sub_position,
    COUNT(*) FILTER (
        WHERE foot IS NULL
    ) AS missing_foot,
    COUNT(*) FILTER (
        WHERE height_in_cm IS NULL
    ) AS missing_height,
    COUNT(*) FILTER (
        WHERE primary_club_id IS NULL
    ) AS missing_primary_club,
    COUNT(*) FILTER (
        WHERE competition_id IS NULL
    ) AS missing_competition,
    COUNT(*) FILTER (
        WHERE total_minutes_played IS NULL
    ) AS missing_minutes
FROM modeling_dataset_v1;

SELECT
    COUNT(*) AS total_rows,
    COUNT(*) FILTER (
        WHERE previous_market_value_in_eur IS NULL
    ) AS missing_previous_market_value,
    COUNT(*) FILTER (
        WHERE days_since_previous_valuation IS NULL
    ) AS missing_previous_valuation_days,
    COUNT(*) FILTER (
        WHERE days_since_last_transfer IS NULL
    ) AS missing_days_since_transfer,
    COUNT(*) FILTER (
        WHERE has_previous_transfer = 0
    ) AS no_previous_transfer
FROM modeling_dataset_v1;

-- ===========================================
-- 4. HISTORICAL VALUATION CHECKS
-- ===========================================

SELECT
    COUNT(*) AS total_rows,
    COUNT(*) FILTER (
        WHERE previous_market_value_in_eur IS NOT NULL
    ) AS with_previous_valuation,
    COUNT(*) FILTER (
        WHERE previous_market_value_in_eur IS NULL
    ) AS without_previous_valuation,
    ROUND(
        COUNT(*) FILTER (
            WHERE previous_market_value_in_eur IS NOT NULL
        ) * 100.0 / COUNT(*),
        2
    ) AS previous_valuation_coverage_pct
FROM modeling_dataset_v1;

SELECT *
FROM modeling_dataset_v1
WHERE
    previous_market_value_in_eur < 0
    OR days_since_previous_valuation <= 0;


-- ===========================================
-- 5. TRANSFER FEATURE CHECKS
-- ===========================================

SELECT
    COUNT(*) AS total_rows,
    COUNT(*) FILTER (
        WHERE has_previous_transfer = 1
    ) AS with_previous_transfer,
    COUNT(*) FILTER (
        WHERE has_previous_transfer = 0
    ) AS without_previous_transfer,
    COUNT(*) FILTER (
        WHERE transfers_during_season > 0
    ) AS transferred_during_season
FROM modeling_dataset_v1;

SELECT *
FROM modeling_dataset_v1
WHERE -- Check for inconsistencies
    (has_previous_transfer = 0 AND total_previous_transfers > 0)
    OR
    (has_previous_transfer = 1 AND total_previous_transfers = 0)
    OR
    (total_previous_transfers = 0 AND days_since_last_transfer IS NOT NULL)
    OR
    (total_previous_transfers > 0 AND days_since_last_transfer IS NULL);

-- ===========================================
-- 6. CLUB CHANGES
-- ===========================================

SELECT
    clubs_played_for_season,
    COUNT(*) AS player_seasons,
    ROUND(
        COUNT(*) * 100.0 /
        SUM(COUNT(*)) OVER (),
        2
    ) AS percentage
FROM modeling_dataset_v1
GROUP BY clubs_played_for_season
ORDER BY clubs_played_for_season;


-- ===========================================
-- 7. NUMERICAL SANITY CHECKS
-- ===========================================

SELECT
    MIN(age_at_valuation) AS min_age,
    MAX(age_at_valuation) AS max_age,
    MIN(height_in_cm) AS min_height,
    MAX(height_in_cm) AS max_height,
    MIN(total_minutes_played) AS min_minutes,
    MAX(total_minutes_played) AS max_minutes,
    MIN(total_games_played_season) AS min_games,
    MAX(total_games_played_season) AS max_games,
    MIN(total_goals) AS min_goals,
    MAX(total_goals) AS max_goals,
    MIN(target_market_value_in_eur) AS min_target_value,
    MAX(target_market_value_in_eur) AS max_target_value
FROM modeling_dataset_v1;

SELECT
    MIN(player_game_participation_rate) AS min_rate,
    MAX(player_game_participation_rate) AS max_rate,
    AVG(player_game_participation_rate) AS avg_rate,
    COUNT(*) FILTER (
        WHERE player_game_participation_rate > 1
    ) AS rates_above_one
FROM modeling_dataset_v1;

SELECT
    season,
    player_id,
    name,
    primary_club_id,
    clubs_played_for_season,
    total_games_played_season,
    club_games_played,
    player_game_participation_rate
FROM modeling_dataset_v1
WHERE player_game_participation_rate > 1
ORDER BY player_game_participation_rate DESC;