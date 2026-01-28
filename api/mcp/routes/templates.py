from typing import Any, Optional
from fastmcp import FastMCP
from fastmcp.server.context import Context
from loguru import logger
from api.lib.descope.auth import AUTH
from api.lib.descope.auth_config import get_settings
from api.lib.routes import fn_template
from api.models.descope.descope_session import DescopeSession
from api.models.templates.artifact_submission import ArtifactSubmission
from api.models.templates.finalize_artifact_response import FinalizeArtifactResponse
from api.models.templates.manifest_response import ManifestResponse
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

_SETTINGS = get_settings()


async def _validate_template_access(ctx: Context) -> DescopeSession:
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


def register_routes(mcp: FastMCP):
    @mcp.tool(
        title="Get Template",
        description="""Retrieve a template by its type and version.

- **template_type**: The type of the template to retrieve.
- **version**: The version of the template to retrieve in the format of `vX.Y` or `X.Y`.
""",
        tags=set(["codex-template"]),
    )
    async def get_template(
        template_type: str, version: str, ctx: Context
    ) -> TemplateResponse:
        """
        Retrieve a template by its type and version.

        - **template_type**: The type of the template to retrieve.
        - **version**: The version of the template to retrieve in the format of `vX.Y` or `X.Y`.

        \f
        Args:
            template_type (str): type of the template to retrieve.
            version (str): version of the template to retrieve.
            ctx (Context): The FastMCP context object containing request information. Automatically provided.

        Raises:
            Exception: on errors such as authentication failure or insufficient permissions.

        Returns:
            TemplateResponse: The requested template data.
        """
        logger.debug("get_template called")

        try:
            session = await _validate_template_access(ctx=ctx)
        except Exception as e:
            raise Exception(f"Authentication failed: {str(e)}")

        app_root_url = ctx_util.get_request_app_root_url(ctx=ctx, return_default=True)

        monad_name = get_user_monad_name(session=session)

        # Call the shared logic

        return await fn_template.get_template(
            template_type=template_type,
            version=version,
            app_root_url=app_root_url,
            monad_name=monad_name,
        )

    @mcp.tool(
        title="Get Template Instructions",
        description="""Retrieves and processes the instruction text for a specific template type and version.
This endpoint reads the corresponding markdown file. It dynamically
replaces placeholders for API URLs and artifact names, and populates
frontmatter metadata with absolute API paths.

- **template_type**: The type of the template.
- **version**: The version of the template in the format of `vX.Y` or `X.Y`.
- **artifact_name**: (Optional) Name of the artifact this template is being applied to.
""",
        tags=set(["codex-template"]),
    )
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
            template_type (str): type of the template to retrieve.
            version (str): version of the template to retrieve.
            ctx (Context): The FastMCP context object containing request information. Automatically provided.
        Returns:
            TemplateInstructionsResponse: The processed template instructions.
        Raises:
            Exception: on errors such as authentication failure or insufficient permissions.
        """

        # raise an error if the session.scopes do not match at least 1 of the template scopes
        logger.debug("get_template called")

        try:
            _ = await _validate_template_access(ctx=ctx)
        except Exception as e:
            raise Exception(f"Authentication failed: {str(e)}")
        # monad_name = get_user_monad_name(session=session)
        cfg = Config()
        return await fn_template.get_template_instructions(
            template_type=template_type,
            version=version,
            app_root_url=cfg.current_api_prefix,
            artifact_name=artifact_name,
        )

    @mcp.tool(
        title="Get Template Manifest",
        description="""Retrieves the manifest for a specific template type and version.

- **template_type**: The type of the template.
- **version**: The version of the template in the format of `vX.Y` or `X.Y`.
""",
        tags=set(["codex-template"]),
    )
    async def get_template_manifest(
        template_type: str,
        version: str,
        ctx: Context,
    ) -> ManifestResponse:
        """
        Retrieves the manifest for a specific template type and version.

        Args:
            template_type (str): The category or type of the template.
            version (str): The specific version of the template.
            ctx (Context): The FastMCP context object containing request information. Automatically provided.
        Returns:
            ManifestResponse: The validated manifest object for the requested template.
        Raises:
            Exception: on errors such as authentication failure or insufficient permissions.
        """
        logger.debug("get_template called")

        try:
            _ = await _validate_template_access(ctx=ctx)
        except Exception as e:
            raise Exception(f"Authentication failed: {str(e)}")
        app_root_url = ctx_util.get_request_app_root_url(ctx=ctx, return_default=True)

        return await fn_template.get_template_manifest(
            template_type=template_type,
            version=version,
            app_root_url=app_root_url,
        )

    @mcp.tool(
        title="Get Template Registry",
        description="""Retrieves and optionally pre-processes a template registry for a given type and version.
This function validates the user's session and scopes, fetches the requested
template registry, and applies monad-based pre-processing if a monad name is
associated with the session. It also sets an optional 'X-Artifact-Name' header
if an artifact name is provided.

