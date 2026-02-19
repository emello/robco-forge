"""Intent recognition for Lucy AI service.

Parses user requests to identify intent and map to appropriate tools.
Requirements: 5.3, 5.4, 5.5
"""

from typing import Dict, Any, Optional, List, Tuple
from enum import Enum
import re
from dataclasses import dataclass


class Intent(str, Enum):
    """Recognized user intents.
    
    Maps to Lucy's capabilities as defined in Requirements 5.3-5.8.
    """
    # Workspace provisioning intents (Req 5.4)
    PROVISION_WORKSPACE = "provision_workspace"
    RECOMMEND_BUNDLE = "recommend_bundle"
    
    # Workspace management intents (Req 5.5)
    LIST_WORKSPACES = "list_workspaces"
    START_WORKSPACE = "start_workspace"
    STOP_WORKSPACE = "stop_workspace"
    TERMINATE_WORKSPACE = "terminate_workspace"
    GET_WORKSPACE_STATUS = "get_workspace_status"
    
    # Cost query intents (Req 5.6)
    GET_COST_SUMMARY = "get_cost_summary"
    GET_COST_RECOMMENDATIONS = "get_cost_recommendations"
    CHECK_BUDGET = "check_budget"
    
    # Diagnostics intents (Req 5.7)
    RUN_DIAGNOSTICS = "run_diagnostics"
    TROUBLESHOOT = "troubleshoot"
    
    # Support intents (Req 5.8)
    CREATE_SUPPORT_TICKET = "create_support_ticket"
    REQUEST_APPROVAL = "request_approval"
    
    # General intents
    GREETING = "greeting"
    HELP = "help"
    UNKNOWN = "unknown"


@dataclass
class RecognizedIntent:
    """Result of intent recognition.
    
    Attributes:
        intent: The recognized intent
        confidence: Confidence score (0.0 to 1.0)
        entities: Extracted entities from the request
        tool_name: Suggested tool to execute (if applicable)
        ambiguous: Whether the intent is ambiguous
        clarification_needed: What clarification is needed (if ambiguous)
    """
    intent: Intent
    confidence: float
    entities: Dict[str, Any]
    tool_name: Optional[str] = None
    ambiguous: bool = False
    clarification_needed: Optional[str] = None


