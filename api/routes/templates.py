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


_TEMPLATE_SCOPE = env_info.get_api_scopes("templates")

router = APIRouter(prefix="/api/v1/templates", tags=["Templates"])
_API_RELATIVE_URL = "/api/v1"


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

    path = Path.cwd() / f"api/templates/{template_type}/{ver}/manifest.json"

    if not path.exists():
        raise HTTPException(status_code=404, detail="Manifest file not found.")
    json_content: dict = json.loads(path.read_text())

    # host = request.headers.get("x-forwarded-host") or request.headers.get("host")
    base_url = str(request.base_url).rstrip("/")  # http://127.0.0.1:8000/
    app_root_url = base_url + _API_RELATIVE_URL
    json_content["template_api_path"] = (
        f"{app_root_url}/templates/{template_type}/{ver}"
    )
    json_content["instructions_api_path"] = (
        f"{app_root_url}/templates/{template_type}/{ver}/instructions"
    )
    json_content["registry_api_path"] = (
        f"{app_root_url}/templates/{template_type}/{ver}/registry"
    )
    json_content["manifest_api_path"] = (
        f"{app_root_url}/templates/{template_type}/{ver}/manifest"
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
    path = Path() / f"api/templates/{template_type}/{ver}/registry.json"
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
    path = Path(f"api/templates/{template_type}/{ver}/template.md")
    if not path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Template file not found."
        )
    fm = FrontMatterMeta(file_path=path)

    # host = request.headers.get("x-forwarded-host") or request.headers.get("host")
    base_url = str(request.base_url).rstrip("/")  # http://127.0.0.1:8000/
    app_root_url = base_url + _API_RELATIVE_URL

    if fm.has_field("template_registry"):
        api_path = f"{app_root_url}/templates/{template_type}/{ver}/registry"
        fm.frontmatter["template_registry"]["api_path"] = api_path
        fm.recompute_sha256()

    if not fm.has_field("instruction_info"):
        fm.set_field("instruction_info", {})
    fm.frontmatter["instruction_info"]["id"] = "instructions"
    fm.frontmatter["instruction_info"]["api_path"] = (
        f"{app_root_url}/templates/{template_type}/{ver}/instructions"
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
    path = Path(f"api/templates/{template_type}/{ver}/instructions.md")
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
            f"{app_root_url}/templates/{template_type}/{ver}/registry"
        )
    if fm.has_field("template_info"):
        fm.frontmatter["template_info"]["api_path"] = (
            f"{app_root_url}/templates/{template_type}/{ver}"
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
)
async def get_template_status(
    template_type: str,
    version: str,
    request: Request,
    session: DescopeSession = Depends(get_descope_session),
):
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
    "/verify", response_model=VerifyArtifactResponse, operation_id="verify_artifact"
)
def verify_artifact(
    submission: ArtifactSubmission,
    request: Request,
    response: Response,
    session: DescopeSession = Depends(get_descope_session),
):
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
        f"api/templates/{fm.template_type}/v{fm.template_version}/registry.json"
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
        f"{app_root_url}/templates/{fm.template_type}/v{fm.template_version}"
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
)
def finalize_artifact(
    submission: ArtifactSubmission,
    request: Request,
    session: DescopeSession = Depends(get_descope_session),
):
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
        f"api/templates/{fm.template_type}/v{fm.template_version}/registry.json"
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
    "/upgrade", response_model=UpgradeArtifactResponse, operation_id="upgrade_artifact"
)
def upgrade_to_template(
    submission: UpgradeToTemplateSubmission,
    request: Request,
    session: DescopeSession = Depends(get_descope_session),
):
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
            f"api/templates/{upgrade_fm.template_type}/{new_version}/template.md"
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
