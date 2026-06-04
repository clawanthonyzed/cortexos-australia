# Getting Started with CortexOS

This guide gets you from zero to a running CortexOS instance in under 10 minutes.

---

## Prerequisites

| Tool | Minimum Version | Check |
|------|----------------|-------|
| Docker | 24.0+ | `docker --version` |
| Docker Compose | v2.20+ | `docker compose version` |
| Node.js | 20 LTS | `node --version` |
| Python | 3.11+ | `python --version` |
| Make | Any | `make --version` |
| Git | 2.x | `git --version` |

**macOS:** Install Docker Desktop. Homebrew handles the rest.  
**Linux (Ubuntu 22.04+):** See [deployment guide](deployment.md) for full Docker install steps.  
**Windows:** WSL2 + Docker Desktop recommended.

---

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/your-org/cortexos.git
cd cortexos
```

### 2. Configure environment

```bash
cp .env.example .env
```

Open `.env` and fill in at minimum:

```env
POSTGRES_PASSWORD=your-strong-password-here
NEO4J_PASSWORD=your-neo4j-password-here
SECRET_KEY=generate-with-openssl-rand-hex-32
ANTHROPIC_API_KEY=sk-ant-...
LANGFUSE_NEXTAUTH_SECRET=generate-with-openssl-rand-hex-32
LANGFUSE_SALT=generate-with-openssl-rand-hex-32
```

Generate secrets quickly:

```bash
openssl rand -hex 32  # run 3 times for SECRET_KEY, LANGFUSE_NEXTAUTH_SECRET, LANGFUSE_SALT
```

### 3. Start all services

```bash
make up
```

This starts: PostgreSQL (with pgvector), Redis, Neo4j, Langfuse, the backend API, Celery workers, and the frontend. First run pulls Docker images — allow 2–3 minutes.

### 4. Run database migrations

```bash
make migrate
```

This applies all Alembic migrations and seeds the default admin account.

### 5. Open CortexOS

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| API Docs (ReDoc) | http://localhost:8000/redoc |
| Langfuse (LLM tracing) | http://localhost:3001 |
| Neo4j Browser | http://localhost:7474 |

**Default admin credentials:**

```
Email:    admin@cortexos.ai
Password: admin
```

Change the password immediately at http://localhost:3000/settings/account.

---

## Common Tasks

### View logs

```bash
make logs            # All services
make logs-backend    # Backend only
make logs-celery     # Celery workers only
```

### Run tests

```bash
make test            # Full suite with coverage
make test-fast       # Fast run (stops on first failure)
```

### Open a shell

```bash
make shell-backend   # bash in the backend container
make shell-db        # psql connected to cortexos DB
```

### Rebuild after code changes

Hot reload is enabled in development — the backend and frontend detect file changes automatically. If you add a dependency, rebuild:

```bash
make build && make up
```

---

## Seeding Sample Data

```bash
make seed
```

Seeds: 3 sample agents (CEO, Research Analyst, Content Writer), 2 workflow templates, and 10 sample tasks so you can explore the UI without building from scratch.

---

## Stopping CortexOS

```bash
make down        # Stop containers, preserve data volumes
make clean       # Stop AND delete all data (destructive)
```

---

## Next Steps

- [Architecture overview](architecture.md) — understand how the pieces fit together
- [Building agents](agents.md) — create your first custom agent
- [Workflows](workflows.md) — automate multi-step processes
- [API reference](api.md) — integrate CortexOS into your own tools
- [Deploy to production](deployment.md) — ship it to a VPS with TLS
