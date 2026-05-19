from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import RefreshTokenBlacklist


def is_refresh_token_blacklisted(db: Session, jti: UUID) -> bool:
    return (
            db.query(RefreshTokenBlacklist)
            .filter(RefreshTokenBlacklist.jti == jti)
            .first()
            is not None
    )


def blacklist_refresh_token(db: Session, *, jti: UUID, expires_at: datetime) -> RefreshTokenBlacklist:
    blacklisted_token = RefreshTokenBlacklist(
        jti=jti,
        expires_at=expires_at,
    )

    db.add(blacklisted_token)
    db.commit()
    db.refresh(blacklisted_token)

    return blacklisted_token