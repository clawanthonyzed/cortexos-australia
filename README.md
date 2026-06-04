# CortexOS

**Agentic Operating System for AI Holding Companies**

CortexOS is a production-ready platform for running AI agent workforces at scale. Configure agents, build multi-step workflows, connect to your commerce platforms, and watch tasks execute — all through a clean dashboard with real-time updates.

Built for operators who run multiple AI-driven ventures and need a single command centre that doesn't break.

---

![CortexOS Dashboard](docs/screenshots/dashboard-placeholder.png)

> Screenshots available in [/docs/screenshots/](docs/screenshots/) after first deploy.

---

## Quick Start

```bash
git clone https://github.com/your-org/cortexos.git
cd cortexos
cp .env.example .env      # fill in your API keys
make up                   # start all services
make migrate              # run database migrations
open http://localhost:3000
```

Default credentials: `admin@cortexos.ai` / `admin` — change immediately.

---

## Features

### Agent Management
- Create and configure AI agents with custom system prompts, tool access, and memory settings
- Choose from Anthropic, OpenAI, Google, or OpenRouter as LLM providers
- Built-in agent types: CEO, Research Analyst, Content Writer, Finance Analyst, QC Inspector
- Real-time task monitoring with step-by-step execution logs via WebSocket

### Workflow Automation
- Visual drag-and-drop workflow editor
- Node types: agent, condition, approval gate, tool, transform
- Schedule workflows on cron triggers or fire via webhook
- Human-in-the-loop approval gates with email notifications
- Automatic retry and error handling

### Memory System
- Four-layer memory architecture: Redis (working), PostgreSQL (episodic), pgvector (semantic), Neo4j (graph)
- Agents remember past tasks and carry context forward automatically
- Semantic search across all historical agent output
- Entity relationship graph via Graphiti

### Finance Dashboard
- Connect Etsy, Gumroad, and LemonSqueezy for unified revenue tracking
- Daily automated sync + real-time webhooks
- P&L by venture, by channel, by time period
- Export to CSV

### Observability
- Self-hosted Langfuse for full LLM tracing
- Every prompt, completion, token count, and cost captured
- Prompt versioning and A/B comparison
- Automatic quality scoring integration

### Production Ready
- Traefik reverse proxy with automatic TLS via Let's Encrypt
- Rate limiting and security headers out of the box
- GitHub Actions CI/CD pipeline (test → lint → deploy)
- One-command deployment to any VPS

---

## Architecture

```
Next.js frontend → FastAPI backend → Agent execution engine
                                   ↕
               PostgreSQL (data) + Redis (cache) + Neo4j (graph)
                                   ↕
                    Anthropic / OpenAI / OpenRouter APIs
```

Full architecture documentation with diagrams: [docs/architecture.md](docs/architecture.md)

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14, TypeScript, Tailwind CSS, shadcn/ui |
| Backend | FastAPI, Python 3.11, SQLAlchemy 2.0, Alembic |
| Task Queue | Celery + Redis |
| Primary DB | PostgreSQL 16 + pgvector |
| Graph Memory | Neo4j 5.24 + APOC + Graphiti |
| Cache / Pub-Sub | Redis 7 |
| Observability | Langfuse (self-hosted) |
| Reverse Proxy | Traefik v3 |
| CI/CD | GitHub Actions |

---

## Documentation

| Doc | Description |
|-----|-------------|
| [Getting Started](docs/README.md) | Prerequisites, setup, first run |
| [Architecture](docs/architecture.md) | System design, data flow, memory model |
| [Agents](docs/agents.md) | Creating agents, config reference, patterns |
| [Workflows](docs/workflows.md) | Building pipelines, templates, scheduling |
| [API Reference](docs/api.md) | REST endpoints, WebSocket events |
| [Deployment](docs/deployment.md) | VPS setup, TLS, backups, monitoring |
| [Integrations](docs/integrations.md) | Etsy, Gumroad, GitHub, Langfuse |

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Write tests first (TDD enforced via CI — 80% coverage required)
4. Implement the feature
5. Open a pull request against `main`

CI runs on every PR: tests, type checking, linting, security scan.

**Code style:**
- Backend: ruff (formatting + linting), mypy (types)
- Frontend: ESLint, TypeScript strict mode

---

## License

MIT License — see [LICENSE](LICENSE) for full text.

---

## Self-Hosting

CortexOS is designed to run on a $20/month VPS. See the [deployment guide](docs/deployment.md) for full instructions. Minimum specs: 4 vCPU, 8GB RAM, 80GB SSD.

All data stays on your server. No telemetry. No phone-home.
