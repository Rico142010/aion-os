# AION OS

Artificial Intelligence Operating Network.

AION OS is a lightweight operating network foundation designed for AI services, automation, orchestration, and modular application workflows.

## Features

- FastAPI backend with health endpoints
- Dashboard served from the frontend directory
- PostgreSQL health checking and Redis status validation
- Docker Compose orchestration for local development
- Environment-based configuration
- Foundation ready for future AI agents, services and workflows

## Tech stack

- Python 3.12
- FastAPI
- PostgreSQL 17
- Redis 8
- Docker Compose

## Quick start

1. Copy the environment file:

   cp .env.example .env

2. Start the services:

   docker compose up --build

3. Open the app:

   http://localhost:8000

4. Check API health:

   http://localhost:8000/api/health

## Services

- API: http://localhost:8000
- PostgreSQL: localhost:5432
- Redis: localhost:6379

## Useful commands

- Stop the stack:

  docker compose down

- Stop and remove volumes:

  docker compose down -v

- View logs:

  docker compose logs -f api

## Project structure

```text
.
├── .env.example
├── .gitignore
├── README.md
├── docker-compose.yml
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── __init__.py
│       ├── api/
│       │   ├── __init__.py
│       │   └── routes/
│       │       ├── __init__.py
│       │       └── health.py
│       ├── core/
│       │   ├── __init__.py
│       │   ├── config.py
│       │   └── database.py
│       └── main.py
├── frontend/
│   ├── app.js
│   ├── index.html
│   └── styles.css
└──
```

## Environment variables

The project reads configuration from `.env` with defaults defined in `.env.example`.

## Current status

This version is a working foundation: the API is up, the frontend loads, and system health checks can validate PostgreSQL and Redis availability.
