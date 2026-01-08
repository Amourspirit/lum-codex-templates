import json
from datetime import datetime
from pathlib import Path
from typing import Any
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import PlainTextResponse, JSONResponse
from fastapi_cache.decorator import cache
from fastapi.responses import Response

from src import verify
from ..responses.markdown_response import MarkdownResponse
from src.template.front_mater_meta import FrontMatterMeta
from ..models.artifact_submission import ArtifactSubmission
from ..lib.util.result import Result
from ..lib.verify.verify_meta_fields import VerifyMetaFields
from ..lib.cleanup.clean_meta_fields import CleanMetaFields

router = APIRouter()
API_RELATIVE_URL = "/api/v1"


@router.get(
    "/api/v1/templates/{template_type}/{version}",
    response_class=MarkdownResponse,
)
@cache(expire=300)  # Cache for 300 seconds
async def get_template(template_type: str, version: str, request: Request):
    path = Path(f"api/templates/{template_type}/{version}/template.md")
    if not path.exists():
        raise HTTPException(status_code=404, detail="Template file not found.")
    fm = FrontMatterMeta(file_path=path)

    # host = request.headers.get("x-forwarded-host") or request.headers.get("host")
    base_url = str(request.base_url).rstrip("/")  # http://127.0.0.1:8000/
    app_root_url = base_url + API_RELATIVE_URL

    if fm.has_field("template_registry"):
        api_path = f"{app_root_url}/templates/{template_type}/{version}/registry"
        fm.frontmatter["template_registry"]["api_path"] = api_path
        fm.recompute_sha256()

    if not fm.has_field("instruction_info"):
        fm.set_field("instruction_info", {})
    fm.frontmatter["instruction_info"]["id"] = "instructions"
    fm.frontmatter["instruction_info"]["api_path"] = (
        f"{app_root_url}/templates/{template_type}/{version}/instructions"
    )

    text = fm.get_template_text()

    return text


@router.get(
    "/api/v1/templates/{template_type}/{version}/instructions",
    response_class=MarkdownResponse,
)
@cache(expire=300)  # Cache for 300 seconds
async def get_template_instructions(template_type: str, version: str, request: Request):
    path = Path(f"api/templates/{template_type}/{version}/instructions.md")
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
            f"{app_root_url}/templates/{template_type}/{version}/registry"
        )
    if fm.has_field("template_info"):
        fm.frontmatter["template_info"]["api_path"] = (
            f"{app_root_url}/templates/{template_type}/{version}"
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
async def get_template_manifest(template_type: str, version: str, request: Request):
    path = Path(f"api/templates/{template_type}/{version}/manifest.json")
    if not path.exists():
        raise HTTPException(status_code=404, detail="Manifest file not found.")
    json_content: dict = json.loads(path.read_text())

    # host = request.headers.get("x-forwarded-host") or request.headers.get("host")
    base_url = str(request.base_url).rstrip("/")  # http://127.0.0.1:8000/
    app_root_url = base_url + API_RELATIVE_URL
    json_content["template_api_path"] = (
        f"{app_root_url}/templates/{template_type}/{version}"
    )
    json_content["instructions_api_path"] = (
        f"{app_root_url}/templates/{template_type}/{version}/instructions"
    )
    json_content["registry_api_path"] = (
        f"{app_root_url}/templates/{template_type}/{version}/registry"
    )
    json_content["executor_mode_api_path"] = (
        f"{app_root_url}/executor_modes/{json_content['canonical_mode']['executor_mode']}-V{json_content['canonical_mode']['version']}"
    )
    return json_content


@router.get(
    "/api/v1/templates/{template_type}/{version}/registry",
    response_class=JSONResponse,
)
async def get_template_registry(template_type: str, version: str):
    path = Path(f"api/templates/{template_type}/{version}/registry.json")
    if not path.exists():
        raise HTTPException(status_code=404, detail="Registry file not found.")
    json_content = json.loads(path.read_text())
    return json_content


@router.get(
    "/api/v1/executor_modes/{version}/cbib",
    response_class=JSONResponse,
)
async def get_template_cbib(version: str):
    path = Path(f"api/templates/executor_modes/{version}/cbib.json")
    if not path.exists():
        raise HTTPException(status_code=404, detail="CBIB file not found.")
    json_content = json.loads(path.read_text())
    return json_content


@router.get(
    "/api/v1/templates/{template_type}/{version}/status",
    response_class=JSONResponse,
)
async def get_template_status(template_type: str, version: str):
    dt_now = datetime.now().astimezone()
    status = {
        "status": "available",
        "template": "available",
        "registry": "available",
        "manifest": "available",
        "instructions": "available",
        "template_type": template_type,
        "template_version": version,
        "last_verified": dt_now.isoformat(),
    }
    json_content = json.loads(json.dumps(status))
    return json_content


@router.get(
    "/api/v1/executor_modes/CANONICAL-EXECUTOR-MODE-V{version}",
    response_class=JSONResponse,
)
async def executor_modes(version: str):
    path = Path(f"api/templates/executor_modes/v{version}/cbib.json")
    if not path.exists():
        raise HTTPException(status_code=404, detail="CBIB file not found.")
    json_content = json.loads(path.read_text())
    return json_content


@router.get("/api/v1/templates/verify")
def verify_artifact(submission: ArtifactSubmission, request: Request):
    s_fm = submission.template_frontmatter.strip()
    if not s_fm:
        raise HTTPException(
            status_code=400, detail="Template frontmatter cannot be empty."
        )
    s_body = submission.template_body.strip()
    if not s_body:
        raise HTTPException(
            status_code=400, detail="Template body content cannot be empty."
        )

    if not s_fm.startswith("---"):
        s_fm = "---\n" + s_fm
    if not s_fm.endswith("---"):
        s_fm = s_fm + "\n---\n"
    content = s_fm + "\n" + s_body
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


@router.get("/api/v1/templates/finalize")
def finalize_artifact(submission: ArtifactSubmission):
    # cleanup and add any final fields before storage
    s_fm = submission.template_frontmatter.strip()
    if not s_fm:
        raise HTTPException(
            status_code=400, detail="Template frontmatter cannot be empty."
        )
    s_body = submission.template_body.strip()
    if not s_body:
        raise HTTPException(
            status_code=400, detail="Template body content cannot be empty."
        )

    if not s_fm.startswith("---"):
        s_fm = "---\n" + s_fm
    if not s_fm.endswith("---"):
        s_fm = s_fm + "\n---\n"
    content = s_fm + "\n" + s_body
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

    template_frontmatter = result.get_frontmatter_yaml()
    template_body = result.content

    default_result = {
        "template_frontmatter": template_frontmatter,
        "template_body": template_body,
        "status": "finalized",
    }

    return default_result
