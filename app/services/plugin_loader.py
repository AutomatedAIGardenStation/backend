import json
import logging
import importlib
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

from app.models.plugin import PluginManifest
from app.services.plugin_base import PluginBase
from pydantic import ValidationError

logger = logging.getLogger(__name__)

class PluginLoader:
    def __init__(self, plugin_dir: str = "app/plugins"):
        self.plugin_dir = Path(plugin_dir)
        self.plugins: Dict[str, PluginBase] = {}
        self.manifests: Dict[str, PluginManifest] = {}
        self.granted_scopes: set = set()

    def set_granted_scopes(self, scopes: List[str]):
        """Sets the list of globally granted permission scopes."""
        self.granted_scopes = set(scopes)

    def discover_plugins(self) -> None:
        """
        Discovers and validates plugins in the plugin directory.
        Only valid plugins with manifest.json files are loaded.
        """
        if not self.plugin_dir.exists() or not self.plugin_dir.is_dir():
            logger.warning(f"Plugin directory not found: {self.plugin_dir}")
            return

        for plugin_path in self.plugin_dir.iterdir():
            if not plugin_path.is_dir():
                continue

            manifest_file = plugin_path / "manifest.json"
            if not manifest_file.exists():
                logger.debug(f"Skipping {plugin_path.name}: no manifest.json found.")
                continue

            try:
                with open(manifest_file, "r") as f:
                    manifest_data = json.load(f)

                manifest = PluginManifest(**manifest_data)

                # Check scopes before loading
                requested_scopes = set(manifest.scopes)
                if not requested_scopes.issubset(self.granted_scopes):
                    missing_scopes = requested_scopes - self.granted_scopes
                    logger.error(
                        f"Plugin '{manifest.name}' requested missing scopes: {missing_scopes}. Plugin will not be loaded."
                    )
                    continue

                # Store manifest
                self.manifests[manifest.name] = manifest

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse manifest.json for plugin '{plugin_path.name}': {e}")
            except ValidationError as e:
                logger.error(f"Invalid manifest.json for plugin '{plugin_path.name}': {e}")
            except Exception as e:
                logger.error(f"Unexpected error parsing manifest for plugin '{plugin_path.name}': {e}")

    def load_plugin(self, plugin_name: str) -> Optional[PluginBase]:
        """
        Loads a single discovered plugin dynamically.
        """
        if plugin_name not in self.manifests:
            logger.error(f"Cannot load plugin '{plugin_name}': Manifest not found.")
            return None

        if plugin_name in self.plugins:
            logger.info(f"Plugin '{plugin_name}' already loaded.")
            return self.plugins[plugin_name]

        manifest = self.manifests[plugin_name]

        added_to_sys_path = False
        try:
            # Need to temporarily add plugin_dir to sys.path to resolve module import
            if str(self.plugin_dir) not in sys.path:
                sys.path.insert(0, str(self.plugin_dir))
                added_to_sys_path = True

            module_name, class_name = manifest.entrypoint.rsplit(".", 1)

            # plugin directory structure should match entrypoint format:
            # e.g. entrypoint="my_plugin.plugin.MyPlugin" -> module="my_plugin.plugin"
            module = importlib.import_module(module_name)
            plugin_class = getattr(module, class_name)

            # Instantiate the plugin
            plugin_instance = plugin_class()

            if not isinstance(plugin_instance, PluginBase):
                logger.error(f"Plugin '{plugin_name}' does not inherit from PluginBase.")
                return None

            self.plugins[plugin_name] = plugin_instance
            logger.info(f"Successfully loaded plugin '{plugin_name}' (v{manifest.version})")
            return plugin_instance

        except ImportError as e:
            logger.error(f"Failed to import plugin module for '{plugin_name}': {e}")
        except AttributeError as e:
            logger.error(f"Failed to find entrypoint class for '{plugin_name}': {e}")
        except Exception as e:
            logger.error(f"Unexpected error loading plugin '{plugin_name}': {e}")
        finally:
            # Clean up sys.path
            if added_to_sys_path and str(self.plugin_dir) in sys.path:
                sys.path.remove(str(self.plugin_dir))

        return None

    def load_all_plugins(self) -> None:
        """Loads all discovered plugins."""
        for plugin_name in list(self.manifests.keys()):
            self.load_plugin(plugin_name)

    async def init_plugin(self, plugin_name: str, config: Dict[str, Any]) -> bool:
        """Safely initializes a loaded plugin."""
        plugin = self.plugins.get(plugin_name)
        if not plugin:
            logger.error(f"Cannot init plugin '{plugin_name}': Plugin not loaded.")
            return False

        try:
            await plugin.init(config)
            logger.info(f"Successfully initialized plugin '{plugin_name}'")
            return True
        except Exception as e:
            logger.error(f"Plugin '{plugin_name}' failed to initialize: {e}", exc_info=True)
            return False

    async def execute_plugin(self, plugin_name: str, data: Any) -> Any:
        """Safely executes a loaded plugin."""
        plugin = self.plugins.get(plugin_name)
        if not plugin:
            logger.error(f"Cannot execute plugin '{plugin_name}': Plugin not loaded.")
            return None

        try:
            return await plugin.execute(data)
        except Exception as e:
            logger.error(f"Plugin '{plugin_name}' failed during execution: {e}", exc_info=True)
            return None

    async def cleanup_plugin(self, plugin_name: str) -> bool:
        """Safely cleans up a loaded plugin."""
        plugin = self.plugins.get(plugin_name)
        if not plugin:
            logger.error(f"Cannot cleanup plugin '{plugin_name}': Plugin not loaded.")
            return False

        try:
            await plugin.cleanup()
            logger.info(f"Successfully cleaned up plugin '{plugin_name}'")
            # Remove from loaded plugins
            del self.plugins[plugin_name]
            return True
        except Exception as e:
            logger.error(f"Plugin '{plugin_name}' failed during cleanup: {e}", exc_info=True)
            # Remove even if cleanup failed to avoid memory leaks
            del self.plugins[plugin_name]
            return False

    async def cleanup_all_plugins(self) -> None:
        """Safely cleans up all loaded plugins."""
        for plugin_name in list(self.plugins.keys()):
            await self.cleanup_plugin(plugin_name)
