import base64
import hashlib
import hmac
import json
import os
import time
import uuid
from typing import Any

from app.core.config import settings

PBKDF2_ALGORITHM = "sha256"
PBKDF2_ITERATIONS = 600_000
SALT_BYTES = 16

TOKEN_ALGORITHM = "HS256"

def hash_app_token(token: str) -> str:
    """
    Creates a deterministic HMAC-SHA256 hash for app tokens.

    Unlike password hashes, app token hashes must be deterministic so the incoming
    token can be hashed and looked up in the database.
    """
    return hmac.new(
        settings.SECRET_KEY.encode("utf-8"),
        token.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

def hash_password(password: str) -> str:
    """
    Hashes the provided password using PBKDF2-HMAC-SHA256 with a random salt.

    The returned value stores the algorithm, iteration count, salt, and hash in a
    single string so it can be verified later.
    """
    salt = os.urandom(SALT_BYTES)
    password_hash = hashlib.pbkdf2_hmac(
        PBKDF2_ALGORITHM,
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
    )

    encoded_salt = base64.b64encode(salt).decode("ascii")
    encoded_hash = base64.b64encode(password_hash).decode("ascii")

    return f"pbkdf2_{PBKDF2_ALGORITHM}${PBKDF2_ITERATIONS}${encoded_salt}${encoded_hash}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plain password against a stored PBKDF2-HMAC password hash.
    """
    try:
        algorithm_name, iterations, encoded_salt, encoded_hash = hashed_password.split("$", 3)
        algorithm = algorithm_name.removeprefix("pbkdf2_")
        iterations = int(iterations)

        salt = base64.b64decode(encoded_salt.encode("ascii"))
        expected_hash = base64.b64decode(encoded_hash.encode("ascii"))

        actual_hash = hashlib.pbkdf2_hmac(
            algorithm,
            plain_password.encode("utf-8"),
            salt,
            iterations,
        )

        return hmac.compare_digest(actual_hash, expected_hash)
    except (ValueError, TypeError):
        return False

def _base64url_encode(data: bytes) -> str:
    """
    Encodes the provided byte data using base64 URL-safe encoding, omitting the
    trailing padding characters.

    :param data: The byte data to be encoded.
    :type data: bytes
    :return: The base64 URL-safe encoded string without padding.
    :rtype: str
    """
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _base64url_decode(data: str) -> bytes:
    """
    Decodes a base64url-encoded string into bytes. This function ensures that the
    input string has appropriate padding before decoding.

    :param data: Base64url-encoded string to decode.
    :type data: str
    :return: Decoded bytes from the base64url-encoded string.
    :rtype: bytes
    """
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def create_token(*, subject: str, token_type: str, expires_in: int) -> str:
    """
    Generate a JSON Web Token (JWT) with the given subject, token type, and expiration
    time. The JWT is encoded using the algorithm and secret key specified in the
    application settings.

    The generated token includes a header, a payload containing the subject and token
    details, and a signature for verification.

    :param subject: The subject associated with the token, typically a unique
        identifier for the user or entity to whom the token belongs.
    :type subject: str
    :param token_type: The type of token being generated, such as "access" or
        "refresh".
    :type token_type: str
    :param expires_in: The number of seconds after issue time when the token will
        expire.
    :type expires_in: int
    :return: A JSON Web Token as a string, consisting of three components
        (header, payload, and signature) separated by periods.
    :rtype: str
    """
    issued_at = int(time.time())

    header = {
        "alg": TOKEN_ALGORITHM,
        "typ": "JWT",
    }
    payload = {
        "sub": subject,
        "type": token_type,
        "jti": str(uuid.uuid7()),
        "iat": issued_at,
        "exp": issued_at + expires_in,
    }

    encoded_header = _base64url_encode(
        json.dumps(header, separators=(",", ":")).encode("utf-8")
    )
    encoded_payload = _base64url_encode(
        json.dumps(payload, separators=(",", ":")).encode("utf-8")
    )

    signing_input = f"{encoded_header}.{encoded_payload}".encode("ascii")
    signature = hmac.new(
        settings.SECRET_KEY.encode("utf-8"),
        signing_input,
        hashlib.sha256,
    ).digest()

    encoded_signature = _base64url_encode(signature)

    return f"{encoded_header}.{encoded_payload}.{encoded_signature}"


def decode_token(token: str, *, expected_token_type: str) -> dict[str, Any] | None:
    """
    Decodes a token and validates its integrity, type, and expiration.

    This function takes an encoded token, verifies its signature, checks its type, and ensures it
    has not expired. If all validations pass, the decoded payload is returned. Otherwise, the
    function returns None to indicate the token is invalid or expired.

    :param token: The encoded token to decode and validate.
    :type token: str
    :param expected_token_type: The expected type of the token that will be verified in the payload.
    :type expected_token_type: str
    :return: A dictionary containing the decoded payload if the token is valid, or None if invalid or expired.
    :rtype: dict[str, Any] | None
    """
    try:
        encoded_header, encoded_payload, encoded_signature = token.split(".", 2)

        signing_input = f"{encoded_header}.{encoded_payload}".encode("ascii")
        expected_signature = hmac.new(
            settings.SECRET_KEY.encode("utf-8"),
            signing_input,
            hashlib.sha256,
        ).digest()

        actual_signature = _base64url_decode(encoded_signature)

        if not hmac.compare_digest(actual_signature, expected_signature):
            return None

        payload = json.loads(_base64url_decode(encoded_payload).decode("utf-8"))

        if payload.get("type") != expected_token_type:
            return None

        expires_at = payload.get("exp")

        if not isinstance(expires_at, int) or expires_at < int(time.time()):
            return None

        return payload
    except (ValueError, TypeError, json.JSONDecodeError):
        return None


def create_access_token(user_id: str) -> str:
    """
    Generate an access token for a specific user.

    This function creates an access token for a given user based on their user ID. The token
    is generated with a predefined expiration time and type, ensuring secure access management
    for authentication purposes.

    :param user_id: The unique identifier of the user for whom the access token is being generated.
    :type user_id: str
    :return: A securely generated access token for the specified user.
    :rtype: str
    """
    return create_token(
        subject=user_id,
        token_type="access",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_SECONDS,
    )


def create_refresh_token(user_id: str) -> str:
    """
    Generates a new refresh token for the specified user. The refresh token is used to
    obtain new access tokens without requiring the user to re-authenticate. The token
    has a limited lifespan determined by the settings of the application.

    :param user_id: The unique identifier of the user for whom the refresh token is
     created.
    :type user_id: str
    :return: A string containing the newly generated refresh token.
    :rtype: str
    """
    return create_token(
        subject=user_id,
        token_type="refresh",
        expires_in=settings.REFRESH_TOKEN_EXPIRE_SECONDS,
    )