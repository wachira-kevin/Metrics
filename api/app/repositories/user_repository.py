from sqlalchemy.orm import Session

from app.models import User


def get_user_by_email(db: Session, email: str) -> User | None:
    """
    Retrieve a user from the database based on their email address. If no user with the
    provided email exists in the database, the function will return None.

    :param db: Database session used to execute the query.
    :type db: Session
    :param email: Email address of the user to look for.
    :type email: str
    :return: The user object if found in the database, otherwise None.
    :rtype: User | None
    """
    return db.query(User).filter(User.email == email).first()


def get_user_by_username(db: Session, username: str) -> User | None:
    """
    Fetch a user object from the database based on the provided username.

    This function queries the database to find a user record that matches
    the specified username. If a matching user is found, the function
    returns the corresponding user object; otherwise, it returns None.

    :param db: Database session used to perform the query.
    :type db: Session
    :param username: The username of the user to be fetched.
    :type username: str
    :return: The user object if a match is found, None otherwise.
    :rtype: User | None
    """
    return db.query(User).filter(User.username == username).first()


def get_user_by_id(db: Session, user_id: str) -> User | None:
    """
    Retrieve a user by their unique identifier.

    This function queries the database to find and return a user whose unique
    identifier matches the provided `user_id`. If no user is found, it returns `None`.

    :param db: Database session to be used for the query
    :type db: Session
    :param user_id: The unique identifier of the user to be retrieved
    :type user_id: str
    :return: The user object if found or `None` if no user matches the specified `user_id`
    :rtype: User | None
    """
    return db.query(User).filter(User.id == user_id).first()


def create_user(
    db: Session,
    *,
    email: str,
    username: str,
    hashed_password: str,
) -> User:
    """
    Creates a new user entry and commits it to the database.

    This function takes in the necessary user details, creates a new user instance,
    adds it to the database session, commits the session to persist the data, and
    refreshes the user instance to update it with the latest database state.

    :param db: Database session used for interacting with the database.
    :type db: Session
    :param email: The email address of the user to be created.
    :type email: str
    :param username: The username of the user to be created.
    :type username: str
    :param hashed_password: The hashed version of the user's password.
    :type hashed_password: str
    :return: The newly created user instance.
    :rtype: User
    """
    user = User(
        email=email,
        username=username,
        hashed_password=hashed_password,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user