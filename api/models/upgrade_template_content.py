from typing import Optional
from pydantic import BaseModel


class UpgradeTemplateContent(BaseModel):
    artifact_name: str
    template_content: str
    new_version: str
    session_id: Optional[str] = None
