import os
from fastapi import APIRouter
from fastapi import Depends
from api.models.descope.descope_session import DescopeSession
from api.lib.descope.session import get_descope_session


router = APIRouter(tags=["Environment"])


@router.get("/env_check/{env_var}", operation_id="env_check")
async def env_check(
    env_var: str, session_user: DescopeSession = Depends(get_descope_session)
):
    """Check whether a specified environment variable is set and report its status.
    Args:
        env_var: The name of the environment variable to inspect.
    Returns:
        A dictionary containing the environment variable name, whether it is set,
        and, if applicable, the type of the stored value.
    """

    value = os.getenv(env_var, None)
    if value is None:
        return {"env_var": env_var, "value": "Not Set"}
    return {"env_var": env_var, "value": "Is Set", "type": str(type(value))}
