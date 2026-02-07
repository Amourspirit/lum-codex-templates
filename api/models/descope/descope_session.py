from typing import Annotated, Any
from pydantic import BaseModel, Field
from functools import cached_property
from loguru import logger


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
    def tenants(self) -> dict[str, Any]:
        """
        Tenants associated with the session.
        Returns:
            dict[str, Any]: A dictionary of tenants.
        """
        return self.session.get("tenants", {})

    @cached_property
    def roles(self) -> set[str]:
        """
        Roles associated with the session.
        Returns:
            set[str]: A list of roles.
        """
        return set(self.session.get("roles", []))

    @cached_property
    def scopes(self) -> set[str]:
        """
        Scopes associated with the session.
        Returns:
            set[str]: A list of scopes.
        """
        # scopes is space delimited string
        scopes_str = self.session.get("scope", "")
        if not scopes_str:
            return set()
        return set(scopes_str.split(" "))

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

    def validate_tenant_roles(
        self, tenant: str, roles: list[str] | str, match_any: bool = False
    ) -> bool:
        """
        Validate that session response has been granted the specified roles on the specified tenant.
            For a multi-tenant environment use validate_tenant_roles function

        Args:
            tenant (str): TenantId. if empty string, validates roles on the global level
            roles (list[str] | str): List of roles to validate for this response
            match_any (bool): If true, validates that at least one of the specified roles is granted. Default is false (all roles must be granted).

        Return value (bool): returns true if all roles granted; false if at least one role not granted
        """
        if isinstance(roles, str):
            roles = [roles]
        granted = set()
        if tenant == "":
            logger.debug(
                "DescopeSession.validate_tenant_roles() Validating global roles: {roles}",
                roles=self.roles,
            )
            granted.update(self.roles)
        else:
            if tenant not in self.tenants:
                logger.debug(
                    "DescopeSession.validate_tenant_roles() tenant {tenant} not found in session tenants",
                    tenant=tenant,
                )
                return False
            granted.update(self.tenants.get(tenant, {}).get("roles", []))
        logger.debug(
            "DescopeSession.validate_tenant_roles() Validating roles for tenant {tenant}: {roles}",
            tenant=tenant,
            roles=granted,
        )
        if match_any:
            for role in roles:
                if role in granted:
                    logger.debug(
                        "DescopeSession.validate_tenant_roles() role {role} granted for tenant {tenant}",
                        role=role,
                        tenant=tenant,
                    )
                    return True
            return False
        for role in roles:
            if role not in granted:
                logger.debug(
                    "DescopeSession.validate_tenant_roles() role {role} NOT granted for tenant {tenant}",
                    role=role,
                    tenant=tenant,
                )
                return False
        return True

    def validate_roles(self, roles: list[str] | str, match_any: bool = False) -> bool:
        """
        Validate that session response has been granted the specified roles on the global level.
        Args:
            roles (list[str] | str): List of roles to validate for this response
            match_any (bool): If true, validates that at least one of the specified roles is granted. Default is false (all roles must be granted).
        Return value (bool): returns true if all roles granted; false if at least one role not granted
        """
        return self.validate_tenant_roles("", roles=roles, match_any=match_any)

    def validate_scopes(self, scopes: list[str] | str, match_any: bool = False) -> bool:
        """
        Validate that session response has been granted the specified scopes.
        Args:
            scopes (list[str] | str): List of scopes to validate for this response
            match_any (bool): If true, validates that at least one of the specified scopes is granted. Default is false (all scopes must be granted).
        Return value (bool): returns true if all scopes granted; false if at least one scope not granted
        """
        local_scopes = self.scopes
        if isinstance(scopes, str):
            scopes = [scopes]
        if match_any:
            for scope in scopes:
                if scope in local_scopes:
                    return True
            return False
        for scope in scopes:
            if scope not in local_scopes:
                return False
        return True
