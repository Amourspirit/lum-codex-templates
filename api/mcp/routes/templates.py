from typing import Any
from fastapi import HTTPException, status
from fastmcp import FastMCP
from fastmcp.server.context import Context
from fastmcp.dependencies import CurrentContext
from fastmcp.server.dependencies import get_http_headers
from mcp.types import PromptMessage, TextContent
from loguru import logger
from api.config import Config
from api.lib.descope.auth import AUTH
from api.lib.descope.auth_config import get_settings
from api.lib.kind import ServerModeKind
from api.lib.mcp import ctx_util
from api.lib.routes import fn_template
from api.lib.routes import fn_versions
from api.lib.user.user_info import get_user_monad_name
from api.models.descope.descope_session import DescopeSession
from api.models.templates.artifact_submission import ArtifactSubmission
from api.models.templates.finalize_artifact_response import FinalizeArtifactResponse
from api.models.templates.manifest_response import ManifestMcpResponse
from api.models.templates.template_response import TemplateResponse
from api.models.templates.template_instruction_response import (
    TemplateInstructionsResponse,
)
from api.models.templates.template_status_response import TemplateStatusResponse
from api.models.templates.upgrade_artifact_response import UpgradeArtifactMcpResponse
from api.models.templates.upgrade_to_template_submission import (
    UpgradeToTemplateSubmission,
)
from api.models.templates.verify_artifact_response import VerifyArtifactMcpResponse
from api.models.args import (
    ArgTemplateVersionOptional,
    ArgTemplateType,
    ArgArtifactNameOptional,
)
from api.models.templates.templates_versions import TemplatesVersions

_SETTINGS = get_settings()


# region Support Functions
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


def _get_latest_template_version(template_type: str) -> str:
    """
    Helper function to get the latest version of a given template type.
    Returns the highest version string or None if not found.
    """
    typ = template_type.lower()
    templates_versions = fn_versions.get_available_versions()
    template_entry = templates_versions.templates.get(typ)
    if not template_entry:
        raise ValueError(f"Template type '{typ}' not found.")
    if not template_entry.versions:
        raise ValueError(f"No versions found for template type '{typ}'.")
    ver = template_entry.versions[0]
    return f"v{ver}" if not ver.startswith("v") else ver


# endregion Supprort Functions


def register_routes(mcp: FastMCP):
    # region Tools

    @mcp.tool(
        name="get_codex_template",
        title="Get Codex Template",
        description="""Use this tool to retrieve a codex template by its type and version.
This template can be applied to create or update artifacts with predefined structures and metadata.
The template consists of Frontmatter metadata and markdown content that contain placeholders for dynamic values.""",
        tags=set(["codex-template"]),
        meta={
            "response_content_mime_type": "text/markdown",
            "response_content_has_front_matter": True,
            "requires_field_being_interaction": True,
        },
        annotations={
            "title": "Get Codex Template",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        },
    )
    async def get_template(
        input_type: ArgTemplateType,
        input_ver: ArgTemplateVersionOptional,
        ctx: Context = CurrentContext(),
    ) -> TemplateResponse:
        """
        Retrieve a template by its type and version.

        Args:
            template_type (str): type of the template to retrieve.
            version (str, optional): version of the template to retrieve.
                If not provided, the latest version for the template type will be used.

        Raises:
            Exception: on errors such as authentication failure or insufficient permissions.

        Returns:
            TemplateResponse: The requested template data.
        """
        logger.debug("get_template called")

        try:
            session = await _header_validate_access()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Authentication failed: {str(e)}",
            )

        typ = input_type.type.strip().lower()
        if not typ:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Template type is required.",
            )

        app_root_url = ctx_util.get_request_app_root_url(ctx=ctx, return_default=True)

        monad_name = get_user_monad_name(session=session)

        # Call the shared logic
        if not input_ver.version or input_ver.version == "latest":
            logger.debug("Fetching latest version for template type: {typ}", typ=typ)
            try:
                ver = _get_latest_template_version(template_type=typ)
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
                )
        else:
            ver = input_ver.version.lower()

        return await fn_template.get_template(
            template_type=typ,
            version=ver,
            app_root_url=app_root_url,
            monad_name=monad_name,
            server_mode_kind=ServerModeKind.MCP,
        )

    @mcp.tool(
        name="get_codex_template_instructions",
        title="Get Codex Template Instructions",
        description="""Use this tool to retrieve the instruction for a specific codex template type and version.""",
        tags=set(["codex-template"]),
        annotations={
            "title": "Get Codex Template Instructions",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        },
    )
    async def get_template_instructions(
        input_type: ArgTemplateType,
        input_ver: ArgTemplateVersionOptional,
        input_artifact_name: ArgArtifactNameOptional,
        ctx: Context = CurrentContext(),
    ) -> TemplateInstructionsResponse:
        """
        Retrieves and processes the instruction text for a specific template type and version.
        This endpoint reads the corresponding markdown file. It dynamically
        replaces placeholders for API URLs and artifact names, and populates
        frontmatter metadata with absolute API paths.

        Args:
            input_type (ArgTemplateType): type of the template to retrieve.
            input_ver (ArgTemplateVersionOptional): version of the template to retrieve.
                If not provided, the latest version for the template type will be used.
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
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Authentication failed: {str(e)}",
            )
        # monad_name = get_user_monad_name(session=session)
        if not input_ver.version:
            try:
                ver = _get_latest_template_version(template_type=input_type.type)
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
                )
        else:
            ver = input_ver.version

        cfg = Config()
        artifact_name = None
        if input_artifact_name.name:
            artifact_name = input_artifact_name.name
        return await fn_template.get_template_instructions(
            template_type=input_type.type,
            version=ver,
            app_root_url=cfg.current_api_prefix,
            artifact_name=artifact_name,
            server_mode_kind=ServerModeKind.MCP,
        )

    @mcp.tool(
        name="get_codex_template_registry",
        title="Get Codex Template Registry",
        description="""Use this tool to get the codex template registry for a specific template that matches type and version.
