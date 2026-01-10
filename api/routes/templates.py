import json
from datetime import datetime
from pathlib import Path
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi_cache.decorator import cache
from fastapi.responses import Response


from ..lib.cleanup.clean_meta_fields import CleanMetaFields
from ..lib.upgrade.upgrade_template import UpgradeTemplate
from ..lib.util.result import Result
from ..lib.verify.verify_meta_fields import VerifyMetaFields
from ..models.artifact_submission import ArtifactSubmission
from ..models.upgrade_template_content import UpgradeTemplateContent
from ..responses.markdown_response import MarkdownResponse
from ..routes.auth import get_current_active_principle
from src.template.front_mater_meta import FrontMatterMeta

router = APIRouter()
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


@router.get(
    "/api/v1/templates/{template_type}/{version}",
    response_class=MarkdownResponse,
)
@cache(expire=300)  # Cache for 300 seconds
async def get_template(
    template_type: str,
    version: str,
    request: Request,
    current_principle: dict[str, str] = Depends(get_current_active_principle),
):
    print("Fetching template:", template_type, version)
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

    return text


@router.get(
    "/api/v1/templates/{template_type}/{version}/instructions",
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


@router.get(
    "/api/v1/templates/{template_type}/{version}/manifest",
    response_class=JSONResponse,
)
@cache(expire=60)  # Cache for 60 seconds
async def get_template_manifest(
    template_type: str,
    version: str,
    request: Request,
    current_principle: dict[str, str] = Depends(get_current_active_principle),
):
    return _get_template_manifest(template_type, version, request)


@router.get(
    "/api/v1/templates/{template_type}/{version}/registry",
    response_class=JSONResponse,
)
async def get_template_registry(
    template_type: str,
    version: str,
    current_principle: dict[str, str] = Depends(get_current_active_principle),
):
    return _get_template_registry(template_type, version)


@router.get(
    "/api/v1/executor_modes/{version}/cbib",
    response_class=JSONResponse,
)
async def get_template_cbib(
    version: str,
    current_principle: dict[str, str] = Depends(get_current_active_principle),
):
    v_result = _validate_version_str(version)
    if not Result.is_success(v_result):
        raise HTTPException(status_code=400, detail=str(v_result.error))
    ver = v_result.data
    path = Path(f"api/templates/executor_modes/{ver}/cbib.json")
    if not path.exists():
        raise HTTPException(status_code=404, detail="CBIB file not found.")
    json_content = json.loads(path.read_text())
    return json_content


@router.get(
    "/api/v1/templates/{template_type}/{version}/status",
    response_class=JSONResponse,
)
async def get_template_status(
    template_type: str,
    version: str,
    current_principle: dict[str, str] = Depends(get_current_active_principle),
):
    v_result = _validate_version_str(version)
    if not Result.is_success(v_result):
        raise HTTPException(status_code=400, detail=str(v_result.error))
    ver = v_result.data
    dt_now = datetime.now().astimezone()
    status = {
        "status": "available",
        "template": "available",
        "registry": "available",
        "manifest": "available",
        "instructions": "available",
        "template_type": template_type,
        "template_version": ver,
        "last_verified": dt_now.isoformat(),
    }
    json_content = json.loads(json.dumps(status))
    return json_content


@router.get(
    "/api/v1/executor_modes/CANONICAL-EXECUTOR-MODE-V{version}",
    response_class=JSONResponse,
)
async def executor_modes(
    version: str,
    current_principle: dict[str, str] = Depends(get_current_active_principle),
):
    # check if version is only a number
    v_result = _validate_version_str(version)
    if not Result.is_success(v_result):
        raise HTTPException(status_code=400, detail=str(v_result.error))
    ver = v_result.data
    path = Path(f"api/templates/executor_modes/{ver}/cbib.json")
    if not path.exists():
        raise HTTPException(status_code=404, detail="CBIB file not found.")
    json_content = json.loads(path.read_text())
    return json_content


@router.post("/api/v1/templates/verify", response_class=JSONResponse)
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
        "status": "verified",
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
        return default_result
    if "missing_fields" in data and data["missing_fields"]:
        default_result["status"] = "failed"
        default_result["field_validation"] = "failed"
        default_result["missing_fields"] = data["missing_fields"]
    if "extra_fields" in data and data["extra_fields"]:
        default_result["extra_fields"] = data["extra_fields"]
    if "incorrect_type_fields" in data and data["incorrect_type_fields"]:
        default_result["field_validation"] = "failed"
        default_result["incorrect_type_fields"] = data["incorrect_type_fields"]
    if "rule_errors" in data and data["rule_errors"]:
        default_result["field_validation"] = "failed"
        default_result["rule_errors"] = data["rule_errors"]

    return default_result


@router.post("/api/v1/templates/finalize", response_class=JSONResponse)
def finalize_artifact(
    submission: ArtifactSubmission,
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
        "status": "finalized",
    }

    return default_result


@router.post("/api/v1/templates/upgrade", response_class=JSONResponse)
def upgrade_template(
    submission: UpgradeTemplateContent,
    request: Request,
    current_principle: dict[str, str] = Depends(get_current_active_principle),
):
    # cleanup and add any final fields before storage
    contents = submission.template_content.strip()
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

    result = {
        "status": "success",
        "content": upgraded_fm.get_template_text(),
        "artifact_name": submission.artifact_name.strip(),
        "requires_field_being": True,
        "template_api_path": manifest["template_api_path"],
        "registry_api_path": manifest["registry_api_path"],
        "instructions_api_path": manifest["instructions_api_path"],
        "manifest_api_path": manifest["manifest_api_path"],
        "executor_mode_api_path": manifest["executor_mode_api_path"],
        "extra_fields": extra_fields,
    }

    return result
