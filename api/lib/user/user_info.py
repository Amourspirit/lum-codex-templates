from ..env import env_info
from ...models.session.session import Session


def get_user_monad_name(
    session: Session,
) -> str | None:
    session_user = session.data.get("username", "anonymous")
    user = env_info.get_user_info(session_user)
    if user and user.monad_name:
        return user.monad_name
    return None
