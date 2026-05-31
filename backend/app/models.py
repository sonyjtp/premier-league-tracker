from app.database import Base
from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship


class Competition(Base):
    __tablename__ = "competitions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    code = Column(String, nullable=False, unique=True)
    type = Column(String, nullable=False)

    matches = relationship("Match", back_populates="competition")
    standings = relationship("GameweekStanding", back_populates="competition")
    player_summaries = relationship("PlayerSeasonSummary", back_populates="competition")


class Season(Base):
    __tablename__ = "seasons"

    id = Column(Integer, primary_key=True, index=True)
    label = Column(String, nullable=False, unique=True)
    season_code = Column(String, nullable=False, unique=True)

    team_associations = relationship("TeamSeason", back_populates="season")
    matches = relationship("Match", back_populates="season")
    standings = relationship("GameweekStanding", back_populates="season")
    player_summaries = relationship("PlayerSeasonSummary", back_populates="season")


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    short_name = Column(String, nullable=False)
    fpl_id = Column(Integer, nullable=True)
    api_football_id = Column(Integer, nullable=True, unique=True)
    stats_api_id = Column(Integer, nullable=True, unique=True)

    season_associations = relationship("TeamSeason", back_populates="team")
    home_matches = relationship(
        "Match", foreign_keys="[Match.home_team_id]", back_populates="home_team"
    )
    away_matches = relationship(
        "Match", foreign_keys="[Match.away_team_id]", back_populates="away_team"
    )
    standings = relationship("GameweekStanding", back_populates="team")
    profile = relationship("TeamProfile", back_populates="team", uselist=False)


class TeamSeason(Base):
    __tablename__ = "team_seasons"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(
        Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False
    )
    season_id = Column(
        Integer, ForeignKey("seasons.id", ondelete="CASCADE"), nullable=False
    )

    team = relationship("Team", back_populates="season_associations")
    season = relationship("Season", back_populates="team_associations")

    __table_args__ = (UniqueConstraint("team_id", "season_id", name="uq_team_season"),)


class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    second_name = Column(String, nullable=False)
    position = Column(String, nullable=False)
    current_fpl_id = Column(Integer, nullable=True, unique=True)
    fpl_team_id = Column(
        Integer, nullable=True, index=True
    )  # FPL team ID (Team.fpl_id)
    api_football_id = Column(Integer, nullable=True, unique=True)
    stats_api_id = Column(Integer, nullable=True, unique=True)

    summaries = relationship("PlayerSeasonSummary", back_populates="player")
    match_stats = relationship("PlayerMatchStat", back_populates="player")
    profile = relationship("PlayerProfile", back_populates="player", uselist=False)
    advanced_stats = relationship("PlayerAdvancedStats", back_populates="player")


class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    competition_id = Column(
        Integer, ForeignKey("competitions.id", ondelete="CASCADE"), nullable=False
    )
    season_id = Column(
        Integer, ForeignKey("seasons.id", ondelete="CASCADE"), nullable=False
    )
    gameweek = Column(Integer, nullable=True)
    round_name = Column(String, nullable=True)
    match_date = Column(Date, nullable=False)
    home_team_id = Column(
        Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False
    )
    away_team_id = Column(
        Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False
    )
    home_goals = Column(Integer, nullable=False)
    away_goals = Column(Integer, nullable=False)
    result = Column(String, nullable=False)
    home_shots = Column(Integer, nullable=True)
    away_shots = Column(Integer, nullable=True)
    home_shots_on_target = Column(Integer, nullable=True)
    away_shots_on_target = Column(Integer, nullable=True)
    # Set after matching a completed match to an API-Football fixture
    api_football_fixture_id = Column(Integer, nullable=True, unique=True)

    competition = relationship("Competition", back_populates="matches")
    season = relationship("Season", back_populates="matches")
    home_team = relationship(
        "Team", foreign_keys=[home_team_id], back_populates="home_matches"
    )
    away_team = relationship(
        "Team", foreign_keys=[away_team_id], back_populates="away_matches"
    )
    player_match_stats = relationship("PlayerMatchStat", back_populates="match")
    advanced_stats = relationship(
        "MatchAdvancedStats", back_populates="match", uselist=False
    )

    __table_args__ = (
        UniqueConstraint(
            "season_id",
            "match_date",
            "home_team_id",
            "away_team_id",
            name="uq_match_unique",
        ),
        Index("idx_match_season_gw", "season_id", "gameweek"),
    )


