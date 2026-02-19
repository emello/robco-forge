"""Tool executor framework for Lucy AI service.

Defines tool interface for Claude function calling with error handling and rate limiting.
Requirements: 5.4
"""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable
from enum import Enum
import redis
from pydantic import BaseModel


class ToolResult(BaseModel):
    """Result of a tool execution."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    requires_confirmation: bool = False
    confirmation_message: Optional[str] = None


class ToolCategory(str, Enum):
    """Categories of tools for rate limiting."""
    PROVISIONING = "provisioning"
    WORKSPACE_MANAGEMENT = "workspace_management"
    COST_QUERY = "cost_query"
    DIAGNOSTICS = "diagnostics"
    SUPPORT = "support"


class Tool(ABC):
    """Abstract base class for Lucy tools.
    
    All tools must:
    - Call Forge API endpoints (NEVER AWS APIs directly)
    - Respect RBAC permissions
    - Handle errors gracefully
    - Support rate limiting
    """
    
    def __init__(self, name: str, category: ToolCategory, description: str):
        """Initialize tool.
        
        Args:
            name: Tool name
            category: Tool category for rate limiting
            description: Tool description for Claude
        """
        self.name = name
        self.category = category
        self.description = description
    
    @abstractmethod
    async def execute(
        self,
        user_id: str,
        **kwargs
    ) -> ToolResult:
        """Execute the tool.
        
        Args:
            user_id: User executing the tool
            **kwargs: Tool-specific parameters
            
        Returns:
            ToolResult with success status and data/error
        """
        pass
    
    def get_schema(self) -> Dict[str, Any]:
        """Get tool schema for Claude function calling.
        
        Returns:
            JSON schema describing tool parameters
        """
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self._get_input_schema()
        }
    
    @abstractmethod
    def _get_input_schema(self) -> Dict[str, Any]:
        """Get input schema for this tool.
        
        Returns:
            JSON schema for tool parameters
        """
        pass


class RateLimiter:
    """Rate limiter for tool executions.
    
    Implements sliding window rate limiting using Redis.
    Requirements: 5.4 (5 provisions per user per hour)
    """
    
    def __init__(self, redis_client: redis.Redis):
        """Initialize rate limiter.
        
        Args:
            redis_client: Redis client for storing rate limit data
        """
        self.redis = redis_client
        self.key_prefix = "lucy:ratelimit:"
    
    def _get_key(self, user_id: str, category: ToolCategory) -> str:
        """Generate Redis key for rate limit tracking."""
        return f"{self.key_prefix}{user_id}:{category.value}"
    
    async def check_rate_limit(
        self,
        user_id: str,
        category: ToolCategory,
        limit: int,
        window_seconds: int
    ) -> tuple[bool, Optional[str]]:
        """Check if user has exceeded rate limit.
        
        Args:
            user_id: User identifier
            category: Tool category
            limit: Maximum number of calls allowed
            window_seconds: Time window in seconds
            
        Returns:
            Tuple of (allowed, error_message)
        """
        key = self._get_key(user_id, category)
        now = datetime.utcnow().timestamp()
        window_start = now - window_seconds
        
        # Remove old entries outside the window
        self.redis.zremrangebyscore(key, 0, window_start)
        
        # Count entries in current window
        current_count = self.redis.zcard(key)
        
        if current_count >= limit:
            # Calculate when the oldest entry will expire
            oldest = self.redis.zrange(key, 0, 0, withscores=True)
            if oldest:
                oldest_timestamp = oldest[0][1]
                retry_after = int(oldest_timestamp + window_seconds - now)
                error_msg = (
                    f"Rate limit exceeded for {category.value}. "
                    f"Limit: {limit} per {window_seconds}s. "
                    f"Retry after {retry_after} seconds."
                )
                return False, error_msg
        
        return True, None
    
    async def record_execution(
        self,
        user_id: str,
        category: ToolCategory,
        window_seconds: int
    ) -> None:
        """Record a tool execution for rate limiting.
        
        Args:
            user_id: User identifier
            category: Tool category
            window_seconds: Time window in seconds
        """
        key = self._get_key(user_id, category)
        now = datetime.utcnow().timestamp()
        
        # Add current execution with timestamp as score
        self.redis.zadd(key, {str(now): now})
        
        # Set expiration on the key
        self.redis.expire(key, window_seconds)


class ToolExecutor:
    """Executes Lucy tools with error handling and rate limiting.
    
    Requirements: 5.4
    """
    
    def __init__(self, redis_client: redis.Redis):
        """Initialize tool executor.
        
        Args:
            redis_client: Redis client for rate limiting
        """
        self.tools: Dict[str, Tool] = {}
        self.rate_limiter = RateLimiter(redis_client)
        
        # Rate limit configuration
        self.rate_limits = {
            ToolCategory.PROVISIONING: {
                "limit": 5,
                "window_seconds": 3600  # 1 hour
            },
            ToolCategory.WORKSPACE_MANAGEMENT: {
                "limit": 50,
                "window_seconds": 3600
            },
            ToolCategory.COST_QUERY: {
                "limit": 100,
                "window_seconds": 3600
            },
            ToolCategory.DIAGNOSTICS: {
                "limit": 20,
                "window_seconds": 3600
            },
            ToolCategory.SUPPORT: {
                "limit": 10,
                "window_seconds": 3600
            }
        }
    
    def register_tool(self, tool: Tool) -> None:
        """Register a tool for execution.
        
        Args:
            tool: Tool instance to register
        """
        self.tools[tool.name] = tool
    
    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """Get schemas for all registered tools.
        
        Returns:
            List of tool schemas for Claude function calling
        """
        return [tool.get_schema() for tool in self.tools.values()]
    
    async def execute_tool(
        self,
        tool_name: str,
        user_id: str,
        **kwargs
    ) -> ToolResult:
        """Execute a tool with rate limiting and error handling.
        
        Args:
            tool_name: Name of tool to execute
            user_id: User executing the tool
            **kwargs: Tool-specific parameters
            
        Returns:
            ToolResult with execution result
        """
        # Import audit logging here to avoid circular imports
        from ..lucy.audit import log_lucy_tool_execution, log_lucy_rate_limit_exceeded
        
        # Check if tool exists
        if tool_name not in self.tools:
            result = ToolResult(
                success=False,
                error=f"Unknown tool: {tool_name}"
            )
            # Log failed tool execution
            log_lucy_tool_execution(
                user_id=user_id,
                tool_name=tool_name,
                tool_parameters=kwargs,
                result="Unknown tool",
                success=False,
                error_message=f"Unknown tool: {tool_name}",
            )
            return result
        
        tool = self.tools[tool_name]
        
        # Check rate limit
        rate_config = self.rate_limits.get(tool.category)
        if rate_config:
            allowed, error_msg = await self.rate_limiter.check_rate_limit(
                user_id,
                tool.category,
                rate_config["limit"],
                rate_config["window_seconds"]
            )
            
            if not allowed:
                result = ToolResult(
                    success=False,
                    error=error_msg
                )
                # Log rate limit exceeded
                log_lucy_rate_limit_exceeded(
                    user_id=user_id,
                    tool_name=tool_name,
                    limit=rate_config["limit"],
                    window_seconds=rate_config["window_seconds"],
                )
                return result
        
        # Execute tool with error handling
        try:
            result = await tool.execute(user_id, **kwargs)
            
            # Record execution for rate limiting
            if rate_config and result.success:
                await self.rate_limiter.record_execution(
                    user_id,
                    tool.category,
                    rate_config["window_seconds"]
                )
            
            # Log tool execution
            log_lucy_tool_execution(
                user_id=user_id,
                tool_name=tool_name,
                tool_parameters=kwargs,
                result=str(result.data) if result.success else result.error,
                success=result.success,
                error_message=result.error if not result.success else None,
            )
            
            return result
            
        except Exception as e:
            result = ToolResult(
                success=False,
                error=f"Tool execution failed: {str(e)}"
            )
            # Log failed tool execution
            log_lucy_tool_execution(
                user_id=user_id,
                tool_name=tool_name,
                tool_parameters=kwargs,
                result="Exception",
                success=False,
                error_message=str(e),
            )
            return result
    
    def get_tool(self, tool_name: str) -> Optional[Tool]:
        """Get a registered tool by name.
        
        Args:
            tool_name: Name of tool to retrieve
            
        Returns:
            Tool instance or None if not found
        """
        return self.tools.get(tool_name)


class ConfirmationRequired(Exception):
    """Exception raised when a tool requires user confirmation.
    
    Used for destructive actions like stop, terminate.
    """
    
    def __init__(self, message: str, tool_name: str, parameters: Dict[str, Any]):
        """Initialize confirmation exception.
        
        Args:
            message: Confirmation message to show user
            tool_name: Name of tool requiring confirmation
            parameters: Tool parameters for execution after confirmation
        """
        self.message = message
        self.tool_name = tool_name
        self.parameters = parameters
        super().__init__(message)
