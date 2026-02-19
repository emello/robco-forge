"""Tests for Lucy conversation context manager.

Requirements:
- 6.1: Conversation context retention (30 minutes)
- 6.2: Context expiration after 30 minutes
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock
import json

from src.lucy.context_manager import (
    ConversationContext,
    ConversationContextManager,
    Message
)


@pytest.fixture
def mock_redis():
    """Create a mock Redis client."""
    redis_mock = Mock()
    redis_mock.get = Mock(return_value=None)
    redis_mock.setex = Mock()
    redis_mock.delete = Mock()
    return redis_mock


@pytest.fixture
def context_manager(mock_redis):
    """Create a ConversationContextManager with mock Redis."""
    return ConversationContextManager(mock_redis, ttl_seconds=1800)


def test_create_context(context_manager, mock_redis):
    """Test creating a new conversation context."""
    user_id = "user123"
    session_id = "session456"
    
    context = context_manager.create_context(user_id, session_id)
    
    assert context.user_id == user_id
    assert context.session_id == session_id
    assert len(context.messages) == 0
    assert context.workspace_context is None
    assert len(context.intent_history) == 0
    assert context.ttl_seconds == 1800
    
    # Verify Redis was called
    mock_redis.setex.assert_called_once()


def test_create_context_with_workspace(context_manager, mock_redis):
    """Test creating context with workspace context."""
    user_id = "user123"
    session_id = "session456"
    workspace_id = "ws-abc123"
    
    context = context_manager.create_context(
        user_id, session_id, workspace_context=workspace_id
    )
    
    assert context.workspace_context == workspace_id


def test_get_context_not_found(context_manager, mock_redis):
    """Test getting context that doesn't exist."""
    mock_redis.get.return_value = None
    
    context = context_manager.get_context("user123", "session456")
    
    assert context is None


def test_get_context_found(context_manager, mock_redis):
    """Test retrieving existing context."""
    user_id = "user123"
    session_id = "session456"
    
    # Create a context
    now = datetime.utcnow()
    test_context = ConversationContext(
        user_id=user_id,
        session_id=session_id,
        created_at=now,
        last_activity=now
    )
    
    # Mock Redis to return serialized context
    mock_redis.get.return_value = test_context.model_dump_json()
    
    # Retrieve context
    context = context_manager.get_context(user_id, session_id)
    
    assert context is not None
    assert context.user_id == user_id
    assert context.session_id == session_id


def test_add_message(context_manager, mock_redis):
    """Test adding a message to conversation."""
    user_id = "user123"
    session_id = "session456"
    
    # Mock get to return None (no existing context)
    mock_redis.get.return_value = None
    
    # Add message
    context = context_manager.add_message(
        user_id, session_id, "user", "Hello Lucy"
    )
    
    assert len(context.messages) == 1
    assert context.messages[0].role == "user"
    assert context.messages[0].content == "Hello Lucy"
    
    # Verify Redis was called to save
    assert mock_redis.setex.call_count >= 1


def test_add_message_to_existing_context(context_manager, mock_redis):
    """Test adding message to existing conversation."""
    user_id = "user123"
    session_id = "session456"
    
    # Create initial context with one message
    now = datetime.utcnow()
    existing_context = ConversationContext(
        user_id=user_id,
        session_id=session_id,
        messages=[
            Message(role="user", content="First message", timestamp=now)
        ],
        created_at=now,
        last_activity=now
    )
    
    # Mock Redis to return existing context
    mock_redis.get.return_value = existing_context.model_dump_json()
    
    # Add second message
    context = context_manager.add_message(
        user_id, session_id, "assistant", "Hello! How can I help?"
    )
    
    assert len(context.messages) == 2
    assert context.messages[1].role == "assistant"
    assert context.messages[1].content == "Hello! How can I help?"


def test_add_intent(context_manager, mock_redis):
    """Test adding intent to conversation history."""
    user_id = "user123"
    session_id = "session456"
    
    mock_redis.get.return_value = None
    
    context = context_manager.add_intent(
        user_id, session_id, "provision_workspace"
    )
    
    assert len(context.intent_history) == 1
    assert context.intent_history[0] == "provision_workspace"


def test_set_workspace_context(context_manager, mock_redis):
    """Test setting workspace context."""
    user_id = "user123"
    session_id = "session456"
    workspace_id = "ws-abc123"
    
    mock_redis.get.return_value = None
    
    context = context_manager.set_workspace_context(
        user_id, session_id, workspace_id
    )
    
    assert context.workspace_context == workspace_id


def test_clear_context(context_manager, mock_redis):
    """Test clearing conversation context."""
    user_id = "user123"
    session_id = "session456"
    
    context_manager.clear_context(user_id, session_id)
    
    # Verify Redis delete was called
    mock_redis.delete.assert_called_once()
    key = f"lucy:context:{user_id}:{session_id}"
    mock_redis.delete.assert_called_with(key)


def test_context_expiration():
    """Test context expiration check."""
    now = datetime.utcnow()
    
    # Recent context (not expired)
    recent_context = ConversationContext(
        user_id="user123",
        session_id="session456",
        created_at=now,
        last_activity=now,
        ttl_seconds=1800
    )
    assert not recent_context.is_expired()
    
    # Old context (expired)
    old_time = now - timedelta(seconds=2000)
    expired_context = ConversationContext(
        user_id="user123",
        session_id="session456",
        created_at=old_time,
        last_activity=old_time,
        ttl_seconds=1800
    )
    assert expired_context.is_expired()


def test_get_context_expired(context_manager, mock_redis):
    """Test that expired context is cleared and returns None."""
    user_id = "user123"
    session_id = "session456"
    
    # Create expired context
    old_time = datetime.utcnow() - timedelta(seconds=2000)
    expired_context = ConversationContext(
        user_id=user_id,
        session_id=session_id,
        created_at=old_time,
        last_activity=old_time,
        ttl_seconds=1800
    )
    
    # Mock Redis to return expired context
    mock_redis.get.return_value = expired_context.model_dump_json()
    
    # Try to get context
    context = context_manager.get_context(user_id, session_id)
    
    # Should return None and clear the context
    assert context is None
    mock_redis.delete.assert_called_once()


def test_ttl_refresh_on_activity(context_manager, mock_redis):
    """Test that TTL is refreshed when adding messages."""
    user_id = "user123"
    session_id = "session456"
    
    # Create context
    now = datetime.utcnow()
    existing_context = ConversationContext(
        user_id=user_id,
        session_id=session_id,
        created_at=now,
        last_activity=now
    )
    
    mock_redis.get.return_value = existing_context.model_dump_json()
    
    # Add message (should refresh TTL)
    context_manager.add_message(user_id, session_id, "user", "Test")
    
    # Verify setex was called (which sets TTL)
    assert mock_redis.setex.called
    call_args = mock_redis.setex.call_args
    assert call_args[0][1] == 1800  # TTL in seconds


def test_redis_key_format(context_manager):
    """Test Redis key format."""
    user_id = "user123"
    session_id = "session456"
    
    key = context_manager._get_key(user_id, session_id)
    
    assert key == "lucy:context:user123:session456"


def test_message_model():
    """Test Message model."""
    now = datetime.utcnow()
    message = Message(
        role="user",
        content="Test message",
        timestamp=now
    )
    
    assert message.role == "user"
    assert message.content == "Test message"
    assert message.timestamp == now
