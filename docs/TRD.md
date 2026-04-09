# QueryMate AI — Technical Requirements Document (TRD)

**Version:** 1.0
**Author:** Nishchal
**Date:** 2026-03-21
**Status:** Approved

---

## 1. System Architecture

QueryMate AI follows a layered architecture with clear separation between the API layer, service layer, and data layer. The system uses two PostgreSQL databases (app metadata + target data), Redis for multi-level caching, and OpenAI for SQL generation.

### Service Topology

| Service | Technology | Port | Purpose |
|---------|-----------|------|---------|
| Backend API | FastAPI (Python 3.11) | 8000 | REST API, service orchestration |
| Frontend | React + TypeScript (Vite) | 3000 | Query interface, results display |
| App Database | PostgreSQL 16 | 5432 | Query history, app metadata |
| Target Database | PostgreSQL 16 | 5433 | Demo e-commerce data (user queries this) |
| Cache | Redis 7 | 6379 | Two-level query caching, rate limiting |
| LLM | OpenAI API (external) | — | SQL generation from natural language |

## 2. Technology Decisions

| Decision | Choice | Alternatives Considered | Rationale |
|----------|--------|------------------------|-----------|
| Backend framework | FastAPI | Flask, Django, Express | Async-native, auto OpenAPI/Swagger docs, Pydantic validation, highest performance among Python frameworks |
| Frontend framework | React + TypeScript | Next.js, Vue, Svelte | SPA sufficient (no SSR needed), largest ecosystem, TypeScript for type safety, Vite for fast builds |
| LLM provider | OpenAI GPT-4o-mini | Claude, Llama, Mistral | Best SQL generation accuracy per dollar, reliable function calling, well-documented API |
| App database | PostgreSQL 16 | SQLite, MySQL | JSONB support for flexible query history, same engine as target DB reduces cognitive load |
| ORM | SQLAlchemy 2.0 (async) | Tortoise ORM, raw SQL | Industry standard, async support, Alembic for migrations, mapped_column modern syntax |
| Cache | Redis 7 | Memcached, in-memory dict | TTL support, persistent across restarts, two data structures needed (string + hash), async client available |
| Containerization | Docker Compose | Kubernetes, Podman | Appropriate for local dev, single-command startup, no orchestration overhead |
| CI/CD | GitHub Actions | CircleCI, Jenkins | Free for public repos, native GitHub integration, service containers for test DBs |
| CSS framework | Tailwind CSS | CSS Modules, styled-components | Utility-first, no context switching, small production bundle with purge |
| Chart library | Recharts | Chart.js, D3, Nivo | React-native, declarative API, lightweight, good defaults for common chart types |

## 3. Core Services Specification

### 3.1 Schema Introspector

**Purpose:** Reads the target database schema and compresses it to fit LLM token budgets.

**Data sources:**
- `information_schema.tables` — Table names
- `information_schema.columns` — Column names, data types, nullable, defaults
- `pg_constraint` + `information_schema.key_column_usage` — Primary keys, foreign keys
- `pg_stat_user_tables` — Approximate row counts
- `SELECT DISTINCT column LIMIT 5` — Sample values per column

**Progressive compression algorithm:**

| Level | Included | Estimated Tokens (8-table schema) |
|-------|----------|-----------------------------------|
| 0 (Full) | Tables, columns, types, PKs, FKs, row counts, sample values | ~2,500 |
| 1 | Tables, columns, types, PKs, FKs, row counts | ~1,800 |
| 2 | Tables, columns, types, PKs, FKs | ~1,200 |
| 3 (Minimal) | Tables, columns, types only | ~600 |

The introspector starts at Level 0. If the token estimate exceeds the budget (default: 3,000), it drops to the next level until it fits.

### 3.2 LLM Service

**Purpose:** Constructs an optimized prompt from schema + user question and extracts SQL from the LLM response.

**Prompt structure:**
```
SYSTEM: You are a PostgreSQL SQL expert...
  - Rules (SELECT only, proper JOINs, LIMIT, PostgreSQL syntax)
  - Schema (from introspector, compressed to fit budget)
  - Few-shot examples (3 e-commerce Q&A pairs)

USER: {natural_language_question}
```

**Response processing:**
1. Extract SQL from response (strip markdown code blocks if present)
2. Normalize whitespace
3. Ensure single statement (no semicolons)
4. Return clean SQL string

