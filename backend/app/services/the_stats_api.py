"""
TheStatsAPI client.

NOTE: Endpoint paths below are based on common football analytics API conventions.
Verify them against your specific TheStatsAPI plan documentation and update as needed.
"""
from typing import Optional

import requests

from app.config import settings

_BASE = settings.STATS_API_HOST.rstrip("/")


def _headers() -> dict:
    return {"Authorization": f"Bearer {settings.STATS_API_KEY}"}


def _get(path: str, params: dict = {}) -> dict:
    if not settings.STATS_API_KEY:
        return {}
    try:
        resp = requests.get(
            f"{_BASE}/{path}", headers=_headers(), params=params, timeout=15
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"[thestatsapi] {path} error: {e}")
        return {}


def get_match_analytics(stats_api_match_id: int) -> dict:
    """
    Fetch xG, possession, PPDA for a completed match.
    Expected response shape:
      { home_xg, away_xg, home_possession, away_possession, home_ppda, away_ppda }
    """
    return _get(f"matches/{stats_api_match_id}")


def get_player_season_analytics(stats_api_player_id: int, season: str) -> dict:
    """
    Fetch xG, xA, progressive stats for a player in a given season.
    season format: e.g. "2023-2024"
    Expected response shape:
      { xg, xa, npxg, xg_per_90, xa_per_90, progressive_carries,
        progressive_passes, progressive_receptions, shots, shots_on_target }
    """
    return _get(f"players/{stats_api_player_id}/seasons/{season}")


def get_team_season_analytics(stats_api_team_id: int, season: str) -> dict:
    """
    Fetch team-level analytics (xG trend, pressing, etc.) for a season.
    season format: e.g. "2023-2024"
    """
    return _get(f"teams/{stats_api_team_id}/seasons/{season}")


def search_player(name: str, season: Optional[str] = None) -> list:
    """Search for a player to retrieve their TheStatsAPI ID."""
    params: dict = {"name": name}
    if season:
        params["season"] = season
    data = _get("players/search", params)
    if isinstance(data, dict):
        return data.get("players", data.get("results", []))
    return data if isinstance(data, list) else []
