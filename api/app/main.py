from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.database import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles startup and shutdown lifecycle events.
    """

    # -----------------------------------------------------
    # Startup
    # -----------------------------------------------------
    print("🚀 Starting Metrics API...")

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        print("✅ Database connection established")

    except Exception as e:
        print("❌ Failed to connect to database")
        print(str(e))
        raise e

    yield

    # -----------------------------------------------------
    # Shutdown
    # -----------------------------------------------------
    print("🛑 Shutting down Metrics API...")

    engine.dispose()

    print("✅ Database connections closed")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

app.include_router(
    api_router,
    prefix="/api/v1"
)


@app.get("/")
async def root():
    return {
        "service": settings.APP_NAME,
        "status": "running"
    }