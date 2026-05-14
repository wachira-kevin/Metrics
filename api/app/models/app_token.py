import uuid
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base
from app.models.base import TimestampMixin


class AppToken(Base, TimestampMixin):
    """
    Represents an application token entity for authentication or tracking purposes.

    This class serves to represent the tokens associated with a specific
    user for authentication, session management, or other application-related
    functionality. It includes necessary attributes such as a unique identifier,
    user association, token hash, and optional label for identification.

    :ivar id: The unique identifier for the application token.
    :type id: UUID
    :ivar user_id: The identifier of the user associated with this token.
    :type user_id: UUID
    :ivar token_hash: The hashed value of the token for security purposes.
    :type token_hash: str
    :ivar label: An optional descriptive label for the token.
    :type label: str
    """
    __tablename__ = "app_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid7)

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)

    token_hash = Column(String, nullable=False)

    label = Column(String(255))