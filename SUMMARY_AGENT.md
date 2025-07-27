# Trajectory Summary Agent Design Proposal

## Executive Summary

This proposal outlines the design and implementation of a trajectory summarization system that:
1. Creates a new `SummaryAgent` in `agentic_loop/` following DSPy patterns
2. Creates a new `SummaryAgentActivity` in `activities/` following existing patterns
3. Adds trajectory summarization to the workflow after each prompt is processed
4. Maintains a separate trajectory summary history correlated with conversation messages
5. Provides reasoning transparency without bloating the conversation history

## Current State Analysis

### Problem Statement
- Trajectories contain rich reasoning information but are currently discarded after each prompt
- No way to understand the agent's reasoning retrospectively
- Trajectories can be large and shouldn't be sent to clients directly
- Need correlation between user messages and the reasoning that produced responses

### Current Trajectory Lifecycle

#### 1. Trajectory Reset (Line 174 in `agentic_ai_workflow.py`)
```python
async def _run_react_loop(
    self,
    prompt: str,
    user_name: str
) -> float:
    """
    Run the React agent loop until completion or max iterations.
    ...
    """
    # Reset trajectories for this new prompt
    self.trajectories = []  # <-- THIS IS WHERE RESET HAPPENS (Line 174)
    recat_loop_iterations = 1
    start_time = workflow.now()
    MAX_ITERATIONS = 10
```

**Key Points**:
- The reset happens at the very beginning of `_run_react_loop` method
- This ensures each new user prompt starts with a clean trajectory slate
- The previous trajectory data is lost unless captured elsewhere
- This is why summarization must happen BEFORE processing the next prompt

#### 2. Trajectory Accumulation
- During the React loop (lines 184-263), trajectories accumulate with each iteration
- ReactAgent adds new trajectory entries (line 214): `self.trajectories = agent_result.trajectories`
- ToolExecution updates observations (line 247): `self.trajectories = tool_result.trajectories`

#### 3. Trajectory Usage
- Used by `ExtractAgent` to synthesize the final answer (line 107-111)
- Passed to `_extract_final_answer` method which calls the ExtractAgentActivity
- The extract agent formats and processes the complete trajectory

#### 4. Post-Processing State
- After processing, trajectories remain in `self.trajectories`
- No persistence mechanism exists
- Next prompt will overwrite these trajectories completely
- No correlation maintained between prompts and their trajectories

#### 5. Lost Information
- Without summarization, all reasoning details are lost
- No way to understand why specific responses were generated
- No audit trail of tool selection rationale
- No performance metrics about reasoning complexity

## Proposed Architecture

### 1. New Components

#### `agentic_loop/summary_agent.py`
```python
"""
Summary Agent - Synthesizes trajectory summaries using DSPy
"""
import dspy
from typing import Type, List
from models.trajectory import Trajectory

class TrajectorySummarySignature(dspy.Signature):
    """Extract key insights from agent reasoning trajectory."""
    
    user_query: str = dspy.InputField(desc="The user's original question")
    trajectory: str = dspy.InputField(desc="The complete reasoning trajectory")
    
    summary: str = dspy.OutputField(
        desc="Concise summary of the reasoning process (2-3 sentences)"
    )
    tools_rationale: str = dspy.OutputField(
        desc="Why specific tools were chosen and how they contributed"
    )
    key_findings: str = dspy.OutputField(
        desc="Key information discovered during the reasoning process"
    )
    confidence_level: str = dspy.OutputField(
        desc="High/Medium/Low confidence in the answer based on trajectory"
    )

class SummaryAgent(dspy.Module):
    """Summarizes trajectories into structured insights."""
    
    def __init__(self, signature: Type["Signature"] = TrajectorySummarySignature):
        super().__init__()
        self.signature = signature
        self.summarize = dspy.ChainOfThought(signature)
    
    def forward(self, trajectories: List[Trajectory], user_query: str):
        """Summarize trajectories into structured format."""
        formatted_trajectory = self._format_trajectories(trajectories)
        
        result = self.summarize(
            user_query=user_query,
            trajectory=formatted_trajectory
        )
        
        return dspy.Prediction(
            summary=result.summary,
            tools_rationale=result.tools_rationale,
            key_findings=result.key_findings,
            confidence_level=result.confidence_level,
            trajectory_count=len(trajectories),
            tools_used=Trajectory.get_tools_used_from_trajectories(trajectories)
        )
```

