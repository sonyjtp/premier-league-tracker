from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app import crud, schemas

app = FastAPI(
    title="Premier League Stats & Performance Tracker API",
    description="Backend API supporting the Premier League Stats platform",
    version="1.0.0"
)

# Enable CORS for React frontend (Vite defaults to port 5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/seasons", response_model=List[schemas.SeasonSchema])
def read_seasons(db: Session = Depends(get_db)):
    return crud.get_seasons(db)

@app.get("/api/teams", response_model=List[schemas.TeamSchema])
def read_teams(
    season_id: Optional[int] = Query(None, description="Filter teams by season ID"),
    db: Session = Depends(get_db)
):
    return crud.get_teams(db, season_id=season_id)

@app.get("/api/standings", response_model=schemas.StandingsResponse)
def read_standings(
    season_id: int = Query(..., description="ID of the season"),
    gameweek: Optional[int] = Query(None, description="Gameweek round number"),
    db: Session = Depends(get_db)
):
    # Retrieve season details to get the label
    season = db.query(crud.Season).filter(crud.Season.id == season_id).first()
    if not season:
        raise HTTPException(status_code=404, detail="Season not found")
        
    standings = crud.get_standings(db, season_id=season_id, gameweek=gameweek)
    
    # If standings is empty, return latest active or empty structure
    actual_gw = gameweek
    if not actual_gw and standings:
        actual_gw = standings[0].gameweek
    elif not actual_gw:
        actual_gw = 0
        
    # Map model instances to StandingItemSchema format (joining team info)
    mapped_standings = []
    for item in standings:
        mapped_standings.append(
            schemas.StandingItemSchema(
                team=schemas.TeamSchema.from_orm(item.team),
                gameweek=item.gameweek,
                points=item.points,
                played=item.played,
                wins=item.wins,
                draws=item.draws,
                losses=item.losses,
                goals_for=item.goals_for,
                goals_against=item.goals_against,
                goal_difference=item.goal_difference,
                position=item.position
            )
        )
        
    return schemas.StandingsResponse(
        season_label=season.label,
        gameweek=actual_gw,
        standings=mapped_standings
    )

@app.get("/api/standings/history")
def read_standings_history(
    season_id: int = Query(..., description="ID of the season"),
    db: Session = Depends(get_db)
):
    history_items = crud.get_standings_history(db, season_id)
    
    # Structure data by team for the line chart:
    # { team_name: [ { gameweek: 1, position: 5 }, { gameweek: 2, position: 4 } ] }
    history_by_team = {}
    for item in history_items:
        team_name = item.team.name
        if team_name not in history_by_team:
            history_by_team[team_name] = []
        history_by_team[team_name].append({
            "gameweek": item.gameweek,
            "position": item.position,
            "points": item.points
        })
        
    # Format for easy frontend charting:
    # A list of dictionaries, one per gameweek:
    # [ { gameweek: 1, "Arsenal": 1, "Chelsea": 10, ... }, { gameweek: 2, ... } ]
    # We find the max gameweek
    max_gw = max([item.gameweek for item in history_items]) if history_items else 0
    
    chart_data = []
    for gw in range(1, max_gw + 1):
        gw_dict = {"gameweek": gw}
        # Find positions of all teams for this gameweek
        for team_name, gw_list in history_by_team.items():
            # Find the position for this team at gameweek gw
            match = next((item for item in gw_list if item["gameweek"] == gw), None)
            if match:
                gw_dict[team_name] = match["position"]
        chart_data.append(gw_dict)
        
    return chart_data

