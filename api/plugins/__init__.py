# api/plugins/__init__.py
"""
Plugin system for extending the API.

This module provides plugin discovery, loading, and management functionality.
Plugins can be used to add custom endpoints, middleware, and functionality
to the API without modifying the core codebase.
"""

import importlib
import importlib.util
import logging
from pathlib import Path
from typing import List, Dict, Any, Type

from fastapi import FastAPI

from api.plugins.base import PluginBase

logger = logging.getLogger(__name__)


class PluginManager:
    """
    Manages plugin discovery, loading, and lifecycle.

    The plugin manager scans a directory for plugin modules, loads them,
    and registers their routers and middleware with the FastAPI application.
    """

    def __init__(self, plugins_dir: str = None):
        """
        Initialize the plugin manager.

        Args:
            plugins_dir: Path to the plugins directory
        """
        if plugins_dir is None:
            plugins_dir = str(Path(__file__).parent)

        self.plugins_dir = Path(plugins_dir)
        self.plugins: Dict[str, PluginBase] = {}
        self._loaded = False

    def discover_plugins(self) -> List[Type[PluginBase]]:
        """
        Discover plugin classes in the plugins directory.

        Returns:
            List of discovered plugin classes
        """
        plugin_classes = []

        if not self.plugins_dir.exists():
            logger.warning(f"Plugins directory not found: {self.plugins_dir}")
            return plugin_classes

        for file_path in self.plugins_dir.glob("*.py"):
            # Skip private modules and base class
            if file_path.name.startswith("_") or file_path.name == "base.py":
                continue

            try:
                # Load the module
                module_name = f"api.plugins.{file_path.stem}"
                spec = importlib.util.spec_from_file_location(
                    module_name, file_path
                )
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)

                    # Find plugin classes in the module
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if (
                            isinstance(attr, type)
                            and issubclass(attr, PluginBase)
                            and attr is not PluginBase
                        ):
                            plugin_classes.append(attr)
                            logger.debug(f"Discovered plugin class: {attr_name}")

            except Exception as e:
                logger.error(f"Failed to load plugin from {file_path}: {e}")

        return plugin_classes

    def load_plugins(self) -> Dict[str, PluginBase]:
        """
        Load and instantiate all discovered plugins.

        Returns:
            Dictionary of loaded plugins by name
        """
        if self._loaded:
            return self.plugins

        plugin_classes = self.discover_plugins()

        for plugin_class in plugin_classes:
            try:
                plugin = plugin_class()
                self.plugins[plugin.name] = plugin
                logger.info(f"Loaded plugin: {plugin.name} v{plugin.version}")
            except Exception as e:
                logger.error(f"Failed to instantiate plugin {plugin_class}: {e}")

        self._loaded = True
        return self.plugins

    def register_plugins(self, app: FastAPI):
        """
        Register all loaded plugins with the FastAPI application.

        Args:
            app: The FastAPI application instance
        """
        if not self._loaded:
            self.load_plugins()

        for name, plugin in self.plugins.items():
            try:
                # Register router if provided
                router = plugin.get_router()
                if router:
                    app.include_router(
                        router,
                        prefix=f"/api/plugins/{name}",
                        tags=[f"Plugin: {name}"],
                    )
                    logger.info(f"Registered router for plugin: {name}")

                # Register middleware
                for middleware_class, kwargs in plugin.get_middleware():
                    app.add_middleware(middleware_class, **kwargs)
                    logger.info(f"Registered middleware from plugin: {name}")

            except Exception as e:
                logger.error(f"Failed to register plugin {name}: {e}")

    def startup_plugins(self):
        """Call on_startup for all loaded plugins."""
        for name, plugin in self.plugins.items():
            try:
                plugin.on_startup()
                logger.debug(f"Started plugin: {name}")
            except Exception as e:
                logger.error(f"Error in plugin {name} startup: {e}")

    def shutdown_plugins(self):
        """Call on_shutdown for all loaded plugins."""
        for name, plugin in self.plugins.items():
            try:
                plugin.on_shutdown()
                logger.debug(f"Shut down plugin: {name}")
            except Exception as e:
                logger.error(f"Error in plugin {name} shutdown: {e}")

    def get_plugin(self, name: str) -> PluginBase:
        """
        Get a loaded plugin by name.

        Args:
            name: The plugin name

        Returns:
            The plugin instance

        Raises:
            KeyError: If the plugin is not found
        """
        return self.plugins[name]

    def list_plugins(self) -> List[Dict[str, Any]]:
        """
        List all loaded plugins with their info.

        Returns:
            List of plugin info dictionaries
        """
        return [
            {
                "name": plugin.name,
                "version": plugin.version,
                "description": plugin.description,
                "author": plugin.author,
            }
            for plugin in self.plugins.values()
        ]


# Global plugin manager instance
plugin_manager = PluginManager()


__all__ = ["PluginBase", "PluginManager", "plugin_manager"]
