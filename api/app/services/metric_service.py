from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import AppToken, MetricEvent, User
from app.repositories.app_token_repository import get_app_token_ids_for_user
from app.repositories.metric_event_repository import create_metric_events, get_metrics_summary, get_top_screens, \
    get_http_metrics, get_crash_timeline, get_device_metrics, get_network_distribution, get_battery_distribution, \
    get_custom_event_metrics, get_frame_drop_trend, get_active_sessions_count, delete_session_events
from app.schemas.metrics import MetricBatchIngestRequest, MetricBatchIngestResponse


def _get_user_app_token_ids(db: Session, user: User) -> list[UUID]:
    """
    Fetches the list of application token IDs associated with a specific user.

    This function retrieves the application token IDs linked to the user
    by their unique identifier.

    :param db: The database session used to perform the query.
    :type db: Session
    :param user: The user object for which the token IDs are being retrieved.
    :type user: User
    :return: A list of UUIDs representing the application token IDs tied to the user.
    :rtype: list[UUID]
    """
    return get_app_token_ids_for_user(db, user.id)


def ingest_metric_events(
    db: Session,
    *,
    app_token: AppToken,
    payload: MetricBatchIngestRequest,
) -> MetricBatchIngestResponse:
    """
    Ingests a batch of metric events into the database.

    This function processes a collection of metric events provided in the request payload
    and stores them in the database. Each metric event is linked to the specified
    application token and includes various details such as event type, value, unit,
    timestamp, session ID, device ID, and additional attributes. After all events are
    persisted, the function returns a response summarizing the number of events accepted.

    :param db: An instance of the database session used for persisting metric events.
    :type db: Session
    :param app_token: The application token associated with the metric events to be
        ingested.
    :type app_token: AppToken
    :param payload: The batch of metric events to be processed and stored.
    :type payload: MetricBatchIngestRequest
    :return: A response containing the number of metric events successfully accepted
        and persisted.
    :rtype: MetricBatchIngestResponse
    """
    metric_events = [
        MetricEvent(
            app_token_id=app_token.id,
            event_type=event.event_type,
            value=event.value,
            unit=event.unit,
            timestamp=event.timestamp,
            session_id=event.session_id,
            device_id=event.device_id,
            attributes=event.attributes,
        )
        for event in payload.events
    ]

    create_metric_events(db, metric_events=metric_events)

    return MetricBatchIngestResponse(
        accepted=len(metric_events),
    )


def get_summary(
    db: Session,
    *,
    user: User,
    from_date: datetime | None,
    to_date: datetime | None,
    device_id: str | None,
) -> dict:
    """
    Retrieve a summary of metrics for a given user and optional filtering criteria.

    This function fetches summarized metrics for a specified user within an optional
    date range and for an optional device identifier. The function delegates the
    summary computation logic to `get_metrics_summary`. The summarized metrics are
    returned as a dictionary.

    :param db: Database session used to fetch data.
    :type db: Session
    :param user: The user for whom the metrics summary is being generated.
    :type user: User
    :param from_date: Start of the date range for filtering metrics. Defaults to None.
    :type from_date: datetime or None
    :param to_date: End of the date range for filtering metrics. Defaults to None.
    :type to_date: datetime or None
    :param device_id: Optional identifier for filtering metrics by a specific device.
        If not provided, metrics across all devices are included.
    :type device_id: str or None
    :return: A dictionary containing the metrics summary for the specified
        user and filtering criteria.
    :rtype: dict
    """
    return get_metrics_summary(
        db,
        app_token_ids=_get_user_app_token_ids(db, user),
        from_date=from_date,
        to_date=to_date,
        device_id=device_id,
    )


def get_screens(
    db: Session,
    *,
    user: User,
    from_date: datetime | None,
    to_date: datetime | None,
    device_id: str | None,
) -> list[dict]:
    """
    Retrieve top screens data for a given user within the specified date range and device ID.

    This function obtains information about the top screens accessed by a user. It filters the data
    based on the provided date range and device ID, if specified.

    :param db: A database session used for querying data.
    :type db: Session
    :param user: The user object for whom screen data is being retrieved.
    :type user: User
    :param from_date: The start date for filtering screen data, or None for no lower boundary.
    :type from_date: datetime | None
    :param to_date: The end date for filtering screen data, or None for no upper boundary.
    :type to_date: datetime | None
    :param device_id: The ID of the device to filter the screen data, or None for no device-specific filtering.
    :type device_id: str | None
    :return: A list of dictionaries containing screen data information.
    :rtype: list[dict]
    """
    return get_top_screens(
        db,
        app_token_ids=_get_user_app_token_ids(db, user),
        from_date=from_date,
        to_date=to_date,
        device_id=device_id,
    )


