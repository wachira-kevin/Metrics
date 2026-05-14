import uuid
from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base
from app.models.base import TimestampMixin


class User(Base, TimestampMixin):
    """
    Represents a User entity in the system.

    This class defines the schema and business logic associated with a user,
    including attributes such as email, username, password, and role. It serves
    as the model mapping for the "users" table in the database.

    :ivar id: Unique identifier for the user.
    :type id: UUID
    :ivar email: Email address associated with the user, which must be unique.
    :type email: str
    :ivar username: Unique username chosen by the user for identification.
    :type username: str
    :ivar hashed_password: Securely stored hashed password of the user.
    :type hashed_password: str
    :ivar role: Role of the user within the system, such as "user" or "admin".
    :type role: str
    """

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True),primary_key=True,default=uuid.uuid7)
    email = Column(String(255),unique=True,nullable=False,index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String,nullable=False)
    role = Column(String(20),nullable=False,default="user")