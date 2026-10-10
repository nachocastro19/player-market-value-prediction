from pathlib import Path
import duckdb


# Find the project folder automatically
PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DATABASE_PATH = PROCESSED_DIR / "transfermarkt.duckdb"


# These are the CSV files we downloaded
TABLES = [
    "appearances",
    "clubs",
    "club_games",
    "competitions",
    "countries",
    "game_events",
    "games",
    "game_lineups",
    "national_teams",
    "players",
    "player_valuations",
    "transfers",
]


# Create data/processed if it does not already exist
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

print(f"Creating database at: {DATABASE_PATH}")

# Connect to the local DuckDB file
connection = duckdb.connect(str(DATABASE_PATH))

for table_name in TABLES:
    csv_path = RAW_DIR / f"{table_name}.csv"

    if not csv_path.exists():
        raise FileNotFoundError(f"Missing CSV file: {csv_path}")

    print(f"Loading {table_name}.csv...")

    connection.execute(
        f"""
        CREATE OR REPLACE TABLE "{table_name}" AS
        SELECT *
        FROM read_csv_auto(?)
        """,
        [str(csv_path)],
    )

    row_count = connection.execute(
        f'SELECT COUNT(*) FROM "{table_name}"'
    ).fetchone()[0]

    print(f"  Created table {table_name}: {row_count:,} rows")


connection.close()

print("Database creation complete.")