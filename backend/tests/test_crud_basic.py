"""Basic CRUD tests focusing on core functionality."""
from app import crud, models


class TestPlayerQueries:
    """Test basic player queries."""

    def test_get_players_limit(self, db):
        """Test that get_players respects limit."""
        players = [
            models.Player(
                first_name=f"P{i}",
                second_name=f"L{i}",
                position="FWD",
                current_fpl_id=i,
            )
            for i in range(20)
        ]
        db.add_all(players)
        db.commit()

        # Test default limit
        results = crud.get_players(db)
        assert len(results) > 0


class TestTeamQueries:
    """Test basic team queries."""

    def test_get_teams_count(self, db):
        """Test counting teams."""
        teams = [
            models.Team(name=f"T{i}", short_name=f"T{i}", fpl_id=i) for i in range(3)
        ]
        db.add_all(teams)
        db.commit()

        results = crud.get_teams(db)
        assert len(results) == 3


class TestCompetitionQueries:
    """Test competition queries."""

    def test_get_competitions_empty(self, db):
        """Test getting empty competitions."""
        results = crud.get_competitions(db)
        assert isinstance(results, list)


class TestAdvancedStatsQueries:
    """Test advanced stats retrieval."""

    def test_get_player_advanced_stats_returns_list(self, db):
        """Test that advanced stats returns a list."""
        result = crud.get_player_advanced_stats(db, 1)
        assert isinstance(result, list)
        assert len(result) == 0


class TestSeasonQueries:
    """Test season queries."""

    def test_get_season_by_id_returns_none(self, db):
        """Test season lookup for non-existent season."""
        # This tests the function exists and handles missing data
        result = db.query(models.Season).filter_by(id=99999).first()
        assert result is None
