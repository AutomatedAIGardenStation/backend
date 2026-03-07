import pytest
import json

from app.services.plugin_loader import PluginLoader
from app.services.plugin_base import PluginBase

@pytest.fixture
def temp_plugin_dir(tmp_path):
    plugin_dir = tmp_path / "plugins"
    plugin_dir.mkdir()

    # Create a mock plugin directory structure
    mock_plugin_dir = plugin_dir / "mock_plugin"
    mock_plugin_dir.mkdir()

    # 1. Manifest
    manifest_data = {
        "name": "mock-sensor",
        "version": "1.0.0",
        "entrypoint": "mock_plugin.plugin.MockPlugin",
        "scopes": ["sensor:read", "sensor:write"]
    }
    with open(mock_plugin_dir / "manifest.json", "w") as f:
        json.dump(manifest_data, f)

    # 2. Plugin code
    plugin_code = """
from typing import Dict, Any
from app.services.plugin_base import PluginBase

class MockPlugin(PluginBase):
    def __init__(self):
        self.initialized = False
        self.executed = False
        self.cleaned_up = False
        self.fail_cleanup = False

    async def init(self, config: Dict[str, Any]) -> None:
        if config.get("fail_init"):
            raise ValueError("Init failed")
        self.initialized = True

    async def execute(self, data: Any) -> Any:
        if data == "fail":
            raise RuntimeError("Execute failed")
        self.executed = True
        return f"Processed: {data}"

    async def cleanup(self) -> None:
        if self.fail_cleanup:
            raise RuntimeError("Cleanup failed")
        self.cleaned_up = True
"""
    with open(mock_plugin_dir / "plugin.py", "w") as f:
        f.write(plugin_code)

    # 3. Create another plugin with missing scopes
    bad_scope_plugin_dir = plugin_dir / "bad_plugin"
    bad_scope_plugin_dir.mkdir()
    bad_manifest = {
        "name": "bad-plugin",
        "version": "1.0.0",
        "entrypoint": "bad_plugin.plugin.BadPlugin",
        "scopes": ["admin:all"]
    }
    with open(bad_scope_plugin_dir / "manifest.json", "w") as f:
        json.dump(bad_manifest, f)

    yield str(plugin_dir)

@pytest.fixture
def loader(temp_plugin_dir):
    loader = PluginLoader(plugin_dir=temp_plugin_dir)
    loader.set_granted_scopes(["sensor:read", "sensor:write", "system:read"])
    return loader

def test_discover_plugins(loader):
    loader.discover_plugins()
    # Should discover mock-sensor, but bad-plugin should be rejected due to scopes
    assert "mock-sensor" in loader.manifests
    assert "bad-plugin" not in loader.manifests

def test_load_plugin(loader):
    loader.discover_plugins()
    plugin = loader.load_plugin("mock-sensor")
    assert plugin is not None
    assert isinstance(plugin, PluginBase)
    assert "mock-sensor" in loader.plugins

@pytest.mark.asyncio
async def test_plugin_lifecycle(loader):
    loader.discover_plugins()
    loader.load_plugin("mock-sensor")

    # Test init
    success = await loader.init_plugin("mock-sensor", {"key": "value"})
    assert success is True
    plugin = loader.plugins["mock-sensor"]
    assert plugin.initialized is True

    # Test execute
    result = await loader.execute_plugin("mock-sensor", "test_data")
    assert result == "Processed: test_data"
    assert plugin.executed is True

    # Test cleanup
    success = await loader.cleanup_plugin("mock-sensor")
    assert success is True
    assert plugin.cleaned_up is True
    assert "mock-sensor" not in loader.plugins

@pytest.mark.asyncio
async def test_plugin_failure_handling(loader):
    loader.discover_plugins()
    loader.load_plugin("mock-sensor")

    # Test init failure
    success = await loader.init_plugin("mock-sensor", {"fail_init": True})
    assert success is False # Handled safely

    # Test execute failure
    result = await loader.execute_plugin("mock-sensor", "fail")
    assert result is None # Handled safely

@pytest.mark.asyncio
async def test_plugin_cleanup_failure_handling(loader):
    loader.discover_plugins()
    loader.load_plugin("mock-sensor")
    plugin = loader.plugins["mock-sensor"]
    plugin.fail_cleanup = True

    # Test cleanup failure
    success = await loader.cleanup_plugin("mock-sensor")
    assert success is False # Handled safely
    assert "mock-sensor" not in loader.plugins # Still removed from active plugins
