"""
APScheduler jobs for syncing data from API-Football and TheStatsAPI.
Imported and scheduled in main.py lifespan.
"""
import logging
import time
from datetime import date, datetime, timedelta

from app import crud
from app.database import SessionLocal
from app.services import api_football, cache, the_stats_api
from fuzzywuzzy import fuzz

logger = logging.getLogger(__name__)

LIVE_KEY = "live_fixtures"
UPCOMING_KEY = "upcoming_fixtures"


# ── Fixture formatting ────────────────────────────────────────────────────────


def _fmt_fixture(f: dict) -> dict:
    fixture = f.get("fixture", {})
    teams = f.get("teams", {})
    goals = f.get("goals", {})
    score = f.get("score", {})
    league = f.get("league", {})
    return {
        "fixture_id": fixture.get("id"),
        "status_short": fixture.get("status", {}).get("short", "NS"),
        "status_long": fixture.get("status", {}).get("long", "Not Started"),
        "elapsed": fixture.get("status", {}).get("elapsed"),
        "kickoff": fixture.get("date"),
        "venue": fixture.get("venue", {}).get("name"),
        "round": league.get("round"),
        "home_team": {
            "name": teams.get("home", {}).get("name"),
            "logo": teams.get("home", {}).get("logo"),
            "api_id": teams.get("home", {}).get("id"),
        },
        "away_team": {
            "name": teams.get("away", {}).get("name"),
            "logo": teams.get("away", {}).get("logo"),
            "api_id": teams.get("away", {}).get("id"),
        },
        "home_score": goals.get("home"),
        "away_score": goals.get("away"),
        "home_ht_score": score.get("halftime", {}).get("home"),
        "away_ht_score": score.get("halftime", {}).get("away"),
    }


# ── Scheduled jobs ────────────────────────────────────────────────────────────


def sync_live_matches():
    """Cache live PL fixtures in Redis with a 60-second TTL."""
    try:
        raw = api_football.get_live_fixtures()
        payload = {
            "fixtures": [_fmt_fixture(f) for f in raw],
            "cached_at": datetime.utcnow().isoformat(),
        }
        cache.set_cached(LIVE_KEY, payload, ttl=60)
        logger.info(f"[sync] {len(raw)} live fixtures cached")
    except Exception as e:
        logger.error(f"[sync] live_matches failed: {e}")


def sync_upcoming_fixtures():
    """Cache upcoming PL fixtures (next 7 days) in Redis with a 5-minute TTL."""
    try:
        raw = api_football.get_upcoming_fixtures(days_ahead=7)
        payload = {
            "fixtures": [_fmt_fixture(f) for f in raw],
            "cached_at": datetime.utcnow().isoformat(),
        }
        cache.set_cached(UPCOMING_KEY, payload, ttl=300)
        logger.info(f"[sync] {len(raw)} upcoming fixtures cached")
    except Exception as e:
        logger.error(f"[sync] upcoming_fixtures failed: {e}")


def sync_player_profiles():
    """
    Fetch photo/nationality from API-Football for players that have an
    api_football_id but no profile record yet.
    Runs daily (low priority — won't block startup).
    """
    db = SessionLocal()
    try:
        players = (
            db.query(crud.Player).filter(crud.Player.api_football_id.isnot(None)).all()
        )
        synced = 0
        for p in players:
            profile = (
                db.query(crud.PlayerProfile)
                .filter(crud.PlayerProfile.player_id == p.id)
                .first()
            )
            if profile and profile.updated_at:
                continue
            data = api_football.get_player_profile(p.api_football_id)
            if not data:
                continue
            info = data.get("player", {})
            crud.upsert_player_profile(
                db,
                p.id,
                {
                    "photo_url": info.get("photo"),
                    "nationality": info.get("nationality"),
                    "birth_date": info.get("birth", {}).get("date"),
                    "height": info.get("height"),
                    "weight": info.get("weight"),
                    "current_club": None,
                },
            )
            synced += 1
            time.sleep(0.4)
        logger.info(f"[sync] player_profiles: {synced} synced")
    except Exception as e:
        logger.error(f"[sync] player_profiles failed: {e}")
    finally:
        db.close()


def sync_match_analytics():
    """
    Fetch xG/possession from TheStatsAPI for matches completed in the last
    3 days that don't yet have advanced stats stored.

    Requires matches to have a stats_api_id mapping (set manually or via a
    future sync job that maps our internal match IDs to TheStatsAPI IDs).
    """
    db = SessionLocal()
    try:
        cutoff = date.today() - timedelta(days=3)
        recent = (
            db.query(crud.Match)
            .filter(
                crud.Match.match_date >= cutoff, crud.Match.match_date <= date.today()
            )
            .all()
        )
        synced = 0
        for match in recent:
            existing = (
                db.query(crud.MatchAdvancedStats)
                .filter(crud.MatchAdvancedStats.match_id == match.id)
                .first()
            )
            if existing:
                continue
            # Uses internal match.id as the TheStatsAPI ID; update this mapping
            # once you have stats_api IDs for your matches.
            stats = the_stats_api.get_match_analytics(match.id)
            if not stats:
                continue
            crud.upsert_match_advanced_stats(db, match.id, stats)
            synced += 1
            time.sleep(0.5)
        logger.info(f"[sync] match_analytics: {synced} synced")
    except Exception as e:
        logger.error(f"[sync] match_analytics failed: {e}")
    finally:
        db.close()


