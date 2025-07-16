import pytest
from datetime import datetime, timedelta

from models.conversation import ConversationState, Message
from models.conversation_models import ConversationSummary
from models.conversation_persistence import (
    ExportedMessage, 
    ExportedConversation,
    export_conversation_state,
    create_conversation_summary_message
)
from helpers.conversation_helpers import ConversationManager


class TestPhase3StateManagement:
    """Tests for Phase 3 state management features"""
    
    def test_conversation_manager_history_limits(self):
        """Test that ConversationManager maintains history size limits"""
        state = ConversationState()
        manager = ConversationManager(state)
        
        # Add many messages
        for i in range(150):
            manager.add_message("user", f"Message {i}")
        
        # Should maintain maximum size
        assert len(manager.state.messages) == ConversationManager.MAX_HISTORY_SIZE
        
        # Should have recent messages
        recent = manager.get_recent_context(5)
        assert len(recent) == 5
        assert recent[-1].content == "Message 149"
    
    def test_conversation_manager_summary(self):
        """Test ConversationManager summary generation"""
        state = ConversationState()
        manager = ConversationManager(state)
        
        # Add various messages
        manager.add_message("user", "Hello")
        manager.add_message("agent", "Hi there!")
        manager.add_message("user", "What's the weather?")
        manager.add_message("agent", "It's sunny today")
        
        # Add tools used
        state.tools_used.extend(["weather_tool", "forecast_tool", "weather_tool"])
        
        # Get summary
        summary = manager.get_conversation_summary()
        
        assert isinstance(summary, ConversationSummary)
        assert summary.total_messages == 4
        assert summary.user_messages == 2
        assert summary.agent_messages == 2
        assert set(summary.tools_used) == {"weather_tool", "forecast_tool"}
        assert summary.duration is not None
    
    def test_exported_message_validation(self):
        """Test ExportedMessage validation"""
        # Valid message
        msg = ExportedMessage(
            actor="user",
            content="Test message",
            timestamp=datetime.now().isoformat()
        )
        assert msg.actor == "user"
        assert msg.content == "Test message"
        
        # Invalid timestamp
        with pytest.raises(ValueError, match="Timestamp must be in ISO format"):
            ExportedMessage(
                actor="user",
                content="Test",
                timestamp="invalid-timestamp"
            )
    
    def test_export_conversation_state(self):
        """Test exporting conversation state"""
        state = ConversationState()
        
        # Add messages
        for i in range(60):
            state.add_message("user" if i % 2 == 0 else "agent", f"Message {i}")
        
        # Add tools and context
        state.tools_used = ["tool1", "tool2", "tool1", "tool3"]
        state.user_context = {"preference": "weather", "location": "NYC"}
        
        # Export state
        exported = export_conversation_state(state)
        
        assert isinstance(exported, ExportedConversation)
        assert len(exported.messages) == 50  # Last 50 messages
        assert exported.messages[0].content == "Message 10"
        assert exported.messages[-1].content == "Message 59"
        assert set(exported.tools_used) == {"tool1", "tool2", "tool3"}
        assert exported.user_context == state.user_context
        assert exported.version == "1.0"
    
    def test_create_conversation_summary_message(self):
        """Test conversation summary message creation"""
        state = ConversationState()
        
        # Add messages and tools
        state.add_message("user", "Hello")
        state.add_message("agent", "Hi")
        state.tools_used = ["weather_tool", "forecast_tool"]
        state.user_context = {"topics": ["weather", "travel"], "name": "John"}
        
        # Create summary
        summary = create_conversation_summary_message(state)
        
        assert "Messages exchanged: 2" in summary
        assert "Key topics: weather, travel" in summary
        assert "Tools used:" in summary
        assert "User preferences:" in summary
    
    def test_conversation_state_validation(self):
        """Test ConversationState validation limits"""
        state = ConversationState()
        
        # Test message count validation
        # Add messages up to the limit
        for i in range(999):
            state.messages.append(Message(actor="user", content=f"Msg {i}"))
        
        # One more should be fine
        state.messages.append(Message(actor="user", content="Msg 999"))
        assert len(state.messages) == 1000
        
        # But exceeding 1000 should raise error when validated
        state.messages.append(Message(actor="user", content="Msg 1000"))
        with pytest.raises(ValueError, match="Conversation exceeds maximum message limit"):
            # Trigger validation by creating new instance
            ConversationState(**state.model_dump())
    
    def test_conversation_manager_duration_calculation(self):
        """Test duration calculation in ConversationManager"""
        state = ConversationState()
        manager = ConversationManager(state)
        
        # Add messages with specific timestamps
        base_time = datetime.now()
        
        # Manually create messages with controlled timestamps
        msg1 = Message(actor="user", content="First", timestamp=base_time)
        msg2 = Message(actor="agent", content="Second", timestamp=base_time + timedelta(seconds=30))
        msg3 = Message(actor="user", content="Third", timestamp=base_time + timedelta(seconds=60))
        
        state.messages = [msg1, msg2, msg3]
        
        # Get summary
        summary = manager.get_conversation_summary()
        
        # Duration should be 60 seconds
        assert summary.duration == 60.0