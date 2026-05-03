"""Schema Introspector — reads PostgreSQL system catalogs and compresses
schema information to fit within LLM token budgets.

Queries:
  - information_schema.tables / columns for structure
  - pg_constraint for PK / FK relationships
  - pg_stat_user_tables for approximate row counts
  - SELECT DISTINCT ... LIMIT 5 for sample values
"""

import logging
from typing import Optional

from pydantic import BaseModel

from backend.core.target_database import get_target_connection

logger = logging.getLogger(__name__)

# Approximate tokens per character (conservative estimate for SQL schemas)
CHARS_PER_TOKEN = 4
DEFAULT_TOKEN_BUDGET = 3000


class ColumnInfo(BaseModel):
    name: str
    data_type: str
    is_nullable: bool
    is_primary_key: bool = False
    foreign_key: Optional[str] = None  # "table.column" format
    sample_values: Optional[list[str]] = None


class TableInfo(BaseModel):
    name: str
    columns: list[ColumnInfo]
    row_count: Optional[int] = None


class SchemaInfo(BaseModel):
    tables: list[TableInfo]
    compression_level: int = 0


def _fetch_tables(cur) -> list[str]:
    """Get all user table names."""
    cur.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
        ORDER BY table_name
    """)
    return [row[0] for row in cur.fetchall()]


def _fetch_columns(cur, table_name: str) -> list[dict]:
    """Get columns with types and nullable info."""
    cur.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = %s
        ORDER BY ordinal_position
    """, (table_name,))
    return [
        {
            'name': row[0],
            'data_type': row[1],
            'is_nullable': row[2] == 'YES',
        }
        for row in cur.fetchall()
    ]


def _fetch_primary_keys(cur, table_name: str) -> set[str]:
    """Get primary key column names for a table."""
    cur.execute("""
        SELECT kcu.column_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
        WHERE tc.table_name = %s
            AND tc.constraint_type = 'PRIMARY KEY'
            AND tc.table_schema = 'public'
    """, (table_name,))
    return {row[0] for row in cur.fetchall()}


def _fetch_foreign_keys(cur, table_name: str) -> dict[str, str]:
    """Get FK mappings: {column_name: 'referenced_table.referenced_column'}."""
    cur.execute("""
        SELECT
            kcu.column_name,
            ccu.table_name AS ref_table,
            ccu.column_name AS ref_column
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage ccu
            ON tc.constraint_name = ccu.constraint_name
            AND tc.table_schema = ccu.table_schema
        WHERE tc.table_name = %s
            AND tc.constraint_type = 'FOREIGN KEY'
            AND tc.table_schema = 'public'
    """, (table_name,))
    return {row[0]: f'{row[1]}.{row[2]}' for row in cur.fetchall()}


def _fetch_row_count(cur, table_name: str) -> int:
    """Get approximate row count from pg_stat (no full table scan)."""
    cur.execute("""
        SELECT COALESCE(n_live_tup, 0)
        FROM pg_stat_user_tables
        WHERE relname = %s
    """, (table_name,))
    result = cur.fetchone()
    return int(result[0]) if result else 0


def _fetch_sample_values(cur, table_name: str, column_name: str) -> list[str]:
    """Get up to 5 distinct non-null sample values for a column."""
    try:
        cur.execute(
            f'SELECT DISTINCT "{column_name}" FROM "{table_name}" '
            f'WHERE "{column_name}" IS NOT NULL LIMIT 5'
        )
        return [str(row[0]) for row in cur.fetchall()]
    except Exception:
        return []


def _estimate_tokens(schema: SchemaInfo) -> int:
    """Estimate token count for the schema when formatted as text."""
    text = format_schema_for_prompt(schema)
    return len(text) // CHARS_PER_TOKEN


def _compress(schema: SchemaInfo, level: int) -> SchemaInfo:
    """Apply compression at the given level."""
    compressed = schema.model_copy(deep=True)
    compressed.compression_level = level

    for table in compressed.tables:
        if level >= 1:
            for col in table.columns:
                col.sample_values = None
        if level >= 2:
            table.row_count = None
        if level >= 3:
            for col in table.columns:
                col.foreign_key = None
                col.is_primary_key = False

    return compressed


def introspect_schema(token_budget: int = DEFAULT_TOKEN_BUDGET) -> SchemaInfo:
    """Read the target database schema with progressive compression.

    Compression levels:
        0 — Full: tables, columns, types, PKs, FKs, row counts, samples
        1 — Drop sample values
        2 — Drop row counts
        3 — Minimal: tables, columns, types only
    """
    tables: list[TableInfo] = []

    with get_target_connection() as conn:
        with conn.cursor() as cur:
            table_names = _fetch_tables(cur)

            for table_name in table_names:
                columns_raw = _fetch_columns(cur, table_name)
                pks = _fetch_primary_keys(cur, table_name)
                fks = _fetch_foreign_keys(cur, table_name)
                row_count = _fetch_row_count(cur, table_name)

                columns = []
                for col in columns_raw:
                    col_name = col['name']
                    samples = _fetch_sample_values(cur, table_name, col_name)
                    columns.append(ColumnInfo(
                        name=col_name,
                        data_type=col['data_type'],
                        is_nullable=col['is_nullable'],
                        is_primary_key=col_name in pks,
                        foreign_key=fks.get(col_name),
                        sample_values=samples if samples else None,
                    ))

                tables.append(TableInfo(
                    name=table_name,
                    columns=columns,
                    row_count=row_count,
                ))

    schema = SchemaInfo(tables=tables, compression_level=0)

    # Progressive compression to fit token budget
    for level in range(4):
        compressed = _compress(schema, level)
        if _estimate_tokens(compressed) <= token_budget:
            logger.info(
                'Schema introspected — %d tables, compression level %d',
                len(tables), level,
            )
            return compressed

    logger.warning('Schema exceeds token budget even at max compression')
    return _compress(schema, 3)


def format_schema_for_prompt(schema: SchemaInfo) -> str:
    """Format schema as readable text for the LLM prompt."""
    lines = []
    for table in schema.tables:
        header = f'Table: {table.name}'
        if table.row_count is not None:
            header += f' (~{table.row_count} rows)'
        lines.append(header)

        for col in table.columns:
            parts = [f'  - {col.name} ({col.data_type})']
            if col.is_primary_key:
                parts.append('PK')
            if col.foreign_key:
                parts.append(f'FK -> {col.foreign_key}')
            if not col.is_nullable:
                parts.append('NOT NULL')
            if col.sample_values:
                samples = ', '.join(col.sample_values[:3])
                parts.append(f'e.g. [{samples}]')
            lines.append(' '.join(parts))

        lines.append('')

    return '\n'.join(lines)