#### `activities/summary_agent_activity.py`
```python
"""Activity that integrates SummaryAgent with Temporal workflows."""
from typing import List
from temporalio import activity
from models.trajectory import Trajectory
from models.types import ActivityStatus, TrajectorySummaryResult

class SummaryAgentActivity:
    """Activity wrapper for trajectory summarization."""
    
    def __init__(self):
        from agentic_loop.summary_agent import SummaryAgent
        self._summary_agent = SummaryAgent()
    
    @activity.defn
    async def summarize_trajectory(
        self, 
        trajectories: List[Trajectory], 
        user_query: str,
        message_id: int,
        user_name: str = "anonymous"
    ) -> TrajectorySummaryResult:
        """
        Summarize a trajectory for storage and analysis.
        
        Args:
            trajectories: Complete trajectory from agent execution
            user_query: Original user query
            message_id: ID of the message this trajectory corresponds to
            user_name: User identifier
            
        Returns:
            TrajectorySummaryResult with summary data
        """
        info = activity.info()
        
        activity.logger.info(
            f"[SummaryAgentActivity] Starting summarization - "
            f"Message ID: {message_id}, Trajectories: {len(trajectories)}"
        )
        
        try:
            summary_result = self._summary_agent(
                trajectories=trajectories,
                user_query=user_query
            )
            
            return TrajectorySummaryResult(
                status=ActivityStatus.SUCCESS,
                message_id=message_id,
                summary=summary_result.summary,
                tools_rationale=summary_result.tools_rationale,
                key_findings=summary_result.key_findings,
                confidence_level=summary_result.confidence_level,
                trajectory_count=summary_result.trajectory_count,
                tools_used=summary_result.tools_used
            )
            
        except Exception as e:
            activity.logger.error(f"[SummaryAgentActivity] Error: {str(e)}")
            return TrajectorySummaryResult(
                status=ActivityStatus.ERROR,
                message_id=message_id,
                error=str(e)
            )
```

#### `models/types.py` additions
```python
class TrajectorySummaryResult(BaseModel):
    """Result from trajectory summarization."""
    
    status: str = Field(description="Success or error status")
    message_id: int = Field(description="ID of message this summary relates to")
    summary: Optional[str] = Field(default=None, description="Concise trajectory summary")
    tools_rationale: Optional[str] = Field(default=None, description="Tool selection reasoning")
    key_findings: Optional[str] = Field(default=None, description="Key discoveries")
    confidence_level: Optional[str] = Field(default=None, description="Confidence in answer")
    trajectory_count: int = Field(default=0, description="Number of trajectory steps")
    tools_used: List[str] = Field(default_factory=list, description="Tools utilized")
    error: Optional[str] = Field(default=None, description="Error if failed")

class TrajectorySummary(BaseModel):
    """Stored trajectory summary linked to conversation."""
    
    message_id: int = Field(description="Links to Message.id in conversation")
    user_query: str = Field(description="Original user query")
    agent_response: str = Field(description="Final response to user")
    summary: str = Field(description="Reasoning process summary")
    tools_rationale: str = Field(description="Why tools were selected")
    key_findings: str = Field(description="Important discoveries")
    confidence_level: str = Field(description="Answer confidence")
    tools_used: List[str] = Field(description="Tools utilized")
    trajectory_count: int = Field(description="Number of reasoning steps")
    execution_time: float = Field(description="Time taken in seconds")
    timestamp: datetime = Field(default_factory=datetime.now)
```

### 2. Workflow Updates

#### Updated `workflows/agentic_ai_workflow.py`

Add new instance variable:
```python
def __init__(self):
    # ... existing init code ...
    self.trajectory_summaries: List[TrajectorySummary] = []
```

