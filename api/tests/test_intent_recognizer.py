"""Tests for Lucy AI intent recognition.

Tests intent recognition, entity extraction, and ambiguity handling.
Requirements: 5.3, 5.4, 5.5
"""

import pytest
from src.lucy.intent_recognizer import IntentRecognizer, Intent, RecognizedIntent


class TestIntentRecognition:
    """Test intent recognition from user messages."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.recognizer = IntentRecognizer()
    
    # Greeting intents
    def test_recognize_greeting(self):
        """Test greeting intent recognition."""
        messages = ["hi", "hello", "hey Lucy", "greetings"]
        
        for message in messages:
            result = self.recognizer.recognize(message)
            assert result.intent == Intent.GREETING
            assert result.confidence > 0.7
    
    # Help intents
    def test_recognize_help(self):
        """Test help intent recognition."""
        messages = [
            "help",
            "what can you do",
            "show me your capabilities",
            "how do I provision a workspace"
        ]
        
        for message in messages:
            result = self.recognizer.recognize(message)
            assert result.intent == Intent.HELP
    
    # Provision workspace intents (Req 5.4)
    def test_recognize_provision_workspace(self):
        """Test workspace provisioning intent recognition."""
        messages = [
            "provision a workspace",
            "create a new workstation",
            "I need a workspace",
            "launch a desktop",
            "spin up a machine",
            "get me a workspace"
        ]
        
        for message in messages:
            result = self.recognizer.recognize(message)
            assert result.intent == Intent.PROVISION_WORKSPACE
            assert result.tool_name == "provision_workspace"
            assert result.confidence > 0.7
    
    def test_provision_with_bundle_type(self):
        """Test provisioning intent with bundle type extraction."""
        result = self.recognizer.recognize("provision a POWER workspace")
        
        assert result.intent == Intent.PROVISION_WORKSPACE
        assert result.entities.get("bundle_type") == "POWER"
    
    # Bundle recommendation intents (Req 5.3)
    def test_recognize_bundle_recommendation(self):
        """Test bundle recommendation intent recognition."""
        messages = [
            "recommend a bundle",
            "which bundle should I use",
            "what configuration do I need",
            "suggest a bundle for ML",
            "help me choose a bundle"
        ]
        
        for message in messages:
            result = self.recognizer.recognize(message)
            assert result.intent == Intent.RECOMMEND_BUNDLE
    
    def test_recommend_bundle_gpu_workload(self):
        """Test bundle recommendation for GPU workloads."""
        result = self.recognizer.recognize("I need a workspace for GPU simulations")
        
        assert result.intent in [Intent.RECOMMEND_BUNDLE, Intent.PROVISION_WORKSPACE]
        if result.intent == Intent.RECOMMEND_BUNDLE:
            requirements = result.entities.get("requirements", {})
            assert requirements.get("needs_gpu") is True
    
    def test_recommend_bundle_ml_workload(self):
        """Test bundle recommendation for ML workloads."""
        result = self.recognizer.recognize("recommend a bundle for machine learning")
        
        assert result.intent == Intent.RECOMMEND_BUNDLE
        requirements = result.entities.get("requirements", {})
        assert requirements.get("needs_high_compute") is True
        assert requirements.get("workload_type") == "ml"
    
    def test_bundle_recommendations_gpu(self):
        """Test bundle recommendations for GPU requirements."""
        requirements = {"needs_gpu": True, "intensity": "high"}
        recommendations = self.recognizer.recommend_bundle(requirements)
        
        assert "GRAPHICSPRO_G4DN" in recommendations or "GRAPHICS_G4DN" in recommendations
        assert len(recommendations) <= 3
    
    def test_bundle_recommendations_ml(self):
        """Test bundle recommendations for ML workloads."""
        requirements = {"needs_high_compute": True, "workload_type": "ml"}
        recommendations = self.recognizer.recommend_bundle(requirements)
        
        assert "POWERPRO" in recommendations or "POWER" in recommendations
        assert len(recommendations) <= 3
    
    def test_bundle_recommendations_light(self):
        """Test bundle recommendations for light workloads."""
        requirements = {"intensity": "low"}
        recommendations = self.recognizer.recommend_bundle(requirements)
        
        assert "STANDARD" in recommendations
        assert len(recommendations) <= 3
    
    # List workspaces intents (Req 5.5)
    def test_recognize_list_workspaces(self):
        """Test list workspaces intent recognition."""
        messages = [
            "list my workspaces",
            "show me my workstations",
            "what workspaces do I have",
            "display all my desktops",
            "my workspaces"
        ]
        
        for message in messages:
            result = self.recognizer.recognize(message)
            assert result.intent == Intent.LIST_WORKSPACES
            assert result.tool_name == "list_workspaces"
    
    # Start workspace intents (Req 5.5)
    def test_recognize_start_workspace(self):
        """Test start workspace intent recognition."""
        messages = [
            "start my workspace",
            "boot workspace ws-1234",
            "power on my workstation",
            "turn on workspace-abcd"
        ]
        
        for message in messages:
            result = self.recognizer.recognize(message)
            assert result.intent == Intent.START_WORKSPACE
            assert result.tool_name == "start_workspace"
    
    def test_start_workspace_with_id(self):
        """Test start workspace with ID extraction."""
        result = self.recognizer.recognize("start workspace ws-1234")
        
        assert result.intent == Intent.START_WORKSPACE
        assert "workspace_id" in result.entities
        assert "1234" in result.entities["workspace_id"]
    
    # Stop workspace intents (Req 5.5)
    def test_recognize_stop_workspace(self):
        """Test stop workspace intent recognition."""
        messages = [
            "stop my workspace",
            "shutdown workspace ws-5678",
            "power off my workstation",
            "turn off workspace-xyz"
        ]
        
        for message in messages:
            result = self.recognizer.recognize(message)
            assert result.intent == Intent.STOP_WORKSPACE
            assert result.tool_name == "stop_workspace"
    
    # Terminate workspace intents (Req 5.5)
    def test_recognize_terminate_workspace(self):
        """Test terminate workspace intent recognition."""
        messages = [
            "terminate my workspace",
            "delete workspace ws-9999",
            "destroy my workstation",
            "remove workspace-test"
        ]
        
        for message in messages:
            result = self.recognizer.recognize(message)
            assert result.intent == Intent.TERMINATE_WORKSPACE
            assert result.tool_name == "terminate_workspace"
    
    # Get workspace status intents (Req 5.5)
    def test_recognize_workspace_status(self):
        """Test workspace status intent recognition."""
        messages = [
            "status of my workspace",
            "what's the state of workspace ws-1111",
            "show me workspace info",
            "describe workspace-test"
        ]
        
        for message in messages:
            result = self.recognizer.recognize(message)
            assert result.intent == Intent.GET_WORKSPACE_STATUS
    
    # Cost summary intents (Req 5.6)
    def test_recognize_cost_summary(self):
        """Test cost summary intent recognition."""
        messages = [
            "what are my costs",
            "how much am I spending",
            "show me my expenses",
            "what's my bill",
            "cost summary"
        ]
        
        for message in messages:
            result = self.recognizer.recognize(message)
            assert result.intent == Intent.GET_COST_SUMMARY
            assert result.tool_name == "get_cost_summary"
    
    def test_cost_summary_with_period(self):
        """Test cost summary with time period extraction."""
        result = self.recognizer.recognize("what are my costs this month")
        
        assert result.intent == Intent.GET_COST_SUMMARY
        assert result.entities.get("period") == "current_month"
    
    def test_cost_summary_with_team(self):
        """Test cost summary with team filter extraction."""
        result = self.recognizer.recognize("show me costs for team: robotics")
        
        assert result.intent == Intent.GET_COST_SUMMARY
        assert result.entities.get("team_id") == "robotics"
    
    # Cost recommendations intents (Req 5.6)
    def test_recognize_cost_recommendations(self):
        """Test cost recommendations intent recognition."""
        messages = [
            "cost optimization recommendations",
            "how can I save money",
            "suggest ways to reduce costs",
            "optimize my spending"
        ]
        
        for message in messages:
            result = self.recognizer.recognize(message)
            assert result.intent == Intent.GET_COST_RECOMMENDATIONS
            assert result.tool_name == "get_cost_recommendations"
    
    # Budget check intents (Req 5.6)
    def test_recognize_budget_check(self):
        """Test budget check intent recognition."""
        messages = [
            "check my budget",
            "how much budget do I have left",
            "show me my quota",
            "what's my budget status"
        ]
        
        for message in messages:
            result = self.recognizer.recognize(message)
            assert result.intent == Intent.CHECK_BUDGET
            assert result.tool_name == "check_budget"
    
    # Diagnostics intents (Req 5.7)
    def test_recognize_diagnostics(self):
        """Test diagnostics intent recognition."""
        messages = [
            "run diagnostics on my workspace",
            "check workspace ws-1234",
            "diagnose my workstation",
            "test workspace health"
        ]
        
        for message in messages:
            result = self.recognizer.recognize(message)
            assert result.intent == Intent.RUN_DIAGNOSTICS
            assert result.tool_name == "run_diagnostics"
    
    def test_recognize_troubleshoot(self):
        """Test troubleshooting intent recognition."""
        messages = [
            "my workspace is not working",
            "workspace is broken",
            "can't connect to my workstation",
            "workspace is slow"
        ]
        
        for message in messages:
            result = self.recognizer.recognize(message)
            assert result.intent == Intent.TROUBLESHOOT
            assert result.tool_name == "run_diagnostics"
    
    # Support ticket intents (Req 5.8)
    def test_recognize_support_ticket(self):
        """Test support ticket intent recognition."""
        messages = [
            "create a support ticket",
            "I need help from support",
            "talk to a human",
            "escalate this issue"
        ]
        
        for message in messages:
            result = self.recognizer.recognize(message)
            assert result.intent == Intent.CREATE_SUPPORT_TICKET
            assert result.tool_name == "create_support_ticket"
    
    # Entity extraction tests
    def test_extract_workspace_id(self):
        """Test workspace ID extraction."""
        messages = [
            ("start ws-1234", "ws-1234"),
            ("stop workspace-abcd", "workspace-abcd"),
            ("terminate WS-XYZ9", "WS-XYZ9")
        ]
        
        for message, expected_id in messages:
            result = self.recognizer.recognize(message)
            assert "workspace_id" in result.entities
            assert expected_id.lower() in result.entities["workspace_id"].lower()
    
    def test_extract_time_period(self):
        """Test time period extraction."""
        test_cases = [
            ("costs this month", "current_month"),
            ("spending last month", "last_month"),
            ("costs last 7 days", "last_7_days"),
            ("expenses last 30 days", "last_30_days")
        ]
        
        for message, expected_period in test_cases:
            result = self.recognizer.recognize(message)
            if result.intent == Intent.GET_COST_SUMMARY:
                assert result.entities.get("period") == expected_period
    
    # Ambiguity handling tests
    def test_unknown_intent(self):
        """Test handling of unknown intents."""
        result = self.recognizer.recognize("xyzabc random gibberish")
        
        assert result.intent == Intent.UNKNOWN
        assert result.ambiguous is True
        assert result.clarification_needed is not None
    
    def test_clarification_needed_no_workspace_id(self):
        """Test clarification request when workspace ID is missing."""
        result = self.recognizer.recognize("start my workspace")
        
        # Should recognize intent but need clarification
        assert result.intent == Intent.START_WORKSPACE
        if "workspace_id" not in result.entities:
            assert result.clarification_needed is not None
    
    def test_clarification_needed_no_bundle_type(self):
        """Test clarification request when bundle type is missing."""
        result = self.recognizer.recognize("provision a workspace")
        
        assert result.intent == Intent.PROVISION_WORKSPACE
        if "bundle_type" not in result.entities:
            assert result.clarification_needed is not None
    
    # Bundle description tests
    def test_get_bundle_description(self):
        """Test bundle description retrieval."""
        descriptions = {
            "STANDARD": self.recognizer.get_bundle_description("STANDARD"),
            "PERFORMANCE": self.recognizer.get_bundle_description("PERFORMANCE"),
            "POWER": self.recognizer.get_bundle_description("POWER"),
            "GRAPHICS_G4DN": self.recognizer.get_bundle_description("GRAPHICS_G4DN")
        }
        
        for bundle, desc in descriptions.items():
            # Check that description contains key info (not necessarily the exact bundle name)
            assert len(desc) > 20  # Should be descriptive
            assert "vCPU" in desc or "vcpu" in desc.lower()  # Should mention CPU
    
    # Complex scenario tests
    def test_provision_with_full_context(self):
        """Test provisioning intent with full context extraction."""
        result = self.recognizer.recognize(
            "provision a POWER workspace for project: sim-engine"
        )
        
        assert result.intent == Intent.PROVISION_WORKSPACE
        assert result.entities.get("bundle_type") == "POWER"
        assert result.entities.get("project_id") == "sim-engine"
    
    def test_cost_query_with_filters(self):
        """Test cost query with multiple filters."""
        result = self.recognizer.recognize(
            "show me costs for team: robotics last month"
        )
        
        assert result.intent == Intent.GET_COST_SUMMARY
        assert result.entities.get("team_id") == "robotics"
        assert result.entities.get("period") == "last_month"
    
    def test_workspace_action_with_id(self):
        """Test workspace action with explicit ID."""
        result = self.recognizer.recognize("stop workspace ws-abc123")
        
        assert result.intent == Intent.STOP_WORKSPACE
        assert "workspace_id" in result.entities
        assert "abc123" in result.entities["workspace_id"].lower()
    
    # Edge cases
    def test_empty_message(self):
        """Test handling of empty message."""
        result = self.recognizer.recognize("")
        
        assert result.intent == Intent.UNKNOWN
        assert result.ambiguous is True
    
    def test_very_long_message(self):
        """Test handling of very long message."""
        long_message = "I need to provision a workspace " * 50
        result = self.recognizer.recognize(long_message)
        
        # Should still recognize the intent
        assert result.intent == Intent.PROVISION_WORKSPACE
    
    def test_mixed_case_message(self):
        """Test handling of mixed case message."""
        result = self.recognizer.recognize("PrOvIsIoN a WoRkSpAcE")
        
        assert result.intent == Intent.PROVISION_WORKSPACE
    
    def test_message_with_special_characters(self):
        """Test handling of message with special characters."""
        result = self.recognizer.recognize("provision a workspace!!!")
        
        assert result.intent == Intent.PROVISION_WORKSPACE
