# DSPy Agentic Loop Demo

A comprehensive example demonstrating how to use DSPy with an agentic loop architecture for multi-tool selection and execution. This project showcases a manually controlled React-style agent loop using DSPy's Chain-of-Thought reasoning, where we explicitly control the React → Extract workflow pattern. This architecture is designed to enable future integration with durable execution frameworks while maintaining full control over the reasoning and action selection process.

The implementation features:
- Type-safe tool registry with Pydantic models for structured input/output
- Manual control over the React (reason → act → observe) loop using DSPy
- Activity management for execution control and metrics
- Support for multiple LLM providers (Ollama, Claude, OpenAI, Gemini)
- Tool sets for different domains (e-commerce, events, treasure hunt, productivity, weather)
- Weather tool set currently uses [Open Meteo](https://open-meteo.com/) (shout out for the great API!) with MCP server integration coming soon

## Quick Start

### Prerequisites

- Python 3.10+
- [Poetry](https://python-poetry.org/) for dependency management
- [Ollama](https://ollama.ai/) installed and running locally (or API keys for cloud providers)

### Setup

```bash
# 1. Clone the repository
git clone https://github.com/retroryan/dspy-system-prompt
cd dspy-system-prompt

# 2. Install dependencies
poetry install

# 3. Copy environment file
cp .env.sample .env
# Edit .env to add your API keys if using cloud providers

# 4. (Optional) For Ollama: pull the model
ollama pull gemma3:27b
```

### Run the Demo

```bash
# Run the React agent demo
poetry run python agentic_loop/demo_react_agent.py

# Run with debug mode to see DSPy prompts
DSPY_DEBUG=true poetry run python agentic_loop/demo_react_agent.py
```

## What is the Agentic Loop?

The agentic loop in this project demonstrates a manually controlled implementation of the DSPy React pattern, where we explicitly separate the React, Extract, and Observe phases for maximum control over execution:

### Flow Diagram

```
User Query
    ↓
┌─────────────────────────────────────┐
│ React Phase (ReactAgent)            │
│ - Uses dspy.Predict                 │
│ - Returns: thought, tool_name, args │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ External Controller                 │
│ (demo_react_agent.py)               │
│ - Execute selected tool             │
│ - Add results to trajectory         │
│ - Decide: continue or finish?       │
└─────────────────────────────────────┘
    ↓ (if tool_name != "finish")
    ↑ (loop until "finish")
    ↓ (when "finish" selected)
┌─────────────────────────────────────┐
│ Extract Phase (ReactExtract)        │
│ - Uses dspy.ChainOfThought          │
│ - Analyzes complete trajectory      │
│ - Synthesizes final answer          │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ Observe Phase                       │
│ - Returns final observer output     │
└─────────────────────────────────────┘
    ↓
Final Answer
```

### React Phase (Tool Selection)
The React agent uses `dspy.Predict` to reason about the user's request and available tools, then returns:
- **next_thought**: The agent's reasoning about what to do next
- **next_tool_name**: Which tool to execute (or "finish" to complete the task)
- **next_tool_args**: Arguments for the selected tool in JSON format

The React phase builds a trajectory dictionary containing all thoughts, tool calls, and observations across iterations.

### External Tool Execution Control
Unlike traditional ReAct where tool execution happens inside the agent, the external controller (`demo_react_agent.py`) decides whether to:
- Execute the selected tool and add results to the trajectory
- Continue the React loop for another iteration
- Handle errors and timeouts
- Manage the overall workflow

### Extract Phase (Answer Synthesis)
After the React loop completes, the Extract agent uses `dspy.ChainOfThought` to:
- Analyze the complete trajectory of thoughts, tool calls, and results
- Synthesize a final answer based on all gathered information
- Provide reasoning for the final response

### Observe Phase (Final Output)
The Extract phase returns an observer that provides the final output, completing the React → Extract → Observe pattern.

### Key Advantages

This manual control approach provides several advantages:
- **Durable Execution Ready**: Each phase can be checkpointed and resumed, making it suitable for integration with workflow engines like Temporal
- **External Control**: The orchestrating code has full control over tool execution, error handling, and flow decisions
- **Explicit State Management**: The trajectory is fully observable and can be persisted between executions
- **Fine-grained Control**: You can inject business logic, validation, or custom handling between any step
- **Debugging & Monitoring**: Clear separation makes it easier to debug issues and monitor agent behavior

The implementation follows DSPy's React → Extract → Observe pattern but with external orchestration:
- **ReactAgent**: DSPy module that performs reasoning and tool selection using `dspy.Predict`
- **External Controller**: Manages the loop, executes tools, and decides when to continue or finish
- **ReactExtract**: DSPy module that synthesizes final answers using `dspy.ChainOfThought`
- **Observer**: Final output phase that returns the completed result

This architecture bridges the gap between LLM reasoning and production systems that require reliability, observability, and durability.

## Detailed Usage

Each tool set comes with comprehensive test cases that demonstrate real-world usage scenarios. The demo runs these test cases to show how the React → Extract → Observe pattern works in practice.

### Weather Tool Set (Recommended Starting Point)

The weather tool set provides comprehensive weather information and is particularly good for demonstrating the agentic loop:

```bash
# Run weather tool set (default)
poetry run python agentic_loop/demo_react_agent.py agriculture

# Example interactions from test cases:
# - "What's the current weather in Paris, France?"
# - "Give me a 7-day forecast for New York City"
# - "What was the weather like in London yesterday?"
```

Available tools:
- `agricultural_weather`: Current weather conditions optimized for agriculture
- `weather_forecast`: Multi-day weather forecasts  
- `historical_weather`: Historical weather data

**Note**: Currently uses [Open Meteo](https://open-meteo.com/) API directly. MCP server integration coming soon for enhanced capabilities.

### E-commerce Tool Set

The e-commerce tool set provides tools for online shopping scenarios with realistic test cases:

```bash
# Run e-commerce demo
poetry run python agentic_loop/demo_react_agent.py ecommerce
```

Available tools:
- `search_products`: Search for products by query and filters
- `add_to_cart`: Add items to shopping cart
- `list_orders`: View customer orders
- `get_order`: Get details of a specific order
- `track_order`: Track shipping status
- `return_item`: Process returns

### Events Tool Set

The events tool set provides tools for event management with comprehensive test scenarios:

```bash
# Run with events tools
poetry run python agentic_loop/demo_react_agent.py events
```

Available tools:
- `find_events`: Search for events by type, location, and date
- `create_event`: Create new events with details
- `cancel_event`: Cancel existing events

### Output and Results

The demo provides:
- Real-time execution progress with reasoning traces
- Tool execution results and state updates
- Performance metrics for each iteration
- Visual progress indicators
- JSON results saved to `test_results/` directory

### Using Different LLM Providers

Configure your LLM provider in the `.env` file:

#### Ollama (Local - Default)
```bash
DSPY_PROVIDER=ollama
OLLAMA_MODEL=gemma3:27b
```

#### Claude (Anthropic)
```bash
DSPY_PROVIDER=claude
ANTHROPIC_API_KEY=your-api-key-here
```

#### OpenAI
```bash
DSPY_PROVIDER=openai
OPENAI_API_KEY=your-api-key-here
```

## Troubleshooting

- **Ollama not running**: Start with `ollama serve`
- **Model not found**: Pull with `ollama pull gemma3:27b`
- **Import errors**: Ensure you're using `poetry run` or activated the virtual environment
- **API key errors**: Check your `.env` file has the correct API keys
- **Timeout errors**: Increase `AGENT_TIMEOUT_SECONDS` in `.env`

## Environment Variables

See `.env.sample` for all available configuration options. Key variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `DSPY_PROVIDER` | LLM provider (`ollama`, `claude`, `openai`) | `ollama` |
| `OLLAMA_MODEL` | Ollama model name | `gemma3:27b` |
| `LLM_TEMPERATURE` | Generation temperature | `0.7` |
| `LLM_MAX_TOKENS` | Maximum tokens | `1024` |
| `DSPY_DEBUG` | Show DSPy prompts/responses | `false` |
| `AGENT_MAX_ITERATIONS` | Maximum agent loop iterations | `5` |
| `AGENT_TIMEOUT_SECONDS` | Maximum execution time | `60.0` |

## Next Steps

- Explore different tool sets and their capabilities
- Create custom tools for your use case
- Experiment with different LLM providers
- Integrate with durable execution frameworks
- Build complex multi-step workflows