- **template_type**: The type of the template.
- **version**: The version of the template in the format of `vX.Y` or `X.Y`.
""",
        tags=set(["codex-template"]),
    )
    async def get_template_registry(
        template_type: str,
        version: str,
        ctx: Context,
    ) -> dict[str, Any]:
        """
        Retrieves and optionally pre-processes a template registry for a given type and version.
        This function validates the user's session and scopes, fetches the requested
        template registry, and applies monad-based pre-processing if a monad name is
        associated with the session. It also sets an optional 'X-Artifact-Name' header
        if an artifact name is provided.

        Args:
            template_type (str): The category or type of the template registry to retrieve.
            version (str): The specific version of the template registry.
            request (Request): The incoming FastAPI request object.
            response (Response): The outgoing FastAPI response object used to append custom headers.
            artifact_name (str, optional): The name of the artifact the template is applied to.
                Defaults to None.
            session (DescopeSession): The authenticated user session obtained via dependency injection.
        Returns:
            dict: The template registry, which may be pre-processed based on the user's monad context.
        Raises:
            Exception: on errors such as authentication failure or insufficient permissions.
        """
        try:
            session = await _validate_template_access(ctx=ctx)
        except Exception as e:
            raise Exception(f"Authentication failed: {str(e)}")

        monad_name = get_user_monad_name(session)

        return await fn_template.get_template_registry(
            template_type=template_type,
            version=version,
            monad_name=monad_name,
        )

    @mcp.tool(
        title="Get Template Status",
        description="""Retrieve the current status of a specific template version.
This endpoint checks the availability of a template type and its associated
components (registry, manifest, instructions) after verifying user authentication
and required permissions.

- **template_type**: The type of the template.
- **version**: The version of the template in the format of `vX.Y` or `X.Y`.
        """,
        tags=set(["codex-template"]),
    )
    async def get_template_status(
        template_type: str,
        version: str,
        ctx: Context,
    ) -> TemplateStatusResponse:
        """
        Retrieve the current status of a specific template version.
        This endpoint checks the availability of a template type and its associated
        components (registry, manifest, instructions) after verifying user authentication
        and required permissions.

        Args:
            template_type (str): The category or type designation of the template.
            version (str): The version string of the template to query.
            request (Request): The FastAPI request object.
            session (DescopeSession): The authenticated user session obtained from the dependency.
        Returns:
            TemplateStatusResponse: A response object containing availability status,
                versioning info, and the last verification timestamp.
        Raises:
            Exception: on errors such as authentication failure or insufficient permissions.
        """
        try:
            _ = await _validate_template_access(ctx=ctx)
        except Exception as e:
            raise Exception(f"Authentication failed: {str(e)}")

        return await fn_template.get_template_status(
            template_type=template_type, version=version
        )

    @mcp.tool(
        title="Get Template Status",
        description="""Verifies the metadata fields of a template artifact against a registered schema.
This endpoint parses the frontmatter from the provided template content, identifies the
appropriate registry version, and validates the fields for completeness, type
correctness, and adherence to defined rules.


- **ArtifactSubmission**: The submission containing the template content to be verified.
        """,
        tags=set(["codex-template"]),
    )
    async def verify_artifact(
        submission: ArtifactSubmission,
        ctx: Context,
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
            _ = await _validate_template_access(ctx=ctx)
        except Exception as e:
            raise Exception(f"Authentication failed: {str(e)}")

        app_root_url = ctx_util.get_request_app_root_url(ctx=ctx, return_default=True)

        return await fn_template.verify_artifact(
            submission=submission, app_root_url=app_root_url
        )

    @mcp.tool(
        title="Finalize Template Submission",
        description="""Finalizes an artifact submission by validating and cleaning its metadata.
    This function performs authentication and authorization checks, parses frontmatter
    from the submitted content, ensures the specified template type and version exist
    within the registry, and cleans metadata fields according to the registry schema.


- **ArtifactSubmission**: The submission containing the template content to be verified.
        """,
        tags=set(["codex-template"]),
    )
    async def finalize_artifact(
        submission: ArtifactSubmission,
        ctx: Context,
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
            _ = await _validate_template_access(ctx=ctx)
        except Exception as e:
            raise Exception(f"Authentication failed: {str(e)}")

        return await fn_template.finalize_artifact(submission=submission)

    @mcp.tool(
        title="Upgrade Template Artifact",
        description="""Upgrade an artifact to a new template version by applying the necessary transformations.
    This function performs authentication and authorization checks, validates the new version,
    parses frontmatter from the submitted content, loads the target template, applies the upgrade,
    and constructs a response with the upgraded content and metadata.

- **ArtifactSubmission**: The submission containing the template content to be verified.
        """,
        tags=set(["codex-template"]),
    )
    async def upgrade_to_template(
        submission: UpgradeToTemplateSubmission,
        ctx: Context,
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
            _ = await _validate_template_access(ctx=ctx)
        except Exception as e:
            raise Exception(f"Authentication failed: {str(e)}")

        app_root_url = ctx_util.get_request_app_root_url(ctx=ctx, return_default=True)

        return await fn_template.upgrade_to_template(
            submission=submission, app_root_url=app_root_url
        )
