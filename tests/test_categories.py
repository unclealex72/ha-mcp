"""Unit tests for category CRUD tools and entity category assignments."""

import json
from unittest.mock import AsyncMock, MagicMock
import pytest

from ha_mcp.tools.registry import register_registry_tools
from ha_mcp.tools.registry_edit import register_registry_edit_tools


class _MockMCPServer:
    def __init__(self):
        self.tools = {}

    def tool(self):
        def decorator(fn):
            self.tools[fn.__name__] = fn
            return fn
        return decorator


@pytest.fixture
def registered_tools():
    server = _MockMCPServer()
    register_registry_tools(server)
    register_registry_edit_tools(server)
    return server.tools


@pytest.fixture
def mock_ctx():
    ctx = MagicMock()
    ws = AsyncMock()
    rest = AsyncMock()
    ctx.fastmcp._lifespan_result = {"ws": ws, "rest": rest}
    return ctx, ws, rest


async def test_list_categories_with_scope(registered_tools, mock_ctx):
    list_categories = registered_tools["list_categories"]
    ctx, ws, _ = mock_ctx

    expected_categories = [
        {"category_id": "cat_1", "name": "Lights", "icon": "mdi:lightbulb"},
        {"category_id": "cat_2", "name": "Security", "icon": "mdi:shield"},
    ]
    ws.send_command.return_value = expected_categories

    res = await list_categories(ctx, scope="automation")
    data = json.loads(res)

    assert data == expected_categories
    ws.send_command.assert_awaited_once_with(
        "config/category_registry/list", scope="automation"
    )


async def test_list_categories_without_scope(registered_tools, mock_ctx):
    list_categories = registered_tools["list_categories"]
    ctx, ws, _ = mock_ctx

    async def side_effect(cmd, scope=None):
        if scope == "automation":
            return [{"category_id": "cat_auto", "name": "Auto"}]
        if scope == "script":
            return [{"category_id": "cat_script", "name": "Script"}]
        return []

    ws.send_command.side_effect = side_effect

    res = await list_categories(ctx)
    data = json.loads(res)

    assert "automation" in data
    assert "script" in data
    assert "scene" not in data  # empty scopes excluded
    assert data["automation"] == [{"category_id": "cat_auto", "name": "Auto"}]
    assert data["script"] == [{"category_id": "cat_script", "name": "Script"}]


async def test_create_category_success(registered_tools, mock_ctx):
    create_category = registered_tools["create_category"]
    ctx, ws, _ = mock_ctx

    created = {
        "category_id": "01HXYZ",
        "name": "Garden",
        "icon": "mdi:flower",
    }
    ws.send_command.return_value = created

    res = await create_category(
        ctx, scope="automation", name="Garden", icon="mdi:flower", skip_confirm=True
    )
    data = json.loads(res)

    assert data["status"] == "created"
    assert data["category"] == created
    ws.send_command.assert_awaited_once_with(
        "config/category_registry/create",
        scope="automation",
        name="Garden",
        icon="mdi:flower",
    )


async def test_create_category_cancelled(registered_tools, mock_ctx):
    create_category = registered_tools["create_category"]
    ctx, ws, _ = mock_ctx

    # Simulate elicit cancellation
    elicit_response = MagicMock()
    elicit_response.action = "accept"
    elicit_response.data = "cancel"
    ctx.elicit = AsyncMock(return_value=elicit_response)

    res = await create_category(
        ctx, scope="automation", name="Garden", skip_confirm=False
    )
    data = json.loads(res)

    assert data["status"] == "cancelled"
    ws.send_command.assert_not_called()


async def test_update_category_success(registered_tools, mock_ctx):
    update_category = registered_tools["update_category"]
    ctx, ws, _ = mock_ctx

    updated = {
        "category_id": "01HXYZ",
        "name": "Backyard",
        "icon": "mdi:tree",
    }
    ws.send_command.return_value = updated

    res = await update_category(
        ctx,
        scope="automation",
        category_id="01HXYZ",
        name="Backyard",
        icon="mdi:tree",
        skip_confirm=True,
    )
    data = json.loads(res)

    assert data["status"] == "updated"
    assert data["category"] == updated
    ws.send_command.assert_awaited_once_with(
        "config/category_registry/update",
        scope="automation",
        category_id="01HXYZ",
        name="Backyard",
        icon="mdi:tree",
    )


async def test_update_category_no_fields(registered_tools, mock_ctx):
    update_category = registered_tools["update_category"]
    ctx, ws, _ = mock_ctx

    res = await update_category(
        ctx, scope="automation", category_id="01HXYZ", skip_confirm=True
    )
    data = json.loads(res)

    assert "error" in data
    ws.send_command.assert_not_called()


async def test_delete_category_success(registered_tools, mock_ctx):
    delete_category = registered_tools["delete_category"]
    ctx, ws, _ = mock_ctx

    res = await delete_category(
        ctx, scope="automation", category_id="01HXYZ", skip_confirm=True
    )
    data = json.loads(res)

    assert data["status"] == "deleted"
    assert data["category_id"] == "01HXYZ"
    assert data["scope"] == "automation"
    ws.send_command.assert_awaited_once_with(
        "config/category_registry/delete",
        scope="automation",
        category_id="01HXYZ",
    )


async def test_delete_category_cancelled(registered_tools, mock_ctx):
    delete_category = registered_tools["delete_category"]
    ctx, ws, _ = mock_ctx

    elicit_response = MagicMock()
    elicit_response.action = "accept"
    elicit_response.data = "cancel"
    ctx.elicit = AsyncMock(return_value=elicit_response)

    res = await delete_category(
        ctx, scope="automation", category_id="01HXYZ", skip_confirm=False
    )
    data = json.loads(res)

    assert data["status"] == "cancelled"
    ws.send_command.assert_not_called()


async def test_update_entity_with_categories(registered_tools, mock_ctx):
    update_entity = registered_tools["update_entity"]
    ctx, ws, _ = mock_ctx

    ws.send_command.return_value = {
        "entity_id": "automation.test_automation",
        "categories": {"automation": "01HXYZ"},
    }

    res = await update_entity(
        ctx,
        entity_id="automation.test_automation",
        categories={"automation": "01HXYZ"},
        skip_confirm=True,
    )
    data = json.loads(res)

    assert data["status"] == "updated"
    ws.send_command.assert_awaited_once_with(
        "config/entity_registry/update",
        entity_id="automation.test_automation",
        categories={"automation": "01HXYZ"},
    )
