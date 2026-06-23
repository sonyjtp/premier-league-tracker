"""
APScheduler jobs for syncing data from API-Football and TheStatsAPI.
Imported and scheduled in main.py lifespan.
"""
import logging
import time
from datetime import date, datetime, timedelta

from fuzzywuzzy import fuzz
from rapidfuzz import fuzz as rfuzz

from app import crud
from app.database import SessionLocal
from app.services import api_football, cache, the_stats_api
from app.services import understat as understat_service

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
    # passes = stats.get("passes", {}) TODO
    games = stats.get("games", {})

    xg = stats.get("goals", {}).get("xg")
    xa = stats.get("goals", {}).get("xassist")
    minutes = games.get("minutes", 0) or 0
    xg_90 = (xg * 90) / minutes if xg and minutes > 0 else None
    xa_90 = (xa * 90) / minutes if xa and minutes > 0 else None

    return {
        "xg": xg,
        "xa": xa,
        "xg_per_90": xg_90,
        "xa_per_90": xa_90,
        "shots": shots.get("total"),
        "shots_on_target": shots.get("on"),
    }


def _parse_fixture_player_stats(player_data: dict, player_api_id: int) -> dict:
    """
    Extract and aggregate xG/xA from fixture/players endpoint.

    Args:
        player_data: Dict with 'player' and 'statistics' keys from fixtures/players response
        player_api_id: The player's API-Football ID to match

    Returns:
        Dict with xG, xA, shots, etc. or empty dict if not found
    """
    player_info = player_data.get("player", {})
    if player_info.get("id") != player_api_id:
        return {}

    stats = player_data.get("statistics", [])
    if not stats:
        return {}

    stat = stats[0]  # First (and usually only) entry per competition
    shots = stat.get("shots", {})
    passes = stat.get("passes", {})
    games = stat.get("games", {})

    xg = stat.get("goals", {}).get("xg") or shots.get("expected")
    xa = passes.get("expected")
    minutes = games.get("minutes", 0)

    xg_90 = (xg * 90) / minutes if xg and minutes > 0 else None
    xa_90 = (xa * 90) / minutes if xa and minutes > 0 else None

    return {
        "xg": xg,
        "xa": xa,
        "xg_per_90": xg_90,
        "xa_per_90": xa_90,
        "shots": shots.get("total"),
        "shots_on_target": shots.get("on"),
        "minutes": minutes,
    }


def _aggregate_fixture_player_stats(fixtures: list, player_api_id: int) -> dict:
    """
    Aggregate xG/xA stats across all fixtures for a single player.
    Fetches fixtures/players for each match and sums xG, xA, and minutes.
    """
    aggregated = {
        "xg": 0.0,
        "xa": 0.0,
        "minutes": 0,
        "shots": 0,
        "shots_on_target": 0,
    }

    for fixture in fixtures:
        fixture_id = fixture.get("fixture_id")
        if not fixture_id:
            continue

        try:
            players_data = api_football.get_fixture_players(fixture_id)
            for player_entry in players_data:
                stats = _parse_fixture_player_stats(player_entry, player_api_id)
                if not stats:
                    continue

                aggregated["xg"] += stats.get("xg") or 0
                aggregated["xa"] += stats.get("xa") or 0
                aggregated["minutes"] += stats.get("minutes") or 0
                aggregated["shots"] += stats.get("shots") or 0
                aggregated["shots_on_target"] += stats.get("shots_on_target") or 0
                break

            time.sleep(0.1)
        except Exception as e:
            logger.warning(f"Failed to get fixture {fixture_id} stats: {e}")
            continue

    minutes = aggregated["minutes"]
    aggregated["xg_per_90"] = (
        (aggregated["xg"] * 90) / minutes if aggregated["xg"] and minutes > 0 else None
    )
    aggregated["xa_per_90"] = (
        (aggregated["xa"] * 90) / minutes if aggregated["xa"] and minutes > 0 else None
    )

    return aggregated


