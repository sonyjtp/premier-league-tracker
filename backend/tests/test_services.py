"""
Tests for service modules (cache, api_football, the_stats_api)
"""
from app.services import cache


class TestCacheService:
    """Tests for caching utilities"""

    def test_cache_init(self):
        """Test cache module initialization"""
        # Verify cache module constants exist
        assert hasattr(cache, "CURR_TTL")
        assert hasattr(cache, "HIST_TTL")
        assert hasattr(cache, "PLAYER_TTL")
        assert hasattr(cache, "UPCOMING_TTL")

    def test_season_ttl_current_season(self, db):
        """Test season_ttl returns correct TTL for current season"""
        from app.models import Competition, GameweekStanding, Season

        # Create current season
        season = Season(label="2024-25", season_code="2425")
        comp = Competition(name="Premier League", code="EPL", type="League")
        db.add_all([season, comp])
        db.commit()

        # Add a standing to make it the current season
        standing = GameweekStanding(
            season_id=season.id,
            team_id=1,
            gameweek=20,
            position=1,
            points=60,
            played=20,
            wins=18,
            draws=6,
            losses=0,
            goals_for=60,
            goals_against=20,
            goal_difference=40,
            competition_id=comp.id,
        )
        db.add(standing)
        db.commit()

        ttl, sliding = cache.season_ttl(season.id, season.id)
        # Current season should have shorter TTL (CURR_TTL)
        assert ttl == cache.CURR_TTL
        assert sliding is False

    def test_season_ttl_past_season(self):
        """Test season_ttl returns correct TTL for past season"""
        current_season_id = 100
        past_season_id = 99

        ttl, sliding = cache.season_ttl(past_season_id, current_season_id)
        # Past season should have longer TTL (HIST_TTL) with sliding
        assert ttl == cache.HIST_TTL
        assert sliding is True

    def test_get_current_season_id(self, db):
        """Test get_current_season_id returns latest season with data"""
        from app.models import Competition, GameweekStanding, Season

        # Create multiple seasons
        season1 = Season(label="2023-24", season_code="2324")
        season2 = Season(label="2024-25", season_code="2425")
        comp = Competition(name="Premier League", code="EPL", type="League")
        db.add_all([season1, season2, comp])
        db.commit()

        # Add standings only for season2
        standing = GameweekStanding(
            season_id=season2.id,
            team_id=1,
            gameweek=1,
            position=1,
            points=3,
            played=1,
            wins=1,
            draws=0,
            losses=0,
            goals_for=1,
            goals_against=0,
            goal_difference=1,
            competition_id=comp.id,
        )
        db.add(standing)
        db.commit()

        current_id = cache.get_current_season_id(db)
        assert current_id == season2.id

    def test_get_or_fetch_cache_hit(self):
        """Test get_or_fetch returns cached value"""

        def fetch_func():
            return {"data": "original"}

        # First call should fetch
        result1 = cache.get_or_fetch("test_key_1", fetch_func, ttl=3600)
        assert result1 == {"data": "original"}

        # Second call should return from cache
        result2 = cache.get_or_fetch("test_key_1", fetch_func, ttl=3600)
        assert result2 == {"data": "original"}

    def test_get_or_fetch_cache_miss(self):
        """Test get_or_fetch fetches when cache miss"""

        def fetch_func():
            return {"data": "fetched"}

        # Using unique key to ensure cache miss
        result = cache.get_or_fetch("unique_key_xyz", fetch_func, ttl=3600)
        assert result == {"data": "fetched"}

    def test_get_or_fetch_none_value(self):
        """Test get_or_fetch handles None return value"""

        def fetch_func():
            return None

        result = cache.get_or_fetch("none_key", fetch_func, ttl=3600)
        assert result is None

    def test_get_or_fetch_with_sliding_window(self):
        """Test get_or_fetch with sliding window TTL"""

        def fetch_func():
            return {"data": "sliding"}

        result = cache.get_or_fetch("sliding_key", fetch_func, ttl=3600, sliding=True)
        assert result == {"data": "sliding"}


