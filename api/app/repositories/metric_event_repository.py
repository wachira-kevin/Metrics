from datetime import datetime, timezone, timedelta
from uuid import UUID

from sqlalchemy import func, cast, Integer, case, Date, true
from sqlalchemy.orm import Session

from app.core.metric_events import (
    ANR_COUNT,
    APP_START_TIME_MS,
    BATTERY_LEVEL_PCT,
    CRASH_COUNT,
    CUSTOM_EVENT,
    FRAME_DROP_COUNT,
    HTTP_ERROR_RATE,
    HTTP_LATENCY_P95_MS,
    HTTP_REQUEST_COUNT,
    LAST_SEEN,
    MEMORY_USED_MB,
    NETWORK_TYPE,
    SCREEN_VIEW,
    SESSION_DURATION_MS,
)
from app.models import MetricEvent


def _base_metric_filters(
    *,
    app_token_ids: list[UUID],
    from_date: datetime | None = None,
    to_date: datetime | None = None,
    device_id: str | None = None,
):
    """
    Builds a list of filters to be applied to metric events based on provided parameters.

    The function generates SQLAlchemy filter conditions used for querying metric events.
    Filters are constructed based on app token IDs, date ranges, and optional device ID.

    :param app_token_ids: A list of UUIDs representing application token IDs to filter by.
    :param from_date: An optional datetime specifying the start of the date range.
    :param to_date: An optional datetime specifying the end of the date range.
    :param device_id: An optional string representing the device ID to filter by.
    :return: A list of SQLAlchemy filter conditions for use in metric event queries.
    """
    filters = [MetricEvent.app_token_id.in_(app_token_ids)]

    if from_date is not None:
        filters.append(MetricEvent.timestamp >= from_date)

    if to_date is not None:
        filters.append(MetricEvent.timestamp <= to_date)

    if device_id is not None:
        filters.append(MetricEvent.device_id == device_id)

    return filters


def create_metric_events(
    db: Session,
    *,
    metric_events: list[MetricEvent],
) -> list[MetricEvent]:
    """
    Creates and persists a list of MetricEvent objects in the database.

    This function accepts a list of MetricEvent objects, adds them to the provided
    database session, commits the session to save the changes, and refreshes
    each MetricEvent object to reflect the updated state in the database. The
    list of MetricEvent objects is then returned.

    :param db: Database session used for adding, committing, and refreshing the
        MetricEvent objects.
    :type db: Session
    :param metric_events: List of MetricEvent objects to be persisted into the
        database.
    :return: List of MetricEvent objects after being committed and refreshed.
    :rtype: list[MetricEvent]
    """
    db.add_all(metric_events)
    db.commit()

    for metric_event in metric_events:
        db.refresh(metric_event)

    return metric_events


def get_metrics_summary(
    db: Session,
    *,
    app_token_ids: list[UUID],
    from_date: datetime | None,
    to_date: datetime | None,
    device_id: str | None,
) -> dict:
    """
    Retrieve a summary of various application performance metrics based on the specified filters.
    This function calculates metrics including the total number of sessions, average session
    duration, total crashes, and average application start time for the given conditions.

    :param db: The database session used to perform queries.
    :type db: Session
    :param app_token_ids: A list of unique application token identifiers to filter metrics.
    :type app_token_ids: list[UUID]
    :param from_date: An optional starting date-time to filter metrics.
    :type from_date: datetime | None
    :param to_date: An optional ending date-time to filter metrics.
    :type to_date: datetime | None
    :param device_id: An optional unique identifier of a device to filter metrics.
    :type device_id: str | None
    :return: A dictionary containing calculated performance metrics:
             - "total_sessions": Total number of sessions.
             - "avg_session_duration": Average duration of sessions.
             - "total_crashes": Total number of crashes.
             - "avg_app_start_time": Average time for application start.
    :rtype: dict
    """
    filters = _base_metric_filters(
        app_token_ids=app_token_ids,
        from_date=from_date,
        to_date=to_date,
        device_id=device_id,
    )

    total_sessions = (
        db.query(func.count(func.distinct(MetricEvent.session_id)))
        .filter(
            *filters,
            MetricEvent.session_id.isnot(None),
        )
        .scalar()
        or 0
    )

    avg_session_duration = (
        db.query(func.coalesce(func.avg(MetricEvent.value), 0.0))
        .filter(
            *filters,
            MetricEvent.event_type == SESSION_DURATION_MS,
        )
        .scalar()
        or 0.0
    )

    total_crashes = (
        db.query(func.coalesce(func.sum(MetricEvent.value), 0.0))
        .filter(
            *filters,
            MetricEvent.event_type == CRASH_COUNT,
        )
        .scalar()
        or 0.0
    )

    avg_app_start_time = (
        db.query(func.coalesce(func.avg(MetricEvent.value), 0.0))
        .filter(
            *filters,
            MetricEvent.event_type == APP_START_TIME_MS,
        )
        .scalar()
        or 0.0
    )

    return {
        "total_sessions": total_sessions,
        "avg_session_duration": float(avg_session_duration),
        "total_crashes": int(total_crashes),
        "avg_app_start_time": float(avg_app_start_time),
    }


