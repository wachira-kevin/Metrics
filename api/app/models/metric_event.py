import uuid
from sqlalchemy import Column, String, Float, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func, text

from app.core.database import Base
from app.models.base import TimestampMixin


class MetricEvent(Base, TimestampMixin):
    """
    Represents a metric event in the system.

    The `MetricEvent` class is used to record various types of events with associated metadata
    such as values, units, timestamps, and identifiers. It is linked to application tokens
    to support tracking of metrics specific to different applications. The class is designed
    to store and manage these events efficiently and supports querying and filtering based
    on event type, timestamps, and other attributes.

    :ivar id: Unique identifier for the metric event.
    :type id: UUID
    :ivar app_token_id: Identifier linking the event to an application token.
    :type app_token_id: UUID
    :ivar event_type: Type of the event such as "click", "view", etc.
    :type event_type: str
    :ivar value: Numeric value associated with the event.
    :type value: float
    :ivar unit: Unit of measurement for the event's value, if applicable.
    :type unit: str
    :ivar timestamp: Timestamp indicating when the event occurred.
    :type timestamp: datetime
    :ivar session_id: Identifier for the user session associated with the event.
    :type session_id: str
    :ivar device_id: Identifier for the device where the event occurred.
    :type device_id: str
    :ivar attributes: Additional attributes or metadata associated with the event in JSON format.
    :type attributes: dict
    """
    __tablename__ = "metric_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid7)
    app_token_id = Column(
        UUID(as_uuid=True),
        ForeignKey("app_tokens.id", ondelete="CASCADE"),
        index=True
    )
    event_type = Column(String(255), nullable=False, index=True)
    value = Column(Float, nullable=False)
    unit = Column(String(50))
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    session_id = Column(String(255), index=True)
    device_id = Column(String(255), index=True)
    attributes = Column(JSONB, server_default=text("'{}'::jsonb"))