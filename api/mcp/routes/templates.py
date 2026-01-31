from typing import Any, Optional, Annotated
from fastmcp import FastMCP
from fastmcp.server.context import Context
from fastmcp.dependencies import CurrentContext
from fastmcp.server.dependencies import get_http_headers
from loguru import logger
from api.lib.descope.auth import AUTH
from api.lib.descope.auth_config import get_settings
from api.lib.routes import fn_template
from api.models.descope.descope_session import DescopeSession
from api.models.templates.artifact_submission import ArtifactSubmission
from api.models.templates.finalize_artifact_response import FinalizeArtifactResponse
from api.models.templates.manifest_response import ManifestMcpResponse
from api.models.templates.template_response import TemplateResponse
from api.lib.user.user_info import get_user_monad_name
from api.lib.mcp import ctx_util
from api.models.templates.template_instruction_response import (
    TemplateInstructionsResponse,
)
from api.models.templates.template_status_response import TemplateStatusResponse
from api.config import Config
from api.models.templates.upgrade_artifact_response import UpgradeArtifactResponse
from api.models.templates.upgrade_to_template_submission import (
    UpgradeToTemplateSubmission,
)
from api.models.templates.verify_artifact_response import VerifyArtifactResponse
from api.models.args import ArgTemplateVersion, ArgTemplateType, ArgArtifactName

_SETTINGS = get_settings()


async def _ctx_validate_template_access(ctx: Context) -> DescopeSession:
    if ctx.request_context is None:
        raise Exception("Request context is missing in the provided context.")
    if ctx.request_context.request is None:
        raise Exception("Request is missing in the request context.")
    bearer = ctx.request_context.request.headers.get("Authorization")
    token = bearer.split(" ")[1] if bearer else None
    if not token:
        raise Exception("Access token is required.")
    session = await AUTH.verify_token(token)
    if not session.validate_roles(["mcp.template.user"], match_any=True):
        logger.error("User does not have the required role to access templates.")
        raise Exception("User does not have the required role to access templates.")
    if not session.validate_scopes(["mcp.template:read"], match_any=True):
        logger.error("User does not have the required scope to access templates.")
        raise Exception("User does not have the required scope to access templates.")
    return session


async def _header_validate_access() -> DescopeSession:
    headers = get_http_headers()

    # Get authorization header
    auth_header = headers.get("authorization", "")
    if not auth_header:
        raise Exception("Authorization header is missing.")
    is_bearer = auth_header.startswith("Bearer ")
    if not is_bearer:
        raise Exception("Authorization header must be a Bearer token.")

    token = auth_header.split(" ")[1]
    if not token:
        raise Exception("Access token is required.")
    session = await AUTH.verify_token(token)
    if not session.validate_roles(["mcp.template.user"], match_any=True):
        logger.error("User does not have the required role to access templates.")
        raise Exception("User does not have the required role to access templates.")
    if not session.validate_scopes(["mcp.template:read"], match_any=True):
        logger.error("User does not have the required scope to access templates.")
        raise Exception("User does not have the required scope to access templates.")
    return session


