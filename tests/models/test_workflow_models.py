import pytest
from models.workflow_models import WorkflowStatus


class TestWorkflowStatus:
    """Test the WorkflowStatus model"""
    
    def test_valid_workflow_status(self):
        """Test creating valid workflow status"""
        status = WorkflowStatus(
            is_processing=True,
            should_end=False,
            message_count=5,
            pending_messages=2,
            interaction_count=7
        )
        
        assert status.is_processing == True
        assert status.should_end == False
        assert status.message_count == 5
        assert status.pending_messages == 2
        assert status.interaction_count == 7
    
    def test_default_values(self):
        """Test default values for optional fields"""
        status = WorkflowStatus(
            is_processing=False,
            should_end=True,
            message_count=0,
            pending_messages=0,
            interaction_count=0
        )
        
        assert status.is_processing == False
        assert status.should_end == True
        assert status.message_count == 0
        assert status.pending_messages == 0
        assert status.interaction_count == 0
    
    def test_negative_count_validation(self):
        """Test that negative counts are not allowed"""
        # Negative message count
        with pytest.raises(ValueError):
            WorkflowStatus(
                is_processing=True,
                should_end=False,
                message_count=-1,
                pending_messages=0,
                interaction_count=0
            )
        
        # Negative pending messages
        with pytest.raises(ValueError):
            WorkflowStatus(
                is_processing=True,
                should_end=False,
                message_count=0,
                pending_messages=-1,
                interaction_count=0
            )
        
        # Negative interaction count
        with pytest.raises(ValueError):
            WorkflowStatus(
                is_processing=True,
                should_end=False,
                message_count=0,
                pending_messages=0,
                interaction_count=-1
            )
    
    def test_zero_counts_allowed(self):
        """Test that zero counts are valid"""
        status = WorkflowStatus(
            is_processing=True,
            should_end=False,
            message_count=0,
            pending_messages=0,
            interaction_count=0
        )
        
        assert status.message_count == 0
        assert status.pending_messages == 0
        assert status.interaction_count == 0