"""Lucy AI chat API endpoints.

Provides REST API for interacting with Lucy AI assistant.
Requirements: 5.2
"""

from typing import Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, Field
import logging

from ..lucy.context_manager import ConversationContext, get_conversation_context, save_conversation_context, clear_conversation_context
from ..lucy.intent_recognizer import IntentRecognizer
from ..lucy.audit import log_lucy_query, log_lucy_conversation_start, log_lucy_conversation_end

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/lucy", tags=["lucy"])


# Request/Response Models

class ChatMessage(BaseModel):
    """Chat message from user to Lucy."""
    message: str = Field(..., description="User message to Lucy", min_length=1, max_length=5000)
    conversation_id: Optional[str] = Field(None, description="Optional conversation ID to continue existing conversation")


class ChatResponse(BaseModel):
    """Response from Lucy to user."""
    message: str = Field(..., description="Lucy's response message")
    conversation_id: str = Field(..., description="Conversation ID for context tracking")
    intent: Optional[str] = Field(None, description="Recognized intent from user message")
    tool_executed: Optional[str] = Field(None, description="Tool that was executed (if any)")
    tool_result: Optional[Dict[str, Any]] = Field(None, description="Result from tool execution (if any)")
    requires_confirmation: bool = Field(False, description="Whether the action requires user confirmation")
    confirmation_message: Optional[str] = Field(None, description="Confirmation message to display to user")


class ContextResponse(BaseModel):
    """Conversation context response."""
    conversation_id: str = Field(..., description="Conversation ID")
    user_id: str = Field(..., description="User ID")
    message_count: int = Field(..., description="Number of messages in conversation")
    created_at: datetime = Field(..., description="When conversation started")
    last_activity: datetime = Field(..., description="Last activity timestamp")
    is_expired: bool = Field(..., description="Whether context has expired")


class ClearContextResponse(BaseModel):
    """Response for clearing context."""
    message: str = Field(..., description="Confirmation message")
    conversation_id: str = Field(..., description="Conversation ID that was cleared")


# Dependency for getting user ID from header
async def get_user_id(x_user_id: str = Header(..., alias="X-User-ID")) -> str:
    """Extract user ID from request header.
    
    Args:
        x_user_id: User ID from X-User-ID header
        
    Returns:
        User ID string
        
    Raises:
        HTTPException: If user ID is missing
    """
    if not x_user_id:
        raise HTTPException(status_code=401, detail="User ID required")
    return x_user_id


# Endpoints

