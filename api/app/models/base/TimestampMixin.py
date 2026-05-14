from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, DateTime
from sqlalchemy.sql import func


class TimestampMixin:
    """Mixin that adds creation and update timestamp columns to SQLAlchemy models.

    Attributes:
        created_at: Timezone-aware datetime set automatically when the row is created.
        updated_at: Timezone-aware datetime set automatically when the row is created
            and refreshed whenever the row is updated.
    """

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)