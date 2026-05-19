from pydantic import BaseModel, EmailStr, Field, ConfigDict


class RegisterRequest(BaseModel):
    """
    Representation of a registration request.

    This class is used to represent the data required for a user to register. It
    validates the given data based on the constraints defined for each attribute,
    such as minimum and maximum lengths for strings.

    :ivar email: The email address of the user.
    :type email: EmailStr
    :ivar username: The username chosen by the user. Must be between 3 and 100
        characters in length.
    :type username: str
    :ivar password: The password chosen by the user. Must be at least 8 characters
        in length.
    :type password: str
    """
    email: EmailStr
    username: str = Field(min_length=3, max_length=100)
    password: str = Field(min_length=8)


class RegisterResponse(BaseModel):
    """
    Represents the response payload for a user registration action.

    This class models the data structure returned after a user registration,
    including all necessary response-related attributes. It leverages Pydantic's
    BaseModel for data validation and serialization.

    :ivar user_id: The unique identifier of the registered user.
    :type user_id: str
    """
    model_config = ConfigDict(populate_by_name=True)

    user_id: str = Field(alias="userId")


class LoginRequest(BaseModel):
    """
    Represents a login request model.

    This class is used to structure and validate the data required for a login
    request. It ensures that the provided username and password meet the specified
    validation criteria. Typically, it is used in scenarios where user authentication
    is handled.

    :ivar username: The username provided by the user. Must have a length
        between 3 and 100 characters.
    :type username: str
    :ivar password: The password provided by the user. Must have a minimum
        length of 8 characters.
    :type password: str
    """
    username: str = Field(min_length=3, max_length=100)
    password: str = Field(min_length=8)


class LoginResponse(BaseModel):
    """
    Represents the response model for a login operation.

    This class is used to handle the response data from a login operation,
    including tokens, their types, and expiration durations. The attributes
    correspond to the fields returned by the backend service, often used in
    authorization mechanisms.

    :ivar access_token: The access token returned after a successful login.
    :type access_token: str
    :ivar refresh_token: The refresh token used for obtaining new access tokens.
    :type refresh_token: str
    :ivar token_type: The type of the provided access token (default is "bearer").
    :type token_type: str
    :ivar expires_in: The duration in seconds for which the access token is valid,
        defaults to 3600 seconds.
    :type expires_in: int
    :ivar refresh_token_expires_in: The duration in seconds for which the refresh token
        is valid, defaults to 86400 seconds.
    :type refresh_token_expires_in: int
    """
    model_config = ConfigDict(populate_by_name=True)

    access_token: str = Field(alias="accessToken")
    refresh_token: str = Field(alias="refreshToken")
    token_type: str = Field(default="bearer", alias="tokenType")
    expires_in: int = Field(default=900, alias="expiresIn")
    refresh_token_expires_in: int = Field(default=604800, alias="refreshTokenExpiresIn")


class RefreshTokenRequest(BaseModel):
    """
    Represents a model for handling a refresh token request.

    This class is used to encapsulate the data structure required for
    processing a refresh token request. It leverages pydantic's BaseModel
    to enable data validation and model configuration.

    :ivar refresh_token: The refresh token string used for obtaining a new
        access token. This is mapped from the input key "refreshToken".
    :type refresh_token: str
    """
    model_config = ConfigDict(populate_by_name=True)

    refresh_token: str = Field(alias="refreshToken")