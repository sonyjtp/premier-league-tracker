from datetime import date

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


class TestPlayerProfileCRUD:
    def test_upsert_player_profile_create(self, db):
        """Test upsert_player_profile creates new profile"""
        player = models.Player(
            first_name="John",
            second_name="Doe",
            position="MID",
            current_fpl_id=1,
        )
        db.add(player)
        db.commit()

        profile_data = {
            "birth_date": date(1990, 5, 15),
            "nationality": "England",
            "height": "180",
        }
        crud.upsert_player_profile(db, player.id, profile_data)

        profile = (
            db.query(models.PlayerProfile)
            .filter(models.PlayerProfile.player_id == player.id)
            .first()
        )
        assert profile is not None
        assert profile.nationality == "England"
        assert profile.height == "180"

    def test_upsert_player_profile_update(self, db):
        """Test upsert_player_profile updates existing profile"""
        player = models.Player(
            first_name="John",
            second_name="Doe",
            position="MID",
            current_fpl_id=1,
        )
        db.add(player)
        db.commit()

        # Create initial profile
        profile_data = {
            "birth_date": date(1990, 5, 15),
            "nationality": "England",
            "height": "180",
        }
        crud.upsert_player_profile(db, player.id, profile_data)

        # Update profile
        new_data = {"nationality": "Scotland"}
        crud.upsert_player_profile(db, player.id, new_data)

        profile = (
            db.query(models.PlayerProfile)
            .filter(models.PlayerProfile.player_id == player.id)
            .first()
        )
        assert profile.nationality == "Scotland"
        assert profile.height == "180"  # Unchanged


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


