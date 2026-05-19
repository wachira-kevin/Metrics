from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class MetricEventIngestRequest(BaseModel):
    """
    Represents one metric event sent by the SDK.
    """
    event_type: str = Field(alias="eventType", min_length=1, max_length=255)
    value: float
    unit: str | None = Field(default=None, max_length=50)
    timestamp: datetime | None = None
    session_id: str | None = Field(default=None, alias="sessionId", max_length=255)
    device_id: str | None = Field(default=None, alias="deviceId", max_length=255)
    attributes: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(populate_by_name=True)


class MetricBatchIngestRequest(BaseModel):
    """
    Represents the batch payload sent by the Java SDK.
    """
    events: list[MetricEventIngestRequest] = Field(min_length=1, max_length=1000)


class MetricBatchIngestResponse(BaseModel):
    """
    Response returned after a successful batch ingest.
    """
    accepted: int