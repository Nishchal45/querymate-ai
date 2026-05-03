# QueryMate AI

> Natural language to SQL query engine with schema-aware LLM prompting, two-level Redis caching, and 4-layer security architecture.

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://www.python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.6-3178C6?logo=typescript&logoColor=white)](https://www.typescriptlang.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D?logo=redis&logoColor=white)](https://redis.io)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://docs.docker.com/compose/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

---

## Problem

Non-technical users (analysts, PMs) cannot query databases directly — they wait hours or days for engineers to write SQL. Even SQL-proficient developers spend significant time writing JOINs across unfamiliar schemas. Existing NL2SQL tools are either toy demos with no security or expensive enterprise products with vendor lock-in.

## Solution

QueryMate AI converts plain English into validated PostgreSQL queries using **schema-aware LLM prompt engineering**. It introspects your database, generates SQL with GPT-4o-mini, validates against 30+ injection patterns, executes through a 4-layer defense-in-depth pipeline, and caches results so repeated questions return in **under 5ms**.

This architecture pattern is used in production at pharmaceutical companies for chemical inventory and batch planning queries, where R&D teams ask questions like *"how many batches of Drug X can we produce given current ingredient stock?"* — and the system computes the answer by introspecting the chemical database and generating the right aggregation SQL.

## Architecture

```
┌──────────────────┐
│  React Frontend  │
│   (TypeScript)   │
└────────┬─────────┘
         │ POST /api/query
         ▼
┌─────────────────────────────────────────────────────────┐
│              FastAPI Backend (Python)                    │
│  ┌────────────┐   ┌──────────┐   ┌─────────────────┐   │
│  │ Introspector│──▶│   LLM    │──▶│  SQL Validator  │   │
│  │  (4-level   │   │ (GPT-4o- │   │   (30+ regex    │   │
│  │ compression)│   │  mini)   │   │   patterns)     │   │
│  └────────────┘   └──────────┘   └────────┬────────┘   │
│                                            ▼            │
│  ┌──────────────┐   ┌─────────────────────────────┐    │
│  │  Two-Level   │   │      Query Executor         │    │
│  │  Redis Cache │◀──│  (timeout, row limits, RO)  │    │
│  │  L1: NL→SQL  │   └──────────┬──────────────────┘    │
│  │  L2: SQL→Res │              │                        │
│  └──────────────┘              ▼                        │
└────────────────────────────────┼────────────────────────┘
                                 ▼
              ┌──────────────────────────────────┐
              │   PostgreSQL Target DB           │
              │   (read-only role, 10s timeout)  │
              └──────────────────────────────────┘
```

See [`docs/architecture/system-design.md`](./docs/architecture/system-design.md) for full Mermaid diagrams.

## Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Backend | FastAPI + Python 3.11 | Async-native, auto OpenAPI docs, Pydantic validation |
| Frontend | React 18 + TypeScript + Vite | Type safety, fast HMR, modern build tooling |
| LLM | OpenAI GPT-4o-mini | Best SQL accuracy per dollar, deterministic at temp=0 |
| App Database | PostgreSQL 16 | Query history with JSONB, same engine as target |
| Target Database | PostgreSQL 16 | Demo e-commerce DB (read-only role) |
| Cache | Redis 7 | TTL support, async client, two-level caching |
| ORM | SQLAlchemy 2.0 + Alembic | Async ORM, versioned migrations |
| Charts | Recharts | React-native, declarative API |
| CI/CD | GitHub Actions | Lint + typecheck + test + frontend build on every PR |
| Containers | Docker Compose | One-command local dev environment |

## Key Engineering Highlights

### 1. Schema Introspection with Progressive Compression

Reads PostgreSQL system catalogs (`information_schema`, `pg_constraint`, `pg_stat_user_tables`) and applies **4-level progressive compression** to fit any schema within LLM token budgets:

| Level | Includes | Use Case |
|-------|----------|----------|
| 0 | Full schema + sample values + row counts | <8 tables |
| 1 | Drop sample values | Medium schemas |
| 2 | Drop row counts | Large schemas |
| 3 | Tables + columns + types only | Massive schemas (100+ tables) |

### 2. 4-Layer Defense-in-Depth Security

Even if one layer fails, three more protect the database:

| Layer | Component | What it Blocks |
|-------|-----------|---------------|
| 1 | SQL Validator (regex) | 30+ patterns: DML, DDL, DCL, stacked queries, comment injection, UNION, system tables, dangerous functions, encoding attacks |
| 2 | Read-only Connection | psycopg2 `readonly=True` — application-level enforcement |
| 3 | Database Role | `querymate_reader` PostgreSQL role with SELECT-only grants |
| 4 | Statement Timeout | 10s timeout at role level — kills runaway queries |

