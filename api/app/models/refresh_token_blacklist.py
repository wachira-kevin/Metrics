import uuid

from sqlalchemy import Column, DateTime
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base
from app.models.base import TimestampMixin


class RefreshTokenBlacklist(Base, TimestampMixin):
    """
    Represents a blacklist for refresh tokens.

    This class is used to store information about blacklisted refresh tokens.
    Each entry contains a unique token identifier (jti) and the expiration timestamp
    for that token. It is useful in managing token invalidation and enhancing security
    practices.

    :ivar jti: Unique identifier for the refresh token.
    :type jti: UUID
    :ivar expires_at: Expiration timestamp of the refresh token in UTC.
    :type expires_at: datetime
    """
    __tablename__ = "refresh_token_blacklist"

    jti = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid7)

    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)