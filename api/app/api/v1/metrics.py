from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.app_token import get_current_app_token
from app.models import AppToken
from app.schemas.metrics import MetricBatchIngestRequest, MetricBatchIngestResponse
from app.services.metric_ingest_service import ingest_metric_events

metrics_router = APIRouter(tags=["metrics"])


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