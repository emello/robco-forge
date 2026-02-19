"""Tests for Lucy tool executor framework.

Requirements: 5.4
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock
import asyncio

from src.lucy.tool_executor import (
    Tool,
    ToolResult,
    ToolCategory,
    ToolExecutor,
    RateLimiter,
    ConfirmationRequired
)


class MockTool(Tool):
    """Mock tool for testing."""
    
    def __init__(self):
        super().__init__(
            name="mock_tool",
            category=ToolCategory.WORKSPACE_MANAGEMENT,
            description="A mock tool for testing"
        )
        self.execute_called = False
        self.execute_params = None
    
    async def execute(self, user_id: str, **kwargs) -> ToolResult:
        """Execute mock tool."""
        self.execute_called = True
        self.execute_params = {"user_id": user_id, **kwargs}
        
        return ToolResult(
            success=True,
            data={"result": "mock_success"}
        )
    
    def _get_input_schema(self):
        """Get input schema."""
        return {
            "type": "object",
            "properties": {
                "param1": {"type": "string"},
                "param2": {"type": "number"}
            },
            "required": ["param1"]
        }


class MockProvisioningTool(Tool):
    """Mock provisioning tool for rate limit testing."""
    
    def __init__(self):
        super().__init__(
            name="provision_workspace",
            category=ToolCategory.PROVISIONING,
            description="Provision a workspace"
        )
    
    async def execute(self, user_id: str, **kwargs) -> ToolResult:
        """Execute provisioning."""
        return ToolResult(
            success=True,
            data={"workspace_id": "ws-123"}
        )
    
    def _get_input_schema(self):
        """Get input schema."""
        return {
            "type": "object",
            "properties": {
                "bundle_type": {"type": "string"}
            }
        }


@pytest.fixture
def mock_redis():
    """Create a mock Redis client."""
    redis_mock = Mock()
    redis_mock.zremrangebyscore = Mock()
    redis_mock.zcard = Mock(return_value=0)
    redis_mock.zrange = Mock(return_value=[])
    redis_mock.zadd = Mock()
    redis_mock.expire = Mock()
    return redis_mock


@pytest.fixture
def rate_limiter(mock_redis):
    """Create a RateLimiter with mock Redis."""
    return RateLimiter(mock_redis)


@pytest.fixture
def tool_executor(mock_redis):
    """Create a ToolExecutor with mock Redis."""
    return ToolExecutor(mock_redis)


def test_tool_result_success():
    """Test successful ToolResult."""
    result = ToolResult(
        success=True,
        data={"key": "value"}
    )
    
    assert result.success is True
    assert result.data == {"key": "value"}
    assert result.error is None


def test_tool_result_error():
    """Test error ToolResult."""
    result = ToolResult(
        success=False,
        error="Something went wrong"
    )
    
    assert result.success is False
    assert result.error == "Something went wrong"
    assert result.data is None


def test_tool_result_requires_confirmation():
    """Test ToolResult with confirmation requirement."""
    result = ToolResult(
        success=True,
        requires_confirmation=True,
        confirmation_message="Are you sure?"
    )
    
    assert result.requires_confirmation is True
    assert result.confirmation_message == "Are you sure?"


def test_tool_initialization():
    """Test Tool initialization."""
    tool = MockTool()
    
    assert tool.name == "mock_tool"
    assert tool.category == ToolCategory.WORKSPACE_MANAGEMENT
    assert tool.description == "A mock tool for testing"


def test_tool_get_schema():
    """Test tool schema generation."""
    tool = MockTool()
    schema = tool.get_schema()
    
    assert schema["name"] == "mock_tool"
    assert schema["description"] == "A mock tool for testing"
    assert "input_schema" in schema
    assert schema["input_schema"]["type"] == "object"
    assert "param1" in schema["input_schema"]["properties"]


@pytest.mark.asyncio
async def test_tool_execute():
    """Test tool execution."""
    tool = MockTool()
    result = await tool.execute("user123", param1="value1", param2=42)
    
    assert result.success is True
    assert result.data == {"result": "mock_success"}
    assert tool.execute_called is True
    assert tool.execute_params["user_id"] == "user123"
    assert tool.execute_params["param1"] == "value1"


@pytest.mark.asyncio
async def test_rate_limiter_allows_within_limit(rate_limiter, mock_redis):
    """Test rate limiter allows requests within limit."""
    mock_redis.zcard.return_value = 3  # 3 requests in window
    
    allowed, error = await rate_limiter.check_rate_limit(
        "user123",
        ToolCategory.PROVISIONING,
        limit=5,
        window_seconds=3600
    )
    
    assert allowed is True
    assert error is None


@pytest.mark.asyncio
async def test_rate_limiter_blocks_over_limit(rate_limiter, mock_redis):
    """Test rate limiter blocks requests over limit."""
    mock_redis.zcard.return_value = 5  # At limit
    mock_redis.zrange.return_value = [(b"timestamp", 1000.0)]
    
    allowed, error = await rate_limiter.check_rate_limit(
        "user123",
        ToolCategory.PROVISIONING,
        limit=5,
        window_seconds=3600
    )
    
    assert allowed is False
    assert error is not None
    assert "Rate limit exceeded" in error
    assert "provisioning" in error


@pytest.mark.asyncio
async def test_rate_limiter_record_execution(rate_limiter, mock_redis):
    """Test recording tool execution."""
    await rate_limiter.record_execution(
        "user123",
        ToolCategory.PROVISIONING,
        window_seconds=3600
    )
    
    # Verify Redis calls
    mock_redis.zadd.assert_called_once()
    mock_redis.expire.assert_called_once()


def test_rate_limiter_key_format(rate_limiter):
    """Test Redis key format for rate limiting."""
    key = rate_limiter._get_key("user123", ToolCategory.PROVISIONING)
    
    assert key == "lucy:ratelimit:user123:provisioning"


def test_tool_executor_initialization(tool_executor):
    """Test ToolExecutor initialization."""
    assert len(tool_executor.tools) == 0
    assert tool_executor.rate_limiter is not None
    
    # Check rate limit configuration
    assert ToolCategory.PROVISIONING in tool_executor.rate_limits
    assert tool_executor.rate_limits[ToolCategory.PROVISIONING]["limit"] == 5
    assert tool_executor.rate_limits[ToolCategory.PROVISIONING]["window_seconds"] == 3600


def test_tool_executor_register_tool(tool_executor):
    """Test registering a tool."""
    tool = MockTool()
    tool_executor.register_tool(tool)
    
    assert "mock_tool" in tool_executor.tools
    assert tool_executor.tools["mock_tool"] == tool


def test_tool_executor_get_tool_schemas(tool_executor):
    """Test getting all tool schemas."""
    tool1 = MockTool()
    tool2 = MockProvisioningTool()
    
    tool_executor.register_tool(tool1)
    tool_executor.register_tool(tool2)
    
    schemas = tool_executor.get_tool_schemas()
    
    assert len(schemas) == 2
    assert any(s["name"] == "mock_tool" for s in schemas)
    assert any(s["name"] == "provision_workspace" for s in schemas)


@pytest.mark.asyncio
async def test_tool_executor_execute_unknown_tool(tool_executor):
    """Test executing unknown tool."""
    result = await tool_executor.execute_tool(
        "unknown_tool",
        "user123"
    )
    
    assert result.success is False
    assert "Unknown tool" in result.error


@pytest.mark.asyncio
async def test_tool_executor_execute_tool_success(tool_executor, mock_redis):
    """Test successful tool execution."""
    tool = MockTool()
    tool_executor.register_tool(tool)
    
    # Mock rate limit check to allow
    mock_redis.zcard.return_value = 0
    
    result = await tool_executor.execute_tool(
        "mock_tool",
        "user123",
        param1="value1"
    )
    
    assert result.success is True
    assert result.data == {"result": "mock_success"}
    assert tool.execute_called is True


@pytest.mark.asyncio
async def test_tool_executor_rate_limit_enforcement(tool_executor, mock_redis):
    """Test rate limit enforcement during execution."""
    tool = MockProvisioningTool()
    tool_executor.register_tool(tool)
    
    # Mock rate limit exceeded
    mock_redis.zcard.return_value = 5  # At limit
    mock_redis.zrange.return_value = [(b"timestamp", 1000.0)]
    
    result = await tool_executor.execute_tool(
        "provision_workspace",
        "user123",
        bundle_type="STANDARD"
    )
    
    assert result.success is False
    assert "Rate limit exceeded" in result.error


@pytest.mark.asyncio
async def test_tool_executor_records_successful_execution(tool_executor, mock_redis):
    """Test that successful executions are recorded for rate limiting."""
    tool = MockProvisioningTool()
    tool_executor.register_tool(tool)
    
    # Mock rate limit check to allow
    mock_redis.zcard.return_value = 0
    
    result = await tool_executor.execute_tool(
        "provision_workspace",
        "user123",
        bundle_type="STANDARD"
    )
    
    assert result.success is True
    
    # Verify execution was recorded
    mock_redis.zadd.assert_called_once()


def test_tool_executor_get_tool(tool_executor):
    """Test getting a tool by name."""
    tool = MockTool()
    tool_executor.register_tool(tool)
    
    retrieved = tool_executor.get_tool("mock_tool")
    
    assert retrieved == tool


def test_tool_executor_get_nonexistent_tool(tool_executor):
    """Test getting a tool that doesn't exist."""
    retrieved = tool_executor.get_tool("nonexistent")
    
    assert retrieved is None


