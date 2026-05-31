from app.database import engine, Base
# Import models here so they are registered on Base.metadata
from app.models import Competition, Season, Team, TeamSeason, Player, Match, GameweekStanding, PlayerSeasonSummary, PlayerMatchStat

def init_db():
    print("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables initialized successfully!")

if __name__ == "__main__":
    init_db()
