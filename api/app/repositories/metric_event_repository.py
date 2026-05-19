from sqlalchemy.orm import Session

from app.models import MetricEvent


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