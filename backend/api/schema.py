"""Schema exploration endpoints — browse the target database structure."""

import logging

from fastapi import APIRouter, HTTPException

from backend.api.schemas import ColumnSchema, SchemaResponse, TableSchema
from backend.services.introspector import introspect_schema

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/api/schema', tags=['schema'])


@router.get('', response_model=SchemaResponse)
async def get_schema() -> SchemaResponse:
    """Get the full target database schema."""
    schema = introspect_schema()
    return SchemaResponse(
        tables=[
            TableSchema(
                name=t.name,
                columns=[
                    ColumnSchema(
                        name=c.name,
                        data_type=c.data_type,
                        is_nullable=c.is_nullable,
                        is_primary_key=c.is_primary_key,
                        foreign_key=c.foreign_key,
                        sample_values=c.sample_values,
                    )
                    for c in t.columns
                ],
                row_count=t.row_count,
            )
            for t in schema.tables
        ],
        table_count=len(schema.tables),
    )


@router.get('/{table_name}', response_model=TableSchema)
async def get_table(table_name: str) -> TableSchema:
    """Get schema details for a single table."""
    schema = introspect_schema()
    for t in schema.tables:
        if t.name == table_name:
            return TableSchema(
                name=t.name,
                columns=[
                    ColumnSchema(
                        name=c.name,
                        data_type=c.data_type,
                        is_nullable=c.is_nullable,
                        is_primary_key=c.is_primary_key,
                        foreign_key=c.foreign_key,
                        sample_values=c.sample_values,
                    )
                    for c in t.columns
                ],
                row_count=t.row_count,
            )
    raise HTTPException(status_code=404, detail=f'Table "{table_name}" not found')
