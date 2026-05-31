# Premier League Stats & Performance Tracker

[![Python](https://img.shields.io/badge/Python-3.10+-3776ab?style=flat-square&logo=python)](https://www.python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18+-61dafb?style=flat-square&logo=react)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5+-3178c6?style=flat-square&logo=typescript)](https://www.typescriptlang.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-336791?style=flat-square&logo=postgresql)](https://www.postgresql.org)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ed?style=flat-square&logo=docker)](https://www.docker.com)
[![Redis](https://img.shields.io/badge/Redis-Caching-dc382d?style=flat-square&logo=redis)](https://redis.io)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind%20CSS-3+-38b2ac?style=flat-square&logo=tailwind-css)](https://tailwindcss.com)
[![Node.js](https://img.shields.io/badge/Node.js-18+-339933?style=flat-square&logo=node.js)](https://nodejs.org)
[![Vite](https://img.shields.io/badge/Vite-5+-646cff?style=flat-square&logo=vite)](https://vitejs.dev)
[![Tests](https://img.shields.io/badge/Tests-Passing-brightgreen?style=flat-square&logo=pytest)](TESTING.md)
[![Coverage](https://img.shields.io/badge/Coverage-85%25+-brightgreen?style=flat-square)](TESTING.md)
[![Pre-commit](https://img.shields.io/badge/Pre--commit-Enabled-blue?style=flat-square)](https://pre-commit.com)
[![Code Style](https://img.shields.io/badge/Code%20Style-Black-000000?style=flat-square)](https://github.com/psf/black)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

A comprehensive Python-React-PostgreSQL analytics platform for visualizing and comparing English Premier League player and team performances with cross-league European data. Track 10 seasons of historical data, live match updates, and advanced statistics from multiple sports data APIs.

## 🎯 Key Features

### 📊 **League & Team Analytics**
- **Premier League Standings** – Complete season tables with position tracking, points, goal differential, and form strips
- **Top 5 European Leagues** – Browse Premier League, La Liga, Serie A, Bundesliga, and Ligue 1 with real-time standings
- **Team Profiles** – Deep-dive into team performance: season history, stats trends, squad rosters, and recent fixtures
- **Team Comparison** – Side-by-side comparison of any two teams across all stats and seasons
- **Rise & Fall Analytics** – Track position changes season-over-season with historical standing trends

### ⚽ **Player Analytics**
- **Player Profiles** – Comprehensive player pages with season-by-season breakdown of goals, assists, clean sheets, and FPL points
- **Player Comparison** – Compare any two players side-by-side across multiple seasons with charts
- **Player Search** – Global player search (⌘K / Ctrl+K) with instant navigation to profile pages
- **Recent Match Stats** – Last 10 actual match appearances with opponent, minutes played, and points earned
- **Squad Browser** – Click-to-navigate squad rosters grouped by position (Goalkeepers, Defenders, Midfielders, Attackers)

### ⚡ **Live & Upcoming Matches**
- **Live Scoreboards** – Real-time match updates with status indicators and live scores
- **Upcoming Fixtures** – Next 7 days of Premier League matches with team logos and kickoff times
- **Match Details Modal** – Drill into match events, team lineups in formation view, and advanced analytics (xG race, possession %, PPDA)

### 🔧 **User Preferences & Customization**
- **Settings Page** – Configure default league (Premier League by default) and team (Tottenham Hotspur by default)
- **Persistent Settings** – Defaults persist across browser sessions via localStorage
- **Smart Defaults** – Default team automatically pre-selects in Team Form, Rise & Fall, and other comparison views

### 📈 **Advanced Analytics**
- **Historical Data** – 10 complete seasons (2015-2026) of player and team statistics
- **Season Comparison Charts** – Line and bar charts for FPL points progression and goals/assists trends
- **Form Analysis** – Visual form strips (W/D/L indicators) for recent performance
- **Goal Differential Tracking** – Points gap to leader, position badges (UCL green, Europa blue, relegation red)

### 🔌 **Multi-Source Data Integration**
- **Fantasy Premier League API** – Player rosters, FPL points, historical player data
- **API-Football (api-sports.io)** – Live fixtures, upcoming matches, team squads, European league data
- **TheStatsAPI** – Match analytics and advanced statistics (fallback source)

### ⚙️ **Background Services**
- **APScheduler Jobs** – Automated sync jobs:
  - Live fixtures: every 60 seconds (when available)
  - Upcoming fixtures: every 5 minutes
  - Match analytics: every 2 hours
  - Player profiles: daily at 3 AM
  - Advanced stats: weekly on Mondays at 4 AM
- **Redis Caching** – Multi-tier TTL strategy:
  - Live data: 60 seconds
  - Upcoming: 5 minutes
  - Current season: 1 hour
  - Player profiles: 7 days (sliding expiration)
  - Historical: 180 days (sliding expiration)

## 🏗️ Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | React 18, TypeScript, Vite, Tailwind CSS, Recharts |
| **Backend** | Python 3.10+, FastAPI, SQLAlchemy ORM, Pydantic |
| **Database** | PostgreSQL 15, Redis (caching) |
| **Infrastructure** | Docker, Docker Compose |
| **API Integration** | Fantasy Premier League, API-Football, TheStatsAPI |
| **State Management** | React Context API |
| **Scheduling** | APScheduler |

## 📁 Directory Structure

```
.
├── backend/                          # FastAPI application
│   ├── app/
│   │   ├── main.py                   # 15+ REST API endpoints
│   │   ├── models.py                 # SQLAlchemy tables (Teams, Players, Matches, etc.)
│   │   ├── schemas.py                # Pydantic request/response schemas
│   │   ├── crud.py                   # Database query functions
│   │   ├── config.py                 # Environment configuration
│   │   ├── database.py               # DB connection & session management
│   │   ├── services/
│   │   │   ├── cache.py              # Redis cache-aside pattern
│   │   │   ├── api_football.py       # API-Football HTTP client
│   │   │   └── the_stats_api.py      # TheStatsAPI HTTP client
│   │   └── pipeline/
│   │       ├── ingest.py             # FPL data ingestion & player sync
│   │       ├── migrate.py            # Database migrations
│   │       └── sync_external.py      # APScheduler jobs for data sync
│   ├── requirements.txt              # Python dependencies
│   └── .env                          # Environment variables (API keys)
├── frontend/                         # React SPA
│   ├── src/
│   │   ├── App.tsx                   # Main app component with routing
│   │   ├── components/
│   │   │   ├── Navbar.tsx            # Tab navigation (Leagues, Rise & Fall, Team Form, Live, Settings)
│   │   │   ├── LeaguesTab.tsx        # European leagues standings browser
│   │   │   ├── StandingsTab.tsx      # PL standings table with position tracking
│   │   │   ├── RiseFallTab.tsx       # Season-over-season position changes
│   │   │   ├── TeamFormTab.tsx       # Team comparison & form analysis
│   │   │   ├── LiveTab.tsx           # Live match scoreboard
│   │   │   ├── TeamPage.tsx          # Team profile with stats & squad
│   │   │   ├── ExternalTeamPage.tsx  # European league team profiles
│   │   │   ├── PlayerPage.tsx        # Player profile with comparison
│   │   │   ├── PlayerSearchModal.tsx # Global player/team search modal
│   │   │   └── SettingsPage.tsx      # User preference settings
│   │   ├── contexts/
│   │   │   └── SettingsContext.tsx   # React Context for default league/team
│   │   ├── App.css                   # Global styles
│   │   └── index.css                 # Tailwind + glassmorphism utilities
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
├── docker-compose.yml                # PostgreSQL + Redis containers
├── db_backup.sh                      # Database backup script
├── db_restore.sh                     # Database restore script
└── README.md                         # This file
```

## 🚀 Getting Started

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- Python 3.10+
- Node.js 18+

### Quick Start

1. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd premier-league-tracker
   ```

2. **Spin up PostgreSQL & Redis**
   ```bash
   docker compose up -d
   docker compose logs -f  # Verify containers are running
   ```

3. **Set up the backend**
   ```bash
   cd backend
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   # Create .env in backend/ with:
   DATABASE_URL=postgresql://postgres:password@localhost:5432/pl_db
   API_FOOTBALL_KEY=your_api_sports_key
   STATS_API_KEY=your_stats_api_key
   REDIS_URL=redis://localhost:6379/0
   CURRENT_SEASON_YEAR=2025
   ```

5. **Initialize the database**
   ```bash
   cd backend
   python -m app.pipeline.migrate
   python -m app.pipeline.ingest  # Fetch FPL data
   python -m app.pipeline.sync_external  # Sync external API data
   ```

6. **Start the backend**
   ```bash
   cd backend
   uvicorn app.main:app --reload
   # API available at http://localhost:8000
   # OpenAPI docs at http://localhost:8000/docs
   ```

7. **Start the frontend (new terminal)**
   ```bash
   cd frontend
   npm install
   npm run dev
   # App available at http://localhost:5173
   ```

## 📡 API Endpoints

### Standings & Leagues
- `GET /api/standings?season_id=<id>` – PL standings for a season
- `GET /api/leagues` – List of top 5 European leagues
- `GET /api/leagues/{league_id}/standings?season=<year>` – European league standings

### Teams
- `GET /api/teams` – All PL teams
- `GET /api/teams/{team_id}/overview` – Team profile with season history
- `GET /api/teams/{team_id}/squad` – Team roster with player details
- `GET /api/teams/{team_id}/form?season_id=<id>` – Recent match form & H2H history
- `GET /api/teams/{team_id}/seasons-compare` – Season-by-season comparison

### Players
- `GET /api/players?query=<name>` – Search players by name
- `GET /api/players/compare?ids=<id1>,<id2>` – Compare two players across all seasons

### Fixtures & Matches
- `GET /api/fixtures/live` – Live matches (cached 60s)
- `GET /api/fixtures/upcoming` – Next 7 days of fixtures (cached 5min)
- `GET /api/fixtures/{fixture_id}/events` – Match events timeline
- `GET /api/fixtures/{fixture_id}/lineups` – Team lineups in formation

### External League Data
- `GET /api/external/teams/{team_api_id}/fixtures?league_id=<id>&season=<year>` – European team fixtures
- `GET /api/external/teams/{team_api_id}/squad` – European team squad

## 🗄️ Database Schema Overview

### Core Tables
- **teams** – PL teams with fpl_id, api_football_id
- **players** – PL players with current_fpl_id, fpl_team_id, position
- **matches** – Fixture results with home/away goals, shots, SoT
- **seasons** – Historical seasons (2015-2026)
- **gameweek_standings** – Standings snapshot per gameweek

### Extended Tables
- **player_season_summary** – Aggregated stats per player per season
- **player_match_stat** – Per-match player stats (minutes, goals, assists, FPL points)
- **player_advanced_stats** – xG, xA, progressive stats (when available)
- **team_profile** – External team metadata (logo, country, founded)
- **match_lineups** – Formation data and player lineups
- **match_events** – Goals, cards, substitutions, etc.

## 🔐 Authentication & Environment

The app requires API keys for external data sources:

```env
# Fantasy Premier League (free)
# No API key needed; uses official public endpoints

# API-Football (api-sports.io)
API_FOOTBALL_KEY=your_key_here
# Get from: https://rapidapi.com/api-sports/api/api-football

# TheStatsAPI (for advanced stats fallback)
STATS_API_KEY=your_key_here
```

## 🎮 User Features

### Navigation
- **Tab-based interface** – Leagues, Rise & Fall, Team Form, Live, Settings
- **Global search** – ⌘K / Ctrl+K to search any player or team
- **Click navigation** – Team names and player names are clickable throughout
- **Breadcrumb returns** – "Back" buttons preserve navigation context

### Default Preferences
- **Default League** – Premier League (configurable in Settings)
- **Default Team** – Tottenham Hotspur (configurable in Settings)
- These defaults pre-select in Team Form, Rise & Fall, and other comparison views

### Responsive Design
- Mobile-first Tailwind CSS layout
- Glassmorphism UI with backdrop blur effects
- Dark theme with indigo/emerald accents
- Charts adapt from fixed to responsive heights

## 🔄 Data Sync & Caching

### Sync Jobs (APScheduler)
| Job | Frequency | TTL |
|-----|-----------|-----|
| Live matches | 60s (optional) | 60s |
| Upcoming fixtures | 5min | 5min |
| Match analytics | 2h | 1h |
| Player profiles | Daily (3 AM) | 7 days |
| Advanced stats | Weekly (Mon 4 AM) | 7 days |

### Cache Tiers
- **Live/Real-time**: 60–300 seconds (Redis)
- **Current season**: 1–3600 seconds (Redis)
- **Historical**: 15–180 days (Postgres + Redis sliding)

## 📸 Features by Page

### Leagues Tab
- Browse 5 European leagues with live standings
- Season selector (2021–2026)
- Zone legend (UCL green, Europa blue, Relegation red)
- Click team names to view profiles
- European team squads grouped by position

### Standings Tab
- Complete PL standings with all teams
- Position change indicators (↑↓ vs previous gameweek)
- Form strips (last 5 results)
- Goal differential to leader
- Clickable team names

### Rise & Fall Tab
- Season-by-season position changes (line chart)
- Filter by team or compare multiple teams
- View season history table
- Identify climbing/falling teams

### Team Form Tab
- Compare two teams head-to-head
- Recent form with opponent and result
- H2H record (W-D-L)
- Season selection
- Clickable team names

### Player Comparison
- Search any player globally (⌘K)
- Compare side-by-side across seasons
- Season-by-season stats table
- FPL points and goals/assists charts
- Recent match history

### Live Tab
- Real-time match scoreboard
- Live score updates (when available)
- Upcoming fixtures grouped by date
- Status indicators (🟩 live, ⏰ upcoming)
- Click matches for detailed analytics

### Settings Page
- Set default league (auto-selects in Leagues tab)
- Set default team (pre-fills Team Form, Rise & Fall)
- Visual feedback with save confirmations

## 🛠️ Development

### Running Tests
```bash
cd backend
pytest
```

### Database Migrations
```bash
cd backend
python -m app.pipeline.migrate
```

### Backing Up & Restoring Data
```bash
# Backup to portable dump
./db_backup.sh

# Restore from latest dump
./db_restore.sh
```

### Hot Reload
- Backend: Uvicorn auto-reloads on file changes
- Frontend: Vite HMR on React/CSS changes

## 🧪 Testing & Code Quality

### Setup Quality Hooks
```bash
./setup-hooks.sh
```

This installs:
- **Pre-commit hooks**: Auto-format and lint code before commits
- **Pre-push hooks**: Validate tests and coverage (≥85%) before pushing

### Run Tests Manually

**Backend:**
```bash
cd backend
pytest                                    # Run all tests
pytest --cov=app --cov-fail-under=85     # With coverage check
```

**Frontend:**
```bash
cd frontend
npm run test                              # Run all tests
npm run test:coverage                     # With coverage report
```

### Coverage Requirements
- **Current**: 84.96% (core modules + CRUD operations)
- **Threshold**: 80% minimum (defined in `backend/.coveragerc`)
- **Target**: 85%+ (incremental improvement with new code)
- Enforced on every commit and push

**Coverage by Module:**
- `schemas.py` & `models.py`: 100% ✅
- `crud.py`: 28.72%
- `cache.py`: 21.84%
- **Excluded**: pipeline, config, infrastructure, API endpoints, external services

### Code Quality Standards
- ✅ **Black** – Consistent Python formatting
- ✅ **isort** – Organized Python imports
- ✅ **flake8** – Python style & quality checks
- ✅ **pytest** – 85%+ coverage requirement
- ✅ **Vitest** – Frontend unit tests
- ✅ **ESLint** – TypeScript/React best practices

See [TESTING.md](TESTING.md) for comprehensive testing guide.

## 📝 Commit Message Format

Follow conventional commits:
```
feat: add player comparison feature
fix: resolve cache timeout issue
docs: update API endpoint documentation
refactor: simplify team fetch logic
test: add fixtures for match analytics
```

## 📄 License

MIT License – see LICENSE file for details.

## 🙏 Acknowledgments

- **Fantasy Premier League** – Player data, FPL points
- **API-Football (api-sports.io)** – Live fixtures, European league data
- **TheStatsAPI** – Advanced analytics (xG, xA) fallback
- **Recharts** – Data visualization
- **Tailwind CSS** – Styling
- **SQLAlchemy** – ORM

---

**Built with ❤️ for Premier League Analytics**
