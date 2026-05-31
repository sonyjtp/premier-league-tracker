"""Tests for sync functions and data pipeline."""
from datetime import date
from unittest.mock import patch

from app import crud, models
from app.pipeline.sync_external import (
    _aggregate_fixture_player_stats,
    _parse_fixture_player_stats,
)


class TestParseFixturePlayerStats:
    """Test fixture player stats parsing."""

    def test_parse_fixture_player_stats_valid(self):
        """Test parsing valid fixture player stats."""
        player_data = {
            "player": {"id": 123},
            "statistics": [
                {
                    "shots": {"expected": 1.5, "total": 5, "on": 2},
                    "passes": {"expected": 0.8},
                    "games": {"minutes_played": 90},
                }
            ],
        }

        result = _parse_fixture_player_stats(player_data, 123)

        assert result["xg"] == 1.5
        assert result["xa"] == 0.8
        assert result["minutes"] == 90
        assert result["shots"] == 5
        assert result["shots_on_target"] == 2
        assert result["xg_per_90"] == 1.5  # (1.5 * 90) / 90
        assert result["xa_per_90"] == 0.8

    def test_parse_fixture_player_stats_wrong_player(self):
        """Test parsing returns empty dict for wrong player ID."""
        player_data = {
            "player": {"id": 123},
            "statistics": [{"shots": {"expected": 1.5}}],
        }

        result = _parse_fixture_player_stats(player_data, 999)

        assert result == {}

    def test_parse_fixture_player_stats_no_stats(self):
        """Test parsing with empty statistics array."""
        player_data = {"player": {"id": 123}, "statistics": []}

        result = _parse_fixture_player_stats(player_data, 123)

        assert result == {}

    def test_parse_fixture_player_stats_per_90_calculation(self):
        """Test per-90 calculation with partial minutes."""
        player_data = {
            "player": {"id": 123},
            "statistics": [
                {
                    "shots": {"expected": 0.5, "total": 2, "on": 1},
                    "passes": {"expected": 0.25},
                    "games": {"minutes_played": 45},
                }
            ],
        }

        result = _parse_fixture_player_stats(player_data, 123)

        # (0.5 * 90) / 45 = 1.0
        assert result["xg_per_90"] == 1.0
        # (0.25 * 90) / 45 = 0.5
        assert result["xa_per_90"] == 0.5

    def test_parse_fixture_player_stats_zero_minutes(self):
        """Test per-90 calculation with zero minutes (no play)."""
        player_data = {
            "player": {"id": 123},
            "statistics": [
                {
                    "shots": {"expected": 1.0},
                    "passes": {"expected": 0.5},
                    "games": {"minutes_played": 0},
                }
            ],
        }

        result = _parse_fixture_player_stats(player_data, 123)

        assert result["xg"] == 1.0
        assert result["xa"] == 0.5
        assert result["minutes"] == 0
        assert result["xg_per_90"] is None
        assert result["xa_per_90"] is None

    def test_parse_fixture_player_stats_missing_xg_xa(self):
        """Test parsing when xG/xA are missing."""
        player_data = {
            "player": {"id": 123},
            "statistics": [
                {
                    "shots": {"total": 3, "on": 1},
                    "passes": {},
                    "games": {"minutes_played": 60},
                }
            ],
        }

        result = _parse_fixture_player_stats(player_data, 123)

        assert result["xg"] is None
        assert result["xa"] is None
        assert result["shots"] == 3
        assert result["shots_on_target"] == 1


