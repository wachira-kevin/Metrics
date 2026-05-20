import argparse
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from sqlalchemy.exc import IntegrityError

from app.core.database import SessionLocal
from app.core.security import hash_app_token, hash_password
from app.models import AppToken, MetricEvent, User

APP_START_TIME_MS = "app_start_time_ms"
SESSION_DURATION_MS = "session_duration_ms"
SCREEN_VIEW = "screen_view"

HTTP_REQUEST_COUNT = "http_request_count"
HTTP_ERROR_RATE = "http_error_rate"
HTTP_LATENCY_P95_MS = "http_latency_p95_ms"

CRASH_COUNT = "crash_count"
ANR_COUNT = "anr_count"

MEMORY_USED_MB = "memory_used_mb"
BATTERY_LEVEL_PCT = "battery_level_pct"
NETWORK_TYPE = "network_type"

FRAME_DROP_COUNT = "frame_drop_count"
CUSTOM_EVENT = "custom_event"

LAST_SEEN = "last_seen"

DEFAULT_TOTAL_RECORDS = 300_000
DEFAULT_BATCH_SIZE = 5_000

DEMO_PASSWORD = "password123"

DEMO_USERS = [
    {
        "email": "admin@example.com",
        "username": "admin",
        "role": "admin",
        "tokens": [
            {
                "raw_token": "admin-demo-token",
                "label": "Admin Demo Token",
            },
        ],
    },
    {
        "email": "user1@example.com",
        "username": "user1",
        "role": "user",
        "tokens": [
            {
                "raw_token": "user1-android-token",
                "label": "User 1 Android Token",
            },
            {
                "raw_token": "user1-ios-token",
                "label": "User 1 iOS Token",
            },
            {
                "raw_token": "user1-staging-token",
                "label": "User 1 Staging Token",
            },
        ],
    },
    {
        "email": "user2@example.com",
        "username": "user2",
        "role": "user",
        "tokens": [
            {
                "raw_token": "user2-android-token",
                "label": "User 2 Android Token",
            },
            {
                "raw_token": "user2-ios-token",
                "label": "User 2 iOS Token",
            },
            {
                "raw_token": "user2-production-token",
                "label": "User 2 Production Token",
            },
        ],
    },
]

SCREEN_NAMES = [
    "SplashActivity",
    "LoginActivity",
    "HomeActivity",
    "DashboardActivity",
    "SearchActivity",
    "ProductDetailsActivity",
    "CheckoutActivity",
    "ProfileActivity",
    "SettingsActivity",
    "NotificationsActivity",
    "ReportsActivity",
    "HelpActivity",
]

NETWORK_TYPES = ["WIFI", "CELLULAR", "NONE"]

CUSTOM_EVENT_KEYS = [
    "button",
    "plan",
    "source",
    "campaign",
    "feature",
    "country",
    "experiment",
    "payment_method",
    "screen",
]

CUSTOM_EVENT_VALUES = [
    "checkout",
    "subscribe",
    "cancel",
    "premium",
    "free",
    "trial",
    "organic",
    "ads",
    "enabled",
    "disabled",
    "KE",
    "US",
    "GB",
    "card",
    "mpesa",
    "paypal",
    "home",
    "search",
    "profile",
]

EVENT_TYPES = [
    APP_START_TIME_MS,
    SESSION_DURATION_MS,
    SCREEN_VIEW,
    HTTP_REQUEST_COUNT,
    HTTP_ERROR_RATE,
    HTTP_LATENCY_P95_MS,
    CRASH_COUNT,
    ANR_COUNT,
    MEMORY_USED_MB,
    BATTERY_LEVEL_PCT,
    NETWORK_TYPE,
    FRAME_DROP_COUNT,
    CUSTOM_EVENT,
    LAST_SEEN,
]

EVENT_WEIGHTS = [
    4,   # app_start_time_ms
    8,   # session_duration_ms
    22,  # screen_view
    10,  # http_request_count
    7,   # http_error_rate
    7,   # http_latency_p95_ms
    2,   # crash_count
    1,   # anr_count
    9,   # memory_used_mb
    8,   # battery_level_pct
    8,   # network_type
    6,   # frame_drop_count
    4,   # custom_event
    12,  # last_seen
]


