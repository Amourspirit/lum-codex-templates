from typing import Literal
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from src.util.validation import check
from ..env import env_info


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=env_info.ENV_FILE, extra="ignore")

    DESCOPE_PROJECT_ID: str
    DESCOPE_API_BASE_URL: str
    DESCOPE_FLOW_ID: str
    DESCOPE_INBOUND_APP_CLIENT_SECRET: str
    DESCOPE_INBOUND_APP_CLIENT_ID: str
    DESCOPE_LOGIN_BASE_URL: str
    MCP_SERVER_URL: str
    BASE_URL: str
    FASTMCP_SERVER_AUTH_DESCOPEPROVIDER_CONFIG_URL: str
    FASTMCP_SERVER_AUTH_DESCOPEPROVIDER_BASE_URL: str
    API_ENV_MODE: Literal["dev", "prod"] = "prod"
    LOG_LEVEL: str = "INFO"

    def model_post_init(self, _context):
        check(self.DESCOPE_PROJECT_ID != "", "descope_project_id must be set")
        check(self.DESCOPE_API_BASE_URL != "", "descope_api_base_url must be set")
        if self.DESCOPE_API_BASE_URL.endswith("/"):
            object.__setattr__(
                self,
                "descope_api_base_url",
                self.DESCOPE_API_BASE_URL.rstrip("/"),
            )

    @property
    def is_production(self) -> bool:
        return self.API_ENV_MODE == "prod"

    @property
    def is_development(self) -> bool:
        return self.API_ENV_MODE == "dev"

    @property
    def authorization_servers(self) -> list[str]:
        return [f"{self.DESCOPE_API_BASE_URL}/{self.DESCOPE_PROJECT_ID}"]

    @property
    def issuer_candidates(self) -> list[str]:
        return [
            f"{self.DESCOPE_API_BASE_URL}/v1/apps/{self.DESCOPE_PROJECT_ID}",
            self.DESCOPE_PROJECT_ID,
        ]

    @property
    def audience(self) -> str:
        return self.DESCOPE_PROJECT_ID

    @property
    def jwks_url(self) -> str:
        return f"{self.DESCOPE_API_BASE_URL}/{self.DESCOPE_PROJECT_ID}/.well-known/jwks.json"

    @property
    def issuer(self) -> str:
        return f"{self.DESCOPE_API_BASE_URL}/v1/apps/{self.DESCOPE_PROJECT_ID}"

    @property
    def authorization_endpoint(self) -> str:
        return f"{self.DESCOPE_API_BASE_URL}/oauth2/v1/apps/authorize"

    @property
    def response_types_supported(self) -> list[str]:
        return ["code", "token", "id_token"]

    @property
    def grant_types_supported(self) -> list[str]:
        return ["authorization_code", "refresh_token"]

    @property
    def token_endpoint_auth_methods_supported(self) -> list[str]:
        return ["client_secret_basic", "client_secret_post"]

    @property
    def scopes_supported(self) -> list[str]:
        scopes = env_info.get_api_scopes()
        scopes_set = scopes.read_scopes | scopes.write_scopes
        scopes_set.add("openid")
        scopes_set.add("profile")
        scopes_set.add("email")

        return list(scopes_set)

    @property
    def claims_supported(self) -> list[str]:
        return ["sub", "email", "name", "picture"]

    @property
    def subject_types_supported(self) -> list[str]:
        return ["public"]

    @property
    def id_token_signing_alg_values_supported(self) -> list[str]:
        return ["RS256"]

    @property
    def code_challenge_methods_supported(self) -> list[str]:
        return ["S256"]

    @property
    def token_endpoint(self) -> str:
        return f"{self.DESCOPE_API_BASE_URL}/oauth2/v1/apps/token"

    @property
    def userinfo_endpoint(self) -> str:
        return f"{self.DESCOPE_API_BASE_URL}/oauth2/v1/apps/userinfo"

    @property
    def revocation_endpoint(self) -> str:
        return f"{self.DESCOPE_API_BASE_URL}/oauth2/v1/apps/revoke"

    @property
    def registration_endpoint(self) -> str:
        return f"{self.DESCOPE_API_BASE_URL}/v1/mgmt/inboundapp/app/{self.DESCOPE_PROJECT_ID}/register"

    @property
    def end_session_endpoint(self) -> str:
        return f"{self.DESCOPE_API_BASE_URL}/oauth2/v1/apps/logout"

    @property
    def api_callback_url(self) -> str:
        return f"{self.BASE_URL}/callback"


@lru_cache()
def get_settings():
    # return Settings(
    #     descope_project_id=env_info.DESCOPE_PROJECT_ID,
    #     descope_api_base_url=env_info.DESCOPE_API_BASE_URL,
    # )
    return Settings()  # type: ignore
