"""Tests for sync functions and data pipeline."""
from datetime import date
from unittest.mock import MagicMock, patch

from app import crud, models
from app.pipeline.sync_external import (
    _aggregate_fixture_player_stats,
    _parse_fixture_player_stats,
)


class TestParseFixturePlayerStats:
    """Test fixture player stats parsing."""

    def test_parse_fixture_player_stats_valid(self):
        """Test parsing valid fixture player stats (current API field layout)."""
        player_data = {
            "player": {"id": 123},
            "statistics": [
                {
                    "goals": {"xg": 1.5},
                    "shots": {"total": 5, "on": 2},
                    "passes": {"expected": 0.8},
                    "games": {"minutes": 90},
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

    def test_parse_fixture_player_stats_xg_fallback(self):
        """Test xG falls back to shots.expected when goals.xg is absent."""
        player_data = {
            "player": {"id": 123},
            "statistics": [
                {
                    "shots": {"expected": 1.2, "total": 4, "on": 1},
                    "passes": {"expected": 0.3},
                    "games": {"minutes": 90},
                }
            ],
        }

        result = _parse_fixture_player_stats(player_data, 123)

        assert result["xg"] == 1.2
        assert result["xa"] == 0.3

    def test_parse_fixture_player_stats_wrong_player(self):
        """Test parsing returns empty dict for wrong player ID."""
        player_data = {
            "player": {"id": 123},
            "statistics": [{"goals": {"xg": 1.5}}],
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
                    "goals": {"xg": 0.5},
                    "shots": {"total": 2, "on": 1},
                    "passes": {"expected": 0.25},
                    "games": {"minutes": 45},
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
                    "goals": {"xg": 1.0},
                    "passes": {"expected": 0.5},
                    "games": {"minutes": 0},
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
                    "games": {"minutes": 60},
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
                        "goals": {"xg": 1.0},
                        "shots": {"total": 3, "on": 1},
                        "passes": {"expected": 0.5},
                        "games": {"minutes": 90},
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
        mock_get_players.side_effect = [
            [
                {
                    "player": {"id": 123},
                    "statistics": [
                        {
                            "goals": {"xg": 1.0},
                            "shots": {"total": 2, "on": 1},
                            "passes": {"expected": 0.5},
                            "games": {"minutes": 90},
                        }
                    ],
                }
            ],
            [
                {
                    "player": {"id": 123},
                    "statistics": [
                        {
                            "goals": {"xg": 0.5},
                            "shots": {"total": 1, "on": 0},
                            "passes": {"expected": 0.3},
                            "games": {"minutes": 60},
                        }
                    ],
                }
            ],
        ]

        fixtures = [{"fixture_id": 1001}, {"fixture_id": 1002}]

        result = _aggregate_fixture_player_stats(fixtures, 123)

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
                    "statistics": [{"goals": {"xg": 1.0}}],
                }
            ],
            [
                {
                    "player": {"id": 123},
                    "statistics": [
                        {
                            "goals": {"xg": 0.5},
                            "shots": {"total": 1, "on": 0},
                            "passes": {"expected": 0.2},
                            "games": {"minutes": 45},
                        }
                    ],
                }
            ],
        ]

        fixtures = [{"fixture_id": 1001}, {"fixture_id": 1002}]

        result = _aggregate_fixture_player_stats(fixtures, 123)

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
                            "goals": {"xg": 0.5},
                            "shots": {"total": 1, "on": 0},
                            "passes": {"expected": 0.2},
                            "games": {"minutes": 45},
                        }
                    ],
                }
            ],
        ]

        fixtures = [{"fixture_id": 1001}, {"fixture_id": 1002}]

        result = _aggregate_fixture_player_stats(fixtures, 123)

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

        fixture_ids = [r["fixture_id"] for r in result]
        assert fixture_ids == [999002, 999001, 999000]


