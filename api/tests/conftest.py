import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
import uuid

from app.main import app
from app.core.database import Base, get_db
from app.core.security import hash_app_token
from app.models import AppToken, User, MetricEvent, RefreshTokenBlacklist
from sqlalchemy import JSON, TypeDecorator, String
from sqlalchemy.dialects.postgresql import JSONB, UUID

# Mock JSONB for SQLite
class JSONB_SQLite(TypeDecorator):
    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'sqlite':
            return dialect.type_descriptor(JSON())
        else:
            return dialect.type_descriptor(JSONB())

# Mock UUID for SQLite
class UUID_SQLite(TypeDecorator):
    impl = String
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'sqlite':
            return dialect.type_descriptor(String(36))
        else:
            return dialect.type_descriptor(UUID(as_uuid=True))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        return uuid.UUID(value)

# Use SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    # Monkeypatch for SQLite compatibility
    models_to_patch = [User, AppToken, MetricEvent, RefreshTokenBlacklist]
    original_types = {}

    for model in models_to_patch:
        for column in model.__table__.columns:
            if isinstance(column.type, (JSONB, UUID)):
                original_types[(model, column.name)] = column.type
                if isinstance(column.type, JSONB):
                    column.type = JSONB_SQLite()
                else:
                    column.type = UUID_SQLite()
            
            # Remove Postgres-specific server defaults
            if column.server_default is not None:
                original_types[(model, column.name, 'server_default')] = column.server_default
                column.server_default = None
                column.nullable = True
    
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    
    # Restore original types and defaults
    for key, orig_val in original_types.items():
        if len(key) == 2:
            model, col_name = key
            model.__table__.c[col_name].type = orig_val
        elif len(key) == 3:
            model, col_name, _ = key
            model.__table__.c[col_name].server_default = orig_val
            model.__table__.c[col_name].nullable = False

@pytest.fixture
def db():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture
def test_user(db):
    # We need a user to associate with app token
    from app.core.security import hash_password
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password=hash_password("password123"),
        role="user"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture
def test_app_token(db, test_user):
    raw_token = "test-token-123"
    token_hash = hash_app_token(raw_token)
    app_token = AppToken(
        user_id=test_user.id,
        token_hash=token_hash,
        label="Test Token"
    )
    db.add(app_token)
    db.commit()
    db.refresh(app_token)
    return raw_token
