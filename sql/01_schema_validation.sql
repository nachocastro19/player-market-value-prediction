-- =====================================================================
-- 01_SCHEMA_VALIDATION.SQL
-- player_market_value_prediction
--
-- Context: All data coming from https://www.kaggle.com/datasets/davidcariboo/player-scores. 
-- Created DuckDB local database with them for inspection on SQL client
--
-- Purpose:
--   1. Inspect source schema
--   2. Validate candidate primary keys
--   3. Validate candidate composite keys
--   4. Check foreign-key / referential integrity
--   5. Distinguish NULL foreign keys from orphan foreign keys
--   6. Inspect the most important orphan entities
-- =====================================================================


-- =====================================================================
-- 1. SCHEMA INSPECTION
-- =====================================================================

SELECT
    table_name,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_catalog = 'transfermarkt'
  AND table_schema = 'main'
ORDER BY
    table_name,
    ordinal_position;



-- =====================================================================
-- 2. SIMPLE PRIMARY KEY CANDIDATE VALIDATION
-- =====================================================================
-- For each candidate PK:
--   total_rows should equal unique_ids
--   null_ids should ideally be 0
--   duplicate query should return 0 rows
-- =====================================================================


-- ---------------------------------------------------------------------
-- 2.1 PLAYERS
-- Candidate PK: player_id
-- ---------------------------------------------------------------------

SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT player_id) AS unique_ids,
    COUNT(*) FILTER (WHERE player_id IS NULL) AS null_ids
FROM players;

SELECT
    player_id,
    COUNT(*) AS n
FROM players
GROUP BY player_id
HAVING COUNT(*) > 1
ORDER BY n DESC;



-- ---------------------------------------------------------------------
-- 2.2 CLUBS
-- Candidate PK: club_id
-- ---------------------------------------------------------------------

SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT club_id) AS unique_ids,
    COUNT(*) FILTER (WHERE club_id IS NULL) AS null_ids
FROM clubs;

SELECT
    club_id,
    COUNT(*) AS n
FROM clubs
GROUP BY club_id
HAVING COUNT(*) > 1
ORDER BY n DESC;



-- ---------------------------------------------------------------------
-- 2.3 GAMES
-- Candidate PK: game_id
-- ---------------------------------------------------------------------

SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT game_id) AS unique_ids,
    COUNT(*) FILTER (WHERE game_id IS NULL) AS null_ids
FROM games;

SELECT
    game_id,
    COUNT(*) AS n
FROM games
GROUP BY game_id
HAVING COUNT(*) > 1
ORDER BY n DESC;



-- ---------------------------------------------------------------------
-- 2.4 APPEARANCES
-- Candidate PK: appearance_id
-- ---------------------------------------------------------------------

SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT appearance_id) AS unique_ids,
    COUNT(*) FILTER (WHERE appearance_id IS NULL) AS null_ids
FROM appearances;

SELECT
    appearance_id,
    COUNT(*) AS n
FROM appearances
GROUP BY appearance_id
HAVING COUNT(*) > 1
ORDER BY n DESC;



-- ---------------------------------------------------------------------
-- 2.5 GAME_LINEUPS
-- Candidate PK: game_lineups_id
-- ---------------------------------------------------------------------

SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT game_lineups_id) AS unique_ids,
    COUNT(*) FILTER (WHERE game_lineups_id IS NULL) AS null_ids
FROM game_lineups;

SELECT
    game_lineups_id,
    COUNT(*) AS n
FROM game_lineups
GROUP BY game_lineups_id
HAVING COUNT(*) > 1
ORDER BY n DESC;



-- =====================================================================
-- 3. COMPOSITE KEY CANDIDATE VALIDATION
-- =====================================================================


-- ---------------------------------------------------------------------
-- 3.1 PLAYER_VALUATIONS
-- Candidate PK: (player_id, date)
-- ---------------------------------------------------------------------

SELECT
    COUNT(*) AS total_rows,
    COUNT(*) FILTER (
        WHERE player_id IS NULL
           OR date IS NULL
    ) AS rows_with_null_key_component
FROM player_valuations;


SELECT
    player_id,
    date,
    COUNT(*) AS n
FROM player_valuations
GROUP BY
    player_id,
    date
HAVING COUNT(*) > 1
ORDER BY n DESC;



-- ---------------------------------------------------------------------
-- 3.2 CLUB_GAMES
-- Candidate PK: (game_id, club_id)
-- ---------------------------------------------------------------------

SELECT
    COUNT(*) AS total_rows,
    COUNT(*) FILTER (
        WHERE game_id IS NULL
           OR club_id IS NULL
    ) AS rows_with_null_key_component
FROM club_games;


SELECT
    game_id,
    club_id,
    COUNT(*) AS n
