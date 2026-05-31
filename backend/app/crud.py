from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from app.models import Competition, Season, Team, TeamSeason, Match, GameweekStanding, Player, PlayerSeasonSummary, PlayerMatchStat
from typing import List, Optional

def get_competitions(db: Session) -> List[Competition]:
    return db.query(Competition).all()

def get_seasons(db: Session) -> List[Season]:
    return db.query(Season).order_by(Season.id.desc()).all()

def get_teams(db: Session, season_id: Optional[int] = None) -> List[Team]:
    if season_id:
        return db.query(Team).join(TeamSeason).filter(TeamSeason.season_id == season_id).order_by(Team.name).all()
    return db.query(Team).order_by(Team.name).all()

def get_team_by_id(db: Session, team_id: int) -> Optional[Team]:
    return db.query(Team).filter(Team.id == team_id).first()

def get_players(db: Session, search_query: Optional[str] = None, limit: int = 50) -> List[Player]:
    q = db.query(Player)
    if search_query:
        search_query = f"%{search_query.strip()}%"
        q = q.filter(
            or_(
                Player.first_name.ilike(search_query),
                Player.second_name.ilike(search_query)
            )
        )
    return q.order_by(Player.second_name).limit(limit).all()

def get_player_by_id(db: Session, player_id: int) -> Optional[Player]:
    return db.query(Player).filter(Player.id == player_id).first()

def get_latest_gameweek(db: Session, season_id: int, competition_code: str = "EPL") -> int:
    comp = db.query(Competition).filter(Competition.code == competition_code).first()
    if not comp:
        return 0
    max_gw = db.query(func.max(GameweekStanding.gameweek)).filter(
        GameweekStanding.season_id == season_id,
        GameweekStanding.competition_id == comp.id
    ).scalar()
    return max_gw or 0

def get_standings(db: Session, season_id: int, gameweek: Optional[int] = None, competition_code: str = "EPL") -> List[GameweekStanding]:
    comp = db.query(Competition).filter(Competition.code == competition_code).first()
    if not comp:
        return []
        
    if gameweek is None or gameweek <= 0:
        gameweek = get_latest_gameweek(db, season_id, competition_code)
        
    if not gameweek:
        return []
        
    return db.query(GameweekStanding).filter(
        GameweekStanding.season_id == season_id,
        GameweekStanding.gameweek == gameweek,
        GameweekStanding.competition_id == comp.id
    ).order_by(GameweekStanding.position).all()

def get_standings_history(db: Session, season_id: int, competition_code: str = "EPL"):
    comp = db.query(Competition).filter(Competition.code == competition_code).first()
    if not comp:
        return []
        
    return db.query(GameweekStanding).filter(
        GameweekStanding.season_id == season_id,
        GameweekStanding.competition_id == comp.id
    ).order_by(GameweekStanding.gameweek, GameweekStanding.position).all()

def get_team_form(db: Session, team_id: int, season_id: int, last_x: int = 5):
    # Fetch all matches in this season where team played
    matches = db.query(Match).filter(
        Match.season_id == season_id,
        or_(Match.home_team_id == team_id, Match.away_team_id == team_id)
    ).order_by(Match.match_date.desc()).limit(last_x).all()
    
    # We reverse them to show chronological order (left to right)
    matches.reverse()
    
    form_list = []
    form_string = ""
    
    for m in matches:
        is_home = (m.home_team_id == team_id)
        opponent = m.away_team if is_home else m.home_team
        
        goals_for = m.home_goals if is_home else m.away_goals
        goals_against = m.away_goals if is_home else m.home_goals
        
        shots = m.home_shots if is_home else m.away_shots
        shots_on_target = m.home_shots_on_target if is_home else m.away_shots_on_target
        
        # Calculate result from perspective of team_id
        if m.result == "D":
            res = "D"
        elif (m.result == "H" and is_home) or (m.result == "A" and not is_home):
            res = "W"
        else:
            res = "L"
            
        form_string += res
        form_list.append({
            "opponent_name": opponent.name,
            "is_home": is_home,
            "goals_for": goals_for,
            "goals_against": goals_against,
            "result": res,
            "match_date": m.match_date,
            "shots": shots,
            "shots_on_target": shots_on_target
        })
        
    return form_list, form_string

def get_player_season_summaries(db: Session, player_id: int) -> List[PlayerSeasonSummary]:
    # Returns summaries for all seasons, joined with Season to get label
    return db.query(PlayerSeasonSummary).filter(
        PlayerSeasonSummary.player_id == player_id
    ).join(Season).order_by(Season.id).all()

def get_player_recent_stats(db: Session, player_id: int, limit: int = 38) -> List[PlayerMatchStat]:
    # Returns player stats joined with matches to get date/gameweek info
    return db.query(PlayerMatchStat).filter(
        PlayerMatchStat.player_id == player_id
    ).join(Match).order_by(Match.match_date.desc()).limit(limit).all()
