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
    DESCOPE_LOGIN_BASE_URL: str
    API_ENV_MODE: str
    MCP_SERVER_URL: str
    BASE_URL: str

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
        return ["code"]

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


@lru_cache()
def get_settings():
    # return Settings(
    #     descope_project_id=env_info.DESCOPE_PROJECT_ID,
    #     descope_api_base_url=env_info.DESCOPE_API_BASE_URL,
    # )
    return Settings()  # type: ignore
