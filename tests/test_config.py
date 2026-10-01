from ha_mcp.config import Settings


def test_stateless_http_default(monkeypatch):
    """Test that stateless_http defaults to True."""
    monkeypatch.delenv("HA_MCP_STATELESS_HTTP", raising=False)
    cfg = Settings()
    assert cfg.stateless_http is True


def test_stateless_http_env_override(monkeypatch):
    """Test that HA_MCP_STATELESS_HTTP environment variable overrides the default."""
    monkeypatch.setenv("HA_MCP_STATELESS_HTTP", "false")
    cfg = Settings()
    assert cfg.stateless_http is False