The response includes the template registry data, which determines the structure and rules for the codex template Frontmatter of the specified type and version.""",
        tags=set(["codex-template"]),
        annotations={
            "title": "Get Codex Template Registry",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        },
    )
    async def get_template_registry(
        input_type: ArgTemplateType,
        input_ver: ArgTemplateVersionOptional,
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
            input_ver (ArgTemplateVersionOptional): The specific version of the template registry.
            ctx (Context): The FastMCP context object containing request information. Automatically provided.

        Returns:
            dict: The template registry, which may be pre-processed based on the user's monad context.
        Raises:
            Exception: on errors such as authentication failure or insufficient permissions.
        """
        try:
            session = await _header_validate_access()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Authentication failed: {str(e)}",
            )

        if not input_ver.version:
            try:
                ver = _get_latest_template_version(template_type=input_type.type)
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
                )
        else:
            ver = input_ver.version

        monad_name = get_user_monad_name(session)

        return await fn_template.get_template_registry(
            template_type=input_type.type,
            version=ver,
            monad_name=monad_name,
            server_mode_kind=ServerModeKind.MCP,
        )

    @mcp.tool(
        name="get_codex_template_status",
        title="Get Codex Template Status",
        description="""Use this tool to get the status of a specific codex template version.
Retrieve the current status of a specific template version.
This endpoint checks the availability of a template type and its associated
components (registry, manifest, instructions) after verifying user authentication
and required permissions.""",
        tags=set(["codex-template"]),
        annotations={
            "title": "Get Codex Template Status",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        },
    )
    async def get_template_status(
        input_type: ArgTemplateType,
        input_ver: ArgTemplateVersionOptional,
        ctx: Context = CurrentContext(),
    ) -> TemplateStatusResponse:
        """
        Retrieve the current status of a specific template version.
        This endpoint checks the availability of a template type and its associated
        components (registry, manifest, instructions) after verifying user authentication
        and required permissions.

        Args:
            input_type (ArgTemplateType): The category or type of the template registry to retrieve.
            input_ver (ArgTemplateVersionOptional): The specific version of the template registry.
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
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Authentication failed: {str(e)}",
            )

        if not input_ver.version:
            try:
                ver = _get_latest_template_version(template_type=input_type.type)
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
                )
        else:
            ver = input_ver.version

        return await fn_template.get_template_status(
            template_type=input_type.type,
            version=ver,
            server_mode_kind=ServerModeKind.MCP,
        )

    @mcp.tool(
        name="verify_codex_template_artifact",
        title="Verify Template Artifact",
        description="""Use this tool to verify metadata fields of a codex template artifact against a registered schema.
This endpoint parses the frontmatter from the provided template content, identifies the
appropriate registry version, and validates the fields for completeness, type
correctness, and adherence to defined rules.


- **ArtifactSubmission**: The submission containing the template content to be verified.
        """,
        tags=set(["codex-template"]),
        annotations={
            "title": "Verify Template Artifact",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        },
    )
    async def verify_artifact(
        submission: ArtifactSubmission,
        ctx: Context = CurrentContext(),
    ) -> VerifyArtifactMcpResponse:
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
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Authentication failed: {str(e)}",
            )

        return await fn_template.verify_mcp_artifact(submission=submission)

    @mcp.tool(
        name="finalize_codex_template_artifact",
        title="Finalize Template Submission",
        description="""Use this tool to finalize an artifact submission by validating and cleaning its metadata.
This function parses frontmatter from the submitted content, ensures the specified template type and version exist
within the registry, and cleans metadata fields according to the registry schema.""",
        tags=set(["codex-template"]),
        annotations={
            "title": "Finalize Template Submission",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        },
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
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Authentication failed: {str(e)}",
            )

        return await fn_template.finalize_artifact(
            submission=submission,
            server_mode_kind=ServerModeKind.MCP,
        )

    @mcp.tool(
        name="upgrade_codex_template_artifact",
        title="Upgrade Codex Template Artifact",
        description="""Use this tool to upgrade an artifact to a new codex template version by applying the necessary transformations.
