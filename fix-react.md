# Fix Proposal: Resolving DSPy Import Issues in Temporal Workflows

## Problem Summary

The Temporal worker is failing with a `RestrictedWorkflowAccessError` because DSPy's import chain includes `requests` → `urllib3`, which tries to access `http.client.IncompleteRead.__mro_entries__` - a restricted operation within Temporal's workflow sandbox.

**Error Location**: `workflows/agentic_ai_workflow.py` imports `ReactAgent` from activities, which imports `dspy`, triggering the restricted import chain.

## Root Cause Analysis

1. **Import Chain**:
   ```
   Workflow → ReactAgent (activity) → dspy → dspy.utils → requests → urllib3 → http.client
   ```

2. **Temporal's Sandbox**: Workflows run in a deterministic sandbox that restricts certain Python operations, including some network-related module introspection.

3. **Current Architecture**: The activity class imports DSPy at the module level, causing the error when the workflow imports the activity.

## Proposed Solutions

### Solution 1: Lazy Import Within Activity

Move all DSPy-related imports inside the activity method, so they only execute during activity runtime (outside the workflow sandbox).

**Implementation**:
```python
# activities/react_agent_activity.py
class ReactAgent:
    def __init__(self, tool_registry=None):
        self.tool_registry = tool_registry
        self._react_agent = None
        self._llm_initialized = False
    
    def _ensure_initialized(self):
        """Lazy initialization of DSPy and ReactAgent."""
        if self._react_agent is None:
            # Import DSPy only when needed
            import dspy
            from agentic_loop.react_agent import ReactAgent as AgenticReactAgent
            from shared.llm_utils import LLMConfig, setup_llm
            
            # Setup LLM
            llm_config = LLMConfig.from_env()
            setup_llm(llm_config)
            
            # Initialize agent
            self._react_agent = AgenticReactAgent(...)
    
    @activity.defn
    async def run_react_agent(self, ...):
        self._ensure_initialized()  # DSPy imported here
        # ... rest of method
```

**Pros**:
- Minimal code changes
- Keeps all agent logic in the activity
- Self-contained activity class

**Cons**:
- LLM initialization happens on first activity call (adds latency)
- Multiple activity instances may initialize LLM separately

### Solution 2: Initialize Agent in Worker, Pass to Activity

Move the `AgenticReactAgent` initialization to the worker script, completely removing DSPy dependencies from the activity module.

**Implementation**:
```python
# scripts/run_worker.py
from agentic_loop.react_agent import ReactAgent as AgenticReactAgent
from shared.llm_utils import LLMConfig, setup_llm

async def main():
    # Setup LLM at worker startup
    llm_config = LLMConfig.from_env()
    setup_llm(llm_config)
    
    # Create tool registry
    registry = create_tool_set_registry(tool_set_name)
    
    # Initialize the Agentic React Agent here
    tool_set_signature = registry.get_react_signature()
    if tool_set_signature:
        # Format signature...
        ReactSignature = tool_set_signature
    else:
        class ReactSignature(dspy.Signature):
            """Use tools to answer the user's question."""
            user_query: str = dspy.InputField(desc="The user's question")
    
    agentic_react_agent = AgenticReactAgent(
        signature=ReactSignature,
        tool_registry=registry
    )
    
    # Create activity with the initialized agent
    react_agent_activity = ReactAgent(agentic_react_agent)
    
    # Register the activity
    worker = Worker(
        client,
        task_queue=TEMPORAL_TASK_QUEUE,
        workflows=[AgenticAIWorkflow],
        activities=[react_agent_activity.run_react_agent],
        activity_executor=activity_executor,
    )
```

```python
# activities/react_agent_activity.py
# NO DSPy imports!
from temporalio import activity
from typing import Any, Dict

class ReactAgent:
    """A ReAct agent activity that uses a pre-initialized agent."""
    
    def __init__(self, agentic_react_agent):
        """
        Initialize with a pre-configured AgenticReactAgent.
        
        Args:
            agentic_react_agent: The initialized agent from agentic_loop
        """
        self._react_agent = agentic_react_agent
    
    @activity.defn
    async def run_react_agent(self, user_query: str, user_name: str = "anonymous") -> Dict[str, Any]:
        """Run the agent without any DSPy imports."""
        # Direct usage - no imports needed
        trajectory, tool_name, tool_args = self._react_agent(
            trajectory={},
            current_iteration=1,
            user_query=user_query
        )
        
        return {
            "status": "success",
            "trajectory": trajectory,
            "tool_name": tool_name,
            "tool_args": tool_args,
            "user_name": user_name,
        }
```

**Pros**:
- Complete separation of concerns
- No DSPy imports in activity module at all
- LLM initialized once at worker startup
- Faster activity execution (no initialization overhead)
- Cleaner activity code

**Cons**:
- Tighter coupling between worker and activity
- Agent configuration happens outside the activity
- Less flexible if different activities need different agent configurations

## Recommendation

I recommend **Solution 2** (Initialize in Worker) for the following reasons:

1. **Clean Separation**: Completely removes DSPy dependencies from the activity module, eliminating any possibility of import issues.

2. **Performance**: LLM and agent initialization happens once at worker startup, not on each activity call.

3. **Follows Temporal Patterns**: Activities should be lightweight executors; complex initialization belongs in the worker setup.

4. **Easier Testing**: The activity becomes a simple wrapper that can be easily mocked/tested without DSPy dependencies.

5. **Aligns with CLAUDE.md Principles**: Keeps the codebase simple and avoids workarounds/hacks.

## Implementation Plan

1. Modify `scripts/run_worker.py` to:
   - Import and setup DSPy/LLM
   - Create and configure the AgenticReactAgent
   - Pass the initialized agent to the activity

2. Simplify `activities/react_agent_activity.py` to:
   - Remove all DSPy imports
   - Accept pre-initialized agent in constructor
   - Focus only on activity execution logic

3. Update any tests to reflect the new initialization pattern

## Alternative Considerations

If we need multiple agent configurations in the future, we could:
- Create a factory pattern in the worker
- Pass configuration to activities and use a shared agent pool
- Use Temporal's workflow-scoped activities for different configurations

## Decision

The recommended approach (Solution 2) provides the cleanest separation, best performance, and most maintainable solution while fully resolving the Temporal sandbox restrictions.