**46 security tests** in [`tests/unit/test_sql_validator.py`](./tests/unit/test_sql_validator.py) covering every blocked pattern + false-positive prevention.

### 3. Two-Level Caching (360x Speedup)

| Cache | Key | TTL | Skips |
|-------|-----|-----|-------|
| L1 | SHA-256 of normalized question | 1 hour | LLM call (~1.5s, $0.002) |
| L2 | SHA-256 of generated SQL | 5 minutes | Database execution (~100ms) |

| Scenario | Latency |
|----------|---------|
| Cold (no cache) | ~1.8s |
| L1 hit (skip LLM) | ~150ms |
| L1 + L2 hit | <5ms ⚡ |

Question normalization (lowercase, strip punctuation, collapse whitespace) ensures *"How many orders?"* and *"how many orders"* share the same cache entry.

## Getting Started

### Prerequisites

- [Docker & Docker Compose](https://docs.docker.com/get-docker/)
- [Python 3.11+](https://www.python.org/downloads/) (for local backend dev)
- [Node.js 20+](https://nodejs.org/) (for local frontend dev)
- An [OpenAI API key](https://platform.openai.com/api-keys)

### Quick Start

```bash
# Clone and configure
git clone https://github.com/Nishchal45/querymate-ai.git
cd querymate-ai
cp .env.example .env  # add your OPENAI_API_KEY

# Start all services (PostgreSQL x2, Redis)
make up

# Apply migrations
make migrate-up

# Open the app
open http://localhost:3000
```

The demo database is pre-seeded with **~2,000 rows across 8 tables** (e-commerce: customers, products, orders, reviews, etc.).

### Try These Queries

```
How many customers are in California?
What are the top 5 best-selling products?
Show me total revenue by month for 2024
What is the average rating per product category?
Which products are running low on stock?
```

### API Examples

```bash
# Run a query
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"question": "How many customers are in California?"}'

# Get the schema
curl http://localhost:8000/api/schema

# Cache stats
curl http://localhost:8000/api/cache/stats

# Query history
curl "http://localhost:8000/api/history?page=1&page_size=10"
```

Full OpenAPI docs at `http://localhost:8000/docs` (auto-generated by FastAPI).

## Project Structure

```
querymate-ai/
├── backend/
│   ├── api/              REST endpoints (query, history, schema, cache, health)
│   ├── core/             Config, logging, database, redis, target_database
│   ├── models/           SQLAlchemy models (query_history)
│   └── services/         introspector, llm_service, sql_validator,
│                          query_executor, cache_service
├── frontend/
│   └── src/
│       ├── api/          Typed Axios client
│       ├── components/   QueryInput, ResultsTable, ChartView, SchemaExplorer,
│                          SqlDisplay, QueryHistory, Layout
│       ├── hooks/        useQuery, useSchema
│       ├── pages/        QueryPage
│       └── types/        TypeScript interfaces matching backend Pydantic
├── tests/
│   ├── unit/             test_sql_validator (46 tests), test_llm_service,
│                          test_cache_service
│   └── integration/      test_query_flow (with real PostgreSQL)
├── alembic/              Database migrations
├── scripts/              01_schema.sql, 02_seed.sql
├── docs/
│   ├── PRD.md            Product Requirements Document
│   ├── TRD.md            Technical Requirements Document
│   ├── ENGINEERING_GUIDE.md   Development process & decisions
│   └── architecture/     System design Mermaid diagrams
├── .github/workflows/    CI pipeline (lint, typecheck, test, build)
├── docker-compose.yml
├── Makefile              20+ dev commands (make help)
└── requirements.txt
```

## Development Workflow

This project follows industry-standard practices:

1. **Planning** — PRD → TRD → Architecture → GitHub Issues (18 total)
2. **Branching** — `main` ← `develop` ← `feature/*`, `fix/*`, `chore/*`, `ci/*`, `docs/*`
3. **Commits** — [Conventional Commits](https://www.conventionalcommits.org/): `feat(scope):`, `fix(scope):`, `docs:`, `chore:`, `ci:`
4. **Pull Requests** — Feature branch → PR with What/Why/How/Testing → CI checks → squash merge
5. **CI/CD** — GitHub Actions runs lint (ruff) + typecheck (mypy) + tests (pytest) + frontend build on every PR
6. **Releases** — `develop` merged into `main` for production releases

See [`docs/ENGINEERING_GUIDE.md`](./docs/ENGINEERING_GUIDE.md) for the full process.

## Documentation

- 📋 [Product Requirements Document (PRD)](./docs/PRD.md)
- 🔧 [Technical Requirements Document (TRD)](./docs/TRD.md)
- 🏗️ [Architecture Diagrams](./docs/architecture/system-design.md)
- 📖 [Engineering Guide](./docs/ENGINEERING_GUIDE.md)

## License

[MIT](./LICENSE)
