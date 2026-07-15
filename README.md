# AION OS

Artificial Intelligence Operating Network

Version: 0.0.1

Status:
🚧 Under Development

Founder:
Eddy Antonio Peña Lebrón
.gitignore
LICENSE
.env.example
APP_NAME=AION OS

APP_ENV=development

POSTGRES_DB=aion

POSTGRES_USER=aion

POSTGRES_PASSWORD=changeme

REDIS_HOST=redis

REDIS_PORT=6379

JWT_SECRET=CHANGE_ME

OPENAI_API_KEY=
docker-compose.yml
docs/
architecture.md
coding-standards.md
api.md
database.md
deployment.md
security.md
roadmap.md
docker compose up
docker/
apps/api/
apps/studio/
packages/database/
packages/kernel/
AION

apps/

packages/

services/

configs/

docs/

scripts/
configs/
requirements.txt
uv
Browser

↓

Gateway

↓

FastAPI

↓

Kernel

↓

Services

↓

Database
Sprint

↓

Planning

↓

Development

↓

Testing

↓

Review

↓

Release
50 archivos
aion-os/
│
├── docker-compose.yml
version: "3.9"

name: aion

services:

  postgres:
    image: postgres:17
    container_name: aion-postgres

    restart: unless-stopped

    environment:
      POSTGRES_DB: aion
      POSTGRES_USER: aion
      POSTGRES_PASSWORD: aion

    ports:
      - "5432:5432"

    volumes:
      - postgres_data:/var/lib/postgresql/data

    healthcheck:
      test: ["CMD-SHELL","pg_isready -U aion"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:8

    container_name: aion-redis

    restart: unless-stopped

    ports:
      - "6379:6379"

    volumes:
      - redis_data:/data

volumes:

  postgres_data:

  redis_data:
APP_NAME=AION OS

APP_ENV=development

POSTGRES_DB=aion

POSTGRES_USER=aion

POSTGRES_PASSWORD=aion

POSTGRES_HOST=postgres

POSTGRES_PORT=5432

REDIS_HOST=redis

REDIS_PORT=6379

JWT_SECRET=CHANGE_ME

OPENAI_API_KEY=
# AION OS

Artificial Intelligence Operating Network

Version 0.0.1-alpha

Status

🚧 Development

## Stack

- FastAPI
- Next.js
- PostgreSQL
- Redis
- Docker
- docker compose up -d
- docker ps
- 