FROM club_games
GROUP BY
    game_id,
    club_id
HAVING COUNT(*) > 1
ORDER BY n DESC;



-- ---------------------------------------------------------------------
-- 3.3 TRANSFERS
-- Candidate PK:
-- (player_id, transfer_date, from_club_id, to_club_id)
--
-- NOTE:
-- If from_club_id or to_club_id can be NULL, this may not be suitable
-- as a strict relational PK even if the combination is unique.
-- ---------------------------------------------------------------------

SELECT
    COUNT(*) AS total_rows,
    COUNT(*) FILTER (
        WHERE player_id IS NULL
           OR transfer_date IS NULL
           OR from_club_id IS NULL
           OR to_club_id IS NULL
    ) AS rows_with_null_key_component
FROM transfers;


SELECT
    player_id,
    transfer_date,
    from_club_id,
    to_club_id,
    COUNT(*) AS n
FROM transfers
GROUP BY
    player_id,
    transfer_date,
    from_club_id,
    to_club_id
HAVING COUNT(*) > 1
ORDER BY n DESC;



-- =====================================================================
-- 4. REFERENTIAL INTEGRITY
-- =====================================================================
--
-- IMPORTANT:
--
-- null_fk_rows:
--      FK itself is NULL.
--
-- orphan_rows:
--      FK has a value, but no matching parent row exists.
--
-- orphan_ids:
--      Number of DISTINCT missing entities.
--
-- orphan_pct:
--      Percentage of NON-NULL FK records that cannot be matched.
-- =====================================================================



-- =====================================================================
-- 4.1 PLAYERS -> CLUBS
-- players.current_club_id -> clubs.club_id
-- =====================================================================

SELECT
    COUNT(*) AS total_rows,
    COUNT(*) FILTER (
        WHERE p.current_club_id IS NULL
    ) AS null_fk_rows,
    COUNT(*) FILTER (
        WHERE p.current_club_id IS NOT NULL
    ) AS rows_with_fk,
    COUNT(*) FILTER (
        WHERE p.current_club_id IS NOT NULL
          AND c.club_id IS NULL
    ) AS orphan_rows,
    COUNT(DISTINCT p.current_club_id) FILTER (
        WHERE p.current_club_id IS NOT NULL
          AND c.club_id IS NULL
    ) AS orphan_ids,
    ROUND(
        100.0 *
        COUNT(*) FILTER (
            WHERE p.current_club_id IS NOT NULL
              AND c.club_id IS NULL
        )
        / NULLIF(
            COUNT(*) FILTER (
                WHERE p.current_club_id IS NOT NULL
            ),
            0
        ),
        2
    ) AS orphan_pct
FROM players p
LEFT JOIN clubs c
    ON p.current_club_id = c.club_id;



-- =====================================================================
-- 4.2 APPEARANCES -> PLAYERS
-- appearances.player_id -> players.player_id
-- =====================================================================

SELECT
    COUNT(*) AS total_rows,
    COUNT(*) FILTER (
        WHERE a.player_id IS NULL
    ) AS null_fk_rows,
    COUNT(*) FILTER (
        WHERE a.player_id IS NOT NULL
    ) AS rows_with_fk,
    COUNT(*) FILTER (
        WHERE a.player_id IS NOT NULL
          AND p.player_id IS NULL
    ) AS orphan_rows,
    COUNT(DISTINCT a.player_id) FILTER (
        WHERE a.player_id IS NOT NULL
          AND p.player_id IS NULL
    ) AS orphan_ids,
    ROUND(
        100.0 *
        COUNT(*) FILTER (
            WHERE a.player_id IS NOT NULL
              AND p.player_id IS NULL
        )
        / NULLIF(
            COUNT(*) FILTER (
                WHERE a.player_id IS NOT NULL
            ),
            0
        ),
        2
    ) AS orphan_pct
FROM appearances a
LEFT JOIN players p
    ON a.player_id = p.player_id;



-- =====================================================================
-- 4.3 APPEARANCES -> CLUBS
-- appearances.player_club_id -> clubs.club_id
-- =====================================================================

SELECT
    COUNT(*) AS total_rows,
    COUNT(*) FILTER (
        WHERE a.player_club_id IS NULL
    ) AS null_fk_rows,
    COUNT(*) FILTER (
        WHERE a.player_club_id IS NOT NULL
    ) AS rows_with_fk,
    COUNT(*) FILTER (
        WHERE a.player_club_id IS NOT NULL
          AND c.club_id IS NULL
    ) AS orphan_rows,
    COUNT(DISTINCT a.player_club_id) FILTER (
        WHERE a.player_club_id IS NOT NULL
          AND c.club_id IS NULL
    ) AS orphan_ids,
    ROUND(
        100.0 *
        COUNT(*) FILTER (
            WHERE a.player_club_id IS NOT NULL
              AND c.club_id IS NULL
        )
        / NULLIF(
            COUNT(*) FILTER (
                WHERE a.player_club_id IS NOT NULL
            ),
            0
        ),
        2
    ) AS orphan_pct
