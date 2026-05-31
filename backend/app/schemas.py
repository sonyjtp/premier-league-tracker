from pydantic import BaseModel
from datetime import date, datetime
from typing import List, Optional


class CompetitionSchema(BaseModel):
    id: int
    name: str
    code: str
    type: str

    class Config:
        orm_mode = True


class SeasonSchema(BaseModel):
    id: int
    label: str
    season_code: str

    class Config:
        orm_mode = True


class TeamSchema(BaseModel):
    id: int
    name: str
    short_name: str
    fpl_id: Optional[int] = None
    api_football_id: Optional[int] = None

    class Config:
        orm_mode = True


class MatchSchema(BaseModel):
    id: int
    competition_id: int
    season_id: int
    gameweek: Optional[int] = None
    round_name: Optional[str] = None
    match_date: date
    home_team: TeamSchema
    away_team: TeamSchema
    home_goals: int
    away_goals: int
    result: str
    home_shots: Optional[int] = None
    away_shots: Optional[int] = None
    home_shots_on_target: Optional[int] = None
    away_shots_on_target: Optional[int] = None

    class Config:
        orm_mode = True


class StandingItemSchema(BaseModel):
    team: TeamSchema
    gameweek: int
    points: int
    played: int
    wins: int
    draws: int
    losses: int
    goals_for: int
    goals_against: int
    goal_difference: int
    position: int

    class Config:
        orm_mode = True


class StandingsResponse(BaseModel):
    season_label: str
    gameweek: int
    standings: List[StandingItemSchema]


class PlayerSchema(BaseModel):
    id: int
    first_name: str
    second_name: str
    position: str
    current_fpl_id: Optional[int] = None
    api_football_id: Optional[int] = None

    class Config:
        orm_mode = True


class PlayerSeasonSummarySchema(BaseModel):
    season_label: str
    minutes: int
    goals: int
    assists: int
    clean_sheets: int
    yellow_cards: int
    red_cards: int
    fpl_points: int

    class Config:
        orm_mode = True


class PlayerMatchStatSchema(BaseModel):
    gameweek: int
    opponent_name: str
    minutes: int
    goals: int
    assists: int
    clean_sheets: int
    yellow_cards: int
    red_cards: int
    fpl_points: int

    class Config:
        orm_mode = True


class PlayerAdvancedStatsSchema(BaseModel):
    season_label: str
    xg: Optional[float] = None
    xa: Optional[float] = None
    npxg: Optional[float] = None
    xg_per_90: Optional[float] = None
    xa_per_90: Optional[float] = None
    progressive_carries: Optional[int] = None
    progressive_passes: Optional[int] = None
    progressive_receptions: Optional[int] = None
    shots: Optional[int] = None
    shots_on_target: Optional[int] = None

    class Config:
        orm_mode = True


class PlayerProfileSchema(BaseModel):
    photo_url: Optional[str] = None
    nationality: Optional[str] = None
    birth_date: Optional[date] = None
    height: Optional[str] = None
    weight: Optional[str] = None
    current_club: Optional[str] = None

    class Config:
        orm_mode = True


class PlayerDetailSchema(BaseModel):
    player: PlayerSchema
    profile: Optional[PlayerProfileSchema] = None
    summaries: List[PlayerSeasonSummarySchema]
    recent_stats: List[PlayerMatchStatSchema]
    advanced_stats: Optional[List[PlayerAdvancedStatsSchema]] = None


class TeamFormMatchSchema(BaseModel):
    opponent_name: str
    is_home: bool
    goals_for: int
    goals_against: int
    result: str
    match_date: date
    shots: Optional[int] = None
    shots_on_target: Optional[int] = None
    xg: Optional[float] = None


class TeamFormResponse(BaseModel):
    team: TeamSchema
    form_string: str
    matches: List[TeamFormMatchSchema]


class TeamProfileSchema(BaseModel):
    logo_url: Optional[str] = None
    country: Optional[str] = None
    founded: Optional[int] = None
    venue_name: Optional[str] = None

    class Config:
        orm_mode = True


# ── Live / Fixtures ───────────────────────────────────────────────────────────

class FixtureTeamSchema(BaseModel):
    name: str
    logo: Optional[str] = None
    api_id: Optional[int] = None


class LiveFixtureSchema(BaseModel):
    fixture_id: int
    status_short: str
    status_long: str
    elapsed: Optional[int] = None
    kickoff: Optional[str] = None
    venue: Optional[str] = None
    round: Optional[str] = None
    home_team: FixtureTeamSchema
    away_team: FixtureTeamSchema
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    home_ht_score: Optional[int] = None
    away_ht_score: Optional[int] = None


class FixturesResponseSchema(BaseModel):
    fixtures: List[LiveFixtureSchema]
    cached_at: Optional[str] = None


# ── Match detail ──────────────────────────────────────────────────────────────

class MatchEventSchema(BaseModel):
    minute: Optional[int] = None
    extra_minute: Optional[int] = None
    event_type: str
    detail: Optional[str] = None
    team_name: Optional[str] = None
    player_name: Optional[str] = None
    assist_name: Optional[str] = None
    comments: Optional[str] = None

    class Config:
        orm_mode = True


class LineupPlayerSchema(BaseModel):
    name: str
    shirt_number: Optional[int] = None
    position: Optional[str] = None
    grid: Optional[str] = None
    is_starter: bool


class TeamLineupSchema(BaseModel):
    team_name: str
    formation: Optional[str] = None
    starters: List[LineupPlayerSchema]
    substitutes: List[LineupPlayerSchema]


class MatchAdvancedStatsSchema(BaseModel):
    home_xg: Optional[float] = None
    away_xg: Optional[float] = None
    home_possession: Optional[float] = None
    away_possession: Optional[float] = None
    home_ppda: Optional[float] = None
    away_ppda: Optional[float] = None

    class Config:
        orm_mode = True


# ── Head-to-head ──────────────────────────────────────────────────────────────

class H2HMatchSchema(BaseModel):
    match_date: date
    season_label: str
    home_team: str
    away_team: str
    home_goals: int
    away_goals: int
    result: str