This function validates the new version, parses frontmatter from the submitted content, loads the target codex template, applies the upgrade,
and constructs a response with the upgraded content and metadata.""",
        tags=set(["codex-template"]),
        meta={"output_format": "list"},
        annotations={
            "title": "Upgrade Template",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        },
    )
    async def upgrade_to_template(
        submission: UpgradeToTemplateSubmission,
        ctx: Context = CurrentContext(),
    ) -> UpgradeArtifactMcpResponse:
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
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Authentication failed: {str(e)}",
            )

        app_root_url = ctx_util.get_request_app_root_url(ctx=ctx, return_default=True)

        return await fn_template.upgrade_to_mcp_template(
            submission=submission,
            app_root_url=app_root_url,
            server_mode_kind=ServerModeKind.MCP,
        )

    @mcp.tool(
        name="list_codex_template_versions",
        title="Get Codex Template Versions",
        description="""Use this tool to retrieve the available versions of codex templates.
This function returns a structured response with template versions. The versions are sorted in descending order so that the highest version appears first.""",
        tags=set(["codex-template"]),
        annotations={
            "title": "Template Versions",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        },
    )
    async def get_codex_templates_versions(
        ctx: Context = CurrentContext(),
    ) -> TemplatesVersions:
        try:
            _ = await _header_validate_access()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Authentication failed: {str(e)}",
            )

        return fn_versions.get_available_versions()

    @mcp.tool(
        name="get_codex_template_latest_version",
        title="Get Codex Template Version",
        description="""Use this tool to retrieve the latest version for a specific codex template type.
The return version will have a prefix of 'v', e.g., 'v1.0'.""",
        tags=set(["codex-template"]),
    )
    async def get_codex_template_latest_version(
        input_type: ArgTemplateType,
        ctx: Context = CurrentContext(),
    ) -> str:
        try:
            _ = await _header_validate_access()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Authentication failed: {str(e)}",
            )

        versions = fn_versions.get_available_versions()
        template_entry = versions.templates.get(input_type.type)
        if not template_entry or not template_entry.versions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Template type '{input_type.type}' not found.",
            )
        ver = template_entry.versions[0]
        return f"v{ver}" if not ver.startswith("v") else ver

    @mcp.tool(
        name="list_codex_template_types",
        title="Get Codex Available Template types",
        description="Use this tool to get a list of all available codex template types.",
        tags=set(["codex-template"]),
        meta={"output_format": "list"},
        annotations={
            "title": "Available Templates",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
        },
    )
    async def get_codex_available_template_types(
        ctx: Context = CurrentContext(),
    ) -> list[str]:
        try:
            _ = await _header_validate_access()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Authentication failed: {str(e)}",
            )

        return fn_versions.get_available_template_types()

    # endregion Tools

    # region Resources
    @mcp.resource(
        "manifest://manifest/{template_type}/{?version}",
        name="get_codex_template_manifest",
        title="Template Manifest",
        mime_type="application/json",
        tags=set(["codex-template"]),
        meta={"response_content_mime_type": "application/json"},
        annotations={"readOnlyHint": True, "idempotentHint": True},
    )
    async def manifest(
        template_type: str,
        version: str = "latest",
        ctx: Context = CurrentContext(),
    ) -> ManifestMcpResponse:
        """
        Use this resource to retrieve the manifest for a specific codex template type and version.

        Args:
            template_type (str): The type of the codex template (e.g., 'glyph', 'stone', 'dyad', 'node_reg', etc.).
            version (str, optional): The version of the codex template in the format of `vX.Y` or `X.Y`.
        Returns:
            ManifestResponse: The validated manifest object for the requested codex template.
        Raises:
            Exception: on errors such as authentication failure or insufficient permissions.
        """
        logger.debug("get_template called")

        try:
            _ = await _header_validate_access()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Authentication failed: {str(e)}",
            )

        if not version or version == "latest":
            try:
                ver = _get_latest_template_version(template_type=template_type)
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
                )
        else:
            ver = version

        result = await fn_template.get_template_manifest(
            template_type=template_type,
            version=ver,
            app_root_url="",
            server_mode_kind=ServerModeKind.MCP,
        )
        return ManifestMcpResponse.from_manifest_response(result)

    # endregion Resources

    # region Prompts
    # Prompt returning a specific message type
    @mcp.prompt(name="generate code request", title="Generate Code Request")
    def generate_code_request(language: str, task_description: str) -> PromptMessage:
        """Generates a user message requesting code generation."""
        content = f"Write a {language} function that performs the following task: {task_description}"
        return PromptMessage(
            role="user", content=TextContent(type="text", text=content)
        )

    # endregion Prompts
