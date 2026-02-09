from os import system

from loguru import logger
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from fastapi.responses import JSONResponse
from mcp.types import PromptMessage, TextContent

from ..models.templates.artifact_submission import ArtifactSubmission
from ..models.templates.upgrade_to_template_submission import (
    UpgradeToTemplateSubmission,
)
from ..models.templates.template_status_response import TemplateStatusResponse
from ..models.templates.verify_artifact_response import VerifyArtifactApiResponse
from ..models.templates.finalize_artifact_response import FinalizeArtifactResponse
from ..models.templates.upgrade_artifact_response import (
    UpgradeArtifactApiResponse,
)
from ..models.templates.manifest_response import ManifestResponse
from ..models.descope.descope_session import DescopeSession
from ..responses.markdown_response import MarkdownResponse
from ..lib.routes import fn_template
from ..lib.user.user_info import get_user_monad_name
from ..lib.descope.session import get_descope_session
from ..lib.env import env_info
from ..lib.routes import fn_versions

_TEMPLATE_SCOPE = env_info.get_api_scopes("templates")

router = APIRouter(prefix="/api/v1/templates", tags=["Templates"])
_API_RELATIVE_URL = "/api/v1"


# region Helper Functions
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


# endregion Helper Functions


# region Template Endpoints


# rate limiting not working when caching is enabled
# https://github.com/laurentS/slowapi/issues/252
@router.get(
    "/{template_type}",
    response_class=MarkdownResponse,
    operation_id="get_template",
    description="Retrieve the template for a specific type and version.",
    summary="Retrieve a template by type and version",
)
async def get_template(
    template_type: str,
    request: Request,
    response: Response,
    artifact_name: str = Query(
        default=None,
        description="Optional name of the artifact this template is being applied to",
    ),
    version: str = Query(
        default=None,
        description="Optional version of the template to retrieve in the format of `vX.Y` or `X.Y`. If not provided, the latest version will be returned.",
    ),
    session: DescopeSession = Depends(get_descope_session),
) -> str:
    """
    Retrieve a template by its type and version.

    - **template_type**: The type of the template to retrieve.
    - **artifact_name**: (Optional) Name of the artifact this template is being applied to.
    - **version**: (optional) The version of the template in the format of `vX.Y` or `X.Y`.

    \f
    Args:
        template_type (str): type of the template to retrieve.
        artifact_name (str, optional): optional name of the artifact this template is being applied to.
            Defaults to None.
        version (str, optional): The specific version of the template to retrieve. If not provided, the latest version will be used.
            Defaults to None.

    Raises:
        HTTPException:

    Returns:
        TemplateResponse: The requested template data.
    """
    # raise an error if the session.scopes do not match at least 1 of the template scopes
    logger.debug(f"Getting template: {template_type}, {version}")
    if session:
        if not session.scopes.intersection(_TEMPLATE_SCOPE.read_scopes):
            # print("Session Scopes:")
            # print(session.scopes)
            # print("Template Read Scopes:")
            # print(_TEMPLATE_SCOPE.read_scopes)
            logger.error("Insufficient scope to access template.")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient scope to access template.",
            )
    else:
        logger.error("Authentication required to access template.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to access template.",
        )

    # host = request.headers.get("x-forwarded-host") or request.headers.get("host")
    base_url = str(request.base_url).rstrip("/")  # http://127.0.0.1:8000/
    app_root_url = base_url + _API_RELATIVE_URL

    monad_name = get_user_monad_name(session)

    if not version:
        try:
            version = _get_latest_template_version(template_type)
            logger.debug(
                "No version specified. Using latest version: {version}", version=version
            )
        except ValueError as e:
            logger.error(str(e))
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    if artifact_name:
        response.headers["X-Artifact-Name"] = artifact_name

    result = await fn_template.get_template(
        template_type=template_type,
        version=version,
        app_root_url=app_root_url,
        monad_name=monad_name,
    )
    return result.content


