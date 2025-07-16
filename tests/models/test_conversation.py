import pytest
from datetime import datetime
from models.conversation import ConversationState, Message


class TestMessage:
    """Test the Message model validation and functionality"""
    
    def test_valid_message_creation(self):
        """Test creating a valid message"""
        msg = Message(actor="user", content="Test message")
        assert msg.actor == "user"
        assert msg.content == "Test message"
        assert msg.timestamp is not None
        assert isinstance(msg.metadata, dict)
        assert len(msg.metadata) == 0
    
    def test_message_with_metadata(self):
        """Test message with metadata"""
        metadata = {"tool": "weather", "confidence": 0.95}
        msg = Message(actor="agent", content="Response", metadata=metadata)
        assert msg.metadata == metadata
    
    def test_actor_validation(self):
        """Test actor field validation"""
        # Valid actors
        for actor in ["user", "agent", "system"]:
            msg = Message(actor=actor, content="Test")
            assert msg.actor == actor
        
        # Invalid actor
        with pytest.raises(ValueError):
            Message(actor="invalid", content="Test")
    
    def test_content_validation(self):
        """Test content field validation"""
        # Empty content
        with pytest.raises(ValueError):
            Message(actor="user", content="")
        
        # Content too long
        with pytest.raises(ValueError):
            Message(actor="user", content="x" * 50001)
        
        # Valid edge cases
        msg1 = Message(actor="user", content="x")  # 1 character
        assert len(msg1.content) == 1
        
        msg2 = Message(actor="user", content="x" * 50000)  # Max length
        assert len(msg2.content) == 50000


class TestConversationState:
    """Test the ConversationState model functionality"""
    
    def test_initial_state(self):
        """Test initial conversation state"""
        state = ConversationState()
        
        assert len(state.messages) == 0
        assert state.interaction_count == 0
        assert state.summary_requested == False
        assert state.summary is None
        assert len(state.tools_used) == 0
        assert len(state.user_context) == 0
    
    def test_add_message(self):
        """Test adding messages to conversation"""
        state = ConversationState()
        
        # Add first message
        state.add_message("user", "Hello")
        assert len(state.messages) == 1
        assert state.interaction_count == 1
        assert state.messages[0].actor == "user"
        assert state.messages[0].content == "Hello"
        
        # Add second message
        state.add_message("agent", "Hi there!", tool="greeting")
        assert len(state.messages) == 2
        assert state.interaction_count == 2
        assert state.messages[1].metadata.get("tool") == "greeting"
    
    def test_message_validation_through_state(self):
        """Test that message validation works when adding through state"""
        state = ConversationState()
        
        # Test content too long
        with pytest.raises(ValueError):
            state.add_message("user", "x" * 50001)
    
    def test_message_count_validation(self):
        """Test conversation message count limits"""
        state = ConversationState()
        
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
    
    def test_tools_used_tracking(self):
        """Test tracking of tools used"""
        state = ConversationState()
        
        state.tools_used.append("weather_tool")
        state.tools_used.append("forecast_tool")
        state.tools_used.append("weather_tool")  # Duplicate
        
        assert len(state.tools_used) == 3
        assert state.tools_used[0] == "weather_tool"
        assert state.tools_used[1] == "forecast_tool"
        assert state.tools_used[2] == "weather_tool"
    
    def test_user_context(self):
        """Test user context storage"""
        state = ConversationState()
        
        state.user_context["name"] = "John"
        state.user_context["preferences"] = {"units": "metric"}
        
        assert state.user_context["name"] == "John"
        assert state.user_context["preferences"]["units"] == "metric"
    
    def test_summary_functionality(self):
        """Test summary request and storage"""
        state = ConversationState()
        
        # Initially no summary
        assert state.summary_requested == False
        assert state.summary is None
        
        # Request summary
        state.summary_requested = True
        state.summary = "This conversation discussed weather patterns."
        
        assert state.summary_requested == True
        assert state.summary == "This conversation discussed weather patterns."