Update `process_prompt_agent_loop` method:
```python
async def process_prompt_agent_loop(self):
    """Process a single prompt through the agent loop."""
    if not self.prompt_queue:
        return

    try:
        next_prompt = self.prompt_queue[0]
        workflow.logger.info(f"[AgenticAIWorkflow] Processing prompt: {next_prompt}")
        
        # Get the message ID for correlation
        current_message_id = self.message_id_counter
        
        # Run React loop
        execution_time = await self._run_react_loop(
            prompt=next_prompt,
            user_name=self.user_name
        )
        
        self.execution_time = execution_time

        # Extract final answer
        self.workflow_status = WorkflowStatus.EXTRACTING_ANSWER
        final_answer = await self._extract_final_answer(
            trajectories=self.trajectories,
            prompt=next_prompt,
            user_name=self.user_name
        )
        
        response_message = self._format_response(final_answer, self.trajectories)
        
        # NEW: Summarize trajectory before adding response
        trajectory_summary = await self._summarize_trajectory(
            trajectories=self.trajectories,
            user_query=next_prompt,
            message_id=current_message_id,
            agent_response=response_message,
            execution_time=execution_time
        )
        
        if trajectory_summary:
            self.trajectory_summaries.append(trajectory_summary)
            workflow.logger.info(
                f"[AgenticAIWorkflow] Trajectory summarized - "
                f"Confidence: {trajectory_summary.confidence_level}, "
                f"Tools: {len(trajectory_summary.tools_used)}"
            )
        
        # Save agent response to conversation history
        self.message_id_counter += 1
        agent_message = Message(
            id=self.message_id_counter,
            role=MessageRole.AGENT,
            content=response_message,
            timestamp=workflow.now()
        )
        self.conversation_history.append(agent_message)
        
        # Log completion
        tools_used = Trajectory.get_tools_used_from_trajectories(self.trajectories)
        workflow.logger.info(
            f"[AgenticAIWorkflow] Prompt processed - Tools: {', '.join(tools_used)}, "
            f"Time: {execution_time:.2f}s"
        )
        
        self.workflow_status = WorkflowStatus.WAITING_FOR_INPUT
        self.prompt_queue.popleft()

    except Exception as e:
        # ... existing error handling ...
```

Add new method:
```python
async def _summarize_trajectory(
    self,
    trajectories: List[Trajectory],
    user_query: str,
    message_id: int,
    agent_response: str,
    execution_time: float
) -> Optional[TrajectorySummary]:
    """
    Summarize the trajectory for storage and analysis.
    
    Args:
        trajectories: Complete trajectory list
        user_query: Original user query
        message_id: ID linking to conversation
        agent_response: Final response given to user
        execution_time: Time taken for execution
        
    Returns:
        TrajectorySummary or None if summarization fails
    """
    try:
        summary_result = await workflow.execute_activity_method(
            SummaryAgentActivity.summarize_trajectory,
            args=[trajectories, user_query, message_id, self.user_name],
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=RetryPolicy(
                initial_interval=timedelta(seconds=1),
                maximum_interval=timedelta(seconds=10),
                maximum_attempts=2,
            ),
        )
        
        if summary_result.status == ActivityStatus.SUCCESS:
            return TrajectorySummary(
                message_id=message_id,
                user_query=user_query,
                agent_response=agent_response,
                summary=summary_result.summary,
                tools_rationale=summary_result.tools_rationale,
                key_findings=summary_result.key_findings,
                confidence_level=summary_result.confidence_level,
                tools_used=summary_result.tools_used,
                trajectory_count=summary_result.trajectory_count,
                execution_time=execution_time,
                timestamp=workflow.now()
            )
        else:
            workflow.logger.error(
                f"[AgenticAIWorkflow] Trajectory summarization failed: {summary_result.error}"
            )
            return None
            
    except Exception as e:
        workflow.logger.error(
            f"[AgenticAIWorkflow] Error summarizing trajectory: {e}"
        )
        return None
```

