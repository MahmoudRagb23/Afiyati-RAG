from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, chat, medications, misc, profile
from app.core.config import Settings
from app.db.database import Database
from app.services.rag_service import RAGService


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    settings.ensure_directories()
    db = Database(settings.database_path)
    db.initialize()

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        yield
        application.state.rag.vectors.close()

    app = FastAPI(
        title="Afiyati Local API",
        description="Evidence-grounded chronic-disease lifestyle assistant",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.state.settings = settings
    app.state.db = db
    app.state.rag = RAGService(settings)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(auth.router, prefix="/api")
    app.include_router(profile.router, prefix="/api")
    app.include_router(medications.router, prefix="/api")
    app.include_router(chat.router, prefix="/api")
    app.include_router(misc.router, prefix="/api")

    @app.get("/api/health")
    async def health(request: Request, deep: bool = False) -> dict:
        result = {
            "status": "ok",
            "database": "ready",
            "rag": request.app.state.rag.status(),
            "ollama": "not_checked",
        }
        if deep:
            try:
                models = await request.app.state.rag.ollama.models()
                result["ollama"] = "ready"
                result["models"] = models
            except Exception as exc:
                result["status"] = "degraded"
                result["ollama"] = str(exc)
        return result

    return app


app = create_app()