FROM appearances a
LEFT JOIN clubs c
    ON a.player_club_id = c.club_id;



-- =====================================================================
-- 4.4 APPEARANCES -> GAMES
-- appearances.game_id -> games.game_id
-- =====================================================================

SELECT
    COUNT(*) AS total_rows,
    COUNT(*) FILTER (
        WHERE a.game_id IS NULL
    ) AS null_fk_rows,
    COUNT(*) FILTER (
        WHERE a.game_id IS NOT NULL
    ) AS rows_with_fk,
    COUNT(*) FILTER (
        WHERE a.game_id IS NOT NULL
          AND g.game_id IS NULL
    ) AS orphan_rows,
    COUNT(DISTINCT a.game_id) FILTER (
        WHERE a.game_id IS NOT NULL
          AND g.game_id IS NULL
    ) AS orphan_ids,
    ROUND(
        100.0 *
        COUNT(*) FILTER (
            WHERE a.game_id IS NOT NULL
              AND g.game_id IS NULL
        )
        / NULLIF(
            COUNT(*) FILTER (
                WHERE a.game_id IS NOT NULL
            ),
            0
        ),
        2
    ) AS orphan_pct
FROM appearances a
LEFT JOIN games g
    ON a.game_id = g.game_id;



-- =====================================================================
-- 4.5 APPEARANCES -> COMPETITIONS
-- appearances.competition_id -> competitions.competition_id
-- =====================================================================

SELECT
    COUNT(*) AS total_rows,
    COUNT(*) FILTER (
        WHERE a.competition_id IS NULL
    ) AS null_fk_rows,
    COUNT(*) FILTER (
        WHERE a.competition_id IS NOT NULL
    ) AS rows_with_fk,
    COUNT(*) FILTER (
        WHERE a.competition_id IS NOT NULL
          AND c.competition_id IS NULL
    ) AS orphan_rows,
    COUNT(DISTINCT a.competition_id) FILTER (
        WHERE a.competition_id IS NOT NULL
          AND c.competition_id IS NULL
    ) AS orphan_ids,
    ROUND(
        100.0 *
        COUNT(*) FILTER (
            WHERE a.competition_id IS NOT NULL
              AND c.competition_id IS NULL
        )
        / NULLIF(
            COUNT(*) FILTER (
                WHERE a.competition_id IS NOT NULL
            ),
            0
        ),
        2
    ) AS orphan_pct
FROM appearances a
LEFT JOIN competitions c
    ON a.competition_id = c.competition_id;



-- =====================================================================
-- 4.6 TRANSFERS -> PLAYERS
-- transfers.player_id -> players.player_id
-- =====================================================================

SELECT
    COUNT(*) AS total_rows,
    COUNT(*) FILTER (
        WHERE t.player_id IS NULL
    ) AS null_fk_rows,
    COUNT(*) FILTER (
        WHERE t.player_id IS NOT NULL
    ) AS rows_with_fk,
    COUNT(*) FILTER (
        WHERE t.player_id IS NOT NULL
          AND p.player_id IS NULL
    ) AS orphan_rows,
    COUNT(DISTINCT t.player_id) FILTER (
        WHERE t.player_id IS NOT NULL
          AND p.player_id IS NULL
    ) AS orphan_ids,
    ROUND(
        100.0 *
        COUNT(*) FILTER (
            WHERE t.player_id IS NOT NULL
              AND p.player_id IS NULL
        )
        / NULLIF(
            COUNT(*) FILTER (
                WHERE t.player_id IS NOT NULL
            ),
            0
        ),
        2
    ) AS orphan_pct
FROM transfers t
LEFT JOIN players p
    ON t.player_id = p.player_id;



-- =====================================================================
-- 4.7 TRANSFERS -> CLUBS (FROM CLUB)
-- transfers.from_club_id -> clubs.club_id
-- =====================================================================

SELECT
    COUNT(*) AS total_rows,
    COUNT(*) FILTER (
        WHERE t.from_club_id IS NULL
    ) AS null_fk_rows,
    COUNT(*) FILTER (
        WHERE t.from_club_id IS NOT NULL
    ) AS rows_with_fk,
    COUNT(*) FILTER (
        WHERE t.from_club_id IS NOT NULL
          AND c.club_id IS NULL
    ) AS orphan_rows,
    COUNT(DISTINCT t.from_club_id) FILTER (
        WHERE t.from_club_id IS NOT NULL
          AND c.club_id IS NULL
    ) AS orphan_ids,
    ROUND(
        100.0 *
        COUNT(*) FILTER (
            WHERE t.from_club_id IS NOT NULL
              AND c.club_id IS NULL
        )
        / NULLIF(
            COUNT(*) FILTER (
                WHERE t.from_club_id IS NOT NULL
            ),
            0
        ),
        2
    ) AS orphan_pct
