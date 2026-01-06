import json
import os
from pathlib import Path
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import PlainTextResponse, JSONResponse
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.decorator import cache
from fastapi.responses import Response
from ..responses.markdown_response import MarkdownResponse
from src.template.front_mater_meta import FrontMatterMeta

router = APIRouter()


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
    api_relative_url = "/api/v1"

    # host = request.headers.get("x-forwarded-host") or request.headers.get("host")
    base_url = str(request.base_url).rstrip("/")  # http://127.0.0.1:8000/
    app_root_url = base_url + api_relative_url

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

    api_relative_url = "/api/v1"

    # host = request.headers.get("x-forwarded-host") or request.headers.get("host")
    base_url = str(request.base_url).rstrip("/")  # http://127.0.0.1:8000/
    app_root_url = base_url + api_relative_url

    content = fm.content.replace("[[API_RELATIVE_URL]]", api_relative_url).replace(
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
async def get_template_manifest(template_type: str, version: str):
    path = Path(f"api/templates/{template_type}/{version}/manifest.json")
    if not path.exists():
        raise HTTPException(status_code=404, detail="Manifest file not found.")
    json_content = json.loads(path.read_text())
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
    "/api/v1/executor_modes/CANONICAL-EXECUTOR-MODE-V{version}",
    response_class=JSONResponse,
)
async def executor_modes(version: str):
    path = Path(f"api/templates/executor_modes/v{version}/cbib.json")
    if not path.exists():
        raise HTTPException(status_code=404, detail="CBIB file not found.")
    json_content = json.loads(path.read_text())
    return json_content
