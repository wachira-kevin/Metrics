from datetime import datetime

from fastapi import APIRouter, Depends, status, Query, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.app_token import get_current_app_token
from app.dependencies.auth import get_current_user
from app.models import AppToken, User
from app.schemas.metrics import MetricBatchIngestRequest, MetricBatchIngestResponse, MetricsSummaryResponse, \
    ScreenMetricResponse, HttpMetricResponse, CrashTimelineResponse, DeviceMetricResponse, NetworkDistributionResponse, \
    BatteryBucketResponse, CustomEventMetricResponse, FrameDropTrendResponse, ActiveSessionsResponse, \
    DeleteSessionMetricsResponse
from app.services.metric_service import ingest_metric_events, get_summary, get_screens, get_http_overview, get_crashes, \
    get_devices, get_network, get_battery, get_custom_events, get_frame_drops, get_active_sessions, \
    delete_session_metrics

metrics_router = APIRouter(tags=["metrics"])


def require_admin(user: User) -> None:
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )


@metrics_router.post(
    "/ingest",
    response_model=MetricBatchIngestResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def ingest(
    payload: MetricBatchIngestRequest,
    db: Session = Depends(get_db),
    app_token: AppToken = Depends(get_current_app_token),
):
    """
    Handles the ingestion of metric events in batch. This endpoint allows clients
    to submit a batch of metric data for processing and storing. The ingestion
    process validates the provided data and processes it asynchronously after
    ensuring it adheres to the expected format and structure.

    :param payload: The MetricBatchIngestRequest object containing a batch of
        metric data submitted for ingestion.
    :param db: A SQLAlchemy Session instance used to interact with the database
        for storing metric data.
    :param app_token: The AppToken object, validated to ensure the request
        originates from an authorized application.
    :return: The MetricBatchIngestResponse object indicating the result of the
        ingestion request, which typically includes metadata about the ingestion
        process.
    """
    return ingest_metric_events(
        db,
        app_token=app_token,
        payload=payload,
    )


@metrics_router.get(
    "/metrics/summary",
    response_model=MetricsSummaryResponse,
    status_code=status.HTTP_200_OK,
)
def metrics_summary(
    from_date: datetime | None = Query(default=None, alias="from"),
    to_date: datetime | None = Query(default=None, alias="to"),
    device_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieves screen usage metrics.

    This endpoint returns analytics related to screen views,
    navigation frequency, and screen interaction trends
    collected from application sessions.

    :param from_date: Optional start datetime used to filter metrics.
    :param to_date: Optional end datetime used to filter metrics.
    :param device_id: Optional device identifier filter.
    :param db: SQLAlchemy database session dependency.
    :param current_user: Authenticated user performing the request.
    :return: List of screen metric analytics.
    """
    return get_summary(
        db,
        user=current_user,
        from_date=from_date,
        to_date=to_date,
        device_id=device_id,
    )


@metrics_router.get(
    "/metrics/screens",
    response_model=list[ScreenMetricResponse],
    status_code=status.HTTP_200_OK,
)
def metrics_screens(
    from_date: datetime | None = Query(default=None, alias="from"),
    to_date: datetime | None = Query(default=None, alias="to"),
    device_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_screens(
        db,
        user=current_user,
        from_date=from_date,
        to_date=to_date,
        device_id=device_id,
    )


@metrics_router.get(
    "/metrics/http",
    response_model=HttpMetricResponse,
    status_code=status.HTTP_200_OK,
)
def metrics_http(
    from_date: datetime | None = Query(default=None, alias="from"),
    to_date: datetime | None = Query(default=None, alias="to"),
    device_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieves HTTP performance and request metrics.

    This endpoint provides insights into HTTP requests,
    including latency, status code distribution,
    request throughput, and failure statistics.

    :param from_date: Optional start datetime used to filter metrics.
    :param to_date: Optional end datetime used to filter metrics.
    :param device_id: Optional device identifier filter.
    :param db: SQLAlchemy database session dependency.
    :param current_user: Authenticated user performing the request.
    :return: Aggregated HTTP metrics response.
    """
    return get_http_overview(
        db,
        user=current_user,
        from_date=from_date,
        to_date=to_date,
        device_id=device_id,
    )


@metrics_router.get(
    "/metrics/crashes",
    response_model=list[CrashTimelineResponse],
    status_code=status.HTTP_200_OK,
)
def metrics_crashes(
    from_date: datetime | None = Query(default=None, alias="from"),
    to_date: datetime | None = Query(default=None, alias="to"),
    device_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieves application crash analytics and crash timelines.

    This endpoint returns crash occurrences collected from
    client devices, allowing analysis of stability trends
    over time.

    :param from_date: Optional start datetime used to filter metrics.
    :param to_date: Optional end datetime used to filter metrics.
    :param device_id: Optional device identifier filter.
    :param db: SQLAlchemy database session dependency.
    :param current_user: Authenticated user performing the request.
    :return: List of crash timeline analytics.
    """
    return get_crashes(
        db,
        user=current_user,
        from_date=from_date,
        to_date=to_date,
        device_id=device_id,
    )


@metrics_router.get(
    "/metrics/devices",
    response_model=list[DeviceMetricResponse],
    status_code=status.HTTP_200_OK,
)
def metrics_devices(
    from_date: datetime | None = Query(default=None, alias="from"),
    to_date: datetime | None = Query(default=None, alias="to"),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieves device-level analytics and usage metrics.

    This endpoint provides aggregated metrics grouped by
    device identifiers, supporting pagination for large
    result sets.

    :param from_date: Optional start datetime used to filter metrics.
    :param to_date: Optional end datetime used to filter metrics.
    :param limit: Maximum number of records to return.
    :param offset: Pagination offset value.
    :param db: SQLAlchemy database session dependency.
    :param current_user: Authenticated user performing the request.
    :return: List of device metric analytics.
    """
    return get_devices(
        db,
        user=current_user,
        from_date=from_date,
        to_date=to_date,
        limit=limit,
        offset=offset,
    )


@metrics_router.get(
    "/metrics/network",
    response_model=list[NetworkDistributionResponse],
    status_code=status.HTTP_200_OK,
)
def metrics_network(
    from_date: datetime | None = Query(default=None, alias="from"),
    to_date: datetime | None = Query(default=None, alias="to"),
    device_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieves network distribution analytics.

    This endpoint provides insights into network usage
    patterns such as WiFi, cellular, and offline distribution
    collected from client telemetry.

    :param from_date: Optional start datetime used to filter metrics.
    :param to_date: Optional end datetime used to filter metrics.
    :param device_id: Optional device identifier filter.
    :param db: SQLAlchemy database session dependency.
    :param current_user: Authenticated user performing the request.
    :return: List of network distribution metrics.
    """
    return get_network(
        db,
        user=current_user,
        from_date=from_date,
        to_date=to_date,
        device_id=device_id,
    )


@metrics_router.get(
    "/metrics/battery",
    response_model=list[BatteryBucketResponse],
    status_code=status.HTTP_200_OK,
)
def metrics_battery(
    from_date: datetime | None = Query(default=None, alias="from"),
    to_date: datetime | None = Query(default=None, alias="to"),
    device_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieves battery usage and battery state analytics.

    This endpoint provides telemetry related to battery
    consumption patterns and battery state distributions
    across application sessions.

    :param from_date: Optional start datetime used to filter metrics.
    :param to_date: Optional end datetime used to filter metrics.
    :param device_id: Optional device identifier filter.
    :param db: SQLAlchemy database session dependency.
    :param current_user: Authenticated user performing the request.
    :return: List of battery metric buckets.
    """
    return get_battery(
        db,
        user=current_user,
        from_date=from_date,
        to_date=to_date,
        device_id=device_id,
    )


@metrics_router.get(
    "/metrics/events/custom",
    response_model=list[CustomEventMetricResponse],
    status_code=status.HTTP_200_OK,
)
def metrics_custom_events(
    from_date: datetime | None = Query(default=None, alias="from"),
    to_date: datetime | None = Query(default=None, alias="to"),
    device_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieves custom application event analytics.

    This endpoint returns metrics related to custom-defined
    events tracked within the client application.

    :param from_date: Optional start datetime used to filter metrics.
    :param to_date: Optional end datetime used to filter metrics.
    :param device_id: Optional device identifier filter.
    :param db: SQLAlchemy database session dependency.
    :param current_user: Authenticated user performing the request.
    :return: List of custom event analytics.
    """
    return get_custom_events(
        db,
        user=current_user,
        from_date=from_date,
        to_date=to_date,
        device_id=device_id,
    )


@metrics_router.get(
    "/metrics/frame-drops",
    response_model=list[FrameDropTrendResponse],
    status_code=status.HTTP_200_OK,
)
def metrics_frame_drops(
    from_date: datetime | None = Query(default=None, alias="from"),
    to_date: datetime | None = Query(default=None, alias="to"),
    device_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieves frame drop and rendering performance analytics.

    This endpoint provides insights into UI rendering
    performance and frame stability metrics captured
    during application usage.

    :param from_date: Optional start datetime used to filter metrics.
    :param to_date: Optional end datetime used to filter metrics.
    :param device_id: Optional device identifier filter.
    :param db: SQLAlchemy database session dependency.
    :param current_user: Authenticated user performing the request.
    :return: List of frame drop trend analytics.
    """
    return get_frame_drops(
        db,
        user=current_user,
        from_date=from_date,
        to_date=to_date,
        device_id=device_id,
    )


@metrics_router.get(
    "/metrics/sessions/active",
    response_model=ActiveSessionsResponse,
    status_code=status.HTTP_200_OK,
)
def metrics_active_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieves the current number of active application sessions.

    This endpoint returns the count of active sessions
    currently observed in the telemetry dataset.

    :param db: SQLAlchemy database session dependency.
    :param current_user: Authenticated user performing the request.
    :return: Active sessions response object.
    """
    return ActiveSessionsResponse(
        activeSessions=get_active_sessions(
            db,
            user=current_user,
        )
    )


@metrics_router.delete(
    "/metrics/session/{session_id}",
    response_model=DeleteSessionMetricsResponse,
    status_code=status.HTTP_200_OK,
)
def delete_metrics_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Deletes all metrics associated with a specific session.

    This endpoint is restricted to administrator users
    and permanently removes telemetry data associated
    with the provided session identifier.

    :param session_id: Session identifier whose metrics should be deleted.
    :param db: SQLAlchemy database session dependency.
    :param current_user: Authenticated user performing the request.
    :return: Response containing number of deleted events.
    """
    require_admin(current_user)

    deleted_count = delete_session_metrics(
        db,
        user=current_user,
        session_id=session_id,
    )

    return DeleteSessionMetricsResponse(
        deletedEvents=deleted_count,
    )