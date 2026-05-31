from contextlib import asynccontextmanager
from datetime import datetime
from typing import List, Optional

from app import crud, schemas
from app.database import get_db
from app.models import Player
from app.pipeline.sync_external import (
    LIVE_KEY,
    UPCOMING_KEY,
    _fmt_fixture,
    sync_live_matches,
    sync_match_analytics,
    sync_player_advanced_stats,
    sync_player_profiles,
    sync_upcoming_fixtures,
)
from app.services import api_football, cache
from app.services.cache import (
    CURR_TTL,
    HIST_TTL,
    PLAYER_TTL,
    UPCOMING_TTL,
    get_current_season_id,
    get_or_fetch,
    season_ttl,
)
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

scheduler = BackgroundScheduler(timezone="UTC")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Requires API-Football Ultra plan — comment back in when upgraded
    # scheduler.add_job(sync_live_matches, "interval", seconds=60, id="live", replace_existing=True)
    scheduler.add_job(
        sync_upcoming_fixtures,
        "interval",
        minutes=5,
        id="upcoming",
        replace_existing=True,
    )
    scheduler.add_job(
        sync_match_analytics,
        "interval",
        hours=2,
        id="match_analytics",
        replace_existing=True,
    )
    scheduler.add_job(
        sync_player_profiles,
        "cron",
        hour=3,
        id="player_profiles",
        replace_existing=True,
    )
    scheduler.add_job(
        sync_player_advanced_stats,
        "cron",
        day_of_week="mon",
        hour=4,
        id="player_adv",
        replace_existing=True,
    )
    scheduler.start()
    sync_upcoming_fixtures()
    yield
    scheduler.shutdown(wait=False)