def get_top_screens(
    db: Session,
    *,
    app_token_ids: list[UUID],
    from_date: datetime | None,
    to_date: datetime | None,
    device_id: str | None,
) -> list[dict]:
    """
    Retrieve the top screens viewed by users based on certain filters applied to the metrics data.

    The function queries the database to gather information about screen views, including the
    number of visits and the average duration spent on each screen. This data is then aggregated
    and sorted in descending order of average duration. It returns a maximum of 10 screens
    that best fit the input filters.

    :param db: Database session used to query metrics data.
    :type db: Session
    :param app_token_ids: List of application token IDs used to filter the data to specific applications.
    :type app_token_ids: list[UUID]
    :param from_date: The starting date for the data filtering. If None, no lower bound is applied.
    :type from_date: datetime | None
    :param to_date: The end date for the data filtering. If None, no upper bound is applied.
    :type to_date: datetime | None
    :param device_id: A specific device ID used to narrow down the data. If None, data is not filtered by device.
    :type device_id: str | None
    :return: A list of dictionaries containing the screen name, visit count,
             and average duration (in milliseconds) for the top screens matching the filters.
    :rtype: list[dict]
    """
    filters = _base_metric_filters(
        app_token_ids=app_token_ids,
        from_date=from_date,
        to_date=to_date,
        device_id=device_id,
    )

    screen_name = MetricEvent.attributes["screen_name"].astext

    rows = (
        db.query(
            screen_name.label("screen_name"),
            func.count(MetricEvent.id).label("visit_count"),
            func.coalesce(func.avg(MetricEvent.value), 0.0).label("avg_duration_ms"),
        )
        .filter(
            *filters,
            MetricEvent.event_type == SCREEN_VIEW,
        )
        .group_by(screen_name)
        .order_by(func.avg(MetricEvent.value).desc())
        .limit(10)
        .all()
    )

    return [
        {
            "screen_name": row.screen_name or "UNKNOWN",
            "visit_count": row.visit_count,
            "avg_duration_ms": float(row.avg_duration_ms),
        }
        for row in rows
    ]


