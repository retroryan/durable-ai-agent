# DSPy Agent Loop Architecture

This document provides a detailed technical overview of how the DSPy agentic loop works in the Durable AI Agent project. For a standalone demonstration of the DSPy agentic loop, see the repository at https://github.com/retroryan/dspy-system-prompt. This repository is set up to run with MCP tools integrated into the Temporal workflow architecture.

## Overview

The DSPy agent loop implements a manually controlled React-style (Reason-Act-Observe) pattern using DSPy's structured prompting capabilities. Unlike traditional implementations where the loop is hidden inside a single module, this architecture explicitly separates each phase for maximum control, observability, and integration with durable execution frameworks.

## Architecture Deep Dive

### Core Components

```
┌─────────────────────────────────────┐
│ ReactAgent (DSPy Module)            │
│ - Reasoning Engine                  │
│ - Tool Selection Logic              │
│ - Trajectory Analysis               │
└─────────────────────────────────────┘
    ↓ Signatures & Predictions
┌─────────────────────────────────────┐
│ External Controller                 │
│ - Workflow Orchestration            │
│ - Tool Execution                    │
│ - State Management                  │
└─────────────────────────────────────┘
    ↓ Complete Trajectory
┌─────────────────────────────────────┐
│ ExtractAgent (DSPy Module)          │
│ - Answer Synthesis                  │
│ - Context Integration               │
│ - Final Response Generation         │
└─────────────────────────────────────┘
```

### DSPy Signatures and Type Safety

The system uses DSPy signatures to define structured input/output contracts:

```python
class ReactSignature(dspy.Signature):
    """Signature for the React reasoning step."""
    
    # Inputs
    query: str = dspy.InputField(desc="The user's question or request")
    trajectory: str = dspy.InputField(desc="Previous thoughts and observations")
    tools: List[str] = dspy.InputField(desc="Available tool names and descriptions")
    
    # Outputs (structured reasoning)
    next_thought: str = dspy.OutputField(desc="Reasoning about next action")
    next_tool_name: str = dspy.OutputField(desc="Tool to execute or 'finish'")
    next_tool_args: str = dspy.OutputField(desc="JSON arguments for the tool")
```

This signature-based approach provides:
- **Type Safety**: Clear contracts between components
- **Self-Documentation**: Fields describe their purpose
- **Automatic Prompt Generation**: DSPy constructs optimal prompts
- **Validation**: Outputs are parsed and validated

### Trajectory Management

The trajectory is managed using a Pydantic model that provides type safety and validation:

```python
class Trajectory(BaseModel):
    """Represents a single iteration in the agent's reasoning process."""
    
    iteration: int = Field(description="Iteration number (0-based)")
    thought: str = Field(description="Agent's reasoning for this step")
    tool_name: str = Field(description="Name of the tool to execute")
    tool_args: Dict[str, Any] = Field(default_factory=dict, description="Arguments for the tool")
    observation: Optional[str] = Field(default=None, description="Result from tool execution")
    error: Optional[str] = Field(default=None, description="Error message if execution failed")
    timestamp: datetime = Field(default_factory=datetime.now, description="When this step occurred")
```

Example trajectory sequence:

```python
trajectories = [
    Trajectory(
        iteration=0,
        thought="I need to find weather information for Chicago",
        tool_name="weather_forecast",
        tool_args={"location": "Chicago", "days": 7},
        observation="7-day forecast showing temperatures 65-75°F..."
    ),
    Trajectory(
        iteration=1,
        thought="User also asked about rainfall, checking historical data",
        tool_name="historical_weather",
        tool_args={"location": "Chicago", "days": 30},
        observation="Last 30 days: 5 rainy days, total 2.3 inches..."
    ),
    Trajectory(
        iteration=2,
        thought="I have all needed information, time to synthesize",
        tool_name="finish",
        tool_args={},
        observation="Completed."
    )
]
```

