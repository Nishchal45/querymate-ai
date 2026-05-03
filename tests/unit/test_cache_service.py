"""Unit tests for cache service helpers (no Redis required)."""

from backend.services.cache_service import _hash_key, _normalize_query


class TestNormalization:
    def test_lowercase(self):
        assert _normalize_query('How Many Orders?') == 'how many orders'

    def test_strips_punctuation(self):
        assert _normalize_query('How many orders?') == _normalize_query('how many orders')

    def test_collapses_whitespace(self):
        assert _normalize_query('how   many\n\torders') == 'how many orders'

    def test_strips_outer_whitespace(self):
        assert _normalize_query('   how many orders?  ') == 'how many orders'

    def test_semantically_equivalent_questions_match(self):
        a = _normalize_query('How many customers?')
        b = _normalize_query('how many customers')
        c = _normalize_query('  HOW MANY CUSTOMERS???  ')
        assert a == b == c


class TestHashing:
    def test_deterministic(self):
        assert _hash_key('hello') == _hash_key('hello')

    def test_different_inputs_differ(self):
        assert _hash_key('hello') != _hash_key('world')

    def test_returns_short_hash(self):
        # First 16 chars of SHA-256
        assert len(_hash_key('anything')) == 16

    def test_handles_unicode(self):
        # Should not crash on non-ASCII
        result = _hash_key('héllo wörld 日本語')
        assert len(result) == 16