def get_http_metrics(
    db: Session,
    *,
    app_token_ids: list[UUID],
    from_date: datetime | None,
    to_date: datetime | None,
    device_id: str | None,
) -> dict:
    """
    Fetches HTTP metrics, including total requests, error rate, average latency,
    and 95th percentile latency, based on provided filters such as app token IDs,
    date range, and device ID.

    :param db: Database session used to execute the query.
    :type db: Session
    :param app_token_ids: List of unique app token IDs to filter metrics.
    :type app_token_ids: list[UUID]
    :param from_date: Start date for the metrics query, if applicable. Accepts None.
    :type from_date: datetime | None
    :param to_date: End date for the metrics query, if applicable. Accepts None.
    :type to_date: datetime | None
    :param device_id: Optional device identifier to filter the query. Accepts None.
    :type device_id: str | None
    :return: A dictionary containing HTTP metrics:
             - 'total_requests': Total number of HTTP requests.
             - 'error_rate': Percentage of error responses (status code >= 400).
             - 'avg_latency': Average latency of HTTP requests in milliseconds.
             - 'p95_latency': 95th percentile latency of HTTP requests in milliseconds.
    :rtype: dict
    """
    filters = _base_metric_filters(
        app_token_ids=app_token_ids,
        from_date=from_date,
        to_date=to_date,
        device_id=device_id,
    )

    total_requests = (
        db.query(func.coalesce(func.sum(MetricEvent.value), 0.0))
        .filter(
            *filters,
            MetricEvent.event_type == HTTP_REQUEST_COUNT,
        )
        .scalar()
        or 0.0
    )

    error_rate = (
        db.query(func.coalesce(func.avg(MetricEvent.value), 0.0))
        .filter(
            *filters,
            MetricEvent.event_type == HTTP_ERROR_RATE,
        )
        .scalar()
        or 0.0
    )

    avg_latency = (
        db.query(func.coalesce(func.avg(MetricEvent.value), 0.0))
        .filter(
            *filters,
            MetricEvent.event_type == HTTP_LATENCY_P95_MS,
        )
        .scalar()
        or 0.0
    )

    p95_latency = (
        db.query(func.coalesce(func.percentile_cont(0.95).within_group(MetricEvent.value), 0.0))
        .filter(
            *filters,
            MetricEvent.event_type == HTTP_LATENCY_P95_MS,
        )
        .scalar()
        or 0.0
    )

    return {
        "total_requests": int(total_requests),
        "error_rate": float(error_rate),
        "avg_latency": float(avg_latency),
        "p95_latency": float(p95_latency),
    }


def get_crash_timeline(
    db: Session,
    *,
    app_token_ids: list[UUID],
    from_date: datetime | None,
    to_date: datetime | None,
    device_id: str | None,
) -> list[dict]:
    """
    Retrieve a timeline of crash and ANR (Application Not Responding) events based on provided filters.
    The function aggregates these event types over the specified date range and returns a list of
    dictionaries containing dates and their corresponding event counts.

    :param db: An instance of the SQLAlchemy session to interact with the database.
    :type db: Session

    :param app_token_ids: A list of application token identifiers used to scope the query to specific applications.
    :type app_token_ids: list[UUID]

    :param from_date: The start date from which to include events in the results. Defaults to None if not provided.
    :type from_date: datetime | None

    :param to_date: The end date until which to include events in the results. Defaults to None if not provided.
    :type to_date: datetime | None

    :param device_id: An optional device identifier to filter events by a specific device. Defaults to None.
    :type device_id: str | None

    :return: A list of dictionaries, each containing the date, crash count, and ANR count for that date.
    :rtype: list[dict]
    """
    filters = _base_metric_filters(
        app_token_ids=app_token_ids,
        from_date=from_date,
        to_date=to_date,
        device_id=device_id,
    )

    event_date = cast(MetricEvent.timestamp, Date)

    rows = (
        db.query(
            event_date.label("date"),
            func.coalesce(
                func.sum(
                    case(
                        (MetricEvent.event_type == CRASH_COUNT, MetricEvent.value),
                        else_=0,
                    )
                ),
                0,
            ).label("crash_count"),
            func.coalesce(
                func.sum(
                    case(
                        (MetricEvent.event_type == ANR_COUNT, MetricEvent.value),
                        else_=0,
                    )
                ),
                0,
            ).label("anr_count"),
        )
        .filter(
            *filters,
            MetricEvent.event_type.in_([CRASH_COUNT, ANR_COUNT]),
        )
        .group_by(event_date)
        .order_by(event_date.asc())
        .all()
    )

    return [
        {
            "date": row.date,
            "crash_count": int(row.crash_count or 0),
            "anr_count": int(row.anr_count or 0),
        }
        for row in rows
    ]


