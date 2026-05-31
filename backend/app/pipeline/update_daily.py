import os
import sys
import requests
from sqlalchemy.orm import Session

# Set up python path so we can import from backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.database import SessionLocal
from app.models import Competition, Season, Team, Match
from app.pipeline.ingest import normalize_team_name, parse_date, precompute_standings, sync_fpl_players_and_summaries

def update_current_season_data():
    db = SessionLocal()
    try:
        print("Starting lightweight daily sync...")
        
        # 1. Get EPL Competition
        epl = db.query(Competition).filter(Competition.code == "EPL").first()
        if not epl:
            print("EPL Competition not found!")
            return
            
        # 2. Get latest season (current season)
        current_season = db.query(Season).order_by(Season.id.desc()).first()
        if not current_season:
            print("No seasons found!")
            return
            
        print(f"Current season identified as: {current_season.label}")
        
        # 3. Download and ingest only the current season CSV
        url = f"https://www.football-data.co.uk/mmz4281/{current_season.season_code}/E0.csv"
        print(f"Downloading current matches from: {url}")
        
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            import csv
            csv_data = response.text.splitlines()
            reader = csv.DictReader(csv_data)
            
            # Load existing team season bindings to avoid duplicate checking
            from app.models import TeamSeason
            added_team_seasons = set(
                [assoc.team_id for assoc in db.query(TeamSeason).filter(TeamSeason.season_id == current_season.id).all()]
            )
            
            matches_count = 0
            for row in reader:
                if not row.get("HomeTeam") or not row.get("AwayTeam") or not row.get("Date"):
                    continue
                
                try:
                    home_name = normalize_team_name(row["HomeTeam"])
                    away_name = normalize_team_name(row["AwayTeam"])
                    
                    home_team = db.query(Team).filter(Team.name == home_name).first()
                    away_team = db.query(Team).filter(Team.name == away_name).first()
                    
                    if not home_team or not away_team:
                        # Fallback to create them if new teams promoted mid-season or seed mismatch
                        if not home_team:
                            home_team = Team(name=home_name, short_name=home_name[:3].upper())
                            db.add(home_team)
                            db.flush()
                        if not away_team:
                            away_team = Team(name=away_name, short_name=away_name[:3].upper())
                            db.add(away_team)
                            db.flush()
                    
                    # Bind to season
                    for team in (home_team, away_team):
                        if team.id not in added_team_seasons:
                            db.add(TeamSeason(team_id=team.id, season_id=current_season.id))
                            added_team_seasons.add(team.id)
                    
                    match_date = parse_date(row["Date"])
                    
                    # Check if match already exists
                    existing_match = db.query(Match).filter(
                        Match.season_id == current_season.id,
                        Match.match_date == match_date,
                        Match.home_team_id == home_team.id,
                        Match.away_team_id == away_team.id
                    ).first()
                    
                    if not existing_match:
                        match = Match(
                            competition_id=epl.id,
                            season_id=current_season.id,
                            match_date=match_date,
                            home_team_id=home_team.id,
                            away_team_id=away_team.id,
                            home_goals=int(row["FTHG"]),
                            away_goals=int(row["FTAG"]),
                            result=row["FTR"].strip(),
                            home_shots=int(row["HS"]) if row.get("HS") else None,
                            away_shots=int(row["AS"]) if row.get("AS") else None,
                            home_shots_on_target=int(row["HST"]) if row.get("HST") else None,
                            away_shots_on_target=int(row["AST"]) if row.get("AST") else None,
                        )
                        db.add(match)
                        matches_count += 1
                except Exception as e:
                    continue
            
            db.commit()
            print(f"Ingested {matches_count} new matches.")
        else:
            print("Failed to fetch latest CSV match results.")
            
        # 4. Recompute standings for the current season only
        # We can call the ingest helper (it will delete and recompute standings for all seasons, 
        # which is fast, taking < 1 second).
        precompute_standings(db, epl)
        
        # 5. Sync player detailed stats for the current season
        # This will query FPL bootstrap elements and player match summaries
        sync_fpl_players_and_summaries(db, epl)
        
        print("Daily sync completed successfully!")
    finally:
        db.close()

if __name__ == "__main__":
    update_current_season_data()
