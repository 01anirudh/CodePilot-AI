"""
CodePilot AI — FastAPI Application Entry Point
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import logging

from app.config import settings
from app.database import init_db
from app.routers import auth, repositories, workflows, agents, github, audit_logs

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    logger.info(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")

    # Initialize database
    try:
        await init_db()
        logger.info("✅ Database initialized")
    except Exception as e:
        logger.warning(f"⚠️  Database init skipped (likely no DB yet): {e}")

    # Initialize Qdrant collection
    try:
        from app.services.qdrant_service import ensure_collection
        await ensure_collection()
        logger.info("✅ Qdrant collection ready")
    except Exception as e:
        logger.warning(f"⚠️  Qdrant init skipped: {e}")

    yield

    logger.info("👋 Shutting down CodePilot AI")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
    **CodePilot AI** — Autonomous Software Engineering Agent Platform
    
    A multi-agent AI system combining Repository Analysis, Code Generation,
    Automated Testing, Code Review, Documentation, and GitHub Integration.
    
    ## Agents
    - 🔍 **Repository Analyzer** — Architecture & dependency analysis
    - 🧠 **Knowledge Agent** — Semantic code embeddings (Qdrant)
    - 📋 **Planner Agent** — Task decomposition & orchestration
    - ⚡ **Code Generation** — Production-quality code generation
    - 🔧 **Refactoring** — Code quality improvements
    - 🧪 **Testing** — Automated test generation
    - 👁️ **Code Review** — Security & performance review
    - 📚 **Documentation** — README, API docs, UML
    - 🐙 **GitHub** — Branch, commit & PR creation
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ─── Middleware ────────────────────────────────────────────────────────────────
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers ──────────────────────────────────────────────────────────────────
app.include_router(auth.router, prefix=settings.API_PREFIX)
app.include_router(repositories.router, prefix=settings.API_PREFIX)
app.include_router(workflows.router, prefix=settings.API_PREFIX)
app.include_router(agents.router, prefix=settings.API_PREFIX)
app.include_router(github.router, prefix=settings.API_PREFIX)
app.include_router(audit_logs.router, prefix=settings.API_PREFIX)


# ─── Health Check ─────────────────────────────────────────────────────────────
@app.get("/health", tags=["System"])
async def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }


@app.get("/", tags=["System"])
async def root():
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "docs": "/docs",
        "version": settings.APP_VERSION,
    }