def sync_player_advanced_stats():
    """
    Aggregate xG/xA stats from API-Football fixtures for PL players.
    Sums fixture-level player stats into season totals and per-90 metrics.
    Runs weekly.
    """
    db = SessionLocal()
    try:
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
                if existing and existing.xg is not None:
                    continue

                season_year = int(s.season.label.split("-")[0])
                raw = api_football.get_player_season_stats(
                    p.api_football_id, season=season_year
                )
                if not raw:
                    continue

                data = _parse_api_football_stats(raw)
                if not data or data.get("xg") is None:
                    continue

                crud.upsert_player_advanced_stats(db, p.id, s.season_id, data)
                synced += 1
                logger.info(
                    f"[sync] {p.name} {s.season.label}: {data['xg']:.2f} xG, "
                    f"{data.get('xa', 0) or 0:.2f} xA"
                )
                time.sleep(0.4)
        logger.info(f"[sync] player_advanced_stats: {synced} synced")
    except Exception as e:
        logger.error(f"[sync] player_advanced_stats failed: {e}")
    finally:
        db.close()


# ── Understat xG/xA sync ──────────────────────────────────────────────────────

UNDERSTAT_LEAGUES = ["ENG-Premier League"]


def sync_understat_player_ids(leagues: list = None, seasons: list = None):
    """
    Fuzzy-match internal players against Understat player names and store
    their stable understat_id. Only runs for players without one already.
    Run once manually after adding new players.
    """
    leagues = leagues or UNDERSTAT_LEAGUES
    # Use the last 3 seasons to catch players who may have left the league
    seasons = seasons or [2024, 2023, 2022]

    db = SessionLocal()
    try:
        # Collect all Understat players across the requested seasons
        understat_map: dict[str, int] = {}  # canonical_name -> understat_id
        for season_year in seasons:
            rows = understat_service.get_player_season_stats(leagues, season_year)
            for row in rows:
                understat_map[row["player"]] = row["player_id"]

        if not understat_map:
            logger.warning("[understat] no players fetched for mapping")
            return

        understat_names = list(understat_map.keys())
        # Single-word Understat names (e.g. "Richarlison", "Alisson") need word-boundary matching
        single_word_names = {n for n in understat_names if " " not in n}

        players = db.query(crud.Player).filter(crud.Player.understat_id.is_(None)).all()

        # Collect all candidate matches, then resolve collisions greedily by score.
        # Specificity bonus: prefer longer Understat names over shorter ones
        # (e.g. "Gabriel Jesus" > "Gabriel" for "Gabriel Fernando de Jesus").
        import re as _re

        def _specificity(uname: str) -> int:
            return (len(uname.split()) - 1) * 15

        # Build word-boundary regex patterns once for efficiency
        word_pat = {
            uname: _re.compile(
                r"(?<!\w)" + _re.escape(uname) + r"(?!\w)", _re.IGNORECASE
            )
            for uname in single_word_names
        }

        # For single-word Understat names, count how many internal players match via word
        # boundary. If more than one player matches (e.g. "Gabriel" matches 5 players),
        # skip word_in_name entirely for that name to avoid wrong assignments.
        all_names = [f"{p.first_name} {p.second_name}".strip() for p in players]
        word_name_unique: dict[
            str, bool
        ] = {}  # uname -> True if only 1 internal player has it
        for uname, pat in word_pat.items():
            count = sum(1 for n in all_names if pat.search(n))
            word_name_unique[uname] = count == 1

        candidates_list = []  # (score, player, understat_name)
        for p in players:
            full_name = f"{p.first_name} {p.second_name}".strip()
            best_match, best_score = None, 0

            # Evaluate every Understat name; apply specificity bonus so longer names
            # win ties over shorter ones (e.g. "Gabriel Jesus" beats "Gabriel").
            for uname in understat_names:
                ts = rfuzz.token_sort_ratio(full_name, uname)
                tset = rfuzz.token_set_ratio(full_name, uname)

                raw = 0
                if ts >= 80:
                    raw = ts
                # token_set_ratio only for multi-word Understat names to avoid false positives
                # like any player with "Gabriel" matching the single-word "Gabriel"
                if " " in uname and tset >= 90 and tset > raw:
                    raw = tset

                if raw == 0:
                    # Word-boundary fallback only for single-word names that are unambiguous
                    # (only one internal player has that exact word in their name)
                    if (
                        uname in word_pat
                        and word_name_unique.get(uname)
                        and word_pat[uname].search(full_name)
                    ):
                        raw = 95

                if raw == 0:
                    continue

                s = raw + _specificity(uname)
                if s > best_score:
                    best_match, best_score = uname, s

            if best_match:
                candidates_list.append((best_score, p, best_match))

        # Greedy assignment: highest score wins; each internal player and each
        # understat_id can only be assigned once.
        candidates_list.sort(key=lambda x: x[0], reverse=True)
        taken_uids: set[int] = set()
        taken_pids: set[int] = set()
        mapped = 0
        for score, p, uname in candidates_list:
            uid = understat_map[uname]
            if uid in taken_uids or p.id in taken_pids:
                continue
            p.understat_id = uid
            taken_uids.add(uid)
            taken_pids.add(p.id)
            mapped += 1
            logger.info(
                f"[understat] mapped '{p.first_name} {p.second_name}' → '{uname}' "
                f"(id={uid}, score={score:.0f})"
            )

        db.commit()
        logger.info(f"[understat] player ID mapping: {mapped}/{len(players)} mapped")
    except Exception as e:
        logger.error(f"[understat] player ID mapping failed: {e}")
        db.rollback()
    finally:
        db.close()


