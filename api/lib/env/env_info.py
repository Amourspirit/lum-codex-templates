import os
import base64
import json
from typing import Any, TypeVar, cast
from ...models.auth.user import User

T = TypeVar("T")

SECRET_KEY = cast(str, os.getenv("API_SECRET_KEY"))
if not SECRET_KEY:
    raise ValueError("API_SECRET_KEY environment variable is not set")
ALGORITHM = cast(str, os.getenv("API_AUTH_ALGORITHM"))
if not ALGORITHM:
    raise ValueError("API_AUTH_ALGORITHM environment variable is not set")
TOKEN_EXPIRES = int(cast(str, os.getenv("API_TOKEN_EXPIRES_MINUTES", "30")))
AUTH_VERSION = int(os.getenv("API_AUTH_VERSION", "1"))
API_ENV_MODE = cast(str, os.getenv("API_ENV_MODE", "prod"))  # dev or prod


_API_ENV_DATA = os.getenv("API_ENV_DATA")
if not _API_ENV_DATA:
    raise ValueError("API environment data variable is not set")

API_ENV_DB: dict[str, dict[str, Any]] = json.loads(
    base64.b64decode(_API_ENV_DATA).decode("utf-8")
)
_API_ENV_DATA = None  # Clear sensitive data from memory


def get_data_value(key: str, default: T = None) -> T:
    return API_ENV_DB.get("data", {}).get(key, default)


def get_api_value(key: str, default: T = None) -> T:
    data = API_ENV_DB.get("data", {})
    return data.get("api", {}).get(key, default)


def get_hashed_api_keys() -> set[str]:
    keys = get_api_value("hashed_api_keys", {}).keys()
    return set(keys)


def get_api_key_allowed_origins(hashed_key: str) -> set[str]:
    keys = get_api_value("hashed_api_keys", {})
    key_data = keys.get(hashed_key, {})
    return set(key_data.get("allowed_origins", []))


def get_user_info(username: str) -> User | None:
    users = get_data_value("users", {})
    if username not in users:
        return None

    user_data = users.get(username)
    if not user_data:
        return None
    return User(**user_data)


def get_users() -> dict[str, User]:
    users = {}
    for username, user_data in API_ENV_DB.get("data", {}).get("users", {}).items():
        users[username] = User(**user_data)
    return users


def get_api_servers() -> list[dict[str, str]]:
    return get_api_value("servers", [])