def sync_team_api_ids():
    """
    Fetch all PL teams from API-Football and map their IDs to internal teams by name.
    This enables squad fetching for the TeamPage.
    """
    db = SessionLocal()
    try:
        # Fetch standings to get team list
        standings = api_football.get_league_standings(league_id=39, season=2025)
        matched = 0

        for entry in standings:
            team_info = entry.get("team", {})
            api_id = team_info.get("id")
            team_name = team_info.get("name")

            if not api_id or not team_name:
                continue

            # Find internal team by name
            internal = db.query(crud.Team).filter(crud.Team.name == team_name).first()

            if internal and not internal.api_football_id:
                internal.api_football_id = api_id
                db.add(internal)
                matched += 1

        db.commit()
        logger.info(f"[sync] team_api_ids: {matched} teams mapped")
    except Exception as e:
        logger.error(f"[sync] team_api_ids failed: {e}")
        db.rollback()
    finally:
        db.close()


def sync_player_api_ids():
    """
    Fetch all PL players from API-Football per-team and map their IDs to internal players.
    Per-team queries return more detailed stats including xG data.
    """
    db = SessionLocal()
    try:
        internal_players = db.query(crud.Player).all()

        # PL team API-Football IDs
        pl_team_ids = [
            33,
            34,
            35,
            36,
            39,
            40,
            41,
            42,
            43,
            44,
            45,
            46,
            47,
            48,
            49,
            50,
            51,
            52,
            55,
            57,
        ]

        matched = 0
        for team_id in pl_team_ids:
            api_players = api_football.get_league_players(
                league_id=39, season=2025, team_id=team_id
            )

            for ap in api_players:
                player_info = ap.get("player", {})
                api_id = player_info.get("id")
                first_name = player_info.get("firstname", "").strip()
                last_name = player_info.get("lastname", "").strip()

                if not api_id or not (first_name and last_name):
                    continue

                # Build full name for matching
                api_full_name = f"{first_name} {last_name}".lower()

                # Try exact match first
                internal = next(
                    (
                        p
                        for p in internal_players
                        if p.first_name.lower() == first_name.lower()
                        and p.second_name.lower() == last_name.lower()
                        and not p.api_football_id
                    ),
                    None,
                )

                # Fallback to fuzzy match if exact match fails
                if not internal:
                    best_match = None
                    best_score = 0
                    for p in internal_players:
                        if p.api_football_id:
                            continue
                        internal_full = f"{p.first_name} {p.second_name}".lower()
                        score = fuzz.token_sort_ratio(api_full_name, internal_full)
                        if score > best_score and score >= 80:
                            best_match = p
                            best_score = score
                    internal = best_match

                if internal:
                    internal.api_football_id = api_id
                    db.add(internal)
                    matched += 1

            time.sleep(0.1)  # Rate limiting

        db.commit()
        logger.info(f"[sync] player_api_ids: {matched} players mapped")
    except Exception as e:
        logger.error(f"[sync] player_api_ids failed: {e}")
        db.rollback()
    finally:
        db.close()


def _parse_api_football_stats(stats: dict) -> dict:
    """Extract xG, xA, shots data from API-Football player stats response."""
    if not stats:
        return {}

    shots = stats.get("shots", {})
    passes = stats.get("passes", {})
    games = stats.get("games", {})

    # API-Football provides expected goals in shots.expected
    xg = shots.get("expected")
    minutes = games.get("minutes_played", 0)
    xg_90 = (xg * 90) / minutes if xg and minutes > 0 else None

    # xA estimation from passes.expected if available
    xa = passes.get("expected") if passes else None
    xa_90 = (xa * 90) / minutes if xa and minutes > 0 else None

    return {
        "xg": xg,
        "xa": xa,
        "xg_per_90": xg_90,
        "xa_per_90": xa_90,
        "shots": shots.get("total"),
        "shots_on_target": shots.get("on"),
    }


def sync_player_advanced_stats():
    """
    Fetch xG/xA stats from API-Football for PL players.
    Falls back to TheStatsAPI if API-Football data unavailable.
    Runs weekly.
    """
    db = SessionLocal()
    try:
        # Query players with api_football_id (PL players synced from API-Football)
        players = (
            db.query(crud.Player).filter(crud.Player.api_football_id.isnot(None)).all()
        )
        synced = 0
        for p in players:
            summaries = crud.get_player_season_summaries(db, p.id)
            for s in summaries:
                existing = (
                    db.query(crud.PlayerAdvancedStats)
                    .filter(
                        crud.PlayerAdvancedStats.player_id == p.id,
                        crud.PlayerAdvancedStats.season_id == s.season_id,
                    )
                    .first()
                )
                if existing:
                    continue

                # Try API-Football first (for PL players)
                season_year = int(s.season.label.split("-")[0])
                stats = api_football.get_player_season_stats(
                    p.api_football_id, league_id=39, season=season_year
                )
                data = _parse_api_football_stats(stats)

                # Fallback to TheStatsAPI if available
                if not data and p.stats_api_id:
                    data = the_stats_api.get_player_season_analytics(
                        p.stats_api_id, s.season.label
                    )

                if not data:
                    continue

                crud.upsert_player_advanced_stats(db, p.id, s.season_id, data)
                synced += 1
                time.sleep(0.2)
        logger.info(f"[sync] player_advanced_stats: {synced} synced")
    except Exception as e:
        logger.error(f"[sync] player_advanced_stats failed: {e}")
    finally:
        db.close()
