import csv
import os
import sys
import time
from datetime import datetime

import requests
from sqlalchemy import or_
from sqlalchemy.orm import Session

# Set up python path so we can import from backend
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from app.database import SessionLocal  # noqa: E402
from app.init_db import init_db  # noqa: E402
from app.models import (  # noqa: E402
    Competition,
    GameweekStanding,
    Match,
    Player,
    PlayerMatchStat,
    PlayerSeasonSummary,
    Season,
    Team,
    TeamSeason,
)
from app.pipeline.seed import seed_initial_data  # noqa: E402

# Normalization mapping for team names across CSV and FPL data sources
TEAM_NAME_MAPPING = {
    "Man United": "Manchester United",
    "Man Utd": "Manchester United",
    "Manchester Utd": "Manchester United",
    "Man City": "Manchester City",
    "Manchester City": "Manchester City",
    "Tottenham Hotspur": "Tottenham Hotspur",
    "Tottenham": "Tottenham Hotspur",
    "Spurs": "Tottenham Hotspur",
    "Newcastle United": "Newcastle United",
    "Newcastle Utd": "Newcastle United",
    "Newcastle": "Newcastle United",
    "Luton Town": "Luton",
    "Luton": "Luton",
    "Sheffield United": "Sheffield United",
    "Sheffield Utd": "Sheffield United",
    "Wolverhampton Wanderers": "Wolverhampton Wanderers",
    "Wolves": "Wolverhampton Wanderers",
    "Wolverhampton": "Wolverhampton Wanderers",
    "West Ham United": "West Ham United",
    "West Ham": "West Ham United",
    "Leicester City": "Leicester City",
    "Leicester": "Leicester City",
    "Nottingham Forest": "Nottingham Forest",
    "Nott'm Forest": "Nottingham Forest",
    "Brighton and Hove Albion": "Brighton & Hove Albion",
    "Brighton & Hove Albion": "Brighton & Hove Albion",
    "Brighton": "Brighton & Hove Albion",
    "AFC Bournemouth": "Bournemouth",
    "Bournemouth": "Bournemouth",
    "Cardiff City": "Cardiff City",
    "Cardiff": "Cardiff City",
    "Huddersfield Town": "Huddersfield Town",
    "Huddersfield": "Huddersfield Town",
    "Swansea City": "Swansea City",
    "Swansea": "Swansea City",
    "Stoke City": "Stoke City",
    "Stoke": "Stoke City",
    "West Bromwich Albion": "West Bromwich Albion",
    "West Brom": "West Bromwich Albion",
    "Norwich City": "Norwich City",
    "Norwich": "Norwich City",
    "Leeds United": "Leeds United",
    "Leeds": "Leeds United",
    "Crystal Palace": "Crystal Palace",
    "Everton": "Everton",
    "Liverpool": "Liverpool",
    "Arsenal": "Arsenal",
    "Chelsea": "Chelsea",
    "Aston Villa": "Aston Villa",
    "Brentford": "Brentford",
    "Fulham": "Fulham",
    "Southampton": "Southampton",
    "Burnley": "Burnley",
    "Watford": "Watford",
    "Ipswich": "Ipswich Town",
    "Ipswich Town": "Ipswich Town",
}


def normalize_team_name(name: str) -> str:
    cleaned = name.strip()
    return TEAM_NAME_MAPPING.get(cleaned, cleaned)


