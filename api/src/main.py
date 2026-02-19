"""Main FastAPI application for RobCo Forge API.

Requirements:
- 23.1: Structured logging (JSON format)
- 23.6: OpenTelemetry for distributed tracing
"""

import logging
import sys
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from prometheus_client import make_asgi_app
import structlog

from .config import settings
from .database import engine
from .models import Base
from .api import auth_routes
from .audit import AuditMiddleware

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


# Configure OpenTelemetry
def setup_telemetry():
    """Configure OpenTelemetry for distributed tracing.
    
    Validates: Requirements 23.6
    """
    trace.set_tracer_provider(TracerProvider())
    tracer_provider = trace.get_tracer_provider()
    
    # Add console exporter for development
    # In production, this would be replaced with OTLP exporter to send to observability backend
    span_processor = BatchSpanProcessor(ConsoleSpanExporter())
    tracer_provider.add_span_processor(span_processor)
    
    logger.info("OpenTelemetry configured", exporter="console")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan manager.
    
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting RobCo Forge API", version=settings.PROJECT_NAME)
    
    # Setup telemetry
    setup_telemetry()
    
    # Create database tables (in production, use Alembic migrations)
    # Base.metadata.create_all(bind=engine)
    
    logger.info("API startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down RobCo Forge API")


# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="RobCo Forge - Self-service cloud engineering workstation platform",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add audit logging middleware
app.add_middleware(AuditMiddleware)


# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses."""
    response = await call_next(request)
    
    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    
    return response


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests with structured logging.
    
    Validates: Requirements 23.1
    """
    logger.info(
        "incoming_request",
        method=request.method,
        path=request.url.path,
        client_host=request.client.host if request.client else None,
    )
    
    response = await call_next(request)
    
    logger.info(
        "request_completed",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
    )
    
    return response


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with structured response."""
    logger.warning(
        "validation_error",
        path=request.url.path,
        errors=exc.errors(),
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": exc.errors(),
            }
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors with structured logging."""
    logger.error(
        "unhandled_exception",
        path=request.url.path,
        error=str(exc),
        exc_info=True,
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
                "details": str(exc) if settings.DEBUG else None,
            }
        },
    )


# Health check endpoints
@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint.
    
    Returns basic health status of the API.
    
    Validates: Requirements 23.1
    """
    return {
        "status": "healthy",
        "service": "forge-api",
        "version": "1.0.0",
    }


@app.get("/health/ready", tags=["health"])
async def readiness_check():
    """Readiness check endpoint.
    
    Checks if the API is ready to accept requests.
    Verifies database connectivity and other dependencies.
    
    Validates: Requirements 23.1
    """
    # Check database connectivity
    try:
        from .database import SessionLocal
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        db_status = "connected"
    except Exception as e:
        logger.error("database_check_failed", error=str(e))
        db_status = "disconnected"
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "not_ready",
                "service": "forge-api",
                "checks": {
                    "database": db_status,
                }
            }
        )
    
    return {
        "status": "ready",
        "service": "forge-api",
        "version": "1.0.0",
        "checks": {
            "database": db_status,
        }
    }


@app.get("/health/live", tags=["health"])
async def liveness_check():
    """Liveness check endpoint.
    
    Simple check to verify the API process is alive.
    """
    return {
        "status": "alive",
        "service": "forge-api",
    }


# Mount Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


# Include routers
app.include_router(auth_routes.router)

# Import workspace routes
from .api import workspace_routes
app.include_router(workspace_routes.router)

# Import blueprint routes
from .api import blueprint_routes
app.include_router(blueprint_routes.router)

# Import cost routes
from .api import cost_routes
app.include_router(cost_routes.router)

# Import audit routes
from .api import audit_routes
app.include_router(audit_routes.router)

# Import budget routes
from .api import budget_routes
app.include_router(budget_routes.router)

# Import Lucy AI routes
from .api import lucy_routes
app.include_router(lucy_routes.router)


# Instrument FastAPI with OpenTelemetry
FastAPIInstrumentor.instrument_app(app)


# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """Root endpoint with API information."""
    return {
        "service": "RobCo Forge API",
        "version": "1.0.0",
        "docs": "/api/docs",
        "health": "/health",
        "metrics": "/metrics",
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_config=None,  # Use structlog instead
    )