Add query methods:
```python
@workflow.query
def get_trajectory_summary(self, message_id: int) -> Optional[TrajectorySummary]:
    """Get trajectory summary for a specific message."""
    for summary in self.trajectory_summaries:
        if summary.message_id == message_id:
            return summary
    return None

@workflow.query
def get_all_trajectory_summaries(self) -> List[TrajectorySummary]:
    """Get all trajectory summaries."""
    return self.trajectory_summaries

@workflow.query
def get_reasoning_analytics(self) -> Dict[str, Any]:
    """Get analytics about reasoning patterns."""
    if not self.trajectory_summaries:
        return {"total_summaries": 0}
    
    confidence_counts = {"High": 0, "Medium": 0, "Low": 0}
    all_tools = []
    total_steps = 0
    
    for summary in self.trajectory_summaries:
        confidence_counts[summary.confidence_level] += 1
        all_tools.extend(summary.tools_used)
        total_steps += summary.trajectory_count
    
    unique_tools = list(set(all_tools))
    avg_steps = total_steps / len(self.trajectory_summaries) if self.trajectory_summaries else 0
    
    return {
        "total_summaries": len(self.trajectory_summaries),
        "confidence_distribution": confidence_counts,
        "unique_tools_used": unique_tools,
        "average_reasoning_steps": round(avg_steps, 2),
        "total_reasoning_steps": total_steps
    }
```

## Design Decisions

### 1. Trajectory Persistence Strategy
**Decision**: Keep trajectories in memory only during processing, summarize after each prompt.

**Rationale**:
- Full trajectories are large and grow with each tool call
- Summaries capture essential reasoning without the bulk
- Correlation with message IDs enables linking user queries to reasoning

### 2. Summary Storage
**Decision**: Store summaries in a separate list, not in conversation history.

**Rationale**:
- Keeps conversation history clean for client consumption
- Allows separate querying of reasoning data
- Enables analytics without parsing conversation

### 3. Synchronous Summarization
**Decision**: Summarize synchronously after extracting the answer.

**Rationale**:
- Ensures summary is available before moving to next prompt
- Maintains consistency between response and summary
- Simplifies error handling

### 4. Reset vs Accumulate
**Decision**: Continue resetting trajectories for each prompt.

**Rationale**:
- Each prompt should be reasoned about independently
- Prevents trajectory growth over long conversations
- Summaries preserve historical reasoning

## Implementation Plan

1. **Phase 1**: Create core components
   - Implement `SummaryAgent` in `agentic_loop/`
   - Implement `SummaryAgentActivity` in `activities/`
   - Add new types to `models/types.py`

2. **Phase 2**: Integrate with workflow
   - Update `AgenticAIWorkflow` with summary logic
   - Add query methods for retrieving summaries
   - Test with existing workflows

3. **Phase 3**: Testing and refinement
   - Unit tests for `SummaryAgent`
   - Integration tests for activity
   - End-to-end workflow tests

4. **Phase 4**: Optional enhancements
   - Add summary quality metrics
   - Enable summary compression for very long trajectories
   - Add trajectory replay capabilities

## Benefits

1. **Reasoning Transparency**: Understand why the agent made specific choices
2. **Debugging**: Trace issues back to specific reasoning steps
3. **Analytics**: Analyze tool usage patterns and confidence levels
4. **Audit Trail**: Complete record of reasoning for each user interaction
5. **Performance Insights**: Identify which queries require more reasoning steps

## Considerations

1. **Performance**: Summarization adds ~1-2 seconds per prompt
2. **Storage**: Summaries are much smaller than full trajectories
3. **Privacy**: Summaries may contain sensitive reasoning details
4. **Consistency**: Summaries should accurately reflect trajectory content

## Example Usage

```python
# Query trajectory summary for a specific message
summary = workflow.query("get_trajectory_summary", 5)
print(f"Reasoning: {summary.summary}")
print(f"Confidence: {summary.confidence_level}")
print(f"Tools used: {', '.join(summary.tools_used)}")

# Get reasoning analytics
analytics = workflow.query("get_reasoning_analytics")
print(f"Average steps: {analytics['average_reasoning_steps']}")
print(f"Confidence distribution: {analytics['confidence_distribution']}")
```

## Conclusion

This trajectory summarization system provides valuable insights into the agent's reasoning process without bloating the conversation history. By correlating summaries with message IDs, we maintain a clear link between user queries and the reasoning that produced responses, enabling better debugging, analytics, and transparency.