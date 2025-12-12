# api/plugins/base.py
"""
Base class for API plugins.

This module provides the abstract base class that all plugins must inherit from.
Plugins can extend the API with custom endpoints, middleware, and event handlers.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

from fastapi import APIRouter


class PluginBase(ABC):
    """
    Abstract base class for API plugins.

    All plugins must inherit from this class and implement the required methods.

    Example:
        class MyPlugin(PluginBase):
            @property
            def name(self) -> str:
                return "my-plugin"

            @property
            def version(self) -> str:
                return "1.0.0"

            def get_router(self) -> APIRouter:
                router = APIRouter()
                @router.get("/my-endpoint")
                async def my_endpoint():
                    return {"message": "Hello from plugin"}
                return router
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Get the unique name of the plugin.

        Returns:
            The plugin name (should be lowercase with hyphens)
        """
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """
        Get the version of the plugin.

        Returns:
            The version string (e.g., "1.0.0")
        """
        pass

    @property
    def description(self) -> str:
        """
        Get a description of the plugin.

        Returns:
            A brief description of what the plugin does
        """
        return ""

    @property
    def author(self) -> str:
        """
        Get the author of the plugin.

        Returns:
            The author name or email
        """
        return "Unknown"

    @property
    def dependencies(self) -> List[str]:
        """
        Get a list of plugin dependencies.

        Returns:
            List of plugin names that this plugin depends on
        """
        return []

    @abstractmethod
    def get_router(self) -> Optional[APIRouter]:
        """
        Get the FastAPI router for this plugin.

        Returns:
            An APIRouter with the plugin's endpoints, or None if no endpoints
        """
        pass

    def on_startup(self):
        """
        Called when the application starts.

        Override this method to perform initialization tasks.
        """
        pass

    def on_shutdown(self):
        """
        Called when the application shuts down.

        Override this method to perform cleanup tasks.
        """
        pass

    def get_middleware(self) -> List[tuple]:
        """
        Get middleware classes to add to the application.

        Returns:
            List of tuples (MiddlewareClass, kwargs) to add
        """
        return []

    def get_config(self) -> Dict[str, Any]:
        """
        Get the plugin's configuration.

        Returns:
            Dictionary of configuration values
        """
        return {}

    def __repr__(self) -> str:
        return f"<Plugin {self.name} v{self.version}>"
