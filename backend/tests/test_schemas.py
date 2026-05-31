from app.schemas import (
    PlayerMatchStatSchema,
    PlayerSchema,
    PlayerSeasonSummarySchema,
    SeasonSchema,
    StandingItemSchema,
    TeamSchema,
)


class TestPlayerSchema:
    def test_player_schema_valid(self):
        player_data = {
            "id": 1,
            "first_name": "John",
            "second_name": "Doe",
            "position": "MID",
            "current_fpl_id": 100,
            "fpl_team_id": 1,
            "api_football_id": 500,
        }
        player = PlayerSchema(**player_data)
        assert player.id == 1
        assert player.first_name == "John"
        assert player.position == "MID"

    def test_player_schema_optional_fields(self):
        player_data = {
            "id": 1,
            "first_name": "John",
            "second_name": "Doe",
            "position": "FWD",
        }
        player = PlayerSchema(**player_data)
        assert player.current_fpl_id is None
        assert player.api_football_id is None


class TestTeamSchema:
    def test_team_schema_valid(self):
        team_data = {
            "id": 1,
            "name": "Manchester United",
            "short_name": "MUN",
            "fpl_id": 1,
            "api_football_id": 33,
        }
        team = TeamSchema(**team_data)
        assert team.name == "Manchester United"
        assert team.fpl_id == 1

    def test_team_schema_minimal(self):
        team_data = {
            "id": 1,
            "name": "Liverpool",
            "short_name": "LIV",
        }
        team = TeamSchema(**team_data)
        assert team.fpl_id is None


class TestSeasonSchema:
    def test_season_schema_valid(self):
        season_data = {
            "id": 1,
            "label": "2024-25",
            "season_code": "2024",
        }
        season = SeasonSchema(**season_data)
        assert season.label == "2024-25"
        assert season.id == 1


class TestPlayerSeasonSummarySchema:
    def test_player_season_summary_valid(self):
        summary_data = {
            "season_label": "2024-25",
            "minutes": 1800,
            "goals": 10,
            "assists": 5,
            "clean_sheets": 3,
            "yellow_cards": 2,
            "red_cards": 0,
            "fpl_points": 150,
        }
        summary = PlayerSeasonSummarySchema(**summary_data)
        assert summary.goals == 10
        assert summary.fpl_points == 150


class TestPlayerMatchStatSchema:
    def test_player_match_stat_valid(self):
        match_data = {
            "gameweek": 1,
            "opponent_name": "Liverpool",
            "minutes": 90,
            "goals": 1,
            "assists": 0,
            "clean_sheets": 0,
            "yellow_cards": 0,
            "red_cards": 0,
            "fpl_points": 15,
        }
        stat = PlayerMatchStatSchema(**match_data)
        assert stat.minutes == 90
        assert stat.opponent_name == "Liverpool"


class TestStandingItemSchema:
    def test_standing_item_schema_valid(self):
        team_data = {
            "id": 1,
            "name": "Manchester City",
            "short_name": "MCI",
        }
        standing_data = {
            "team": team_data,
            "gameweek": 10,
            "points": 30,
            "played": 10,
            "wins": 10,
            "draws": 0,
            "losses": 0,
            "goals_for": 30,
            "goals_against": 5,
            "goal_difference": 25,
            "position": 1,
        }
        standing = StandingItemSchema(**standing_data)
        assert standing.position == 1
        assert standing.goal_difference == 25
