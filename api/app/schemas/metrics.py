from datetime import datetime, date
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


class MetricsSummaryResponse(BaseModel):
    """
    Response returned after a successful metrics summary request.
    """
    model_config = ConfigDict(populate_by_name=True)

    total_sessions: int = Field(alias="totalSessions")
    avg_session_duration: float = Field(alias="avgSessionDuration")
    total_crashes: int = Field(alias="totalCrashes")
    avg_app_start_time: float = Field(alias="avgAppStartTime")


class ScreenMetricResponse(BaseModel):
    """
    Response returned after a successful screen metrics request.
    """
    model_config = ConfigDict(populate_by_name=True)

    screen_name: str = Field(alias="screenName")
    visit_count: int = Field(alias="visitCount")
    avg_duration_ms: float = Field(alias="avgDurationMs")


class HttpMetricResponse(BaseModel):
    """
    Response returned after a successful HTTP metrics request.
    """
    model_config = ConfigDict(populate_by_name=True)

    total_requests: int = Field(alias="totalRequests")
    error_rate: float = Field(alias="errorRate")
    avg_latency: float = Field(alias="avgLatency")
    p95_latency: float = Field(alias="p95Latency")


class CrashTimelineResponse(BaseModel):
    """
    Response returned after a successful Crash Timeline metrics request.
    """
    model_config = ConfigDict(populate_by_name=True)

    date: date
    crash_count: int = Field(alias="crashCount")
    anr_count: int = Field(alias="anrCount")


class DeviceMetricResponse(BaseModel):
    """
    Response returned after a successful Device metrics request.
    """
    model_config = ConfigDict(populate_by_name=True)

    device_id: str | None = Field(alias="deviceId")
    sessions: int
    crashes: int
    avg_memory: float = Field(alias="avgMemory")


class NetworkDistributionResponse(BaseModel):
    """
    Response returned after a successful Network Distribution metrics request.
    """
    model_config = ConfigDict(populate_by_name=True)

    network_type: str = Field(alias="networkType")
    count: int
    percentage: float


class BatteryBucketResponse(BaseModel):
    """
    Response returned after a successful Battery Bucket metrics request.
    """
    model_config = ConfigDict(populate_by_name=True)

    bucket_start: int = Field(alias="bucketStart")
    bucket_end: int = Field(alias="bucketEnd")
    session_count: int = Field(alias="sessionCount")


class CustomEventMetricResponse(BaseModel):
    """
    Response returned after a successful Custom Event metrics request.
    """
    key: str
    value: str
    frequency: int


class FrameDropTrendResponse(BaseModel):
    """
    Response returned after a successful Frame Drop Trend metrics request.
    """
    model_config = ConfigDict(populate_by_name=True)

    date: date
    screen_name: str | None = Field(alias="screenName")
    avg_frame_drop_count: float = Field(alias="avgFrameDropCount")


class ActiveSessionsResponse(BaseModel):
    """
    Response returned after a successful Active Sessions metrics request.
    """
    model_config = ConfigDict(populate_by_name=True)

    active_sessions: int = Field(alias="activeSessions")


class DeleteSessionMetricsResponse(BaseModel):
    """
    Response returned after a successful Delete Session Metrics request.
    """
    model_config = ConfigDict(populate_by_name=True)

    deleted_events: int = Field(alias="deletedEvents")