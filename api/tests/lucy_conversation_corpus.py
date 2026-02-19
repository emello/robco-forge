"""Conversation corpus for Lucy AI testing.

This corpus contains test cases for evaluating Lucy's intent recognition,
tool selection, and response quality across various scenarios.

Requirements: 5.3, 5.4, 5.5, 5.6
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class ConversationTestCase:
    """A single test case for Lucy conversation evaluation.
    
    Attributes:
        id: Unique identifier for the test case
        category: Category of the test (provisioning, cost, error, rbac)
        user_message: The user's input message
        expected_intent: The intent Lucy should recognize
        expected_tool: The tool Lucy should select (if applicable)
        expected_entities: Entities Lucy should extract
        description: Human-readable description of what's being tested
        should_succeed: Whether the request should succeed
        expected_error: Expected error message (if should_succeed=False)
    """
    id: str
    category: str
    user_message: str
    expected_intent: str
    expected_tool: Optional[str]
    expected_entities: Dict[str, Any]
    description: str
    should_succeed: bool = True
    expected_error: Optional[str] = None


# Provisioning Request Test Cases
PROVISIONING_CASES = [
    ConversationTestCase(
        id="prov_001",
        category="provisioning",
        user_message="I need a GPU workspace for machine learning",
        expected_intent="recommend_bundle",
        expected_tool=None,
        expected_entities={"requirements": ["gpu", "ml"]},
        description="Request for GPU workspace with ML requirements"
    ),
    ConversationTestCase(
        id="prov_002",
        category="provisioning",
        user_message="Launch a standard workspace with Windows",
        expected_intent="provision_workspace",
        expected_tool="provision_workspace",
        expected_entities={"bundle_type": "STANDARD", "os": "Windows"},
        description="Direct provisioning request with bundle and OS"
    ),
    ConversationTestCase(
        id="prov_003",
        category="provisioning",
        user_message="Can you provision a Performance bundle for me?",
        expected_intent="provision_workspace",
        expected_tool="provision_workspace",
        expected_entities={"bundle_type": "PERFORMANCE"},
        description="Provisioning request with specific bundle type"
    ),
    ConversationTestCase(
        id="prov_004",
        category="provisioning",
        user_message="I need a workspace for running simulations",
        expected_intent="recommend_bundle",
        expected_tool=None,
        expected_entities={"requirements": ["simulation"]},
        description="Provisioning request requiring bundle recommendation"
    ),
    ConversationTestCase(
        id="prov_005",
        category="provisioning",
        user_message="Create a Power workspace with the data-science blueprint",
        expected_intent="provision_workspace",
        expected_tool="provision_workspace",
        expected_entities={"bundle_type": "POWER", "blueprint": "data-science"},
        description="Provisioning with bundle and blueprint specified"
    ),
    ConversationTestCase(
        id="prov_006",
        category="provisioning",
        user_message="I need a Linux workspace for development",
        expected_intent="provision_workspace",
        expected_tool="provision_workspace",
        expected_entities={"os": "Linux"},
        description="Provisioning request with OS but no bundle"
    ),
    ConversationTestCase(
        id="prov_007",
        category="provisioning",
        user_message="What workspace should I use for AI training?",
        expected_intent="recommend_bundle",
        expected_tool=None,
        expected_entities={"requirements": ["ai"]},
        description="Bundle recommendation for AI workload"
    ),
    ConversationTestCase(
        id="prov_008",
        category="provisioning",
        user_message="Launch a GraphicsPro workspace in us-west-2",
        expected_intent="provision_workspace",
        expected_tool="provision_workspace",
        expected_entities={"bundle_type": "GRAPHICSPRO_G4DN", "region": "us-west-2"},
        description="Provisioning with bundle and region specified"
    ),
]

# Workspace Management Test Cases
MANAGEMENT_CASES = [
    ConversationTestCase(
        id="mgmt_001",
        category="management",
        user_message="Show me my workspaces",
        expected_intent="list_workspaces",
        expected_tool="list_workspaces",
        expected_entities={},
        description="List all user workspaces"
    ),
    ConversationTestCase(
        id="mgmt_002",
        category="management",
        user_message="Start workspace ws-abc123",
        expected_intent="start_workspace",
        expected_tool="start_workspace",
        expected_entities={"workspace_id": "ws-abc123"},
        description="Start specific workspace by ID"
    ),
    ConversationTestCase(
        id="mgmt_003",
        category="management",
        user_message="Stop my GPU workspace",
        expected_intent="stop_workspace",
        expected_tool="stop_workspace",
        expected_entities={"bundle_type": "gpu"},
        description="Stop workspace by bundle type description"
    ),
    ConversationTestCase(
        id="mgmt_004",
        category="management",
        user_message="Terminate workspace ws-xyz789",
        expected_intent="terminate_workspace",
        expected_tool="terminate_workspace",
        expected_entities={"workspace_id": "ws-xyz789"},
        description="Terminate specific workspace"
    ),
    ConversationTestCase(
        id="mgmt_005",
        category="management",
        user_message="What's the status of my workspaces?",
        expected_intent="get_workspace_status",
        expected_tool="list_workspaces",
        expected_entities={},
        description="Check workspace status"
    ),
    ConversationTestCase(
        id="mgmt_006",
        category="management",
        user_message="List all my running workspaces",
        expected_intent="list_workspaces",
        expected_tool="list_workspaces",
        expected_entities={"status": "running"},
        description="List workspaces filtered by status"
    ),
]

# Cost Query Test Cases
COST_CASES = [
    ConversationTestCase(
        id="cost_001",
        category="cost",
        user_message="How much am I spending this month?",
        expected_intent="get_cost_summary",
        expected_tool="get_cost_summary",
        expected_entities={"time_period": "month"},
        description="Get monthly cost summary"
    ),
    ConversationTestCase(
        id="cost_002",
        category="cost",
        user_message="Show me cost recommendations",
        expected_intent="get_cost_recommendations",
        expected_tool="get_cost_recommendations",
        expected_entities={},
        description="Get cost optimization recommendations"
    ),
    ConversationTestCase(
        id="cost_003",
        category="cost",
        user_message="What's my team's budget status?",
        expected_intent="check_budget",
        expected_tool="check_budget",
        expected_entities={"scope": "team"},
        description="Check team budget"
    ),
    ConversationTestCase(
        id="cost_004",
        category="cost",
        user_message="How much did I spend last week?",
        expected_intent="get_cost_summary",
        expected_tool="get_cost_summary",
        expected_entities={"time_period": "week"},
        description="Get weekly cost summary"
    ),
    ConversationTestCase(
        id="cost_005",
        category="cost",
        user_message="What are my workspace costs by project?",
        expected_intent="get_cost_summary",
        expected_tool="get_cost_summary",
        expected_entities={"group_by": "project"},
        description="Get costs grouped by project"
    ),
    ConversationTestCase(
        id="cost_006",
        category="cost",
        user_message="Am I close to my budget limit?",
        expected_intent="check_budget",
        expected_tool="check_budget",
        expected_entities={},
        description="Check personal budget status"
    ),
    ConversationTestCase(
        id="cost_007",
        category="cost",
        user_message="Can I save money on my workspaces?",
        expected_intent="get_cost_recommendations",
        expected_tool="get_cost_recommendations",
        expected_entities={},
        description="Request cost savings recommendations"
    ),
]

# Diagnostics Test Cases
DIAGNOSTICS_CASES = [
    ConversationTestCase(
        id="diag_001",
        category="diagnostics",
        user_message="Run diagnostics on workspace ws-abc123",
        expected_intent="run_diagnostics",
        expected_tool="run_diagnostics",
        expected_entities={"workspace_id": "ws-abc123"},
        description="Run diagnostics on specific workspace"
    ),
    ConversationTestCase(
        id="diag_002",
        category="diagnostics",
        user_message="My workspace is slow, can you check it?",
        expected_intent="troubleshoot",
        expected_tool="run_diagnostics",
        expected_entities={"issue": "slow"},
        description="Troubleshoot performance issue"
    ),
    ConversationTestCase(
        id="diag_003",
        category="diagnostics",
        user_message="Why can't I connect to my workspace?",
        expected_intent="troubleshoot",
        expected_tool="run_diagnostics",
        expected_entities={"issue": "connection"},
        description="Troubleshoot connection issue"
    ),
]

# Error Scenario Test Cases
ERROR_CASES = [
    ConversationTestCase(
        id="err_001",
        category="error",
        user_message="Launch a workspace",
        expected_intent="provision_workspace",
        expected_tool="provision_workspace",
        expected_entities={},
        description="Ambiguous provisioning request - missing bundle type",
        should_succeed=False,
        expected_error="clarification_needed"
    ),
    ConversationTestCase(
        id="err_002",
        category="error",
        user_message="Stop workspace",
        expected_intent="stop_workspace",
        expected_tool="stop_workspace",
        expected_entities={},
        description="Missing workspace identifier",
        should_succeed=False,
        expected_error="missing_workspace_id"
    ),
    ConversationTestCase(
        id="err_003",
        category="error",
        user_message="Start workspace ws-invalid-id",
        expected_intent="start_workspace",
        expected_tool="start_workspace",
        expected_entities={"workspace_id": "ws-invalid-id"},
        description="Invalid workspace ID format",
        should_succeed=False,
        expected_error="invalid_workspace_id"
    ),
    ConversationTestCase(
        id="err_004",
        category="error",
        user_message="Give me a super ultra mega powerful workspace",
        expected_intent="recommend_bundle",
        expected_tool=None,
        expected_entities={"requirements": ["powerful"]},
        description="Vague requirements needing clarification"
    ),
    ConversationTestCase(
        id="err_005",
        category="error",
        user_message="What's the weather like?",
        expected_intent="unknown",
        expected_tool=None,
        expected_entities={},
        description="Out of scope request",
        should_succeed=False,
        expected_error="out_of_scope"
    ),
]

# RBAC Denial Test Cases
RBAC_CASES = [
    ConversationTestCase(
        id="rbac_001",
        category="rbac",
        user_message="Launch a PowerPro workspace",
        expected_intent="provision_workspace",
        expected_tool="provision_workspace",
        expected_entities={"bundle_type": "POWERPRO"},
        description="Contractor requesting restricted bundle",
        should_succeed=False,
        expected_error="rbac_denied"
    ),
    ConversationTestCase(
        id="rbac_002",
        category="rbac",
        user_message="Terminate workspace ws-other-user-123",
        expected_intent="terminate_workspace",
        expected_tool="terminate_workspace",
        expected_entities={"workspace_id": "ws-other-user-123"},
        description="User attempting to terminate another user's workspace",
        should_succeed=False,
        expected_error="rbac_denied"
    ),
    ConversationTestCase(
        id="rbac_003",
        category="rbac",
        user_message="Show me all team workspaces",
        expected_intent="list_workspaces",
        expected_tool="list_workspaces",
        expected_entities={"scope": "team"},
        description="Non-team-lead requesting team-wide view",
        should_succeed=False,
        expected_error="rbac_denied"
    ),
]

# Budget Denial Test Cases
BUDGET_CASES = [
    ConversationTestCase(
        id="budget_001",
        category="budget",
        user_message="Launch a Graphics workspace",
        expected_intent="provision_workspace",
        expected_tool="provision_workspace",
        expected_entities={"bundle_type": "GRAPHICS_G4DN"},
        description="Provisioning request exceeding budget",
        should_succeed=False,
        expected_error="budget_exceeded"
    ),
    ConversationTestCase(
        id="budget_002",
        category="budget",
        user_message="Create 5 Power workspaces",
        expected_intent="provision_workspace",
        expected_tool="provision_workspace",
        expected_entities={"bundle_type": "POWER", "count": 5},
        description="Bulk provisioning exceeding budget",
        should_succeed=False,
        expected_error="budget_exceeded"
    ),
]

# Support and Routing Test Cases
SUPPORT_CASES = [
    ConversationTestCase(
        id="support_001",
        category="support",
        user_message="I need help with my workspace configuration",
        expected_intent="create_support_ticket",
        expected_tool="create_support_ticket",
        expected_entities={"issue_type": "configuration"},
        description="Request for support ticket creation"
    ),
    ConversationTestCase(
        id="support_002",
        category="support",
        user_message="Can I get access to the production blueprint?",
        expected_intent="request_approval",
        expected_tool="create_support_ticket",
        expected_entities={"request_type": "access"},
        description="Request requiring approval workflow"
    ),
]

# General Conversation Test Cases
GENERAL_CASES = [
    ConversationTestCase(
        id="gen_001",
        category="general",
        user_message="Hello Lucy",
        expected_intent="greeting",
        expected_tool=None,
        expected_entities={},
        description="Greeting message"
    ),
    ConversationTestCase(
        id="gen_002",
        category="general",
        user_message="What can you help me with?",
        expected_intent="help",
        expected_tool=None,
        expected_entities={},
        description="Help request"
    ),
    ConversationTestCase(
        id="gen_003",
        category="general",
        user_message="Thanks for your help!",
        expected_intent="greeting",
        expected_tool=None,
        expected_entities={},
        description="Thank you message"
    ),
]

# Complete corpus
CONVERSATION_CORPUS = (
    PROVISIONING_CASES +
    MANAGEMENT_CASES +
    COST_CASES +
    DIAGNOSTICS_CASES +
    ERROR_CASES +
    RBAC_CASES +
    BUDGET_CASES +
    SUPPORT_CASES +
    GENERAL_CASES
)


def get_test_cases_by_category(category: str) -> List[ConversationTestCase]:
    """Get all test cases for a specific category.
    
    Args:
        category: Category name (provisioning, cost, error, rbac, etc.)
        
    Returns:
        List of test cases in that category
    """
    return [case for case in CONVERSATION_CORPUS if case.category == category]


def get_test_case_by_id(test_id: str) -> Optional[ConversationTestCase]:
    """Get a specific test case by ID.
    
    Args:
        test_id: Test case ID
        
    Returns:
        Test case if found, None otherwise
    """
    for case in CONVERSATION_CORPUS:
        if case.id == test_id:
            return case
    return None


def get_all_categories() -> List[str]:
    """Get list of all test case categories.
    
    Returns:
        List of unique category names
    """
    return list(set(case.category for case in CONVERSATION_CORPUS))
