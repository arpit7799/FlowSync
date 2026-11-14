# FlowSync — Setup & Installation Instructions

This guide provides step-by-step setup instructions for running the complete FlowSync system on macOS / Linux.

## Prerequisites

- **Python 3.12**
- **Node.js 18+** & **npm**
- **Eclipse SUMO** (Simulation of Urban MObility) with TraCI
- **Docker** and **Docker Compose** (for Mosquitto MQTT & PostgreSQL)

---

## 1. Python Environment Setup

Clone the repository and activate the virtual environment:

```bash
cd /Users/arpit_7799/Documents/Projects/FlowSync

# Create virtual environment if not present
python3.12 -m venv flowsync_env

# Activate
source flowsync_env/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

---

## 2. Infrastructure Services (Docker)

To run Mosquitto (MQTT) and PostgreSQL:

```bash
docker compose -f docker/docker-compose.yml up -d
```

- **MQTT Broker:** `localhost:1883`
- **PostgreSQL Database:** `localhost:5432` (User: `flowsync`, Database: `flowsync`)

*(Note: The system supports automatic SQLite fallback if Docker is not started).*

---

## 3. Database Migrations

Run database migrations via Alembic:

```bash
source flowsync_env/bin/activate
alembic -c backend/alembic.ini upgrade head
```

---

## 4. Backend Startup (FastAPI)

Start the REST API and WebSocket live server:

```bash
source flowsync_env/bin/activate
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

- API Documentation: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health Check: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)
- WebSocket Live Feed: `ws://localhost:8000/ws/live`

---

## 5. Frontend Startup (Next.js)

In a separate terminal:

```bash
cd frontend
npm install
npm run dev
```

- Live Dashboard: [http://localhost:3000](http://localhost:3000)

---

## 6. Running Tests

Run the full automated pytest suite (78 tests):

```bash
source flowsync_env/bin/activate
pytest tests/ -v
```

---

## 7. Running the Full Demonstration

Execute the self-contained 12-step demonstration script:

```bash
source flowsync_env/bin/activate
python scripts/run_demonstration.py
```