def get_http_overview(
    db: Session,
    *,
    user: User,
    from_date: datetime | None,
    to_date: datetime | None,
    device_id: str | None,
) -> dict:
    """
    Retrieve an overview of HTTP metrics for the specified user, optionally filtered by date range
    or device ID. The method gathers data based on the user's app token IDs and related metrics.

    :param db: The database session used for querying data.
    :type db: Session
    :param user: The user for whom HTTP metrics data is being retrieved.
    :type user: User
    :param from_date: The start date for filtering metrics. Can be None for no lower bound.
    :type from_date: datetime | None
    :param to_date: The end date for filtering metrics. Can be None for no upper bound.
    :type to_date: datetime | None
    :param device_id: The identifier of a specific device to filter metrics by. Defaults to None.
    :type device_id: str | None
    :return: A dictionary containing the HTTP metrics overview data for the specified period and
        device, based on the user's app tokens.
    :rtype: dict
    """
    return get_http_metrics(
        db,
        app_token_ids=_get_user_app_token_ids(db, user),
        from_date=from_date,
        to_date=to_date,
        device_id=device_id,
    )


def get_crashes(
    db: Session,
    *,
    user: User,
    from_date: datetime | None,
    to_date: datetime | None,
    device_id: str | None,
) -> list[dict]:
    """
    Fetches crash data within the specified time range and optionally filters it by device ID.

    This function retrieves a timeline of crash events for a user's applications,
    allowing optional filtering by date range and/or device ID. It utilizes the
    user's application token IDs to identify the relevant data.

    :param db: Database session for accessing the datastore.
    :type db: Session
    :param user: The user whose application crash data is to be retrieved.
    :type user: User
    :param from_date: Start of the date range for filtering the crash data.
        This parameter is optional.
    :type from_date: datetime | None
    :param to_date: End of the date range for filtering the crash data.
        This parameter is optional.
    :type to_date: datetime | None
    :param device_id: Optional parameter to filter crash events by device ID.
    :type device_id: str | None
    :return: A list of dictionaries containing the crash event data for the user's
        applications after applying the specified filters.
    :rtype: list[dict]
    """
    return get_crash_timeline(
        db,
        app_token_ids=_get_user_app_token_ids(db, user),
        from_date=from_date,
        to_date=to_date,
        device_id=device_id,
    )


def get_devices(
    db: Session,
    *,
    user: User,
    from_date: datetime | None,
    to_date: datetime | None,
    limit: int,
    offset: int,
) -> list[dict]:
    """
    Fetches a list of devices and their respective metrics based on the given parameters. This function retrieves
    device information within a specified date range and applies pagination controls using limit and offset.

    :param db: Database session to interact with the database.
    :type db: Session
    :param user: The user whose app token IDs will be used for filtering device metrics.
    :type user: User
    :param from_date: Start date for retrieving device metrics. If None, no lower date bound is applied.
    :type from_date: datetime | None
    :param to_date: End date for retrieving device metrics. If None, no upper date bound is applied.
    :type to_date: datetime | None
    :param limit: Maximum number of device metrics to retrieve.
    :type limit: int
    :param offset: Number of device metrics to skip before starting retrieval.
    :type offset: int
    :return: A list of dictionaries containing metrics for the requested devices.
    :rtype: list[dict]
    """
    return get_device_metrics(
        db,
        app_token_ids=_get_user_app_token_ids(db, user),
        from_date=from_date,
        to_date=to_date,
        limit=limit,
        offset=offset,
    )


def get_network(
    db: Session,
    *,
    user: User,
    from_date: datetime | None,
    to_date: datetime | None,
    device_id: str | None,
) -> list[dict]:
    """
    Fetches the network distribution for a user's applications within the
    specified date range and optionally filters by device ID.

    This function retrieves network-related data based on the provided user
    context, date range, and device identifier. It consolidates the
    information and returns a list of dictionaries representing the network
    distribution.

    :param db: Database session used to query data.
    :type db: Session
    :param user: The user for whom the network distribution data is being retrieved.
    :type user: User
    :param from_date: The start date of the range for fetching data. If None, no lower bound is applied.
    :type from_date: datetime | None
    :param to_date: The end date of the range for fetching data. If None, no upper bound is applied.
    :type to_date: datetime | None
    :param device_id: Optional device identifier to filter the network data. If None, no filtering by device is applied.
    :type device_id: str | None
    :return: A list of dictionaries representing the network distribution data.
    :rtype: list[dict]
    """
    return get_network_distribution(
        db,
        app_token_ids=_get_user_app_token_ids(db, user),
        from_date=from_date,
        to_date=to_date,
        device_id=device_id,
    )


