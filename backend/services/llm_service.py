"""LLM Service — constructs prompts from schema + natural language
and extracts valid PostgreSQL SQL from the LLM response.
"""

import logging
import re

from openai import AsyncOpenAI

from backend.core.config import settings
from backend.services.introspector import SchemaInfo, format_schema_for_prompt

logger = logging.getLogger(__name__)

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=settings.openai_api_key)
    return _client


SYSTEM_PROMPT = """You are a PostgreSQL SQL expert. Given the database schema below, generate a single SELECT query that answers the user's question.

Rules:
- ONLY generate SELECT statements — never INSERT, UPDATE, DELETE, DROP, or any data-modifying statement
- Use proper JOIN syntax when relating tables via foreign keys
- Use table aliases for readability (e.g., SELECT o.id FROM orders o)
- Include LIMIT 1000 unless the user specifies a different count
- Use PostgreSQL-compatible syntax
- Return ONLY the SQL query, no explanations or markdown

Schema:
{schema}

Examples:
Q: How many customers are there?
A: SELECT COUNT(*) AS customer_count FROM customers;

Q: What are the top 5 best-selling products?
A: SELECT p.name, SUM(oi.quantity) AS total_sold FROM products p JOIN order_items oi ON oi.product_id = p.id GROUP BY p.id, p.name ORDER BY total_sold DESC LIMIT 5;

Q: What is the average order value by month?
A: SELECT DATE_TRUNC('month', order_date) AS month, ROUND(AVG(total_amount), 2) AS avg_order_value FROM orders GROUP BY month ORDER BY month;"""


def _extract_sql(response_text: str) -> str:
    """Extract SQL from the LLM response, stripping markdown if present."""
    text = response_text.strip()

    # Handle markdown code blocks: ```sql ... ``` or ``` ... ```
    code_block = re.search(r'```(?:sql)?\s*\n?(.*?)\n?```', text, re.DOTALL)
    if code_block:
        text = code_block.group(1).strip()

    # Remove trailing semicolons (executor doesn't need them)
    text = text.rstrip(';').strip()

    # Remove any leading/trailing whitespace or newlines
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return ' '.join(lines)


async def generate_sql(
    natural_language: str,
    schema: SchemaInfo,
) -> str:
    """Generate a PostgreSQL SELECT query from natural language.

    Args:
        natural_language: The user's question in plain English
        schema: Database schema from the introspector

    Returns:
        Clean SQL string ready for validation
    """
    formatted_schema = format_schema_for_prompt(schema)
    system_prompt = SYSTEM_PROMPT.format(schema=formatted_schema)

    client = _get_client()
    response = await client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': natural_language},
        ],
        temperature=0,
        max_tokens=500,
    )

    raw_sql = response.choices[0].message.content or ''
    sql = _extract_sql(raw_sql)

    logger.info(
        'SQL generated — model=%s tokens=%d',
        settings.openai_model,
        response.usage.total_tokens if response.usage else 0,
    )

    return sql
