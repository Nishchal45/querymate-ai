"""SQL Validator — security layer that blocks dangerous SQL patterns
before queries reach the database.

This is Layer 1 of the defense-in-depth model:
  Layer 1: SQL Validator (this module) — regex pattern matching
  Layer 2: Read-only connection (psycopg2 readonly=True)
  Layer 3: Database role privileges (querymate_reader = SELECT only)
  Layer 4: Statement timeout (10s at role level)

Design decision: regex over SQL parser (sqlparse)
  A SQL parser can be tricked by malformed SQL that PostgreSQL still
  executes. Regex catches a broader range of obfuscation attempts.
  The 4-layer model means this is just one of four safety nets.
"""

import re

from pydantic import BaseModel


class ValidationResult(BaseModel):
    is_valid: bool
    sql: str
    violations: list[str]


# Patterns that should NEVER appear in LLM-generated queries.
# Each tuple: (compiled regex, human-readable violation message)
_BLOCKED_PATTERNS: list[tuple[re.Pattern, str]] = [
    # DML — data modification
    (re.compile(r'\bINSERT\b', re.I), 'INSERT statements are not allowed'),
    (re.compile(r'\bUPDATE\b(?!\w)', re.I), 'UPDATE statements are not allowed'),
    (re.compile(r'\bDELETE\b', re.I), 'DELETE statements are not allowed'),
    (re.compile(r'\bMERGE\b', re.I), 'MERGE statements are not allowed'),

    # DDL — schema modification
    (re.compile(r'\bDROP\b', re.I), 'DROP statements are not allowed'),
    (re.compile(r'\bALTER\b', re.I), 'ALTER statements are not allowed'),
    (re.compile(r'\bCREATE\b', re.I), 'CREATE statements are not allowed'),
    (re.compile(r'\bTRUNCATE\b', re.I), 'TRUNCATE statements are not allowed'),

    # DCL — access control
    (re.compile(r'\bGRANT\b', re.I), 'GRANT statements are not allowed'),
    (re.compile(r'\bREVOKE\b', re.I), 'REVOKE statements are not allowed'),

    # Stacked queries
    (re.compile(r';'), 'Multiple statements (semicolons) are not allowed'),

    # Comment injection
    (re.compile(r'--'), 'SQL comments (--) are not allowed'),
    (re.compile(r'/\*'), 'Block comments (/*) are not allowed'),

    # UNION injection
    (re.compile(r'\bUNION\s+(ALL\s+)?SELECT\b', re.I),
     'UNION SELECT injection detected'),

    # System table access
    (re.compile(r'\bpg_catalog\b', re.I),
     'Access to pg_catalog is not allowed'),
    (re.compile(r'\binformation_schema\b', re.I),
     'Access to information_schema is not allowed'),
    (re.compile(r'\bpg_stat\b', re.I),
     'Access to pg_stat tables is not allowed'),

    # Dangerous functions
    (re.compile(r'\bpg_sleep\b', re.I),
     'pg_sleep() is not allowed'),
    (re.compile(r'\bpg_read_file\b', re.I),
     'pg_read_file() is not allowed'),
    (re.compile(r'\bpg_ls_dir\b', re.I),
     'pg_ls_dir() is not allowed'),
    (re.compile(r'\blo_import\b', re.I),
     'lo_import() is not allowed'),
    (re.compile(r'\blo_export\b', re.I),
     'lo_export() is not allowed'),
    (re.compile(r'\bdblink\b', re.I),
     'dblink() is not allowed'),
    (re.compile(r'\bquery_to_xml\b', re.I),
     'query_to_xml() is not allowed'),

    # File operations
    (re.compile(r'\bINTO\s+OUTFILE\b', re.I),
     'INTO OUTFILE is not allowed'),
    (re.compile(r'\bINTO\s+DUMPFILE\b', re.I),
     'INTO DUMPFILE is not allowed'),
    (re.compile(r'\bCOPY\b', re.I),
     'COPY command is not allowed'),

    # Role escalation
    (re.compile(r'\bSET\s+ROLE\b', re.I),
     'SET ROLE is not allowed'),
    (re.compile(r'\bSET\s+SESSION\b', re.I),
     'SET SESSION is not allowed'),

    # Encoding attacks
    (re.compile(r'0x[0-9a-fA-F]+'),
     'Hex-encoded values are not allowed'),
    (re.compile(r'\bCHR\s*\(', re.I),
     'CHR() encoding is not allowed'),

    # Extension loading
    (re.compile(r'\bLOAD\b', re.I),
     'LOAD command is not allowed'),
]

# Columns that contain blocked keywords as substrings.
# These are whitelisted to prevent false positives.
# e.g., "updated_at" contains "UPDATE", "created_at" contains "CREATE"
_COLUMN_WHITELIST = re.compile(
    r'(?:updated_at|created_at|deleted_at|drop_off|load_date|'
    r'grant_date|merge_key|copy_of|alter_ego|insert_date)',
    re.I,
)


def _strip_string_literals(sql: str) -> str:
    """Remove string literals to avoid false positives on values."""
    return re.sub(r"'[^']*'", "''", sql)


def _strip_column_identifiers(sql: str) -> str:
    """Replace known safe column names that contain blocked keywords."""
    return _COLUMN_WHITELIST.sub('__safe_col__', sql)


def validate_sql(sql: str) -> ValidationResult:
    """Validate SQL against all security patterns.

    Returns ValidationResult with is_valid=True if safe,
    or is_valid=False with a list of specific violations.
    """
    if not sql or not sql.strip():
        return ValidationResult(
            is_valid=False,
            sql=sql,
            violations=['Empty query'],
        )

    # Check that it starts with SELECT (after stripping whitespace)
    stripped = sql.strip()
    if not re.match(r'^SELECT\b', stripped, re.I):
        return ValidationResult(
            is_valid=False,
            sql=sql,
            violations=['Query must start with SELECT'],
        )

    # Prepare SQL for pattern matching:
    # 1. Strip string literals (prevents false positives on values like 'UPDATE')
    # 2. Strip known safe column names (prevents false positives on updated_at)
    check_sql = _strip_string_literals(stripped)
    check_sql = _strip_column_identifiers(check_sql)

    # Remove the leading SELECT to avoid matching it against blocked patterns
    # (e.g., "SELECT" itself is fine, we only block non-SELECT statement types)
    check_body = re.sub(r'^SELECT\b', '', check_sql, count=1, flags=re.I)

    violations: list[str] = []
    for pattern, message in _BLOCKED_PATTERNS:
        if pattern.search(check_body):
            violations.append(message)

    return ValidationResult(
        is_valid=len(violations) == 0,
        sql=sql,
        violations=violations,
    )
