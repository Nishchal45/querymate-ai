"""Security tests for the SQL validator.

This is the most important test file — it codifies the security
boundary of QueryMate AI. Every blocked attack pattern has a
dedicated test case.
"""

import pytest

from backend.services.sql_validator import validate_sql


# ── Valid queries should pass ──

class TestValidQueries:
    def test_simple_select(self):
        result = validate_sql('SELECT * FROM customers')
        assert result.is_valid
        assert result.violations == []

    def test_select_with_where(self):
        result = validate_sql("SELECT name FROM customers WHERE state = 'CA'")
        assert result.is_valid

    def test_select_with_join(self):
        sql = (
            'SELECT c.name, o.total_amount '
            'FROM customers c JOIN orders o ON o.customer_id = c.id'
        )
        result = validate_sql(sql)
        assert result.is_valid

    def test_select_with_group_by(self):
        sql = (
            'SELECT category_id, COUNT(*) AS cnt FROM products '
            'GROUP BY category_id HAVING COUNT(*) > 5'
        )
        result = validate_sql(sql)
        assert result.is_valid

    def test_select_with_subquery(self):
        sql = (
            'SELECT name FROM customers '
            'WHERE id IN (SELECT customer_id FROM orders)'
        )
        result = validate_sql(sql)
        assert result.is_valid

    def test_select_with_aggregates(self):
        sql = 'SELECT AVG(total_amount), MAX(total_amount), MIN(total_amount) FROM orders'
        result = validate_sql(sql)
        assert result.is_valid


# ── DML statements blocked (data modification) ──

class TestDMLBlocked:
    @pytest.mark.parametrize('sql', [
        "INSERT INTO customers (name) VALUES ('hacker')",
        "SELECT 1; INSERT INTO customers VALUES ('x')",
    ])
    def test_insert_blocked(self, sql):
        result = validate_sql(sql)
        assert not result.is_valid

    @pytest.mark.parametrize('sql', [
        'UPDATE customers SET name = NULL',
        'SELECT * FROM customers WHERE id IN (SELECT 1) ; UPDATE x SET y=1',
    ])
    def test_update_blocked(self, sql):
        result = validate_sql(sql)
        assert not result.is_valid

    def test_delete_blocked(self):
        result = validate_sql('DELETE FROM customers')
        assert not result.is_valid

    def test_merge_blocked(self):
        result = validate_sql('SELECT 1 FROM customers; MERGE INTO orders USING customers')
        assert not result.is_valid


# ── DDL statements blocked (schema modification) ──

class TestDDLBlocked:
    def test_drop_table_blocked(self):
        result = validate_sql('DROP TABLE customers')
        assert not result.is_valid
        assert any('SELECT' in v or 'DROP' in v for v in result.violations)

    def test_alter_table_blocked(self):
        result = validate_sql('ALTER TABLE customers ADD COLUMN evil TEXT')
        assert not result.is_valid

    def test_create_table_blocked(self):
        result = validate_sql('CREATE TABLE evil (id INT)')
        assert not result.is_valid

    def test_truncate_blocked(self):
        result = validate_sql('TRUNCATE customers')
        assert not result.is_valid


# ── DCL blocked (access control) ──

class TestDCLBlocked:
    def test_grant_blocked(self):
        result = validate_sql('SELECT 1; GRANT ALL ON customers TO public')
        assert not result.is_valid

    def test_revoke_blocked(self):
        result = validate_sql('SELECT 1; REVOKE ALL ON customers FROM public')
        assert not result.is_valid


# ── Injection attack patterns ──