def parse_date(date_str: str) -> datetime.date:
    for fmt in ("%d/%m/%y", "%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(date_str.strip(), fmt).date()
        except ValueError:
            pass
    raise ValueError(f"Date format not supported for '{date_str}'")


def download_and_ingest_historical_csvs(db: Session, competition: Competition):
    seasons = db.query(Season).order_by(Season.id).all()

    for season in seasons:
        print(f"\nProcessing season {season.label}...")
        url = f"https://www.football-data.co.uk/mmz4281/{season.season_code}/E0.csv"

        try:
            response = requests.get(url, timeout=15)
            if response.status_code != 200:
                print(f"Failed to fetch CSV for season {season.label} from URL: {url}")
                continue

            csv_data = response.text.splitlines()
            reader = csv.DictReader(csv_data)

            added_team_seasons = set()
            existing_assocs = (
                db.query(TeamSeason).filter(TeamSeason.season_id == season.id).all()
            )
            for assoc in existing_assocs:
                added_team_seasons.add(assoc.team_id)

            matches_count = 0
            for row in reader:
                # Basic validation
                if (
                    not row.get("HomeTeam")
                    or not row.get("AwayTeam")
                    or not row.get("Date")
                ):
                    continue

                try:
                    home_name = normalize_team_name(row["HomeTeam"])
                    away_name = normalize_team_name(row["AwayTeam"])

                    # Create teams if not exist
                    home_team = db.query(Team).filter(Team.name == home_name).first()
                    if not home_team:
                        home_team = Team(
                            name=home_name, short_name=home_name[:3].upper()
                        )
                        db.add(home_team)
                        db.flush()

                    away_team = db.query(Team).filter(Team.name == away_name).first()
                    if not away_team:
                        away_team = Team(
                            name=away_name, short_name=away_name[:3].upper()
                        )
                        db.add(away_team)
                        db.flush()

                    # Create TeamSeason mapping if not exist
                    for team in (home_team, away_team):
                        if team.id not in added_team_seasons:
                            db.add(TeamSeason(team_id=team.id, season_id=season.id))
                            added_team_seasons.add(team.id)

                    match_date = parse_date(row["Date"])

                    # Check if match already exists
                    existing_match = (
                        db.query(Match)
                        .filter(
                            Match.season_id == season.id,
                            Match.match_date == match_date,
                            Match.home_team_id == home_team.id,
                            Match.away_team_id == away_team.id,
                        )
                        .first()
                    )

                    if not existing_match:
                        match = Match(
                            competition_id=competition.id,
                            season_id=season.id,
                            match_date=match_date,
                            home_team_id=home_team.id,
                            away_team_id=away_team.id,
                            home_goals=int(row["FTHG"]),
                            away_goals=int(row["FTAG"]),
                            result=row["FTR"].strip(),
                            home_shots=int(row["HS"]) if row.get("HS") else None,
                            away_shots=int(row["AS"]) if row.get("AS") else None,
                            home_shots_on_target=int(row["HST"])
                            if row.get("HST")
                            else None,
                            away_shots_on_target=int(row["AST"])
                            if row.get("AST")
                            else None,
                        )
                        db.add(match)
                        matches_count += 1
                except Exception as e:
                    # Skip corrupt rows but log them
                    print(f"Skipped match row error: {e}")
                    continue

            db.commit()
            print(f"Ingested {matches_count} matches for season {season.label}")

        except Exception as e:
            print(f"Error fetching season {season.label}: {e}")
            db.rollback()


def precompute_standings(db: Session, competition: Competition):
    seasons = db.query(Season).all()
    print("\nPrecomputing standings round-by-round...")

    # Delete existing standings to recompute cleanly
    db.query(GameweekStanding).filter(
        GameweekStanding.competition_id == competition.id
    ).delete()
    db.commit()

    for season in seasons:
        print(f"Computing for season {season.label}...")

        # Get all matches for this season in chronological order
        matches = (
            db.query(Match)
            .filter(
                Match.season_id == season.id, Match.competition_id == competition.id
            )
            .order_by(Match.match_date)
            .all()
        )

        if not matches:
            continue

        # Track stats for each team
        teams_stats = {}
        # Track matches played count to identify the team's N-th game
        teams_matches_played = {}

        # Initialize stats for teams in this season
        team_seasons = (
            db.query(TeamSeason).filter(TeamSeason.season_id == season.id).all()
        )
        for ts in team_seasons:
            teams_stats[ts.team_id] = {
                "played": 0,
                "wins": 0,
                "draws": 0,
                "losses": 0,
                "goals_for": 0,
                "goals_against": 0,
                "points": 0,
            }
            teams_matches_played[ts.team_id] = []

        # Group matches chronologically per team
        for match in matches:
            # Skip matches with invalid teams (shouldn't happen)
            if (
                match.home_team_id not in teams_stats
                or match.away_team_id not in teams_stats
            ):
                continue

            teams_matches_played[match.home_team_id].append(match)
            teams_matches_played[match.away_team_id].append(match)

        # We will precompute the standings for round 1 to 38
        # For each round R:
        # We compute the state of every team after they have played exactly R games.
        # If the season is in progress, some teams might not have played R games yet.
        # We only compute standing up to the maximum round that at least one team has reached.
        max_games_played = (
            max([len(m_list) for m_list in teams_matches_played.values()])
            if teams_matches_played
            else 0
        )

        for round_num in range(1, max_games_played + 1):
            round_teams_data = []

            for team_id, match_list in teams_matches_played.items():
                # Calculate statistics up to the round_num-th match for this team
                # Skip if team hasn't played round_num matches yet
                if len(match_list) < round_num:
                    continue

                played = 0
                wins = 0
                draws = 0
                losses = 0
                goals_for = 0
                goals_against = 0
                points = 0

                # Iterate over the first `round_num` matches of this team
                for i in range(round_num):
                    m = match_list[i]
                    is_home = m.home_team_id == team_id

                    goals_scored = m.home_goals if is_home else m.away_goals
                    goals_conceded = m.away_goals if is_home else m.home_goals

                    goals_for += goals_scored
                    goals_against += goals_conceded
                    played += 1

                    # Calculate result
                    if m.result == "D":
                        draws += 1
                        points += 1
                    elif (m.result == "H" and is_home) or (
                        m.result == "A" and not is_home
                    ):
                        wins += 1
                        points += 3
                    else:
                        losses += 1

                round_teams_data.append(
                    {
                        "team_id": team_id,
                        "played": played,
                        "wins": wins,
                        "draws": draws,
                        "losses": losses,
                        "goals_for": goals_for,
                        "goals_against": goals_against,
                        "goal_difference": goals_for - goals_against,
                        "points": points,
                    }
                )

            # Rank teams for this round
            # Standard EPL ranking rules: Points desc, GD desc, GS desc, Name asc
            def get_ranking_key(team_data):
                team = db.query(Team).filter(Team.id == team_data["team_id"]).first()
                team_name = team.name if team else ""
                # We return a tuple where numbers we want descending are negated
                return (
                    -team_data["points"],
                    -team_data["goal_difference"],
                    -team_data["goals_for"],
                    team_name,
                )

            sorted_teams = sorted(round_teams_data, key=get_ranking_key)

            # Save standings to DB
            for idx, team_data in enumerate(sorted_teams):
                standing = GameweekStanding(
                    competition_id=competition.id,
                    season_id=season.id,
                    team_id=team_data["team_id"],
                    gameweek=round_num,
                    points=team_data["points"],
                    played=team_data["played"],
                    wins=team_data["wins"],
                    draws=team_data["draws"],
                    losses=team_data["losses"],
                    goals_for=team_data["goals_for"],
                    goals_against=team_data["goals_against"],
                    goal_difference=team_data["goal_difference"],
                    position=idx + 1,
                )
                db.add(standing)

        db.commit()
    print("Standings precomputation completed successfully!")


def sync_fpl_players_and_summaries(db: Session, competition: Competition):
    print("\nSyncing players and summaries from Fantasy Premier League (FPL) API...")
    bootstrap_url = "https://fantasy.premierleague.com/api/bootstrap-static/"

    try:
        response = requests.get(bootstrap_url, timeout=15)
        if response.status_code != 200:
            print("Failed to contact FPL bootstrap endpoint.")
            return

        data = response.json()

        # Map FPL team IDs to our database Team IDs
        fpl_teams = data.get("teams", [])
        fpl_team_to_db_id = {}
        for fpl_t in fpl_teams:
            name = normalize_team_name(fpl_t["name"])
            db_team = db.query(Team).filter(Team.name == name).first()
            if db_team:
                db_team.fpl_id = fpl_t["id"]
                fpl_team_to_db_id[fpl_t["id"]] = db_team.id

        db.commit()

        # Map FPL element types to positions
        position_mapping = {1: "GK", 2: "DEF", 3: "MID", 4: "FWD"}

        fpl_players = data.get("elements", [])
        print(f"Found {len(fpl_players)} players in FPL. Syncing metadata...")

        active_player_ids = []
        for fp in fpl_players:
            first_name = fp["first_name"].strip()
            second_name = fp["second_name"].strip()
            position = position_mapping.get(fp["element_type"], "MID")
            current_fpl_id = fp["id"]

            # Check if player exists by name/fpl_id
            player = (
                db.query(Player).filter(Player.current_fpl_id == current_fpl_id).first()
            )
            if not player:
                player = (
                    db.query(Player)
                    .filter(
                        Player.first_name == first_name,
                        Player.second_name == second_name,
                    )
                    .first()
                )

            if not player:
                player = Player(
                    first_name=first_name,
                    second_name=second_name,
                    position=position,
                    current_fpl_id=current_fpl_id,
                    fpl_team_id=fp.get("team"),
                )
                db.add(player)
            else:
                player.current_fpl_id = current_fpl_id
                player.position = position
                player.fpl_team_id = fp.get("team")

            db.flush()
            active_player_ids.append(
                (player.id, current_fpl_id, f"{first_name} {second_name}")
            )

        db.commit()

        # Fetch detailed history summaries for players
        # To avoid overloading the FPL API or slowing down execution excessively,
        # we will fetch the detailed season history only.
        print("\nFetching player multi-season historical summaries...")

        # We will loop over players and get their summary
        count = 0
        total = len(active_player_ids)

        for db_id, fpl_id, full_name in active_player_ids:
            count += 1
            if count % 50 == 0:
                print(f"Processed {count}/{total} players...")

            summary_url = (
                f"https://fantasy.premierleague.com/api/element-summary/{fpl_id}/"
            )

            try:
                # Small rate-limit delay
                time.sleep(0.04)

                resp = requests.get(summary_url, timeout=10)
                if resp.status_code != 200:
                    continue

                p_data = resp.json()

                # Parse historical seasons (`history_past`)
                history_past = p_data.get("history_past", [])
                for hp in history_past:
                    # Match FPL season label (e.g. "2022/23") to our label format (e.g. "2022-2023")
                    fpl_season_label = hp["season_name"]
                    parts = fpl_season_label.split("/")
                    if len(parts) == 2:
                        # e.g., "2022/23" -> "2022-2023"
                        start_yr = parts[0]
                        end_yr = start_yr[:2] + parts[1]
                        normalized_label = f"{start_yr}-{end_yr}"
                    else:
                        normalized_label = fpl_season_label

                    season_record = (
                        db.query(Season)
                        .filter(Season.label == normalized_label)
                        .first()
                    )
                    if not season_record:
                        continue

                    # Save summary
                    existing_summary = (
                        db.query(PlayerSeasonSummary)
                        .filter(
                            PlayerSeasonSummary.player_id == db_id,
                            PlayerSeasonSummary.season_id == season_record.id,
                            PlayerSeasonSummary.competition_id == competition.id,
                        )
                        .first()
                    )

                    if not existing_summary:
                        summary = PlayerSeasonSummary(
                            player_id=db_id,
                            season_id=season_record.id,
                            competition_id=competition.id,
                            minutes=hp.get("minutes", 0),
                            goals=hp.get("goals_scored", 0),
                            assists=hp.get("assists", 0),
                            clean_sheets=hp.get("clean_sheets", 0),
                            yellow_cards=hp.get("yellow_cards", 0),
                            red_cards=hp.get("red_cards", 0),
                            fpl_points=hp.get("total_points", 0),
                        )
                        db.add(summary)
                    else:
                        existing_summary.minutes = hp.get("minutes", 0)
                        existing_summary.goals = hp.get("goals_scored", 0)
                        existing_summary.assists = hp.get("assists", 0)
                        existing_summary.clean_sheets = hp.get("clean_sheets", 0)
                        existing_summary.yellow_cards = hp.get("yellow_cards", 0)
                        existing_summary.red_cards = hp.get("red_cards", 0)
                        existing_summary.fpl_points = hp.get("total_points", 0)

                # Parse current season's detailed matches (`history` array)
                # This populates PlayerMatchStat for the current season matches
                current_season_record = (
                    db.query(Season).order_by(Season.id.desc()).first()
                )  # Latest season
                if current_season_record:
                    history = p_data.get("history", [])
                    for h in history:
                        opponent_fpl_id = h["opponent_team"]
                        kickoff_str = h.get(
                            "kickoff_time"
                        )  # e.g. "2026-05-18T19:00:00Z"

                        if kickoff_str:
                            try:
                                kickoff_date = datetime.strptime(
                                    kickoff_str[:10], "%Y-%m-%d"
                                ).date()
                            except ValueError:
                                continue

                            opponent_db_team = (
                                db.query(Team)
                                .filter(Team.fpl_id == opponent_fpl_id)
                                .first()
                            )
                            if opponent_db_team:
                                # Find match by season, date, and opponent participation
                                match_record = (
                                    db.query(Match)
                                    .filter(
                                        Match.season_id == current_season_record.id,
                                        Match.match_date == kickoff_date,
                                        or_(
                                            Match.home_team_id == opponent_db_team.id,
                                            Match.away_team_id == opponent_db_team.id,
                                        ),
                                    )
                                    .first()
                                )

                                if match_record:
                                    existing_match_stat = (
                                        db.query(PlayerMatchStat)
                                        .filter(
                                            PlayerMatchStat.match_id == match_record.id,
                                            PlayerMatchStat.player_id == db_id,
                                        )
                                        .first()
                                    )

                                    if not existing_match_stat:
                                        match_stat = PlayerMatchStat(
                                            match_id=match_record.id,
                                            player_id=db_id,
                                            minutes=h.get("minutes", 0),
                                            goals=h.get("goals_scored", 0),
                                            assists=h.get("assists", 0),
                                            clean_sheets=h.get("clean_sheets", 0),
                                            yellow_cards=h.get("yellow_cards", 0),
                                            red_cards=h.get("red_cards", 0),
                                            fpl_points=h.get("total_points", 0),
                                        )
                                        db.add(match_stat)
                                    else:
                                        existing_match_stat.minutes = h.get(
                                            "minutes", 0
                                        )
                                        existing_match_stat.goals = h.get(
                                            "goals_scored", 0
                                        )
                                        existing_match_stat.assists = h.get(
                                            "assists", 0
                                        )
                                        existing_match_stat.clean_sheets = h.get(
                                            "clean_sheets", 0
                                        )
                                        existing_match_stat.yellow_cards = h.get(
                                            "yellow_cards", 0
                                        )
                                        existing_match_stat.red_cards = h.get(
                                            "red_cards", 0
                                        )
                                        existing_match_stat.fpl_points = h.get(
                                            "total_points", 0
                                        )

            except Exception as ex:
                print(f"Error loading summary for FPL ID {fpl_id}: {ex}")
                continue

        db.commit()
        print("FPL sync completed successfully!")
    except Exception as e:
        print(f"Error in FPL sync: {e}")
        db.rollback()


def run_pipeline():
    # 1. Initialize tables
    init_db()

    # 2. Seed initial static data
    seed_initial_data()

    db = SessionLocal()
    try:
        # Get Premier League competition
        epl = db.query(Competition).filter(Competition.code == "EPL").first()
        if not epl:
            print("EPL Competition not seeded properly!")
            return

        # 3. Download and ingest CSV results
        download_and_ingest_historical_csvs(db, epl)

        # 4. Precompute standings
        precompute_standings(db, epl)

        # 5. Sync FPL Players and historical summaries
        sync_fpl_players_and_summaries(db, epl)

        print("\nAll Ingestion Tasks Completed Successfully!")
    finally:
        db.close()


if __name__ == "__main__":
    run_pipeline()