class TestSyncUnderstatPlayerIds:
    """Tests for sync_understat_player_ids fuzzy-matching logic."""

    @patch("app.pipeline.sync_external.understat_service.get_player_season_stats")
    @patch("app.pipeline.sync_external.SessionLocal")
    def test_maps_simple_name(self, mock_session_cls, mock_get_stats):
        """Normal two-word name matches cleanly."""
        mock_get_stats.return_value = [
            {"player": "Mohamed Salah", "player_id": 111},
        ]

        mock_db = MagicMock()
        mock_session_cls.return_value = mock_db

        player = MagicMock()
        player.first_name = "Mohamed"
        player.second_name = "Salah"
        player.id = 1
        player.understat_id = None
        mock_db.query.return_value.filter.return_value.all.return_value = [player]

        from app.pipeline.sync_external import sync_understat_player_ids

        sync_understat_player_ids(leagues=["ENG-Premier League"], seasons=[2024])

        assert player.understat_id == 111
        mock_db.commit.assert_called_once()

    @patch("app.pipeline.sync_external.understat_service.get_player_season_stats")
    @patch("app.pipeline.sync_external.SessionLocal")
    def test_maps_single_name_player(self, mock_session_cls, mock_get_stats):
        """Player known by one name (e.g. Richarlison) is matched via word boundary."""
        mock_get_stats.return_value = [
            {"player": "Richarlison", "player_id": 6026},
        ]

        mock_db = MagicMock()
        mock_session_cls.return_value = mock_db

        player = MagicMock()
        player.first_name = "Richarlison"
        player.second_name = "de Andrade"
        player.id = 1
        player.understat_id = None
        mock_db.query.return_value.filter.return_value.all.return_value = [player]

        from app.pipeline.sync_external import sync_understat_player_ids

        sync_understat_player_ids(leagues=["ENG-Premier League"], seasons=[2024])

        assert player.understat_id == 6026

    @patch("app.pipeline.sync_external.understat_service.get_player_season_stats")
    @patch("app.pipeline.sync_external.SessionLocal")
    def test_skips_ambiguous_single_name(self, mock_session_cls, mock_get_stats):
        """Single-word Understat name shared by multiple players is skipped."""
        mock_get_stats.return_value = [
            {"player": "Gabriel", "player_id": 5613},
        ]

        mock_db = MagicMock()
        mock_session_cls.return_value = mock_db

        # Two players both have "Gabriel" in their name → ambiguous
        p1 = MagicMock()
        p1.first_name = "Gabriel"
        p1.second_name = "dos Santos Magalhães"
        p1.id = 1
        p1.understat_id = None

        p2 = MagicMock()
        p2.first_name = "Gabriel"
        p2.second_name = "Gudmundsson"
        p2.id = 2
        p2.understat_id = None

        mock_db.query.return_value.filter.return_value.all.return_value = [p1, p2]

        from app.pipeline.sync_external import sync_understat_player_ids

        sync_understat_player_ids(leagues=["ENG-Premier League"], seasons=[2024])

        # Neither should be mapped — ambiguous single-name match skipped
        assert p1.understat_id is None
        assert p2.understat_id is None

    @patch("app.pipeline.sync_external.understat_service.get_player_season_stats")
    @patch("app.pipeline.sync_external.SessionLocal")
    def test_token_set_ratio_multi_word(self, mock_session_cls, mock_get_stats):
        """token_set_ratio matches 'Gabriel Fernando de Jesus' → 'Gabriel Jesus'."""
        mock_get_stats.return_value = [
            {"player": "Gabriel Jesus", "player_id": 5543},
            {"player": "Gabriel", "player_id": 5613},
        ]

        mock_db = MagicMock()
        mock_session_cls.return_value = mock_db

        player = MagicMock()
        player.first_name = "Gabriel"
        player.second_name = "Fernando de Jesus"
        player.id = 29
        player.understat_id = None
        mock_db.query.return_value.filter.return_value.all.return_value = [player]

        from app.pipeline.sync_external import sync_understat_player_ids

        sync_understat_player_ids(leagues=["ENG-Premier League"], seasons=[2024])

        # Should match "Gabriel Jesus" (higher specificity) not "Gabriel"
        assert player.understat_id == 5543

    @patch("app.pipeline.sync_external.understat_service.get_player_season_stats")
    @patch("app.pipeline.sync_external.SessionLocal")
    def test_no_match_below_threshold(self, mock_session_cls, mock_get_stats):
        """Player with no good Understat match remains unmapped."""
        mock_get_stats.return_value = [
            {"player": "Completely Different Name", "player_id": 9999},
        ]

        mock_db = MagicMock()
        mock_session_cls.return_value = mock_db

        player = MagicMock()
        player.first_name = "Unrelated"
        player.second_name = "Player"
        player.id = 99
        player.understat_id = None
        mock_db.query.return_value.filter.return_value.all.return_value = [player]

        from app.pipeline.sync_external import sync_understat_player_ids

        sync_understat_player_ids(leagues=["ENG-Premier League"], seasons=[2024])

        assert player.understat_id is None

    @patch("app.pipeline.sync_external.understat_service.get_player_season_stats")
    @patch("app.pipeline.sync_external.SessionLocal")
    def test_collision_resolved_by_score(self, mock_session_cls, mock_get_stats):
        """When two players compete for the same Understat ID, higher score wins."""
        mock_get_stats.return_value = [
            {"player": "Mohamed Salah", "player_id": 111},
        ]

        mock_db = MagicMock()
        mock_session_cls.return_value = mock_db

        # p1: exact full-name match (score ~100)
        p1 = MagicMock()
        p1.first_name = "Mohamed"
        p1.second_name = "Salah"
        p1.id = 1
        p1.understat_id = None

        # p2: partial match (lower score)
        p2 = MagicMock()
        p2.first_name = "Salah"
        p2.second_name = "Benali"
        p2.id = 2
        p2.understat_id = None

        mock_db.query.return_value.filter.return_value.all.return_value = [p1, p2]

        from app.pipeline.sync_external import sync_understat_player_ids

        sync_understat_player_ids(leagues=["ENG-Premier League"], seasons=[2024])

        # p1 wins the collision; p2 is not assigned the same ID
        assert p1.understat_id == 111
        assert p2.understat_id is None


