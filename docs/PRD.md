# QueryMate AI — Product Requirements Document (PRD)

**Version:** 1.0
**Author:** Nishchal
**Date:** 2026-03-21
**Status:** Approved

---

## 1. Overview

QueryMate AI is a natural language to SQL conversion system that enables users to query PostgreSQL databases using plain English. The system reads the database schema, constructs an optimized LLM prompt, generates validated SQL, executes it safely, and returns structured results with optional chart visualizations.

## 2. Problem Statement

Non-technical users (analysts, product managers, business stakeholders) cannot query databases directly — they depend on engineers to write SQL for every data question. Even for SQL-proficient engineers, writing correct JOINs across unfamiliar schemas is slow and error-prone.

**Current pain points:**
- Data analysts wait hours/days for engineers to write queries
- Ad-hoc SQL is often unoptimized and sometimes unsafe
- Schema documentation is outdated or nonexistent
- Repeated questions hit the database and LLM unnecessarily

## 3. Target Users

| User | Need | Frequency |
|------|------|-----------|
| **Data Analyst** | Query databases without writing SQL; knows the data but not the syntax | Daily |
| **Product Manager** | Get quick answers about metrics, orders, revenue without filing tickets | Weekly |
| **Engineer** | Explore unfamiliar schemas quickly; validate query logic | As needed |
| **Portfolio Reviewer** | Understand the system's architecture, security model, and engineering decisions | One-time |

## 4. Goals

| ID | Goal | Measurable Outcome |
|----|------|-------------------|
| G1 | Natural language to SQL conversion | >85% accuracy on demo schema (correct SQL for common e-commerce questions) |
| G2 | Fast response times | <2s end-to-end for first query; <5ms for cached queries |
| G3 | Zero SQL injection vulnerabilities | 20+ attack patterns blocked; 4-layer defense in depth |
| G4 | Reduce redundant LLM/DB calls | Two-level caching reduces LLM calls by 60%+ for repeated questions |
| G5 | Schema-aware prompting | Automatic schema introspection with progressive compression for token budget |

## 5. Non-Goals

- Multi-database support (PostgreSQL only — no MySQL, SQLite, etc.)
- User authentication or multi-tenancy
- Write queries (INSERT, UPDATE, DELETE — SELECT only)
- Cloud deployment or Kubernetes orchestration
- Real-time streaming or WebSocket responses
- Natural language query correction or suggestion system

## 6. User Stories

### Epic 1: Query Execution

| ID | Story | Priority |
|----|-------|----------|
| US-1 | As an analyst, I want to type a question in plain English and get back a table of results so I don't need to know SQL | P0 |
| US-2 | As an analyst, I want to see the generated SQL so I can verify the query logic and learn SQL patterns | P0 |
| US-3 | As a user, I want dangerous queries blocked automatically so the database is protected from accidental damage | P0 |
| US-4 | As a user, I want queries that take too long to be cancelled automatically so one bad query doesn't lock the database | P1 |

### Epic 2: Schema Exploration

| ID | Story | Priority |
|----|-------|----------|
| US-5 | As a user, I want to browse the database schema (tables, columns, types) so I know what data is available to query | P1 |
| US-6 | As a user, I want to see sample values for each column so I can formulate more precise questions | P2 |

### Epic 3: History & Caching

| ID | Story | Priority |
|----|-------|----------|
| US-7 | As a user, I want my past queries saved so I can re-run them without retyping | P1 |
| US-8 | As a user, I want repeated questions to return instantly from cache so I'm not waiting for the LLM every time | P1 |

### Epic 4: Visualization

| ID | Story | Priority |
|----|-------|----------|
| US-9 | As an analyst, I want results displayed as charts when appropriate so I can spot trends quickly | P2 |
| US-10 | As a user, I want to sort and paginate large result sets so I can explore the data interactively | P1 |

## 7. Success Criteria

| Metric | Target | How to Measure |
|--------|--------|----------------|
| SQL accuracy | >85% on demo schema | Run 20 representative questions, count correct SQL |
| First query latency | <2 seconds | Measure end-to-end from API request to response |
| Cached query latency | <5 milliseconds | Measure L1 cache hit response time |
| Security coverage | 20+ attack patterns | Count test cases in test_sql_validator.py |
| Cache hit rate | >60% in typical usage | Redis stats after running the same 10 questions twice |

## 8. Milestones

| Milestone | Phase | Description |
|-----------|-------|-------------|
| M0 | Phase 0 | Planning complete — PRD, TRD, architecture, issues created |
| M1 | Phase 1 | Infrastructure ready — Docker, CI, scaffolding |
| M2 | Phase 2 | Backend foundation — FastAPI running, DB connected |
| M3 | Phase 3 | Core pipeline — NL→SQL→validate→execute working end-to-end |
| M4 | Phase 4-5 | Full backend — Caching + REST API complete |
| M5 | Phase 6 | Frontend — Full UI with query, results, charts |
| M6 | Phase 7-8 | Production-ready — Tests passing, docs complete |

## 9. Risks

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| LLM generates invalid SQL | Poor UX, user frustration | Medium | Validator catches dangerous SQL; executor returns friendly errors for syntax issues |
| OpenAI API costs during development | Budget overrun | Low | Use gpt-4o-mini (~$0.15/1M tokens), cache aggressively, mock in tests |
| Schema too large for token budget | LLM can't see full schema | Medium | Progressive compression drops metadata at 4 levels to fit any budget |
| SQL injection via LLM output | Database compromise | High | 4-layer defense: validator + read-only connection + DB role + statement timeout |