FROM transfers t
LEFT JOIN clubs c
    ON t.from_club_id = c.club_id;



-- =====================================================================
-- 4.8 TRANSFERS -> CLUBS (TO CLUB)
-- transfers.to_club_id -> clubs.club_id
-- =====================================================================

SELECT
    COUNT(*) AS total_rows,
    COUNT(*) FILTER (
        WHERE t.to_club_id IS NULL
    ) AS null_fk_rows,
    COUNT(*) FILTER (
        WHERE t.to_club_id IS NOT NULL
    ) AS rows_with_fk,
    COUNT(*) FILTER (
        WHERE t.to_club_id IS NOT NULL
          AND c.club_id IS NULL
    ) AS orphan_rows,
    COUNT(DISTINCT t.to_club_id) FILTER (
        WHERE t.to_club_id IS NOT NULL
          AND c.club_id IS NULL
    ) AS orphan_ids,
    ROUND(
        100.0 *
        COUNT(*) FILTER (
            WHERE t.to_club_id IS NOT NULL
              AND c.club_id IS NULL
        )
        / NULLIF(
            COUNT(*) FILTER (
                WHERE t.to_club_id IS NOT NULL
            ),
            0
        ),
        2
    ) AS orphan_pct
FROM transfers t
LEFT JOIN clubs c
    ON t.to_club_id = c.club_id;



-- =====================================================================
-- 4.9 PLAYER_VALUATIONS -> PLAYERS
-- player_valuations.player_id -> players.player_id
-- =====================================================================

SELECT
    COUNT(*) AS total_rows,
    COUNT(*) FILTER (
        WHERE pv.player_id IS NULL
    ) AS null_fk_rows,
    COUNT(*) FILTER (
        WHERE pv.player_id IS NOT NULL
    ) AS rows_with_fk,
    COUNT(*) FILTER (
        WHERE pv.player_id IS NOT NULL
          AND p.player_id IS NULL
    ) AS orphan_rows,
    COUNT(DISTINCT pv.player_id) FILTER (
        WHERE pv.player_id IS NOT NULL
          AND p.player_id IS NULL
    ) AS orphan_ids,
    ROUND(
        100.0 *
        COUNT(*) FILTER (
            WHERE pv.player_id IS NOT NULL
              AND p.player_id IS NULL
        )
        / NULLIF(
            COUNT(*) FILTER (
                WHERE pv.player_id IS NOT NULL
            ),
            0
        ),
        2
    ) AS orphan_pct
FROM player_valuations pv
LEFT JOIN players p
    ON pv.player_id = p.player_id;



-- =====================================================================
-- 4.10 PLAYER_VALUATIONS -> CLUBS
-- player_valuations.current_club_id -> clubs.club_id
-- =====================================================================

SELECT
    COUNT(*) AS total_rows,
    COUNT(*) FILTER (
        WHERE pv.current_club_id IS NULL
    ) AS null_fk_rows,
    COUNT(*) FILTER (
        WHERE pv.current_club_id IS NOT NULL
    ) AS rows_with_fk,
    COUNT(*) FILTER (
        WHERE pv.current_club_id IS NOT NULL
          AND c.club_id IS NULL
    ) AS orphan_rows,
    COUNT(DISTINCT pv.current_club_id) FILTER (
        WHERE pv.current_club_id IS NOT NULL
          AND c.club_id IS NULL
    ) AS orphan_ids,
    ROUND(
        100.0 *
        COUNT(*) FILTER (
            WHERE pv.current_club_id IS NOT NULL
              AND c.club_id IS NULL
        )
        / NULLIF(
            COUNT(*) FILTER (
                WHERE pv.current_club_id IS NOT NULL
            ),
            0
        ),
        2
    ) AS orphan_pct
FROM player_valuations pv
LEFT JOIN clubs c
    ON pv.current_club_id = c.club_id;



-- =====================================================================
-- 4.11 GAME_LINEUPS -> PLAYERS
-- game_lineups.player_id -> players.player_id
-- =====================================================================