def register_routes(mcp: FastMCP):
    @mcp.tool(
        title="Get Codex Template",
        description="Retrieve a codex template by its type and version. The template consists of Frontmatter metadata and markdown content that contain placeholders for dynamic values.",
        tags=set(["codex-template"]),
    )
    async def get_template(
        input_type: ArgTemplateType,
        input_ver: ArgTemplateVersion,
        ctx: Context = CurrentContext(),
    ) -> TemplateResponse:
        """
        Retrieve a template by its type and version.

        Args:
            input_type (ArgTemplateType): type of the template to retrieve.
            input_ver (ArgTemplateVersion): version of the template to retrieve.
            ctx (Context): The FastMCP context object containing request information. Automatically provided.

        Raises:
            Exception: on errors such as authentication failure or insufficient permissions.

        Returns:
            TemplateResponse: The requested template data.
        """
        logger.debug("get_template called")

        try:
            session = await _header_validate_access()
        except Exception as e:
            raise Exception(f"Authentication failed: {str(e)}")

        app_root_url = ctx_util.get_request_app_root_url(ctx=ctx, return_default=True)

        monad_name = get_user_monad_name(session=session)

        # Call the shared logic

        return await fn_template.get_template(
            template_type=input_type.type,
            version=input_ver.version,
            app_root_url=app_root_url,
            monad_name=monad_name,
        )

    @mcp.tool(
        title="Get Codex Template Instructions",
        description="Retrieves the instruction for a specific codex template type and version.",
        tags=set(["codex-template"]),
    )
    async def get_template_instructions(
        input_type: ArgTemplateType,
        input_ver: ArgTemplateVersion,
        input_artifact_name: Optional[ArgArtifactName] = None,
        ctx: Context = CurrentContext(),
    ) -> TemplateInstructionsResponse:
        """
        Retrieves and processes the instruction text for a specific template type and version.
        This endpoint reads the corresponding markdown file. It dynamically
        replaces placeholders for API URLs and artifact names, and populates
        frontmatter metadata with absolute API paths.

        Args:
            input_type (ArgTemplateType): type of the template to retrieve.
            input_ver (ArgTemplateVersion): version of the template to retrieve.
            ctx (Context): The FastMCP context object containing request information. Automatically provided.
        Returns:
            TemplateInstructionsResponse: The processed template instructions.
        Raises:
            Exception: on errors such as authentication failure or insufficient permissions.
        """

        # raise an error if the session.scopes do not match at least 1 of the template scopes
        logger.debug("get_template called")

        try:
            _ = await _ctx_validate_template_access(ctx=ctx)
        except Exception as e:
            raise Exception(f"Authentication failed: {str(e)}")
        # monad_name = get_user_monad_name(session=session)
        cfg = Config()
        artifact_name = None
        if input_artifact_name is not None:
            artifact_name = input_artifact_name.name
        return await fn_template.get_template_instructions(
            template_type=input_type.type,
            version=input_ver.version,
            app_root_url=cfg.current_api_prefix,
            artifact_name=artifact_name,
        )

    #     @mcp.tool(
    #         title="Get Template Manifest",
    #         description="""Retrieves the manifest for a specific template type and version.

    # - **template_type**: The type of the template.
    # - **version**: The version of the template in the format of `vX.Y` or `X.Y`.
    # """,
    #         tags=set(["codex-template"]),
    #     )
    #     @mcp.resource(
    #         "resource://template_manifest/{template_type}/{version}",  # Use URI template with placeholders
    #         title="Template Manifest",
    #         description="""Retrieves the manifest for a specific template type and version.

    # - **template_type**: The type of the template.
    # - **version**: The version of the template in the format of `vX.Y` or `X.Y`.
    # """,
    #         tags=set(["codex-template"]),
    #         mime_type="application/json",
    #         enabled=True,
    #     )
    @mcp.resource(
        "resource://template_manifest/{template_type}/{version}",
        title="Template Manifest",
        mime_type="application/json",
        tags=set(["codex-template"]),
    )
    async def template_manifest_route(
        template_type: str,
        version: str,
        ctx: Context = CurrentContext(),
    ) -> ManifestMcpResponse:
        """
        Retrieves the manifest for a specific codex template type and version.

        Args:
            template_type (str): The type of the codex template (e.g., 'glyph', 'stone', 'dyad', 'node_reg', etc.).
            version (str): The version of the codex template in the format of `vX.Y` or `X.Y`.
        Returns:
            ManifestResponse: The validated manifest object for the requested codex template.
        Raises:
            Exception: on errors such as authentication failure or insufficient permissions.
        """
        logger.debug("get_template called")

        try:
            _ = await _header_validate_access()
        except Exception as e:
            raise Exception(f"Authentication failed: {str(e)}")
        # app_root_url = ctx_util.get_request_app_root_url(ctx=ctx, return_default=True)

        result = await fn_template.get_template_manifest(
            template_type=template_type,
            version=version,
            app_root_url="",
        )
        return ManifestMcpResponse.from_manifest_response(result)

    @mcp.tool(
        title="Get Codex Template Registry",
        description="""Use this tool to get the codex template registry for a specific template that matches type and version.
The response includes the template registry data, which determines the structure and rules for the codex template Frontmatter of the specified type and version.""",
        tags=set(["codex-template"]),
    )
    async def get_template_registry(
        input_type: ArgTemplateType,
        input_ver: ArgTemplateVersion,
        ctx: Context = CurrentContext(),
    ) -> dict[str, Any]:
        """
        Retrieves and optionally pre-processes a template registry for a given type and version.
        This function validates the user's session and scopes, fetches the requested
        template registry, and applies monad-based pre-processing if a monad name is
        associated with the session. It also sets an optional 'X-Artifact-Name' header
        if an artifact name is provided.

        Args:
            input_type (ArgTemplateType): The category or type of the template registry to retrieve.
            input_ver (ArgTemplateVersion): The specific version of the template registry.
            ctx (Context): The FastMCP context object containing request information. Automatically provided.

        Returns:
            dict: The template registry, which may be pre-processed based on the user's monad context.
        Raises:
            Exception: on errors such as authentication failure or insufficient permissions.
        """
        try:
            session = await _header_validate_access()
        except Exception as e:
            raise Exception(f"Authentication failed: {str(e)}")

        monad_name = get_user_monad_name(session)

        return await fn_template.get_template_registry(
            template_type=input_type.type,
            version=input_ver.version,
            monad_name=monad_name,
        )

    @mcp.tool(
        title="Get Codex Template Status",
        description="""Use this tool to get the status of a specific codex template version.
Retrieve the current status of a specific template version.
This endpoint checks the availability of a template type and its associated
components (registry, manifest, instructions) after verifying user authentication
and required permissions.""",
        tags=set(["codex-template"]),
    )
    async def get_template_status(
        input_type: ArgTemplateType,
        input_ver: ArgTemplateVersion,
        ctx: Context = CurrentContext(),
    ) -> TemplateStatusResponse:
        """
        Retrieve the current status of a specific template version.
        This endpoint checks the availability of a template type and its associated
        components (registry, manifest, instructions) after verifying user authentication
        and required permissions.

        Args:
            input_type (ArgTemplateType): The category or type of the template registry to retrieve.
            input_ver (ArgTemplateVersion): The specific version of the template registry.
            ctx (Context): The FastMCP context object containing request information. Automatically provided.
        Returns:
            TemplateStatusResponse: A response object containing availability status,
                versioning info, and the last verification timestamp.
        Raises:
            Exception: on errors such as authentication failure or insufficient permissions.
        """
        try:
            _ = await _header_validate_access()
        except Exception as e:
            raise Exception(f"Authentication failed: {str(e)}")

        return await fn_template.get_template_status(
            template_type=input_type.type, version=input_ver.version
        )

    @mcp.tool(
        title="Verify Template Artifact",
        description="""Use this tool to verify metadata fields of a codex template artifact against a registered schema.
This endpoint parses the frontmatter from the provided template content, identifies the
appropriate registry version, and validates the fields for completeness, type
correctness, and adherence to defined rules.


- **ArtifactSubmission**: The submission containing the template content to be verified.
        """,
        tags=set(["codex-template"]),
    )
    async def verify_artifact(
        submission: ArtifactSubmission,
        ctx: Context = CurrentContext(),
    ) -> VerifyArtifactResponse:
        """
        Verifies the metadata fields of a template artifact against a registered schema.
        This endpoint parses the frontmatter from the provided template content, identifies the
        appropriate registry version, and validates the fields for completeness, type
        correctness, and adherence to defined rules.

        Args:
            submission (ArtifactSubmission): The submission containing the template content to be verified.
            ctx (Context): The FastMCP context object containing request information. Automatically provided.
        Returns:
            VerifyArtifactResponse: An object containing the validation results, template metadata,
                and related API endpoints if verification is successful.
        Raises:
            Exception: on errors such as authentication failure or insufficient permissions.
        """
        try:
            _ = await _header_validate_access()
        except Exception as e:
            raise Exception(f"Authentication failed: {str(e)}")

        app_root_url = ctx_util.get_request_app_root_url(ctx=ctx, return_default=True)

        return await fn_template.verify_artifact(
            submission=submission, app_root_url=app_root_url
        )

    @mcp.tool(
        title="Finalize Template Submission",
        description="""Use this tool to finalize an artifact submission by validating and cleaning its metadata.
This function parses frontmatter from the submitted content, ensures the specified template type and version exist
within the registry, and cleans metadata fields according to the registry schema.""",
        tags=set(["codex-template"]),
    )
    async def finalize_artifact(
        submission: ArtifactSubmission,
        ctx: Context = CurrentContext(),
    ) -> FinalizeArtifactResponse:
        """
        Finalizes an artifact submission by validating and cleaning its metadata.
        This function performs authentication and authorization checks, parses frontmatter
        from the submitted content, ensures the specified template type and version exist
        within the registry, and cleans metadata fields according to the registry schema.

        Args:
            submission (ArtifactSubmission): The submission data containing the template content.
            ctx (Context): The FastMCP context object containing request information. Automatically provided.
        Returns:
            FinalizeArtifactResponse: An object containing the finalized artifact metadata and related information.
        Raises:
            Exception: on errors such as authentication failure, insufficient permissions.

        """
        try:
            _ = await _header_validate_access()
        except Exception as e:
            raise Exception(f"Authentication failed: {str(e)}")

        return await fn_template.finalize_artifact(submission=submission)

    @mcp.tool(
        title="Upgrade Codex Template Artifact",
        description="""Use this tool to upgrade an artifact to a new codex template version by applying the necessary transformations.
This function validates the new version, parses frontmatter from the submitted content, loads the target codex template, applies the upgrade,
and constructs a response with the upgraded content and metadata.""",
        tags=set(["codex-template"]),
    )
    async def upgrade_to_template(
        submission: UpgradeToTemplateSubmission,
        ctx: Context = CurrentContext(),
    ) -> UpgradeArtifactResponse:
        """
        Upgrade an artifact to a new template version by applying the necessary transformations.
        This function performs authentication and authorization checks, validates the new version,
        parses frontmatter from the submitted content, loads the target template, applies the upgrade,
        and constructs a response with the upgraded content and metadata.

        Args:
            submission (UpgradeToTemplateSubmission): The submission data containing the markdown content and new version.
            ctx (Context): The FastMCP context object containing request information. Automatically provided.
        Returns:
            UpgradeArtifactResponse: An object containing the upgraded artifact content and metadata.
        Raises:
            Exception: on errors such as authentication failure, insufficient permissions.
        """
        try:
            _ = await _header_validate_access()
        except Exception as e:
            raise Exception(f"Authentication failed: {str(e)}")

        app_root_url = ctx_util.get_request_app_root_url(ctx=ctx, return_default=True)

        return await fn_template.upgrade_to_template(
            submission=submission, app_root_url=app_root_url
        )
