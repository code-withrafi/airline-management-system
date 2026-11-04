# ⚙️ Setup & Deployment Guide

> **Airline Management System — Final Year Project**
> Complete guide to install, configure, run, and deploy the system.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Local Development Setup](#2-local-development-setup)
3. [ML Model Training (One-Time Setup)](#3-ml-model-training-one-time-setup)
4. [Environment Variables Reference](#4-environment-variables-reference)
5. [Verifying the Installation](#5-verifying-the-installation)
6. [Common Issues](#6-common-issues)
7. [Deployment (Docker Compose)](#7-deployment-docker-compose)
8. [Production Checklist](#8-production-checklist)

---

## 1. Prerequisites

| Tool | Version | Purpose |
|---|---|---|
| Python | 3.12+ | Backend + desktop app |
| Node.js | 18+ | React frontend |
| PostgreSQL | 14+ | Database |
| Git | Any | Version control |

**Optional tooling**

- **pgAdmin** or **DBeaver** — Database inspection
- **VS Code** — Editor with Python + ESLint extensions

---

## 2. Local Development Setup

### 2.1 Clone the repository

```bash
git clone <your-repo-url>
cd Airline-Management-System
```

### 2.2 Set up a Python virtual environment

**Windows (PowerShell)**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2.3 Install Python dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If `psycopg` fails on Windows, use the prebuilt wheel:

```bash
python -m pip install "psycopg[binary]==3.2.3"
```

The `requirements.txt` includes both the core stack and the ML dependencies:

```
# Core
fastapi==0.115.0
uvicorn[standard]==0.32.0
pydantic==2.9.2
pydantic-settings==2.5.2
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.12
email-validator==2.2.0
psycopg[binary]==3.2.3
sqlalchemy==2.0.35
reportlab==4.2.2
qrcode[pil]==8.0
python-barcode==0.15.1

# Machine Learning
scikit-learn==1.5.2
xgboost==2.1.1
pandas==2.2.3
numpy==2.1.1
joblib==1.4.2
```

### 2.4 Configure the database

Create a PostgreSQL database:

```sql
CREATE DATABASE airline_management;
```

Copy `.env.example` to `.env` and edit:

```ini
APP_NAME=Airline Management System
APP_ENV=development

DB_HOST=localhost
DB_PORT=5432
DB_NAME=airline_management
DB_USER=postgres
DB_PASSWORD=your_password_here

JWT_SECRET=change_me_to_a_random_48_char_string
```

### 2.5 Initialize the database

```bash
python -c "from app.models.init_database import init_database; init_database()"
```

This creates all tables and seeds initial data (airports, aircraft, routes, users).

### 2.6 Train the ML models (one-time)

See [Section 3](#3-ml-model-training-one-time-setup) for details. Run these six commands **once** after the database is initialized:

```bash
python -m app.ml.no_show.generate_data
python -m app.ml.no_show.train
python -m app.ml.recommender.prepare_data
python -m app.ml.recommender.train
python -m app.ml.fare.generate_data
python -m app.ml.fare.train
```

### 2.7 Start the FastAPI backend

```bash
python -m uvicorn api.main:app --reload --host 127.0.0.1 --port 8000
```

Verify: <http://127.0.0.1:8000/health> → `{"status":"ok"}`

### 2.8 Set up and start the React frontend

Open a new terminal:

```bash
cd frontend
npm install
npm run dev
```

Open <http://localhost:5173>

### 2.9 Launch the desktop app

Open a third terminal:

```bash
python -m app.main
```

Log in with the seeded admin account:

| Role | Email | Password |
|---|---|---|
| Admin | `admin@airline.com` | `admin123` |
| Staff | `staff@airline.com` | `staff123` |
| Passenger | `rafsan@passenger.com` | `test123` |

---

## 3. ML Model Training (One-Time Setup)

The system ships **three trained ML models**. Each is trained offline from a script and saved as a `.pkl` artifact. The `.pkl` files are **not committed to Git** (they're reproducible in seconds), so you must generate them the first time you run the project.

### 3.1 Why train once?

- **Deterministic** — with `random_state=42`, training produces identical results on any machine
- **Fast** — the full pipeline (all three models) runs in under 60 seconds
- **Self-contained** — no external datasets or downloads required
- **Documented** — the training scripts are executable documentation

### 3.2 Train the No-Show Predictor

**Purpose:** predict expected no-shows per flight, power the Overbooking Advisor panel.

```bash
python -m app.ml.no_show.generate_data
python -m app.ml.no_show.train
```

**Expected output:**
```
Generating 30000 synthetic no-show samples...
✓ Wrote 30000 rows to data\no_show_training.csv
  No-show rate: ~19.6%

Training XGBoost model...
  Accuracy: ~0.77
  ROC-AUC:  ~0.81

✓ Saved model to app\ml\models\no_show_v1.pkl
```

**Artifact:** `app/ml/models/no_show_v1.pkl`

### 3.3 Train the Route Recommender

**Purpose:** personalize route suggestions for logged-in passengers; falls back to popular routes for anonymous visitors.

```bash
python -m app.ml.recommender.prepare_data
python -m app.ml.recommender.train
```

**Expected output:**
```
Discovered 12 routes...
✓ Wrote ~6000 interactions to data\route_interactions.csv
  Matrix shape: (2000, 12)

Computing item-item cosine similarity...

✓ Saved recommender to app\ml\models\recommender_v1.pkl
```

**Artifact:** `app/ml/models/recommender_v1.pkl`

### 3.4 Train the Fare Predictor

**Purpose:** dynamically price each flight based on route distance, day, hour, and season.

```bash
python -m app.ml.fare.generate_data
python -m app.ml.fare.train
```

**Expected output:**
```
Generating 30000 synthetic fare samples...
✓ Wrote 30000 rows to data\fare_training.csv

Training XGBoost regressor...
  MAE:   ~0.029
  RMSE:  ~0.038
  R²:    ~0.98

✓ Saved model to app\ml\models\fare_v1.pkl
```

**Artifact:** `app/ml/models/fare_v1.pkl`

### 3.5 Verify the Models

```bash
# Unit test the aircraft range rule
python -m scripts.test_aircraft_range

# Verify no ATR turboprops assigned to long routes
python -m scripts.verify_aircraft_range

# Show fare variation across routes and times
python -m scripts.verify_fares
```

### 3.6 Retraining

You can retrain any model at any time. The API and desktop app **hot-reload** the model on the next request after the `.pkl` file changes (the model is loaded lazily and cached per-process).

To force a reload **without restarting the server**, just restart uvicorn:

```bash
python -m uvicorn api.main:app --reload
```

### 3.7 Model Artifacts Directory

After training, `app/ml/models/` should contain:

```
app/ml/models/
├── .gitkeep
├── no_show_v1.pkl         # ~200 KB
├── recommender_v1.pkl     # ~5 KB
└── fare_v1.pkl            # ~150 KB
```

Total ~400 KB. Safe to regenerate anytime.

---

## 4. Environment Variables Reference

| Variable | Default | Notes |
|---|---|---|
| `APP_NAME` | `Airline Management System` | Display name |
| `APP_ENV` | `development` | `development` / `production` |
| `DB_HOST` | `localhost` | Postgres host |
| `DB_PORT` | `5432` | Postgres port |
| `DB_NAME` | `airline_management` | Database name |
| `DB_USER` | `postgres` | Postgres user |
| `DB_PASSWORD` | — | Postgres password |
| `JWT_SECRET` | (dev default) | Move to environment variable for production |

---

## 5. Verifying the Installation

Run these checks after setup to confirm everything works.

### 5.1 Backend health

```bash
curl http://127.0.0.1:8000/health
```

**Expected:** `{"status":"ok"}`

### 5.2 Database connectivity

```bash
python -c "from app.config.database import SessionLocal; from app.models.user import User; db = SessionLocal(); print(f'Users: {db.query(User).count()}'); db.close()"
```

**Expected:** `Users: <N>` (N > 0)

### 5.3 ML models available

```bash
python -c "from pathlib import Path; [print(f'{m.name}: {\"OK\" if Path(m).exists() else \"MISSING\"}') for m in ['app/ml/models/no_show_v1.pkl', 'app/ml/models/recommender_v1.pkl', 'app/ml/models/fare_v1.pkl']]"
```

**Expected:**
```
no_show_v1.pkl: OK
recommender_v1.pkl: OK
fare_v1.pkl: OK
```

### 5.4 Frontend build

```bash
cd frontend
npm run build
```

**Expected:** a `frontend/dist/` folder with no errors.

### 5.5 End-to-end smoke test

```bash
# 1. Login as admin
$body = '{"email":"admin@airline.com","password":"Admin@12345"}'
$login = Invoke-RestMethod -Uri http://127.0.0.1:8000/api/auth/staff-login -Method Post -Body $body -ContentType "application/json"
$headers = @{ Authorization = "Bearer $($login.access_token)" }

# 2. Get ML recommendations (public)
Invoke-RestMethod -Uri http://127.0.0.1:8000/api/ml/recommendations

# 3. Generate flights for a small range
$genBody = @{ start_date = "2027-01-01"; end_date = "2027-01-03"; overwrite_existing = $false } | ConvertTo-Json
Invoke-RestMethod -Uri http://127.0.0.1:8000/api/schedule/generate -Method Post -Body $genBody -ContentType "application/json" -Headers $headers
```

**Expected:** each returns HTTP 200 with valid JSON.

---

## 6. Common Issues

### ❌ `ModuleNotFoundError: No module named 'psycopg'`

```bash
python -m pip install "psycopg[binary]==3.2.3"
```

### ❌ `ModuleNotFoundError: No module named 'sklearn'` (or `xgboost`, `pandas`)

ML dependencies are missing:

```bash
python -m pip install scikit-learn==1.5.2 xgboost==2.1.1 pandas==2.2.3 numpy==2.1.1 joblib==1.4.2
```

### ❌ `No-show model not found at app/ml/models/no_show_v1.pkl`

The ML models haven't been trained yet. Run the training commands in [Section 3](#3-ml-model-training-one-time-setup).

### ❌ `503 Recommender model not trained yet`

Same cause — run the recommender training commands.

### ❌ `database is locked`

- **If using SQLite:** switch to Postgres, or enable WAL mode.
- **If using Postgres:** check for long-running transactions.

### ❌ `Access denied` on Postgres

Verify `.env` credentials. Test connection:

```bash
psql -U postgres -h localhost -d airline_management -c "SELECT 1;"
```

### ❌ Frontend can't reach backend

- Check uvicorn is running on port 8000
- Check CORS in `api/main.py` allows `http://localhost:5173`
- Check browser DevTools → Network tab for the actual error

### ❌ `psycopg2` build errors on Windows

Install the binary wheel:

```bash
python -m pip install psycopg2-binary
```

### ❌ Vite dev server port clash

If port 5173 is in use, kill the process:

```powershell
Get-Process -Name node | Stop-Process
```

Or change the port in `vite.config.js`.

### ❌ Desktop app shows no seats

Run the backfill script:

```bash
python backfill_seats.py
```

### ❌ ATR aircraft still assigned to long routes

The range rule is enforced only for **newly-generated** flights. Flights created before the rule was added still violate it. Clean up:

```bash
python -m scripts.purge_future_flights
```

Then regenerate via the admin panel or the `/api/schedule/generate` endpoint.

### ❌ Flights have identical fares

The ML fare model isn't trained or is missing:

```bash
python -m app.ml.fare.generate_data
python -m app.ml.fare.train
```

Then delete old flights and regenerate.

---

## 7. Deployment (Docker Compose)

> *(Optional — for FYP demo, local setup is sufficient)*

### 7.1 `Dockerfile.backend`

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Train ML models during image build (fast, deterministic)
RUN python -m app.ml.no_show.generate_data && \
    python -m app.ml.no_show.train && \
    python -m app.ml.recommender.prepare_data && \
    python -m app.ml.recommender.train && \
    python -m app.ml.fare.generate_data && \
    python -m app.ml.fare.train

EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 7.2 `Dockerfile.frontend`

```dockerfile
FROM node:20-alpine AS build
WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

### 7.3 `docker-compose.yml`

```yaml
version: '3.9'
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_DB: airline_management
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - pgdata:/var/lib/postgresql/data
    ports: ["5432:5432"]

  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    environment:
      DB_HOST: db
      DB_PORT: 5432
      DB_NAME: airline_management
      DB_USER: postgres
      DB_PASSWORD: postgres
      JWT_SECRET: change_me_in_production_32_chars_min
    depends_on: [db]
    ports: ["8000:8000"]

  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    depends_on: [backend]
    ports: ["80:80"]

volumes:
  pgdata:
```

### 7.4 Run

```bash
docker-compose up --build
```

**Access:**

- Web app: <http://localhost>
- API docs: <http://localhost:8000/docs>

---

## 8. Production Checklist

Before deploying to production:

- [ ] Move `JWT_SECRET` to a secure environment variable
- [ ] Set `APP_ENV=production`
- [ ] Use HTTPS (reverse proxy)
- [ ] Restrict CORS to the production domain
- [ ] Enable Postgres SSL
- [ ] Set up database backups
- [ ] Configure logging (structured JSON)
- [ ] Add rate limiting to `/api/auth/*`
- [ ] Retrain ML models on **real historical data** (not synthetic)
- [ ] Set up a model monitoring / drift detection process
- [ ] Use a real payment gateway
- [ ] Set up error tracking (Sentry)
- [ ] Add a background job runner for periodic schedule generation