SELECT
    COUNT(*) AS total_rows,
    COUNT(*) FILTER (
        WHERE gl.player_id IS NULL
    ) AS null_fk_rows,
    COUNT(*) FILTER (
        WHERE gl.player_id IS NOT NULL
    ) AS rows_with_fk,
    COUNT(*) FILTER (
        WHERE gl.player_id IS NOT NULL
          AND p.player_id IS NULL
    ) AS orphan_rows,
    COUNT(DISTINCT gl.player_id) FILTER (
        WHERE gl.player_id IS NOT NULL
          AND p.player_id IS NULL
    ) AS orphan_ids,
    ROUND(
        100.0 *
        COUNT(*) FILTER (
            WHERE gl.player_id IS NOT NULL
              AND p.player_id IS NULL
        )
        / NULLIF(
            COUNT(*) FILTER (
                WHERE gl.player_id IS NOT NULL
            ),
            0
        ),
        2
    ) AS orphan_pct
FROM game_lineups gl
LEFT JOIN players p
    ON gl.player_id = p.player_id;



-- =====================================================================
-- 4.12 GAME_LINEUPS -> GAMES
-- game_lineups.game_id -> games.game_id
-- =====================================================================

SELECT
    COUNT(*) AS total_rows,
    COUNT(*) FILTER (
        WHERE gl.game_id IS NULL
    ) AS null_fk_rows,
    COUNT(*) FILTER (
        WHERE gl.game_id IS NOT NULL
    ) AS rows_with_fk,
    COUNT(*) FILTER (
        WHERE gl.game_id IS NOT NULL
          AND g.game_id IS NULL
    ) AS orphan_rows,
    COUNT(DISTINCT gl.game_id) FILTER (
        WHERE gl.game_id IS NOT NULL
          AND g.game_id IS NULL
    ) AS orphan_ids,
    ROUND(
        100.0 *
        COUNT(*) FILTER (
            WHERE gl.game_id IS NOT NULL
              AND g.game_id IS NULL
        )
        / NULLIF(
            COUNT(*) FILTER (
                WHERE gl.game_id IS NOT NULL
            ),
            0
        ),
        2
    ) AS orphan_pct
FROM game_lineups gl
LEFT JOIN games g
    ON gl.game_id = g.game_id;



-- =====================================================================
-- 4.13 GAME_LINEUPS -> CLUBS
-- game_lineups.club_id -> clubs.club_id
-- =====================================================================

SELECT
    COUNT(*) AS total_rows,
    COUNT(*) FILTER (
        WHERE gl.club_id IS NULL
    ) AS null_fk_rows,
    COUNT(*) FILTER (
        WHERE gl.club_id IS NOT NULL
    ) AS rows_with_fk,
    COUNT(*) FILTER (
        WHERE gl.club_id IS NOT NULL
          AND c.club_id IS NULL
    ) AS orphan_rows,
    COUNT(DISTINCT gl.club_id) FILTER (
        WHERE gl.club_id IS NOT NULL
          AND c.club_id IS NULL
    ) AS orphan_ids,
    ROUND(
        100.0 *
        COUNT(*) FILTER (
            WHERE gl.club_id IS NOT NULL
              AND c.club_id IS NULL
        )
        / NULLIF(
            COUNT(*) FILTER (
                WHERE gl.club_id IS NOT NULL
            ),
            0
        ),
        2
    ) AS orphan_pct
FROM game_lineups gl
LEFT JOIN clubs c
    ON gl.club_id = c.club_id;



-- =====================================================================
-- 4.14 CLUB_GAMES -> GAMES
-- club_games.game_id -> games.game_id
-- =====================================================================

SELECT
    COUNT(*) AS total_rows,
    COUNT(*) FILTER (
        WHERE cg.game_id IS NULL
    ) AS null_fk_rows,
    COUNT(*) FILTER (
        WHERE cg.game_id IS NOT NULL
    ) AS rows_with_fk,
    COUNT(*) FILTER (
        WHERE cg.game_id IS NOT NULL
          AND g.game_id IS NULL
    ) AS orphan_rows,
    COUNT(DISTINCT cg.game_id) FILTER (
        WHERE cg.game_id IS NOT NULL
          AND g.game_id IS NULL
    ) AS orphan_ids,
    ROUND(
        100.0 *
        COUNT(*) FILTER (
            WHERE cg.game_id IS NOT NULL
              AND g.game_id IS NULL
        )
        / NULLIF(
            COUNT(*) FILTER (
                WHERE cg.game_id IS NOT NULL
            ),
            0
        ),
        2
    ) AS orphan_pct
FROM club_games cg
LEFT JOIN games g
    ON cg.game_id = g.game_id;



-- =====================================================================
-- 4.15 CLUB_GAMES -> CLUBS
-- club_games.club_id -> clubs.club_id
-- =====================================================================

