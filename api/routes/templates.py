from loguru import logger
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from fastapi.responses import JSONResponse

from ..models.templates.artifact_submission import ArtifactSubmission
from ..models.templates.template_response import TemplateResponse
from ..models.templates.upgrade_to_template_submission import (
    UpgradeToTemplateSubmission,
)
from ..models.templates.template_status_response import TemplateStatusResponse
from ..models.templates.verify_artifact_response import VerifyArtifactResponse
from ..models.templates.finalize_artifact_response import FinalizeArtifactResponse
from ..models.templates.upgrade_artifact_response import UpgradeArtifactResponse
from ..models.templates.template_instruction_response import (
    TemplateInstructionsResponse,
)
from ..models.templates.manifest_response import ManifestResponse
from ..models.descope.descope_session import DescopeSession
from ..lib.routes import fn_template
from ..lib.user.user_info import get_user_monad_name
from ..lib.descope.session import get_descope_session
from ..lib.env import env_info


_TEMPLATE_SCOPE = env_info.get_api_scopes("templates")

router = APIRouter(prefix="/api/v1/templates", tags=["Templates"])
_API_RELATIVE_URL = "/api/v1"


# rate limiting not working when caching is enabled
# https://github.com/laurentS/slowapi/issues/252
@router.get(
    "/{template_type}/{version}",
    response_model=TemplateResponse,
    operation_id="get_template",
    description="Retrieve the template for a specific type and version.",
    summary="Retrieve a template by type and version",
    tags=["codex-template", "mcp-tool"],
)
async def get_template(
    template_type: str,
    version: str,
    request: Request,
    response: Response,
    artifact_name: str = Query(
        default=None,
        description="Optional name of the artifact this template is being applied to",
    ),
    session: DescopeSession = Depends(get_descope_session),
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

    if artifact_name:
        response.headers["X-Artifact-Name"] = artifact_name

    return await fn_template.get_template(
        template_type=template_type,
        version=version,
        app_root_url=app_root_url,
        monad_name=monad_name,
    )


# rate limiting not working when caching is enabled
@router.get(
    "/{template_type}/{version}/instructions",
    response_model=TemplateInstructionsResponse,
    operation_id="get_template_instructions",
    description="Retrieve the instructions for a specific template type and version.",
    summary="Retrieve template instructions by type and version",
    tags=["codex-template", "mcp-tool"],
)
async def get_template_instructions(
    template_type: str,
    version: str,
    request: Request,
    response: Response,
    artifact_name: str = Query(
        default=None,
        description="Optional name of the artifact this template is being applied to",
    ),
    session: DescopeSession = Depends(get_descope_session),
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

    if artifact_name:
        response.headers["X-Artifact-Name"] = artifact_name

    return await fn_template.get_template_instructions(
        template_type=template_type,
        version=version,
        app_root_url=app_root_url,
        artifact_name=artifact_name,
    )


# rate limiting not working when caching is enabled
@router.get(
    "/{template_type}/{version}/manifest",
    response_model=ManifestResponse,
    operation_id="get_template_manifest",
    description="Retrieve the manifest for a specific template type and version.",
    summary="Retrieve template manifest by type and version",
    tags=["codex-template", "mcp-tool"],
)
async def get_template_manifest(
    template_type: str,
    version: str,
    request: Request,
    response: Response,
    artifact_name: str = Query(
        default=None,
        description="Optional name of the artifact this template is being applied to",
    ),
    session: DescopeSession = Depends(get_descope_session),
) -> ManifestResponse:
    """
    Retrieves the manifest for a specific template type and version.

    - **template_type**: The type of the template.
    - **version**: The version of the template in the format of `vX.Y` or `X.Y`.
    - **artifact_name**: (Optional) Name of the artifact this template is being applied to.

    \f
    Args:
        template_type (str): The category or type of the template.
        version (str): The specific version of the template.
        request (Request): The incoming FastAPI request object.
        response (Response): The FastAPI response object, used to append custom headers.
        artifact_name (str, optional): Optional name of the artifact this template is being applied to.
        session (DescopeSession): The authenticated user session, derived from dependencies.
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

    if artifact_name:
        response.headers["X-Artifact-Name"] = artifact_name

    return await fn_template.get_template_manifest(
        template_type=template_type,
        version=version,
        app_root_url=app_root_url,
    )


@router.get(
    "/{template_type}/{version}/registry",
    response_class=JSONResponse,
    operation_id="get_template_registry",
    description="Retrieve the template registry for a given type and version.",
    summary="Retrieve template registry by type and version",
    tags=["codex-template", "mcp-tool"],
)
async def get_template_registry(
    template_type: str,
    version: str,
    request: Request,
    response: Response,
    artifact_name: str = Query(
        default=None,
        description="Optional name of the artifact this template is being applied to",
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
    - **version**: The version of the template registry in the format of `vX.Y` or `X.Y`.
    - **artifact_name**: (Optional) Name of the artifact this template is being applied to.

    \f
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

    if artifact_name:
        response.headers["X-Artifact-Name"] = artifact_name

    return await fn_template.get_template_registry(
        template_type=template_type,
        version=version,
        monad_name=monad_name,
    )


@router.get(
    "/{template_type}/{version}/status",
    response_model=TemplateStatusResponse,
    operation_id="get_template_status",
    description="Retrieve the current status of a specific template version.",
    summary="Get template status by type and version",
    tags=["codex-template", "mcp-tool"],
)
async def get_template_status(
    template_type: str,
    version: str,
    request: Request,
    session: DescopeSession = Depends(get_descope_session),
):
    """
    Retrieve the current status of a specific template version.
    This endpoint checks the availability of a template type and its associated
    components (registry, manifest, instructions) after verifying user authentication
    and required permissions.

    - **template_type**: The type/category of the template.
    - **version**: The version of the template in the format of `vX.Y` or `X.Y`.

    \f
    Args:
        template_type (str): The category or type designation of the template.
        version (str): The version string of the template to query.
        request (Request): The FastAPI request object.
        session (DescopeSession): The authenticated user session obtained from the dependency.
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

    return await fn_template.get_template_status(
        template_type=template_type, version=version
    )


@router.post(
    "/verify",
    response_model=VerifyArtifactResponse,
    operation_id="post_verify_artifact",
    description="Verify the metadata fields of a template artifact against a registered schema.",
    summary="Verify template artifact metadata fields",
    tags=["codex-template", "mcp-tool"],
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

    return await fn_template.verify_artifact(
        submission=submission, app_root_url=app_root_url
    )


@router.post(
    "/finalize",
    response_model=FinalizeArtifactResponse,
    operation_id="post_finalize_artifact",
    description="Finalize an artifact submission by cleaning and validating its metadata fields.",
    summary="Finalize template artifact metadata fields",
    tags=["codex-template", "mcp-tool"],
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
    response_model=UpgradeArtifactResponse,
    operation_id="post_upgrade_artifact",
    description="Upgrade an artifact to a new template version by applying necessary transformations.",
    summary="Upgrade template artifact to new version",
    tags=["codex-template", "mcp-tool"],
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

    return await fn_template.upgrade_to_template(
        submission=submission, app_root_url=app_root_url
    )
