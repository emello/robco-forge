"""Conversation context manager for Lucy AI service.

Manages conversation state with Redis storage and 30-minute TTL expiration.
Requirements: 6.1, 6.2
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import json
import redis
from pydantic import BaseModel


class Message(BaseModel):
    """A single message in a conversation."""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime


class ConversationContext(BaseModel):
    """Manages Lucy's conversation state.
    
    Stores conversation history, intent tracking, and workspace context
    with automatic 30-minute TTL expiration.
    """
    
    user_id: str
    session_id: str
    messages: List[Message] = []
    workspace_context: Optional[str] = None  # Current workspace being discussed
    intent_history: List[str] = []
    created_at: datetime
    last_activity: datetime
    ttl_seconds: int = 1800  # 30 minutes
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ConversationContextManager:
    """Manages conversation context storage and retrieval with Redis.
    
    Implements 30-minute TTL expiration and conversation history tracking.
    Requirements: 6.1, 6.2
    """
    
    def __init__(self, redis_client: redis.Redis, ttl_seconds: int = 1800):
        """Initialize context manager.
        
        Args:
            redis_client: Redis client instance
            ttl_seconds: Time-to-live in seconds (default: 1800 = 30 minutes)
        """
        self.redis = redis_client
        self.ttl_seconds = ttl_seconds
        self.key_prefix = "lucy:context:"
    
    def _get_key(self, user_id: str, session_id: str) -> str:
        """Generate Redis key for conversation context."""
        return f"{self.key_prefix}{user_id}:{session_id}"
    
    def create_context(
        self,
        user_id: str,
        session_id: str,
        workspace_context: Optional[str] = None
    ) -> ConversationContext:
        """Create a new conversation context.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            workspace_context: Optional workspace ID being discussed
            
        Returns:
            New ConversationContext instance
        """
        now = datetime.utcnow()
        context = ConversationContext(
            user_id=user_id,
            session_id=session_id,
            workspace_context=workspace_context,
            created_at=now,
            last_activity=now
        )
        
        # Store in Redis with TTL
        self._save_context(context)
        
        return context
    
    def get_context(
        self,
        user_id: str,
        session_id: str
    ) -> Optional[ConversationContext]:
        """Retrieve conversation context from Redis.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            
        Returns:
            ConversationContext if found and not expired, None otherwise
        """
        key = self._get_key(user_id, session_id)
        data = self.redis.get(key)
        
        if not data:
            return None
        
        # Deserialize from JSON
        context_dict = json.loads(data)
        
        # Convert ISO format strings back to datetime
        context_dict['created_at'] = datetime.fromisoformat(context_dict['created_at'])
        context_dict['last_activity'] = datetime.fromisoformat(context_dict['last_activity'])
        
        # Convert message timestamps
        for msg in context_dict.get('messages', []):
            msg['timestamp'] = datetime.fromisoformat(msg['timestamp'])
        
        context = ConversationContext(**context_dict)
        
        # Check if expired
        if context.is_expired():
            self.clear_context(user_id, session_id)
            return None
        
        return context
    
    def add_message(
        self,
        user_id: str,
        session_id: str,
        role: str,
        content: str
    ) -> ConversationContext:
        """Add a message to the conversation context.
        
        Updates last_activity timestamp and resets TTL.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            role: Message role ('user' or 'assistant')
            content: Message content
            
        Returns:
            Updated ConversationContext
        """
        context = self.get_context(user_id, session_id)
        
        if not context:
            # Create new context if none exists
            context = self.create_context(user_id, session_id)
        
        # Add message
        message = Message(
            role=role,
            content=content,
            timestamp=datetime.utcnow()
        )
        context.messages.append(message)
        
        # Update last activity
        context.last_activity = datetime.utcnow()
        
        # Save to Redis with refreshed TTL
        self._save_context(context)
        
        return context
    
    def add_intent(
        self,
        user_id: str,
        session_id: str,
        intent: str
    ) -> ConversationContext:
        """Add an intent to the conversation history.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            intent: Detected intent
            
        Returns:
            Updated ConversationContext
        """
        context = self.get_context(user_id, session_id)
        
        if not context:
            context = self.create_context(user_id, session_id)
        
        context.intent_history.append(intent)
        context.last_activity = datetime.utcnow()
        
        self._save_context(context)
        
        return context
    
    def set_workspace_context(
        self,
        user_id: str,
        session_id: str,
        workspace_id: Optional[str]
    ) -> ConversationContext:
        """Set the current workspace being discussed.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            workspace_id: Workspace ID or None to clear
            
        Returns:
            Updated ConversationContext
        """
        context = self.get_context(user_id, session_id)
        
        if not context:
            context = self.create_context(user_id, session_id, workspace_id)
        else:
            context.workspace_context = workspace_id
            context.last_activity = datetime.utcnow()
            self._save_context(context)
        
        return context
    
    def clear_context(self, user_id: str, session_id: str) -> None:
        """Clear conversation context from Redis.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
        """
        key = self._get_key(user_id, session_id)
        self.redis.delete(key)
    
    def _save_context(self, context: ConversationContext) -> None:
        """Save conversation context to Redis with TTL.
        
        Args:
            context: ConversationContext to save
        """
        key = self._get_key(context.user_id, context.session_id)
        
        # Serialize to JSON
        data = context.model_dump_json()
        
        # Store with TTL
        self.redis.setex(
            key,
            self.ttl_seconds,
            data
        )


# Extension method for ConversationContext
def is_expired(self: ConversationContext) -> bool:
    """Check if context has expired.
    
    Returns:
        True if more than ttl_seconds have elapsed since last_activity
    """
    elapsed = datetime.utcnow() - self.last_activity
    return elapsed.total_seconds() > self.ttl_seconds


# Monkey patch the method onto ConversationContext
ConversationContext.is_expired = is_expired


# Global context manager instance (will be initialized with Redis client)
_context_manager: Optional[ConversationContextManager] = None


def initialize_context_manager(redis_client: redis.Redis, ttl_seconds: int = 1800) -> None:
    """Initialize the global context manager.
    
    Args:
        redis_client: Redis client instance
        ttl_seconds: Time-to-live in seconds (default: 1800 = 30 minutes)
    """
    global _context_manager
    _context_manager = ConversationContextManager(redis_client, ttl_seconds)


def get_conversation_context(user_id: str, session_id: str) -> Optional[ConversationContext]:
    """Get conversation context (convenience function).
    
    Args:
        user_id: User identifier
        session_id: Session identifier
        
    Returns:
        ConversationContext if found, None otherwise
    """
    if _context_manager is None:
        # For testing/development, create a mock Redis client
        import fakeredis
        initialize_context_manager(fakeredis.FakeRedis())
    
    return _context_manager.get_context(user_id, session_id)


def save_conversation_context(context: ConversationContext) -> None:
    """Save conversation context (convenience function).
    
    Args:
        context: ConversationContext to save
    """
    if _context_manager is None:
        # For testing/development, create a mock Redis client
        import fakeredis
        initialize_context_manager(fakeredis.FakeRedis())
    
    _context_manager._save_context(context)


def clear_conversation_context(user_id: str, session_id: str) -> None:
    """Clear conversation context (convenience function).
    
    Args:
        user_id: User identifier
        session_id: Session identifier
    """
    if _context_manager is None:
        # For testing/development, create a mock Redis client
        import fakeredis
        initialize_context_manager(fakeredis.FakeRedis())
    
    _context_manager.clear_context(user_id, session_id)


# Extension method for ConversationContext to add messages
def add_message(self: ConversationContext, role: str, content: str) -> None:
    """Add a message to the conversation.
    
    Args:
        role: Message role ('user' or 'assistant')
        content: Message content
    """
    message = Message(
        role=role,
        content=content,
        timestamp=datetime.utcnow()
    )
    self.messages.append(message)
    self.last_activity = datetime.utcnow()


# Monkey patch the method onto ConversationContext
ConversationContext.add_message = add_message
