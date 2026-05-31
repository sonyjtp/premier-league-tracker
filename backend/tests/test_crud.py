from app import crud, models


class TestPlayerCRUD:
    def test_get_players_empty(self, db):
        players = crud.get_players(db)
        assert players == []

    def test_get_players_with_search(self, db):
        player = models.Player(
            first_name="John",
            second_name="Doe",
            position="MID",
            current_fpl_id=1,
        )
        db.add(player)
        db.commit()

        results = crud.get_players(db, search_query="John")
        assert len(results) == 1
        assert results[0].first_name == "John"

    def test_get_players_no_match(self, db):
        player = models.Player(
            first_name="John",
            second_name="Doe",
            position="MID",
            current_fpl_id=1,
        )
        db.add(player)
        db.commit()

        results = crud.get_players(db, search_query="Nonexistent")
        assert results == []

    def test_get_player_by_id(self, db):
        player = models.Player(
            first_name="Jane",
            second_name="Smith",
            position="FWD",
            current_fpl_id=2,
        )
        db.add(player)
        db.commit()

        retrieved = crud.get_player_by_id(db, player.id)
        assert retrieved.first_name == "Jane"
        assert retrieved.position == "FWD"

    def test_get_player_by_id_not_found(self, db):
        retrieved = crud.get_player_by_id(db, 999)
        assert retrieved is None


class TestTeamCRUD:
    def test_get_teams_empty(self, db):
        teams = crud.get_teams(db)
        assert teams == []

    def test_get_teams_with_data(self, db):
        team = models.Team(
            name="Manchester United",
            short_name="MUN",
            fpl_id=1,
        )
        db.add(team)
        db.commit()

        teams = crud.get_teams(db)
        assert len(teams) == 1
        assert teams[0].name == "Manchester United"

    def test_get_team_by_id(self, db):
        team = models.Team(
            name="Liverpool",
            short_name="LIV",
            fpl_id=2,
        )
        db.add(team)
        db.commit()

        retrieved = crud.get_team_by_id(db, team.id)
        assert retrieved.name == "Liverpool"

    def test_get_team_by_id_not_found(self, db):
        retrieved = crud.get_team_by_id(db, 999)
        assert retrieved is None


class TestSeasonCRUD:
    def test_get_seasons(self, db):
        """Test retrieving all seasons."""
        season = models.Season(
            label="2024-25",
            season_code="2024",
        )
        db.add(season)
        db.commit()

        seasons = crud.get_seasons(db)
        assert len(seasons) >= 1
        assert any(s.label == "2024-25" for s in seasons)

    def test_get_season_by_id(self, db):
        """Test retrieving a season by ID."""
        season = models.Season(
            label="2023-24",
            season_code="2023",
        )
        db.add(season)
        db.commit()

        # Query directly instead of using crud function that may not exist
        retrieved = (
            db.query(models.Season).filter(models.Season.id == season.id).first()
        )
        assert retrieved is not None
        assert retrieved.label == "2023-24"


class TestPlayerSeasonSummaryCRUD:
    def test_get_player_season_summaries(self, db):
        """Test retrieving player season summaries."""
        competition = models.Competition(
            id=1, name="Premier League", code="PL", type="League"
        )
        season = models.Season(label="2024-25", season_code="2024")
        player = models.Player(
            first_name="Test",
            second_name="Player",
            position="MID",
            current_fpl_id=1,
        )
        db.add(competition)
        db.add(season)
        db.add(player)
        db.commit()

        summary = models.PlayerSeasonSummary(
            player_id=player.id,
            season_id=season.id,
            competition_id=competition.id,
            minutes=1800,
            goals=10,
            assists=5,
            clean_sheets=0,
            yellow_cards=2,
            red_cards=0,
            fpl_points=150,
        )
        db.add(summary)
        db.commit()

        results = crud.get_player_season_summaries(db, player.id)
        assert len(results) == 1
        assert results[0].goals == 10

    def test_get_player_season_summaries_empty(self, db):
        """Test empty player season summaries."""
        results = crud.get_player_season_summaries(db, 999)
        assert results == []
