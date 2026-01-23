import os
import base64
import json
from functools import lru_cache
from typing import Any, TypeVar, cast, TypedDict
from src.config.pkg_config import PkgConfig
from ...models.auth.user import User
from ..security.security_scope import SecurityScope


def _load_env() -> str:
    config = PkgConfig()
    env_mode = os.getenv("API_ENV_MODE", "prod")
    env_files = {
        "dev": config.api_info.env.dev,
        "prod": config.api_info.env.prod,
        "test": config.api_info.env.test,
    }
    env_file = env_files.get(env_mode, ".env")  # Fallback to '.env'

    from dotenv import load_dotenv

    # Load the specific file or default
    load_dotenv(dotenv_path=env_file)
    return env_file


T = TypeVar("T")


class ScopesDictItem(TypedDict):
    scope: str
    description: str


ENV_FILE = _load_env()
"""Path to the environment file being used. See also pyproject.toml `[tool.project.config.api.env]` section."""

# SECRET_KEY = cast(str, os.getenv("API_SECRET_KEY"))
# if not SECRET_KEY:
#     raise ValueError("API_SECRET_KEY environment variable is not set")
# ALGORITHM = cast(str, os.getenv("API_AUTH_ALGORITHM"))
# if not ALGORITHM:
#     raise ValueError("API_AUTH_ALGORITHM environment variable is not set")
# TOKEN_EXPIRES = int(cast(str, os.getenv("API_TOKEN_EXPIRES_MINUTES", "30")))
AUTH_VERSION = int(os.getenv("API_AUTH_VERSION", "1"))
API_ENV_MODE = cast(str, os.getenv("API_ENV_MODE", "prod"))  # dev or prod
DESCOPE_PROJECT_ID = cast(str, os.getenv("DESCOPE_PROJECT_ID", ""))
"""Descope Project ID for authentication"""

if AUTH_VERSION == 2 and not DESCOPE_PROJECT_ID:
    raise ValueError(
        "DESCOPE_PROJECT_ID environment variable is not set for AUTH_VERSION 2"
    )

DESCOPE_INBOUND_APP_CLIENT_ID = cast(
    str, os.getenv("DESCOPE_INBOUND_APP_CLIENT_ID", "")
)
"""Descope Inbound App Client ID for authentication"""

if AUTH_VERSION == 2 and not DESCOPE_INBOUND_APP_CLIENT_ID:
    raise ValueError(
        "DESCOPE_INBOUND_APP_CLIENT_ID environment variable is not set for AUTH_VERSION 2"
    )

DESCOPE_INBOUND_APP_CLIENT_SECRET = cast(
    str, os.getenv("DESCOPE_INBOUND_APP_CLIENT_SECRET", "")
)
"""Descope Inbound App Client Secret for authentication"""
if AUTH_VERSION == 2 and not DESCOPE_INBOUND_APP_CLIENT_SECRET:
    raise ValueError(
        "DESCOPE_INBOUND_APP_CLIENT_SECRET environment variable is not set for AUTH_VERSION 2"
    )

DESCOPE_API_BASE_URL = cast(
    str, os.getenv("DESCOPE_API_BASE_URL", "https://api.descope.com")
)
"""Base URL for Descope API such as `https://api.descope.com`"""

DESCOPE_LOGIN_BASE_URL = cast(
    str, os.getenv("DESCOPE_LOGIN_BASE_URL", "https://api.descope.com/login")
)
"""Base URL for Descope Login such as `https://api.descope.com/login`"""

DESCOPE_FLOW_ID = cast(str, os.getenv("DESCOPE_FLOW_ID", ""))
"""Descope Flow ID for authentication flows"""

API_CUSTOM_GPT_CALLBACK_URL = cast(str, os.getenv("API_CUSTOM_GPT_CALLBACK_URL", ""))
"""Callback URL for Authorization"""

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


# def get_hashed_api_keys() -> set[str]:
# keys = get_api_value("hashed_api_keys", {}).keys()
# return set(keys)


# def get_api_key_allowed_origins(hashed_key: str) -> set[str]:
#     keys = get_api_value("hashed_api_keys", {})
#     key_data = keys.get(hashed_key, {})
#     return set(key_data.get("allowed_origins", []))


def get_user_info(user_id: str) -> User | None:
    users = get_data_value("users", {})
    if user_id not in users:
        return None

    user_data = users.get(user_id)
    if not user_data:
        return None
    return User(monad_name=user_data.get("monad_name"))


def get_users() -> dict[str, User]:
    users = {}
    for user_id, user_data in API_ENV_DB.get("data", {}).get("users", {}).items():
        users[user_id] = User(monad_name=user_data.get("monad_name"))
    return users


def get_api_servers() -> list[dict[str, str]]:
    return get_api_value("servers", [])


@lru_cache(maxsize=32)
def get_api_scopes(scope_type: str = "general") -> SecurityScope:
    scopes = get_api_value("scopes", {})
    if scope_type not in scopes:
        return SecurityScope(name=scope_type)
    st = cast(dict, scopes.get(scope_type, {}))
    scope_reads = cast(list[ScopesDictItem], st.get("read", []))
    scope_writes = cast(list[ScopesDictItem], st.get("write", []))
    reads = [s["scope"] for s in scope_reads]
    writes = [s["scope"] for s in scope_writes]
    return SecurityScope(
        name=scope_type,
        read_scopes=set(reads),
        write_scopes=set(writes),
    )
