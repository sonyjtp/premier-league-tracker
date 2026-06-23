"""
Thin wrapper around soccerdata's Understat scraper.

Returns clean dicts so the rest of the app never imports pandas.
Understat covers: ENG-Premier League, ESP-La Liga, GER-Bundesliga,
                  ITA-Serie A, FRA-Ligue 1.
"""
import logging
import warnings
from typing import Dict, List

warnings.filterwarnings("ignore")

logger = logging.getLogger(__name__)

SUPPORTED_LEAGUES = [
    "ENG-Premier League",
    "ESP-La Liga",
    "GER-Bundesliga",
    "ITA-Serie A",
    "FRA-Ligue 1",
]


def get_player_season_stats(leagues: List[str], season_year: int) -> List[Dict]:
    """
    Fetch player season stats from Understat for the given leagues and season.

    Args:
        leagues: List of soccerdata league strings (e.g. ["ENG-Premier League"])
        season_year: Start year of the season (e.g. 2024 for 2024-25)

    Returns:
        List of dicts with keys: player_id, player, team, league, season,
        xg, xa, np_xg, goals, assists, shots, key_passes, minutes
    """
    try:
        import soccerdata as sd

        scraper = sd.Understat(leagues=leagues, seasons=season_year)
        df = scraper.read_player_season_stats()
        df = df.reset_index()

        return [
            {
                "player_id": int(row["player_id"]),
                "player": row["player"],
                "team": row["team"],
                "league": row["league"],
                "season": row["season"],
                "xg": float(row["xg"]) if row["xg"] is not None else None,
                "xa": float(row["xa"]) if row["xa"] is not None else None,
                "np_xg": float(row["np_xg"]) if row["np_xg"] is not None else None,
                "goals": int(row["goals"]) if row["goals"] is not None else None,
                "assists": int(row["assists"]) if row["assists"] is not None else None,
                "shots": int(row["shots"]) if row["shots"] is not None else None,
                "key_passes": int(row["key_passes"])
                if row["key_passes"] is not None
                else None,
                "minutes": int(row["minutes"]) if row["minutes"] is not None else None,
            }
            for _, row in df.iterrows()
        ]
    except Exception as e:
        logger.error(f"[understat] fetch failed for {leagues} {season_year}: {e}")
        return []
