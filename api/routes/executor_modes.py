import json
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Request


from ..lib.util.result import Result
from ..lib.descope.session import get_descope_session
from ..routes.limiter import limiter
from ..models.executor_modes.v1_0.cbib_response import CbibResponse
from ..models.descope.descope_session import DescopeSession


router = APIRouter(prefix="/api/v1/executor_modes", tags=["Executor Modes"])


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


@router.get(
    "/{version}/cbib",
    response_model=CbibResponse,
)
@limiter.limit("15/minute")
async def get_template_cbib(
    version: str,
    request: Request,
    session: DescopeSession = Depends(get_descope_session),
):
    v_result = _validate_version_str(version)
    if not Result.is_success(v_result):
        raise HTTPException(status_code=400, detail=str(v_result.error))
    ver = v_result.data
    path = Path(f"api/templates/executor_modes/{ver}/cbib.json")
    if not path.exists():
        raise HTTPException(status_code=404, detail="CBIB file not found.")
    json_content = json.loads(path.read_text())
    return CbibResponse(**json_content)


@router.get(
    "/CANONICAL-EXECUTOR-MODE-V{version}",
    response_model=CbibResponse,
)
@limiter.limit("15/minute")
async def executor_modes(
    version: str,
    request: Request,
    session: DescopeSession = Depends(get_descope_session),
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
    return CbibResponse(**json_content)
