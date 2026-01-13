from ..env import env_info


def get_user_monad_name(
    session: dict,
) -> str | None:
    session_user = session["data"].get("username", "anonymous")
    user = env_info.get_user_info(session_user)
    if user and user.monad_name:
        return user.monad_name
    return None
