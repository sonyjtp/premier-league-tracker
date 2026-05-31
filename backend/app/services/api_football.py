import time
import requests
from datetime import date, timedelta
from typing import Optional
from app.config import settings

# Direct api-sports.io uses a single header — no RapidAPI host required
def _headers() -> dict:
    return {"x-apisports-key": settings.API_FOOTBALL_KEY}


def _get(path: str, params: dict = {}) -> dict:
    if not settings.API_FOOTBALL_KEY:
        print("[api-football] API key not configured")
        return {}
    try:
        url = f"{settings.API_FOOTBALL_BASE}/{path}"
        resp = requests.get(url, headers=_headers(), params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"[api-football] {path} error: {e}")
        return {}


def get_live_fixtures() -> list:
    data = _get("fixtures", {"league": settings.PL_LEAGUE_ID, "live": "all"})
    return data.get("response", [])


def get_upcoming_fixtures(days_ahead: int = 7) -> list:
    today = date.today().isoformat()
    end = (date.today() + timedelta(days=days_ahead)).isoformat()
    data = _get("fixtures", {
        "league": settings.PL_LEAGUE_ID,
        "season": settings.CURRENT_SEASON_YEAR,
        "from": today,
        "to": end,
    })
    return data.get("response", [])


def get_fixture_events(fixture_id: int) -> list:
    data = _get("fixtures/events", {"fixture": fixture_id})
    return data.get("response", [])


def get_fixture_lineups(fixture_id: int) -> list:
    data = _get("fixtures/lineups", {"fixture": fixture_id})
    return data.get("response", [])


def get_fixture_statistics(fixture_id: int) -> list:
    data = _get("fixtures/statistics", {"fixture": fixture_id})
    return data.get("response", [])


def get_player_profile(player_api_id: int, season_year: Optional[int] = None) -> dict:
    season = season_year or settings.CURRENT_SEASON_YEAR
    data = _get("players", {"id": player_api_id, "season": season})
    resp = data.get("response", [])
    return resp[0] if resp else {}


def get_team_info(team_api_id: int) -> dict:
    data = _get("teams", {"id": team_api_id})
    resp = data.get("response", [])
    return resp[0] if resp else {}


def get_team_squad(team_api_id: int) -> list:
    data = _get("players/squads", {"team": team_api_id})
    resp = data.get("response", [])
    return resp[0].get("players", []) if resp else []


def search_team(name: str) -> list:
    data = _get("teams", {"name": name, "country": "England"})
    return data.get("response", [])


def get_league_standings(league_id: int, season: int) -> list:
    """
    Returns a flat list of standing entries for every team in the league.
    API-Football nests: response[0].league.standings[0] = list of teams.
    """
    data = _get("standings", {"league": league_id, "season": season})
    try:
        return data["response"][0]["league"]["standings"][0]
    except (KeyError, IndexError):
        return []


def get_team_recent_fixtures(team_api_id: int, league_id: int, season: int, last: int = 10) -> list:
    data = _get("fixtures", {
        "team":   team_api_id,
        "league": league_id,
        "season": season,
        "last":   last,
    })
    return data.get("response", [])


def get_league_players(league_id: int = 39, season: int = 2025, team_id: Optional[int] = None) -> list:
    """
    Fetch players in a league for a given season, optionally filtered by team.
    Team-specific queries may return more detailed stats including xG.
    """
    params = {
        "league": league_id,
        "season": season,
    }
    if team_id:
        params["team"] = team_id
    data = _get("players", params)
    return data.get("response", [])


def get_player_season_stats(player_api_id: int, league_id: int = 39, season: int = 2025) -> dict:
    """
    Fetch detailed player season stats from API-Football including xG, xA, shots, etc.
    Returns a dict with stats for the player in the given season/league combination.
    """
    data = _get("players", {
        "id": player_api_id,
        "league": league_id,
        "season": season,
    })
    resp = data.get("response", [])
    if not resp:
        return {}

    player_data = resp[0]
    stats_list = player_data.get("statistics", [])

    # Find the matching league/season combination
    for stats in stats_list:
        if (stats.get("league", {}).get("id") == league_id and
            stats.get("season") == season):
            return stats

    return stats_list[0] if stats_list else {}
