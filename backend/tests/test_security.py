from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.core import security


def test_create_and_decode_access_token_round_trip():
    token = security.create_access_token(
        {"user_id": 7, "role": "admin"},
        expires_delta=timedelta(minutes=5),
    )

    payload = security.decode_access_token(token)

    assert payload is not None
    assert payload["user_id"] == 7
    assert payload["role"] == "admin"
    assert "exp" in payload


def test_create_access_token_uses_default_expiry_when_not_provided():
    token = security.create_access_token({"user_id": 11})

    payload = security.decode_access_token(token)

    assert payload is not None
    assert payload["user_id"] == 11
    assert "exp" in payload


def test_decode_access_token_returns_none_for_invalid_token():
    assert security.decode_access_token("not-a-valid-token") is None


def test_token_blacklist_reports_active_token():
    blacklist = security.TokenBlacklist()
    blacklist.add("token-1", expiry_timestamp=9999999999)

    assert blacklist.is_blacklisted("token-1") is True
    assert blacklist.is_blacklisted("token-2") is False


def test_token_blacklist_cleans_expired_tokens(monkeypatch):
    blacklist = security.TokenBlacklist()
    blacklist.add("expired-token", expiry_timestamp=100)

    monkeypatch.setattr(security.time, "time", lambda: 200)

    assert blacklist.is_blacklisted("expired-token") is False
    assert blacklist._blacklist == set()
    assert blacklist._expiry == {}


def test_token_blacklist_clear_resets_state():
    blacklist = security.TokenBlacklist()
    blacklist.add("token-1", expiry_timestamp=9999999999)

    blacklist.clear()

    assert blacklist._blacklist == set()
    assert blacklist._expiry == {}


@pytest.mark.asyncio
async def test_get_current_user_id_returns_user_id(monkeypatch):
    monkeypatch.setattr(
        security,
        "decode_access_token",
        lambda token: {"user_id": 42},
    )

    fake_repo = SimpleNamespace(get_by_id=AsyncMock(return_value=SimpleNamespace(id=42)))
    monkeypatch.setattr(security, "UserRepository", lambda db: fake_repo)

    result = await security.get_current_user_id(token="valid-token", db=object())

    assert result == 42
    fake_repo.get_by_id.assert_awaited_once_with(42)


@pytest.mark.asyncio
async def test_get_current_user_id_raises_for_missing_payload(monkeypatch):
    monkeypatch.setattr(security, "decode_access_token", lambda token: None)

    with pytest.raises(HTTPException) as exc_info:
        await security.get_current_user_id(token="bad-token", db=object())

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_id_raises_when_user_id_missing(monkeypatch):
    monkeypatch.setattr(security, "decode_access_token", lambda token: {})

    with pytest.raises(HTTPException) as exc_info:
        await security.get_current_user_id(token="bad-token", db=object())

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_id_raises_when_user_not_found(monkeypatch):
    monkeypatch.setattr(
        security,
        "decode_access_token",
        lambda token: {"user_id": 8},
    )
    fake_repo = SimpleNamespace(get_by_id=AsyncMock(return_value=None))
    monkeypatch.setattr(security, "UserRepository", lambda db: fake_repo)

    with pytest.raises(HTTPException) as exc_info:
        await security.get_current_user_id(token="valid-token", db=object())

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_get_optional_user_id_returns_none_on_auth_failure(monkeypatch):
    async def raise_http_exception(*args, **kwargs):
        raise HTTPException(status_code=401, detail="无法验证凭据")

    monkeypatch.setattr(security, "get_current_user_id", raise_http_exception)

    result = await security.get_optional_user_id(token="bad-token", db=object())

    assert result is None
