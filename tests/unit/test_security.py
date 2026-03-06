import pytest
from fastapi import HTTPException
from app.core.security import (
    Role,
    User,
    get_current_user,
    require_role,
    verify_config_drift,
)
from app.config import settings

@pytest.mark.asyncio
async def test_get_current_user_admin_header():
    class MockRequest:
        headers = {"X-Mock-Role": "admin"}
    req = MockRequest()
    user = await get_current_user(request=req) # type: ignore
    assert user.role == Role.ADMIN
    assert user.username == "mock_user"

@pytest.mark.asyncio
async def test_get_current_user_user_header():
    class MockRequest:
        headers = {"X-Mock-Role": "user"}
    req = MockRequest()
    user = await get_current_user(request=req) # type: ignore
    assert user.role == Role.USER
    assert user.username == "mock_user"

@pytest.mark.asyncio
async def test_require_role_success():
    user = User(username="admin_user", role=Role.ADMIN)
    checker = require_role(Role.ADMIN)
    # the checker is an async function that accepts a User
    result = await checker(current_user=user)
    assert result == user

@pytest.mark.asyncio
async def test_require_role_fallback_admin_to_user():
    # If endpoint requires USER, an ADMIN should pass
    user = User(username="admin_user", role=Role.ADMIN)
    checker = require_role(Role.USER)
    result = await checker(current_user=user)
    assert result == user

@pytest.mark.asyncio
async def test_require_role_failure():
    # If endpoint requires ADMIN, a USER should fail
    user = User(username="regular", role=Role.USER)
    checker = require_role(Role.ADMIN)
    with pytest.raises(HTTPException) as excinfo:
        await checker(current_user=user)
    assert excinfo.value.status_code == 403
    assert "Operation not permitted" in str(excinfo.value.detail)

@pytest.mark.asyncio
async def test_verify_config_drift_success():
    # Calling this directly should pass since we haven't mutated settings
    await verify_config_drift()

@pytest.mark.asyncio
async def test_verify_config_drift_failure(monkeypatch):
    # Mutating the configuration to simulate drift
    monkeypatch.setattr(settings, "app_name", "Hacked App")

    with pytest.raises(HTTPException) as excinfo:
        await verify_config_drift()

    assert excinfo.value.status_code == 500
    assert "Zero-trust boundary violation" in str(excinfo.value.detail)
