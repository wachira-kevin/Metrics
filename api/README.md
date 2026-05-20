# Metrics Backend API

A robust FastAPI-based backend service for user authentication, metrics ingestion, and retrieval, featuring JWT-based security and high-performance data handling.

## 🚀 Features

- **User Authentication**: Secure signup and login with JWT tokens (access and refresh tokens).
- **Metrics Management**: Ingest and query metric events with support for large datasets.
- **Auto-Migrations**: Database schema management using Alembic.
- **Data Seeding**: Built-in script to generate large amounts of demo data for testing.
- **Containerized**: Docker support for easy deployment and consistent environments.
- **Modern Tooling**: Powered by `uv` for lightning-fast dependency management.

## 🏗️ Project Structure

The project follows a modular architecture:

- `app/api/v1/`: API route definitions for authentication and metrics.
- `app/core/`: Centralized configuration, database setup, and security utilities.
- `app/models/`: SQLAlchemy database models (Users, MetricEvents, etc.).
- `app/repositories/`: Data access layer to abstract database operations.
- `app/services/`: Business logic layer.
- `app/schemas/`: Pydantic models for data validation and serialization.
- `migrations/`: Alembic database migration scripts.
- `start.py`: Master startup script that handles migrations, seeding, and service launch.
- `seed.py`: Dedicated script for generating and inserting demo metrics.

## 🛠️ Local Setup

### Prerequisites

- **Python 3.14+**
- **uv** (Recommended): [Install uv](https://github.com/astral-sh/uv)
- **PostgreSQL**: A running instance of PostgreSQL.

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd metrics-api
   ```

2. **Set up environment variables**:
   Create a `.env` file in the root directory:
   ```env
   DATABASE_URI=postgresql://user:password@localhost:5432/metrics_db
   SECRET_KEY=your-super-secret-key
   ```

3. **Install dependencies**:
   Using `uv`:
   ```bash
   uv sync
   ```

## 🏃 Running the Application

The easiest way to start the service is using the `start.py` script, which automatically runs migrations and seeds demo data.

```bash
# Start with default seeding (300,000 records)
uv run python start.py

# Start and skip seeding
uv run python start.py --skip-seed

# Start and reset existing seed data
uv run python start.py --reset-seed --records 100000
```

The API will be available at `http://localhost:8000`.

### API Documentation

Once the service is running, you can access the interactive Swagger UI at:
`http://localhost:8000/docs`

## 🐳 Docker Setup

To run the application using Docker:

1. **Build the image**:
   ```bash
   docker build -t metrics-api .
   ```

2. **Run the container**:
   ```bash
   docker run -p 8000:8000 --env DATABASE_URI=postgresql://user:password@host.docker.internal:5432/metrics_db metrics-api
   ```
