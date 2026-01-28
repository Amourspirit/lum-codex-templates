from typing import Optional
from fastmcp import FastMCP
from fastmcp.server.dependencies import get_access_token
from fastmcp.server.context import Context
from loguru import logger
from api.lib.descope.auth_config import get_settings
from api.lib.routes import fn_template
from api.models.descope.descope_session import DescopeSession
from api.models.templates.template_response import TemplateResponse
from api.lib.user.user_info import get_user_monad_name
from api.lib.mcp import ctx_util
from api.models.templates.template_instruction_response import (
    TemplateInstructionsResponse,
)
from api.config import Config

_SETTINGS = get_settings()


def register_routes(mcp: FastMCP):
    @mcp.tool
    async def get_template(
        template_type: str, version: str, ctx: Context
    ) -> TemplateResponse:
        """
        Retrieve a template by its type and version.

        - **template_type**: The type of the template to retrieve.
        - **version**: The version of the template to retrieve in the format of `vX.Y` or `X.Y`.
        - **artifact_name**: (Optional) Name of the artifact this template is being applied to.

        \f
        Args:
            template_type (str): type of the template to retrieve.
            version (str): version of the template to retrieve.
            request (Request): the incoming HTTP request.
            response (Response): the HTTP response object.
            artifact_name (str, optional): optional name of the artifact this template is being applied to.
            session: DescopeSession = Depends(get_descope_session),

        Raises:
            HTTPException:

        Returns:
            TemplateResponse: The requested template data.
        """
        logger.debug("get_template called")
        if ctx:
            logger.debug("Context received in get_template")
        token = get_access_token()
        if not token:
            raise Exception("Access token is required.")
        # token_verify = TokenVerifier()
        # await token_verify.verify_token(token.)  # type: ignore
        session = DescopeSession(session=token.claims)
        if not session.validate_roles(["mcp.template.user"], match_any=True):
            logger.error("User does not have the required role to access templates.")
            raise Exception("User does not have the required role to access templates.")
        if not session.validate_scopes(["mcp.template:read"], match_any=True):
            logger.error("User does not have the required scope to access templates.")
            raise Exception(
                "User does not have the required scope to access templates."
            )

        app_root_url = ctx_util.get_request_app_root_url(ctx=ctx, return_default=True)

        monad_name = get_user_monad_name(session=session)

        # Call the shared logic

        return await fn_template.get_template(
            template_type=template_type,
            version=version,
            app_root_url=app_root_url,
            monad_name=monad_name,
        )

    @mcp.tool
    async def get_template_instructions(
        template_type: str,
        version: str,
        ctx: Context,
        artifact_name: Optional[str] = None,
    ) -> TemplateInstructionsResponse:
        """
        Retrieves and processes the instruction text for a specific template type and version.
        This endpoint reads the corresponding markdown file. It dynamically
        replaces placeholders for API URLs and artifact names, and populates
        frontmatter metadata with absolute API paths.

        - **template_type**: The type of the template.
        - **version**: The version of the template in the format of `vX.Y` or `X.Y`.
        - **artifact_name**: (Optional) Name of the artifact this template is being applied to.

        \f
        Args:
            template_type (str): The category or type of the template.
            version (str): The specific version of the template to retrieve.
            request (Request): The FastAPI request object used to resolve base URLs.
            response (Response): The FastAPI response object used to set custom headers.
            artifact_name (str, optional): An optional name of the artifact to be injected
                into the template text. Defaults to None.
            session (DescopeSession): The authenticated user session containing security scopes.
        Returns:
            str: The processed template instructions with placeholders resolved.
        Raises:
            HTTPException:
                - 401 Unauthorized: If no session is provided.
                - 403 Forbidden: If the session lacks the required scopes.
                - 400 Bad Request: If the version string format is invalid.
                - 404 Not Found: If the instruction file does not exist at the expected path.
        """

        # raise an error if the session.scopes do not match at least 1 of the template scopes
        logger.debug("get_template called")
        if ctx:
            logger.debug("Context received in get_template")
        token = get_access_token()
        if not token:
            raise Exception("Access token is required.")
        # token_verify = TokenVerifier()
        # await token_verify.verify_token(token.)  # type: ignore
        session = DescopeSession(session=token.claims)
        if not session.validate_roles(["mcp.template.user"], match_any=True):
            logger.error("User does not have the required role to access templates.")
            raise Exception("User does not have the required role to access templates.")
        if not session.validate_scopes(["mcp.template:read"], match_any=True):
            logger.error("User does not have the required scope to access templates.")
            raise Exception(
                "User does not have the required scope to access templates."
            )

        # monad_name = get_user_monad_name(session=session)
        cfg = Config()
        return await fn_template.get_template_instructions(
            template_type=template_type,
            version=version,
            app_root_url=cfg.current_api_prefix,
            artifact_name=artifact_name,
        )
