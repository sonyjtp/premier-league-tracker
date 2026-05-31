"""Cache module tests (Redis-dependent - run with Redis available)."""
from app.services.cache import CURR_TTL, HIST_TTL, PLAYER_TTL, UPCOMING_TTL


class TestCacheTTLConstants:
    """Test cache TTL constants are properly defined."""

    def test_live_ttl_constant(self):
        """Verify cache TTL constants are defined."""
        assert UPCOMING_TTL == 300
        assert CURR_TTL == 3600
        assert PLAYER_TTL == 604_800
        assert HIST_TTL == 15_552_000

    def test_ttl_values_are_positive(self):
        """TTL values must be positive integers."""
        assert UPCOMING_TTL > 0
        assert CURR_TTL > 0
        assert PLAYER_TTL > 0
        assert HIST_TTL > 0

    def test_ttl_ordering(self):
        """TTL values should be ordered by duration."""
        assert UPCOMING_TTL < CURR_TTL < PLAYER_TTL < HIST_TTL
