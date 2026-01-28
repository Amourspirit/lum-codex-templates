from fastmcp.server.context import Context
from loguru import logger
from api.lib.descope.auth_config import get_settings

_CONFIG = get_settings()


def get_request_app_root_url(ctx: Context, return_default: bool = True) -> str:
    """
    Extract the application root URL from the request context within the provided Context.

    Args:
        ctx (Context): The FastMCP context containing the request context.
        return_default (bool): Whether to return the default BASE_URL from configuration
                               if extraction fails. Defaults to True.

    Raises:
        Exception: If invalid context is provided and return_default is False.
    Returns:
        str: The application root URL constructed from the request's base URL
        or the default BASE_URL from configuration if extraction fails and return_default is True.
    """
    try:
        if ctx.request_context is None:
            raise ValueError("Request context is None")
        if ctx.request_context.request is None:
            raise ValueError("Request is None in request context")
        parsed_url = ctx.request_context.request.base_url
        app_root_url = f"{parsed_url.scheme}://{parsed_url.netloc}".rstrip("/")
        logger.debug("Extracted app_root_url from request: {url}", url=app_root_url)
        return app_root_url
    except Exception as e:
        if return_default:
            logger.debug(
                "Returning Default, Failed to parse app_root_url from request: {error}",
                error=e,
            )
            return _CONFIG.BASE_URL or "http://localhost:8000"  # Default/fallback
        else:
            logger.error(
                "Failed to parse app_root_url from request and return_default is False: {error}",
                error=e,
            )
            raise e
