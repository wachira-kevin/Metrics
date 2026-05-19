from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.auth import RegisterRequest, RegisterResponse, LoginResponse, LoginRequest, RefreshTokenRequest
from app.services.auth_service import EmailAlreadyExists, register_user, login_user, InvalidCredentials, \
    refresh_user_token, InvalidRefreshToken

auth_router = APIRouter(prefix="/auth", tags=["auth"])


@auth_router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    """
    Registers a new user with the provided details. This endpoint accepts a user
    registration payload, validates the input data, and creates a new user record
    in the database if the email does not already exist. On successful registration,
    it returns the user ID of the registered user.

    :param payload: The registration details provided by the client. Must include
        the user's email, password, and other information required for registration.
    :param db: The database session object used to query and persist data.
    :return: A response containing the ID of the newly registered user.
    """
    try:
        user = register_user(db, payload)
    except EmailAlreadyExists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already exists",
        )

    return RegisterResponse(userId=str(user.id))


@auth_router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticates a user by validating the provided login credentials and returns
    a response model upon successful authentication.

    :param payload: An instance of `LoginRequest` containing the user's login
        information such as username and password.
    :param db: A database session, automatically injected using dependency
        injection, used to interact with the database during authentication.
    :return: An instance of `LoginResponse` containing details of the
        authenticated user, including tokens or additional metadata.
    """
    try:
        return login_user(db, payload)
    except InvalidCredentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )


@auth_router.post(
    "/refresh",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
)
def refresh(payload: RefreshTokenRequest, db: Session = Depends(get_db)):
    """
    Handles the endpoint for refreshing a user's authentication token. It processes
    a request containing a refresh token and returns a new authentication token if
    the refresh token is valid. If the refresh token is invalid, expired, or already
    used, an unauthorized error is raised.

    :param payload: The payload containing the refresh token.
    :type payload: RefreshTokenRequest
    :param db: Database session used to check and update the refresh token blacklist.
    :type db: Session
    :return: A new authentication token response.
    :rtype: LoginResponse
    :raises HTTPException: If the refresh token is invalid, expired, or already used.
    """
    try:
        return refresh_user_token(db, payload)
    except InvalidRefreshToken:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )