from app.database import SessionLocal
from app.models import Competition, Season

def seed_initial_data():
    db = SessionLocal()
    try:
        print("Seeding competitions...")
        competitions = [
            {"name": "English Premier League", "code": "EPL", "type": "LEAGUE"},
            {"name": "FA Cup", "code": "FAC", "type": "CUP"},
            {"name": "Carabao Cup", "code": "EFLC", "type": "CUP"},
            {"name": "UEFA Champions League", "code": "UCL", "type": "CUP"},
        ]

        for comp_data in competitions:
            existing = db.query(Competition).filter(Competition.code == comp_data["code"]).first()
            if not existing:
                comp = Competition(**comp_data)
                db.add(comp)
                print(f"Added competition: {comp_data['name']}")
            else:
                print(f"Competition {comp_data['name']} already exists.")

        print("\nSeeding seasons (last 10 years)...")
        seasons = [
            {"label": "2016-2017", "season_code": "1617"},
            {"label": "2017-2018", "season_code": "1718"},
            {"label": "2018-2019", "season_code": "1819"},
            {"label": "2019-2020", "season_code": "1920"},
            {"label": "2020-2021", "season_code": "2021"},  # note: football-data.co.uk uses '2021' for 20/21
            {"label": "2021-2022", "season_code": "2122"},
            {"label": "2022-2023", "season_code": "2223"},
            {"label": "2023-2024", "season_code": "2324"},
            {"label": "2024-2025", "season_code": "2425"},
            {"label": "2025-2026", "season_code": "2526"},
        ]

        for season_data in seasons:
            existing = db.query(Season).filter(Season.season_code == season_data["season_code"]).first()
            if not existing:
                season = Season(**season_data)
                db.add(season)
                print(f"Added season: {season_data['label']}")
            else:
                print(f"Season {season_data['label']} already exists.")

        db.commit()
        print("\nSeeding completed successfully!")
    except Exception as e:
        db.rollback()
        print(f"Error during seeding: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed_initial_data()
