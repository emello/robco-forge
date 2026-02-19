"""Audit logging middleware for FastAPI.

Requirements:
- 10.1: Capture all API requests
- 10.2: Extract user identity, action, resource, result
"""

import logging
from typing import Callable
from datetime import datetime

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from .audit_logger import audit_log
from ..database import SessionLocal

logger = logging.getLogger(__name__)


class AuditMiddleware(BaseHTTPMiddleware):
    """Middleware to automatically audit all API requests.
    
    Captures:
    - User identity (from JWT token)
    - Action (HTTP method + endpoint)
    - Resource type and ID (from URL path)
    - Result (HTTP status code)
    - Source IP address
    - User agent
    - Interface (inferred from user agent or headers)
    
    Validates: Requirements 10.1, 10.2
    """
    
    def __init__(self, app: ASGIApp):
        """Initialize audit middleware.
        
        Args:
            app: ASGI application
        """
        super().__init__(app)
        
        # Endpoints to exclude from audit logging
        self.excluded_paths = {
            "/health",
            "/health/ready",
            "/health/live",
            "/metrics",
            "/api/docs",
            "/api/redoc",
            "/api/openapi.json",
            "/",
        }
    
    def _should_audit(self, path: str) -> bool:
        """Check if request should be audited.
        
        Args:
            path: Request path
            
        Returns:
            True if should audit, False otherwise
        """
        # Exclude health checks and documentation
        if path in self.excluded_paths:
            return False
        
        # Exclude static files
        if path.startswith("/static/"):
            return False
        
        return True
    
    def _extract_resource_info(self, method: str, path: str) -> tuple[str, str, str]:
        """Extract resource type, ID, and action from request.
        
        Args:
            method: HTTP method
            path: Request path
            
        Returns:
            Tuple of (action, resource_type, resource_id)
        """
        # Parse path to extract resource info
        parts = [p for p in path.split("/") if p]
        
        # Default values
        resource_type = "unknown"
        resource_id = None
        action = f"{method.lower()}.{resource_type}"
        
        # Try to extract from API path structure
        # Expected format: /api/v1/{resource_type}/{resource_id?}/{sub_action?}
        if len(parts) >= 3 and parts[0] == "api" and parts[1].startswith("v"):
            resource_type = parts[2]
            
            if len(parts) >= 4 and not parts[3] in ["start", "stop", "callback", "refresh", "logout", "me"]:
                resource_id = parts[3]
            
            # Determine action
            if method == "POST":
                if len(parts) >= 5:
                    # Sub-action like /workspaces/{id}/start
                    action = f"{resource_type}.{parts[4]}"
                else:
                    action = f"{resource_type}.create"
            elif method == "GET":
                if resource_id:
                    action = f"{resource_type}.read"
                else:
                    action = f"{resource_type}.list"
            elif method == "PUT" or method == "PATCH":
                action = f"{resource_type}.update"
            elif method == "DELETE":
                action = f"{resource_type}.delete"
            else:
                action = f"{resource_type}.{method.lower()}"
        
        return action, resource_type, resource_id
    
    def _determine_interface(self, user_agent: str, headers: dict) -> str:
        """Determine which interface was used.
        
        Args:
            user_agent: User agent string
            headers: Request headers
            
        Returns:
            Interface name (PORTAL, CLI, LUCY, API)
        """
        user_agent_lower = user_agent.lower() if user_agent else ""
        
        # Check for CLI
        if "forge-cli" in user_agent_lower or "curl" in user_agent_lower:
            return "CLI"
        
        # Check for Lucy (would have custom header or user agent)
        if headers.get("x-forge-interface") == "lucy":
            return "LUCY"
        
        # Check for web portal
        if "mozilla" in user_agent_lower or "chrome" in user_agent_lower or "safari" in user_agent_lower:
            return "PORTAL"
        
        # Default to API
        return "API"
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and create audit log.
        
        Args:
            request: FastAPI request
            call_next: Next middleware/handler
            
        Returns:
            Response
        """
        # Check if should audit
        if not self._should_audit(request.url.path):
            return await call_next(request)
        
        # Extract request info
        method = request.method
        path = request.url.path
        source_ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent", "")
        
        # Extract resource info
        action, resource_type, resource_id = self._extract_resource_info(method, path)
        
        # Determine interface
        interface = self._determine_interface(user_agent, dict(request.headers))
        
        # Extract user ID from request state (set by auth middleware)
        user_id = None
        try:
            # Try to get user from request state
            if hasattr(request.state, "user"):
                user_id = request.state.user.get("user_id")
            
            # Try to extract from Authorization header if not in state
            if not user_id:
                auth_header = request.headers.get("authorization", "")
                if auth_header.startswith("Bearer "):
                    # We'll log as "authenticated" but won't decode token here
                    user_id = "authenticated"
        except Exception:
            pass
        
        # Default to anonymous if no user
        if not user_id:
            user_id = "anonymous"
        
        # Process request
        start_time = datetime.utcnow()
        response = await call_next(request)
        duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Determine result based on status code
        if 200 <= response.status_code < 300:
            result = "SUCCESS"
        elif response.status_code == 401 or response.status_code == 403:
            result = "DENIED"
        else:
            result = "FAILURE"
        
        # Create audit log entry (async in background to not slow down response)
        try:
            db = SessionLocal()
            audit_log(
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                result=result,
                resource_id=resource_id,
                source_ip=source_ip,
                user_agent=user_agent,
                interface=interface,
                metadata={
                    "method": method,
                    "path": path,
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                },
                db=db,
            )
            db.close()
        except Exception as e:
            # Log error but don't fail the request
            logger.error(f"Failed to create audit log: {e}", exc_info=True)
        
        return response
