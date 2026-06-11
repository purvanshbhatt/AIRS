"""
Role-Based Access Control (RBAC).

Foundation for RBAC covering three core roles:
- org_admin: Full connector/policy management
- org_member: Read-only dashboards + assessments
- auditor: Read-only governance + audit trail access
"""
import enum
from typing import List, Callable, Dict, Any

from fastapi import HTTPException, Depends
from starlette import status

from app.core.auth import User, require_auth


class Role(str, enum.Enum):
    """System Roles."""
    org_admin = "org_admin"
    org_member = "org_member"
    auditor = "auditor"


# Minimal hardcoded policies for initial RBAC foundation
ROLE_PERMISSIONS: Dict[Role, List[str]] = {
    Role.org_admin: [
        "connectors:manage",
        "policies:manage",
        "assessments:manage",
        "reports:manage",
        "inventory:manage",
        "simulations:manage",
        "dashboard:read",
        "audit_trail:read",
    ],
    Role.org_member: [
        "dashboard:read",
        "assessments:read",
        "reports:read",
        "inventory:read",
        "simulations:read",
    ],
    Role.auditor: [
        "dashboard:read",
        "assessments:read",
        "reports:read",
        "policies:read",
        "inventory:read",
        "audit_trail:read",
    ],
}


def require_role(required_roles: List[Role]) -> Callable:
    """Dependency to enforce that current user has one of the required roles."""

    async def role_checker(user: User = Depends(require_auth)) -> User:
        # In a real environment, roles would be extracted from JWT claims
        # or queried from the database based on user.uid.
        # For this foundation, we mock it by inspecting the email or assuming
        # dev users are org_admins.
        
        user_roles = []
        if getattr(user, "email", None):
            email = user.email.lower()
            if "admin" in email:
                user_roles.append(Role.org_admin)
            elif "auditor" in email:
                user_roles.append(Role.auditor)
            else:
                user_roles.append(Role.org_member)
        else:
            # Default mock logic
            if user.uid.startswith("dev-") or user.uid.startswith("mock-"):
                user_roles.append(Role.org_admin)
            else:
                user_roles.append(Role.org_member)
        
        has_required_role = any(role in user_roles for role in required_roles)
        
        if not has_required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not permitted. Required roles: {[r.value for r in required_roles]}",
            )
            
        # Attach roles to user for downstream logic
        user.roles = user_roles
        return user

    return role_checker


def require_permission(permission: str) -> Callable:
    """Dependency to enforce that current user has a specific permission."""

    async def permission_checker(user: User = Depends(require_auth)) -> User:
        # Same role extraction as require_role
        user_roles = []
        if getattr(user, "email", None):
            email = user.email.lower()
            if "admin" in email:
                user_roles.append(Role.org_admin)
            elif "auditor" in email:
                user_roles.append(Role.auditor)
            else:
                user_roles.append(Role.org_member)
        else:
            if user.uid.startswith("dev-") or user.uid.startswith("mock-"):
                user_roles.append(Role.org_admin)
            else:
                user_roles.append(Role.org_member)
        
        user.roles = user_roles
        
        # Check if any of the user's roles has the required permission
        has_permission = False
        for role in user_roles:
            if permission in ROLE_PERMISSIONS.get(role, []):
                has_permission = True
                break
                
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not permitted. Required permission: {permission}",
            )
            
        return user

    return permission_checker