SELECT
    COUNT(*) AS total_rows,
    COUNT(*) FILTER (
        WHERE cg.club_id IS NULL
    ) AS null_fk_rows,
    COUNT(*) FILTER (
        WHERE cg.club_id IS NOT NULL
    ) AS rows_with_fk,
    COUNT(*) FILTER (
        WHERE cg.club_id IS NOT NULL
          AND c.club_id IS NULL
    ) AS orphan_rows,
    COUNT(DISTINCT cg.club_id) FILTER (
        WHERE cg.club_id IS NOT NULL
          AND c.club_id IS NULL
    ) AS orphan_ids,
    ROUND(
        100.0 *
        COUNT(*) FILTER (
            WHERE cg.club_id IS NOT NULL
              AND c.club_id IS NULL
        )
        / NULLIF(
            COUNT(*) FILTER (
                WHERE cg.club_id IS NOT NULL
            ),
            0
        ),
        2
    ) AS orphan_pct
FROM club_games cg
LEFT JOIN clubs c
    ON cg.club_id = c.club_id;



-- =====================================================================
-- 4.16 CLUB_GAMES -> CLUBS (OPPONENT)
-- club_games.opponent_id -> clubs.club_id
-- =====================================================================

SELECT
    COUNT(*) AS total_rows,
    COUNT(*) FILTER (
        WHERE cg.opponent_id IS NULL
    ) AS null_fk_rows,
    COUNT(*) FILTER (
        WHERE cg.opponent_id IS NOT NULL
    ) AS rows_with_fk,
    COUNT(*) FILTER (
        WHERE cg.opponent_id IS NOT NULL
          AND c.club_id IS NULL
    ) AS orphan_rows,
    COUNT(DISTINCT cg.opponent_id) FILTER (
        WHERE cg.opponent_id IS NOT NULL
          AND c.club_id IS NULL
    ) AS orphan_ids,
    ROUND(
        100.0 *
        COUNT(*) FILTER (
            WHERE cg.opponent_id IS NOT NULL
              AND c.club_id IS NULL
        )
        / NULLIF(
            COUNT(*) FILTER (
                WHERE cg.opponent_id IS NOT NULL
            ),
            0
        ),
        2
    ) AS orphan_pct
FROM club_games cg
LEFT JOIN clubs c
    ON cg.opponent_id = c.club_id;



-- =====================================================================
-- 4.17 GAMES -> CLUBS (HOME CLUB)
-- games.home_club_id -> clubs.club_id
-- =====================================================================

SELECT
    COUNT(*) AS total_rows,
    COUNT(*) FILTER (
        WHERE g.home_club_id IS NULL
    ) AS null_fk_rows,
    COUNT(*) FILTER (
        WHERE g.home_club_id IS NOT NULL
    ) AS rows_with_fk,
    COUNT(*) FILTER (
        WHERE g.home_club_id IS NOT NULL
          AND c.club_id IS NULL
    ) AS orphan_rows,
    COUNT(DISTINCT g.home_club_id) FILTER (
        WHERE g.home_club_id IS NOT NULL
          AND c.club_id IS NULL
    ) AS orphan_ids,
    ROUND(
        100.0 *
        COUNT(*) FILTER (
            WHERE g.home_club_id IS NOT NULL
              AND c.club_id IS NULL
        )
        / NULLIF(
            COUNT(*) FILTER (
                WHERE g.home_club_id IS NOT NULL
            ),
            0
        ),
        2
    ) AS orphan_pct
FROM games g
LEFT JOIN clubs c
    ON g.home_club_id = c.club_id;



-- =====================================================================
-- 4.18 GAMES -> CLUBS (AWAY CLUB)
-- games.away_club_id -> clubs.club_id
-- =====================================================================

SELECT
    COUNT(*) AS total_rows,
    COUNT(*) FILTER (
        WHERE g.away_club_id IS NULL
    ) AS null_fk_rows,
    COUNT(*) FILTER (
        WHERE g.away_club_id IS NOT NULL
    ) AS rows_with_fk,
    COUNT(*) FILTER (
        WHERE g.away_club_id IS NOT NULL
          AND c.club_id IS NULL
    ) AS orphan_rows,
    COUNT(DISTINCT g.away_club_id) FILTER (
        WHERE g.away_club_id IS NOT NULL
          AND c.club_id IS NULL
    ) AS orphan_ids,
    ROUND(
        100.0 *
        COUNT(*) FILTER (
            WHERE g.away_club_id IS NOT NULL
              AND c.club_id IS NULL
        )
        / NULLIF(
            COUNT(*) FILTER (
                WHERE g.away_club_id IS NOT NULL
            ),
            0
        ),
        2
    ) AS orphan_pct
FROM games g
LEFT JOIN clubs c
    ON g.away_club_id = c.club_id;



