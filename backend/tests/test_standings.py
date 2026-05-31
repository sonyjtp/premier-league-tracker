from datetime import date

import pytest
from app.database import Base
from app.models import Competition, GameweekStanding, Match, Season, Team, TeamSeason
from app.pipeline.ingest import precompute_standings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


# Setup an in-memory SQLite database for testing
@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_precompute_standings_ranking_logic(db_session):
    # 1. Seed static competition and season
    comp = Competition(name="English Premier League", code="EPL", type="LEAGUE")
    season = Season(label="2023-2024", season_code="2324")
    db_session.add_all([comp, season])
    db_session.commit()

    # 2. Seed 4 teams
    team_a = Team(name="Arsenal", short_name="ARS")  # Alpha 1
    team_b = Team(name="Aston Villa", short_name="AVL")  # Alpha 2
    team_c = Team(name="Chelsea", short_name="CHE")  # Alpha 3
    team_d = Team(name="Everton", short_name="EVE")  # Alpha 4
    db_session.add_all([team_a, team_b, team_c, team_d])
    db_session.commit()

    # Associate teams to season
    for team in (team_a, team_b, team_c, team_d):
        db_session.add(TeamSeason(team_id=team.id, season_id=season.id))
    db_session.commit()

    # 3. Create matches for Round 1
    # Match 1: Arsenal beats Aston Villa 3-1
    # Arsenal: played=1, wins=1, GF=3, GA=1, GD=+2, pts=3
    # Aston Villa: played=1, losses=1, GF=1, GA=3, GD=-2, pts=0
    match_1 = Match(
        competition_id=comp.id,
        season_id=season.id,
        gameweek=1,
        match_date=date(2023, 8, 12),
        home_team_id=team_a.id,
        away_team_id=team_b.id,
        home_goals=3,
        away_goals=1,
        result="H",
    )

    # Match 2: Chelsea draws with Everton 2-2
    # Chelsea: played=1, draws=1, GF=2, GA=2, GD=0, pts=1
    # Everton: played=1, draws=1, GF=2, GA=2, GD=0, pts=1
    match_2 = Match(
        competition_id=comp.id,
        season_id=season.id,
        gameweek=1,
        match_date=date(2023, 8, 12),
        home_team_id=team_c.id,
        away_team_id=team_d.id,
        home_goals=2,
        away_goals=2,
        result="D",
    )

    db_session.add_all([match_1, match_2])
    db_session.commit()

    # 4. Run standings precomputation
    precompute_standings(db_session, comp)

    # 5. Fetch standings and verify rankings
    standings = (
        db_session.query(GameweekStanding)
        .filter(GameweekStanding.season_id == season.id, GameweekStanding.gameweek == 1)
        .order_by(GameweekStanding.position)
        .all()
    )

    assert len(standings) == 4

    # Rank 1: Arsenal (3 pts, +2 GD)
    assert standings[0].position == 1
    assert standings[0].team_id == team_a.id
    assert standings[0].points == 3
    assert standings[0].goal_difference == 2

    # Rank 2: Chelsea (1 pt, 0 GD, 2 GS, Alphabetical 'C' before 'E')
    assert standings[1].position == 2
    assert standings[1].team_id == team_c.id
    assert standings[1].points == 1
    assert standings[1].goal_difference == 0
    assert standings[1].goals_for == 2

    # Rank 3: Everton (1 pt, 0 GD, 2 GS, Alphabetical 'E' after 'C')
    assert standings[2].position == 3
    assert standings[2].team_id == team_d.id
    assert standings[2].points == 1
    assert standings[2].goal_difference == 0
    assert standings[2].goals_for == 2

    # Rank 4: Aston Villa (0 pts, -2 GD)
    assert standings[3].position == 4
    assert standings[3].team_id == team_b.id
    assert standings[3].points == 0
    assert standings[3].goal_difference == -2
