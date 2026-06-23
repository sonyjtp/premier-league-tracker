"""
One-time migration: adds new columns to existing tables and creates new tables.
Run once from the backend/ directory after updating models.py:

    python -m app.pipeline.migrate
"""
import os
import sys

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from sqlalchemy import text  # noqa: E402

from app import models  # noqa: E402,F401 registers all models on Base.metadata
from app.database import Base, engine  # noqa: E402

COLUMN_MIGRATIONS = [
    "ALTER TABLE teams ADD COLUMN IF NOT EXISTS api_football_id INTEGER UNIQUE",
    "ALTER TABLE teams ADD COLUMN IF NOT EXISTS stats_api_id INTEGER UNIQUE",
    "ALTER TABLE players ADD COLUMN IF NOT EXISTS api_football_id INTEGER UNIQUE",
    "ALTER TABLE players ADD COLUMN IF NOT EXISTS stats_api_id INTEGER UNIQUE",
    "ALTER TABLE players ADD COLUMN IF NOT EXISTS fpl_team_id INTEGER",
    "CREATE INDEX IF NOT EXISTS idx_player_fpl_team ON players (fpl_team_id)",
    "ALTER TABLE matches ADD COLUMN IF NOT EXISTS api_football_fixture_id INTEGER UNIQUE",
    "ALTER TABLE players ADD COLUMN IF NOT EXISTS understat_id INTEGER UNIQUE",
]


def run():
    print("Running column migrations on existing tables...")
    with engine.begin() as conn:
        for sql in COLUMN_MIGRATIONS:
            try:
                conn.execute(text(sql))
                print(f"  OK  {sql}")
            except Exception as e:
                print(f"  SKIP ({e})")

    print("Creating any new tables...")
    Base.metadata.create_all(bind=engine)
    print("Done.")


if __name__ == "__main__":
    run()
