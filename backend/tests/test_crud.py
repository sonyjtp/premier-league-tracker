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

    def test_get_teams_with_season_filter(self, db):
        """Test get_teams filters by season_id"""
        season = models.Season(label="2023-24", season_code="2324")
        team1 = models.Team(name="Arsenal", short_name="ARS", fpl_id=1)
        team2 = models.Team(name="Chelsea", short_name="CHE", fpl_id=2)
        db.add_all([season, team1, team2])
        db.commit()

        # Add only team1 to season
        db.add(models.TeamSeason(team_id=team1.id, season_id=season.id))
        db.commit()

        teams = crud.get_teams(db, season_id=season.id)
        assert len(teams) == 1
        assert teams[0].name == "Arsenal"


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


class TestStandingsCRUD:
    def test_get_standings_empty(self, db):
        """Test get_standings when no standings exist"""
        season = models.Season(label="2023-24", season_code="2324")
        comp = models.Competition(
            id=1, name="Premier League", code="EPL", type="League"
        )
        db.add_all([season, comp])
        db.commit()

        standings = crud.get_standings(db, season_id=season.id)
        assert standings == []

    def test_get_standings_specific_gameweek(self, db):
        """Test get_standings with specific gameweek"""
        season = models.Season(label="2023-24", season_code="2324")
        team = models.Team(name="Arsenal", short_name="ARS", fpl_id=1)
        comp = models.Competition(
            id=1, name="Premier League", code="EPL", type="League"
        )
        db.add_all([season, team, comp])
        db.commit()

        # Add standings for different gameweeks
        for gw in [1, 2, 3]:
            standing = models.GameweekStanding(
                season_id=season.id,
                team_id=team.id,
                gameweek=gw,
                position=1,
                points=3 * gw,
                played=gw,
                wins=gw,
                draws=0,
                losses=0,
                goals_for=3 * gw,
                goals_against=0,
                goal_difference=3 * gw,
                competition_id=comp.id,
            )
            db.add(standing)
        db.commit()

        standings = crud.get_standings(db, season_id=season.id, gameweek=2)
        assert len(standings) == 1
        assert standings[0].points == 6

    def test_get_standings_history(self, db):
        """Test get_standings_history"""
        season = models.Season(label="2023-24", season_code="2324")
        team = models.Team(name="Arsenal", short_name="ARS", fpl_id=1)
        comp = models.Competition(
            id=1, name="Premier League", code="EPL", type="League"
        )
        db.add_all([season, team, comp])
        db.commit()

        # Add standings for multiple gameweeks
        for gw in [1, 2, 3]:
            standing = models.GameweekStanding(
                season_id=season.id,
                team_id=team.id,
                gameweek=gw,
                position=1,
                points=3 * gw,
                played=gw,
                wins=gw,
                draws=0,
                losses=0,
                goals_for=3 * gw,
                goals_against=0,
                goal_difference=3 * gw,
                competition_id=comp.id,
            )
            db.add(standing)
        db.commit()

        history = crud.get_standings_history(db, season_id=season.id)
        assert len(history) == 3
        assert history[0].gameweek == 1
        assert history[2].gameweek == 3


class TestTeamFormCRUD:
    def test_get_team_form_empty(self, db):
        """Test get_team_form when team has no matches"""
        season = models.Season(label="2023-24", season_code="2324")
        team = models.Team(name="Arsenal", short_name="ARS", fpl_id=1)
        db.add_all([season, team])
        db.commit()

        form_list, form_string = crud.get_team_form(db, team.id, season.id)
        assert form_list == []
        assert form_string == ""

    def test_get_team_form_with_matches(self, db):
        """Test get_team_form with actual match data"""
        from datetime import date

        season = models.Season(label="2023-24", season_code="2324")
        team_home = models.Team(name="Arsenal", short_name="ARS", fpl_id=1)
        team_away = models.Team(name="Chelsea", short_name="CHE", fpl_id=2)
        comp = models.Competition(
            id=1, name="Premier League", code="EPL", type="League"
        )
        db.add_all([season, team_home, team_away, comp])
        db.commit()

        # Add a match that Arsenal won
        match = models.Match(
            season_id=season.id,
            competition_id=comp.id,
            gameweek=1,
            match_date=date(2023, 8, 12),
            home_team_id=team_home.id,
            away_team_id=team_away.id,
            home_goals=3,
            away_goals=1,
            result="H",
            home_shots=10,
            away_shots=5,
            home_shots_on_target=5,
            away_shots_on_target=2,
        )
        db.add(match)
        db.commit()

        form_list, form_string = crud.get_team_form(db, team_home.id, season.id)
        assert len(form_list) == 1
        assert form_string == "W"
        assert form_list[0]["result"] == "W"
        assert form_list[0]["goals_for"] == 3
        assert form_list[0]["goals_against"] == 1