@router.post("/chat", response_model=ChatResponse)
async def chat_with_lucy(
    request: ChatMessage,
    user_id: str = Depends(get_user_id),
    x_forwarded_for: Optional[str] = Header(None, alias="X-Forwarded-For"),
    user_agent: Optional[str] = Header(None, alias="User-Agent"),
) -> ChatResponse:
    """Send a message to Lucy AI assistant.
    
    Validates: Requirements 5.2
    
    This endpoint:
    1. Receives user message
    2. Recognizes intent
    3. Maintains conversation context
    4. Executes appropriate tools (if needed)
    5. Returns Lucy's response
    
    Args:
        request: Chat message request
        user_id: User ID from header
        x_forwarded_for: Source IP (optional)
        user_agent: User agent string (optional)
        
    Returns:
        Lucy's response with conversation context
        
    Raises:
        HTTPException: If message processing fails
    """
    try:
        # Get or create conversation context
        conversation_id = request.conversation_id
        if conversation_id:
            context = get_conversation_context(user_id, conversation_id)
            if not context:
                # Context expired or doesn't exist, create new one
                conversation_id = f"conv-{user_id}-{int(datetime.utcnow().timestamp())}"
                context = ConversationContext(
                    user_id=user_id,
                    session_id=conversation_id,
                    messages=[],
                    created_at=datetime.utcnow(),
                    last_activity=datetime.utcnow(),
                )
                log_lucy_conversation_start(
                    user_id=user_id,
                    conversation_id=conversation_id,
                    source_ip=x_forwarded_for,
                    user_agent=user_agent,
                )
        else:
            # Create new conversation
            conversation_id = f"conv-{user_id}-{int(datetime.utcnow().timestamp())}"
            context = ConversationContext(
                user_id=user_id,
                session_id=conversation_id,
                messages=[],
                created_at=datetime.utcnow(),
                last_activity=datetime.utcnow(),
            )
            log_lucy_conversation_start(
                user_id=user_id,
                conversation_id=conversation_id,
                source_ip=x_forwarded_for,
                user_agent=user_agent,
            )
        
        # Add user message to context
        context.add_message("user", request.message)
        
        # Recognize intent
        recognizer = IntentRecognizer()
        recognized_intent = recognizer.recognize(request.message)
        
        # Log the query
        log_lucy_query(
            user_id=user_id,
            query=request.message,
            intent=recognized_intent.intent.value if recognized_intent else None,
            source_ip=x_forwarded_for,
            user_agent=user_agent,
            conversation_id=conversation_id,
        )
        
        # TODO: In a full implementation, this would:
        # 1. Call Claude API with the message and context
        # 2. Execute any tools that Claude requests
        # 3. Get Claude's response
        # For now, we'll return a mock response based on intent
        
        response_message = _generate_mock_response(recognized_intent, request.message)
        
        # Add Lucy's response to context
        context.add_message("assistant", response_message)
        
        # Save updated context
        save_conversation_context(context)
        
        logger.info(
            f"lucy_chat_processed user_id={user_id} conversation_id={conversation_id} "
            f"intent={recognized_intent.intent.value if recognized_intent else 'unknown'}"
        )
        
        return ChatResponse(
            message=response_message,
            conversation_id=conversation_id,
            intent=recognized_intent.intent.value if recognized_intent else None,
            tool_executed=recognized_intent.tool_name if recognized_intent else None,
            tool_result=None,  # Would be populated by actual tool execution
            requires_confirmation=recognized_intent.ambiguous if recognized_intent else False,
            confirmation_message=recognized_intent.clarification_needed if recognized_intent else None,
        )
        
    except Exception as e:
        logger.error(f"Failed to process Lucy chat: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process message: {str(e)}"
        )


@router.get("/context", response_model=ContextResponse)
async def get_context(
    conversation_id: str,
    user_id: str = Depends(get_user_id),
) -> ContextResponse:
    """Get conversation context for a specific conversation.
    
    Validates: Requirements 5.2
    
    Args:
        conversation_id: Conversation ID to retrieve
        user_id: User ID from header
        
    Returns:
        Conversation context details
        
    Raises:
        HTTPException: If context not found or expired
    """
    try:
        context = get_conversation_context(user_id, conversation_id)
        
        if not context:
            raise HTTPException(
                status_code=404,
                detail=f"Conversation {conversation_id} not found or expired"
            )
        
        # Check if context belongs to user
        if context.user_id != user_id:
            raise HTTPException(
                status_code=403,
                detail="Access denied: conversation belongs to another user"
            )
        
        return ContextResponse(
            conversation_id=context.session_id,
            user_id=context.user_id,
            message_count=len(context.messages),
            created_at=context.created_at,
            last_activity=context.last_activity,
            is_expired=context.is_expired(),
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get conversation context: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve context: {str(e)}"
        )


@router.delete("/context", response_model=ClearContextResponse)
async def clear_context(
    conversation_id: str,
    user_id: str = Depends(get_user_id),
    x_forwarded_for: Optional[str] = Header(None, alias="X-Forwarded-For"),
    user_agent: Optional[str] = Header(None, alias="User-Agent"),
) -> ClearContextResponse:
    """Clear conversation context for a specific conversation.
    
    Validates: Requirements 5.2
    
    Args:
        conversation_id: Conversation ID to clear
        user_id: User ID from header
        x_forwarded_for: Source IP (optional)
        user_agent: User agent string (optional)
        
    Returns:
        Confirmation of context clearing
        
    Raises:
        HTTPException: If context not found or access denied
    """
    try:
        # Get context to verify ownership and get stats
        context = get_conversation_context(user_id, conversation_id)
        
        if not context:
            raise HTTPException(
                status_code=404,
                detail=f"Conversation {conversation_id} not found"
            )
        
        # Check if context belongs to user
        if context.user_id != user_id:
            raise HTTPException(
                status_code=403,
                detail="Access denied: conversation belongs to another user"
            )
        
        # Log conversation end before clearing
        message_count = len(context.messages)
        tool_executions = len([m for m in context.messages if m.get("role") == "tool"])
        
        log_lucy_conversation_end(
            user_id=user_id,
            conversation_id=conversation_id,
            message_count=message_count,
            tool_executions=tool_executions,
            source_ip=x_forwarded_for,
            user_agent=user_agent,
        )
        
        # Clear the context
        clear_conversation_context(user_id, conversation_id)
        
        logger.info(f"lucy_context_cleared user_id={user_id} conversation_id={conversation_id}")
        
        return ClearContextResponse(
            message=f"Conversation context cleared successfully",
            conversation_id=conversation_id,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to clear conversation context: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear context: {str(e)}"
        )


