from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_token
from app.models import User
from app.repositories.user_repository import get_user_by_username, get_user_by_id

bearer_scheme = HTTPBearer()


def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
        db: Session = Depends(get_db)
) -> User:
    """
    Retrieves the currently authenticated user based on the provided credentials and
    database session. The token in the credentials is decoded and validated to extract
    the user ID. The user is then fetched from the database using the extracted user ID.

    :param credentials: The HTTP authorization credentials containing the token
        to be decoded and validated.
    :type credentials: HTTPAuthorizationCredentials
    :param db: The database session used to interact with the user database.
    :type db: Session
    :return: The authenticated user corresponding to the token in the credentials.
    :rtype: User
    :raises HTTPException: If the token is invalid, expired, or the user is not found
        in the database.
    """
    token = credentials.credentials

    payload = decode_token(token, expected_token_type="access")

    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    user_id = payload.get("sub")

    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = get_user_by_id(db, user_id)

    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    return user