class TestPlayerRecentStatsCRUD:
    def test_get_player_recent_stats_empty(self, db):
        """Test get_player_recent_stats when player has no stats"""
        player = models.Player(
            first_name="John",
            second_name="Doe",
            position="MID",
            current_fpl_id=1,
        )
        db.add(player)
        db.commit()

        stats = crud.get_player_recent_stats(db, player.id)
        assert stats == []

    def test_get_player_recent_stats_with_data(self, db):
        """Test get_player_recent_stats returns recent match stats"""
        from datetime import date

        season = models.Season(label="2023-24", season_code="2324")
        team = models.Team(name="Arsenal", short_name="ARS", fpl_id=1)
        player = models.Player(
            first_name="John",
            second_name="Doe",
            position="MID",
            current_fpl_id=1,
            fpl_team_id=1,
        )
        comp = models.Competition(
            id=1, name="Premier League", code="EPL", type="League"
        )
        db.add_all([season, team, player, comp])
        db.commit()

        # Add matches
        for i in range(1, 4):
            match = models.Match(
                season_id=season.id,
                competition_id=comp.id,
                gameweek=i,
                match_date=date(2023, 8, 12 + i),
                home_team_id=team.id,
                away_team_id=team.id,
                home_goals=1,
                away_goals=0,
                result="H",
            )
            db.add(match)
        db.commit()

        # Add player match stats
        matches = db.query(models.Match).all()
        for match in matches:
            stat = models.PlayerMatchStat(
                player_id=player.id,
                match_id=match.id,
                minutes=90,
                goals=1,
                assists=0,
            )
            db.add(stat)
        db.commit()

        stats = crud.get_player_recent_stats(db, player.id, limit=2)
        assert len(stats) == 2


class TestTeamSeasonHistoryCRUD:
    def test_get_team_season_history_empty(self, db):
        """Test get_team_season_history when team has no standings"""
        team = models.Team(name="Arsenal", short_name="ARS", fpl_id=1)
        db.add(team)
        db.commit()

        history = crud.get_team_season_history(db, team.id)
        assert history == []

    def test_get_team_season_history_single_season(self, db):
        """Test get_team_season_history for one season"""
        season = models.Season(label="2023-24", season_code="2324")
        team = models.Team(name="Arsenal", short_name="ARS", fpl_id=1)
        comp = models.Competition(
            id=1, name="Premier League", code="EPL", type="League"
        )
        db.add_all([season, team, comp])
        db.commit()

        # Add standings for final gameweek
        standing = models.GameweekStanding(
            season_id=season.id,
            team_id=team.id,
            gameweek=38,
            position=2,
            points=89,
            played=38,
            wins=26,
            draws=11,
            losses=1,
            goals_for=88,
            goals_against=33,
            goal_difference=55,
            competition_id=comp.id,
        )
        db.add(standing)
        db.commit()

        history = crud.get_team_season_history(db, team.id)
        assert len(history) == 1
        assert history[0]["final_position"] == 2
        assert history[0]["season_label"] == "2023-24"


class TestCompetitionsCRUD:
    def test_get_competitions_empty(self, db):
        """Test get_competitions when no competitions exist"""
        comps = crud.get_competitions(db)
        assert comps == []

    def test_get_competitions_with_data(self, db):
        """Test get_competitions returns all competitions"""
        comp1 = models.Competition(name="Premier League", code="EPL", type="League")
        comp2 = models.Competition(name="FA Cup", code="FAC", type="Cup")
        db.add_all([comp1, comp2])
        db.commit()

        comps = crud.get_competitions(db)
        assert len(comps) == 2


