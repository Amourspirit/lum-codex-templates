from typing import Annotated, Any
from pydantic import BaseModel, Field
from functools import cached_property


class DescopeSession(BaseModel):
    # Allow cached_property to work with Pydantic
    model_config = {"ignored_types": (cached_property,)}

    session: Annotated[
        dict[str, Any],
        Field(title="Session", description="The session data provided by Descope."),
    ]

    @cached_property
    def iat(self) -> str:
        """
        Issued-at time of the session.
        Returns:
            str: The issued-at time.
        """
        return self.session.get("iat", "")

    @cached_property
    def user_id(self) -> str:
        """
        User ID associated with the session.
        Returns:
            str: The user ID.
        """
        return self.session.get("sub", "")

    @cached_property
    def auth_methods(self) -> set[str]:
        """
        Authentication methods used in the session.
        Returns:
            set[str]: A list of authentication methods (AMR) such as `["oauth"]`
        """
        return set(self.session.get("amr", []))

    @cached_property
    def permissions(self) -> set[str]:
        """
        Permissions associated with the session.
        Returns:
            set[str]: A list of permissions.
        """
        return set(self.session.get("permissions", []))

    @cached_property
    def roles(self) -> set[str]:
        """
        Roles associated with the session.
        Returns:
            set[str]: A list of roles.
        """
        return set(self.session.get("roles", []))

    @cached_property
    def logical_session_id(self) -> str:
        """
        Generate a logical session ID based on user ID and issued-at time.

        Descope does not provide a direct session ID for Access Tokens, so we can use the
        user ID and issued-at time to create a unique identifier.

        Returns:
            str: A string representing the logical session ID.
        """
        return f"{self.user_id}:{self.iat}"
