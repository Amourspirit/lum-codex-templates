from ..env import env_info
from ...models.descope.descope_session import DescopeSession


def get_user_monad_name(
    session: DescopeSession,
) -> str | None:
    user = env_info.get_user_info(session.user_id)
    if user and user.monad_name:
        return user.monad_name
    return None