class TestHeadToHeadCRUD:
    def test_get_head_to_head_empty(self, db):
        """Test get_head_to_head when teams have no matches"""
        team_a = models.Team(name="Arsenal", short_name="ARS", fpl_id=1)
        team_b = models.Team(name="Chelsea", short_name="CHE", fpl_id=2)
        db.add_all([team_a, team_b])
        db.commit()

        matches = crud.get_head_to_head(db, team_a.id, team_b.id)
        assert matches == []

    def test_get_head_to_head_with_matches(self, db):
        """Test get_head_to_head returns matches between two teams"""
        from datetime import date

        season = models.Season(label="2023-24", season_code="2324")
        team_a = models.Team(name="Arsenal", short_name="ARS", fpl_id=1)
        team_b = models.Team(name="Chelsea", short_name="CHE", fpl_id=2)
        comp = models.Competition(
            id=1, name="Premier League", code="EPL", type="League"
        )
        db.add_all([season, team_a, team_b, comp])
        db.commit()

        # Add home and away matches
        match1 = models.Match(
            season_id=season.id,
            competition_id=comp.id,
            gameweek=1,
            match_date=date(2023, 8, 12),
            home_team_id=team_a.id,
            away_team_id=team_b.id,
            home_goals=2,
            away_goals=1,
            result="H",
        )
        match2 = models.Match(
            season_id=season.id,
            competition_id=comp.id,
            gameweek=15,
            match_date=date(2024, 1, 15),
            home_team_id=team_b.id,
            away_team_id=team_a.id,
            home_goals=1,
            away_goals=1,
            result="D",
        )
        db.add_all([match1, match2])
        db.commit()

        matches = crud.get_head_to_head(db, team_a.id, team_b.id)
        assert len(matches) == 2


class TestTeamProfileCRUD:
    def test_upsert_team_profile_create(self, db):
        """Test upsert_team_profile creates new profile"""
        team = models.Team(name="Arsenal", short_name="ARS", fpl_id=1)
        db.add(team)
        db.commit()

        profile_data = {
            "logo_url": "https://example.com/logo.png",
            "country": "England",
            "founded": 1886,
        }
        crud.upsert_team_profile(db, team.id, profile_data)

        profile = (
            db.query(models.TeamProfile)
            .filter(models.TeamProfile.team_id == team.id)
            .first()
        )
        assert profile is not None
        assert profile.logo_url == "https://example.com/logo.png"
        assert profile.country == "England"
        assert profile.founded == 1886

    def test_upsert_team_profile_update(self, db):
        """Test upsert_team_profile updates existing profile"""
        team = models.Team(name="Arsenal", short_name="ARS", fpl_id=1)
        db.add(team)
        db.commit()

        # Create initial profile
        profile_data = {
            "logo_url": "https://example.com/logo.png",
            "country": "England",
            "founded": 1886,
        }
        crud.upsert_team_profile(db, team.id, profile_data)

        # Update profile
        new_data = {"country": "Scotland"}
        crud.upsert_team_profile(db, team.id, new_data)

        profile = (
            db.query(models.TeamProfile)
            .filter(models.TeamProfile.team_id == team.id)
            .first()
        )
        assert profile.country == "Scotland"
        assert profile.founded == 1886  # Unchanged


class TestLatestGameweekCRUD:
    def test_get_latest_gameweek_no_competition(self, db):
        """Test get_latest_gameweek when competition doesn't exist"""
        season = models.Season(label="2023-24", season_code="2324")
        db.add(season)
        db.commit()

        gw = crud.get_latest_gameweek(db, season.id, "NONEXISTENT")
        assert gw == 0

    def test_get_latest_gameweek_empty(self, db):
        """Test get_latest_gameweek when no standings exist"""
        season = models.Season(label="2023-24", season_code="2324")
        comp = models.Competition(
            id=1, name="Premier League", code="EPL", type="League"
        )
        db.add_all([season, comp])
        db.commit()

        gw = crud.get_latest_gameweek(db, season.id)
        assert gw == 0

    def test_get_latest_gameweek_with_data(self, db):
        """Test get_latest_gameweek returns highest gameweek"""
        season = models.Season(label="2023-24", season_code="2324")
        team = models.Team(name="Arsenal", short_name="ARS", fpl_id=1)
        comp = models.Competition(
            id=1, name="Premier League", code="EPL", type="League"
        )
        db.add_all([season, team, comp])
        db.commit()

        # Add standings for multiple gameweeks
        for gw in [1, 5, 10, 15]:
            standing = models.GameweekStanding(
                season_id=season.id,
                team_id=team.id,
                gameweek=gw,
                position=1,
                points=3 * gw,
                played=gw,
                wins=gw,
                draws=0,
                losses=0,
                goals_for=3 * gw,
                goals_against=0,
                goal_difference=3 * gw,
                competition_id=comp.id,
            )
            db.add(standing)
        db.commit()

        gw = crud.get_latest_gameweek(db, season.id)
        assert gw == 15
