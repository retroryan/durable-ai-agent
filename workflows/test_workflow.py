"""Simple test workflow for testing activities."""
from datetime import timedelta
from typing import Any, Dict

from temporalio import workflow

from models.types import ToolExecutionRequest


@workflow.defn
class TestWorkflow:
    """Test workflow that executes a single activity."""
    
    @workflow.run
    async def run(self, request: ToolExecutionRequest) -> Dict[str, Any]:
        """Run workflow that executes the MCP activity."""
        # Execute the activity
        result = await workflow.execute_activity(
            "execute_mcp_tool",
            request,
            start_to_close_timeout=timedelta(seconds=30),
        )
        
        return result