def get_device_metrics(
    db: Session,
    *,
    app_token_ids: list[UUID],
    from_date: datetime | None,
    to_date: datetime | None,
    limit: int,
    offset: int,
) -> list[dict]:
    """
    Retrieve aggregated device metrics for the specified criteria.

    This function fetches metrics for devices and aggregates data such as the number of
    sessions, crashes, and average memory usage based on the provided filters and limits.
    The results are grouped by device ID and ordered by the number of distinct sessions in
    descending order.

    :param db: The database session used for querying.
    :type db: Session
    :param app_token_ids: A list of application token IDs to filter metrics by.
    :type app_token_ids: list[UUID]
    :param from_date: The start date to filter metric events. If `None`, no start date
        filter is applied.
    :type from_date: datetime | None
    :param to_date: The end date to filter metric events. If `None`, no end date
        filter is applied.
    :type to_date: datetime | None
    :param limit: The maximum number of device metric rows to retrieve.
    :type limit: int
    :param offset: The number of device metric rows to skip before retrieving results.
    :type offset: int
    :return: A list of dictionaries where each dictionary contains the device ID,
        number of sessions, number of crashes, and average memory usage for a device.
    :rtype: list[dict]
    """
    filters = _base_metric_filters(
        app_token_ids=app_token_ids,
        from_date=from_date,
        to_date=to_date,
    )

    rows = (
        db.query(
            MetricEvent.device_id.label("device_id"),
            func.count(func.distinct(MetricEvent.session_id)).label("sessions"),
            func.coalesce(
                func.sum(
                    case(
                        (MetricEvent.event_type == CRASH_COUNT, MetricEvent.value),
                        else_=0,
                    )
                ),
                0,
            ).label("crashes"),
            func.coalesce(
                func.avg(
                    case(
                        (MetricEvent.event_type == MEMORY_USED_MB, MetricEvent.value),
                        else_=None,
                    )
                ),
                0.0,
            ).label("avg_memory"),
        )
        .filter(
            *filters,
            MetricEvent.device_id.isnot(None),
        )
        .group_by(MetricEvent.device_id)
        .order_by(func.count(func.distinct(MetricEvent.session_id)).desc())
        .limit(limit)
        .offset(offset)
        .all()
    )

    return [
        {
            "device_id": row.device_id,
            "sessions": row.sessions or 0,
            "crashes": int(row.crashes or 0),
            "avg_memory": float(row.avg_memory),
        }
        for row in rows
    ]


def get_network_distribution(
    db: Session,
    *,
    app_token_ids: list[UUID],
    from_date: datetime | None,
    to_date: datetime | None,
    device_id: str | None,
) -> list[dict]:
    """
    Retrieves the distribution of network types for session start events within the specified
    criteria. The function calculates the count and percentage of sessions for each network
    type, based on provided filters such as application token IDs, date range, and device ID.

    :param db: Database session object used to query the data.
    :param app_token_ids: List of UUIDs identifying the applications to filter by.
    :param from_date: Optional start date for filtering sessions.
    :param to_date: Optional end date for filtering sessions.
    :param device_id: Optional string representing a specific device ID for filtering.
    :return: List of dictionaries, each containing the network type, the count of sessions,
             and the percentage representation for the network type across all sessions.
    """
    filters = _base_metric_filters(
        app_token_ids=app_token_ids,
        from_date=from_date,
        to_date=to_date,
        device_id=device_id,
    )

    network_type = MetricEvent.attributes["network_type"].astext

    rows = (
        db.query(
            network_type.label("network_type"),
            func.count(MetricEvent.id).label("count"),
        )
        .filter(
            *filters,
            MetricEvent.event_type == NETWORK_TYPE,
        )
        .group_by(network_type)
        .all()
    )

    total = sum(row.count for row in rows) or 1

    return [
        {
            "network_type": row.network_type or "UNKNOWN",
            "count": row.count,
            "percentage": round((row.count / total) * 100, 2),
        }
        for row in rows
    ]