class TestAggregateFixturePlayerStats:
    """Test fixture player stats aggregation."""

    @patch("app.pipeline.sync_external.api_football.get_fixture_players")
    def test_aggregate_fixture_player_stats_single_match(self, mock_get_players):
        """Test aggregating stats from a single fixture."""
        mock_get_players.return_value = [
            {
                "player": {"id": 123},
                "statistics": [
                    {
                        "shots": {"expected": 1.0, "total": 3, "on": 1},
                        "passes": {"expected": 0.5},
                        "games": {"minutes_played": 90},
                    }
                ],
            }
        ]

        fixtures = [{"fixture_id": 1001}]

        result = _aggregate_fixture_player_stats(fixtures, 123)

        assert result["xg"] == 1.0
        assert result["xa"] == 0.5
        assert result["minutes"] == 90
        assert result["shots"] == 3

    @patch("app.pipeline.sync_external.api_football.get_fixture_players")
    def test_aggregate_fixture_player_stats_multiple_matches(self, mock_get_players):
        """Test aggregating stats across multiple fixtures."""
        # Mock different stats for each fixture
        mock_get_players.side_effect = [
            [
                {
                    "player": {"id": 123},
                    "statistics": [
                        {
                            "shots": {"expected": 1.0, "total": 2, "on": 1},
                            "passes": {"expected": 0.5},
                            "games": {"minutes_played": 90},
                        }
                    ],
                }
            ],
            [
                {
                    "player": {"id": 123},
                    "statistics": [
                        {
                            "shots": {"expected": 0.5, "total": 1, "on": 0},
                            "passes": {"expected": 0.3},
                            "games": {"minutes_played": 60},
                        }
                    ],
                }
            ],
        ]

        fixtures = [{"fixture_id": 1001}, {"fixture_id": 1002}]

        result = _aggregate_fixture_player_stats(fixtures, 123)

        # Should sum across fixtures
        assert result["xg"] == 1.5  # 1.0 + 0.5
        assert result["xa"] == 0.8  # 0.5 + 0.3
        assert result["minutes"] == 150  # 90 + 60
        assert result["shots"] == 3  # 2 + 1
        assert result["shots_on_target"] == 1  # 1 + 0

    @patch("app.pipeline.sync_external.api_football.get_fixture_players")
    def test_aggregate_fixture_player_stats_player_not_in_fixture(
        self, mock_get_players
    ):
        """Test aggregation when player didn't play in some fixtures."""
        mock_get_players.side_effect = [
            [
                {
                    "player": {"id": 999},
                    "statistics": [{"shots": {"expected": 1.0}}],
                }
            ],
            [
                {
                    "player": {"id": 123},
                    "statistics": [
                        {
                            "shots": {"expected": 0.5, "total": 1, "on": 0},
                            "passes": {"expected": 0.2},
                            "games": {"minutes_played": 45},
                        }
                    ],
                }
            ],
        ]

        fixtures = [{"fixture_id": 1001}, {"fixture_id": 1002}]

        result = _aggregate_fixture_player_stats(fixtures, 123)

        # Should only count the second fixture
        assert result["xg"] == 0.5
        assert result["minutes"] == 45

    @patch("app.pipeline.sync_external.api_football.get_fixture_players")
    def test_aggregate_fixture_player_stats_no_fixtures(self, mock_get_players):
        """Test aggregation with empty fixture list."""
        fixtures = []

        result = _aggregate_fixture_player_stats(fixtures, 123)

        assert result["xg"] == 0.0
        assert result["xa"] == 0.0
        assert result["minutes"] == 0

    @patch("app.pipeline.sync_external.api_football.get_fixture_players")
    def test_aggregate_fixture_player_stats_api_error(self, mock_get_players):
        """Test aggregation handles API errors gracefully."""
        mock_get_players.side_effect = [
            Exception("API Error"),
            [
                {
                    "player": {"id": 123},
                    "statistics": [
                        {
                            "shots": {"expected": 0.5, "total": 1, "on": 0},
                            "passes": {"expected": 0.2},
                            "games": {"minutes_played": 45},
                        }
                    ],
                }
            ],
        ]

        fixtures = [{"fixture_id": 1001}, {"fixture_id": 1002}]

        # Should not raise, should skip the failed fixture
        result = _aggregate_fixture_player_stats(fixtures, 123)

        # Should only count the second successful fixture
        assert result["xg"] == 0.5
        assert result["minutes"] == 45


