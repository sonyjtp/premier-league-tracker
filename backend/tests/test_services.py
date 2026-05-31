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
