import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Header, Request, Response
from fastapi.responses import JSONResponse
from fastapi_cache.decorator import cache
from pydantic import ValidationError


from ..lib.cleanup.clean_meta_fields import CleanMetaFields
from ..lib.upgrade.upgrade_template import UpgradeTemplate
from ..lib.util.result import Result
from ..lib.verify.verify_meta_fields import VerifyMetaFields
from ..models.templates.artifact_submission import ArtifactSubmission
from ..models.templates.upgrade_to_template_submission import (
    UpgradeToTemplateSubmission,
)
from ..models.templates.template_status_response import TemplateStatusResponse
from ..models.templates.verify_artifact_response import VerifyArtifactResponse
from ..models.templates.finalize_artifact_response import FinalizeArtifactResponse
from ..models.templates.upgrade_artifact_response import UpgradeArtifactResponse
from ..models.templates.manifest_response import ManifestResponse
from ..responses.markdown_response import MarkdownResponse
from ..routes.auth import get_current_active_principle
from ..routes.limiter import limiter
from ..lib.decorators.session_decorator import with_session
from ..lib.user.user_info import get_user_monad_name
from ..lib.content_processors.pre_processors.pre_process_template import (
    PreProcessTemplate,
)
from src.template.front_mater_meta import FrontMatterMeta

router = APIRouter(prefix="/api/v1/templates", tags=["templates"])
API_RELATIVE_URL = "/api/v1"


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
    app_root_url = base_url + API_RELATIVE_URL
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


def _get_template_registry(template_type: str, version: str):
    v_result = _validate_version_str(version)
    if not Result.is_success(v_result):
        raise HTTPException(status_code=400, detail=str(v_result.error))
    ver = v_result.data
    path = Path() / f"api/templates/{template_type}/{ver}/registry.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Registry file not found.")
    json_content = json.loads(path.read_text())
    return json_content


# rate limiting not working when caching is enabled
# https://github.com/laurentS/slowapi/issues/252
@router.get(
    "/{template_type}/{version}",
    response_class=MarkdownResponse,
)
@cache(expire=300)  # Cache for 300 seconds
@with_session(optional=False)
async def get_template(
    template_type: str,
    version: str,
    request: Request,
    response: Response,
    current_principle: dict[str, str] = Depends(get_current_active_principle),
    session: Optional[dict] = None,
    x_session_id: str = Header(default=None, alias="X-Session-ID"),
):
    # print("Fetching template:", template_type, version)
    v_result = _validate_version_str(version)
    if not Result.is_success(v_result):
        raise HTTPException(status_code=400, detail=str(v_result.error))
    ver = v_result.data
    path = Path(f"api/templates/{template_type}/{ver}/template.md")
    if not path.exists():
        raise HTTPException(status_code=404, detail="Template file not found.")
    fm = FrontMatterMeta(file_path=path)

    # host = request.headers.get("x-forwarded-host") or request.headers.get("host")
    base_url = str(request.base_url).rstrip("/")  # http://127.0.0.1:8000/
    app_root_url = base_url + API_RELATIVE_URL

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

    if session and "session_id" in session:
        response.headers["X-Session-ID"] = session["session_id"]

    if session:
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
)
@cache(expire=300)  # Cache for 300 seconds
async def get_template_instructions(
    template_type: str,
    version: str,
    request: Request,
    current_principle: dict[str, str] = Depends(get_current_active_principle),
):
    v_result = _validate_version_str(version)
    if not Result.is_success(v_result):
        raise HTTPException(status_code=400, detail=str(v_result.error))
    ver = v_result.data
    path = Path(f"api/templates/{template_type}/{ver}/instructions.md")
    if not path.exists():
        raise HTTPException(status_code=404, detail="Instructions file not found.")
    fm = FrontMatterMeta(file_path=path)

    # host = request.headers.get("x-forwarded-host") or request.headers.get("host")
    base_url = str(request.base_url).rstrip("/")  # http://127.0.0.1:8000/
    app_root_url = base_url + API_RELATIVE_URL

    content = fm.content.replace("[[API_RELATIVE_URL]]", API_RELATIVE_URL).replace(
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

    # fm.frontmatter["canonical_executor_mode"]["api_path"] = (
    #     "/api/v1/executor_modes/CANONICAL-EXECUTOR-MODE-V1.0"
    # )
    text = fm.get_template_text()

    return text


# rate limiting not working when caching is enabled
@router.get(
    "/{template_type}/{version}/manifest",
    response_model=ManifestResponse,
)
@cache(expire=60)  # Cache for 60 seconds
async def get_template_manifest(
    template_type: str,
    version: str,
    request: Request,
    current_principle: dict[str, str] = Depends(get_current_active_principle),
):
    try:
        results_dict = _get_template_manifest(template_type, version, request)
        manifest = ManifestResponse(**results_dict)
        return manifest
    except ValidationError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Validation error in ManifestResponse: {e}",
        )


