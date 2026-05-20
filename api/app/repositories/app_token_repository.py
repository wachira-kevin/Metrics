from uuid import UUID

from sqlalchemy.orm import Session

from app.models import AppToken


def get_app_token(db: Session, token_hash: str):
    """
    Retrieve an application token from the database by its token hash.

    This function performs a query on the `AppToken` database table, searching
    for a record that matches the provided token hash. If such a record
    exists, it returns the corresponding `AppToken` object; otherwise, it
    returns `None`.

    :param db: Database session used to perform the query.
    :type db: Session
    :param token_hash: The hashed value of the token to search for within
        the `AppToken` records.
    :type token_hash: str
    :return: The `AppToken` object if a match is found, otherwise `None`.
    :rtype: Optional[AppToken]
    """
    return db.query(AppToken).filter(AppToken.token_hash == token_hash).first()


def get_app_token_ids_for_user(db: Session, user_id: UUID) -> list[UUID]:
    """
    Retrieve a list of application token IDs for a specified user from the database.

    This function queries the database to find all application tokens associated with
    a given user's ID. It returns the IDs of the matched application tokens as a list.

    :param db: A SQLAlchemy database session, used to access and execute queries in the
        application's database.
    :type db: Session
    :param user_id: The unique identifier of the user whose application token IDs
        are being retrieved.
    :type user_id: UUID
    :return: A list of UUIDs representing the application token IDs associated with
        the specified user.
    :rtype: list[UUID]
    """
    rows = (
        db.query(AppToken.id)
        .filter(AppToken.user_id == user_id)
        .all()
    )

    return [row.id for row in rows]