def test_confirmation_required_exception():
    """Test ConfirmationRequired exception."""
    params = {"workspace_id": "ws-123"}
    exc = ConfirmationRequired(
        "Are you sure you want to terminate this workspace?",
        "terminate_workspace",
        params
    )
    
    assert exc.message == "Are you sure you want to terminate this workspace?"
    assert exc.tool_name == "terminate_workspace"
    assert exc.parameters == params


def test_tool_categories():
    """Test ToolCategory enum."""
    assert ToolCategory.PROVISIONING.value == "provisioning"
    assert ToolCategory.WORKSPACE_MANAGEMENT.value == "workspace_management"
    assert ToolCategory.COST_QUERY.value == "cost_query"
    assert ToolCategory.DIAGNOSTICS.value == "diagnostics"
    assert ToolCategory.SUPPORT.value == "support"


def test_rate_limit_configuration(tool_executor):
    """Test rate limit configuration for different categories."""
    # Provisioning: 5 per hour
    prov_config = tool_executor.rate_limits[ToolCategory.PROVISIONING]
    assert prov_config["limit"] == 5
    assert prov_config["window_seconds"] == 3600
    
    # Workspace management: 50 per hour
    ws_config = tool_executor.rate_limits[ToolCategory.WORKSPACE_MANAGEMENT]
    assert ws_config["limit"] == 50
    
    # Cost queries: 100 per hour
    cost_config = tool_executor.rate_limits[ToolCategory.COST_QUERY]
    assert cost_config["limit"] == 100
