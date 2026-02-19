"""Audit logging for Lucy AI actions.

Logs every tool execution with user identity, action, and timestamp.
Requirements: 6.7
"""

from typing import Dict, Any, Optional
from datetime import datetime
import logging

from ..audit.audit_logger import audit_log
from ..models.audit_log import ActionType, ActionResult
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class LucyAuditLogger:
    """Audit logger specifically for Lucy AI actions.
    
    Validates: Requirements 6.7
    
    Logs every Lucy action including:
    - User identity
    - Action performed (tool execution, query, etc.)
    - Timestamp
    - Result (success/failure)
    - Additional context
    """
    
    def __init__(self):
        """Initialize Lucy audit logger."""
        pass
    
    def log_tool_execution(
        self,
        user_id: str,
        tool_name: str,
        tool_parameters: Dict[str, Any],
        result: str,
        success: bool,
        error_message: Optional[str] = None,
        source_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        conversation_id: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> None:
        """Log a Lucy tool execution.
        
        Validates: Requirements 6.7
        
        Args:
            user_id: User who triggered the action
            tool_name: Name of the tool executed
            tool_parameters: Parameters passed to the tool
            result: Result of the tool execution
            success: Whether the tool execution succeeded
            error_message: Optional error message if failed
            source_ip: Source IP address
            user_agent: User agent string
            conversation_id: Optional conversation ID for context
            db: Database session
        """
        try:
            # Determine action type based on tool name
            action_type = self._map_tool_to_action_type(tool_name)
            
            # Determine result status
            result_status = ActionResult.SUCCESS if success else ActionResult.FAILURE
            
            # Build metadata
            metadata = {
                "tool_name": tool_name,
                "tool_parameters": tool_parameters,
                "tool_result": result,
                "conversation_id": conversation_id,
                "interface": "LUCY",
            }
            
            # Create audit log entry
            audit_log(
                user_id=user_id,
                action=f"lucy.tool.{tool_name}",
                resource_type="lucy_tool",
                resource_id=tool_name,
                result=result_status.value,
                error_message=error_message,
                source_ip=source_ip,
                user_agent=user_agent,
                interface="LUCY",
                metadata=metadata,
                db=db,
            )
            
            logger.info(
                f"lucy_tool_execution_logged user_id={user_id} tool={tool_name} success={success}"
            )
            
        except Exception as e:
            # Log error but don't fail the operation
            logger.error(f"Failed to log Lucy tool execution: {e}", exc_info=True)
    
    def log_conversation_start(
        self,
        user_id: str,
        conversation_id: str,
        source_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> None:
        """Log the start of a Lucy conversation.
        
        Validates: Requirements 6.7
        
        Args:
            user_id: User starting the conversation
            conversation_id: Conversation identifier
            source_ip: Source IP address
            user_agent: User agent string
            db: Database session
        """
        try:
            metadata = {
                "conversation_id": conversation_id,
                "interface": "LUCY",
            }
            
            audit_log(
                user_id=user_id,
                action="lucy.conversation.start",
                resource_type="lucy_conversation",
                resource_id=conversation_id,
                result=ActionResult.SUCCESS.value,
                source_ip=source_ip,
                user_agent=user_agent,
                interface="LUCY",
                metadata=metadata,
                db=db,
            )
            
            logger.info(f"lucy_conversation_start_logged user_id={user_id} conversation_id={conversation_id}")
            
        except Exception as e:
            logger.error(f"Failed to log Lucy conversation start: {e}", exc_info=True)
    
    def log_conversation_end(
        self,
        user_id: str,
        conversation_id: str,
        message_count: int,
        tool_executions: int,
        source_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> None:
        """Log the end of a Lucy conversation.
        
        Validates: Requirements 6.7
        
        Args:
            user_id: User ending the conversation
            conversation_id: Conversation identifier
            message_count: Number of messages in conversation
            tool_executions: Number of tools executed
            source_ip: Source IP address
            user_agent: User agent string
            db: Database session
        """
        try:
            metadata = {
                "conversation_id": conversation_id,
                "message_count": message_count,
                "tool_executions": tool_executions,
                "interface": "LUCY",
            }
            
            audit_log(
                user_id=user_id,
                action="lucy.conversation.end",
                resource_type="lucy_conversation",
                resource_id=conversation_id,
                result=ActionResult.SUCCESS.value,
                source_ip=source_ip,
                user_agent=user_agent,
                interface="LUCY",
                metadata=metadata,
                db=db,
            )
            
            logger.info(
                f"lucy_conversation_end_logged user_id={user_id} conversation_id={conversation_id} "
                f"messages={message_count} tools={tool_executions}"
            )
            
        except Exception as e:
            logger.error(f"Failed to log Lucy conversation end: {e}", exc_info=True)
    
    def log_query(
        self,
        user_id: str,
        query: str,
        intent: Optional[str] = None,
        source_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        conversation_id: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> None:
        """Log a Lucy query/message.
        
        Validates: Requirements 6.7
        
        Args:
            user_id: User who sent the query
            query: The query text
            intent: Recognized intent (if available)
            source_ip: Source IP address
            user_agent: User agent string
            conversation_id: Optional conversation ID
            db: Database session
        """
        try:
            metadata = {
                "query_length": len(query),
                "intent": intent,
                "conversation_id": conversation_id,
                "interface": "LUCY",
            }
            
            audit_log(
                user_id=user_id,
                action="lucy.query",
                resource_type="lucy_query",
                resource_id=conversation_id,
                result=ActionResult.SUCCESS.value,
                source_ip=source_ip,
                user_agent=user_agent,
                interface="LUCY",
                metadata=metadata,
                db=db,
            )
            
            logger.info(f"lucy_query_logged user_id={user_id} intent={intent}")
            
        except Exception as e:
            logger.error(f"Failed to log Lucy query: {e}", exc_info=True)
    
    def log_rate_limit_exceeded(
        self,
        user_id: str,
        tool_name: str,
        limit: int,
        window_seconds: int,
        source_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        conversation_id: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> None:
        """Log a rate limit exceeded event.
        
        Validates: Requirements 6.7
        
        Args:
            user_id: User who exceeded the rate limit
            tool_name: Tool that was rate limited
            limit: Rate limit threshold
            window_seconds: Rate limit window in seconds
            source_ip: Source IP address
            user_agent: User agent string
            conversation_id: Optional conversation ID
            db: Database session
        """
        try:
            metadata = {
                "tool_name": tool_name,
                "limit": limit,
                "window_seconds": window_seconds,
                "conversation_id": conversation_id,
                "interface": "LUCY",
            }
            
            audit_log(
                user_id=user_id,
                action="lucy.rate_limit_exceeded",
                resource_type="lucy_tool",
                resource_id=tool_name,
                result=ActionResult.DENIED.value,
                error_message=f"Rate limit exceeded: {limit} per {window_seconds}s",
                source_ip=source_ip,
                user_agent=user_agent,
                interface="LUCY",
                metadata=metadata,
                db=db,
            )
            
            logger.warning(
                f"lucy_rate_limit_exceeded user_id={user_id} tool={tool_name} "
                f"limit={limit}/{window_seconds}s"
            )
            
        except Exception as e:
            logger.error(f"Failed to log Lucy rate limit exceeded: {e}", exc_info=True)
    
    def log_budget_denial(
        self,
        user_id: str,
        tool_name: str,
        estimated_cost: float,
        budget_limit: float,
        current_spend: float,
        source_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        conversation_id: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> None:
        """Log a budget denial event.
        
        Validates: Requirements 6.7, 6.4
        
        Args:
            user_id: User whose request was denied
            tool_name: Tool that was denied
            estimated_cost: Estimated cost of the action
            budget_limit: Budget limit
            current_spend: Current spending
            source_ip: Source IP address
            user_agent: User agent string
            conversation_id: Optional conversation ID
            db: Database session
        """
        try:
            metadata = {
                "tool_name": tool_name,
                "estimated_cost": estimated_cost,
                "budget_limit": budget_limit,
                "current_spend": current_spend,
                "budget_percentage": (current_spend / budget_limit * 100) if budget_limit > 0 else 0,
                "conversation_id": conversation_id,
                "interface": "LUCY",
            }
            
            audit_log(
                user_id=user_id,
                action="lucy.budget_denial",
                resource_type="lucy_tool",
                resource_id=tool_name,
                result=ActionResult.DENIED.value,
                error_message=f"Budget exceeded: ${current_spend:.2f} / ${budget_limit:.2f}",
                source_ip=source_ip,
                user_agent=user_agent,
                interface="LUCY",
                metadata=metadata,
                db=db,
            )
            
            logger.warning(
                f"lucy_budget_denial user_id={user_id} tool={tool_name} "
                f"cost=${estimated_cost:.2f} budget=${budget_limit:.2f}"
            )
            
        except Exception as e:
            logger.error(f"Failed to log Lucy budget denial: {e}", exc_info=True)
    
    def log_rbac_denial(
        self,
        user_id: str,
        tool_name: str,
        required_permission: str,
        user_role: str,
        source_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        conversation_id: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> None:
        """Log an RBAC denial event.
        
        Validates: Requirements 6.7, 6.3
        
        Args:
            user_id: User whose request was denied
            tool_name: Tool that was denied
            required_permission: Permission that was required
            user_role: User's current role
            source_ip: Source IP address
            user_agent: User agent string
            conversation_id: Optional conversation ID
            db: Database session
        """
        try:
            metadata = {
                "tool_name": tool_name,
                "required_permission": required_permission,
                "user_role": user_role,
                "conversation_id": conversation_id,
                "interface": "LUCY",
            }
            
            audit_log(
                user_id=user_id,
                action="lucy.rbac_denial",
                resource_type="lucy_tool",
                resource_id=tool_name,
                result=ActionResult.DENIED.value,
                error_message=f"Permission denied: requires {required_permission}, user has role {user_role}",
                source_ip=source_ip,
                user_agent=user_agent,
                interface="LUCY",
                metadata=metadata,
                db=db,
            )
            
            logger.warning(
                f"lucy_rbac_denial user_id={user_id} tool={tool_name} "
                f"required={required_permission} role={user_role}"
            )
            
        except Exception as e:
            logger.error(f"Failed to log Lucy RBAC denial: {e}", exc_info=True)
    
    def _map_tool_to_action_type(self, tool_name: str) -> ActionType:
        """Map tool name to action type.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Corresponding ActionType
        """
        tool_action_map = {
            "provision_workspace": ActionType.LUCY_PROVISION,
            "start_workspace": ActionType.LUCY_ACTION,
            "stop_workspace": ActionType.LUCY_ACTION,
            "terminate_workspace": ActionType.LUCY_ACTION,
            "list_workspaces": ActionType.LUCY_QUERY,
            "get_cost_summary": ActionType.LUCY_QUERY,
            "get_cost_recommendations": ActionType.LUCY_QUERY,
            "check_budget": ActionType.LUCY_QUERY,
            "run_diagnostics": ActionType.LUCY_ACTION,
            "create_support_ticket": ActionType.LUCY_ACTION,
        }
        
        return tool_action_map.get(tool_name, ActionType.LUCY_ACTION)


# Global Lucy audit logger instance
_lucy_audit_logger = LucyAuditLogger()


def log_lucy_tool_execution(
    user_id: str,
    tool_name: str,
    tool_parameters: Dict[str, Any],
    result: str,
    success: bool,
    **kwargs
) -> None:
    """Convenience function for logging Lucy tool executions.
    
    Args:
        user_id: User who triggered the action
        tool_name: Name of the tool executed
        tool_parameters: Parameters passed to the tool
        result: Result of the tool execution
        success: Whether the tool execution succeeded
        **kwargs: Additional audit log fields
    """
    _lucy_audit_logger.log_tool_execution(
        user_id=user_id,
        tool_name=tool_name,
        tool_parameters=tool_parameters,
        result=result,
        success=success,
        **kwargs
    )


def log_lucy_query(
    user_id: str,
    query: str,
    intent: Optional[str] = None,
    **kwargs
) -> None:
    """Convenience function for logging Lucy queries.
    
    Args:
        user_id: User who sent the query
        query: The query text
        intent: Recognized intent (if available)
        **kwargs: Additional audit log fields
    """
    _lucy_audit_logger.log_query(
        user_id=user_id,
        query=query,
        intent=intent,
        **kwargs
    )


def log_lucy_rate_limit_exceeded(
    user_id: str,
    tool_name: str,
    limit: int,
    window_seconds: int,
    **kwargs
) -> None:
    """Convenience function for logging rate limit exceeded events.
    
    Args:
        user_id: User who exceeded the rate limit
        tool_name: Tool that was rate limited
        limit: Rate limit threshold
        window_seconds: Rate limit window in seconds
        **kwargs: Additional audit log fields
    """
    _lucy_audit_logger.log_rate_limit_exceeded(
        user_id=user_id,
        tool_name=tool_name,
        limit=limit,
        window_seconds=window_seconds,
        **kwargs
    )


def log_lucy_budget_denial(
    user_id: str,
    tool_name: str,
    estimated_cost: float,
    budget_limit: float,
    current_spend: float,
    **kwargs
) -> None:
    """Convenience function for logging budget denial events.
    
    Args:
        user_id: User whose request was denied
        tool_name: Tool that was denied
        estimated_cost: Estimated cost of the action
        budget_limit: Budget limit
        current_spend: Current spending
        **kwargs: Additional audit log fields
    """
    _lucy_audit_logger.log_budget_denial(
        user_id=user_id,
        tool_name=tool_name,
        estimated_cost=estimated_cost,
        budget_limit=budget_limit,
        current_spend=current_spend,
        **kwargs
    )


def log_lucy_rbac_denial(
    user_id: str,
    tool_name: str,
    required_permission: str,
    user_role: str,
    **kwargs
) -> None:
    """Convenience function for logging RBAC denial events.
    
    Args:
        user_id: User whose request was denied
        tool_name: Tool that was denied
        required_permission: Permission that was required
        user_role: User's current role
        **kwargs: Additional audit log fields
    """
    _lucy_audit_logger.log_rbac_denial(
        user_id=user_id,
        tool_name=tool_name,
        required_permission=required_permission,
        user_role=user_role,
        **kwargs
    )
