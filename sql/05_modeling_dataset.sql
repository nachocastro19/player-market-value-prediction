-- ===========================================
-- MODELING DATASET
-- ===========================================
CREATE OR REPLACE TEMP VIEW modeling_dataset_v1 AS
WITH model_games AS (
SELECT *
FROM games
WHERE season BETWEEN 2020 AND 2025
  AND competition_id IN (
      'GB1', -- Premier League (ENGLAND)
      'ES1', -- LaLiga (SPAIN)
      'IT1', -- Serie A (ITALY)
      'L1',  -- Bundesliga (GERMANY)
      'FR1'  -- Ligue 1 (FRANCE)
  )),
player_model_population AS ( -- All players that have made a single appearance on the TOP 5 Leagues in the season context (2020-2025)
	SELECT DISTINCT
        mg.season,
        a.player_id
    FROM model_games mg
    JOIN appearances a
        ON a.game_id = mg.game_id
    WHERE a.player_id IS NOT NULL
),
player_characteristics AS (
	SELECT
	pmp.season,
	pmp.player_id,
	p.name,
	p.player_code,
	p.date_of_birth, -- to calculate age per season
	p.position,
	p.sub_position,
	p.foot,
	p.height_in_cm
	FROM player_model_population pmp
	LEFT JOIN players p
	ON p.player_id = pmp.player_id
),
appearances_per_season AS ( 
-- A min of 900 minutes played (equivalent to 10 full games) is required to qualify for the x90 min rates
    SELECT
        mg.season,
        a.player_id,
        SUM(a.yellow_cards) AS total_yellow_cards,
        CASE
            WHEN SUM(a.minutes_played) >= 900
            THEN ROUND(
                SUM(a.yellow_cards) * 90.0
                / NULLIF(SUM(a.minutes_played), 0),
                5
            )
            ELSE NULL
        END AS yellow_cards_per_90_min,
        SUM(a.red_cards) AS total_red_cards,
        CASE
            WHEN SUM(a.minutes_played) >= 900
            THEN ROUND(
                SUM(a.red_cards) * 90.0
                / NULLIF(SUM(a.minutes_played), 0),
                5
            )
            ELSE NULL
        END AS red_cards_per_90_min,
        SUM(a.goals) AS total_goals,
        CASE
            WHEN SUM(a.minutes_played) >= 900
            THEN ROUND(
                SUM(a.goals) * 90.0
                / NULLIF(SUM(a.minutes_played), 0),
                3
            )
            ELSE NULL
        END AS goals_per_90_min,
        SUM(a.assists) AS total_assists,
        CASE
            WHEN SUM(a.minutes_played) >= 900
            THEN ROUND(
                SUM(a.assists) * 90.0
                / NULLIF(SUM(a.minutes_played), 0),
                3
            )
            ELSE NULL
        END AS assists_per_90_min,
        CASE
            WHEN SUM(a.minutes_played) >= 900
            THEN ROUND(
                (SUM(a.assists) + SUM(a.goals)) * 90.0
                / NULLIF(SUM(a.minutes_played), 0),
                3
            )
            ELSE NULL
        END AS goal_contributions_per_90_min,
        COUNT(*) FILTER (
            WHERE cg.opponent_goals = 0
              AND a.minutes_played > 0
        ) AS total_clean_sheets,
        ROUND(
            COUNT(*) FILTER (
                WHERE cg.opponent_goals = 0
                  AND a.minutes_played > 0
            ) * 1.0
            / NULLIF(COUNT(DISTINCT a.game_id), 0),
            3
        ) AS clean_sheet_rate,
        SUM(a.minutes_played) AS total_minutes_played,
        COUNT(DISTINCT a.game_id) AS total_games_played_season
    FROM model_games mg
    JOIN appearances a
        ON a.game_id = mg.game_id
    LEFT JOIN club_games cg
        ON cg.game_id = mg.game_id
        AND cg.club_id = a.player_club_id
    GROUP BY
        mg.season,
        a.player_id
),
club_performance AS (
	SELECT
	mg.season,
	cg.club_id,
	SUM(cg.own_goals) AS club_goals_scored,
	SUM(cg.opponent_goals) AS club_goals_conceded,
	COUNT(*) FILTER (WHERE cg.own_goals > cg.opponent_goals)  AS wins,
    COUNT(*) FILTER (WHERE cg.own_goals = cg.opponent_goals)  AS draws,
    COUNT(*) FILTER (WHERE cg.own_goals < cg.opponent_goals)  AS losses,
    COUNT(*) AS number_of_games,
    SUM(CASE
        WHEN cg.own_goals > cg.opponent_goals THEN 3
        WHEN cg.own_goals = cg.opponent_goals THEN 1
        ELSE 0
    END) AS points,
    ROUND(SUM(CASE
        WHEN cg.own_goals > cg.opponent_goals THEN 3.0
        WHEN cg.own_goals = cg.opponent_goals THEN 1.0
        ELSE 0.0
    END) / COUNT(*),2) AS avg_points_per_game
	FROM model_games mg
	LEFT JOIN club_games cg
	ON cg.game_id = mg.game_id
	GROUP BY mg.season, cg.club_id
),
end_of_season_valuations_ranked AS (
    SELECT
    pv.player_id,
    YEAR(pv.date) - 1 AS season,
    pv.date AS valuation_date,
    pv.market_value_in_eur,
    ROW_NUMBER() OVER (
        PARTITION BY
            pv.player_id,
            YEAR(pv.date) - 1
        ORDER BY pv.date DESC
    ) AS rn
    FROM player_valuations pv
    WHERE MONTH(pv.date) IN (5,6)
      AND YEAR(pv.date) BETWEEN 2021 AND 2026
),
end_of_season_valuations AS (
SELECT
    player_id,
    season,
    valuation_date,
    market_value_in_eur AS target_market_value_in_eur
FROM end_of_season_valuations_ranked
WHERE rn = 1
),
player_club_minutes AS (
    SELECT
        mg.season,
        a.player_id,
        a.player_club_id AS club_id,
        mg.competition_id,
        SUM(a.minutes_played) AS minutes_for_club
    FROM model_games mg
    JOIN appearances a
        ON a.game_id = mg.game_id
    WHERE a.player_club_id IS NOT NULL
    GROUP BY
        mg.season,
        a.player_id,
        a.player_club_id,
        mg.competition_id
),
player_primary_club_ranked AS (
    SELECT
        season,
        player_id,
        club_id,
        competition_id,
        minutes_for_club,
        ROW_NUMBER() OVER (
            PARTITION BY season, player_id
            ORDER BY minutes_for_club DESC
        ) AS rn,
        COUNT(*) OVER (
            PARTITION BY season, player_id
        ) AS clubs_played_for_season
    FROM player_club_minutes
),
player_primary_club AS (
    SELECT
        season,
        player_id,
        club_id,
        competition_id,
        minutes_for_club,
        clubs_played_for_season
    FROM player_primary_club_ranked
    WHERE rn = 1
),
season_dates AS (
    SELECT
        season,
        MIN(date) AS season_start_date,
        MAX(date) AS season_end_date
    FROM model_games
    GROUP BY season
),
transfer_features AS (
    SELECT
        pmp.season,
        pmp.player_id,
        COUNT(t.transfer_date) FILTER (
            WHERE t.transfer_date < eosv.valuation_date
        ) AS total_previous_transfers,
        COUNT(t.transfer_date) FILTER (
            WHERE t.transfer_date >= sd.season_start_date
              AND t.transfer_date < eosv.valuation_date
        ) AS transfers_during_season,
        MAX(t.transfer_date) FILTER (
            WHERE t.transfer_date < eosv.valuation_date
        ) AS last_transfer_date
    FROM player_model_population pmp
    JOIN end_of_season_valuations eosv
        ON eosv.player_id = pmp.player_id
        AND eosv.season = pmp.season
    JOIN season_dates sd
        ON sd.season = pmp.season
    LEFT JOIN transfers t
        ON t.player_id = pmp.player_id
    GROUP BY
        pmp.season,
        pmp.player_id
),
historical_valuations_ranked AS (
    SELECT
        pmp.season,
        pmp.player_id,
        eosv.valuation_date AS target_valuation_date,
        pv.date AS previous_valuation_date,
        pv.market_value_in_eur AS previous_market_value_in_eur,
        ROW_NUMBER() OVER (
            PARTITION BY
                pmp.season,
                pmp.player_id
            ORDER BY pv.date DESC
        ) AS rn
    FROM player_model_population pmp
    JOIN end_of_season_valuations eosv
        ON eosv.player_id = pmp.player_id
        AND eosv.season = pmp.season
    LEFT JOIN player_valuations pv
        ON pv.player_id = pmp.player_id
    AND pv.date <
        MAKE_DATE(
            YEAR(eosv.valuation_date),
            5,
            1) -- Considering historical valuation anything before the first of May of the target year
),
historical_valuation_features AS (
    SELECT
        season,
        player_id,
        previous_valuation_date,
        previous_market_value_in_eur,
        DATE_DIFF(
            'day',
            previous_valuation_date,
            target_valuation_date
        ) AS days_since_previous_valuation
    FROM historical_valuations_ranked
    WHERE rn = 1
),
modeling_dataset as (
SELECT
    -- ===========================================
    -- IDENTIFIERS
    -- ===========================================
    pc.season,
    pc.player_id,
    pc.name,
    pc.player_code,
    -- ===========================================
    -- PLAYER CHARACTERISTICS
    -- ===========================================
    DATE_PART('year',AGE(eosv.valuation_date, pc.date_of_birth)) AS age_at_valuation,
    pc.position,
    pc.sub_position,
    pc.foot,
    pc.height_in_cm,
    -- ===========================================
    -- PLAYER PERFORMANCE
    -- ===========================================
    aps.total_games_played_season,
    aps.total_minutes_played,
    aps.total_goals,
    aps.goals_per_90_min,
    aps.total_assists,
    aps.assists_per_90_min,
    aps.goal_contributions_per_90_min,
    aps.total_yellow_cards,
    aps.yellow_cards_per_90_min,
    aps.total_red_cards,
    aps.red_cards_per_90_min,
    aps.total_clean_sheets,
	aps.clean_sheet_rate,
    -- ===========================================
    -- CLUB / COMPETITION CONTEXT
    -- ===========================================
    ppc.club_id AS primary_club_id,
    ppc.competition_id,
    ppc.clubs_played_for_season,
    cp.club_goals_scored,
    cp.club_goals_conceded,
    cp.wins,
    cp.draws,
    cp.losses,
    cp.number_of_games AS club_games_played,
    cp.points,
    cp.avg_points_per_game,
    -- Player participation relative to club games
    ROUND(aps.total_games_played_season * 1.0 / NULLIF(cp.number_of_games, 0),3) AS player_game_participation_rate,
    -- ===========================================
    -- TRANSFERS & HISTORICAL VALUE
    -- ===========================================
	hvf.previous_market_value_in_eur,
	hvf.days_since_previous_valuation,
	tf.total_previous_transfers,
	tf.transfers_during_season,
	CASE
	    WHEN tf.last_transfer_date IS NULL THEN 0
	    ELSE 1
	END AS has_previous_transfer,
	DATE_DIFF(
	    'day',
	    tf.last_transfer_date,
	    eosv.valuation_date
	) AS days_since_last_transfer,
    -- ===========================================
    -- TARGET
    -- ===========================================
    eosv.valuation_date,
    eosv.target_market_value_in_eur
FROM player_characteristics pc
JOIN appearances_per_season aps
    ON aps.player_id = pc.player_id
    AND aps.season = pc.season
LEFT JOIN player_primary_club ppc
    ON ppc.player_id = pc.player_id
    AND ppc.season = pc.season
LEFT JOIN club_performance cp
    ON cp.club_id = ppc.club_id
    AND cp.season = ppc.season
JOIN end_of_season_valuations eosv
    ON eosv.player_id = pc.player_id
    AND eosv.season = pc.season
LEFT JOIN historical_valuation_features hvf
ON hvf.player_id = pc.player_id
AND hvf.season = pc.season
LEFT JOIN transfer_features tf
ON tf.player_id = pc.player_id
AND tf.season = pc.season
ORDER BY
    pc.season,
    pc.player_id
)
SELECT * FROM modeling_dataset;

SELECT * FROM modeling_dataset_v1