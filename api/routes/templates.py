import json
from datetime import datetime
from pathlib import Path
from typing import Any, cast
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from fastapi.responses import JSONResponse

# from fastapi_cache.decorator import cache
from pydantic import ValidationError

from ..responses.markdown_response import MarkdownResponse

# from ..routes.limiter import limiter
from ..models.templates.artifact_submission import ArtifactSubmission
from ..models.templates.upgrade_to_template_submission import (
    UpgradeToTemplateSubmission,
)
from ..models.templates.template_status_response import TemplateStatusResponse
from ..models.templates.verify_artifact_response import VerifyArtifactResponse
from ..models.templates.finalize_artifact_response import FinalizeArtifactResponse
from ..models.templates.upgrade_artifact_response import UpgradeArtifactResponse
from ..models.templates.manifest_response import ManifestResponse
from ..models.descope.descope_session import DescopeSession
from ..lib.cleanup.clean_meta_fields import CleanMetaFields
from ..lib.upgrade.upgrade_template import UpgradeTemplate
from ..lib.util.result import Result
from ..lib.verify.verify_meta_fields import VerifyMetaFields
from ..lib.user.user_info import get_user_monad_name
from ..lib.descope.session import get_descope_session
from ..lib.env import env_info
from ..lib.content_processors.pre_processors.pre_process_template import (
    PreProcessTemplate,
)
from ..lib.content_processors.pre_processors.pre_process_registry import (
    PreProcessRegistry,
)
from src.template.front_mater_meta import FrontMatterMeta
from src.config.pkg_config import PkgConfig


_TEMPLATE_SCOPE = env_info.get_api_scopes("templates")

router = APIRouter(prefix="/api/v1/templates", tags=["Templates"])
_API_RELATIVE_URL = "/api/v1"

_TEMPLATE_DIR = PkgConfig().api_info.info_templates.dir_name


def _validate_version_str(version: str) -> Result[str, None] | Result[None, Exception]:
    v = version.strip().lower()
    v = v.lstrip("v")
    if not v:
        return Result(None, Exception("Version cannot be empty."))
    if not v.replace(".", "").isdigit():
        return Result(None, Exception("Invalid version format."))
    if v.isdigit():
        v = f"{v}.0"
    if not v.startswith("v"):
        v = "v" + v
    return Result(v, None)


def _get_template_manifest(template_type: str, version: str, request: Request):
    v_result = _validate_version_str(version)
    if not Result.is_success(v_result):
        raise HTTPException(status_code=400, detail=str(v_result.error))
    ver = v_result.data

    path = Path.cwd() / f"api/{_TEMPLATE_DIR}/{template_type}/{ver}/manifest.json"

    if not path.exists():
        raise HTTPException(status_code=404, detail="Manifest file not found.")
    json_content: dict = json.loads(path.read_text())

    # host = request.headers.get("x-forwarded-host") or request.headers.get("host")
    base_url = str(request.base_url).rstrip("/")  # http://127.0.0.1:8000/
    app_root_url = base_url + _API_RELATIVE_URL
    json_content["template_api_path"] = (
        f"{app_root_url}/{_TEMPLATE_DIR}/{template_type}/{ver}"
    )
    json_content["instructions_api_path"] = (
        f"{app_root_url}/{_TEMPLATE_DIR}/{template_type}/{ver}/instructions"
    )
    json_content["registry_api_path"] = (
        f"{app_root_url}/{_TEMPLATE_DIR}/{template_type}/{ver}/registry"
    )
    json_content["manifest_api_path"] = (
        f"{app_root_url}/{_TEMPLATE_DIR}/{template_type}/{ver}/manifest"
    )
    json_content["executor_mode_api_path"] = (
        f"{app_root_url}/executor_modes/{json_content['canonical_mode']['executor_mode']}-V{json_content['canonical_mode']['version']}"
    )
    return json_content


def _get_template_registry(template_type: str, version: str) -> dict[str, Any]:
    v_result = _validate_version_str(version)
    if not Result.is_success(v_result):
        raise HTTPException(status_code=400, detail=str(v_result.error))
    ver = v_result.data
    path = Path() / f"api/{_TEMPLATE_DIR}/{template_type}/{ver}/registry.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Registry file not found.")
    json_content = cast(dict[str, Any], json.loads(path.read_text()))
    return json_content


