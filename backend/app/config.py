import os

# Load .env if python-dotenv is installed; silently skip otherwise
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
except ImportError:
    pass

from pydantic import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "postgresql+pg8000://pl_user:pl_password@localhost:5435/pl_db"
    )
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")

    API_FOOTBALL_KEY: str = os.getenv("API_FOOTBALL_KEY", "")
    API_FOOTBALL_HOST: str = os.getenv("API_FOOTBALL_HOST", "api-football-v1.p.rapidapi.com")

    # NOTE: verify endpoint paths against your TheStatsAPI plan documentation
    STATS_API_KEY: str = os.getenv("STATS_API_KEY", "")
    STATS_API_HOST: str = os.getenv("STATS_API_HOST", "https://api.thestatsapi.com")

    PL_LEAGUE_ID: int = int(os.getenv("PL_LEAGUE_ID", "39"))
    CURRENT_SEASON_YEAR: int = int(os.getenv("CURRENT_SEASON_YEAR", "2024"))

    API_PREFIX: str = "/api"
    PROJECT_NAME: str = "Premier League Stats & Performance Tracker"

    class Config:
        case_sensitive = True


settings = Settings()