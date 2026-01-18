from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse


router = APIRouter(tags=["Privacy Terms"])


@router.get("/privacy", response_class=FileResponse)
async def read_privacy_policy():
    path = Path("api/html/privacy_policy.html")
    if not path.exists():
        raise HTTPException(status_code=404, detail="Privacy Policy file not found.")
    return FileResponse(path)