# rate limiting not working when caching is enabled
# https://github.com/laurentS/slowapi/issues/252
@router.get(
    "/{template_type}/{version}",
    response_class=MarkdownResponse,
    operation_id="get_template",
    description="Retrieve the template for a specific type and version.",
    summary="Retrieve a template by type and version",
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
):
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
        str: The template content in markdown format.
    """
    # raise an error if the session.scopes do not match at least 1 of the template scopes
    print("Getting template:", template_type, version)
    if session:
        if not session.scopes.intersection(_TEMPLATE_SCOPE.read_scopes):
            # print("Session Scopes:")
            # print(session.scopes)
            # print("Template Read Scopes:")
            # print(_TEMPLATE_SCOPE.read_scopes)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient scope to access template.",
            )
    else:
        print("No session found.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to access template.",
        )
    v_result = _validate_version_str(version)
    if not Result.is_success(v_result):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(v_result.error)
        )
    ver = v_result.data
    path = Path(f"api/{_TEMPLATE_DIR}/{template_type}/{ver}/template.md")
    if not path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Template file not found."
        )
    fm = FrontMatterMeta(file_path=path)

    # host = request.headers.get("x-forwarded-host") or request.headers.get("host")
    base_url = str(request.base_url).rstrip("/")  # http://127.0.0.1:8000/
    app_root_url = base_url + _API_RELATIVE_URL

    if fm.has_field("template_registry"):
        api_path = f"{app_root_url}/{_TEMPLATE_DIR}/{template_type}/{ver}/registry"
        fm.frontmatter["template_registry"]["api_path"] = api_path
        fm.recompute_sha256()

    if not fm.has_field("instruction_info"):
        fm.set_field("instruction_info", {})
    fm.frontmatter["instruction_info"]["id"] = "instructions"
    fm.frontmatter["instruction_info"]["api_path"] = (
        f"{app_root_url}/{_TEMPLATE_DIR}/{template_type}/{ver}/instructions"
    )
    text = fm.get_template_text()

    if session and artifact_name:
        response.headers["X-Artifact-Name"] = artifact_name

    try:
        monad_name = get_user_monad_name(session)
        if monad_name:
            pre_processor = PreProcessTemplate(
                template_content=text, monad_name=monad_name
            )
            processed_text = pre_processor.pre_process_template()
            print(f"Processed template with monad: {monad_name}")
            return processed_text
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error during template pre-processing: {e}"
        )

    return text


# rate limiting not working when caching is enabled
@router.get(
    "/{template_type}/{version}/instructions",
    response_class=MarkdownResponse,
    operation_id="get_template_instructions",
    description="Retrieve the instructions for a specific template type and version.",
    summary="Retrieve template instructions by type and version",
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
):
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
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient scope to access template instructions.",
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to access template instructions.",
        )
    v_result = _validate_version_str(version)
    if not Result.is_success(v_result):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(v_result.error)
        )
    ver = v_result.data
    path = Path(f"api/{_TEMPLATE_DIR}/{template_type}/{ver}/instructions.md")
    if not path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Instructions file not found."
        )
    fm = FrontMatterMeta(file_path=path)

    # host = request.headers.get("x-forwarded-host") or request.headers.get("host")
    base_url = str(request.base_url).rstrip("/")  # http://127.0.0.1:8000/
    app_root_url = base_url + _API_RELATIVE_URL

    content = fm.content.replace("[[API_RELATIVE_URL]]", _API_RELATIVE_URL).replace(
        "[[API_ROOT_URL]]", app_root_url
    )
    fm.content = content

    if fm.has_field("canonical_executor_mode"):
        fm.frontmatter["canonical_executor_mode"]["api_path"] = (
            f"{app_root_url}/executor_modes/CANONICAL-EXECUTOR-MODE-V{fm.frontmatter['canonical_executor_mode']['version']}"
        )

    if fm.has_field("template_registry"):
        fm.frontmatter["template_registry"]["api_path"] = (
            f"{app_root_url}/{_TEMPLATE_DIR}/{template_type}/{ver}/registry"
        )
    if fm.has_field("template_info"):
        fm.frontmatter["template_info"]["api_path"] = (
            f"{app_root_url}/{_TEMPLATE_DIR}/{template_type}/{ver}"
        )

    if artifact_name:
        response.headers["X-Artifact-Name"] = artifact_name

    text = fm.get_template_text()
    if artifact_name:
        text = text.replace("{Artifact Name}", artifact_name)

    return text


# rate limiting not working when caching is enabled
@router.get(
    "/{template_type}/{version}/manifest",
    response_model=ManifestResponse,
    operation_id="get_template_manifest",
    description="Retrieve the manifest for a specific template type and version.",
    summary="Retrieve template manifest by type and version",
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
):
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
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient scope to access template manifest.",
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to access template manifest.",
        )
    try:
        results_dict = _get_template_manifest(template_type, version, request)
        manifest = ManifestResponse(**results_dict)
        if session and artifact_name:
            response.headers["X-Artifact-Name"] = artifact_name
        return manifest
    except ValidationError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Validation error in ManifestResponse: {e}",
        )


@router.get(
    "/{template_type}/{version}/registry",
    response_class=JSONResponse,
    operation_id="get_template_registry",
    description="Retrieve the template registry for a given type and version.",
    summary="Retrieve template registry by type and version",
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
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient scope to access template registry.",
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to access template registry.",
        )
    reg = _get_template_registry(template_type, version)

    try:
        if artifact_name:
            response.headers["X-Artifact-Name"] = artifact_name

        monad_name = get_user_monad_name(session)
        if monad_name:
            pre_processor = PreProcessRegistry(registry=reg, monad_name=monad_name)
            processed_reg = pre_processor.pre_process_registry()
            print(f"Processed registry with monad: {monad_name}")
            return processed_reg
        print("No monad name found in session for registry pre-processing.")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error during registry pre-processing: {e}"
        )
    return reg


@router.get(
    "/{template_type}/{version}/status",
    response_model=TemplateStatusResponse,
    operation_id="get_template_status",
    description="Retrieve the current status of a specific template version.",
    summary="Get template status by type and version",
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
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient scope to access template status.",
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to access template status.",
        )
    v_result = _validate_version_str(version)
    if not Result.is_success(v_result):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(v_result.error)
        )
    ver = v_result.data
    dt_now = datetime.now().astimezone()
    status_dict = {
        "status": "available",
        "template_type": template_type,
        "template_version": ver,
        "template": "available",
        "registry": "available",
        "manifest": "available",
        "instructions": "available",
        "last_verified": dt_now,
    }

    return TemplateStatusResponse(**status_dict)


@router.post(
    "/verify",
    response_model=VerifyArtifactResponse,
    operation_id="verify_artifact",
    description="Verify the metadata fields of a template artifact against a registered schema.",
    summary="Verify template artifact metadata fields",
)
def verify_artifact(
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
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient scope to verify artifact.",
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to verify artifact.",
        )
    content = submission.template_content.strip()
    if not content:
        raise HTTPException(
            status_code=400, detail="Template frontmatter cannot be empty."
        )

    fm = FrontMatterMeta.from_content(content)
    if not fm.template_type:
        raise HTTPException(
            status_code=400,
            detail="Field template_type is not specified in frontmatter.",
        )

    if not fm.template_version:
        raise HTTPException(
            status_code=400,
            detail="Field template_version is not specified in frontmatter.",
        )

    registry_path = Path(
        f"api/{_TEMPLATE_DIR}/{fm.template_type}/v{fm.template_version}/registry.json"
    )
    if not registry_path.is_absolute():
        registry_path = Path.cwd() / registry_path
    if not registry_path.exists():
        raise HTTPException(
            status_code=400,
            detail=f"No registry found for the specified template_type of {fm.template_type} and template_version {fm.template_version} not found.",
        )
    registry: dict[str, Any] = json.loads(registry_path.read_text())

    verify_instance = VerifyMetaFields(registry=registry, fm=fm)
    result = verify_instance.verify()
    if not result.is_success:
        raise HTTPException(
            status_code=500,
            detail=str(result.error),
        )
    # Verification passed, now check hash
    base_url = str(request.base_url).rstrip("/")  # http://127.0.0.1:8000/
    app_root_url = base_url + _API_RELATIVE_URL
    template_api_path = (
        f"{app_root_url}/{_TEMPLATE_DIR}/{fm.template_type}/v{fm.template_version}"
    )
    dt_now = datetime.now().astimezone()
    default_result = {
        "status": 200,
        "template_type": fm.template_type,
        "template_id": fm.template_id,
        "template_version": fm.template_version,
        "registry_id": registry.get("registry_id"),
        "registry_version": registry.get("registry_version"),
        "field_validation": "pass",
        "template_api_path": template_api_path,
        "registry_api_path": f"{template_api_path}/registry",
        "manifest_api_path": f"{template_api_path}/manifest",
        "instructions_api_path": f"{template_api_path}/instructions",
        "verified_at": dt_now.isoformat(),
    }
    data = result.data
    if not data:
        raise HTTPException(
            status_code=500,
            detail="Verification result data is missing.",
        )
    errors: list[str] = []
    if "missing_fields" in data and data["missing_fields"]:
        errors.append("missing fields")
        default_result["status"] = status.HTTP_422_UNPROCESSABLE_ENTITY
        default_result["field_validation"] = "failed"
        default_result["missing_fields"] = data["missing_fields"]
    if "extra_fields" in data and data["extra_fields"]:
        default_result["extra_fields"] = data["extra_fields"]
    if "incorrect_type_fields" in data and data["incorrect_type_fields"]:
        errors.append("incorrect type fields")
        default_result["status"] = status.HTTP_422_UNPROCESSABLE_ENTITY
        default_result["field_validation"] = "failed"
        default_result["incorrect_type_fields"] = data["incorrect_type_fields"]
    if "rule_errors" in data and data["rule_errors"]:
        errors.append("rule errors")
        default_result["status"] = status.HTTP_422_UNPROCESSABLE_ENTITY
        default_result["field_validation"] = "failed"
        default_result["rule_errors"] = data["rule_errors"]

    try:
        result = VerifyArtifactResponse(**default_result)
    except ValidationError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Validation error in VerifyArtifactResponse: {e}",
        )
    if result.status != status.HTTP_200_OK:
        details = {"message": "Template verification failed.", "errors": errors}
        model_details = result.model_dump(
            exclude={
                "status",
                "template_api_path",
                "registry_api_path",
                "manifest_api_path",
                "instructions_api_path",
            }
        )
        details.update(model_details)
        raise HTTPException(
            status_code=result.status,
            detail=details,
        )

    return result


@router.post(
    "/finalize",
    response_model=FinalizeArtifactResponse,
    operation_id="finalize_artifact",
    description="Finalize an artifact submission by cleaning and validating its metadata fields.",
    summary="Finalize template artifact metadata fields",
)
def finalize_artifact(
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
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient scope to finalize artifact.",
            )
    else:
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
    fm = FrontMatterMeta.from_content(content)
    if not fm.template_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Field template_type is not specified in frontmatter.",
        )

    if not fm.template_version:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Field template_version is not specified in frontmatter.",
        )

    registry_path = Path(
        f"api/{_TEMPLATE_DIR}/{fm.template_type}/v{fm.template_version}/registry.json"
    )
    if not registry_path.is_absolute():
        registry_path = Path.cwd() / registry_path
    if not registry_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No registry found for the specified template_type of {fm.template_type} and template_version {fm.template_version} not found.",
        )
    registry: dict[str, Any] = json.loads(registry_path.read_text())

    clean_instance = CleanMetaFields(registry=registry, fm=fm)
    result = clean_instance.cleanup()

    default_result = {
        "template_content": result.get_template_text(),
        "status": status.HTTP_200_OK,
    }

    try:
        finalize_result = FinalizeArtifactResponse(**default_result)
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Validation error in FinalizeArtifactResponse: {e}",
        )
    return finalize_result


@router.post(
    "/upgrade",
    response_model=UpgradeArtifactResponse,
    operation_id="upgrade_artifact",
    description="Upgrade an artifact to a new template version by applying necessary transformations.",
    summary="Upgrade template artifact to new version",
)
def upgrade_to_template(
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
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient scope to upgrade artifact.",
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to upgrade artifact.",
        )
    contents = submission.markdown_content.strip()
    v_result = _validate_version_str(submission.new_version)
    if not Result.is_success(v_result):
        raise HTTPException(status_code=400, detail=str(v_result.error))
    new_version = v_result.data

    if not contents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Template contents cannot be empty.",
        )
    try:
        upgrade_fm = FrontMatterMeta.from_content(contents)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error parsing template contents: {e}",
        )
    if not upgrade_fm.template_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Field template_type is not specified in frontmatter.",
        )

    try:
        path = Path(
            f"api/{_TEMPLATE_DIR}/{upgrade_fm.template_type}/{new_version}/template.md"
        )
        if not path.exists():
            raise HTTPException(status_code=404, detail="Template file not found.")
        template_fm = FrontMatterMeta(file_path=path)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error loading template for type {upgrade_fm.template_type} and version {new_version}: {e}",
        )

    try:
        upgrade_template = UpgradeTemplate(
            upgrade_fm=upgrade_fm, template_fm=template_fm
        )
        upgraded_dict = upgrade_template.apply_upgrade()
        upgraded_fm: FrontMatterMeta = upgraded_dict["frontmatter"]
        extra_fields = upgraded_dict["extra_fields"]
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error applying upgrade: {e}",
        )

    manifest = _get_template_manifest(upgrade_fm.template_type, new_version, request)
    dt_now = datetime.now().astimezone()
    result = {
        "status": status.HTTP_200_OK,
        "template_type": upgrade_fm.template_type,
        "template_id": upgrade_fm.template_id,
        "template_version": new_version,
        "requires_field_being": True,
        "template_content": upgraded_fm.get_template_text(),
        "artifact_name": submission.artifact_name.strip(),
        "upgraded_at": dt_now.isoformat(),
        "template_api_path": manifest["template_api_path"],
        "registry_api_path": manifest["registry_api_path"],
        "manifest_api_path": manifest["manifest_api_path"],
        "instructions_api_path": manifest["instructions_api_path"],
        "executor_mode_api_path": manifest["executor_mode_api_path"],
        "extra_fields": extra_fields,
    }

    try:
        upgrade_result = UpgradeArtifactResponse(**result)
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Validation error in UpgradeArtifactResponse: {e}",
        )

    return upgrade_result