def get_battery_distribution(
    db: Session,
    *,
    app_token_ids: list[UUID],
    from_date: datetime | None,
    to_date: datetime | None,
    device_id: str | None,
) -> list[dict]:
    """
    Retrieve the distribution of battery levels in defined buckets based on session start
    events for the specified filters.

    The function queries a database to group session start events by battery level buckets,
    counts the occurrences, and returns the resulting distribution.

    :param db: Database session instance used to run the query.
    :type db: Session
    :param app_token_ids: List of application token IDs to filter session events by.
    :type app_token_ids: list[UUID]
    :param from_date: Start date for filtering session events, or None if not specified.
    :type from_date: datetime | None
    :param to_date: End date for filtering session events, or None if not specified.
    :type to_date: datetime | None
    :param device_id: Unique identifier for the device to filter session events by, or None
        if not specified.
    :type device_id: str | None
    :return: A list of dictionaries where each dictionary represents a battery level
        bucket. Each dictionary contains keys for the bucket start (integer),
        bucket end (integer), and session count (integer).
    :rtype: list[dict]
    """
    filters = _base_metric_filters(
        app_token_ids=app_token_ids,
        from_date=from_date,
        to_date=to_date,
        device_id=device_id,
    )

    bucket_start = cast(func.floor(MetricEvent.value / 10) * 10, Integer)

    rows = (
        db.query(
            bucket_start.label("bucket_start"),
            func.count(func.distinct(MetricEvent.session_id)).label("session_count"),
        )
        .filter(
            *filters,
            MetricEvent.event_type == BATTERY_LEVEL_PCT,
        )
        .group_by(bucket_start)
        .order_by(bucket_start.asc())
        .all()
    )

    return [
        {
            "bucket_start": row.bucket_start,
            "bucket_end": min(row.bucket_start + 9, 100),
            "session_count": row.session_count,
        }
        for row in rows
    ]


def get_custom_event_metrics(
    db: Session,
    *,
    app_token_ids: list[UUID],
    from_date: datetime | None,
    to_date: datetime | None,
    device_id: str | None,
) -> list[dict]:
    """
    Fetches custom event metrics based on the specified filters. This includes analyzing
    custom attributes of events and computing their occurrences. The function applies
    various filters such as application token IDs, event dates, and device ID to ensure
    results are scoped appropriately.

    :param db: Database session used to query and retrieve data.
    :type db: Session

    :param app_token_ids: A list of app token UUIDs to filter the events.
    :type app_token_ids: list[UUID]

    :param from_date: The start date from which to filter events. If None, no lower date bound is applied.
    :type from_date: datetime | None

    :param to_date: The end date until which to filter events. If None, no upper date bound is applied.
    :type to_date: datetime | None

    :param device_id: An optional device ID used to further filter events. If None, results are not filtered by device ID.
    :type device_id: str | None

    :return: A list of dictionaries, where each dictionary represents a custom attribute key,
             its corresponding value, and the frequency of occurrence in the dataset.
    :rtype: list[dict]
    """
    filters = _base_metric_filters(
        app_token_ids=app_token_ids,
        from_date=from_date,
        to_date=to_date,
        device_id=device_id,
    )

    custom_attributes = func.jsonb_each_text(MetricEvent.attributes).table_valued(
        "key",
        "value",
    ).render_derived()

    query_rows = (
        db.query(
            custom_attributes.c.key.label("key"),
            custom_attributes.c.value.label("value"),
            func.count().label("frequency"),
        )
        .select_from(MetricEvent)
        .join(custom_attributes, true())
        .filter(
            *filters,
            MetricEvent.event_type == CUSTOM_EVENT,
        )
        .group_by(custom_attributes.c.key, custom_attributes.c.value)
        .order_by(func.count().desc())
        .all()
    )

    return [
        {
            "key": row.key,
            "value": row.value,
            "frequency": row.frequency,
        }
        for row in query_rows
    ]


