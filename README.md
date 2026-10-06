# AION OS

Artificial Intelligence Operating Network.

AION OS is a lightweight project foundation designed to run a backend API and a simple web interface, with PostgreSQL and Redis pre-integrated for future AI, automation and orchestration features.

## Features

- FastAPI backend with health endpoints
- Simple web dashboard served by FastAPI
- PostgreSQL database ready for future models and storage
- Redis support ready for caching and queues
- Docker Compose orchestration for local development
- Environment-based configuration

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

3. Open the application:

   http://localhost:8000

4. API health check:

   http://localhost:8000/api/health

## Services

- API: http://localhost:8000
- PostgreSQL: localhost:5432
- Redis: localhost:6379

## Useful commands

- Stop services:

  docker compose down

- Stop and remove volumes:

  docker compose down -v

- View logs:

  docker compose logs -f api

## Structure

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
│       ├── main.py
│       ├── api/
│       │   ├── __init__.py
│       │   └── routes/
│       │       ├── __init__.py
│       │       └── health.py
│       └── core/
│           ├── __init__.py
│           └── config.py
├── frontend/
│   ├── app.js
│   ├── index.html
│   └── styles.css
└──
```

## Environment variables

The project reads configuration from `.env` with defaults defined in `.env.example`.

## Notes

This is the foundation for an operating network and AI orchestration platform. The current version provides a working baseline that is ready for new modules, APIs, automation flows, and more advanced features.