class GameweekStanding(Base):
    __tablename__ = "gameweek_standings"

    id = Column(Integer, primary_key=True, index=True)
    competition_id = Column(
        Integer, ForeignKey("competitions.id", ondelete="CASCADE"), nullable=False
    )
    season_id = Column(
        Integer, ForeignKey("seasons.id", ondelete="CASCADE"), nullable=False
    )
    team_id = Column(
        Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False
    )
    gameweek = Column(Integer, nullable=False)
    points = Column(Integer, nullable=False)
    played = Column(Integer, nullable=False)
    wins = Column(Integer, nullable=False)
    draws = Column(Integer, nullable=False)
    losses = Column(Integer, nullable=False)
    goals_for = Column(Integer, nullable=False)
    goals_against = Column(Integer, nullable=False)
    goal_difference = Column(Integer, nullable=False)
    position = Column(Integer, nullable=False)

    competition = relationship("Competition", back_populates="standings")
    season = relationship("Season", back_populates="standings")
    team = relationship("Team", back_populates="standings")

    __table_args__ = (
        UniqueConstraint(
            "competition_id", "season_id", "team_id", "gameweek", name="uq_gw_standing"
        ),
        Index("idx_standing_lookup", "season_id", "gameweek", "position"),
    )


class PlayerSeasonSummary(Base):
    __tablename__ = "player_season_summaries"

    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(
        Integer, ForeignKey("players.id", ondelete="CASCADE"), nullable=False
    )
    season_id = Column(
        Integer, ForeignKey("seasons.id", ondelete="CASCADE"), nullable=False
    )
    competition_id = Column(
        Integer, ForeignKey("competitions.id", ondelete="CASCADE"), nullable=False
    )
    minutes = Column(Integer, default=0)
    goals = Column(Integer, default=0)
    assists = Column(Integer, default=0)
    clean_sheets = Column(Integer, default=0)
    yellow_cards = Column(Integer, default=0)
    red_cards = Column(Integer, default=0)
    fpl_points = Column(Integer, default=0)

    player = relationship("Player", back_populates="summaries")
    season = relationship("Season", back_populates="player_summaries")
    competition = relationship("Competition", back_populates="player_summaries")

    __table_args__ = (
        UniqueConstraint(
            "player_id", "season_id", "competition_id", name="uq_player_season_comp"
        ),
    )


class PlayerMatchStat(Base):
    __tablename__ = "player_match_stats"

    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(
        Integer, ForeignKey("matches.id", ondelete="CASCADE"), nullable=False
    )
    player_id = Column(
        Integer, ForeignKey("players.id", ondelete="CASCADE"), nullable=False
    )
    minutes = Column(Integer, default=0)
    goals = Column(Integer, default=0)
    assists = Column(Integer, default=0)
    clean_sheets = Column(Integer, default=0)
    yellow_cards = Column(Integer, default=0)
    red_cards = Column(Integer, default=0)
    fpl_points = Column(Integer, default=0)

    match = relationship("Match", back_populates="player_match_stats")
    player = relationship("Player", back_populates="match_stats")

    __table_args__ = (
        UniqueConstraint("match_id", "player_id", name="uq_match_player_stat"),
    )


# ── New tables ────────────────────────────────────────────────────────────────


