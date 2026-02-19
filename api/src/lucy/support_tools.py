"""Support and routing tools for Lucy AI.

These tools handle support ticket creation and fallback routing.
Requirements: 5.8
"""

from typing import Dict, Any, Optional
import httpx

from .tool_executor import Tool, ToolResult, ToolCategory


class CreateSupportTicketTool(Tool):
    """Tool for creating support tickets.
    
    Calls Forge API POST /api/v1/support/tickets endpoint.
    Used when Lucy cannot fulfill a request directly.
    Requirements: 5.8
    """
    
    def __init__(self, api_base_url: str):
        """Initialize create support ticket tool.
        
        Args:
            api_base_url: Base URL for Forge API
        """
        super().__init__(
            name="create_support_ticket",
            category=ToolCategory.SUPPORT,
            description=(
                "Create a support ticket for requests that cannot be fulfilled automatically. "
                "Use this when the user needs human assistance or when a request requires "
                "approval workflows. Provide a clear title and detailed description."
            )
        )
        self.api_base_url = api_base_url
    
    async def execute(self, user_id: str, **kwargs) -> ToolResult:
        """Execute support ticket creation.
        
        Args:
            user_id: User creating the ticket
            **kwargs: Must include title and description
            
        Returns:
            ToolResult with ticket details
        """
        title = kwargs.get("title")
        description = kwargs.get("description")
        priority = kwargs.get("priority", "medium")
        category = kwargs.get("category", "general")
        
        if not title:
            return ToolResult(
                success=False,
                error="title is required"
            )
        
        if not description:
            return ToolResult(
                success=False,
                error="description is required"
            )
        
        # Build request payload
        payload = {
            "title": title,
            "description": description,
            "priority": priority,
            "category": category,
            "source": "lucy_ai"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base_url}/api/v1/support/tickets",
                    json=payload,
                    headers={"X-User-ID": user_id},
                    timeout=10.0
                )
                
                if response.status_code == 201:
                    ticket = response.json()
                    return ToolResult(
                        success=True,
                        data={
                            "ticket_id": ticket.get("id"),
                            "status": ticket.get("status"),
                            "created_at": ticket.get("created_at"),
                            "message": (
                                f"Support ticket #{ticket.get('id')} created successfully. "
                                f"A support team member will review your request shortly."
                            )
                        }
                    )
                else:
                    error_data = response.json()
                    return ToolResult(
                        success=False,
                        error=f"Failed to create ticket: {error_data.get('detail', 'Unknown error')}"
                    )
                    
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Failed to create support ticket: {str(e)}"
            )
    
    def _get_input_schema(self) -> Dict[str, Any]:
        """Get input schema for ticket creation."""
        return {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Brief title summarizing the request"
                },
                "description": {
                    "type": "string",
                    "description": "Detailed description of the request or issue"
                },
                "priority": {
                    "type": "string",
                    "enum": ["low", "medium", "high", "urgent"],
                    "description": "Priority level for the ticket",
                    "default": "medium"
                },
                "category": {
                    "type": "string",
                    "enum": ["general", "provisioning", "access", "billing", "technical"],
                    "description": "Category of the request",
                    "default": "general"
                }
            },
            "required": ["title", "description"]
        }


class FallbackRouter:
    """Handles fallback routing for unfulfillable requests.
    
    Determines when to route requests to support tickets or approval workflows.
    Requirements: 5.8
    """
    
    def __init__(self, support_ticket_tool: CreateSupportTicketTool):
        """Initialize fallback router.
        
        Args:
            support_ticket_tool: Tool for creating support tickets
        """
        self.support_ticket_tool = support_ticket_tool
    
    async def route_unfulfillable_request(
        self,
        user_id: str,
        request: str,
        reason: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ToolResult:
        """Route an unfulfillable request to appropriate channel.
        
        Args:
            user_id: User making the request
            request: Original user request
            reason: Reason why request cannot be fulfilled
            context: Optional context about the request
            
        Returns:
            ToolResult with routing outcome
        """
        # Determine priority based on reason
        priority = "medium"
        category = "general"
        
        if "permission" in reason.lower() or "access" in reason.lower():
            priority = "high"
            category = "access"
        elif "budget" in reason.lower() or "cost" in reason.lower():
            priority = "high"
            category = "billing"
        elif "error" in reason.lower() or "failed" in reason.lower():
            priority = "high"
            category = "technical"
        elif "approval" in reason.lower():
            priority = "medium"
            category = "provisioning"
        
        # Build ticket description
        description = f"""
User Request: {request}

Reason for Routing: {reason}

Context:
{self._format_context(context)}

This request was automatically routed by Lucy AI because it could not be fulfilled directly.
Please review and take appropriate action.
        """.strip()
        
        # Create support ticket
        result = await self.support_ticket_tool.execute(
            user_id=user_id,
            title=f"Lucy AI Routing: {request[:50]}...",
            description=description,
            priority=priority,
            category=category
        )
        
        return result
    
    def _format_context(self, context: Optional[Dict[str, Any]]) -> str:
        """Format context dictionary for ticket description.
        
        Args:
            context: Context dictionary
            
        Returns:
            Formatted context string
        """
        if not context:
            return "No additional context provided"
        
        lines = []
        for key, value in context.items():
            lines.append(f"- {key}: {value}")
        
        return "\n".join(lines)
    
    def should_route_to_support(self, error_type: str) -> bool:
        """Determine if an error should be routed to support.
        
        Args:
            error_type: Type of error encountered
            
        Returns:
            True if should route to support, False otherwise
        """
        # Route to support for these error types
        support_errors = [
            "permission_denied",
            "budget_exceeded",
            "approval_required",
            "quota_exceeded",
            "configuration_error",
            "unknown_error"
        ]
        
        return error_type in support_errors
    
    def get_fallback_message(self, error_type: str) -> str:
        """Get user-friendly fallback message for error type.
        
        Args:
            error_type: Type of error encountered
            
        Returns:
            User-friendly message
        """
        messages = {
            "permission_denied": (
                "I don't have permission to complete this request. "
                "I've created a support ticket for you. A team member will review your access needs."
            ),
            "budget_exceeded": (
                "This request would exceed your budget limit. "
                "I've created a support ticket to discuss budget adjustments with your team lead."
            ),
            "approval_required": (
                "This request requires approval from your team lead or admin. "
                "I've created a support ticket to route this through the approval workflow."
            ),
            "quota_exceeded": (
                "You've reached your quota limit for this resource. "
                "I've created a support ticket to request a quota increase."
            ),
            "configuration_error": (
                "There's a configuration issue preventing this request. "
                "I've created a support ticket for the technical team to investigate."
            ),
            "unknown_error": (
                "I encountered an unexpected error. "
                "I've created a support ticket so the team can investigate and help you."
            )
        }
        
        return messages.get(
            error_type,
            "I couldn't complete this request. I've created a support ticket for assistance."
        )