class TestInjectionBlocked:
    def test_stacked_queries_blocked(self):
        result = validate_sql('SELECT 1; DROP TABLE customers')
        assert not result.is_valid
        assert any('semicolon' in v.lower() or 'multiple' in v.lower()
                   for v in result.violations)

    def test_dash_comment_blocked(self):
        result = validate_sql('SELECT * FROM customers -- WHERE id = 1')
        assert not result.is_valid

    def test_block_comment_blocked(self):
        result = validate_sql('SELECT * FROM customers /* comment */')
        assert not result.is_valid

    def test_union_injection_blocked(self):
        result = validate_sql(
            'SELECT name FROM customers UNION SELECT password FROM admin_users'
        )
        assert not result.is_valid

    def test_union_all_injection_blocked(self):
        result = validate_sql(
            'SELECT name FROM customers UNION ALL SELECT secret FROM secrets'
        )
        assert not result.is_valid

    def test_hex_encoding_blocked(self):
        result = validate_sql('SELECT * FROM customers WHERE id = 0x44524F50')
        assert not result.is_valid

    def test_chr_encoding_blocked(self):
        result = validate_sql('SELECT CHR(68) || CHR(82) || CHR(79) || CHR(80) FROM customers')
        assert not result.is_valid


# ── Dangerous PostgreSQL functions ──

class TestDangerousFunctionsBlocked:
    def test_pg_sleep_blocked(self):
        result = validate_sql('SELECT pg_sleep(10) FROM customers')
        assert not result.is_valid

    def test_pg_read_file_blocked(self):
        result = validate_sql("SELECT pg_read_file('/etc/passwd')")
        assert not result.is_valid

    def test_pg_ls_dir_blocked(self):
        result = validate_sql("SELECT pg_ls_dir('/')")
        assert not result.is_valid

    def test_lo_import_blocked(self):
        result = validate_sql("SELECT lo_import('/etc/passwd')")
        assert not result.is_valid

    def test_lo_export_blocked(self):
        result = validate_sql("SELECT lo_export(1, '/tmp/dump')")
        assert not result.is_valid

    def test_dblink_blocked(self):
        result = validate_sql("SELECT dblink('host=evil', 'SELECT 1')")
        assert not result.is_valid


# ── System table access ──

class TestSystemTablesBlocked:
    def test_pg_catalog_blocked(self):
        result = validate_sql('SELECT * FROM pg_catalog.pg_user')
        assert not result.is_valid

    def test_information_schema_blocked(self):
        result = validate_sql('SELECT * FROM information_schema.tables')
        assert not result.is_valid

    def test_pg_stat_blocked(self):
        result = validate_sql('SELECT * FROM pg_stat_activity')
        assert not result.is_valid


# ── File operations and role escalation ──

class TestFileOpsAndRoleEscalation:
    def test_into_outfile_blocked(self):
        result = validate_sql("SELECT * FROM customers INTO OUTFILE '/tmp/data.csv'")
        assert not result.is_valid

    def test_copy_blocked(self):
        result = validate_sql("SELECT 1; COPY customers TO '/tmp/data.csv'")
        assert not result.is_valid

    def test_set_role_blocked(self):
        result = validate_sql('SELECT 1; SET ROLE postgres')
        assert not result.is_valid

    def test_load_blocked(self):
        result = validate_sql("SELECT 1; LOAD 'extension.so'")
        assert not result.is_valid


# ── False positive prevention ──

class TestFalsePositives:
    """These queries contain blocked-keyword substrings but should pass."""

    def test_updated_at_column_passes(self):
        result = validate_sql('SELECT name, updated_at FROM customers')
        assert result.is_valid

    def test_created_at_column_passes(self):
        result = validate_sql('SELECT id, created_at FROM customers ORDER BY created_at DESC')
        assert result.is_valid

    def test_string_with_keyword_in_value_passes(self):
        # The value is in a string literal, not a SQL keyword
        result = validate_sql("SELECT * FROM logs WHERE action = 'INSERT'")
        assert result.is_valid


# ── Edge cases ──

class TestEdgeCases:
    def test_empty_query_blocked(self):
        result = validate_sql('')
        assert not result.is_valid

    def test_whitespace_only_blocked(self):
        result = validate_sql('   \n  \t  ')
        assert not result.is_valid

    def test_non_select_statement_blocked(self):
        result = validate_sql('SHOW TABLES')
        assert not result.is_valid

    def test_case_insensitive_select(self):
        # Lowercase select should pass
        result = validate_sql('select * from customers')
        assert result.is_valid

    def test_case_insensitive_blocking(self):
        result = validate_sql('SELECT 1; drop TABLE customers')
        assert not result.is_valid
