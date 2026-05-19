from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from app.models import User
from app.repositories.refresh_token_blacklist_repository import is_refresh_token_blacklisted, blacklist_refresh_token
from app.repositories.user_repository import get_user_by_email, create_user, get_user_by_username
from app.schemas.auth import RegisterRequest, LoginRequest, LoginResponse, RefreshTokenRequest


class EmailAlreadyExists(Exception):
    """
    Exception raised when attempting to register an email address that already exists.

    This exception is used in the context where unique email addresses are required,
    such as user registration systems. It indicates that the operation cannot proceed
    because the provided email address is already in use.
    """
    pass


class InvalidCredentials(Exception):
    """
    Exception raised for invalid credentials errors.

    This exception is used to indicate that the provided credentials are invalid
    or incorrect. It can be used in authentication processes or when verifying user
    credentials within an application.
    """
    pass


class InvalidRefreshToken(Exception):
    """
    Represents an exception raised when a refresh token is invalid.

    This exception is specifically used to indicate that a provided refresh
    token cannot be processed because it is invalid. It can be used to handle
    authentication or session management failures.
    """
    pass


def register_user(db: Session, payload: RegisterRequest) -> User:
    """
    Registers a new user by checking for existing accounts and hashing the provided
    password before creating a new user entry in the database.

    :param db: Database session used for database transactions.
    :type db: Session
    :param payload: Request payload containing the user's registration details,
                    including email, username, and password.
    :type payload: RegisterRequest
    :return: The newly created user object after successful registration.
    :rtype: User
    :raises EmailAlreadyExists: If a user with the provided email already exists
                                 in the database.
    """
    existing_user = get_user_by_email(db, payload.email)

    if existing_user:
        raise EmailAlreadyExists(
            f"User with email {payload.email} already exists."
        )

    hashed_password = hash_password(payload.password)

    return create_user(
        db=db,
        email=payload.email,
        username=payload.username,
        hashed_password=hashed_password,
    )


def login_user(db: Session, payload: LoginRequest) -> LoginResponse:
    """
    Logs in a user by verifying credentials and generating access and refresh tokens.

    :param db: Database session used for querying the user data.
    :type db: Session
    :param payload: Represents the login request data, including username and password.
    :type payload: LoginRequest
    :return: A response containing generated access and refresh tokens.
    :rtype: LoginResponse
    :raises InvalidCredentials: If the username is not found or the password is invalid.
    """
    user = get_user_by_username(db, payload.username)

    if not user or not verify_password(payload.password, user.hashed_password):
        raise InvalidCredentials("Invalid username or password.")

    return LoginResponse(
        accessToken=create_access_token(str(user.id)),
        refreshToken=create_refresh_token(str(user.id)),
    )


def refresh_user_token(db: Session, payload: RefreshTokenRequest) -> LoginResponse:
    """
    Refreshes a user's authentication tokens using a valid refresh token.

    The used refresh token is blacklisted so it cannot be reused. This prevents
    refresh token replay.

    :param db: db session used for querying the user data.
    :param payload: The request containing the refresh token to be used for generating
        a new set of tokens.
    :type payload: RefreshTokenRequest
    :return: A response containing the newly generated access and refresh tokens.
    :rtype: LoginResponse
    :raises InvalidRefreshToken: Raised if the provided refresh token is invalid or
        expired, or if the token's subject is not valid.
    """
    token_payload = decode_token(
        payload.refresh_token,
        expected_token_type="refresh",
    )

    if not token_payload:
        raise InvalidRefreshToken("Invalid or expired refresh token.")

    user_id = token_payload.get("sub")
    refresh_token_jti = token_payload.get("jti")
    refresh_token_expires_at = token_payload.get("exp")

    if not isinstance(user_id, str):
        raise InvalidRefreshToken("Invalid refresh token subject.")

    if not isinstance(refresh_token_jti, str):
        raise InvalidRefreshToken("Invalid refresh token ID.")

    if not isinstance(refresh_token_expires_at, int):
        raise InvalidRefreshToken("Invalid refresh token expiration.")

    try:
        refresh_token_jti_uuid = UUID(refresh_token_jti)
    except ValueError:
        raise InvalidRefreshToken("Invalid refresh token ID format.")

    if is_refresh_token_blacklisted(db, refresh_token_jti_uuid):
        raise InvalidRefreshToken("Refresh token has already been used.")

    blacklist_refresh_token(
        db,
        jti=refresh_token_jti_uuid,
        expires_at=datetime.fromtimestamp(refresh_token_expires_at, tz=timezone.utc),
    )

    return LoginResponse(
        accessToken=create_access_token(user_id),
        refreshToken=create_refresh_token(user_id),
    )