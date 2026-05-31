# Premier League Stats & Performance Tracker

A Python-React-Postgres stack for visualizing and comparing English Premier League player and team performances across the last 10 seasons.

## Directory Structure

- `backend/` - Python FastAPI application, database schemas, and data pipelines.
- `frontend/` - React SPA (Vite + TypeScript + CSS).
- `docker-compose.yml` - Runs the PostgreSQL database container.
- `db_backup.sh` - Backs up the Postgres database to an architecture-independent `.dump` file.
- `db_restore.sh` - Restores the database from the latest backup.
- `db_data/` - Git-ignored local database directory bound to the Postgres container (created on startup).
- `db_dumps/` - Folder containing the portable database backup files.

## Getting Started

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (to run Postgres locally).
- Python 3.10+
- Node.js 18+

### Running the Database

1. Spin up the local database container:
   ```bash
   docker compose up -d
   ```
2. Check logs to confirm it's running:
   ```bash
   docker compose logs -f
   ```

### Running the Backend

The backend is a FastAPI app managed with a Python virtual environment.

1. Create and activate the virtual environment (first time only):
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
2. Activate the virtual environment (subsequent runs):
   ```bash
   source venv/bin/activate
   ```
3. Install dependencies (first time only):
   ```bash
   pip install -r backend/requirements.txt
   ```
4. Start the FastAPI server:
   ```bash
   cd backend && uvicorn app.main:app --reload
   ```
   The API will be available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

### Running the Frontend

The frontend is a React + Vite app.

1. Install dependencies (first time only):
   ```bash
   cd frontend && npm install
   ```
2. Start the dev server:
   ```bash
   cd frontend && npm run dev
   ```
   The app will be available at `http://localhost:5173`.

### Backing Up & Migrating

Because raw database volumes are processor-architecture dependent (e.g. they will break when copying between Intel and Apple Silicon), use the provided scripts:

- **Backup**: Runs a clean `pg_dump` and saves it in `./db_dumps/pl_db_backup_latest.dump`.
  ```bash
  ./db_backup.sh
  ```
- **Restore**: Restores the latest dump back into your local container.
  ```bash
  ./db_restore.sh
  ```
