"""Secure API key management using system keyring.

Stores and retrieves API keys from the system keyring with fallback
to environment variables for compatibility.
"""

import os

import keyring
import structlog

logger = structlog.get_logger()

# Service name for keyring storage
KEYRING_SERVICE = "jiro-dreams-of-code"
KEYRING_USERNAME = "anthropic"
ENV_VAR_NAME = "ANTHROPIC_API_KEY"


def store_api_key(key: str) -> bool:
    """Store API key in system keyring.

    Args:
        key: The API key to store.

    Returns:
        True if successfully stored, False if keyring is unavailable.

    Raises:
        ValueError: If key is empty.
    """
    if not key or not key.strip():
        raise ValueError("API key cannot be empty")

    try:
        keyring.set_password(KEYRING_SERVICE, KEYRING_USERNAME, key.strip())
        logger.info("api_key_stored", service=KEYRING_SERVICE)
        return True
    except Exception as e:
        logger.warning(
            "keyring_unavailable",
            error=str(e),
            error_type=type(e).__name__,
        )
        return False


def get_api_key() -> str | None:
    """Get API key from keyring with fallback to environment variable.

    Tries to retrieve the API key from the system keyring first.
    Falls back to ANTHROPIC_API_KEY environment variable if keyring
    is unavailable or the key is not stored.

    Returns:
        API key if found, None otherwise.
    """
    # Try keyring first
    try:
        key: str | None = keyring.get_password(KEYRING_SERVICE, KEYRING_USERNAME)
        if key:
            logger.debug("api_key_from_keyring", service=KEYRING_SERVICE)
            return key
    except Exception as e:
        logger.debug(
            "keyring_retrieval_failed",
            error=str(e),
            error_type=type(e).__name__,
        )

    # Fall back to environment variable
    env_key = os.environ.get(ENV_VAR_NAME, "").strip()
    if env_key:
        logger.debug("api_key_from_environment", variable=ENV_VAR_NAME)
        return env_key

    return None


def remove_api_key() -> bool:
    """Remove API key from system keyring.

    Args:
        None

    Returns:
        True if successfully removed, False if key not found or keyring unavailable.
    """
    try:
        keyring.delete_password(KEYRING_SERVICE, KEYRING_USERNAME)
        logger.info("api_key_removed", service=KEYRING_SERVICE)
        return True
    except keyring.errors.PasswordDeleteError:
        logger.debug("api_key_not_found", service=KEYRING_SERVICE)
        return False
    except Exception as e:
        logger.warning(
            "keyring_removal_failed",
            error=str(e),
            error_type=type(e).__name__,
        )
        return False


def is_key_stored() -> bool:
    """Check if API key is stored in keyring.

    Args:
        None

    Returns:
        True if key is stored in keyring, False otherwise.
    """
    try:
        key = keyring.get_password(KEYRING_SERVICE, KEYRING_USERNAME)
        return key is not None
    except Exception as e:
        logger.debug(
            "keyring_check_failed",
            error=str(e),
            error_type=type(e).__name__,
        )
        return False
