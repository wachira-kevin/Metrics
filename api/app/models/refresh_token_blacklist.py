import uuid

from sqlalchemy import Column, DateTime
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base
from app.models.base import TimestampMixin


class RefreshTokenBlacklist(Base, TimestampMixin):
    __tablename__ = "refresh_token_blacklist"

    jti = Column(UUID(as_uuid=True), primary_key=True)

    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)