"""Unit tests for the LLM service — focusing on SQL extraction logic
(the part that doesn't need an actual OpenAI call).
"""

from backend.services.llm_service import _extract_sql


class TestSqlExtraction:
    def test_plain_sql(self):
        assert _extract_sql('SELECT * FROM customers') == 'SELECT * FROM customers'

    def test_strips_trailing_semicolon(self):
        assert _extract_sql('SELECT * FROM customers;') == 'SELECT * FROM customers'

    def test_strips_markdown_code_block(self):
        text = '```sql\nSELECT * FROM customers\n```'
        assert _extract_sql(text) == 'SELECT * FROM customers'

    def test_strips_unlabeled_code_block(self):
        text = '```\nSELECT 1\n```'
        assert _extract_sql(text) == 'SELECT 1'

    def test_collapses_multiline_whitespace(self):
        text = 'SELECT name,\n  email\nFROM customers'
        assert 'SELECT name, email FROM customers' == _extract_sql(text)

    def test_handles_extra_whitespace(self):
        assert _extract_sql('  SELECT 1  ') == 'SELECT 1'