app = FastAPI(
    title="Premier League Stats & Performance Tracker API",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Seasons & teams (tiny, no caching needed) ─────────────────────────────────


@app.get("/api/seasons", response_model=List[schemas.SeasonSchema])
def read_seasons(db: Session = Depends(get_db)):
    return crud.get_seasons(db)


@app.get("/api/teams", response_model=List[schemas.TeamSchema])
def read_teams(
    season_id: Optional[int] = Query(None),
    query: Optional[str] = Query(None, description="Filter teams by name"),
    db: Session = Depends(get_db),
):
    teams = crud.get_teams(db, season_id=season_id)
    if query and query.strip():
        q = query.strip().lower()
        teams = [t for t in teams if q in t.name.lower() or q in t.short_name.lower()]
    return teams


# ── Standings ─────────────────────────────────────────────────────────────────


@app.get("/api/standings", response_model=schemas.StandingsResponse)
def read_standings(
    season_id: int = Query(...),
    gameweek: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    curr = get_current_season_id(db)
    ttl, sliding = season_ttl(season_id, curr)
    gw_label = gameweek or "latest"
    key = f"standings:{season_id}:{gw_label}"

    def fetch():
        season = db.query(crud.Season).filter(crud.Season.id == season_id).first()
        if not season:
            return None
        standings = crud.get_standings(db, season_id=season_id, gameweek=gameweek)
        actual_gw = gameweek or (standings[0].gameweek if standings else 0)
        return schemas.StandingsResponse(
            season_label=season.label,
            gameweek=actual_gw,
            standings=[
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
                    position=item.position,
                )
                for item in standings
            ],
        )

    result = get_or_fetch(key, fetch, ttl=ttl, sliding=sliding)
    if result is None:
        raise HTTPException(status_code=404, detail="Season not found")
    return result


@app.get("/api/standings/history")
def read_standings_history(
    season_id: int = Query(...),
    db: Session = Depends(get_db),
):
    curr = get_current_season_id(db)
    ttl, sliding = season_ttl(season_id, curr)
    key = f"standings_history:{season_id}"

    def fetch():
        items = crud.get_standings_history(db, season_id)
        history_by_team: dict = {}
        for item in items:
            name = item.team.name
            history_by_team.setdefault(name, []).append(
                {
                    "gameweek": item.gameweek,
                    "position": item.position,
                    "points": item.points,
                }
            )
        max_gw = max((i.gameweek for i in items), default=0)
        chart_data = []
        for gw in range(1, max_gw + 1):
            row: dict = {"gameweek": gw}
            for name, gw_list in history_by_team.items():
                match = next((x for x in gw_list if x["gameweek"] == gw), None)
                if match:
                    row[name] = match["position"]
            chart_data.append(row)
        return chart_data

    return get_or_fetch(key, fetch, ttl=ttl, sliding=sliding)


# ── Team form & season compare ────────────────────────────────────────────────


@app.get("/api/teams/{team_id}/form", response_model=schemas.TeamFormResponse)
def read_team_form(
    team_id: int,
    season_id: int = Query(...),
    last_x: int = Query(5),
    db: Session = Depends(get_db),
):
    curr = get_current_season_id(db)
    ttl, sliding = season_ttl(season_id, curr)
    key = f"team_form:{team_id}:{season_id}:{last_x}"

    def fetch():
        team = crud.get_team_by_id(db, team_id)
        if not team:
            return None
        matches_form, form_str = crud.get_team_form(db, team_id, season_id, last_x)
        return schemas.TeamFormResponse(
            team=schemas.TeamSchema.from_orm(team),
            form_string=form_str,
            matches=[schemas.TeamFormMatchSchema(**m) for m in matches_form],
        )

    result = get_or_fetch(key, fetch, ttl=ttl, sliding=sliding)
    if result is None:
        raise HTTPException(status_code=404, detail="Team not found")
    return result


@app.get("/api/teams/{team_id}/seasons-compare")
def compare_team_seasons(
    team_id: int,
    seasons: str = Query(...),
    db: Session = Depends(get_db),
):
    from sqlalchemy import or_

    try:
        season_ids = [int(s) for s in seasons.split(",") if s.strip()]
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid season IDs")

    curr = get_current_season_id(db)
    # Use the most conservative TTL across all requested seasons
    has_current = any(sid >= curr for sid in season_ids)
    ttl = CURR_TTL if has_current else HIST_TTL
    sliding = not has_current
    key = f"seasons_compare:{team_id}:{'-'.join(str(s) for s in sorted(season_ids))}"

    def fetch():
        db_seasons = db.query(crud.Season).filter(crud.Season.id.in_(season_ids)).all()
        season_label = {s.id: s.label for s in db_seasons}

        matches = (
            db.query(crud.Match)
            .filter(
                crud.Match.season_id.in_(season_ids),
                or_(
                    crud.Match.home_team_id == team_id,
                    crud.Match.away_team_id == team_id,
                ),
            )
            .order_by(crud.Match.season_id, crud.Match.match_date)
            .all()
        )

        matches_by_season: dict = {}
        for m in matches:
            matches_by_season.setdefault(m.season_id, []).append(m)

        standings = (
            db.query(crud.GameweekStanding)
            .filter(
                crud.GameweekStanding.team_id == team_id,
                crud.GameweekStanding.season_id.in_(season_ids),
            )
            .all()
        )
        standings_map = {(s.season_id, s.gameweek): s for s in standings}

        chart_data = []
        for gw in range(1, 39):
            row: dict = {"gameweek": gw}
            has_data = False
            for sid in season_ids:
                lbl = season_label.get(sid)
                if not lbl:
                    continue
                standing = standings_map.get((sid, gw))
                season_matches = matches_by_season.get(sid, [])
                match = season_matches[gw - 1] if len(season_matches) >= gw else None
                if standing:
                    row[lbl] = standing.position
                    has_data = True
                    if match:
                        is_home = match.home_team_id == team_id
                        opp = match.away_team if is_home else match.home_team
                        gf = match.home_goals if is_home else match.away_goals
                        ga = match.away_goals if is_home else match.home_goals
                        res = (
                            "D"
                            if match.result == "D"
                            else (
                                "W"
                                if (match.result == "H" and is_home)
                                or (match.result == "A" and not is_home)
                                else "L"
                            )
                        )
                        row[f"{lbl}_date"] = match.match_date.isoformat()
                        row[f"{lbl}_opponent"] = opp.name if opp else "Unknown"
                        row[f"{lbl}_score"] = f"{gf} - {ga}"
                        row[f"{lbl}_result"] = res
            if has_data:
                chart_data.append(row)
        return chart_data

    return get_or_fetch(key, fetch, ttl=ttl, sliding=sliding)


# ── Players ───────────────────────────────────────────────────────────────────


@app.get("/api/players", response_model=List[schemas.PlayerSchema])
def read_players(
    query: Optional[str] = Query(None),
    team_internal_id: Optional[int] = Query(
        None, description="Filter by internal team DB ID"
    ),
    db: Session = Depends(get_db),
):
    key = f"player_search:{(query or '').strip().lower()}:{team_internal_id or ''}"
    cached = cache.get_cached(key)
    if cached is not None:
        return cached
    results = crud.get_players(
        db, search_query=query, team_internal_id=team_internal_id
    )
    serialised = [schemas.PlayerSchema.from_orm(p).dict() for p in results]
    cache.set_cached(key, serialised, ttl=300)
    return results


@app.get("/api/players/compare", response_model=List[schemas.PlayerDetailSchema])
def compare_players(
    ids: str = Query(...),
    db: Session = Depends(get_db),
):
    try:
        player_ids = [int(pid) for pid in ids.split(",") if pid.strip()]
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid player IDs")
    return [d for pid in player_ids if (d := _get_player_detail_cached(db, pid))]


@app.get("/api/players/{player_id}", response_model=schemas.PlayerDetailSchema)
def read_player(player_id: int, db: Session = Depends(get_db)):
    detail = _get_player_detail_cached(db, player_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Player not found")
    return detail


@app.get("/api/players/{player_id}/profile", response_model=schemas.PlayerProfileSchema)
def get_player_profile_route(player_id: int, db: Session = Depends(get_db)):
    key = f"player_profile:{player_id}"

    def fetch():
        profile = (
            db.query(crud.PlayerProfile)
            .filter(crud.PlayerProfile.player_id == player_id)
            .first()
        )
        return schemas.PlayerProfileSchema.from_orm(profile) if profile else None

    result = get_or_fetch(key, fetch, ttl=PLAYER_TTL, sliding=True)
    if result is None:
        raise HTTPException(
            status_code=404, detail="Profile not yet synced for this player"
        )
    return result


@app.get(
    "/api/players/{player_id}/advanced",
    response_model=List[schemas.PlayerAdvancedStatsSchema],
)
def get_player_advanced(player_id: int, db: Session = Depends(get_db)):
    key = f"player_advanced:{player_id}"

    def fetch():
        stats = crud.get_player_advanced_stats(db, player_id)
        return [
            schemas.PlayerAdvancedStatsSchema(
                season_label=s.season.label,
                xg=s.xg,
                xa=s.xa,
                npxg=s.npxg,
                xg_per_90=s.xg_per_90,
                xa_per_90=s.xa_per_90,
                progressive_carries=s.progressive_carries,
                progressive_passes=s.progressive_passes,
                progressive_receptions=s.progressive_receptions,
                shots=s.shots,
                shots_on_target=s.shots_on_target,
            )
            for s in stats
        ] or None

    return get_or_fetch(key, fetch, ttl=PLAYER_TTL, sliding=True) or []


@app.get(
    "/api/players/lookup/api-football/{api_football_id}",
    response_model=schemas.PlayerSchema,
)
def lookup_player_by_api_football_id(
    api_football_id: int, db: Session = Depends(get_db)
):
    """Lookup internal player by API-Football player ID"""
    player = db.query(Player).filter(Player.api_football_id == api_football_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    return schemas.PlayerSchema.from_orm(player)


# ── Teams ─────────────────────────────────────────────────────────────────────


@app.get("/api/teams/{team_id}/profile", response_model=schemas.TeamProfileSchema)
def get_team_profile_route(team_id: int, db: Session = Depends(get_db)):
    key = f"team_profile:{team_id}"

    def fetch():
        profile = (
            db.query(crud.TeamProfile)
            .filter(crud.TeamProfile.team_id == team_id)
            .first()
        )
        return schemas.TeamProfileSchema.from_orm(profile) if profile else None

    result = get_or_fetch(key, fetch, ttl=PLAYER_TTL, sliding=True)
    if result is None:
        raise HTTPException(
            status_code=404, detail="Profile not yet synced for this team"
        )
    return result


@app.get("/api/teams/{team_id}/squad")
def get_team_squad(team_id: int, db: Session = Depends(get_db)):
    key = f"squad:{team_id}"
    cached = cache.get_cached(key, sliding_ttl=PLAYER_TTL)
    if cached:
        return cached
    team = crud.get_team_by_id(db, team_id)
    if not team or not team.api_football_id:
        raise HTTPException(
            status_code=404, detail="Team has no API-Football ID mapped"
        )
    squad = api_football.get_team_squad(team.api_football_id)
    result = [
        {
            "id": p.get("id"),
            "name": p.get("name"),
            "age": p.get("age"),
            "number": p.get("number"),
            "position": p.get("position"),
            "photo": p.get("photo"),
        }
        for p in squad
    ]
    cache.set_cached(key, result, ttl=PLAYER_TTL)
    return result


# ── Live & fixtures ───────────────────────────────────────────────────────────


@app.get("/api/live", response_model=schemas.FixturesResponseSchema)
def get_live():
    cached = cache.get_cached(LIVE_KEY)
    if cached:
        return cached
    # Live fixtures require API-Football Ultra plan.
    # Returns empty until the scheduler job is enabled.
    return {"fixtures": [], "cached_at": datetime.utcnow().isoformat()}


@app.get("/api/fixtures", response_model=schemas.FixturesResponseSchema)
def get_upcoming_fixtures_route():
    cached = cache.get_cached(UPCOMING_KEY)
    if cached:
        return cached
    raw = api_football.get_upcoming_fixtures(days_ahead=7)
    payload = {
        "fixtures": [_fmt_fixture(f) for f in raw],
        "cached_at": datetime.utcnow().isoformat(),
    }
    cache.set_cached(UPCOMING_KEY, payload, ttl=UPCOMING_TTL)
    return payload


# ── Match detail ──────────────────────────────────────────────────────────────


@app.get(
    "/api/fixtures/{fixture_id}/events", response_model=List[schemas.MatchEventSchema]
)
def get_fixture_events(fixture_id: int, db: Session = Depends(get_db)):
    key = f"match_events:{fixture_id}"

    def fetch():
        stored = crud.get_match_events(db, fixture_id)
        if stored:
            return [schemas.MatchEventSchema.from_orm(e).dict() for e in stored]
        raw = api_football.get_fixture_events(fixture_id)
        if not raw:
            return []
        entries = [
            {
                "minute": ev.get("time", {}).get("elapsed"),
                "extra_minute": ev.get("time", {}).get("extra"),
                "event_type": ev.get("type", ""),
                "detail": ev.get("detail"),
                "team_name": ev.get("team", {}).get("name"),
                "player_name": ev.get("player", {}).get("name"),
                "assist_name": ev.get("assist", {}).get("name"),
                "comments": ev.get("comments"),
            }
            for ev in raw
        ]
        crud.store_match_events(db, fixture_id, entries)
        return entries

    # Events for a completed fixture never change → HIST_TTL, sliding
    return get_or_fetch(key, fetch, ttl=HIST_TTL, sliding=True) or []


@app.get(
    "/api/fixtures/{fixture_id}/lineups", response_model=List[schemas.TeamLineupSchema]
)
def get_fixture_lineups(fixture_id: int, db: Session = Depends(get_db)):
    key = f"match_lineups:{fixture_id}"

    def fetch():
        stored = crud.get_match_lineups(db, fixture_id)
        if not stored:
            raw = api_football.get_fixture_lineups(fixture_id)
            entries = []
            for team_data in raw:
                team_name = team_data.get("team", {}).get("name", "")
                formation = team_data.get("formation")
                for p in team_data.get("startXI", []):
                    pi = p.get("player", {})
                    entries.append(
                        {
                            "team_name": team_name,
                            "formation": formation,
                            "player_name": pi.get("name", ""),
                            "player_api_id": pi.get("id"),
                            "is_starter": True,
                            "position": pi.get("pos"),
                            "grid": pi.get("grid"),
                            "shirt_number": pi.get("number"),
                        }
                    )
                for p in team_data.get("substitutes", []):
                    pi = p.get("player", {})
                    entries.append(
                        {
                            "team_name": team_name,
                            "formation": formation,
                            "player_name": pi.get("name", ""),
                            "player_api_id": pi.get("id"),
                            "is_starter": False,
                            "position": pi.get("pos"),
                            "grid": None,
                            "shirt_number": pi.get("number"),
                        }
                    )
            if entries:
                crud.store_match_lineups(db, fixture_id, entries)
            stored = crud.get_match_lineups(db, fixture_id)

        teams: dict = {}
        for row in stored:
            t = teams.setdefault(
                row.team_name,
                {
                    "team_name": row.team_name,
                    "formation": row.formation,
                    "starters": [],
                    "substitutes": [],
                },
            )
            player = schemas.LineupPlayerSchema(
                name=row.player_name,
                shirt_number=row.shirt_number,
                position=row.position,
                grid=row.grid,
                is_starter=row.is_starter,
            )
            (t["starters"] if row.is_starter else t["substitutes"]).append(
                player.dict()
            )
        return [v for v in teams.values()]

    return get_or_fetch(key, fetch, ttl=HIST_TTL, sliding=True) or []


@app.get(
    "/api/fixtures/{fixture_id}/analytics",
    response_model=schemas.MatchAdvancedStatsSchema,
)
def get_fixture_analytics(fixture_id: int, db: Session = Depends(get_db)):
    key = f"match_analytics:{fixture_id}"

    def fetch():
        stats = crud.get_match_advanced_stats(db, fixture_id)
        return (
            schemas.MatchAdvancedStatsSchema.from_orm(stats).dict() if stats else None
        )

    result = get_or_fetch(key, fetch, ttl=HIST_TTL, sliding=True)
    if result is None:
        raise HTTPException(
            status_code=404, detail="Analytics not yet available for this match"
        )
    return result


# ── Head-to-head ──────────────────────────────────────────────────────────────


@app.get("/api/head2head", response_model=List[schemas.H2HMatchSchema])
def head_to_head(
    team_a: int = Query(...),
    team_b: int = Query(...),
    limit: int = Query(10),
    db: Session = Depends(get_db),
):
    key = f"h2h:{min(team_a, team_b)}:{max(team_a, team_b)}:{limit}"

    def fetch():
        matches = crud.get_head_to_head(db, team_a, team_b, limit)
        results = []
        for m in matches:
            season = db.query(crud.Season).filter(crud.Season.id == m.season_id).first()
            results.append(
                schemas.H2HMatchSchema(
                    match_date=m.match_date,
                    season_label=season.label if season else "",
                    home_team=m.home_team.name,
                    away_team=m.away_team.name,
                    home_goals=m.home_goals,
                    away_goals=m.away_goals,
                    result=m.result,
                ).dict()
            )
        return results

    # H2H spans all seasons; use CURR_TTL since current season is included
    return get_or_fetch(key, fetch, ttl=CURR_TTL, sliding=False) or []


# ── Private helper ────────────────────────────────────────────────────────────


def _get_player_detail_cached(db: Session, player_id: int):
    key = f"player_detail:{player_id}"

    def fetch():
        player = crud.get_player_by_id(db, player_id)
        if not player:
            return None

        summaries = crud.get_player_season_summaries(db, player_id)
        # Get more than 10 to account for matches with 0 minutes after filtering
        recent_all = crud.get_player_recent_stats(db, player_id, limit=20)
        # Filter to only matches where player actually played (minutes > 0)
        recent = [r for r in recent_all if r.minutes > 0][:10]
        adv_stats = crud.get_player_advanced_stats(db, player_id)
        profile_db = (
            db.query(crud.PlayerProfile)
            .filter(crud.PlayerProfile.player_id == player_id)
            .first()
        )

        summary_schemas = [
            schemas.PlayerSeasonSummarySchema(
                season_label=s.season.label,
                minutes=s.minutes,
                goals=s.goals,
                assists=s.assists,
                clean_sheets=s.clean_sheets,
                yellow_cards=s.yellow_cards,
                red_cards=s.red_cards,
                fpl_points=s.fpl_points,
            )
            for s in summaries
        ]

        recent_schemas = []
        for r in recent:
            home_team = (
                db.query(crud.Team).filter(crud.Team.id == r.match.home_team_id).first()
            )
            away_team = (
                db.query(crud.Team).filter(crud.Team.id == r.match.away_team_id).first()
            )
            opponent = None

            # Determine opponent based on player's team
            if player.fpl_team_id and home_team and away_team:
                if home_team.fpl_id == player.fpl_team_id:
                    opponent = away_team  # Player is home, opponent is away
                elif away_team.fpl_id == player.fpl_team_id:
                    opponent = home_team  # Player is away, opponent is home

            # Fallback if fpl_team_id match fails
            if not opponent:
                opponent = away_team

            recent_schemas.append(
                schemas.PlayerMatchStatSchema(
                    gameweek=r.match.gameweek or 0,
                    opponent_name=opponent.name if opponent else "Unknown",
                    minutes=r.minutes,
                    goals=r.goals,
                    assists=r.assists,
                    clean_sheets=r.clean_sheets,
                    yellow_cards=r.yellow_cards,
                    red_cards=r.red_cards,
                    fpl_points=r.fpl_points,
                )
            )

        adv_schemas = [
            schemas.PlayerAdvancedStatsSchema(
                season_label=a.season.label,
                xg=a.xg,
                xa=a.xa,
                npxg=a.npxg,
                xg_per_90=a.xg_per_90,
                xa_per_90=a.xa_per_90,
                progressive_carries=a.progressive_carries,
                progressive_passes=a.progressive_passes,
                progressive_receptions=a.progressive_receptions,
                shots=a.shots,
                shots_on_target=a.shots_on_target,
            )
            for a in adv_stats
        ] or None

        # Get player's current team
        team_name = None
        if player.fpl_team_id:
            team = (
                db.query(crud.Team)
                .filter(crud.Team.fpl_id == player.fpl_team_id)
                .first()
            )
            team_name = team.name if team else None

        return schemas.PlayerDetailSchema(
            player=schemas.PlayerSchema.from_orm(player),
            profile=schemas.PlayerProfileSchema.from_orm(profile_db)
            if profile_db
            else None,
            team_name=team_name,
            summaries=summary_schemas,
            recent_stats=recent_schemas,
            advanced_stats=adv_schemas,
        )

    # Player data spans seasons; cache for 1 week with sliding expiry
    return get_or_fetch(key, fetch, ttl=PLAYER_TTL, sliding=True)


# ── Top-5 European leagues ────────────────────────────────────────────────────

TOP5_LEAGUES = [
    {
        "id": 39,
        "name": "Premier League",
        "country": "England",
        "flag": "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
        "logo": "https://media.api-sports.io/football/leagues/39.png",
    },
    {
        "id": 140,
        "name": "La Liga",
        "country": "Spain",
        "flag": "🇪🇸",
        "logo": "https://media.api-sports.io/football/leagues/140.png",
    },
    {
        "id": 135,
        "name": "Serie A",
        "country": "Italy",
        "flag": "🇮🇹",
        "logo": "https://media.api-sports.io/football/leagues/135.png",
    },
    {
        "id": 78,
        "name": "Bundesliga",
        "country": "Germany",
        "flag": "🇩🇪",
        "logo": "https://media.api-sports.io/football/leagues/78.png",
    },
    {
        "id": 61,
        "name": "Ligue 1",
        "country": "France",
        "flag": "🇫🇷",
        "logo": "https://media.api-sports.io/football/leagues/61.png",
    },
]


@app.get("/api/leagues")
def list_leagues():
    return TOP5_LEAGUES


@app.get("/api/leagues/{league_id}/standings")
def get_league_standings(
    league_id: int,
    season: int = Query(..., description="e.g. 2025 for the 2025-26 season"),
):
    key = f"league_standings:{league_id}:{season}"
    cached = cache.get_cached(key)
    if cached is not None:
        return cached

    raw = api_football.get_league_standings(league_id, season)
    result = [
        {
            "rank": entry.get("rank"),
            "team_api_id": entry.get("team", {}).get("id"),
            "team_name": entry.get("team", {}).get("name"),
            "team_logo": entry.get("team", {}).get("logo"),
            "points": entry.get("points"),
            "goals_diff": entry.get("goalsDiff"),
            "form": entry.get("form", ""),
            "played": entry.get("all", {}).get("played"),
            "wins": entry.get("all", {}).get("win"),
            "draws": entry.get("all", {}).get("draw"),
            "losses": entry.get("all", {}).get("lose"),
            "goals_for": entry.get("all", {}).get("goals", {}).get("for"),
            "goals_against": entry.get("all", {}).get("goals", {}).get("against"),
        }
        for entry in raw
    ]
    cache.set_cached(key, result, ttl=CURR_TTL)
    return result


@app.get("/api/external/teams/{team_api_id}/squad")
def get_external_team_squad(team_api_id: int):
    key = f"ext_squad:{team_api_id}"
    cached = cache.get_cached(key, sliding_ttl=PLAYER_TTL)
    if cached:
        return cached

    squad = api_football.get_team_squad(team_api_id)
    result = [
        {
            "id": p.get("id"),
            "name": p.get("name"),
            "age": p.get("age"),
            "number": p.get("number"),
            "position": p.get("position"),
            "photo": p.get("photo"),
        }
        for p in squad
    ]
    cache.set_cached(key, result, ttl=PLAYER_TTL)
    return result


@app.get("/api/external/teams/{team_api_id}/fixtures")
def get_external_team_fixtures(
    team_api_id: int,
    league_id: int = Query(...),
    season: int = Query(...),
    limit: int = Query(10),
):
    key = f"ext_fixtures:{team_api_id}:{league_id}:{season}:{limit}"
    cached = cache.get_cached(key, sliding_ttl=CURR_TTL)
    if cached is not None:
        return cached

    raw = api_football.get_team_recent_fixtures(team_api_id, league_id, season, limit)
    result = []
    for f in raw:
        fixture = f.get("fixture", {})
        teams = f.get("teams", {})
        goals = f.get("goals", {})
        result.append(
            {
                "fixture_id": fixture.get("id"),
                "date": fixture.get("date"),
                "status_short": fixture.get("status", {}).get("short"),
                "home_team": teams.get("home", {}).get("name"),
                "away_team": teams.get("away", {}).get("name"),
                "home_logo": teams.get("home", {}).get("logo"),
                "away_logo": teams.get("away", {}).get("logo"),
                "home_goals": goals.get("home"),
                "away_goals": goals.get("away"),
                "home_winner": teams.get("home", {}).get("winner"),
            }
        )
    cache.set_cached(key, result, ttl=CURR_TTL)
    return result


@app.get("/api/teams/lookup")
def lookup_internal_team(
    api_football_id: int = Query(..., description="API-Football team ID"),
    db: Session = Depends(get_db),
):
    """Map an API-Football team ID to an internal DB team ID (PL teams only)."""
    team = (
        db.query(crud.Team).filter(crud.Team.api_football_id == api_football_id).first()
    )
    return {"internal_team_id": team.id if team else None}


# ── Team overview ─────────────────────────────────────────────────────────────


@app.get("/api/teams/{team_id}/overview", response_model=schemas.TeamOverviewResponse)
def get_team_overview(
    team_id: int,
    season_id: Optional[int] = Query(
        None, description="Season to show standings for; defaults to latest"
    ),
    db: Session = Depends(get_db),
):
    team = crud.get_team_by_id(db, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    curr = get_current_season_id(db)
    sid = season_id or curr
    ttl, sliding = season_ttl(sid, curr)
    key = f"team_overview:{team_id}:{sid}"

    def fetch():
        # Profile
        profile_db = (
            db.query(crud.TeamProfile)
            .filter(crud.TeamProfile.team_id == team_id)
            .first()
        )

        # Current standing for the chosen season
        standings = crud.get_standings(db, season_id=sid)
        standing = next((s for s in standings if s.team_id == team_id), None)

        standing_schema = None
        if standing:
            standing_schema = schemas.StandingItemSchema(
                team=schemas.TeamSchema.from_orm(team),
                gameweek=standing.gameweek,
                points=standing.points,
                played=standing.played,
                wins=standing.wins,
                draws=standing.draws,
                losses=standing.losses,
                goals_for=standing.goals_for,
                goals_against=standing.goals_against,
                goal_difference=standing.goal_difference,
                position=standing.position,
            )

        # Recent form
        form_matches, form_string = crud.get_team_form(db, team_id, sid, last_x=10)

        # Season history
        history_raw = crud.get_team_season_history(db, team_id)
        history = [schemas.TeamSeasonHistoryItem(**h) for h in history_raw]

        return schemas.TeamOverviewResponse(
            team=schemas.TeamSchema.from_orm(team),
            profile=schemas.TeamProfileSchema.from_orm(profile_db)
            if profile_db
            else None,
            current_season_id=sid,
            current_standing=standing_schema,
            form_string=form_string,
            recent_matches=[schemas.TeamFormMatchSchema(**m) for m in form_matches],
            season_history=history,
        )

    result = get_or_fetch(key, fetch, ttl=ttl, sliding=sliding)
    if result is None:
        raise HTTPException(status_code=404, detail="Team not found")
    return result


# ── Admin: manual sync triggers ───────────────────────────────────────────────
# Accessible at /docs — fire these to populate data on demand.


@app.post("/api/admin/sync/upcoming", tags=["admin"])
def trigger_sync_upcoming():
    """Fetch upcoming PL fixtures from API-Football and cache them."""
    sync_upcoming_fixtures()
    return {"status": "ok", "job": "upcoming_fixtures"}


@app.post("/api/admin/sync/live", tags=["admin"])
def trigger_sync_live():
    """Fetch live PL scores from API-Football and cache them."""
    sync_live_matches()
    return {"status": "ok", "job": "live_matches"}


@app.post("/api/admin/sync/match-analytics", tags=["admin"])
def trigger_sync_match_analytics():
    """Fetch xG/possession from TheStatsAPI for recently completed matches."""
    sync_match_analytics()
    return {"status": "ok", "job": "match_analytics"}


@app.post("/api/admin/sync/player-profiles", tags=["admin"])
def trigger_sync_player_profiles():
    """Fetch player photos/nationality from API-Football for unmapped players."""
    sync_player_profiles()
    return {"status": "ok", "job": "player_profiles"}


@app.post("/api/admin/sync/player-advanced", tags=["admin"])
def trigger_sync_player_advanced():
    """Fetch xG/xA/progressive stats from TheStatsAPI for all mapped players."""
    sync_player_advanced_stats()
    return {"status": "ok", "job": "player_advanced_stats"}
