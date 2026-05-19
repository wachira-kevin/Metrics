from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Defines the settings/configuration for the application by extending BaseSettings.

    This class includes configurations such as database connection URI, application host
    and port, name, version, and environment file options. It leverages Pydantic's
    BaseSettings to simplify the management and loading of environment variables.
    These settings are essential for proper configuration and deployment of the
    application.

    :ivar DATABASE_URI: The URI for connecting to the database.
    :type DATABASE_URI: str
    :ivar APP_HOST: The host address where the application runs. Defaults to "0.0.0.0".
    :type APP_HOST: str
    :ivar APP_PORT: The port on which the application listens. Defaults to 8000.
    :type APP_PORT: int
    :ivar APP_NAME: The name of the application. Defaults to "Metrics API".
    :type APP_NAME: str
    :ivar APP_VERSION: The version number of the application. Defaults to "1.0.0".
    :type APP_VERSION: str
    :ivar SECRET_KEY: The secret key used for securely signing and verifying tokens.
    :type SECRET_KEY: str
    :ivar ACCESS_TOKEN_EXPIRE_SECONDS: The duration in seconds for which access tokens
    :type ACCESS_TOKEN_EXPIRE_SECONDS: int
    :ivar REFRESH_TOKEN_EXPIRE_SECONDS: The duration in seconds for which refresh tokens
    :type REFRESH_TOKEN_EXPIRE_SECONDS: int
    """
    DATABASE_URI: str

    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    APP_NAME: str = "Metrics API"
    APP_VERSION: str = "1.0.0"

    SECRET_KEY: str = "change-this-secret-key-in-production"
    ACCESS_TOKEN_EXPIRE_SECONDS: int = 900
    REFRESH_TOKEN_EXPIRE_SECONDS: int = 604800

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

settings = Settings()