# Helper Functions

def _generate_mock_response(recognized_intent, user_message: str) -> str:
    """Generate a mock response based on recognized intent.
    
    This is a placeholder until full Claude integration is implemented.
    
    Args:
        recognized_intent: Recognized intent from user message
        user_message: Original user message
        
    Returns:
        Mock response string
    """
    from ..lucy.intent_recognizer import Intent
    
    if not recognized_intent or recognized_intent.intent == Intent.UNKNOWN:
        return "I'm not sure I understand. Could you rephrase your request? I can help you provision workspaces, check costs, run diagnostics, and more."
    
    intent = recognized_intent.intent
    
    # Generate response based on intent
    if intent == Intent.GREETING:
        return "Hi! I'm Lucy, your AI assistant for RobCo Forge. I can help you provision workspaces, manage costs, run diagnostics, and more. What can I help you with today?"
    
    elif intent == Intent.HELP:
        return """I can help you with:
- Provisioning and managing workspaces
- Checking costs and budget status
- Getting cost optimization recommendations
- Running diagnostics on workspaces
- Creating support tickets

Just ask me in natural language, like "I need a GPU workspace" or "What are my costs this month?"
"""
    
    elif intent == Intent.PROVISION_WORKSPACE:
        if recognized_intent.clarification_needed:
            return recognized_intent.clarification_needed
        bundle = recognized_intent.entities.get("bundle_type", "PERFORMANCE")
        return f"I can help you provision a {bundle} workspace. To proceed, I'll need to check your budget and permissions. Would you like me to continue?"
    
    elif intent == Intent.RECOMMEND_BUNDLE:
        requirements = recognized_intent.entities.get("requirements", {})
        from ..lucy.intent_recognizer import IntentRecognizer
        recognizer = IntentRecognizer()
        recommendations = recognizer.recommend_bundle(requirements)
        
        if recommendations:
            response = "Based on your requirements, I recommend:\n\n"
            for i, bundle in enumerate(recommendations, 1):
                desc = recognizer.get_bundle_description(bundle)
                response += f"{i}. {desc}\n"
            response += "\nWould you like me to provision one of these?"
            return response
        else:
            return "I'd recommend a PERFORMANCE bundle for most development workloads. Would you like me to provision one?"
    
    elif intent == Intent.LIST_WORKSPACES:
        return "I can show you your workspaces. Let me fetch that information for you..."
    
    elif intent in [Intent.START_WORKSPACE, Intent.STOP_WORKSPACE, Intent.TERMINATE_WORKSPACE]:
        if recognized_intent.clarification_needed:
            return recognized_intent.clarification_needed
        workspace_id = recognized_intent.entities.get("workspace_id", "your workspace")
        action = intent.value.replace("_", " ")
        return f"I can {action} {workspace_id}. Would you like me to proceed?"
    
    elif intent == Intent.GET_COST_SUMMARY:
        period = recognized_intent.entities.get("period", "this month")
        return f"Let me get your cost summary for {period}..."
    
    elif intent == Intent.GET_COST_RECOMMENDATIONS:
        return "I'll analyze your workspace usage and provide cost optimization recommendations..."
    
    elif intent == Intent.CHECK_BUDGET:
        return "Let me check your current budget status..."
    
    elif intent == Intent.RUN_DIAGNOSTICS:
        if recognized_intent.clarification_needed:
            return recognized_intent.clarification_needed
        return "I'll run diagnostics on your workspace and report any issues..."
    
    elif intent == Intent.CREATE_SUPPORT_TICKET:
        return "I can create a support ticket for you. What issue would you like to report?"
    
    else:
        return f"I understand you want to {intent.value.replace('_', ' ')}. Let me help you with that..."
