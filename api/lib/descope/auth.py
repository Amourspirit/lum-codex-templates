from typing import Optional, List
import jwt
from jwt import PyJWKClient
from fastapi import Depends
from fastapi.security import SecurityScopes, HTTPAuthorizationCredentials, HTTPBearer

from .exception_handlers import (
    UnauthenticatedException,
    UnauthorizedException,
)
from ..env import env_info

jwks_url = (
    f"https://api.descope.com/{env_info.DESCOPE_PROJECT_ID}/.well-known/jwks.json"
)


class TokenVerifier:
    def __init__(self):
        self.jwks_client = PyJWKClient(jwks_url)
        self.allowed_algorithms = ["RS256"]

    async def __call__(
        self,
        security_scopes: SecurityScopes,
        # token injected by FastAPI Security, specified in the FastAPI route definition
        token: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer()),
    ):
        if token is None:
            raise UnauthenticatedException

        token_c = token.credentials

        key = self._get_signing_key(token_c)
        payload = self._decode_token(token_c, key)

        if security_scopes.scopes:
            self._enforce_scopes(payload, security_scopes.scopes)

        return payload

    def _get_signing_key(self, token: str):
        try:
            return self.jwks_client.get_signing_key_from_jwt(token).key
        except Exception as e:
            raise UnauthorizedException(f"Failed to fetch signing key: {str(e)}")

    # helper which calls jwt.decode()
    def _decode_token(self, token: str, key):
        try:
            project_id = env_info.DESCOPE_PROJECT_ID
            issuer_candidates = [
                f"https://api.descope.com/v1/apps/{project_id}",
                project_id,
            ]
            return jwt.decode(
                token,
                key,
                algorithms=self.allowed_algorithms,
                issuer=issuer_candidates,
                audience=project_id,
            )
        except Exception as e:
            raise UnauthorizedException(f"Token decoding failed: {str(e)}")

    def _enforce_scopes(self, payload: dict, required_scopes: List[str]):
        scope_claim = payload.get("scope")
        if scope_claim is None:
            raise UnauthorizedException('Missing required claim: "scope"')

        scopes = scope_claim.split() if isinstance(scope_claim, str) else scope_claim
        missing = [scope for scope in required_scopes if scope not in scopes]

        if missing:
            raise UnauthorizedException(
                f"Missing required scopes: {', '.join(missing)}"
            )


AUTH = TokenVerifier()
