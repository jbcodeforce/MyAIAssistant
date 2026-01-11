from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings, get_config_info, setup_logging
from app.db.database import init_db
from app.api.todos import router as todos_router
from app.api.knowledge import router as knowledge_router
from app.api.rag import router as rag_router
from app.api.chat import router as chat_router
from app.api.organizations import router as organizations_router
from app.api.projects import router as projects_router
from app.api.metrics import router as metrics_router
from app.api.slp_assessments import router as slp_assessments_router
from app.api.meeting_refs import router as meeting_refs_router
from app.api.assets import router as assets_router
from app.api.persons import router as persons_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize database
    await init_db()
    yield
    # Shutdown: cleanup if needed


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    setup_logging()
    settings = get_settings()
    
    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=lifespan
    )

    # Configure CORS
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    application.include_router(todos_router, prefix="/api")
    application.include_router(knowledge_router, prefix="/api")
    application.include_router(rag_router, prefix="/api")
    application.include_router(chat_router, prefix="/api")
    application.include_router(organizations_router, prefix="/api")
    application.include_router(projects_router, prefix="/api")
    application.include_router(metrics_router, prefix="/api")
    application.include_router(slp_assessments_router, prefix="/api")
    application.include_router(meeting_refs_router, prefix="/api")
    application.include_router(assets_router, prefix="/api")
    application.include_router(persons_router, prefix="/api")

    return application


app = create_app()

@app.get("/")
async def root():
    settings = get_settings()
    return {
        "message": "Welcome to MyAIAssistant API",
        "version": settings.app_version
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/debug/config")
async def debug_config():
    """
    Debug endpoint to show current configuration paths.
    Useful for verifying CONFIG_FILE is being applied correctly.
    """
    return get_config_info()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