-- =====================================================================
-- 4.19 GAMES -> COMPETITIONS
-- games.competition_id -> competitions.competition_id
-- =====================================================================

SELECT
    COUNT(*) AS total_rows,
    COUNT(*) FILTER (
        WHERE g.competition_id IS NULL
    ) AS null_fk_rows,
    COUNT(*) FILTER (
        WHERE g.competition_id IS NOT NULL
    ) AS rows_with_fk,
    COUNT(*) FILTER (
        WHERE g.competition_id IS NOT NULL
          AND c.competition_id IS NULL
    ) AS orphan_rows,
    COUNT(DISTINCT g.competition_id) FILTER (
        WHERE g.competition_id IS NOT NULL
          AND c.competition_id IS NULL
    ) AS orphan_ids,
    ROUND(
        100.0 *
        COUNT(*) FILTER (
            WHERE g.competition_id IS NOT NULL
              AND c.competition_id IS NULL
        )
        / NULLIF(
            COUNT(*) FILTER (
                WHERE g.competition_id IS NOT NULL
            ),
            0
        ),
        2
    ) AS orphan_pct
FROM games g
LEFT JOIN competitions c
    ON g.competition_id = c.competition_id;



-- =====================================================================
-- 4.20 CLUBS -> COMPETITIONS
-- clubs.domestic_competition_id -> competitions.competition_id
-- =====================================================================

SELECT
    COUNT(*) AS total_rows,
    COUNT(*) FILTER (
        WHERE cl.domestic_competition_id IS NULL
    ) AS null_fk_rows,
    COUNT(*) FILTER (
        WHERE cl.domestic_competition_id IS NOT NULL
    ) AS rows_with_fk,
    COUNT(*) FILTER (
        WHERE cl.domestic_competition_id IS NOT NULL
          AND co.competition_id IS NULL
    ) AS orphan_rows,
    COUNT(DISTINCT cl.domestic_competition_id) FILTER (
        WHERE cl.domestic_competition_id IS NOT NULL
          AND co.competition_id IS NULL
    ) AS orphan_ids,
    ROUND(
        100.0 *
        COUNT(*) FILTER (
            WHERE cl.domestic_competition_id IS NOT NULL
              AND co.competition_id IS NULL
        )
        / NULLIF(
            COUNT(*) FILTER (
                WHERE cl.domestic_competition_id IS NOT NULL
            ),
            0
        ),
        2
    ) AS orphan_pct
FROM clubs cl
LEFT JOIN competitions co
    ON cl.domestic_competition_id = co.competition_id;



-- =====================================================================
-- 5. INSPECT ORPHAN ENTITIES
-- =====================================================================
--
-- These queries help determine whether missing relationships represent:
--   - actual bad data
--   - lower-league clubs
--   - youth/reserve teams
--   - clubs outside dataset scope
--   - players outside players-table coverage
-- =====================================================================


-- ---------------------------------------------------------------------
-- 5.1 Missing clubs referenced by APPEARANCES
-- ---------------------------------------------------------------------

SELECT
    a.player_club_id AS missing_club_id,
    COUNT(*) AS appearance_rows,
    COUNT(DISTINCT a.player_id) AS players,
    COUNT(DISTINCT a.game_id) AS games
FROM appearances a
LEFT JOIN clubs c
    ON a.player_club_id = c.club_id
WHERE a.player_club_id IS NOT NULL
  AND c.club_id IS NULL
GROUP BY a.player_club_id
ORDER BY appearance_rows DESC;

-- Some of them seem to be national teams, validate that
WITH missing_clubs_referenced_by_appearances AS (
	SELECT
	    a.player_club_id AS missing_club_id,
	    COUNT(*) AS appearance_rows,
	    COUNT(DISTINCT a.player_id) AS players,
	    COUNT(DISTINCT a.game_id) AS games
	FROM appearances a
	LEFT JOIN clubs c
	    ON a.player_club_id = c.club_id
	WHERE a.player_club_id IS NOT NULL
	  AND c.club_id IS NULL
	GROUP BY a.player_club_id
	ORDER BY appearance_rows DESC
)
SELECT 
mcrba.missing_club_id,
nt.national_team_id,
CASE 
	WHEN nt.national_team_id IS NOT NULL THEN TRUE
	ELSE FALSE
END AS is_national_team
FROM missing_clubs_referenced_by_appearances mcrba
LEFT JOIN national_teams nt
ON mcrba.missing_club_id = nt.national_team_id;




-- ---------------------------------------------------------------------
-- 5.2 Missing players referenced by APPEARANCES
-- ---------------------------------------------------------------------

SELECT
    a.player_id AS missing_player_id,
    COUNT(*) AS appearance_rows,
    COUNT(DISTINCT a.game_id) AS games
