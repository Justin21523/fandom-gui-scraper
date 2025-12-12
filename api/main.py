# api/main.py
"""
FastAPI application for Fandom Scraper REST API.

This module provides a REST API interface for accessing scraped character data.

Usage:
    uvicorn api.main:app --reload --port 8000
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from api.endpoints import characters, auth, ws, scraper
from api.middleware.rate_limit import RateLimitMiddleware
from api.schemas.character import ErrorResponse
from api.plugins import plugin_manager

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info("Starting Fandom Scraper API...")

    # Load and register plugins
    plugin_manager.load_plugins()
    plugin_manager.register_plugins(app)
    plugin_manager.startup_plugins()

    yield

    # Shutdown plugins
    plugin_manager.shutdown_plugins()
    logger.info("Shutting down Fandom Scraper API...")


app = FastAPI(
    title="Fandom Scraper API",
    description="""
    REST API for accessing anime character data scraped from Fandom wikis.

    ## Features

    - **Characters**: CRUD operations for character data
    - **Search**: Full-text search across characters
    - **Statistics**: Aggregate statistics and analytics
    - **Authentication**: JWT-based authentication for write operations

    ## Authentication

    Read operations are public. Write operations (POST, PUT, DELETE) require
    a valid JWT token. Obtain a token via the `/api/v1/auth/token` endpoint.
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting middleware
app.add_middleware(
    RateLimitMiddleware,
    requests_per_hour=1000,
    requests_per_minute=60,
)


# Include routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(characters.router, prefix="/api/v1")
app.include_router(ws.router, prefix="/api/v1")
app.include_router(scraper.router, prefix="/api/v1")


@app.get("/", tags=["root"])
async def root():
    """API root endpoint."""
    return {
        "name": "Fandom Scraper API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
    }


@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/plugins", tags=["plugins"])
async def list_plugins():
    """List all loaded plugins."""
    return {
        "plugins": plugin_manager.list_plugins(),
        "count": len(plugin_manager.plugins),
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal Server Error",
            detail=str(exc),
            status_code=500,
        ).model_dump(),
    )


# Mount frontend static files
frontend_path = Path(__file__).parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/frontend", StaticFiles(directory=str(frontend_path)), name="frontend")
    # Serve index.html at root for SPA
    from fastapi.responses import FileResponse

    @app.get("/app", include_in_schema=False)
    @app.get("/app/{path:path}", include_in_schema=False)
    async def serve_frontend(path: str = ""):
        index_path = frontend_path / "index.html"
        if index_path.exists():
            return FileResponse(str(index_path))
        return JSONResponse({"error": "Frontend not found"}, status_code=404)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
