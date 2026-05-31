from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.models import (
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
from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

# ── Existing lookups ──────────────────────────────────────────────────────────


def get_competitions(db: Session) -> List[Competition]:
    return db.query(Competition).all()


def get_seasons(db: Session) -> List[Season]:
    return db.query(Season).order_by(Season.id.desc()).all()


def get_teams(db: Session, season_id: Optional[int] = None) -> List[Team]:
    if season_id:
        return (
            db.query(Team)
            .join(TeamSeason)
            .filter(TeamSeason.season_id == season_id)
            .order_by(Team.name)
            .all()
        )
    return db.query(Team).order_by(Team.name).all()


def get_team_by_id(db: Session, team_id: int) -> Optional[Team]:
    return db.query(Team).filter(Team.id == team_id).first()


def get_players(
    db: Session,
    search_query: Optional[str] = None,
    team_internal_id: Optional[int] = None,
    limit: int = 50,
) -> List[Player]:
    q = db.query(Player)
    if team_internal_id:
        team = db.query(Team).filter(Team.id == team_internal_id).first()
        if team and team.fpl_id:
            q = q.filter(Player.fpl_team_id == team.fpl_id)
    if search_query:
        pat = f"%{search_query.strip()}%"
        q = q.filter(or_(Player.first_name.ilike(pat), Player.second_name.ilike(pat)))
    return q.order_by(Player.second_name).limit(limit).all()


def get_player_by_id(db: Session, player_id: int) -> Optional[Player]:
    return db.query(Player).filter(Player.id == player_id).first()


def get_latest_gameweek(
    db: Session, season_id: int, competition_code: str = "EPL"
) -> int:
    comp = db.query(Competition).filter(Competition.code == competition_code).first()
    if not comp:
        return 0
    max_gw = (
        db.query(func.max(GameweekStanding.gameweek))
        .filter(
            GameweekStanding.season_id == season_id,
            GameweekStanding.competition_id == comp.id,
        )
        .scalar()
    )
    return max_gw or 0


def get_standings(
    db: Session,
    season_id: int,
    gameweek: Optional[int] = None,
    competition_code: str = "EPL",
) -> List[GameweekStanding]:
    comp = db.query(Competition).filter(Competition.code == competition_code).first()
    if not comp:
        return []
    if gameweek is None or gameweek <= 0:
        gameweek = get_latest_gameweek(db, season_id, competition_code)
    if not gameweek:
        return []
    return (
        db.query(GameweekStanding)
        .filter(
            GameweekStanding.season_id == season_id,
            GameweekStanding.gameweek == gameweek,
            GameweekStanding.competition_id == comp.id,
        )
        .order_by(GameweekStanding.position)
        .all()
    )


def get_standings_history(db: Session, season_id: int, competition_code: str = "EPL"):
    comp = db.query(Competition).filter(Competition.code == competition_code).first()
    if not comp:
        return []
    return (
        db.query(GameweekStanding)
        .filter(
            GameweekStanding.season_id == season_id,
            GameweekStanding.competition_id == comp.id,
        )
        .order_by(GameweekStanding.gameweek, GameweekStanding.position)
        .all()
    )


def get_team_form(db: Session, team_id: int, season_id: int, last_x: int = 5):
    rows = (
        db.query(Match, MatchAdvancedStats)
        .outerjoin(MatchAdvancedStats, MatchAdvancedStats.match_id == Match.id)
        .filter(
            Match.season_id == season_id,
            or_(Match.home_team_id == team_id, Match.away_team_id == team_id),
        )
        .order_by(Match.match_date.desc())
        .limit(last_x)
        .all()
    )
    rows.reverse()

    form_list, form_string = [], ""
    for m, adv in rows:
        is_home = m.home_team_id == team_id
        opponent = m.away_team if is_home else m.home_team
        goals_for = m.home_goals if is_home else m.away_goals
        goals_against = m.away_goals if is_home else m.home_goals
        shots = m.home_shots if is_home else m.away_shots
        sot = m.home_shots_on_target if is_home else m.away_shots_on_target
        xg = (adv.home_xg if is_home else adv.away_xg) if adv else None

        if m.result == "D":
            res = "D"
        elif (m.result == "H" and is_home) or (m.result == "A" and not is_home):
            res = "W"
        else:
            res = "L"

        form_string += res
        form_list.append(
            {
                "opponent_name": opponent.name,
                "is_home": is_home,
                "goals_for": goals_for,
                "goals_against": goals_against,
                "result": res,
                "match_date": m.match_date,
                "shots": shots,
                "shots_on_target": sot,
                "xg": xg,
            }
        )
    return form_list, form_string


def get_player_season_summaries(
    db: Session, player_id: int
) -> List[PlayerSeasonSummary]:
    return (
        db.query(PlayerSeasonSummary)
        .filter(PlayerSeasonSummary.player_id == player_id)
        .join(Season)
        .order_by(Season.id)
        .all()
    )


def get_player_recent_stats(
    db: Session, player_id: int, limit: int = 38
) -> List[PlayerMatchStat]:
    return (
        db.query(PlayerMatchStat)
        .filter(PlayerMatchStat.player_id == player_id)
        .join(Match)
        .order_by(Match.match_date.desc())
        .limit(limit)
        .all()
    )


def get_team_season_history(db: Session, team_id: int) -> List[dict]:
    """Final-gameweek standing for every season this team appears in."""
    from sqlalchemy import func

    max_gw_sq = (
        db.query(
            GameweekStanding.season_id,
            func.max(GameweekStanding.gameweek).label("max_gw"),
        )
        .filter(GameweekStanding.team_id == team_id)
        .group_by(GameweekStanding.season_id)
        .subquery()
    )

    rows = (
        db.query(GameweekStanding, Season)
        .join(Season, Season.id == GameweekStanding.season_id)
        .join(
            max_gw_sq,
            (max_gw_sq.c.season_id == GameweekStanding.season_id)
            & (max_gw_sq.c.max_gw == GameweekStanding.gameweek),
        )
        .filter(GameweekStanding.team_id == team_id)
        .order_by(Season.id.desc())
        .all()
    )

    return [
        {
            "season_id": gws.season_id,
            "season_label": s.label,
            "final_position": gws.position,
            "points": gws.points,
            "played": gws.played,
            "wins": gws.wins,
            "draws": gws.draws,
            "losses": gws.losses,
            "goals_for": gws.goals_for,
            "goals_against": gws.goals_against,
            "goal_difference": gws.goal_difference,
        }
        for gws, s in rows
    ]


def get_head_to_head(
    db: Session, team_a_id: int, team_b_id: int, limit: int = 10
) -> List[Match]:
    return (
        db.query(Match)
        .filter(
            or_(
                and_(Match.home_team_id == team_a_id, Match.away_team_id == team_b_id),
                and_(Match.home_team_id == team_b_id, Match.away_team_id == team_a_id),
            )
        )
        .order_by(Match.match_date.desc())
        .limit(limit)
        .all()
    )


# ── Profile upserts ───────────────────────────────────────────────────────────


def upsert_team_profile(db: Session, team_id: int, data: Dict[str, Any]) -> None:
    profile = db.query(TeamProfile).filter(TeamProfile.team_id == team_id).first()
    if profile:
        for k, v in data.items():
            if hasattr(profile, k):
                setattr(profile, k, v)
        profile.updated_at = datetime.now(timezone.utc)
    else:
        profile = TeamProfile(
            team_id=team_id, updated_at=datetime.now(timezone.utc), **data
        )
        db.add(profile)
    db.commit()


def upsert_player_profile(db: Session, player_id: int, data: Dict[str, Any]) -> None:
    profile = (
        db.query(PlayerProfile).filter(PlayerProfile.player_id == player_id).first()
    )
    if profile:
        for k, v in data.items():
            if hasattr(profile, k):
                setattr(profile, k, v)
        profile.updated_at = datetime.now(timezone.utc)
    else:
        profile = PlayerProfile(
            player_id=player_id, updated_at=datetime.now(timezone.utc), **data
        )
        db.add(profile)
    db.commit()


# ── Events / lineups (stored by API-Football fixture ID) ──────────────────────


def get_match_events(db: Session, fixture_api_id: int) -> List[MatchEvent]:
    return (
        db.query(MatchEvent)
        .filter(MatchEvent.fixture_api_id == fixture_api_id)
        .order_by(MatchEvent.minute)
        .all()
    )


def store_match_events(db: Session, fixture_api_id: int, events: List[Dict]) -> None:
    for ev in events:
        exists = (
            db.query(MatchEvent)
            .filter(
                MatchEvent.fixture_api_id == fixture_api_id,
                MatchEvent.minute == ev.get("minute"),
                MatchEvent.event_type == ev.get("event_type", ""),
                MatchEvent.player_name == ev.get("player_name"),
            )
            .first()
        )
        if not exists:
            db.add(MatchEvent(fixture_api_id=fixture_api_id, **ev))
    db.commit()


def get_match_lineups(db: Session, fixture_api_id: int) -> List[MatchLineup]:
    return (
        db.query(MatchLineup).filter(MatchLineup.fixture_api_id == fixture_api_id).all()
    )


def store_match_lineups(db: Session, fixture_api_id: int, entries: List[Dict]) -> None:
    for entry in entries:
        exists = (
            db.query(MatchLineup)
            .filter(
                MatchLineup.fixture_api_id == fixture_api_id,
                MatchLineup.team_name == entry.get("team_name"),
                MatchLineup.player_name == entry.get("player_name"),
            )
            .first()
        )
        if not exists:
            db.add(MatchLineup(fixture_api_id=fixture_api_id, **entry))
    db.commit()


# ── Advanced stats ────────────────────────────────────────────────────────────


def get_match_advanced_stats(
    db: Session, match_id: int
) -> Optional[MatchAdvancedStats]:
    return (
        db.query(MatchAdvancedStats)
        .filter(MatchAdvancedStats.match_id == match_id)
        .first()
    )


def upsert_match_advanced_stats(
    db: Session, match_id: int, data: Dict[str, Any]
) -> None:
    existing = (
        db.query(MatchAdvancedStats)
        .filter(MatchAdvancedStats.match_id == match_id)
        .first()
    )
    fields = {
        k: data.get(k)
        for k in (
            "home_xg",
            "away_xg",
            "home_possession",
            "away_possession",
            "home_ppda",
            "away_ppda",
        )
    }
    if existing:
        for k, v in fields.items():
            setattr(existing, k, v)
        existing.fetched_at = datetime.now(timezone.utc)
    else:
        db.add(
            MatchAdvancedStats(
                match_id=match_id, fetched_at=datetime.now(timezone.utc), **fields
            )
        )
    db.commit()


def get_player_advanced_stats(db: Session, player_id: int) -> List[PlayerAdvancedStats]:
    return (
        db.query(PlayerAdvancedStats)
        .filter(PlayerAdvancedStats.player_id == player_id)
        .join(Season)
        .order_by(Season.id)
        .all()
    )


def upsert_player_advanced_stats(
    db: Session, player_id: int, season_id: int, data: Dict[str, Any]
) -> None:
    existing = (
        db.query(PlayerAdvancedStats)
        .filter(
            PlayerAdvancedStats.player_id == player_id,
            PlayerAdvancedStats.season_id == season_id,
        )
        .first()
    )
    fields = {
        k: data.get(k)
        for k in (
            "xg",
            "xa",
            "npxg",
            "xg_per_90",
            "xa_per_90",
            "progressive_carries",
            "progressive_passes",
            "progressive_receptions",
            "shots",
            "shots_on_target",
        )
    }
    if existing:
        for k, v in fields.items():
            setattr(existing, k, v)
        existing.fetched_at = datetime.now(timezone.utc)
    else:
        db.add(
            PlayerAdvancedStats(
                player_id=player_id,
                season_id=season_id,
                fetched_at=datetime.now(timezone.utc),
                **fields,
            )
        )
    db.commit()