class TeamProfile(Base):
    """Enhanced team metadata sourced from API-Football."""

    __tablename__ = "team_profiles"

    id = Column(Integer, primary_key=True)
    team_id = Column(
        Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    logo_url = Column(String, nullable=True)
    country = Column(String, nullable=True)
    founded = Column(Integer, nullable=True)
    venue_name = Column(String, nullable=True)
    updated_at = Column(DateTime, nullable=True)

    team = relationship("Team", back_populates="profile")


class PlayerProfile(Base):
    """Enhanced player metadata sourced from API-Football."""

    __tablename__ = "player_profiles"

    id = Column(Integer, primary_key=True)
    player_id = Column(
        Integer,
        ForeignKey("players.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    photo_url = Column(String, nullable=True)
    nationality = Column(String, nullable=True)
    birth_date = Column(Date, nullable=True)
    height = Column(String, nullable=True)
    weight = Column(String, nullable=True)
    current_club = Column(String, nullable=True)
    updated_at = Column(DateTime, nullable=True)

    player = relationship("Player", back_populates="profile")


class MatchEvent(Base):
    """Goal / card / substitution events for a fixture, sourced from API-Football."""

    __tablename__ = "match_events"

    id = Column(Integer, primary_key=True)
    fixture_api_id = Column(Integer, nullable=False, index=True)
    minute = Column(Integer, nullable=True)
    extra_minute = Column(Integer, nullable=True)
    # Goal, Card, subst, Var
    event_type = Column(String, nullable=False)
    # e.g. "Normal Goal", "Yellow Card", "Substitution 1"
    detail = Column(String, nullable=True)
    team_name = Column(String, nullable=True)
    player_name = Column(String, nullable=True)
    assist_name = Column(String, nullable=True)
    comments = Column(Text, nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "fixture_api_id",
            "minute",
            "event_type",
            "player_name",
            name="uq_match_event",
        ),
    )


class MatchLineup(Base):
    """Starting XI and substitutes for a fixture, sourced from API-Football."""

    __tablename__ = "match_lineups"

    id = Column(Integer, primary_key=True)
    fixture_api_id = Column(Integer, nullable=False, index=True)
    team_name = Column(String, nullable=False)
    formation = Column(String, nullable=True)
    player_name = Column(String, nullable=False)
    player_api_id = Column(Integer, nullable=True)
    is_starter = Column(Boolean, nullable=False, default=True)
    position = Column(String, nullable=True)
    grid = Column(String, nullable=True)
    shirt_number = Column(Integer, nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "fixture_api_id", "team_name", "player_name", name="uq_lineup_entry"
        ),
    )


class MatchAdvancedStats(Base):
    """xG, possession, PPDA per match sourced from TheStatsAPI. Stored permanently."""

    __tablename__ = "match_advanced_stats"

    match_id = Column(
        Integer, ForeignKey("matches.id", ondelete="CASCADE"), primary_key=True
    )
    home_xg = Column(Float, nullable=True)
    away_xg = Column(Float, nullable=True)
    home_possession = Column(Float, nullable=True)
    away_possession = Column(Float, nullable=True)
    # Passes per defensive action — lower = more pressing
    home_ppda = Column(Float, nullable=True)
    away_ppda = Column(Float, nullable=True)
    fetched_at = Column(DateTime, nullable=False)

    match = relationship("Match", back_populates="advanced_stats")


class PlayerAdvancedStats(Base):
    """Per-season xG, xA, progressive stats sourced from TheStatsAPI."""

    __tablename__ = "player_advanced_stats"

    id = Column(Integer, primary_key=True)
    player_id = Column(
        Integer, ForeignKey("players.id", ondelete="CASCADE"), nullable=False
    )
    season_id = Column(
        Integer, ForeignKey("seasons.id", ondelete="CASCADE"), nullable=False
    )
    xg = Column(Float, nullable=True)
    xa = Column(Float, nullable=True)
    npxg = Column(Float, nullable=True)
    xg_per_90 = Column(Float, nullable=True)
    xa_per_90 = Column(Float, nullable=True)
    progressive_carries = Column(Integer, nullable=True)
    progressive_passes = Column(Integer, nullable=True)
    progressive_receptions = Column(Integer, nullable=True)
    shots = Column(Integer, nullable=True)
    shots_on_target = Column(Integer, nullable=True)
    fetched_at = Column(DateTime, nullable=False)

    player = relationship("Player", back_populates="advanced_stats")
    season = relationship("Season")

    __table_args__ = (
        UniqueConstraint("player_id", "season_id", name="uq_player_adv_stats"),
    )
