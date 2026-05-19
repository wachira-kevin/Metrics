from fastapi import Header, HTTPException, status, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import hash_app_token
from app.models.app_token import AppToken
from app.repositories.app_token_repository import get_app_token


def get_current_app_token(
    app_token: str | None = Header(default=None, alias="app_token"),
    db: Session = Depends(get_db),
) -> AppToken:
    if not app_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing app token",
        )

    token_hash = hash_app_token(app_token)

    current_app_token = get_app_token(db, token_hash=token_hash)

    if current_app_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid app token",
        )

    return current_app_token