class TestCacheInternals:
    """Tests for cache primitives and tiered helpers."""

    def test_serialize_pydantic_model(self):
        from app.schemas import SeasonSchema
        from app.services.cache import _serialize

        model = SeasonSchema(id=1, label="2024-25", season_code="2425")
        result = _serialize(model)
        assert isinstance(result, dict)
        assert result["id"] == 1

    def test_serialize_list_with_model(self):
        from app.schemas import SeasonSchema
        from app.services.cache import _serialize

        model = SeasonSchema(id=2, label="2023-24", season_code="2324")
        result = _serialize([model, {"plain": "dict"}])
        assert isinstance(result, list)
        assert result[0]["id"] == 2
        assert result[1] == {"plain": "dict"}

    def test_serialize_nested_dict(self):
        from app.schemas import SeasonSchema
        from app.services.cache import _serialize

        model = SeasonSchema(id=3, label="2022-23", season_code="2223")
        result = _serialize({"key": model})
        assert result["key"]["id"] == 3

    def test_get_cached_redis_exception_returns_none(self):
        from unittest.mock import patch

        from app.services.cache import get_cached

        with patch("app.services.cache.get_redis", side_effect=Exception("Redis down")):
            result = get_cached("any_key")
        assert result is None

    def test_set_cached_calls_redis(self):
        from unittest.mock import MagicMock, patch

        from app.services.cache import set_cached

        mock_redis = MagicMock()
        with patch("app.services.cache.get_redis", return_value=mock_redis):
            set_cached("test_key", {"val": 1}, ttl=60)
        mock_redis.setex.assert_called_once()

    def test_set_cached_exception_is_silent(self):
        from unittest.mock import patch

        from app.services.cache import set_cached

        with patch("app.services.cache.get_redis", side_effect=Exception("Redis down")):
            set_cached("any_key", {"val": 1}, ttl=60)  # must not raise

    def test_delete_cached_calls_redis(self):
        from unittest.mock import MagicMock, patch

        from app.services.cache import delete_cached

        mock_redis = MagicMock()
        with patch("app.services.cache.get_redis", return_value=mock_redis):
            delete_cached("some_key")
        mock_redis.delete.assert_called_once_with("some_key")

    def test_delete_cached_exception_is_silent(self):
        from unittest.mock import patch

        from app.services.cache import delete_cached

        with patch("app.services.cache.get_redis", side_effect=Exception("Redis down")):
            delete_cached("any_key")  # must not raise

    def test_get_or_fetch_with_db_db_hit(self):
        from unittest.mock import MagicMock, patch

        from app.services.cache import get_or_fetch_with_db

        mock_redis = MagicMock()
        mock_redis.get.return_value = None  # cache miss

        with patch("app.services.cache.get_redis", return_value=mock_redis):
            result = get_or_fetch_with_db(
                key="db_hit_key",
                db_fetch_fn=lambda: {"source": "db"},
                external_fetch_fn=lambda: {"source": "api"},
                ttl=60,
            )
        assert result == {"source": "db"}

    def test_get_or_fetch_with_db_external_hit(self):
        from unittest.mock import MagicMock, patch

        from app.services.cache import get_or_fetch_with_db

        mock_redis = MagicMock()
        mock_redis.get.return_value = None  # cache miss

        with patch("app.services.cache.get_redis", return_value=mock_redis):
            result = get_or_fetch_with_db(
                key="ext_hit_key",
                db_fetch_fn=lambda: None,  # DB miss
                external_fetch_fn=lambda: {"source": "api"},
                ttl=60,
            )
        assert result == {"source": "api"}

    def test_get_or_fetch_with_db_all_miss(self):
        from unittest.mock import MagicMock, patch

        from app.services.cache import get_or_fetch_with_db

        mock_redis = MagicMock()
        mock_redis.get.return_value = None

        with patch("app.services.cache.get_redis", return_value=mock_redis):
            result = get_or_fetch_with_db(
                key="all_miss_key",
                db_fetch_fn=lambda: None,
                external_fetch_fn=lambda: None,
                ttl=60,
            )
        assert result is None

    def test_get_current_season_id_db_path(self, db):
        from unittest.mock import MagicMock, patch

        from app.models import Season
        from app.services.cache import get_current_season_id

        season = Season(label="2024-25", season_code="2425")
        db.add(season)
        db.commit()

        mock_redis = MagicMock()
        mock_redis.get.return_value = None  # force cache miss

        with patch("app.services.cache.get_redis", return_value=mock_redis):
            sid = get_current_season_id(db)

        assert sid == season.id


