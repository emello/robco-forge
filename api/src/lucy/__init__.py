"""Lucy AI Service - Conversational AI assistant for RobCo Forge.

Requirements:
- 5.1: AI chatbot powered by Anthropic Claude
- 5.4: Tool execution with rate limiting
- 5.5: Workspace management tools
- 5.6: Cost query tools
- 5.7: Diagnostic tools
- 5.8: Support and fallback routing
- 6.1: Conversation context retention (30 minutes)
- 6.2: Context expiration after 30 minutes
- 6.3: RBAC enforcement
- 6.4: Budget enforcement
- 6.5: Security constraints
"""

from .claude_client import ClaudeClient
from .context_manager import (
    ConversationContext,
    ConversationContextManager,
    Message
)
from .tool_executor import (
    Tool,
    ToolResult,
    ToolCategory,
    ToolExecutor,
    RateLimiter,
    ConfirmationRequired
)
from .workspace_tools import (
    ProvisionWorkspaceTool,
    ListWorkspacesTool,
    StartWorkspaceTool,
    StopWorkspaceTool,
    TerminateWorkspaceTool
)
from .cost_tools import (
    GetCostSummaryTool,
    GetCostRecommendationsTool,
    CheckBudgetTool,
    RunDiagnosticsTool
)
from .support_tools import (
    CreateSupportTicketTool,
    FallbackRouter
)
from .system_prompt import (
    LucySystemPrompt,
    PROMPT_TEMPLATES
)

__all__ = [
    'ClaudeClient',
    'ConversationContext',
    'ConversationContextManager',
    'Message',
    'Tool',
    'ToolResult',
    'ToolCategory',
    'ToolExecutor',
    'RateLimiter',
    'ConfirmationRequired',
    'ProvisionWorkspaceTool',
    'ListWorkspacesTool',
    'StartWorkspaceTool',
    'StopWorkspaceTool',
    'TerminateWorkspaceTool',
    'GetCostSummaryTool',
    'GetCostRecommendationsTool',
    'CheckBudgetTool',
    'RunDiagnosticsTool',
    'CreateSupportTicketTool',
    'FallbackRouter',
    'LucySystemPrompt',
    'PROMPT_TEMPLATES'
]