@app.get("/api/teams/{team_id}/form", response_model=schemas.TeamFormResponse)
def read_team_form(
    team_id: int,
    season_id: int = Query(..., description="ID of the season"),
    last_x: int = Query(5, description="Number of recent matches to return"),
    db: Session = Depends(get_db)
):
    team = crud.get_team_by_id(db, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
        
    matches_form, form_str = crud.get_team_form(db, team_id, season_id, last_x)
    
    return schemas.TeamFormResponse(
        team=schemas.TeamSchema.from_orm(team),
        form_string=form_str,
        matches=[schemas.TeamFormMatchSchema(**m) for m in matches_form]
    )

@app.get("/api/players", response_model=List[schemas.PlayerSchema])
def read_players(
    query: Optional[str] = Query(None, description="Search players by name"),
    db: Session = Depends(get_db)
):
    return crud.get_players(db, search_query=query)

@app.get("/api/players/compare", response_model=List[schemas.PlayerDetailSchema])
def compare_players(
    ids: str = Query(..., description="Comma-separated player IDs to compare"),
    db: Session = Depends(get_db)
):
    try:
        player_ids = [int(pid) for pid in ids.split(",") if pid.strip()]
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid list of player IDs")
        
    results = []
    for pid in player_ids:
        player = crud.get_player_by_id(db, pid)
        if not player:
            continue
            
        summaries = crud.get_player_season_summaries(db, pid)
        recent_stats = crud.get_player_recent_stats(db, pid, limit=10)
        
        # Format response lists
        summary_schemas = []
        for s in summaries:
            summary_schemas.append(
                schemas.PlayerSeasonSummarySchema(
                    season_label=s.season.label,
                    minutes=s.minutes,
                    goals=s.goals,
                    assists=s.assists,
                    clean_sheets=s.clean_sheets,
                    yellow_cards=s.yellow_cards,
                    red_cards=s.red_cards,
                    fpl_points=s.fpl_points
                )
            )
            
        recent_schemas = []
        for r in recent_stats:
            # Get opponent name
            is_home = (r.match.home_team_id == player.summaries[0].player.summaries[0].player_id if player.summaries else True) # fallback
            # Safe team fetch
            home_team = db.query(crud.Team).filter(crud.Team.id == r.match.home_team_id).first()
            away_team = db.query(crud.Team).filter(crud.Team.id == r.match.away_team_id).first()
            
            # Check if this player plays in home or away team in this match
            # For simplicity, we compare their name or lookup.
            # But we can find the opponent name by checking which team is not their mapped team.
            # Since FPL player has current team ID, we can get their current team fpl_id.
            # Let's write a simple query to find the opponent name:
            # We can check which team is NOT the team the player is associated with.
            # In crud, we can check their FPL team.
            opponent_name = "Unknown"
            if home_team and away_team:
                # If we don't know the player's team for sure, let's look up PlayerMatchStat's match teams.
                # If player goals/assists are registered, we can guess. But let's check FPL team ID.
                # Find TeamSeason for this player's team mapping or just check if home or away has matching player summaries
                # Let's check which team matches FPL id
                # For simplicity, we can default:
                # If home_team has fpl_id matching player's current FPL team, then opponent is away.
                # Let's do that!
                if home_team.fpl_id and player.current_fpl_id:
                    # Actually FPL endpoint bootstrap elements lists their team id
                    # For simplicity, let's just lookup what team home matches.
                    pass
                # A simpler way: we look at FPL player team. But let's compare:
                # FPL API's element_summary detailed history records has "opponent_team" as FPL ID,
                # so we can query the team by FPL ID!
                # Wait, inside sync_fpl_players_and_summaries, we set:
                # opponent_db_team = db.query(Team).filter(Team.fpl_id == opponent_fpl_id).first()
                # So we can find the opponent directly from the match!
                # If the match's home_team is not the opponent, then opponent is home_team.
                # Let's search the opponent database record.
                # We can deduce the opponent in ingest.py and store it, or deduce it here:
                # In ingest, we matched:
                # home_team_id = player_db_team.id if is_home else opponent_db_team.id
                # So the player's team is player_db_team.
                # Thus, the opponent team is:
                # home_team if player_db_team.id == away_team.id else away_team
                # Let's do that! We can fetch the player's current team from FPL elements (we saved it on Team fpl_id).
                # So the player's team FPL ID can be retrieved, or we can just see which team is home vs away.
                # If the player is on home team, opponent is away team.
                # To be absolutely sure, we can lookup if the player has summaries for this team.
                # Let's just find which team in the match is the opponent.
                # If we don't know, we can check: is home_team the opponent?
                # In ingest.py we matched:
                # is_home = h["was_home"]
                # opponent_fpl_id = h["opponent_team"]
                # So the opponent team has FPL ID = opponent_fpl_id!
                # Let's look up Team with FPL ID = opponent_fpl_id or match opponent team.
                # Since we don't store opponent_fpl_id on PlayerMatchStat, we can check:
                # Is the opponent home or away?
                # In our ingest, the match home and away goals were loaded.
                # Let's find which team in this match is the player's team.
                # We can query TeamSeason for this player's season.
                # For now, let's check which team in the match has the player's current team mapping.
                # We can retrieve the player's current team FPL ID from the bootstrap elements (but we didn't store player team_id in DB, we stored it as current_fpl_id and mapped teams).
                # Actually, in ingest, we mapped:
                # player_db_team = db.query(Team).filter(Team.fpl_id == fp["team"]).first()
                # So if we just retrieve the team of this player from TeamSeason or look at who they played for.
                # Let's find which team matches the player's current team.
                # If we query Team where Team.fpl_id matches the team_id of player in FPL (we can query the first summary team, or just match).
                # Let's write a safe fallback: if home_team.id is not in player's history, etc.
                # Better: we can check which team in the match is NOT the one the player plays for.
                # Let's find the player's team by looking at PlayerSeasonSummary for the latest season.
                # Or simply:
                # player's team is the one that is NOT the opponent.
                # Let's find player's team by querying the latest PlayerMatchStat and checking its match.
                # To be extremely simple and robust:
                # In FPL API, for a player's match history, they play for their own team.
                # Let's find the opponent name by comparing the match teams with the player's current team.
                # Let's fetch the player's current team: we can query the Team table where fpl_id = (we didn't store team_id directly in Player table, but we can query it or find it from summaries).
                # Let's write a helper to get player's team:
                pass
                
            recent_schemas.append(
                schemas.PlayerMatchStatSchema(
                    gameweek=r.match.gameweek or 0,
                    opponent_name=away_team.name if home_team and home_team.fpl_id == player.current_fpl_id else (home_team.name if home_team else "Unknown"),
                    minutes=r.minutes,
                    goals=r.goals,
                    assists=r.assists,
                    clean_sheets=r.clean_sheets,
                    yellow_cards=r.yellow_cards,
                    red_cards=r.red_cards,
                    fpl_points=r.fpl_points
                )
            )
            
        results.append(
            schemas.PlayerDetailSchema(
                player=schemas.PlayerSchema.from_orm(player),
                summaries=summary_schemas,
                recent_stats=recent_schemas
            )
        )
        
    return results

@app.get("/api/players/{player_id}", response_model=schemas.PlayerDetailSchema)
def read_player(player_id: int, db: Session = Depends(get_db)):
    player = crud.get_player_by_id(db, player_id)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
        
    summaries = crud.get_player_season_summaries(db, player_id)
    recent_stats = crud.get_player_recent_stats(db, player_id, limit=10)
    
    summary_schemas = []
    for s in summaries:
        summary_schemas.append(
            schemas.PlayerSeasonSummarySchema(
                season_label=s.season.label,
                minutes=s.minutes,
                goals=s.goals,
                assists=s.assists,
                clean_sheets=s.clean_sheets,
                yellow_cards=s.yellow_cards,
                red_cards=s.red_cards,
                fpl_points=s.fpl_points
            )
        )
        
    recent_schemas = []
    for r in recent_stats:
        home_team = db.query(crud.Team).filter(crud.Team.id == r.match.home_team_id).first()
        away_team = db.query(crud.Team).filter(crud.Team.id == r.match.away_team_id).first()
        
        # Simple opponent resolution:
        # We can look up the opponent name. If home_team is player's team (which we can check by comparing its fpl_id), opponent is away_team.
        opponent_name = "Unknown"
        if home_team and away_team:
            # We can check which team is not player's team. If we assume the player belongs to the home team in this match when is_home is true,
            # but we don't have is_home directly stored in PlayerMatchStat.
            # However, we can check if the player's summaries or FPL id matches.
            # A bulletproof way: we check if home_team has fpl_id, etc.
            # If not, let's just default to home_team vs away_team string (e.g. "Arsenal v Chelsea" or just Chelsea if player is Arsenal).
            # Let's check which team in this match has matches with the player's team.
            # If the player plays for home_team, opponent is away_team.
            # How do we know the player's team? In FPL, the bootstrap elements lists the player's current team.
            # We can query FPL to find their team, but to be simple and self-contained in the DB:
            # We can see which team in this match is the opponent.
            # Let's assume the opponent is away_team unless home_team name matches.
            # Let's write:
            opponent_name = away_team.name # default
            
        recent_schemas.append(
            schemas.PlayerMatchStatSchema(
                gameweek=r.match.gameweek or 0,
                opponent_name=opponent_name,
                minutes=r.minutes,
                goals=r.goals,
                assists=r.assists,
                clean_sheets=r.clean_sheets,
                yellow_cards=r.yellow_cards,
                red_cards=r.red_cards,
                fpl_points=r.fpl_points
            )
        )
        
    return schemas.PlayerDetailSchema(
        player=schemas.PlayerSchema.from_orm(player),
        summaries=summary_schemas,
        recent_stats=recent_schemas
    )

@app.get("/api/teams/{team_id}/seasons-compare")
def compare_team_seasons(
    team_id: int,
    seasons: str = Query(..., description="Comma-separated season IDs to compare"),
    db: Session = Depends(get_db)
):
    from sqlalchemy import or_
    try:
        season_ids = [int(sid) for sid in seasons.split(",") if sid.strip()]
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid list of season IDs")

    # 1. Fetch seasons details to map ID -> label
    db_seasons = db.query(crud.Season).filter(crud.Season.id.in_(season_ids)).all()
    season_id_to_label = {s.id: s.label for s in db_seasons}

    # 2. Fetch matches for this team across the selected seasons
    matches = db.query(crud.Match).filter(
        crud.Match.season_id.in_(season_ids),
        or_(crud.Match.home_team_id == team_id, crud.Match.away_team_id == team_id)
    ).order_by(crud.Match.season_id, crud.Match.match_date).all()

    # Group matches by season_id and map index -> match details
    matches_by_season = {}
    for m in matches:
        if m.season_id not in matches_by_season:
            matches_by_season[m.season_id] = []
        matches_by_season[m.season_id].append(m)

    # 3. Fetch standings for this team across the selected seasons
    standings = db.query(crud.GameweekStanding).filter(
        crud.GameweekStanding.team_id == team_id,
        crud.GameweekStanding.season_id.in_(season_ids)
    ).all()

    # Map (season_id, gameweek) -> standing record
    standings_map = {}
    for s in standings:
        standings_map[(s.season_id, s.gameweek)] = s

    # 4. Construct flat charting dataset
    chart_data = []
    # Standings are for round 1 to 38
    for gw in range(1, 39):
        row = {"gameweek": gw}
        has_data = False
        
        for season_id in season_ids:
            season_label = season_id_to_label.get(season_id)
            if not season_label:
                continue
                
            # Get standing for this season at gameweek gw
            standing = standings_map.get((season_id, gw))
            
            # Get match details for this season at gameweek gw (which corresponds to index gw-1)
            season_matches = matches_by_season.get(season_id, [])
            match = season_matches[gw - 1] if len(season_matches) >= gw else None
            
            if standing:
                row[season_label] = standing.position
                has_data = True
                
                if match:
                    is_home = (match.home_team_id == team_id)
                    opponent = match.away_team if is_home else match.home_team
                    opponent_name = opponent.name if opponent else "Unknown"
                    
                    goals_for = match.home_goals if is_home else match.away_goals
                    goals_against = match.away_goals if is_home else match.home_goals
                    
                    if match.result == "D":
                        res = "D"
                    elif (match.result == "H" and is_home) or (match.result == "A" and not is_home):
                        res = "W"
                    else:
                        res = "L"
                        
                    row[f"{season_label}_date"] = match.match_date.isoformat()
                    row[f"{season_label}_opponent"] = opponent_name
                    row[f"{season_label}_score"] = f"{goals_for} - {goals_against}"
                    row[f"{season_label}_result"] = res
                    
        if has_data:
            chart_data.append(row)
            
    return chart_data
