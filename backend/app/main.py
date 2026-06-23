"""
main.py — FastAPI application entry point.

Handles:
- App initialization with lifespan (DB connect/disconnect)
- CORS middleware for frontend access
- Observability middleware (request timing → /metrics)
- Router registration for all API modules
- Health check + Prometheus metrics endpoints
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db.mongo import connect_db, close_db
from app.utils.observability import metrics_middleware, render_metrics

# ── API Routers (imported after app is created) ───────────────────────────────
from app.api import (
    webhooks, tenants, sessions, messages, broadcast, sse,
    metrics as metrics_api, agent_actions, agent_runs, templates,
)

# ── Structured logging ────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle — connect DB on startup, close on shutdown."""
    await connect_db()
    yield
    await close_db()


# ── Create App ────────────────────────────────────────────────────────────────
settings = get_settings()

app = FastAPI(
    title="Multi-Tenant WhatsApp Agent API",
    description="Cloud-native SaaS for multi-tenant WhatsApp AI agents powered by LangGraph + Gemini",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── Middleware ────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.middleware("http")(metrics_middleware)


# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(webhooks.router, prefix="/api", tags=["Webhooks"])
app.include_router(tenants.router, prefix="/api", tags=["Tenants"])
app.include_router(sessions.router, prefix="/api", tags=["Sessions"])
app.include_router(messages.router, prefix="/api", tags=["Messages"])
app.include_router(broadcast.router, prefix="/api", tags=["Broadcast"])
app.include_router(sse.router, prefix="/api", tags=["Live Updates"])
app.include_router(metrics_api.router, prefix="/api", tags=["Analytics"])
app.include_router(agent_actions.router, prefix="/api", tags=["Agent Actions"])
app.include_router(agent_runs.router, prefix="/api", tags=["Agent Runs"])
app.include_router(templates.router, prefix="/api", tags=["Templates"])


# ── Health Check ──────────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
async def health_check():
    """Render/Cloud Run health probe endpoint."""
    return {"status": "healthy", "service": "whatsapp-agent-backend", "version": "2.0.0"}


@app.get("/metrics", tags=["Observability"], include_in_schema=False)
async def prometheus_metrics():
    """Prometheus text-format metrics for scraping (Grafana / Cloud Monitoring)."""
    return Response(content=render_metrics(), media_type="text/plain; version=0.0.4")


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Multi-Tenant WhatsApp Agent API",
        "docs": "/docs",
        "health": "/health",
        "metrics": "/metrics",
    }