class TestAPIFootballService:
    """Tests for API-Football service integration"""

    def test_api_football_module_exists(self):
        """Test api_football module can be imported"""
        from app.services import api_football

        # Verify module has expected functions
        assert hasattr(api_football, "get_league_standings")
        assert hasattr(api_football, "get_team_info")
        assert hasattr(api_football, "get_league_players")


class TestTheStatsAPIService:
    """Tests for The Stats API service integration"""

    def test_stats_api_module_exists(self):
        """Test the_stats_api module can be imported"""
        from app.services import the_stats_api

        # Verify module exists and can be imported
        assert the_stats_api is not None


class TestUnderstatService:
    """Tests for the Understat xG/xA wrapper service."""

    def test_understat_module_exists(self):
        """Test understat service can be imported and has expected interface."""
        from app.services import understat

        assert hasattr(understat, "get_player_season_stats")
        assert hasattr(understat, "SUPPORTED_LEAGUES")

    def test_supported_leagues_covers_big5(self):
        """Understat covers exactly the Big-5 domestic leagues."""
        from app.services.understat import SUPPORTED_LEAGUES

        expected = {
            "ENG-Premier League",
            "ESP-La Liga",
            "GER-Bundesliga",
            "ITA-Serie A",
            "FRA-Ligue 1",
        }
        assert set(SUPPORTED_LEAGUES) == expected

    def test_get_player_season_stats_returns_list_on_error(self):
        """Returns an empty list (not an exception) when soccerdata fails."""
        from unittest.mock import patch

        import soccerdata as sd
        from app.services import understat

        # soccerdata is imported inside get_player_season_stats, so patch at the top level
        with patch.object(sd, "Understat", side_effect=RuntimeError("network error")):
            result = understat.get_player_season_stats(["ENG-Premier League"], 2024)

        assert result == []

    def test_get_player_season_stats_schema(self):
        """Each row returned contains the required keys."""
        from unittest.mock import MagicMock, patch

        import pandas as pd
        import soccerdata as sd
        from app.services import understat

        fake_row = {
            "player_id": 6026,
            "player": "Richarlison",
            "team": "Tottenham",
            "league": "ENG-Premier League",
            "season": "2425",
            "xg": 4.3,
            "xa": 0.8,
            "np_xg": 4.0,
            "goals": 4,
            "assists": 1,
            "shots": 17,
            "key_passes": 12,
            "minutes": 900,
        }
        fake_df = pd.DataFrame([fake_row])

        mock_scraper = MagicMock()
        mock_scraper.read_player_season_stats.return_value = fake_df
        with patch.object(sd, "Understat", return_value=mock_scraper):
            result = understat.get_player_season_stats(["ENG-Premier League"], 2024)

        assert len(result) == 1
        row = result[0]
        required_keys = {
            "player_id",
            "player",
            "team",
            "league",
            "season",
            "xg",
            "xa",
            "np_xg",
            "goals",
            "assists",
            "shots",
            "key_passes",
            "minutes",
        }
        assert required_keys.issubset(set(row.keys()))
        assert row["player_id"] == 6026
        assert row["xg"] == 4.3

    def test_get_player_season_stats_no_pandas_in_return(self):
        """Return values must be plain Python dicts/scalars, not pandas types."""
        from unittest.mock import MagicMock, patch

        import pandas as pd
        import soccerdata as sd
        from app.services import understat

        fake_df = pd.DataFrame(
            [
                {
                    "player_id": 7322,
                    "player": "Bukayo Saka",
                    "team": "Arsenal",
                    "league": "ENG-Premier League",
                    "season": "2425",
                    "xg": 8.94,
                    "xa": 11.58,
                    "np_xg": 8.0,
                    "goals": 14,
                    "assists": 10,
                    "shots": 75,
                    "key_passes": 90,
                    "minutes": 2900,
                }
            ]
        )

        mock_scraper = MagicMock()
        mock_scraper.read_player_season_stats.return_value = fake_df
        with patch.object(sd, "Understat", return_value=mock_scraper):
            result = understat.get_player_season_stats(["ENG-Premier League"], 2024)

        row = result[0]
        # All numeric values must be plain Python types, not pandas scalars
        assert isinstance(row["player_id"], int)
        assert isinstance(row["xg"], float)
        assert isinstance(row["minutes"], int)