@router.get(
    "/api/v1/templates/{template_type}/{version}/registry",
    response_class=JSONResponse,
)
@limiter.limit("15/minute")
async def get_template_registry(
    template_type: str,
    version: str,
    request: Request,
    current_principle: dict[str, str] = Depends(get_current_active_principle),
):
    return _get_template_registry(template_type, version)


@router.get(
    "/{template_type}/{version}/status",
    response_model=TemplateStatusResponse,
)
@limiter.limit("15/minute")
async def get_template_status(
    template_type: str,
    version: str,
    request: Request,
    current_principle: dict[str, str] = Depends(get_current_active_principle),
):
    v_result = _validate_version_str(version)
    if not Result.is_success(v_result):
        raise HTTPException(status_code=400, detail=str(v_result.error))
    ver = v_result.data
    dt_now = datetime.now().astimezone()
    status = {
        "status": "available",
        "template_type": template_type,
        "template_version": ver,
        "template": "available",
        "registry": "available",
        "manifest": "available",
        "instructions": "available",
        "last_verified": dt_now,
    }
    json_content = json.loads(json.dumps(status))
    return json_content


@router.post("/verify", response_model=VerifyArtifactResponse)
@limiter.limit("15/minute")
def verify_artifact(
    submission: ArtifactSubmission,
    request: Request,
    current_principle: dict[str, str] = Depends(get_current_active_principle),
):
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
    app_root_url = base_url + API_RELATIVE_URL
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
        default_result["status"] = 422
        default_result["field_validation"] = "failed"
        default_result["missing_fields"] = data["missing_fields"]
    if "extra_fields" in data and data["extra_fields"]:
        default_result["extra_fields"] = data["extra_fields"]
    if "incorrect_type_fields" in data and data["incorrect_type_fields"]:
        errors.append("incorrect type fields")
        default_result["status"] = 422
        default_result["field_validation"] = "failed"
        default_result["incorrect_type_fields"] = data["incorrect_type_fields"]
    if "rule_errors" in data and data["rule_errors"]:
        errors.append("rule errors")
        default_result["status"] = 422
        default_result["field_validation"] = "failed"
        default_result["rule_errors"] = data["rule_errors"]

    try:
        result = VerifyArtifactResponse(**default_result)
    except ValidationError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Validation error in VerifyArtifactResponse: {e}",
        )
    if result.status != 200:
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


@router.post("/finalize", response_model=FinalizeArtifactResponse)
@limiter.limit("15/minute")
def finalize_artifact(
    submission: ArtifactSubmission,
    request: Request,
    current_principle: dict[str, str] = Depends(get_current_active_principle),
):
    # cleanup and add any final fields before storage
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

    clean_instance = CleanMetaFields(registry=registry, fm=fm)
    result = clean_instance.cleanup()

    default_result = {
        "template_content": result.get_template_text(),
        "status": 200,
    }

    try:
        finalize_result = FinalizeArtifactResponse(**default_result)
    except ValidationError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Validation error in FinalizeArtifactResponse: {e}",
        )
    return finalize_result


@router.post("/upgrade", response_model=UpgradeArtifactResponse)
@limiter.limit("15/minute")
def upgrade_to_template(
    submission: UpgradeToTemplateSubmission,
    request: Request,
    current_principle: dict[str, str] = Depends(get_current_active_principle),
):
    if submission.session_id:
        print(
            f"Session {submission.session_id} upgrading {submission.artifact_name} v{submission.new_version}"
        )

    contents = submission.markdown_content.strip()
    v_result = _validate_version_str(submission.new_version)
    if not Result.is_success(v_result):
        raise HTTPException(status_code=400, detail=str(v_result.error))
    new_version = v_result.data

    if not contents:
        raise HTTPException(
            status_code=400, detail="Template contents cannot be empty."
        )
    try:
        upgrade_fm = FrontMatterMeta.from_content(contents)
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Error parsing template contents: {e}"
        )
    if not upgrade_fm.template_type:
        raise HTTPException(
            status_code=400,
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
        "status": 200,
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
            status_code=500,
            detail=f"Validation error in UpgradeArtifactResponse: {e}",
        )
    return upgrade_result
