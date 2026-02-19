"""Tests for Lucy AI audit logging.

Tests that all Lucy actions are properly logged.
Requirements: 6.7
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys

# Mock database imports before importing lucy.audit
sys.modules['src.database'] = MagicMock()
sys.modules['src.audit.audit_logger'] = MagicMock()

from src.lucy.audit import (
    LucyAuditLogger,
)


class TestLucyAuditLogger:
    """Test Lucy audit logging functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.logger = LucyAuditLogger()
        self.user_id = "user-123"
        self.source_ip = "192.168.1.1"
        self.user_agent = "Mozilla/5.0"
        self.conversation_id = "conv-abc"
    
    @patch('src.lucy.audit.audit_log')
    def test_log_tool_execution_success(self, mock_audit_log):
        """Test logging successful tool execution."""
        tool_name = "provision_workspace"
        tool_parameters = {"bundle_type": "POWER", "blueprint_id": "bp-123"}
        result = "WorkSpace ws-456 provisioned"
        
        self.logger.log_tool_execution(
            user_id=self.user_id,
            tool_name=tool_name,
            tool_parameters=tool_parameters,
            result=result,
            success=True,
            source_ip=self.source_ip,
            user_agent=self.user_agent,
            conversation_id=self.conversation_id,
        )
        
        # Verify audit_log was called
        assert mock_audit_log.called
        call_args = mock_audit_log.call_args
        
        # Check required fields
        assert call_args.kwargs["user_id"] == self.user_id
        assert call_args.kwargs["action"] == f"lucy.tool.{tool_name}"
        assert call_args.kwargs["resource_type"] == "lucy_tool"
        assert call_args.kwargs["resource_id"] == tool_name
        assert call_args.kwargs["result"] == "SUCCESS"
        assert call_args.kwargs["interface"] == "LUCY"
        assert call_args.kwargs["source_ip"] == self.source_ip
        
        # Check metadata
        metadata = call_args.kwargs["metadata"]
        assert metadata["tool_name"] == tool_name
        assert metadata["tool_parameters"] == tool_parameters
        assert metadata["tool_result"] == result
        assert metadata["conversation_id"] == self.conversation_id
    
    @patch('src.lucy.audit.audit_log')
    def test_log_tool_execution_failure(self, mock_audit_log):
        """Test logging failed tool execution."""
        tool_name = "provision_workspace"
        tool_parameters = {"bundle_type": "POWER"}
        error_message = "Budget exceeded"
        
        self.logger.log_tool_execution(
            user_id=self.user_id,
            tool_name=tool_name,
            tool_parameters=tool_parameters,
            result="",
            success=False,
            error_message=error_message,
            source_ip=self.source_ip,
        )
        
        # Verify audit_log was called
        assert mock_audit_log.called
        call_args = mock_audit_log.call_args
        
        # Check result is FAILURE
        assert call_args.kwargs["result"] == "FAILURE"
        assert call_args.kwargs["error_message"] == error_message
    
    @patch('src.lucy.audit.audit_log')
    def test_log_conversation_start(self, mock_audit_log):
        """Test logging conversation start."""
        self.logger.log_conversation_start(
            user_id=self.user_id,
            conversation_id=self.conversation_id,
            source_ip=self.source_ip,
            user_agent=self.user_agent,
        )
        
        # Verify audit_log was called
        assert mock_audit_log.called
        call_args = mock_audit_log.call_args
        
        assert call_args.kwargs["action"] == "lucy.conversation.start"
        assert call_args.kwargs["resource_type"] == "lucy_conversation"
        assert call_args.kwargs["resource_id"] == self.conversation_id
        assert call_args.kwargs["result"] == "SUCCESS"
    
    @patch('src.lucy.audit.audit_log')
    def test_log_conversation_end(self, mock_audit_log):
        """Test logging conversation end."""
        message_count = 5
        tool_executions = 2
        
        self.logger.log_conversation_end(
            user_id=self.user_id,
            conversation_id=self.conversation_id,
            message_count=message_count,
            tool_executions=tool_executions,
            source_ip=self.source_ip,
        )
        
        # Verify audit_log was called
        assert mock_audit_log.called
        call_args = mock_audit_log.call_args
        
        assert call_args.kwargs["action"] == "lucy.conversation.end"
        metadata = call_args.kwargs["metadata"]
        assert metadata["message_count"] == message_count
        assert metadata["tool_executions"] == tool_executions
    
    @patch('src.lucy.audit.audit_log')
    def test_log_query(self, mock_audit_log):
        """Test logging Lucy query."""
        query = "I need a GPU workspace"
        intent = "provision_workspace"
        
        self.logger.log_query(
            user_id=self.user_id,
            query=query,
            intent=intent,
            source_ip=self.source_ip,
            conversation_id=self.conversation_id,
        )
        
        # Verify audit_log was called
        assert mock_audit_log.called
        call_args = mock_audit_log.call_args
        
        assert call_args.kwargs["action"] == "lucy.query"
        assert call_args.kwargs["resource_type"] == "lucy_query"
        metadata = call_args.kwargs["metadata"]
        assert metadata["query_length"] == len(query)
        assert metadata["intent"] == intent
    
    @patch('src.lucy.audit.audit_log')
    def test_log_rate_limit_exceeded(self, mock_audit_log):
        """Test logging rate limit exceeded."""
        tool_name = "provision_workspace"
        limit = 5
        window_seconds = 3600
        
        self.logger.log_rate_limit_exceeded(
            user_id=self.user_id,
            tool_name=tool_name,
            limit=limit,
            window_seconds=window_seconds,
            source_ip=self.source_ip,
        )
        
        # Verify audit_log was called
        assert mock_audit_log.called
        call_args = mock_audit_log.call_args
        
        assert call_args.kwargs["action"] == "lucy.rate_limit_exceeded"
        assert call_args.kwargs["result"] == "DENIED"
        metadata = call_args.kwargs["metadata"]
        assert metadata["tool_name"] == tool_name
        assert metadata["limit"] == limit
        assert metadata["window_seconds"] == window_seconds
    
    @patch('src.lucy.audit.audit_log')
    def test_log_budget_denial(self, mock_audit_log):
        """Test logging budget denial."""
        tool_name = "provision_workspace"
        estimated_cost = 50.0
        budget_limit = 1000.0
        current_spend = 980.0
        
        self.logger.log_budget_denial(
            user_id=self.user_id,
            tool_name=tool_name,
            estimated_cost=estimated_cost,
            budget_limit=budget_limit,
            current_spend=current_spend,
            source_ip=self.source_ip,
        )
        
        # Verify audit_log was called
        assert mock_audit_log.called
        call_args = mock_audit_log.call_args
        
        assert call_args.kwargs["action"] == "lucy.budget_denial"
        assert call_args.kwargs["result"] == "DENIED"
        metadata = call_args.kwargs["metadata"]
        assert metadata["estimated_cost"] == estimated_cost
        assert metadata["budget_limit"] == budget_limit
        assert metadata["current_spend"] == current_spend
        assert metadata["budget_percentage"] == 98.0
    
    @patch('src.lucy.audit.audit_log')
    def test_log_rbac_denial(self, mock_audit_log):
        """Test logging RBAC denial."""
        tool_name = "provision_workspace"
        required_permission = "workspace.provision"
        user_role = "contractor"
        
        self.logger.log_rbac_denial(
            user_id=self.user_id,
            tool_name=tool_name,
            required_permission=required_permission,
            user_role=user_role,
            source_ip=self.source_ip,
        )
        
        # Verify audit_log was called
        assert mock_audit_log.called
        call_args = mock_audit_log.call_args
        
        assert call_args.kwargs["action"] == "lucy.rbac_denial"
        assert call_args.kwargs["result"] == "DENIED"
        metadata = call_args.kwargs["metadata"]
        assert metadata["tool_name"] == tool_name
        assert metadata["required_permission"] == required_permission
        assert metadata["user_role"] == user_role
    
    def test_map_tool_to_action_type(self):
        """Test mapping tool names to action types."""
        from src.models.audit_log import ActionType
        
        # Test provisioning tool
        action_type = self.logger._map_tool_to_action_type("provision_workspace")
        assert action_type == ActionType.LUCY_PROVISION
        
        # Test query tool
        action_type = self.logger._map_tool_to_action_type("list_workspaces")
        assert action_type == ActionType.LUCY_QUERY
        
        # Test action tool
        action_type = self.logger._map_tool_to_action_type("start_workspace")
        assert action_type == ActionType.LUCY_ACTION
        
        # Test unknown tool (defaults to LUCY_ACTION)
        action_type = self.logger._map_tool_to_action_type("unknown_tool")
        assert action_type == ActionType.LUCY_ACTION
    
    @patch('src.lucy.audit.audit_log')
    def test_convenience_function_log_lucy_tool_execution(self, mock_audit_log):
        """Test convenience function for logging tool execution."""
        from src.lucy.audit import log_lucy_tool_execution
        
        log_lucy_tool_execution(
            user_id=self.user_id,
            tool_name="provision_workspace",
            tool_parameters={"bundle_type": "POWER"},
            result="Success",
            success=True,
        )
        
        assert mock_audit_log.called
    
    @patch('src.lucy.audit.audit_log')
    def test_convenience_function_log_lucy_query(self, mock_audit_log):
        """Test convenience function for logging query."""
        from src.lucy.audit import log_lucy_query
        
        log_lucy_query(
            user_id=self.user_id,
            query="I need a workspace",
            intent="provision_workspace",
        )
        
        assert mock_audit_log.called
    
    @patch('src.lucy.audit.audit_log')
    def test_convenience_function_log_rate_limit(self, mock_audit_log):
        """Test convenience function for logging rate limit."""
        from src.lucy.audit import log_lucy_rate_limit_exceeded
        
        log_lucy_rate_limit_exceeded(
            user_id=self.user_id,
            tool_name="provision_workspace",
            limit=5,
            window_seconds=3600,
        )
        
        assert mock_audit_log.called
    
    @patch('src.lucy.audit.audit_log')
    def test_convenience_function_log_budget_denial(self, mock_audit_log):
        """Test convenience function for logging budget denial."""
        from src.lucy.audit import log_lucy_budget_denial
        
        log_lucy_budget_denial(
            user_id=self.user_id,
            tool_name="provision_workspace",
            estimated_cost=50.0,
            budget_limit=1000.0,
            current_spend=980.0,
        )
        
        assert mock_audit_log.called
    
    @patch('src.lucy.audit.audit_log')
    def test_convenience_function_log_rbac_denial(self, mock_audit_log):
        """Test convenience function for logging RBAC denial."""
        from src.lucy.audit import log_lucy_rbac_denial
        
        log_lucy_rbac_denial(
            user_id=self.user_id,
            tool_name="provision_workspace",
            required_permission="workspace.provision",
            user_role="contractor",
        )
        
        assert mock_audit_log.called
    
    @patch('src.lucy.audit.audit_log')
    def test_audit_logging_does_not_fail_operation(self, mock_audit_log):
        """Test that audit logging failures don't fail the operation."""
        # Make audit_log raise an exception
        mock_audit_log.side_effect = Exception("Database error")
        
        # Should not raise exception
        self.logger.log_tool_execution(
            user_id=self.user_id,
            tool_name="provision_workspace",
            tool_parameters={},
            result="Success",
            success=True,
        )
        
        # Verify it was attempted
        assert mock_audit_log.called
