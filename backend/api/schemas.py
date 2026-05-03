"""Pydantic request/response models for the API."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


# ── Query ──

class QueryRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=3,
        max_length=500,
        examples=['How many customers are in California?'],
    )


class QueryResponse(BaseModel):
    query_id: UUID
    question: str
    sql: str
    result: dict[str, Any] | None = None
    error: str | None = None
    execution_time_ms: float
    cached: bool = False
    cache_level: str | None = None


# ── History ──

class HistoryItem(BaseModel):
    id: UUID
    natural_language: str
    generated_sql: str
    execution_time_ms: float | None
    row_count: int | None
    was_cached: bool
    cache_level: str | None
    error: str | None
    created_at: datetime


class HistoryResponse(BaseModel):
    items: list[HistoryItem]
    total: int
    page: int
    page_size: int


# ── Schema ──

class ColumnSchema(BaseModel):
    name: str
    data_type: str
    is_nullable: bool
    is_primary_key: bool
    foreign_key: str | None = None
    sample_values: list[str] | None = None


class TableSchema(BaseModel):
    name: str
    columns: list[ColumnSchema]
    row_count: int | None = None


class SchemaResponse(BaseModel):
    tables: list[TableSchema]
    table_count: int


# ── Cache ──

class CacheStatsResponse(BaseModel):
    l1_hits: int
    l1_misses: int
    l2_hits: int
    l2_misses: int
    l1_hit_rate: float
    l2_hit_rate: float