**Model configuration:**
- Model: `gpt-4o-mini` (configurable via env)
- Temperature: 0 (deterministic SQL generation)
- Max tokens: 500 (SQL queries shouldn't be longer)

### 3.3 SQL Validator

**Purpose:** Security layer that blocks dangerous SQL patterns before execution. Uses regex-based pattern matching for broad coverage.

**Validation pipeline (fail-fast, ordered by severity):**

| Check | Pattern | Example Blocked |
|-------|---------|----------------|
| Statement type | Must start with `SELECT` | `DROP TABLE users` |
| DML keywords | `INSERT\|UPDATE\|DELETE\|MERGE` | `DELETE FROM orders` |
| DDL keywords | `DROP\|ALTER\|CREATE\|TRUNCATE` | `ALTER TABLE users ADD...` |
| DCL keywords | `GRANT\|REVOKE` | `GRANT ALL ON...` |
| Stacked queries | Semicolons (`;`) | `SELECT 1; DROP TABLE` |
| Comment injection | `--`, `/*`, `*/` | `SELECT 1 -- DROP TABLE` |
| UNION injection | `UNION\s+(ALL\s+)?SELECT` | `UNION SELECT password FROM...` |
| System tables | `pg_catalog\|information_schema\|pg_stat` | `SELECT * FROM pg_shadow` |
| Dangerous functions | `pg_sleep\|pg_read_file\|lo_import\|dblink` | `SELECT pg_sleep(999)` |
| File operations | `INTO\s+OUTFILE\|INTO\s+DUMPFILE\|COPY` | `COPY users TO '/tmp/data'` |
| Role escalation | `SET\s+ROLE\|SET\s+SESSION` | `SET ROLE superuser` |
| Encoding attacks | `0x[0-9a-f]\|CHR\(` | `SELECT CHR(68)\|\|CHR(82)\|\|CHR(79)\|\|CHR(80)` |
| Extension loading | `LOAD\|CREATE\s+EXTENSION` | `CREATE EXTENSION dblink` |

**False positive handling:**
- Column names like `updated_at` contain "UPDATE" but are safe inside identifiers
- The validator checks for blocked keywords as standalone tokens, not substrings
- Uses word boundary matching (`\b`) where appropriate

**Design decision: Regex vs SQL Parser**
A regex approach is intentionally chosen over AST parsing (e.g., sqlparse). Reason: a SQL parser can be tricked by malformed SQL that PostgreSQL still executes. Regex catches a broader range of obfuscation attempts. The defense-in-depth model means this is just one of four layers.

### 3.4 Query Executor

**Purpose:** Executes validated SQL against the target database with safety limits.

**Safety mechanisms:**
- `statement_timeout`: Cancels queries exceeding the configured timeout (default 10s)
- `max_result_rows`: Fetches at most N rows (default 1,000) to prevent memory exhaustion
- Read-only connection: Uses the `querymate_reader` role with SELECT-only privileges
- Error mapping: PostgreSQL error codes mapped to user-friendly messages

**Result structure:**
```python
{
  "columns": ["product_name", "total_sold"],
  "rows": [["Widget A", 150], ["Widget B", 120]],
  "row_count": 2,
  "execution_time_ms": 45.2,
  "truncated": false
}
```

### 3.5 Cache Service

**Purpose:** Two-level caching to minimize redundant LLM calls and database queries.

**Level 1 — Natural Language to SQL:**
- Key: `querymate:nl:{sha256(normalize(question))}`
- Value: Generated SQL string
- TTL: 3,600 seconds (1 hour)
- Purpose: Same question asked twice → skip LLM entirely
- Normalization: lowercase, strip whitespace, remove trailing punctuation

**Level 2 — SQL to Results:**
- Key: `querymate:sql:{sha256(sql)}`
- Value: JSON-serialized query result
- TTL: 300 seconds (5 minutes)
- Purpose: Different questions that produce the same SQL → skip DB execution
- Shorter TTL because underlying data changes more frequently than query intent

**Cache decision flow:**
```
User asks question
  → Normalize question
  → Check L1 cache
    → HIT: Use cached SQL, skip LLM
    → MISS: Call LLM, cache SQL in L1
  → Check L2 cache (with the SQL)
    → HIT: Return cached results, skip DB
    → MISS: Execute query, cache results in L2
```

**Performance impact:**
- Cold query (no cache): ~1.8s (LLM: ~1.5s + DB: ~0.1s + overhead: ~0.2s)
- L1 hit (skip LLM): ~0.15s (DB: ~0.1s + overhead: ~0.05s)
- L1 + L2 hit (skip both): ~0.005s (<5ms, Redis only)

## 4. Security Architecture — Defense in Depth

Four independent layers. Even if one fails, the others protect the database.

| Layer | Component | Protection |
|-------|-----------|------------|
| 1 | SQL Validator | Regex pattern matching blocks 20+ attack vectors before SQL reaches the DB |
| 2 | Read-only connection | Application connects via `psycopg2` with a read-only PostgreSQL user |
| 3 | Database role privileges | `querymate_reader` role has only `SELECT` grants — `INSERT`/`UPDATE`/`DELETE` fail at DB level |
| 4 | Statement timeout | `statement_timeout = 10s` at role level — runaway queries are automatically cancelled |

**Why four layers?**
- Layer 1 catches known attack patterns but could miss novel obfuscation
- Layer 2 prevents damage even if Layer 1 fails (application-level)
- Layer 3 prevents damage even if Layer 2 is bypassed (database-level)
- Layer 4 prevents resource exhaustion regardless of query content

## 5. Database Schemas

### App Database (querymate_app)

```sql
CREATE TABLE query_history (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    natural_language TEXT NOT NULL,
    generated_sql   TEXT NOT NULL,
    execution_time_ms FLOAT,
    row_count       INTEGER,
    was_cached      BOOLEAN DEFAULT FALSE,
    cache_level     VARCHAR(2),    -- 'L1' or 'L2'
    error           TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_query_history_created_at ON query_history(created_at DESC);
CREATE INDEX idx_query_history_nl_hash ON query_history(md5(natural_language));
```

### Target Database (ecommerce_demo)

| Table | Columns | ~Rows | Purpose |
|-------|---------|-------|---------|
| customers | id, name, email, city, state, created_at | 200 | Customer profiles |
| categories | id, name, description | 10 | Product categories |
| products | id, name, category_id (FK), price, stock_quantity, created_at | 100 | Product catalog |
| orders | id, customer_id (FK), order_date, status, total_amount | 500 | Order records |
| order_items | id, order_id (FK), product_id (FK), quantity, unit_price | 800 | Line items |
| reviews | id, product_id (FK), customer_id (FK), rating, comment, created_at | 300 | Product reviews |
| shipping | id, order_id (FK), carrier, tracking_number, shipped_date, delivered_date | 400 | Shipping tracking |
| payments | id, order_id (FK), payment_method, amount, status, paid_at | 500 | Payment records |

Total: ~2,800 rows across 8 tables with proper foreign key relationships.

## 6. API Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/query` | Execute natural language query | None |
| GET | `/api/history` | List query history (paginated) | None |
| GET | `/api/history/{id}` | Get single query detail | None |
| DELETE | `/api/history` | Clear all history | None |
| GET | `/api/schema` | Get full database schema | None |
| GET | `/api/schema/{table}` | Get single table detail | None |
| GET | `/api/cache/stats` | Get cache hit/miss statistics | None |
| POST | `/api/cache/invalidate` | Clear all caches | None |
| GET | `/health` | Basic health check | None |
| GET | `/health/ready` | Readiness check (DB + Redis) | None |

## 7. Error Handling Strategy

| Error Type | HTTP Status | User Message |
|------------|-------------|-------------|
| Invalid query (validator blocked) | 400 | "Query blocked: {specific violation}" |
| LLM generated invalid SQL | 400 | "Could not generate valid SQL. Try rephrasing your question." |
| Query timeout | 408 | "Query took too long and was cancelled. Try a more specific question." |
| Database connection failed | 503 | "Database is temporarily unavailable. Please try again." |
| Redis unavailable | 200 (degraded) | Query succeeds but without caching (graceful degradation) |
| OpenAI API error | 502 | "AI service is temporarily unavailable. Please try again." |
| Rate limit exceeded | 429 | "Too many requests. Please wait a moment." |

## 8. Performance Requirements

| Metric | Target | Strategy |
|--------|--------|----------|
| Cold query latency | <2s | Use gpt-4o-mini (faster), minimal prompt, LIMIT in SQL |
| Cached query (L1 hit) | <200ms | Skip LLM entirely, only DB execution |
| Cached query (L1+L2 hit) | <5ms | Skip LLM and DB, Redis only |
| Concurrent users | 10+ | Async FastAPI, connection pooling, Redis connection pool |
| Memory usage | <512MB | Row limits, result pagination, no in-memory caching |
