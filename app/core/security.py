import hashlib
import json
from enum import Enum
from typing import Callable
from pydantic import BaseModel
from fastapi import Request, HTTPException, Depends
from app.config import settings

class Role(str, Enum):
    ADMIN = "admin"
    USER = "user"

class User(BaseModel):
    username: str
    role: Role

async def get_current_user(request: Request) -> User:
    """
    Mock dependency to retrieve the current user based on headers for initial RBAC setup.
    In a real app, this would verify JWT tokens against DB or an identity provider.
    In production, X-Mock-Role headers are ignored and all requests are rejected until
    real JWT authentication is implemented.
    """
    if settings.environment == "production":
        raise HTTPException(
            status_code=401,
            detail="Authentication required. JWT authentication is not yet configured.",
        )

    # In non-production environments, allow passing a role via a custom header or fallback to USER
    role_header = request.headers.get("X-Mock-Role", "user").lower()
    if role_header == "admin":
        role = Role.ADMIN
    else:
        role = Role.USER

    return User(username="mock_user", role=role)

def require_role(required_role: Role) -> Callable:
    """
    Dependency to check if the current user has the required role.
    """
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role != required_role:
            # We explicitly check for admin. If an endpoint requires USER, an ADMIN should ideally pass too,
            # but for this simple setup we check exact match or if current user is ADMIN.
            if required_role == Role.USER and current_user.role == Role.ADMIN:
                return current_user
            raise HTTPException(
                status_code=403,
                detail=f"Operation not permitted. Requires role: {required_role.value}"
            )
        return current_user
    return role_checker

def compute_config_hash() -> str:
    """
    Compute a hash of the current application settings to monitor for drift.
    """
    settings_dict = settings.model_dump(mode='json')
    # Use json.dumps to get a consistent string representation
    settings_str = json.dumps(settings_dict, sort_keys=True)
    return hashlib.sha256(settings_str.encode("utf-8")).hexdigest()

# Store the initial config hash at module load/app startup
INITIAL_CONFIG_HASH = compute_config_hash()

async def verify_config_drift() -> None:
    """
    Dependency that enforces zero-trust boundaries by checking if
    the application configuration has drifted since startup.
    """
    current_hash = compute_config_hash()
    if current_hash != INITIAL_CONFIG_HASH:
        raise HTTPException(
            status_code=500,
            detail="Zero-trust boundary violation: Application configuration drift detected."
        )