class TestCRUDMissingBranches:
    """Targeted tests for previously uncovered crud.py branches."""

    # ── get_players with team filter ──────────────────────────────────────────

    def test_get_players_by_team_internal_id(self, db):
        team = models.Team(name="Spurs", short_name="TOT", fpl_id=6)
        player = models.Player(
            first_name="Harry",
            second_name="Kane",
            position="FWD",
            current_fpl_id=10,
            fpl_team_id=6,
        )
        db.add_all([team, player])
        db.commit()

        results = crud.get_players(db, team_internal_id=team.id)
        assert len(results) == 1
        assert results[0].second_name == "Kane"

    # ── get_standings / get_standings_history with no competition ─────────────

    def test_get_standings_no_competition(self, db):
        assert crud.get_standings(db, season_id=1) == []

    def test_get_standings_history_no_competition(self, db):
        assert crud.get_standings_history(db, season_id=1) == []

    # ── get_team_form result branches ─────────────────────────────────────────

    def _make_competition(self, db):
        comp = models.Competition(name="Premier League", code="EPL", type="League")
        db.add(comp)
        db.commit()
        return comp

    def _make_match(
        self, db, home_team, away_team, season, comp, result, home_goals, away_goals
    ):
        m = models.Match(
            season_id=season.id,
            competition_id=comp.id,
            home_team_id=home_team.id,
            away_team_id=away_team.id,
            match_date=__import__("datetime").date(2024, 1, 1),
            result=result,
            home_goals=home_goals,
            away_goals=away_goals,
        )
        db.add(m)
        db.commit()
        return m

    def test_get_team_form_draw(self, db):
        season = models.Season(label="2024-25", season_code="2425")
        home = models.Team(name="Arsenal", short_name="ARS", fpl_id=1)
        away = models.Team(name="Chelsea", short_name="CHE", fpl_id=2)
        db.add_all([season, home, away])
        db.commit()
        comp = self._make_competition(db)
        self._make_match(db, home, away, season, comp, "D", 1, 1)

        form_list, form_str = crud.get_team_form(db, home.id, season.id)
        assert form_str == "D"
        assert form_list[0]["result"] == "D"

    def test_get_team_form_loss(self, db):
        season = models.Season(label="2024-25", season_code="2425")
        home = models.Team(name="Arsenal", short_name="ARS", fpl_id=1)
        away = models.Team(name="Chelsea", short_name="CHE", fpl_id=2)
        db.add_all([season, home, away])
        db.commit()
        comp = self._make_competition(db)
        self._make_match(db, home, away, season, comp, "A", 0, 2)

        form_list, form_str = crud.get_team_form(db, home.id, season.id)
        assert form_str == "L"
        assert form_list[0]["result"] == "L"

    # ── Profile upserts (update-existing branch) ──────────────────────────────

    def test_upsert_team_profile_update_existing(self, db):
        team = models.Team(name="Everton", short_name="EVE", fpl_id=7)
        db.add(team)
        db.commit()

        crud.upsert_team_profile(db, team.id, {"logo_url": "http://old.png"})
        crud.upsert_team_profile(db, team.id, {"logo_url": "http://new.png"})

        profile = db.query(models.TeamProfile).filter_by(team_id=team.id).first()
        assert profile.logo_url == "http://new.png"

    def test_upsert_player_profile_update_existing(self, db):
        player = models.Player(
            first_name="Mo", second_name="Salah", position="FWD", current_fpl_id=99
        )
        db.add(player)
        db.commit()

        crud.upsert_player_profile(db, player.id, {"nationality": "Egyptian"})
        crud.upsert_player_profile(db, player.id, {"nationality": "Egypt"})

        profile = db.query(models.PlayerProfile).filter_by(player_id=player.id).first()
        assert profile.nationality == "Egypt"

    # ── Match events ──────────────────────────────────────────────────────────

    def test_store_and_get_match_events(self, db):
        events = [
            {
                "minute": 45,
                "event_type": "Goal",
                "player_name": "Kane",
                "team_name": "Spurs",
                "detail": None,
                "assist_name": None,
                "comments": None,
                "extra_minute": None,
            },
        ]
        crud.store_match_events(db, fixture_api_id=9001, events=events)
        result = crud.get_match_events(db, fixture_api_id=9001)
        assert len(result) == 1
        assert result[0].minute == 45

    def test_store_match_events_no_duplicate(self, db):
        events = [
            {
                "minute": 10,
                "event_type": "Card",
                "player_name": "Silva",
                "team_name": "City",
                "detail": None,
                "assist_name": None,
                "comments": None,
                "extra_minute": None,
            },
        ]
        crud.store_match_events(db, fixture_api_id=9002, events=events)
        crud.store_match_events(db, fixture_api_id=9002, events=events)
        assert len(crud.get_match_events(db, fixture_api_id=9002)) == 1

    # ── Match lineups ─────────────────────────────────────────────────────────

    def test_store_and_get_match_lineups(self, db):
        entries = [
            {
                "team_name": "Arsenal",
                "formation": "4-3-3",
                "player_name": "Raya",
                "player_api_id": 1,
                "is_starter": True,
                "position": "G",
                "grid": "1:1",
                "shirt_number": 22,
            },
        ]
        crud.store_match_lineups(db, fixture_api_id=8001, entries=entries)
        result = crud.get_match_lineups(db, fixture_api_id=8001)
        assert len(result) == 1
        assert result[0].player_name == "Raya"

    def test_store_match_lineups_no_duplicate(self, db):
        entries = [
            {
                "team_name": "Chelsea",
                "formation": "4-2-3-1",
                "player_name": "Caballero",
                "player_api_id": 2,
                "is_starter": False,
                "position": "G",
                "grid": None,
                "shirt_number": 1,
            },
        ]
        crud.store_match_lineups(db, fixture_api_id=8002, entries=entries)
        crud.store_match_lineups(db, fixture_api_id=8002, entries=entries)
        assert len(crud.get_match_lineups(db, fixture_api_id=8002)) == 1

    # ── Match advanced stats ──────────────────────────────────────────────────

    def _make_match_with_season(self, db):
        season = models.Season(label="2024-25", season_code="2425")
        home = models.Team(name="T1", short_name="T1", fpl_id=11)
        away = models.Team(name="T2", short_name="T2", fpl_id=12)
        comp = models.Competition(name="Premier League", code="EPL", type="League")
        db.add_all([season, home, away, comp])
        db.commit()
        m = models.Match(
            season_id=season.id,
            competition_id=comp.id,
            home_team_id=home.id,
            away_team_id=away.id,
            match_date=__import__("datetime").date(2024, 3, 1),
            result="H",
            home_goals=2,
            away_goals=0,
        )
        db.add(m)
        db.commit()
        return m

    def test_get_match_advanced_stats_none(self, db):
        assert crud.get_match_advanced_stats(db, match_id=99999) is None

    def test_upsert_match_advanced_stats_insert(self, db):
        m = self._make_match_with_season(db)
        crud.upsert_match_advanced_stats(
            db,
            m.id,
            {
                "home_xg": 1.5,
                "away_xg": 0.8,
                "home_possession": 55.0,
                "away_possession": 45.0,
                "home_ppda": None,
                "away_ppda": None,
            },
        )
        stats = crud.get_match_advanced_stats(db, m.id)
        assert stats.home_xg == 1.5

    def test_upsert_match_advanced_stats_update(self, db):
        m = self._make_match_with_season(db)
        crud.upsert_match_advanced_stats(
            db,
            m.id,
            {
                "home_xg": 1.0,
                "away_xg": 0.5,
                "home_possession": 50.0,
                "away_possession": 50.0,
                "home_ppda": None,
                "away_ppda": None,
            },
        )
        crud.upsert_match_advanced_stats(
            db,
            m.id,
            {
                "home_xg": 2.0,
                "away_xg": 1.0,
                "home_possession": 60.0,
                "away_possession": 40.0,
                "home_ppda": None,
                "away_ppda": None,
            },
        )
        stats = crud.get_match_advanced_stats(db, m.id)
        assert stats.home_xg == 2.0

    # ── Player advanced stats upsert ──────────────────────────────────────────

    def test_upsert_player_advanced_stats_insert(self, db):
        season = models.Season(label="2024-25", season_code="2425")
        player = models.Player(
            first_name="Bukayo", second_name="Saka", position="MID", current_fpl_id=55
        )
        db.add_all([season, player])
        db.commit()

        crud.upsert_player_advanced_stats(
            db,
            player.id,
            season.id,
            {
                "xg": 8.5,
                "xa": 6.2,
                "npxg": 7.9,
                "xg_per_90": 0.4,
                "xa_per_90": 0.3,
                "progressive_carries": 80,
                "progressive_passes": 120,
                "progressive_receptions": 90,
                "shots": 75,
                "shots_on_target": 30,
            },
        )
        stats = (
            db.query(models.PlayerAdvancedStats)
            .filter_by(player_id=player.id, season_id=season.id)
            .first()
        )
        assert stats.xg == 8.5

    def test_upsert_player_advanced_stats_update(self, db):
        season = models.Season(label="2024-25", season_code="2425")
        player = models.Player(
            first_name="Bukayo", second_name="Saka", position="MID", current_fpl_id=55
        )
        db.add_all([season, player])
        db.commit()

        data = {
            "xg": 5.0,
            "xa": 3.0,
            "npxg": 4.5,
            "xg_per_90": 0.3,
            "xa_per_90": 0.2,
            "progressive_carries": 60,
            "progressive_passes": 100,
            "progressive_receptions": 70,
            "shots": 50,
            "shots_on_target": 20,
        }
        crud.upsert_player_advanced_stats(db, player.id, season.id, data)
        data["xg"] = 9.9
        crud.upsert_player_advanced_stats(db, player.id, season.id, data)

        stats = (
            db.query(models.PlayerAdvancedStats)
            .filter_by(player_id=player.id, season_id=season.id)
            .first()
        )
        assert stats.xg == 9.9
