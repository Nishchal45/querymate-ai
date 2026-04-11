import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column

from backend.core.database import Base


class QueryHistory(Base):
    """Tracks every NL query, the generated SQL, timing, and cache info."""

    __tablename__ = 'query_history'

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    natural_language: Mapped[str]
    generated_sql: Mapped[str]
    execution_time_ms: Mapped[Optional[float]] = mapped_column(default=None)
    row_count: Mapped[Optional[int]] = mapped_column(default=None)
    was_cached: Mapped[bool] = mapped_column(default=False)
    cache_level: Mapped[Optional[str]] = mapped_column(default=None)
    error: Mapped[Optional[str]] = mapped_column(default=None)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