class TestSyncUnderstatXg:
    """Tests for sync_understat_xg data writing."""

    def _make_db_mock(self, seasons, players, existing_stat=None):
        """
        Build a MagicMock database session wired for sync_understat_xg.

        sync_understat_xg uses three distinct query patterns:
          1. db.query(Season).all()                        → seasons list
          2. db.query(Player).filter(...).all()            → players list
          3. db.query(PlayerAdvancedStats).filter(...).first() → existing row
        """
        mock_db = MagicMock()

        def _query_side_effect(model):
            q = MagicMock()
            model_name = getattr(model, "__name__", str(model))
            if "Season" in model_name:
                q.all.return_value = seasons
                q.filter.return_value.all.return_value = seasons
            elif "PlayerAdvancedStats" in model_name:
                # Must be checked before "Player" since it contains that substring
                q.filter.return_value.first.return_value = existing_stat
            elif "Player" in model_name:
                q.all.return_value = players
                q.filter.return_value.all.return_value = players
            return q

        mock_db.query.side_effect = _query_side_effect
        return mock_db

    @patch("app.pipeline.sync_external.crud.upsert_player_advanced_stats")
    @patch("app.pipeline.sync_external.understat_service.get_player_season_stats")
    @patch("app.pipeline.sync_external.SessionLocal")
    def test_writes_xg_for_mapped_player(
        self, mock_session_cls, mock_get_stats, mock_upsert
    ):
        """xG/xA rows are written for players with a mapped understat_id."""
        mock_get_stats.return_value = [
            {
                "player_id": 6026,
                "player": "Richarlison",
                "xg": 4.3,
                "xa": 0.8,
                "np_xg": 4.0,
                "shots": 17,
                "minutes": 900,
            }
        ]

        season = MagicMock()
        season.id = 10
        season.label = "2024-2025"

        player = MagicMock()
        player.id = 742
        player.understat_id = 6026

        mock_session_cls.return_value = self._make_db_mock(
            seasons=[season], players=[player], existing_stat=None
        )

        from app.pipeline.sync_external import sync_understat_xg

        sync_understat_xg(leagues=["ENG-Premier League"])

        mock_upsert.assert_called_once()
        stats_dict = mock_upsert.call_args[0][3]
        assert stats_dict["xg"] == 4.3
        assert stats_dict["xa"] == 0.8
        assert stats_dict["shots"] == 17

    @patch("app.pipeline.sync_external.crud.upsert_player_advanced_stats")
    @patch("app.pipeline.sync_external.understat_service.get_player_season_stats")
    @patch("app.pipeline.sync_external.SessionLocal")
    def test_skips_already_populated(
        self, mock_session_cls, mock_get_stats, mock_upsert
    ):
        """Seasons where xg is already populated are skipped."""
        mock_get_stats.return_value = [
            {
                "player_id": 6026,
                "xg": 4.3,
                "xa": 0.8,
                "np_xg": 4.0,
                "shots": 17,
                "minutes": 900,
            }
        ]

        season = MagicMock()
        season.id = 10
        season.label = "2024-2025"

        player = MagicMock()
        player.id = 742
        player.understat_id = 6026

        existing = MagicMock()
        existing.xg = 4.3  # already populated

        mock_session_cls.return_value = self._make_db_mock(
            seasons=[season], players=[player], existing_stat=existing
        )

        from app.pipeline.sync_external import sync_understat_xg

        sync_understat_xg(leagues=["ENG-Premier League"])

        mock_upsert.assert_not_called()

    @patch("app.pipeline.sync_external.crud.upsert_player_advanced_stats")
    @patch("app.pipeline.sync_external.understat_service.get_player_season_stats")
    @patch("app.pipeline.sync_external.SessionLocal")
    def test_skips_player_with_no_minutes(
        self, mock_session_cls, mock_get_stats, mock_upsert
    ):
        """Players who didn't play in a season (minutes=0) are skipped."""
        mock_get_stats.return_value = [
            {
                "player_id": 6026,
                "xg": 0.0,
                "xa": 0.0,
                "np_xg": 0.0,
                "shots": 0,
                "minutes": 0,
            }
        ]

        season = MagicMock()
        season.id = 10
        season.label = "2024-2025"

        player = MagicMock()
        player.id = 742
        player.understat_id = 6026

        mock_session_cls.return_value = self._make_db_mock(
            seasons=[season], players=[player], existing_stat=None
        )

        from app.pipeline.sync_external import sync_understat_xg

        sync_understat_xg(leagues=["ENG-Premier League"])

        mock_upsert.assert_not_called()

    @patch("app.pipeline.sync_external.understat_service.get_player_season_stats")
    @patch("app.pipeline.sync_external.SessionLocal")
    def test_skips_pre_2014_seasons(self, mock_session_cls, mock_get_stats):
        """Seasons before 2014 are skipped (Understat doesn't cover them)."""
        old_season = MagicMock()
        old_season.label = "2013-2014"

        mock_session_cls.return_value = self._make_db_mock(
            seasons=[old_season], players=[]
        )

        from app.pipeline.sync_external import sync_understat_xg

        sync_understat_xg(leagues=["ENG-Premier League"])

        mock_get_stats.assert_not_called()
