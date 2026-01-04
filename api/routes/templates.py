import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse, JSONResponse
from ..responses.markdown_response import MarkdownResponse
from fastapi.responses import Response
from pathlib import Path

router = APIRouter()


@router.get("/templates/{template_type}/{version}", response_class=MarkdownResponse)
async def get_template(template_type: str, version: str):
    path = Path(f"api/templates/{template_type}/{version}/template.md")
    if not path.exists():
        raise HTTPException(status_code=404, detail="Template file not found.")
    return path.read_text()
    # return Response(content=md, media_type="text/markdown")


@router.get(
    "/templates/{template_type}/{version}/instructions", response_class=MarkdownResponse
)
async def get_template_instructions(template_type: str, version: str):
    path = Path(f"api/templates/{template_type}/{version}/instructions.md")
    if not path.exists():
        raise HTTPException(status_code=404, detail="Instructions file not found.")
    return path.read_text()


@router.get(
    "/templates/{template_type}/{version}/manifest",
    response_class=JSONResponse,
)
async def get_template_manifest(template_type: str, version: str):
    path = Path(f"api/templates/{template_type}/{version}/manifest.json")
    if not path.exists():
        raise HTTPException(status_code=404, detail="Manifest file not found.")
    json_content = json.loads(path.read_text())
    return JSONResponse(content=json_content)


@router.get(
    "/templates/{template_type}/{version}/registry",
    response_class=JSONResponse,
)
async def get_template_registry(template_type: str, version: str):
    path = Path(f"api/templates/{template_type}/{version}/registry.json")
    if not path.exists():
        raise HTTPException(status_code=404, detail="Registry file not found.")
    json_content = json.loads(path.read_text())
    return JSONResponse(content=json_content)


@router.get(
    "/templates/cbib/{version}/cbib",
    response_class=JSONResponse,
)
async def get_template_cbib(version: str):
    path = Path(f"api/templates/cbib/{version}/cbib.json")
    if not path.exists():
        raise HTTPException(status_code=404, detail="CBIB file not found.")
    json_content = json.loads(path.read_text())
    return JSONResponse(content=json_content)
