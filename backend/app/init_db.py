from app.database import Base, engine
from app.models import (  # noqa: F401
    Competition,
    GameweekStanding,
    Match,
    MatchAdvancedStats,
    MatchEvent,
    MatchLineup,
    Player,
    PlayerAdvancedStats,
    PlayerMatchStat,
    PlayerProfile,
    PlayerSeasonSummary,
    Season,
    Team,
    TeamProfile,
    TeamSeason,
)


def init_db():
    print("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables initialized successfully!")


if __name__ == "__main__":
    init_db()