def get_or_create_user(db, *, email: str, username: str, role: str) -> User:
    existing_user = db.query(User).filter(User.email == email).first()

    if existing_user is not None:
        return existing_user

    user = User(
        email=email,
        username=username,
        hashed_password=hash_password(DEMO_PASSWORD),
        role=role,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def get_or_create_app_token(
    db,
    *,
    user: User,
    raw_token: str,
    label: str,
) -> AppToken:
    token_hash = hash_app_token(raw_token)

    existing_token = (
        db.query(AppToken)
        .filter(AppToken.token_hash == token_hash)
        .first()
    )

    if existing_token is not None:
        return existing_token

    app_token = AppToken(
        user_id=user.id,
        token_hash=token_hash,
        label=label,
    )

    db.add(app_token)
    db.commit()
    db.refresh(app_token)

    return app_token


def seed_users_and_tokens(db) -> list[AppToken]:
    app_tokens: list[AppToken] = []

    print("Creating demo users and app tokens...")

    for user_definition in DEMO_USERS:
        user = get_or_create_user(
            db,
            email=user_definition["email"],
            username=user_definition["username"],
            role=user_definition["role"],
        )

        for token_definition in user_definition["tokens"]:
            app_token = get_or_create_app_token(
                db,
                user=user,
                raw_token=token_definition["raw_token"],
                label=token_definition["label"],
            )
            app_tokens.append(app_token)

    print("Demo accounts:")
    print("")
    for user_definition in DEMO_USERS:
        print(f"  {user_definition['role'].upper()}:")
        print(f"    email:    {user_definition['email']}")
        print(f"    username: {user_definition['username']}")
        print(f"    password: {DEMO_PASSWORD}")
        print("    app tokens:")
        for token_definition in user_definition["tokens"]:
            print(f"      - {token_definition['raw_token']} ({token_definition['label']})")
        print("")

    return app_tokens


def random_timestamp(days_back: int) -> datetime:
    now = datetime.now(timezone.utc)
    random_days = random.randint(0, days_back)
    random_seconds = random.randint(0, 86_400)

    return now - timedelta(days=random_days, seconds=random_seconds)


def random_device_id(device_count: int) -> str:
    return f"device-{random.randint(1, device_count):05d}"


def random_session_id(session_count: int) -> str:
    return f"session-{random.randint(1, session_count):08d}"


def build_custom_event_attributes() -> dict[str, str]:
    attribute_count = random.randint(1, 4)
    attributes: dict[str, str] = {}

    for _ in range(attribute_count):
        attributes[random.choice(CUSTOM_EVENT_KEYS)] = random.choice(CUSTOM_EVENT_VALUES)

    return attributes


def build_metric_payload(event_type: str) -> tuple[float, str | None, dict[str, Any]]:
    value: float
    unit: str | None = None
    attributes: dict[str, Any] = {}

    if event_type == APP_START_TIME_MS:
        value = float(random.randint(150, 6_000))
        unit = "ms"

    elif event_type == SESSION_DURATION_MS:
        value = float(random.randint(5_000, 1_800_000))
        unit = "ms"

    elif event_type == SCREEN_VIEW:
        value = float(random.randint(300, 180_000))
        unit = "ms"
        attributes = {
            "screen_name": random.choice(SCREEN_NAMES),
        }

    elif event_type == HTTP_REQUEST_COUNT:
        value = float(random.randint(1, 250))
        unit = "count"

    elif event_type == HTTP_ERROR_RATE:
        value = round(random.uniform(0, 35), 2)
        unit = "%"

    elif event_type == HTTP_LATENCY_P95_MS:
        value = float(random.randint(40, 5_000))
        unit = "ms"

    elif event_type == CRASH_COUNT:
        value = float(random.choices([0, 1, 2, 3], weights=[92, 6, 1.5, 0.5], k=1)[0])
        unit = "count"

    elif event_type == ANR_COUNT:
        value = float(random.choices([0, 1, 2], weights=[96, 3.5, 0.5], k=1)[0])
        unit = "count"

    elif event_type == MEMORY_USED_MB:
        value = round(random.uniform(64, 1_800), 2)
        unit = "MB"

    elif event_type == BATTERY_LEVEL_PCT:
        value = round(random.uniform(1, 100), 2)
        unit = "%"

    elif event_type == NETWORK_TYPE:
        value = 1.0
        attributes = {
            "network_type": random.choices(
                NETWORK_TYPES,
                weights=[65, 30, 5],
                k=1,
            )[0],
        }

    elif event_type == FRAME_DROP_COUNT:
        value = float(random.randint(0, 120))
        unit = "count"
        attributes = {
            "screen_name": random.choice(SCREEN_NAMES),
        }

    elif event_type == CUSTOM_EVENT:
        value = 1.0
        attributes = build_custom_event_attributes()

    elif event_type == LAST_SEEN:
        value = 1.0
        unit = "count"

    else:
        value = 1.0

    return value, unit, attributes


def build_metric_event(
    *,
    app_token_id,
    days_back: int,
    device_count: int,
    session_count: int,
) -> MetricEvent:
    event_type = random.choices(
        EVENT_TYPES,
        weights=EVENT_WEIGHTS,
        k=1,
    )[0]

    value, unit, attributes = build_metric_payload(event_type)

    return MetricEvent(
        app_token_id=app_token_id,
        event_type=event_type,
        value=value,
        unit=unit,
        timestamp=random_timestamp(days_back),
        session_id=random_session_id(session_count),
        device_id=random_device_id(device_count),
        attributes=attributes,
    )


def seed_metric_events(
    db,
    *,
    app_tokens: list[AppToken],
    total_records: int,
    batch_size: int,
    days_back: int,
    device_count: int,
    session_count: int,
) -> None:
    if not app_tokens:
        raise RuntimeError("No app tokens found. Cannot seed metric events.")

    inserted = 0

    print(f"Seeding {total_records:,} metric events...")
    print(f"Batch size: {batch_size:,}")
    print("")

    while inserted < total_records:
        current_batch_size = min(batch_size, total_records - inserted)

        batch = [
            build_metric_event(
                app_token_id=random.choice(app_tokens).id,
                days_back=days_back,
                device_count=device_count,
                session_count=session_count,
            )
            for _ in range(current_batch_size)
        ]

        db.bulk_save_objects(batch)
        db.commit()

        inserted += current_batch_size

        print(f"Inserted {inserted:,}/{total_records:,} metric events")

    print("")
    print("Metric event seeding complete.")


def delete_existing_demo_data(db) -> None:
    demo_emails = [user["email"] for user in DEMO_USERS]

    demo_users = db.query(User).filter(User.email.in_(demo_emails)).all()
    demo_user_ids = [user.id for user in demo_users]

    if not demo_user_ids:
        print("No existing demo data found.")
        return

    demo_app_tokens = (
        db.query(AppToken)
        .filter(AppToken.user_id.in_(demo_user_ids))
        .all()
    )
    demo_app_token_ids = [app_token.id for app_token in demo_app_tokens]

    print("Deleting existing demo metric events, app tokens, and users...")

    if demo_app_token_ids:
        db.query(MetricEvent).filter(
            MetricEvent.app_token_id.in_(demo_app_token_ids)
        ).delete(synchronize_session=False)

    db.query(AppToken).filter(
        AppToken.user_id.in_(demo_user_ids)
    ).delete(synchronize_session=False)

    db.query(User).filter(
        User.id.in_(demo_user_ids)
    ).delete(synchronize_session=False)

    db.commit()

    print("Existing demo data deleted.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Seed demo users, app tokens, and metric events."
    )

    parser.add_argument(
        "--records",
        type=int,
        default=DEFAULT_TOTAL_RECORDS,
        help=f"Number of metric events to create. Default: {DEFAULT_TOTAL_RECORDS}",
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help=f"Insert batch size. Default: {DEFAULT_BATCH_SIZE}",
    )

    parser.add_argument(
        "--days-back",
        type=int,
        default=60,
        help="Spread generated timestamps across the last N days. Default: 60",
    )

    parser.add_argument(
        "--devices",
        type=int,
        default=1_000,
        help="Number of unique device IDs to generate. Default: 1000",
    )

    parser.add_argument(
        "--sessions",
        type=int,
        default=75_000,
        help="Number of unique session IDs to generate. Default: 75000",
    )

    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete existing demo users, app tokens, and their metric events before seeding.",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    db = SessionLocal()

    try:
        if args.reset:
            delete_existing_demo_data(db)

        app_tokens = seed_users_and_tokens(db)

        seed_metric_events(
            db,
            app_tokens=app_tokens,
            total_records=args.records,
            batch_size=args.batch_size,
            days_back=args.days_back,
            device_count=args.devices,
            session_count=args.sessions,
        )

        print("")
        print("Done.")
        print("")
        print("You can log in with:")
        print(f"  admin / {DEMO_PASSWORD}")
        print(f"  user1 / {DEMO_PASSWORD}")
        print(f"  user2 / {DEMO_PASSWORD}")
        print("")
        print("Example SDK app_token headers:")
        print("  app_token: user1-android-token")
        print("  app_token: user1-ios-token")
        print("  app_token: user2-android-token")
        print("  app_token: user2-ios-token")
        print("")

    except IntegrityError as exc:
        db.rollback()
        raise RuntimeError(
            "Failed to seed demo data because of a database integrity error."
        ) from exc

    finally:
        db.close()


if __name__ == "__main__":
    main()