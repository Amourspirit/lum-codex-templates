from pydantic import BaseModel


class TemplateParams(BaseModel):
    template_type: str
    template_version: str
