import pytest
from fastapi import HTTPException

from app.middleware.permission import (
    require_admin_or_root,
    require_role,
    require_root_only,
)


@pytest.mark.asyncio
async def test_require_role_allows_expected_role():
    @require_role("admin", "root")
    async def protected_endpoint(*, current_user):
        return {"role": current_user["role"]}

    result = await protected_endpoint(current_user={"role": "admin"})

    assert result == {"role": "admin"}


@pytest.mark.asyncio
async def test_require_role_rejects_unlisted_role():
    @require_role("admin", "root")
    async def protected_endpoint(*, current_user):
        return current_user

    with pytest.raises(HTTPException) as exc_info:
        await protected_endpoint(current_user={"role": "user"})

    assert exc_info.value.status_code == 403
    assert "admin, root" in exc_info.value.detail


@pytest.mark.asyncio
async def test_require_admin_or_root_accepts_root():
    @require_admin_or_root
    async def protected_endpoint(*, current_user):
        return current_user["role"]

    result = await protected_endpoint(current_user={"role": "root"})

    assert result == "root"


@pytest.mark.asyncio
async def test_require_root_only_rejects_admin():
    @require_root_only
    async def protected_endpoint(*, current_user):
        return current_user["role"]

    with pytest.raises(HTTPException) as exc_info:
        await protected_endpoint(current_user={"role": "admin"})

    assert exc_info.value.status_code == 403
    assert "root" in exc_info.value.detail
