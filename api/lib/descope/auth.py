from typing import Any, Optional, List
from loguru import logger
import jwt
from jwt import PyJWKClient
from fastapi import Depends
from fastapi.security import SecurityScopes, HTTPAuthorizationCredentials, HTTPBearer
from ..exceptions import UnauthenticatedException, UnauthorizedException
from .auth_config import get_settings
from api.models.descope.descope_session import DescopeSession


class TokenVerifier:
    def __init__(self):
        self.config = get_settings()
        headers = {"User-Agent": "Mozilla/5.0 (CodexTemplatesFastAPIApp)"}
        self.jwks_client = PyJWKClient(uri=self.config.jwks_url, headers=headers)
        self.allowed_algorithms = ["RS256"]

    async def __call__(
        self,
        security_scopes: SecurityScopes,
        token: Optional[HTTPAuthorizationCredentials] = Depends(
            HTTPBearer(auto_error=False)
        ),
    ):
        if token is None:
            logger.error("TokenVerifier: No token provided.")
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
            logger.error("TokenVerifier: Failed to get signing key - {error}", error=e)
            raise UnauthorizedException(f"Failed to fetch signing key: {str(e)}")

    def _decode_token(self, token: str, key) -> dict[str, Any]:
        try:
            return jwt.decode(
                token,
                key,
                algorithms=self.allowed_algorithms,
                issuer=self.config.issuer_candidates,
                audience=self.config.audience,
            )
        except Exception as e:
            logger.error("TokenVerifier: Token decoding failed - {error}", error=e)
            raise UnauthorizedException(f"Token decoding failed: {str(e)}")

    def _enforce_scopes(self, payload: dict, required_scopes: List[str]):
        scope_claim = payload.get("scope")
        if scope_claim is None:
            logger.error("TokenVerifier: Missing required scope claim.")
            raise UnauthorizedException('Missing required claim: "scope"')
        scopes = scope_claim.split() if isinstance(scope_claim, str) else scope_claim
        missing = [scope for scope in required_scopes if scope not in scopes]
        if missing:
            missing_str = ", ".join(missing)
            logger.error(
                "TokenVerifier: Missing required scopes - {scopes}", scopes=missing_str
            )
            raise UnauthorizedException(f"Missing required scopes: {missing_str}")

    async def verify_token(self, token: str) -> DescopeSession:
        """
        Verifies the provided authentication token.
        This method retrieves the appropriate signing key, decodes the token,
        and returns a DescopeSession object populated with the token's payload.
        Args:
            token (str): The authentication token to be verified.
        Raises:
            UnauthorizedException: If token verification fails.
        Returns:
            DescopeSession: An object representing the validated session data.
        """

        key = self._get_signing_key(token)
        payload = self._decode_token(token, key)
        return DescopeSession(**payload)


AUTH = TokenVerifier()
