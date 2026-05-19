from sqlalchemy.orm import Session

from app.models import AppToken


def get_app_token(db: Session, token_hash: str):
    return db.query(AppToken).filter(AppToken.token_hash == token_hash).first()