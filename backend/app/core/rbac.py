from fastapi import HTTPException, status
from app.models.user import UserRole


ROLE_PERMISSIONS = {
    UserRole.ADMIN: {
        "users:read", "users:write", "users:delete",
        "repositories:read", "repositories:write", "repositories:delete",
        "workflows:read", "workflows:write", "workflows:delete",
        "workflows:approve",
        "audit_logs:read",
        "settings:read", "settings:write",
    },
    UserRole.DEVELOPER: {
        "repositories:read", "repositories:write",
        "workflows:read", "workflows:write",
        "workflows:approve",
        "audit_logs:read",
        "settings:read",
    },
    UserRole.VIEWER: {
        "repositories:read",
        "workflows:read",
        "audit_logs:read",
    },
}


def check_permission(user_role: UserRole, permission: str) -> None:
    """Raises HTTPException if user doesn't have the required permission."""
    allowed = ROLE_PERMISSIONS.get(user_role, set())
    if permission not in allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission '{permission}' required. Your role '{user_role}' does not have this permission.",
        )


def has_permission(user_role: UserRole, permission: str) -> bool:
    allowed = ROLE_PERMISSIONS.get(user_role, set())
    return permission in allowed
