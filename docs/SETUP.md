# Setup & Deployment Guide

> **Airline Management System**
> Complete guide to install, configure, and run the system locally or deploy it.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Local Development Setup](#2-local-development-setup)
3. [Environment Variables Reference](#3-environment-variables-reference)
4. [Common Issues](#4-common-issues)
5. [Deployment (Docker Compose)](#5-deployment-docker-compose)
6. [Production Checklist](#6-production-checklist)

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
```

### 2.5 Initialize the database

```bash
python -c "from app.models.init_database import init_database; init_database()"
```

This creates all tables and seeds initial data (airports, aircraft, routes, users).

### 2.6 Start the FastAPI backend

```bash
python -m uvicorn api.main:app --reload --host 127.0.0.1 --port 8000
```

Verify: <http://127.0.0.1:8000/health> → `{"status":"ok"}`

### 2.7 Set up and start the React frontend

Open a new terminal:

```bash
cd frontend
npm install
npm run dev
```

Open <http://localhost:5173>

### 2.8 Launch the desktop app

Open a third terminal:

```bash
python -m app.main
```

Log in with `admin@airline.com` / `admin123`.

---

## 3. Environment Variables Reference

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

## 4. Common Issues

### ❌ `ModuleNotFoundError: No module named 'psycopg'`

```bash
python -m pip install "psycopg[binary]==3.2.3"
```

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

---

## 5. Deployment (Docker Compose)

> *(Optional — for FYP demo, local setup is sufficient)*

### 5.1 `Dockerfile.backend`

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 5.2 `Dockerfile.frontend`

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

### 5.3 `docker-compose.yml`

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

### 5.4 Run

```bash
docker-compose up --build
```

**Access:**

- Web app: <http://localhost>
- API docs: <http://localhost:8000/docs>

---

## 6. Production Checklist

Before deploying to production:

- [ ] Move `JWT_SECRET` to an environment variable
- [ ] Set `APP_ENV=production`
- [ ] Use HTTPS (reverse proxy)
- [ ] Restrict CORS to the production domain
- [ ] Enable Postgres SSL
- [ ] Set up database backups
- [ ] Configure logging (structured JSON)
- [ ] Add rate limiting to `/api/auth/*`
- [ ] Use a real payment gateway
- [ ] Set up error tracking (Sentry)