FROM appearances a
LEFT JOIN players p
    ON a.player_id = p.player_id
WHERE a.player_id IS NOT NULL
  AND p.player_id IS NULL
GROUP BY a.player_id
ORDER BY appearance_rows DESC;



-- ---------------------------------------------------------------------
-- 5.3 Missing players referenced by GAME_LINEUPS
-- ---------------------------------------------------------------------

SELECT
    gl.player_id AS missing_player_id,
    MAX(gl.player_name) AS player_name,
    COUNT(*) AS lineup_rows,
    COUNT(DISTINCT gl.game_id) AS games
FROM game_lineups gl
LEFT JOIN players p
    ON gl.player_id = p.player_id
WHERE gl.player_id IS NOT NULL
  AND p.player_id IS NULL
GROUP BY gl.player_id
ORDER BY lineup_rows DESC;



-- ---------------------------------------------------------------------
-- 5.4 Missing origin clubs referenced by TRANSFERS
-- ---------------------------------------------------------------------

SELECT
    t.from_club_id AS missing_club_id,
    MAX(t.from_club_name) AS club_name,
    COUNT(*) AS transfer_rows,
    COUNT(DISTINCT t.player_id) AS players
FROM transfers t
LEFT JOIN clubs c
    ON t.from_club_id = c.club_id
WHERE t.from_club_id IS NOT NULL
  AND c.club_id IS NULL
GROUP BY t.from_club_id
ORDER BY transfer_rows DESC;



-- ---------------------------------------------------------------------
-- 5.5 Missing destination clubs referenced by TRANSFERS
-- ---------------------------------------------------------------------

SELECT
    t.to_club_id AS missing_club_id,
    MAX(t.to_club_name) AS club_name,
    COUNT(*) AS transfer_rows,
    COUNT(DISTINCT t.player_id) AS players
FROM transfers t
LEFT JOIN clubs c
    ON t.to_club_id = c.club_id
WHERE t.to_club_id IS NOT NULL
  AND c.club_id IS NULL
GROUP BY t.to_club_id
ORDER BY transfer_rows DESC;



-- ---------------------------------------------------------------------
-- 5.6 Missing clubs referenced by CLUB_GAMES
-- ---------------------------------------------------------------------

SELECT
    cg.club_id AS missing_club_id,
    COUNT(*) AS club_game_rows,
    COUNT(DISTINCT cg.game_id) AS games
FROM club_games cg
LEFT JOIN clubs c
    ON cg.club_id = c.club_id
WHERE cg.club_id IS NOT NULL
  AND c.club_id IS NULL
GROUP BY cg.club_id
ORDER BY club_game_rows DESC;

-- Probaly some are national_teams, validate
WITH missing_clubs_referenced_by_club_games AS (
	SELECT
    cg.club_id AS missing_club_id,
    COUNT(*) AS club_game_rows,
    COUNT(DISTINCT cg.game_id) AS games
	FROM club_games cg
	LEFT JOIN clubs c
	    ON cg.club_id = c.club_id
	WHERE cg.club_id IS NOT NULL
	  AND c.club_id IS NULL
	GROUP BY cg.club_id
	ORDER BY club_game_rows DESC
)
SELECT 
mcrbcg.missing_club_id,
nt.national_team_id,
CASE 
	WHEN nt.national_team_id IS NOT NULL THEN TRUE
	ELSE FALSE
END AS is_national_team
FROM missing_clubs_referenced_by_club_games mcrbcg
LEFT JOIN national_teams nt
ON mcrbcg.missing_club_id = nt.national_team_id;



-- =====================================================================
-- 6. BASIC TABLE SIZE OVERVIEW
-- =====================================================================
-- Useful for understanding the relative scale of each dataset.
-- =====================================================================

SELECT 'players' AS table_name, COUNT(*) AS row_count FROM players
UNION ALL
SELECT 'clubs', COUNT(*) FROM clubs
UNION ALL
SELECT 'competitions', COUNT(*) FROM competitions
UNION ALL
SELECT 'games', COUNT(*) FROM games
UNION ALL
SELECT 'club_games', COUNT(*) FROM club_games
UNION ALL
SELECT 'appearances', COUNT(*) FROM appearances
UNION ALL
SELECT 'game_lineups', COUNT(*) FROM game_lineups
UNION ALL
SELECT 'game_events', COUNT(*) FROM game_events
UNION ALL
SELECT 'transfers', COUNT(*) FROM transfers
UNION ALL
SELECT 'player_valuations', COUNT(*) FROM player_valuations
UNION ALL
SELECT 'countries', COUNT(*) FROM countries
UNION ALL
SELECT 'national_teams', COUNT(*) FROM national_teams
ORDER BY row_count DESC;