Key aspects of trajectory management:
- **Type Safety**: Pydantic models ensure data consistency and validation
- **State Tracking**: Each trajectory includes completion status, errors, and timestamps
- **Immutable History**: Each iteration creates a new Trajectory object
- **Built-in Methods**: 
  - `is_complete()`: Check if step has observation or error
  - `is_finish`: Property to identify termination steps
  - `summarize_trajectories()`: Generate human-readable summaries
  - `get_tools_used_from_trajectories()`: Extract unique tool usage
- **Error Handling**: Separate fields for observations and errors
- **Temporal Integration**: Timestamps enable debugging and performance analysis
- **Serializable State**: Pydantic models can be easily serialized for durable execution

### The React Loop Mechanics

The React loop operates through these phases:

1. **Reasoning Phase** (ReactAgent)
   - Analyzes user query and current trajectory
   - Uses DSPy's `Predict` for structured reasoning
   - Outputs: thought, tool selection, and arguments

2. **Execution Phase** (External Controller)
   - Validates tool selection
   - Executes tool with provided arguments
   - Handles errors and timeouts
   - Updates trajectory with results

3. **Decision Phase** (Controller Logic)
   - Checks if tool_name == "finish"
   - Enforces iteration limits
   - Manages timeout constraints
   - Decides whether to continue or extract

4. **Extraction Phase** (ExtractAgent)
   - Uses DSPy's `ChainOfThought` for deep analysis
   - Synthesizes information from complete trajectory
   - Generates coherent final answer

### DSPy vs Traditional Prompting

Traditional approach:
```python
# Brittle, string-based prompting
prompt = f"""
You are an AI assistant with access to tools.
User query: {query}
Available tools: {tools}
Previous actions: {history}

Think step by step and respond with your answer in the following JSON format:
{{
    "thought": "your reasoning about what to do next",
    "tool_name": "name of the tool to use",
    "tool_args": {{
        "arg1": "value1",
        "arg2": "value2"
    }}
}}

IMPORTANT: 
- Respond ONLY with valid JSON
- Do not include any text before or after the JSON
- Ensure all JSON keys are properly quoted
- Tool arguments must be a valid JSON object
- If no arguments needed, use empty object {{}}
"""
response = llm.complete(prompt)
# Complex parsing logic with error handling
try:
    # Hope the LLM followed instructions...
    result = json.loads(response)
    thought = result.get("thought", "")
    tool_name = result.get("tool_name", "")
    tool_args = result.get("tool_args", {})
except json.JSONDecodeError:
    # Try to extract JSON from response with regex
    json_match = re.search(r'\{.*\}', response, re.DOTALL)
    if json_match:
        result = json.loads(json_match.group())
    else:
        # Fallback parsing logic...
        pass
```

DSPy approach:
```python
# Structured, type-safe approach
react = dspy.Predict(ReactSignature)
result = react(
    query=query,
    trajectory=trajectory_string,
    tools=tool_descriptions
)
# Direct access to typed fields
thought = result.next_thought
tool = result.next_tool_name
args = json.loads(result.next_tool_args)
```

Benefits of DSPy:
- **No Prompt Engineering**: DSPy generates optimal prompts
- **Automatic Parsing**: Structured outputs without regex
- **Optimization Ready**: Can be optimized with DSPy's compile
- **Model Agnostic**: Works across different LLM providers
- **Maintainable**: Changes to structure don't break parsing

### Integration with Temporal Workflows

The architecture maps perfectly to Temporal's activity model:

```python
@activity.defn
async def react_agent_activity(request: ReactRequest) -> ReactResponse:
    """Temporal activity wrapping DSPy React agent."""
    agent = ReactAgent(tool_registry=request.tool_registry)
    result = agent.forward(
        query=request.query,
        trajectory=request.trajectory
    )
    return ReactResponse(
        thought=result.next_thought,
        tool_name=result.next_tool_name,
        tool_args=result.next_tool_args
    )

@activity.defn
async def tool_execution_activity(request: ToolRequest) -> ToolResponse:
    """Execute selected tool in isolated activity."""
    tool = tool_registry.get_tool(request.tool_name)
    result = await tool.execute(**request.tool_args)
    return ToolResponse(observation=result)
```

