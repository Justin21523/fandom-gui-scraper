# api/plugins/example_plugin.py
"""
Example plugin demonstrating the plugin system.

This plugin serves as a template for creating new plugins.
"""

from typing import Optional

from fastapi import APIRouter

from api.plugins.base import PluginBase


class ExamplePlugin(PluginBase):
    """
    Example plugin that demonstrates the plugin system.

    This plugin adds a simple endpoint that returns a greeting.
    """

    @property
    def name(self) -> str:
        return "example"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def description(self) -> str:
        return "Example plugin demonstrating the plugin system"

    @property
    def author(self) -> str:
        return "Fandom Scraper Team"

    def get_router(self) -> Optional[APIRouter]:
        router = APIRouter()

        @router.get("/hello")
        async def hello():
            """Return a greeting from the example plugin."""
            return {
                "message": "Hello from the example plugin!",
                "plugin": self.name,
                "version": self.version,
            }

        @router.get("/info")
        async def info():
            """Return information about this plugin."""
            return {
                "name": self.name,
                "version": self.version,
                "description": self.description,
                "author": self.author,
            }

        return router

    def on_startup(self):
        """Called when the application starts."""
        print(f"Example plugin {self.version} started!")

    def on_shutdown(self):
        """Called when the application shuts down."""
        print(f"Example plugin shutting down...")