# rate limiting not working when caching is enabled
@router.get(
    "/{template_type}/instructions",
    response_class=MarkdownResponse,
    operation_id="get_template_instructions",
    description="Retrieve the instructions for a specific template type and version.",
    summary="Retrieve template instructions by type and version",
)
async def get_template_instructions(
    template_type: str,
    request: Request,
    response: Response,
    artifact_name: str = Query(
        default=None,
        description="Optional name of the artifact this template is being applied to",
    ),
    version: str = Query(
        default=None,
        description="Optional version of the template to retrieve in the format of `vX.Y` or `X.Y`. If not provided, the latest version will be returned.",
    ),
    session: DescopeSession = Depends(get_descope_session),
) -> str:
    """
    Retrieves and processes the instruction text for a specific template type and version.
    This endpoint reads the corresponding markdown file. It dynamically
    replaces placeholders for API URLs and artifact names, and populates
    frontmatter metadata with absolute API paths.

    - **template_type**: The type of the template.
    - **artifact_name**: (Optional) Name of the artifact this template is being applied to.
    - **version**: (optional) The version of the template in the format of `vX.Y` or `X.Y`.

    \f
    Args:
        template_type (str): The category or type of the template.
        artifact_name (str, optional): An optional name of the artifact to be injected
            into the template text. Defaults to None.
        version (str, optional): The specific version of the template to retrieve. If not provided, the latest version will be used.
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
    if session:
        if not session.scopes.intersection(_TEMPLATE_SCOPE.read_scopes):
            logger.error("Insufficient scope to access template instructions.")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient scope to access template instructions.",
            )
    else:
        logger.error("Authentication required to access template instructions.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to access template instructions.",
        )

    # host = request.headers.get("x-forwarded-host") or request.headers.get("host")
    base_url = str(request.base_url).rstrip("/")  # http://127.0.0.1:8000/
    app_root_url = base_url + _API_RELATIVE_URL

    if not version:
        try:
            version = _get_latest_template_version(template_type)
            logger.debug(
                "No version specified. Using latest version: {version}", version=version
            )
        except ValueError as e:
            logger.error(str(e))
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    if artifact_name:
        response.headers["X-Artifact-Name"] = artifact_name

    result = await fn_template.get_template_instructions(
        template_type=template_type,
        version=version,
        app_root_url=app_root_url,
        artifact_name=artifact_name,
    )
    return result.content


# rate limiting not working when caching is enabled
@router.get(
    "/{template_type}/manifest",
    response_model=ManifestResponse,
    operation_id="get_template_manifest",
    description="Retrieve the manifest for a specific template type and version.",
    summary="Retrieve template manifest by type and version",
)
async def get_template_manifest(
    template_type: str,
    request: Request,
    response: Response,
    artifact_name: str = Query(
        default=None,
        description="Optional name of the artifact this template is being applied to",
    ),
    version: str = Query(
        default=None,
        description="Optional version of the template to retrieve in the format of `vX.Y` or `X.Y`. If not provided, the latest version will be returned.",
    ),
    session: DescopeSession = Depends(get_descope_session),
) -> ManifestResponse:
    """
    Retrieves the manifest for a specific template type and version.

    - **template_type**: The type of the template.
    - **version**: (optional) The version of the template in the format of `vX.Y` or `X.Y`.
    - **artifact_name**: (Optional) Name of the artifact this template is being applied to.

    \f
    Args:
        template_type (str): The category or type of the template.
        version (str, optional): The specific version of the template to retrieve. If not provided, the latest version will be used.
        artifact_name (str, optional): Optional name of the artifact this template is being applied to.
    Returns:
        ManifestResponse: The validated manifest object for the requested template.
    Raises:
        HTTPException:
            - 401 Unauthorized if no session is provided.
            - 403 Forbidden if the session does not have sufficient read scopes.
            - 500 Internal Server Error if the retrieved manifest fails Pydantic validation.
    """
    if session:
        if not session.scopes.intersection(_TEMPLATE_SCOPE.read_scopes):
            logger.error("Insufficient scope to access template manifest.")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient scope to access template manifest.",
            )
    else:
        logger.error("Authentication required to access template manifest.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to access template manifest.",
        )

    # host = request.headers.get("x-forwarded-host") or request.headers.get("host")
    base_url = str(request.base_url).rstrip("/")  # http://127.0.0.1:8000/
    app_root_url = base_url + _API_RELATIVE_URL

    if not version:
        try:
            version = _get_latest_template_version(template_type)
            logger.debug(
                "No version specified. Using latest version: {version}", version=version
            )
        except ValueError as e:
            logger.error(str(e))
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    if artifact_name:
        response.headers["X-Artifact-Name"] = artifact_name

    return await fn_template.get_template_manifest(
        template_type=template_type,
        version=version,
        app_root_url=app_root_url,
    )


@router.get(
    "/{template_type}/registry",
    response_class=JSONResponse,
    operation_id="get_template_registry",
    description="Retrieve the template registry for a given type and version.",
    summary="Retrieve template registry by type and version",
)
async def get_template_registry(
    template_type: str,
    request: Request,
    response: Response,
    artifact_name: str = Query(
        default=None,
        description="Optional name of the artifact this template is being applied to",
    ),
    version: str = Query(
        default=None,
        description="Optional version of the template to retrieve in the format of `vX.Y` or `X.Y`. If not provided, the latest version will be returned.",
    ),
    session: DescopeSession = Depends(get_descope_session),
):
    """
    Retrieves and optionally pre-processes a template registry for a given type and version.
    This function validates the user's session and scopes, fetches the requested
    template registry, and applies monad-based pre-processing if a monad name is
    associated with the session. It also sets an optional 'X-Artifact-Name' header
    if an artifact name is provided.

    - **template_type**: The type/category of the template registry to retrieve.
    - **artifact_name**: (Optional) Name of the artifact this template is being applied to.
    - **version**: (optional) The version of the template in the format of `vX.Y` or `X.Y`.

    \f
    Args:
        template_type (str): The category or type of the template registry to retrieve.
        artifact_name (str, optional): The name of the artifact the template is applied to.
            Defaults to None.
        version (str, optional): The specific version of the template to retrieve. If not provided, the latest version will be used.
            Defaults to None.
        session (DescopeSession): The authenticated user session obtained via dependency injection.
    Returns:
        dict: The template registry, which may be pre-processed based on the user's monad context.
    Raises:
        HTTPException:
            - 401 Unauthorized: If the session is missing.
            - 403 Forbidden: If the session does not have sufficient scopes.
            - 500 Internal Server Error: If an error occurs during registry pre-processing.
    """
    if session:
        if not session.scopes.intersection(_TEMPLATE_SCOPE.read_scopes):
            logger.error("Insufficient scope to access template registry.")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient scope to access template registry.",
            )
    else:
        logger.error("Authentication required to access template registry.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to access template registry.",
        )

    monad_name = get_user_monad_name(session)

    if not version:
        try:
            version = _get_latest_template_version(template_type)
            logger.debug(
                "No version specified. Using latest version: {version}", version=version
            )
        except ValueError as e:
            logger.error(str(e))
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    if artifact_name:
        response.headers["X-Artifact-Name"] = artifact_name

    return await fn_template.get_template_registry(
        template_type=template_type,
        version=version,
        monad_name=monad_name,
    )


@router.get(
    "/{template_type}/status",
    response_model=TemplateStatusResponse,
    operation_id="get_template_status",
    description="Retrieve the current status of a specific template version.",
    summary="Get template status by type and version",
)
async def get_template_status(
    template_type: str,
    version: str = Query(
        default=None,
        description="Optional version of the template to retrieve in the format of `vX.Y` or `X.Y`. If not provided, the latest version will be returned.",
    ),
    session: DescopeSession = Depends(get_descope_session),
):
    """
    Retrieve the current status of a specific template version.
    This endpoint checks the availability of a template type and its associated
    components (registry, manifest, instructions) after verifying user authentication
    and required permissions.

    - **template_type**: The type/category of the template.
    - **artifact_name**: (Optional) Name of the artifact this template is being applied to.

    \f
    Args:
        template_type (str): The category or type designation of the template.
        version (str, optional): The specific version of the template to retrieve. If not provided, the latest version will be used.
            Defaults to None.
    Returns:
        TemplateStatusResponse: A response object containing availability status,
            versioning info, and the last verification timestamp.
    Raises:
        HTTPException:
            - 401 UNAUTHORIZED: If no valid session is provided.
            - 403 FORBIDDEN: If the session does not have sufficient scopes.
            - 400 BAD_REQUEST: If the provided version string is invalid.
    """
    if session:
        if not session.scopes.intersection(_TEMPLATE_SCOPE.read_scopes):
            logger.error("Insufficient scope to access template status.")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient scope to access template status.",
            )
    else:
        logger.error("Authentication required to access template status.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to access template status.",
        )

    if not version:
        try:
            version = _get_latest_template_version(template_type)
            logger.debug(
                "No version specified. Using latest version: {version}", version=version
            )
        except ValueError as e:
            logger.error(str(e))
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    return await fn_template.get_template_status(
        template_type=template_type, version=version
    )


@router.post(
    "/verify",
    response_model=VerifyArtifactApiResponse,
    operation_id="post_verify_artifact",
    description="Verify the metadata fields of a template artifact against a registered schema.",
    summary="Verify template artifact metadata fields",
)
async def verify_artifact(
    submission: ArtifactSubmission,
    request: Request,
    response: Response,
    session: DescopeSession = Depends(get_descope_session),
):
    """
    Verifies the metadata fields of a template artifact against a registered schema.
    This endpoint parses the frontmatter from the provided template content, identifies the
    appropriate registry version, and validates the fields for completeness, type
    correctness, and adherence to defined rules.

    - **name**: The name of the artifact being verified.
    - **template_content**: The full content of the template, including frontmatter.

    \f
    Args:
        submission (ArtifactSubmission): The submission containing the template content to be verified.
        request (Request): The FastAPI request object, used to generate absolute API paths.
        response (Response): The FastAPI response object.
        session (DescopeSession): The authentication session, injected via dependency,
            containing user scopes.
    Returns:
        VerifyArtifactResponse: An object containing the validation results, template metadata,
            and related API endpoints if verification is successful.
    Raises:
        HTTPException:
            - 401 (Unauthorized): If authentication is missing.
            - 403 (Forbidden): If the session lacks the required read scopes.
            - 400 (Bad Request): If the template content is empty, metadata is missing
              required fields (type/version), or the corresponding registry does not exist.
            - 422 (Unprocessable Entity): If field validation fails (missing fields,
              incorrect types, or rule violations).
            - 500 (Internal Server Error): If verification processing fails or
              response model validation fails.
    """
    if session:
        if not session.scopes.intersection(_TEMPLATE_SCOPE.read_scopes):
            logger.error("Insufficient scope to verify artifact.")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient scope to verify artifact.",
            )
    else:
        logger.error("Authentication required to verify artifact.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to verify artifact.",
        )
    content = submission.template_content.strip()
    if not content:
        raise HTTPException(
            status_code=400, detail="Template frontmatter cannot be empty."
        )

    base_url = str(request.base_url).rstrip("/")  # http://127.0.0.1:8000/
    app_root_url = base_url + _API_RELATIVE_URL

    return await fn_template.verify_api_artifact(
        submission=submission, app_root_url=app_root_url
    )


@router.post(
    "/finalize",
    response_model=FinalizeArtifactResponse,
    operation_id="post_finalize_artifact",
    description="Finalize an artifact submission by cleaning and validating its metadata fields.",
    summary="Finalize template artifact metadata fields",
)
async def finalize_artifact(
    submission: ArtifactSubmission,
    request: Request,
    session: DescopeSession = Depends(get_descope_session),
):
    """
    Finalizes an artifact submission by validating and cleaning its metadata.
    This function performs authentication and authorization checks, parses frontmatter
    from the submitted content, ensures the specified template type and version exist
    within the registry, and cleans metadata fields according to the registry schema.

    - **artifact_name**: Artifact name such as, `Glyph of Silent Blessing`, associated with the template to be upgraded.
    - **template_content**: Markdown contents containing Front-matter and body associated with the artifact to be upgraded.

    \f
    Args:
        submission (ArtifactSubmission): The submission data containing the template content.
        request (Request): The incoming FastAPI request object.
        session (DescopeSession): The authenticated user session derived from the request.
    Returns:
        FinalizeArtifactResponse: A response object containing the cleaned template content
            and a 200 OK status.
    Raises:
        HTTPException (401): If no authenticated session is provided.
        HTTPException (403): If the session lacks the required write scopes.
        HTTPException (400): If the template content is empty or if required frontmatter
            fields (template_type, template_version) are missing.
        HTTPException (404): If the registry file for the specified template type and
            version does not exist.
        HTTPException (500): If there is a validation error when constructing the final
            response object.
    """
    if session:
        if not session.scopes.intersection(_TEMPLATE_SCOPE.write_scopes):
            logger.error("Insufficient scope to finalize artifact.")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient scope to finalize artifact.",
            )
    else:
        logger.error("Authentication required to finalize artifact.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to finalize artifact.",
        )
    # cleanup and add any final fields before storage
    content = submission.template_content.strip()
    if not content:
        raise HTTPException(
            status_code=400, detail="Template frontmatter cannot be empty."
        )

    return await fn_template.finalize_artifact(submission=submission)


@router.post(
    "/upgrade",
    response_model=UpgradeArtifactApiResponse,
    operation_id="post_upgrade_artifact",
    description="Upgrade an artifact to a new template version by applying necessary transformations.",
    summary="Upgrade template artifact to new version",
)
async def upgrade_to_template(
    submission: UpgradeToTemplateSubmission,
    request: Request,
    session: DescopeSession = Depends(get_descope_session),
):
    """
    Upgrade an artifact to a new template version by applying the necessary transformations.
    This function performs authentication and authorization checks, validates the new version,
    parses frontmatter from the submitted content, loads the target template, applies the upgrade,
    and constructs a response with the upgraded content and metadata.

    - **artifact_name**: Artifact name such as, `Glyph of Silent Blessing`, associated with the template to be upgraded.
    - **markdown_content**: Content of the markdown template containing Front-matter and body associated with the artifact to be upgraded.
    - **new_version**: The new version that the template should be upgraded to, e.g., '1.0', '2.10', etc.

    \f
    Args:
        submission (UpgradeToTemplateSubmission): The submission data containing the markdown content and new version.
        request (Request): The incoming FastAPI request object.
        session (DescopeSession): The authenticated user session derived from the request.
    Returns:
        UpgradeArtifactResponse: A response object containing the upgraded template content,
            metadata, and a 200 OK status.
    Raises:
        HTTPException (401): If no authenticated session is provided.
        HTTPException (403): If the session lacks the required write scopes.
        HTTPException (400): If the markdown content is empty, if the new version string is invalid,
            or if required frontmatter fields are missing.
        HTTPException (404): If the target template file for the specified type and version does not exist.
        HTTPException (500): If there is an error applying the upgrade or constructing the final response object.
    """
    if session:
        if not session.scopes.intersection(_TEMPLATE_SCOPE.write_scopes):
            logger.error("Insufficient scope to upgrade artifact.")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient scope to upgrade artifact.",
            )
    else:
        logger.error("Authentication required to upgrade artifact.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to upgrade artifact.",
        )

    base_url = str(request.base_url).rstrip("/")  # http://127.0.0.1:8000/
    app_root_url = base_url + _API_RELATIVE_URL

    return await fn_template.upgrade_to_api_template(
        submission=submission, app_root_url=app_root_url
    )


# endregion Template Endpoints


# region Template Prompts
@router.get(
    "/prompt/{template_type}/{artifact_name}",
    response_class=MarkdownResponse,
    operation_id="prompt_template_upgrade",
    description="Retrieve a structured prompt for upgrading an artifact to the latest version of a specified template type. The prompt includes instructions, template content, and registry information to guide the upgrade process.",
    summary="Retrieve a structured prompt for upgrading an artifact to the latest template version",
)
async def get_template_prompt(
    template_type: str,
    artifact_name: str,
    request: Request,
    response: Response,
    session: DescopeSession = Depends(get_descope_session),
):

    if session:
        if not session.scopes.intersection(_TEMPLATE_SCOPE.read_scopes):
            logger.error("Insufficient scope to access template registry.")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient scope to access template registry.",
            )
    else:
        logger.error("Authentication required to access template registry.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to access template registry.",
        )

    tt = template_type.strip().lower()
    if not tt:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Template type is required.",
        )

    try:
        latest_version = _get_latest_template_version(template_type)
        logger.debug(
            "No version specified. Using latest version: {version}",
            version=latest_version,
        )
    except ValueError as e:
        logger.error(str(e))
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    if artifact_name:
        response.headers["X-Artifact-Name"] = artifact_name

    system_content = (
        "## System Instructions  \n\n"
        "**You are an assistant that can:**  \n"
        "- Call tools (e.g. `get_codex_template_instructions`) to perform active queries.\n"
        "- Load resources (URIs starting with `executor-mode://`) to read static documentation.\n"
        "\n"
        "**Available tools:**  \n"
        "  1. **get_codex_template(input_type: ArgTemplateType, input_ver: ArgTemplateVersionOptional)**\n"
        "    - Use this when you need to get the full template content for a specific type and version.\n"
        "  2. **get_codex_template_instructions(input_type: ArgTemplateType, input_ver: ArgTemplateVersionOptional, input_artifact_name: ArgArtifactNameOptional)**\n"
        "    - Use this when you need to get the instructions on how to apply templates.\n"
        "  3. **get_codex_template_registry(input_type: ArgTemplateType, input_ver: ArgTemplateVersionOptional)**\n"
        "    - Use this when you need to get the registry for the template. This registry determines how the metadata in the template is structured and the rules to apply.\n"
        "  4. **verify_codex_template_artifact(artifact_name: str, template_content: str)**\n"
        "    - Use this to verify the metadata fields of a template artifact against the registered schema.\n"
        "    - Input `template_content` should include the full markdown content with frontmatter.\n"
        "  5. **finalize_codex_template_artifact(artifact_name: str, template_content: str)**\n"
        "    - Use this to finalize an artifact submission by validating and cleaning its metadata.\n"
        "    - Input `template_content` should include the full markdown content with frontmatter.\n"
        "\n\n"
        "## Available resources:  \n"
        "  **1. executor-mode://default_executor_mode**\n"
        "    - Executor mode used when applying templates.\n"
    )

    user_content = (
        "## User Instructions  \n\n"
        f"Upgrade the artifact named '{artifact_name}' to the latest template of type `{tt}` and version '{latest_version}'.  \n"
        f'  1. Call tool `get_codex_template({{"input_type":{{"type":"{tt}"}},"input_ver":{{"version":"{latest_version}"}}}})` to get the full template content.\n'
        "    - This is the target template to upgrade to.\n"
        "  2. Use the resource `executor-mode://default_executor_mode` to understand the executor mode to apply the template.\n"
        f'  3. Call tool `get_codex_template_registry({{"input_type":{{"type":"{tt}"}},"input_ver":{{"version":"{latest_version}"}}}})` to get the template registry.\n'
        "    - Use this registry to understand the structure and rules for the template metadata.\n"
        f'  4. Call tool `get_codex_template_instructions({{"input_type":{{"type":"{tt}"}},"input_ver":{{"version":"{latest_version}"}},"input_artifact_name":{{"name":"{artifact_name}"}}}})` to get the instructions for applying the template.\n'
        "    - Use these instructions to guide the upgrade process.\n"
        "\n"
        "Proceed to upgrade the artifact by applying the template according to the instructions and registry rules.\n"
        "Now that the the upgrade is complete, it is time to verify and finalize the upgraded artifact.\n"
        "\n"
        "4. Pass the upgraded template content, including the full markdown content with frontmatter, to `verify_codex_template_artifact` tool to verify the metadata fields.\n"
        "5. Next, pass the verified template content to `finalize_codex_template_artifact` tool to finalize the artifact submission.\n"
        "6. Provide the finalized artifact as the output."
    )

    return f"{system_content}\n\n{user_content}"


# endregion Template Prompts
