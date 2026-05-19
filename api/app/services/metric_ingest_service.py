from sqlalchemy.orm import Session

from app.models import AppToken, MetricEvent
from app.repositories.metric_event_repository import create_metric_events
from app.schemas.metrics import MetricBatchIngestRequest, MetricBatchIngestResponse


def ingest_metric_events(
    db: Session,
    *,
    app_token: AppToken,
    payload: MetricBatchIngestRequest,
) -> MetricBatchIngestResponse:
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