class TestGetFixturesForSeason:
    """Test CRUD function to get fixtures for a season."""

    def test_get_fixtures_for_season_basic(self, db):
        """Test querying fixtures for a specific season."""
        season = models.Season(label="2024-2025", season_code="2024/25")
        competition = models.Competition(
            name="Premier League", code="PL", type="league"
        )
        home_team = models.Team(name="Arsenal", short_name="ARS", fpl_id=1)
        away_team = models.Team(name="Liverpool", short_name="LIV", fpl_id=2)

        match = models.Match(
            competition=competition,
            season=season,
            gameweek=1,
            match_date=date(2024, 8, 10),
            home_team=home_team,
            away_team=away_team,
            home_goals=2,
            away_goals=2,
            result="D",
            api_football_fixture_id=999001,
        )

        db.add_all([season, competition, home_team, away_team, match])
        db.commit()

        result = crud.get_fixtures_for_season(db, 39, 2024)

        assert len(result) == 1
        assert result[0]["fixture_id"] == 999001

    def test_get_fixtures_for_season_multiple_fixtures(self, db):
        """Test querying multiple fixtures for a season."""
        season = models.Season(label="2024-2025", season_code="2024/25")
        competition = models.Competition(
            name="Premier League", code="PL", type="league"
        )
        home_team = models.Team(name="Arsenal", short_name="ARS", fpl_id=1)
        away_team = models.Team(name="Liverpool", short_name="LIV", fpl_id=2)

        matches = [
            models.Match(
                competition=competition,
                season=season,
                gameweek=i,
                match_date=date(2024, 8, 10 + i),
                home_team=home_team,
                away_team=away_team,
                home_goals=2,
                away_goals=0,
                result="H",
                api_football_fixture_id=999000 + i,
            )
            for i in range(3)
        ]

        db.add_all([season, competition, home_team, away_team] + matches)
        db.commit()

        result = crud.get_fixtures_for_season(db, 39, 2024)

        assert len(result) == 3
        fixture_ids = [r["fixture_id"] for r in result]
        assert 999000 in fixture_ids
        assert 999001 in fixture_ids
        assert 999002 in fixture_ids

    def test_get_fixtures_for_season_excludes_incomplete(self, db):
        """Test that fixtures without api_football_fixture_id are excluded."""
        season = models.Season(label="2024-2025", season_code="2024/25")
        competition = models.Competition(
            name="Premier League", code="PL", type="league"
        )
        home_team = models.Team(name="Arsenal", short_name="ARS", fpl_id=1)
        away_team = models.Team(name="Liverpool", short_name="LIV", fpl_id=2)

        # Match without API fixture ID (not yet matched)
        incomplete_match = models.Match(
            competition=competition,
            season=season,
            gameweek=1,
            match_date=date(2024, 8, 10),
            home_team=home_team,
            away_team=away_team,
            home_goals=2,
            away_goals=2,
            result="D",
            api_football_fixture_id=None,
        )

        # Match with API fixture ID (completed/matched)
        complete_match = models.Match(
            competition=competition,
            season=season,
            gameweek=2,
            match_date=date(2024, 8, 17),
            home_team=home_team,
            away_team=away_team,
            home_goals=1,
            away_goals=0,
            result="H",
            api_football_fixture_id=999002,
        )

        db.add_all(
            [
                season,
                competition,
                home_team,
                away_team,
                incomplete_match,
                complete_match,
            ]
        )
        db.commit()

        result = crud.get_fixtures_for_season(db, 39, 2024)

        # Should only return the completed match
        assert len(result) == 1
        assert result[0]["fixture_id"] == 999002

    def test_get_fixtures_for_season_wrong_season(self, db):
        """Test querying fixtures for a non-existent season."""
        result = crud.get_fixtures_for_season(db, 39, 2020)

        assert len(result) == 0

    def test_get_fixtures_for_season_ordered_by_date(self, db):
        """Test that fixtures are ordered by date descending."""
        season = models.Season(label="2024-2025", season_code="2024/25")
        competition = models.Competition(
            name="Premier League", code="PL", type="league"
        )
        home_team = models.Team(name="Arsenal", short_name="ARS", fpl_id=1)
        away_team = models.Team(name="Liverpool", short_name="LIV", fpl_id=2)

        matches = [
            models.Match(
                competition=competition,
                season=season,
                gameweek=i,
                match_date=date(2024, 8, 10 + i),
                home_team=home_team,
                away_team=away_team,
                home_goals=1,
                away_goals=0,
                result="H",
                api_football_fixture_id=999000 + i,
            )
            for i in range(3)
        ]

        db.add_all([season, competition, home_team, away_team] + matches)
        db.commit()

        result = crud.get_fixtures_for_season(db, 39, 2024)

        # Should be ordered by date descending (most recent first)
        fixture_ids = [r["fixture_id"] for r in result]
        assert fixture_ids == [999002, 999001, 999000]
