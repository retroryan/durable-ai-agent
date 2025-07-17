import pytest
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker
from workflows.simple_agent_workflow import SimpleAgentWorkflow
from models.conversation import ConversationState, Message
from models.workflow_models import WorkflowStatus


@pytest.mark.asyncio
class TestSimpleAgentWorkflow:
    """Test SimpleAgentWorkflow signal and query handlers"""
    
