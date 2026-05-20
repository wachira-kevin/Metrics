from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import RefreshTokenBlacklist


def is_refresh_token_blacklisted(db: Session, jti: UUID) -> bool:
    """
    Check if a refresh token is blacklisted.

    This function verifies whether a given refresh token, identified by its
    JTI (JWT ID), exists in the refresh token blacklist. The blacklist operates as
    a security mechanism to ensure that compromised or invalidated tokens
    cannot be reused.

    :param db: The database session used for querying the refresh token blacklist.
    :type db: Session
    :param jti: The unique identifier (JTI) of the refresh token to check.
    :type jti: UUID
    :return: A boolean indicating whether the refresh token is blacklisted.
    :rtype: bool
    """
    return (
            db.query(RefreshTokenBlacklist)
            .filter(RefreshTokenBlacklist.jti == jti)
            .first()
            is not None
    )


def blacklist_refresh_token(db: Session, *, jti: UUID, expires_at: datetime) -> RefreshTokenBlacklist:
    """
    Blacklists a refresh token by adding it to the database. This ensures that the token is no longer valid for
    future authentication actions. The token is blacklisted based on its unique identifier (jti) and the expiration
    time.

    :param db: The database session used to create and commit the blacklisted token object.
    :type db: Session
    :param jti: The unique identifier of the refresh token to be blacklisted.
    :type jti: UUID
    :param expires_at: The timestamp indicating when the blacklisted token will expire.
    :type expires_at: datetime
    :return: The newly blacklisted refresh token entry.
    :rtype: RefreshTokenBlacklist
    """
    blacklisted_token = RefreshTokenBlacklist(
        jti=jti,
        expires_at=expires_at,
    )

    db.add(blacklisted_token)
    db.commit()
    db.refresh(blacklisted_token)

    return blacklisted_token