class IntentRecognizer:
    """Recognizes user intent from natural language requests.
    
    Validates:
    - Requirements 5.3: Intent recognition for recommendations
    - Requirements 5.4: Intent recognition for provisioning
    - Requirements 5.5: Intent recognition for workspace management
    
    Uses pattern matching and keyword analysis to identify user intent.
    In production, could be enhanced with:
    - Claude's native understanding (let Claude identify intent)
    - Fine-tuned classification model
    - Semantic similarity matching
    """
    
    def __init__(self):
        """Initialize intent recognizer with pattern definitions."""
        # Intent patterns: (intent, patterns, tool_name)
        self.patterns = self._build_patterns()
        
        # Bundle type keywords for recommendations
        self.bundle_keywords = {
            "gpu": ["GRAPHICS_G4DN", "GRAPHICSPRO_G4DN"],
            "graphics": ["GRAPHICS_G4DN", "GRAPHICSPRO_G4DN"],
            "simulation": ["GRAPHICS_G4DN", "GRAPHICSPRO_G4DN"],
            "ml": ["GRAPHICS_G4DN", "POWER", "POWERPRO"],
            "machine learning": ["GRAPHICS_G4DN", "POWER", "POWERPRO"],
            "ai": ["GRAPHICS_G4DN", "POWER", "POWERPRO"],
            "heavy": ["POWER", "POWERPRO"],
            "intensive": ["POWER", "POWERPRO"],
            "light": ["STANDARD"],
            "basic": ["STANDARD"],
            "standard": ["STANDARD"],
            "medium": ["PERFORMANCE"],
            "moderate": ["PERFORMANCE"]
        }
    
    def _build_patterns(self) -> List[Tuple[Intent, List[str], Optional[str]]]:
        """Build intent recognition patterns.
        
        Returns:
            List of (intent, patterns, tool_name) tuples
        """
        return [
            # Greeting patterns (check first - very specific)
            (Intent.GREETING, [
                r"^(hi|hello|hey|greetings)(\s|$)",
            ], None),
            
            # Help patterns (check early)
            (Intent.HELP, [
                r"^(help|what can you do|capabilities|commands)(\s|$)",
                r"^how\s+(do i|can i|to)(?!.*(workspace|workstation|desktop))",
            ], None),
            
            # Start workspace patterns (more specific than provision)
            (Intent.START_WORKSPACE, [
                r"\b(start|boot|power on|turn on|wake)\s*(workspace|workstation|desktop|ws-|workspace-)",
                r"\b(start|resume)\s+(ws-|workspace-)[a-zA-Z0-9]+\b",
            ], "start_workspace"),
            
            # Stop workspace patterns (more specific than provision)
            (Intent.STOP_WORKSPACE, [
                r"\b(stop|shutdown|power off|turn off|pause)\s*(workspace|workstation|desktop|ws-|workspace-)",
                r"\b(stop|halt)\s+(ws-|workspace-)[a-zA-Z0-9]+\b",
            ], "stop_workspace"),
            
            # Terminate workspace patterns
            (Intent.TERMINATE_WORKSPACE, [
                r"\b(terminate|delete|destroy|remove)\s*(workspace|workstation|desktop|ws-|workspace-)",
                r"\b(terminate|delete)\s+(ws-|workspace-)[a-zA-Z0-9]+\b",
            ], "terminate_workspace"),
            
            # Get workspace status patterns
            (Intent.GET_WORKSPACE_STATUS, [
                r"\b(status|state|info|details|describe)\s+(of\s+)?(my\s+)?(workspace|workstation|desktop)\b",
                r"\bwhat.*(status|state).*(workspace|workstation|desktop)\b",
                r"\b(check|show)\s+(ws-|workspace-)[a-zA-Z0-9]+\s+(status|state|info)\b",
            ], "list_workspaces"),
            
            # Provision workspace patterns (check after start/stop/terminate)
            (Intent.PROVISION_WORKSPACE, [
                r"\b(provision|create|launch|spin up)\s*(a\s+|an\s+)?(workspace|workstation|desktop|machine|environment)\b",
                r"\b(get me|give me|set up)\s*(a\s+|an\s+)?(workspace|workstation|desktop)\b",
                r"\bi need\s+(a|an)\s+(workspace|workstation|desktop)\b",
            ], "provision_workspace"),
            
            # Recommend bundle patterns (Req 5.3)
            (Intent.RECOMMEND_BUNDLE, [
                r"\b(recommend|suggest|which|what)\s*(bundle|configuration|spec|hardware)\b",
                r"\bwhat\s+(bundle|configuration|spec).*(should|do|need)\b",
                r"\b(best|right|appropriate)\s*(bundle|configuration)\b",
                r"\bhelp me\s+(choose|pick|select)\s*(bundle|configuration)\b",
            ], None),
            
            # List workspaces patterns (Req 5.5)
            (Intent.LIST_WORKSPACES, [
                r"\b(list|show|display|get|view)\s*(my\s+)?(workspace|workstation|desktop)s?\b",
                r"\bwhat\s+(workspace|workstation|desktop)s?\s+(do i have|are running)\b",
                r"\b(my|all)\s+(workspace|workstation|desktop)s?\b",
            ], "list_workspaces"),
            
            # Cost summary patterns (Req 5.6) - more specific
            (Intent.GET_COST_SUMMARY, [
                r"\b(cost|spend|spending|expense|bill|billing)s?\b",
                r"\bhow much.*(cost|spend|spent|pay|paying)\b",
                r"\b(show|get|view)\s*(my\s+)?(cost|spend|spending|expense)s?\b",
                r"\bwhat.*(cost|spend|spending)\b",
            ], "get_cost_summary"),
            
            # Cost recommendations patterns (Req 5.6)
            (Intent.GET_COST_RECOMMENDATIONS, [
                r"\b(cost\s+)?(optimization|optimize|save|saving|reduce|reducing)\b",
                r"\b(recommend|suggest).*(cost|save|saving)\b",
                r"\bhow\s+(can i|to)\s+(save|reduce).*(cost|money)\b",
            ], "get_cost_recommendations"),
            
            # Budget check patterns (Req 5.6)
            (Intent.CHECK_BUDGET, [
                r"\b(budget|quota|limit|allowance)\b",
                r"\bhow much.*(budget|quota|left|remaining)\b",
                r"\b(check|show|view).*(budget|quota)\b",
            ], "check_budget"),
            
            # Diagnostics patterns (Req 5.7)
            (Intent.RUN_DIAGNOSTICS, [
                r"\b(diagnose|diagnostic)\s*(workspace|workstation|desktop)\b",
                r"\b(run|perform).*(diagnostic|check|test)\b",
                r"\bwhat.*(wrong|problem|issue).*(workspace|workstation|desktop)\b",
                r"\b(check|test)\s+(workspace|workstation|desktop)\b",
            ], "run_diagnostics"),
            
            # Troubleshoot patterns (Req 5.7)
            (Intent.TROUBLESHOOT, [
                r"\b(not working|broken|issue|problem|error|fail)\b",
                r"\bcan'?t\s+(connect|access|start|use)\b",
                r"\b(slow|laggy|unresponsive)\b",
            ], "run_diagnostics"),
            
            # Support ticket patterns (Req 5.8) - check after help
            (Intent.CREATE_SUPPORT_TICKET, [
                r"\b(support|ticket|escalate)\b",
                r"\b(talk to|speak to|reach)\s+(human|person|support|admin)\b",
                r"\bneed\s+(help|assistance)\s+(from|with)\b",
                r"\bcreate\s+(a\s+)?support\s+ticket\b",
            ], "create_support_ticket"),
        ]
    
    def recognize(self, user_message: str) -> RecognizedIntent:
        """Recognize intent from user message.
        
        Validates: Requirements 5.3, 5.4, 5.5
        
        Args:
            user_message: User's natural language request
            
        Returns:
            RecognizedIntent with identified intent and extracted entities
        """
        message_lower = user_message.lower()
        
        # Try to match patterns
        matches = []
        for intent, patterns, tool_name in self.patterns:
            for pattern in patterns:
                if re.search(pattern, message_lower, re.IGNORECASE):
                    matches.append((intent, tool_name, self._calculate_confidence(pattern, message_lower)))
                    break
        
        # If no matches, return unknown intent
        if not matches:
            return RecognizedIntent(
                intent=Intent.UNKNOWN,
                confidence=0.0,
                entities={},
                ambiguous=True,
                clarification_needed="I'm not sure what you're asking for. Could you rephrase your request?"
            )
        
        # Sort by confidence and get best match
        matches.sort(key=lambda x: x[2], reverse=True)
        best_intent, tool_name, confidence = matches[0]
        
        # Check for ambiguity (multiple high-confidence matches)
        if len(matches) > 1 and matches[1][2] > 0.7:
            return self._handle_ambiguous_intent(matches, user_message)
        
        # Extract entities based on intent
        entities = self._extract_entities(best_intent, user_message)
        
        # Check if we need clarification
        clarification = self._check_clarification_needed(best_intent, entities)
        
        return RecognizedIntent(
            intent=best_intent,
            confidence=confidence,
            entities=entities,
            tool_name=tool_name,
            ambiguous=clarification is not None,
            clarification_needed=clarification
        )
    
    def _calculate_confidence(self, pattern: str, message: str) -> float:
        """Calculate confidence score for a pattern match.
        
        Args:
            pattern: Regex pattern that matched
            message: User message
            
        Returns:
            Confidence score (0.0 to 1.0)
        """
        # Base confidence for any match
        confidence = 0.8
        
        # Increase confidence for exact matches
        if re.fullmatch(pattern, message, re.IGNORECASE):
            confidence = 1.0
        
        # Increase confidence for longer patterns (more specific)
        if len(pattern) > 50:
            confidence = min(1.0, confidence + 0.1)
        
        return confidence
    
    def _handle_ambiguous_intent(
        self,
        matches: List[Tuple[Intent, Optional[str], float]],
        user_message: str
    ) -> RecognizedIntent:
        """Handle ambiguous intent with multiple high-confidence matches.
        
        Args:
            matches: List of (intent, tool_name, confidence) tuples
            user_message: Original user message
            
        Returns:
            RecognizedIntent with ambiguity information
        """
        # Get top 2 intents
        intent1, tool1, conf1 = matches[0]
        intent2, tool2, conf2 = matches[1]
        
        # Build clarification message
        clarification = (
            f"I'm not sure if you want to {intent1.value.replace('_', ' ')} "
            f"or {intent2.value.replace('_', ' ')}. Could you clarify?"
        )
        
        return RecognizedIntent(
            intent=intent1,  # Use best match as default
            confidence=conf1,
            entities={},
            tool_name=tool1,
            ambiguous=True,
            clarification_needed=clarification
        )
    
    def _extract_entities(self, intent: Intent, message: str) -> Dict[str, Any]:
        """Extract entities from message based on intent.
        
        Args:
            intent: Recognized intent
            message: User message
            
        Returns:
            Dictionary of extracted entities
        """
        entities = {}
        message_lower = message.lower()
        
        # Extract workspace ID if present - improved regex
        workspace_id_match = re.search(r'\b(ws-|workspace-)([a-zA-Z0-9]+)\b', message, re.IGNORECASE)
        if workspace_id_match:
            entities["workspace_id"] = workspace_id_match.group(0)
        
        # Extract bundle type if mentioned
        bundle_types = ["STANDARD", "PERFORMANCE", "POWER", "POWERPRO", "GRAPHICS_G4DN", "GRAPHICSPRO_G4DN"]
        for bundle in bundle_types:
            if bundle.lower() in message_lower or bundle.replace("_", " ").lower() in message_lower:
                entities["bundle_type"] = bundle
                break
        
        # Extract bundle requirements for recommendations
        if intent == Intent.RECOMMEND_BUNDLE:
            entities["requirements"] = self._extract_bundle_requirements(message_lower)
        
        # Extract time period for cost queries
        if intent in [Intent.GET_COST_SUMMARY, Intent.CHECK_BUDGET]:
            period = self._extract_time_period(message_lower)
            if period:
                entities["period"] = period
        
        # Extract team/project identifiers
        team_match = re.search(r'\bteam[:\s]+([a-zA-Z0-9-]+)\b', message_lower)
        if team_match:
            entities["team_id"] = team_match.group(1)
        
        project_match = re.search(r'\bproject[:\s]+([a-zA-Z0-9-]+)\b', message_lower)
        if project_match:
            entities["project_id"] = project_match.group(1)
        
        return entities
    
    def _extract_bundle_requirements(self, message: str) -> Dict[str, Any]:
        """Extract bundle requirements from message for recommendations.
        
        Validates: Requirements 5.3 (Bundle recommendations)
        
        Args:
            message: User message (lowercase)
            
        Returns:
            Dictionary of requirements
        """
        requirements = {}
        
        # Check for GPU/graphics needs
        if any(keyword in message for keyword in ["gpu", "graphics", "simulation", "rendering", "3d"]):
            requirements["needs_gpu"] = True
        
        # Check for ML/AI workloads
        if any(keyword in message for keyword in ["ml", "machine learning", "ai", "deep learning", "training"]):
            requirements["needs_high_compute"] = True
            requirements["workload_type"] = "ml"
        
        # Check for intensity keywords
        if any(keyword in message for keyword in ["heavy", "intensive", "demanding", "powerful"]):
            requirements["intensity"] = "high"
        elif any(keyword in message for keyword in ["light", "basic", "simple", "minimal"]):
            requirements["intensity"] = "low"
        else:
            requirements["intensity"] = "medium"
        
        # Check for specific use cases
        if any(keyword in message for keyword in ["web dev", "web development", "coding", "programming"]):
            requirements["use_case"] = "development"
        elif any(keyword in message for keyword in ["data", "analytics", "analysis"]):
            requirements["use_case"] = "data_analysis"
        elif any(keyword in message for keyword in ["design", "creative", "video"]):
            requirements["use_case"] = "creative"
        
        return requirements
    
    def _extract_time_period(self, message: str) -> Optional[str]:
        """Extract time period from message.
        
        Args:
            message: User message (lowercase)
            
        Returns:
            Time period string or None
        """
        if "this month" in message or "current month" in message:
            return "current_month"
        elif "last month" in message:
            return "last_month"
        elif "last 7 days" in message or "past week" in message:
            return "last_7_days"
        elif "last 30 days" in message or "past month" in message:
            return "last_30_days"
        elif "today" in message:
            return "today"
        elif "yesterday" in message:
            return "yesterday"
        
        return None
    
    def _check_clarification_needed(
        self,
        intent: Intent,
        entities: Dict[str, Any]
    ) -> Optional[str]:
        """Check if clarification is needed for the intent.
        
        Args:
            intent: Recognized intent
            entities: Extracted entities
            
        Returns:
            Clarification message or None
        """
        # Check if workspace-specific intents have workspace ID
        workspace_intents = [
            Intent.START_WORKSPACE,
            Intent.STOP_WORKSPACE,
            Intent.TERMINATE_WORKSPACE,
            Intent.RUN_DIAGNOSTICS
        ]
        
        if intent in workspace_intents and "workspace_id" not in entities:
            return "Which workspace would you like me to work with? Please provide the workspace ID."
        
        # Check if provision intent has bundle type
        if intent == Intent.PROVISION_WORKSPACE and "bundle_type" not in entities:
            return "What type of workspace do you need? (e.g., standard, performance, power, GPU)"
        
        return None
    
    def recommend_bundle(self, requirements: Dict[str, Any]) -> List[str]:
        """Recommend bundle types based on requirements.
        
        Validates: Requirements 5.3 (Bundle recommendations)
        
        Args:
            requirements: Dictionary of user requirements
            
        Returns:
            List of recommended bundle types (ordered by preference)
        """
        recommendations = []
        
        # GPU workloads
        if requirements.get("needs_gpu"):
            if requirements.get("intensity") == "high":
                recommendations.append("GRAPHICSPRO_G4DN")
                recommendations.append("GRAPHICS_G4DN")
            else:
                recommendations.append("GRAPHICS_G4DN")
        
        # High compute workloads (ML/AI)
        elif requirements.get("needs_high_compute"):
            recommendations.append("POWERPRO")
            recommendations.append("POWER")
            recommendations.append("GRAPHICS_G4DN")  # GPU can help with ML
        
        # Intensity-based recommendations
        elif requirements.get("intensity") == "high":
            recommendations.append("POWER")
            recommendations.append("POWERPRO")
        elif requirements.get("intensity") == "low":
            recommendations.append("STANDARD")
            recommendations.append("PERFORMANCE")
        else:  # medium intensity
            recommendations.append("PERFORMANCE")
            recommendations.append("POWER")
        
        # Use case specific recommendations
        use_case = requirements.get("use_case")
        if use_case == "development" and not recommendations:
            recommendations.append("PERFORMANCE")
            recommendations.append("STANDARD")
        elif use_case == "data_analysis" and not recommendations:
            recommendations.append("POWER")
            recommendations.append("PERFORMANCE")
        elif use_case == "creative" and not recommendations:
            recommendations.append("GRAPHICS_G4DN")
            recommendations.append("POWER")
        
        # Default recommendation if nothing matched
        if not recommendations:
            recommendations.append("PERFORMANCE")
            recommendations.append("STANDARD")
        
        # Remove duplicates while preserving order
        seen = set()
        unique_recommendations = []
        for bundle in recommendations:
            if bundle not in seen:
                seen.add(bundle)
                unique_recommendations.append(bundle)
        
        return unique_recommendations[:3]  # Return top 3 recommendations
    
    def get_bundle_description(self, bundle_type: str) -> str:
        """Get human-readable description of a bundle type.
        
        Args:
            bundle_type: Bundle type identifier
            
        Returns:
            Description string
        """
        descriptions = {
            "STANDARD": "Standard (2 vCPU, 8 GB RAM) - Good for light development and general tasks",
            "PERFORMANCE": "Performance (8 vCPU, 32 GB RAM) - Good for most development workloads",
            "POWER": "Power (16 vCPU, 64 GB RAM) - Good for intensive workloads and data processing",
            "POWERPRO": "PowerPro (32 vCPU, 128 GB RAM) - Best for very demanding workloads",
            "GRAPHICS_G4DN": "Graphics (16 vCPU, 64 GB RAM, NVIDIA T4 GPU) - Good for GPU workloads, ML, and graphics",
            "GRAPHICSPRO_G4DN": "GraphicsPro (64 vCPU, 256 GB RAM, NVIDIA T4 GPU) - Best for intensive GPU workloads"
        }
        
        return descriptions.get(bundle_type, bundle_type)
