import time
import requests
from datetime import date, timedelta
from typing import Optional
from app.config import settings

_BASE = "https://api-football-v1.p.rapidapi.com/v3"


def _headers() -> dict:
    return {
        "X-RapidAPI-Key": settings.API_FOOTBALL_KEY,
        "X-RapidAPI-Host": settings.API_FOOTBALL_HOST,
    }


def _get(path: str, params: dict = {}) -> dict:
    if not settings.API_FOOTBALL_KEY:
        return {}
    try:
        resp = requests.get(
            f"{_BASE}/{path}", headers=_headers(), params=params, timeout=10
        )
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
    """Basic per-team stats: shots, corners, possession from API-Football."""
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