def sync_understat_xg(leagues: list = None):
    """
    Fetch xG/xA from Understat for all players with an understat_id.
    Iterates over every season in the DB and writes into PlayerAdvancedStats.
    Skips seasons already populated (xg is not None).
    Runs weekly alongside the regular advanced stats job.
    """
    leagues = leagues or UNDERSTAT_LEAGUES

    db = SessionLocal()
    try:
        seasons = db.query(crud.Season).all()
        synced = 0

        for season in seasons:
            season_year = int(season.label.split("-")[0])
            if season_year < 2014:
                continue  # Understat only goes back to 2014-15

            rows = understat_service.get_player_season_stats(leagues, season_year)
            if not rows:
                continue

            # Index by understat player_id for O(1) lookup
            stats_by_understat_id = {row["player_id"]: row for row in rows}

            players = (
                db.query(crud.Player).filter(crud.Player.understat_id.isnot(None)).all()
            )

            for p in players:
                row = stats_by_understat_id.get(p.understat_id)
                if not row or not row.get("minutes"):
                    continue  # player didn't play this season

                existing = (
                    db.query(crud.PlayerAdvancedStats)
                    .filter(
                        crud.PlayerAdvancedStats.player_id == p.id,
                        crud.PlayerAdvancedStats.season_id == season.id,
                    )
                    .first()
                )
                if existing and existing.xg is not None:
                    continue

                minutes = row["minutes"] or 0
                xg = row.get("xg")
                xa = row.get("xa")
                crud.upsert_player_advanced_stats(
                    db,
                    p.id,
                    season.id,
                    {
                        "xg": xg,
                        "xa": xa,
                        "npxg": row.get("np_xg"),
                        "xg_per_90": (xg * 90 / minutes)
                        if xg and minutes > 0
                        else None,
                        "xa_per_90": (xa * 90 / minutes)
                        if xa and minutes > 0
                        else None,
                        "shots": row.get("shots"),
                    },
                )
                synced += 1

            logger.info(f"[understat] {season.label}: {synced} records written so far")

        logger.info(f"[understat] xG sync complete: {synced} total")
    except Exception as e:
        logger.error(f"[understat] xG sync failed: {e}")
        db.rollback()
    finally:
        db.close()
