from loguru import logger
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status, Query
from fastapi import Path as ApiPath
from ..models.descope.descope_session import DescopeSession
from ..responses.markdown_response import MarkdownResponse
from ..lib.descope.session import get_descope_session
from ..lib.env import env_info
from ..lib.util.url_helper import encode_url_component
from ..lib.templates.prompts import apply_template

_TEMPLATE_SCOPE = env_info.get_api_scopes("templates")

router = APIRouter(prefix="/api/v1/prompts", tags=["Prompts"])


# region Template Prompts
@router.get(
    "/mcp_apply_template/{template_type}/{artifact_name}",
    response_class=MarkdownResponse,
    operation_id="prompt_template_apply",
    description="Retrieve a structured prompt for applying an artifact to the latest version of a specified template type. The prompt includes instructions, template content, and registry information to guide the application process.",
    summary="Retrieve a structured prompt for applying an artifact to the latest template version",
)
async def get_apply_template_prompt(
    request: Request,
    response: Response,
    template_type: str = ApiPath(
        ...,
        title="Template Type",
        description="The type of the template to apply to (e.g. `glyph`, `sigil`, `seal`).",
    ),
    artifact_name: str = ApiPath(
        ...,
        title="Artifact Name",
        description="The name of the artifact to apply.",
    ),
    attached_img_name: str | None = Query(
        default=None,
        description="Optional name such as `Glyph` or `Sigil` of an attached image to be included in the prompt.",
    ),
    template_name: str | None = Query(
        default=None,
        description="Optional name of the rendering template such as `apply_01`.",
    ),
    session: DescopeSession = Depends(get_descope_session),
):

    if session:
        if not session.scopes.intersection(_TEMPLATE_SCOPE.read_scopes):
            logger.error("Insufficient scope to access template registry.")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient scope to access template registry.",
            )
    else:
        logger.error("Authentication required to access template registry.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to access template registry.",
        )

    tt = template_type.strip().lower()
    if not tt:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Template type is required.",
        )

    if artifact_name:
        # decode URL-encoded artifact name
        response.headers["X-Artifact-Name"] = encode_url_component(artifact_name)
    else:
        artifact_name = "{artifact_name}"
    try:
        result = apply_template.get_apply_template_prompt(
            template_type=template_type,
            artifact_name=artifact_name,
            attached_img_name=attached_img_name,
            template_name=template_name,
        )
        return result
    except Exception as e:
        logger.error(f"Error generating upgrade template prompt: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating upgrade template prompt: {str(e)}",
        )


@router.get(
    "/mcp_upgrade_template/{template_type}/{artifact_name}",
    response_class=MarkdownResponse,
    operation_id="prompt_template_upgrade",
    description="Retrieve a structured prompt for upgrading an artifact to the latest version of a specified template type. The prompt includes instructions, template content, and registry information to guide the upgrade process.",
    summary="Retrieve a structured prompt for upgrading an artifact to the latest template version",
)
async def get_upgrade_template_prompt(
    request: Request,
    response: Response,
    template_type: str = ApiPath(
        ...,
        title="Template Type",
        description="The type of the template to upgrade to (e.g. `glyph`, `sigil`, `seal`).",
    ),
    artifact_name: str = ApiPath(
        ...,
        title="Artifact Name",
        description="The name of the artifact to upgrade.",
    ),
    attached_img_name: str | None = Query(
        default=None,
        description="Optional name such as `Glyph` or `Sigil` of an attached image to be included in the prompt.",
    ),
    template_name: str | None = Query(
        default=None,
        description="Optional name of the rendering template such as `upgrade_01`.",
    ),
    session: DescopeSession = Depends(get_descope_session),
):

    if session:
        if not session.scopes.intersection(_TEMPLATE_SCOPE.read_scopes):
            logger.error("Insufficient scope to access template registry.")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient scope to access template registry.",
            )
    else:
        logger.error("Authentication required to access template registry.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to access template registry.",
        )

    tt = template_type.strip().lower()
    if not tt:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Template type is required.",
        )

    if artifact_name:
        # decode URL-encoded artifact name
        response.headers["X-Artifact-Name"] = encode_url_component(artifact_name)
    else:
        artifact_name = "{artifact_name}"
    try:
        result = apply_template.get_upgrade_template_prompt(
            template_type=template_type,
            artifact_name=artifact_name,
            attached_img_name=attached_img_name,
            template_name=template_name,
        )
        return result
    except Exception as e:
        logger.error(f"Error generating upgrade template prompt: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating upgrade template prompt: {str(e)}",
        )


# endregion Template Prompts