def get_battery(
    db: Session,
    *,
    user: User,
    from_date: datetime | None,
    to_date: datetime | None,
    device_id: str | None,
) -> list[dict]:
    """
    Fetches battery distribution data for a specific user and optional filters.

    This function retrieves the battery distribution data for a user by utilizing their
    app token IDs and applying optional filters such as date range and device ID.
    It communicates with the underlying database to collect and return the necessary data
    as a list of dictionaries.

    :param db: Represents the database session to perform queries.
    :type db: Session
    :param user: The user whose battery data is being retrieved.
    :type user: User
    :param from_date: Start date filter for the data, if provided.
    :type from_date: datetime or None
    :param to_date: End date filter for the data, if provided.
    :type to_date: datetime or None
    :param device_id: Optional unique identifier of the device to filter the data.
    :type device_id: str or None
    :return: A list of dictionaries containing the battery distribution data.
    :rtype: list[dict]
    """
    return get_battery_distribution(
        db,
        app_token_ids=_get_user_app_token_ids(db, user),
        from_date=from_date,
        to_date=to_date,
        device_id=device_id,
    )


def get_custom_events(
    db: Session,
    *,
    user: User,
    from_date: datetime | None,
    to_date: datetime | None,
    device_id: str | None,
) -> list[dict]:
    """
    Retrieve custom events for a specified user within an optional date range and device ID.

    This function fetches custom event metrics by using the user context, date range, and
    an optional device identifier. The events are retrieved from the database and
    returned as a list of dictionaries.

    :param db: Database session used to query custom events.
    :type db: Session
    :param user: The User object representing the current user whose events need to be fetched.
    :type user: User
    :param from_date: The start date for filtering events. Can be None to include all events
        up to the specified `to_date`.
    :type from_date: datetime | None
    :param to_date: The end date for filtering events. Can be None to include all events
        from the specified `from_date` onwards.
    :type to_date: datetime | None
    :param device_id: Optional device identifier for narrowing down events to a specific device.
    :type device_id: str | None
    :return: A list of dictionaries containing custom event data for the specified filters.
    :rtype: list[dict]
    """
    return get_custom_event_metrics(
        db,
        app_token_ids=_get_user_app_token_ids(db, user),
        from_date=from_date,
        to_date=to_date,
        device_id=device_id,
    )


def get_frame_drops(
    db: Session,
    *,
    user: User,
    from_date: datetime | None,
    to_date: datetime | None,
    device_id: str | None,
) -> list[dict]:
    """
    Retrieve frame drop data trends for the specified user and device within a given date range.

    This function processes and returns a list of frame drop trends by extracting relevant
    data filtered by the user's application tokens, date range, and device identifier.

    :param db: Database session instance for querying the data.
    :type db: Session
    :param user: The user for whom the frame drop trends are to be retrieved.
    :type user: User
    :param from_date: Start of the date range for filtering frame drops. Defaults to None.
    :type from_date: datetime | None
    :param to_date: End of the date range for filtering frame drops. Defaults to None.
    :type to_date: datetime | None
    :param device_id: Identifier of the device for filtering frame drops. Defaults to None.
    :type device_id: str | None
    :return: A list of dictionaries representing frame drop trends.
    :rtype: list[dict]
    """
    return get_frame_drop_trend(
        db,
        app_token_ids=_get_user_app_token_ids(db, user),
        from_date=from_date,
        to_date=to_date,
        device_id=device_id,
    )


def get_active_sessions(
    db: Session,
    *,
    user: User,
) -> int:
    """
    Fetches the number of active sessions for a specified user.

    This function calculates and returns the total count of active sessions
    associated with the given user. It internally utilizes the user's app token
    data to determine the relevant active session information.

    :param db: Database session used to query the active sessions.
    :type db: Session
    :param user: The user for which active sessions are to be calculated.
    :type user: User
    :return: The count of active sessions for the specified user.
    :rtype: int
    """
    return get_active_sessions_count(
        db,
        app_token_ids=_get_user_app_token_ids(db, user),
    )


def delete_session_metrics(
    db: Session,
    *,
    user: User,
    session_id: str,
) -> int:
    """
    Deletes session metrics associated with the given session ID and user.

    This function handles the deletion of session metrics by first
    retrieving the user's app token IDs and then proceeding to
    remove the relevant session events.

    :param db: The database session used for querying and deletion operations.
    :type db: Session
    :param user: The user for whom the session metrics need to be deleted.
    :type user: User
    :param session_id: The unique identifier of the session to be deleted.
    :type session_id: str
    :return: The number of deleted rows from the session events table.
    :rtype: int
    """
    return delete_session_events(
        db,
        app_token_ids=_get_user_app_token_ids(db, user),
        session_id=session_id,
    )