This separation enables:
- **Durability**: Each activity is independently retryable
- **Observability**: Clear boundaries for monitoring
- **Scalability**: Activities can run on different workers
- **Error Isolation**: Tool failures don't crash the workflow

### Tool Registry Pattern

The tool registry provides dynamic tool management:

```python
class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
    
    def register_tool(self, tool: BaseTool):
        """Register a tool with validation."""
        # Validate tool has required methods
        # Check for naming conflicts
        # Store with metadata
        
    def get_tool_descriptions(self) -> List[str]:
        """Generate descriptions for DSPy context."""
        return [
            f"{name}: {tool.description}"
            for name, tool in self._tools.items()
        ]
```

This enables:
- **Modularity**: Tools can be added/removed dynamically
- **Type Safety**: Tools implement BaseTool interface
- **Domain Separation**: Different tool sets for different contexts
- **Testing**: Easy to mock tools for unit tests

### Error Handling and Recovery

The architecture provides multiple levels of error handling:

1. **Tool-Level Errors**
   ```python
   try:
       result = await tool.execute(**args)
   except ToolExecutionError as e:
       # Add error to trajectory as observation
       trajectory[f"observation_{idx}"] = f"Error: {str(e)}"
       # Agent can reason about the error and try alternatives
   ```

2. **Iteration Limits**
   ```python
   if iteration_count >= max_iterations:
       # Force extraction with partial results
       # Prevents infinite loops
   ```

3. **Timeout Management**
   ```python
   async with timeout(agent_timeout):
       # All operations must complete within timeout
       # Ensures bounded execution time
   ```

4. **Workflow-Level Recovery**
   - Temporal handles activity retries
   - Workflow state persists across restarts
   - Can resume from any checkpoint

### Advanced Features

#### Trajectory Analysis
The system can analyze trajectories for patterns:
- Tool usage frequency
- Error recovery strategies
- Reasoning depth metrics
- Performance optimization opportunities

#### Context Window Management
For long-running conversations:
- Trajectory summarization when approaching token limits
- Selective history retention
- Important observation prioritization

#### Multi-Agent Coordination
The architecture supports:
- Specialized agents for different domains
- Agent hand-offs based on expertise
- Parallel agent execution for complex queries

#### Optimization Opportunities
With DSPy's compilation features:
- Optimize prompts based on successful trajectories
- Learn better tool selection strategies
- Improve extraction quality with examples

## Production Considerations

### Monitoring and Observability

Key metrics to track:
- **Iterations per query**: Indicates reasoning efficiency
- **Tool success rates**: Identifies problematic tools
- **Token usage**: Cost and performance optimization
- **Latency breakdown**: Time spent in each phase

### Security Considerations

- **Tool Sandboxing**: Execute tools in isolated environments
- **Input Validation**: Sanitize user queries and tool arguments
- **Access Control**: Limit tool availability by user context
- **Audit Logging**: Record all tool executions for compliance

### Scalability Patterns

- **Stateless Agents**: ReactAgent and ExtractAgent are stateless
- **Horizontal Scaling**: Add more workers for parallel execution
- **Caching**: Cache tool results for repeated queries
- **Batch Processing**: Group similar tool calls for efficiency

## Conclusion

The DSPy agent loop architecture provides a robust foundation for building production AI agents. By separating reasoning from execution and leveraging DSPy's structured approach, we achieve:

- **Reliability**: Clear error boundaries and recovery strategies
- **Maintainability**: Type-safe, self-documenting code
- **Observability**: Every decision point is traceable
- **Durability**: Natural integration with workflow engines
- **Flexibility**: Easy to extend with new tools and capabilities

This architecture bridges the gap between experimental AI agents and production-ready systems, providing the control and reliability needed for real-world applications.