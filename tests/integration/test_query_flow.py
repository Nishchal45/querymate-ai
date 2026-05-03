"""Integration tests for the full query flow.

These tests require a running PostgreSQL with the demo schema seeded.
The GitHub Actions CI workflow seeds it via scripts/01_schema.sql.
"""

import os

import pytest

psycopg2 = pytest.importorskip('psycopg2')

# Skip integration tests if target DB is not configured
TARGET_DB_URL = os.environ.get('TARGET_DATABASE_URL')

pytestmark = pytest.mark.skipif(
    not TARGET_DB_URL,
    reason='TARGET_DATABASE_URL not set; skipping integration tests',
)


@pytest.fixture
def target_db_conn():
    """Connection to the target database for direct verification."""
    conn = psycopg2.connect(TARGET_DB_URL)
    conn.set_session(readonly=True, autocommit=True)
    yield conn
    conn.close()


def test_demo_schema_has_expected_tables(target_db_conn):
    """Verify the demo schema has all 8 expected tables."""
    expected_tables = {
        'customers', 'categories', 'products', 'orders',
        'order_items', 'reviews', 'shipping', 'payments',
    }

    with target_db_conn.cursor() as cur:
        cur.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
        """)
        actual = {row[0] for row in cur.fetchall()}

    assert expected_tables.issubset(actual), (
        f'Missing tables: {expected_tables - actual}'
    )


def test_introspector_returns_all_tables(target_db_conn):
    """Schema introspector reads all tables from the demo DB."""
    from backend.services.introspector import introspect_schema

    schema = introspect_schema()
    table_names = {t.name for t in schema.tables}
    assert {'customers', 'orders', 'products'}.issubset(table_names)


def test_introspector_detects_foreign_keys(target_db_conn):
    """FK relationships should be detected (orders.customer_id -> customers.id)."""
    from backend.services.introspector import introspect_schema

    schema = introspect_schema()
    orders = next(t for t in schema.tables if t.name == 'orders')
    customer_id_col = next(c for c in orders.columns if c.name == 'customer_id')
    assert customer_id_col.foreign_key == 'customers.id'


def test_executor_runs_simple_select(target_db_conn):
    """Validated SQL should execute via the executor service."""
    from backend.services.query_executor import QueryResult, execute_query

    result = execute_query('SELECT COUNT(*) AS total FROM customers')
    assert isinstance(result, QueryResult)
    assert result.row_count == 1
    assert result.columns == ['total']
    # Should have approximately 200 customers from seed data
    assert int(result.rows[0][0]) >= 100


def test_executor_blocks_write_at_db_level(target_db_conn):
    """Even if the validator missed it, the read-only connection blocks writes."""
    from backend.services.query_executor import QueryError, execute_query

    # This SQL bypasses the validator (skipping it intentionally for this test)
    # to verify Layer 2/3 (read-only connection + DB role) catches it
    result = execute_query("INSERT INTO customers (name, email) VALUES ('hack', 'h@h.com')")
    assert isinstance(result, QueryError)