def get_frame_drop_trend(
    db: Session,
    *,
    app_token_ids: list[UUID],
    from_date: datetime | None,
    to_date: datetime | None,
    device_id: str | None,
) -> list[dict]:
    """
    Fetches the frame drop trend data based on specified filters and calculates the
    average frame drop count for each screen name and date.

    The function queries the `MetricEvent` table to compute the average frame drop count
    grouped by `event_date` and `screen_name`. It applies filters provided as input
    parameters to narrow down the dataset.

    :param db: The database session to use for querying.
    :type db: Session
    :param app_token_ids: A list of unique application token identifiers to filter the data.
    :type app_token_ids: list[UUID]
    :param from_date: The start date for filtering the frame drop events. May be None.
    :type from_date: datetime | None
    :param to_date: The end date for filtering the frame drop events. May be None.
    :type to_date: datetime | None
    :param device_id: The device identifier to filter data for a specific device. May be None.
    :type device_id: str | None
    :return: A list of dictionaries containing the frame drop trend with keys:
             'date', 'screen_name', and 'avg_frame_drop_count'.
    :rtype: list[dict]
    """
    filters = _base_metric_filters(
        app_token_ids=app_token_ids,
        from_date=from_date,
        to_date=to_date,
        device_id=device_id,
    )

    event_date = cast(MetricEvent.timestamp, Date)
    screen_name = MetricEvent.attributes["screen_name"].astext

    rows = (
        db.query(
            event_date.label("date"),
            screen_name.label("screen_name"),
            func.coalesce(func.avg(MetricEvent.value), 0.0).label("avg_frame_drop_count"),
        )
        .filter(
            *filters,
            MetricEvent.event_type == FRAME_DROP_COUNT,
        )
        .group_by(event_date, screen_name)
        .order_by(event_date.asc(), screen_name.asc())
        .all()
    )

    return [
        {
            "date": row.date,
            "screen_name": row.screen_name or "UNKNOWN",
            "avg_frame_drop_count": float(row.avg_frame_drop_count),
        }
        for row in rows
    ]


def get_active_sessions_count(
    db: Session,
    *,
    app_token_ids: list[UUID],
) -> int:
    """
    Get the count of active sessions within the last 5 minutes.

    This function calculates the number of active sessions for a specific set of
    application tokens, based on unique session IDs found in the database. A session
    is considered active if it has a last seen event (`session.last_seen`) within
    the last five minutes.

    :param db: A SQLAlchemy Session instance used to perform the database query.
    :type db: Session
    :param app_token_ids: A list of app token IDs used to filter the relevant sessions.
    :return: The count of active sessions with `session.last_seen` events in the past
        five minutes. Returns 0 if no active sessions are found.
    :rtype: int
    """
    five_minutes_ago = datetime.now(timezone.utc) - timedelta(minutes=5)

    return (
        db.query(func.count(func.distinct(MetricEvent.session_id)))
        .filter(
            MetricEvent.app_token_id.in_(app_token_ids),
            MetricEvent.session_id.isnot(None),
            MetricEvent.event_type == LAST_SEEN,
            MetricEvent.timestamp >= five_minutes_ago,
        )
        .scalar()
        or 0
    )


def delete_session_events(
    db: Session,
    *,
    app_token_ids: list[UUID],
    session_id: str,
) -> int:
    """
    Deletes session events associated with a specific session ID and list of app token IDs
    from the database.

    This function removes `MetricEvent` entries from the database where the app token IDs
    and session ID match the provided parameters.

    :param db: SQLAlchemy database session used to perform the delete operation.
    :type db: Session
    :param app_token_ids: List of app token IDs to match for deletion.
    :type app_token_ids: list[UUID]
    :param session_id: The session ID used as a filter criterion for deleting events.
    :type session_id: str
    :return: The number of rows deleted from the database.
    :rtype: int
    """
    deleted_count = (
        db.query(MetricEvent)
        .filter(
            MetricEvent.app_token_id.in_(app_token_ids),
            MetricEvent.session_id == session_id,
        )
        .delete(synchronize_session=False)
    )

    db.commit()

    return deleted_count