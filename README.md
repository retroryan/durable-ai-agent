# Durable AI Agent

Production-ready AI agents with automatic checkpointing, seamless recovery, and intelligent tool orchestration.

## Overview

This framework introduces a new architecture for production-grade AI agents that survive failures, restarts, and long-running operations. Built on Temporal's durable execution, it provides the resilience, scalability, and observability needed for reliable agentic systems in real-world business processes.

## The Problem: Production AI Reliability

AI agent frameworks make it easy to build intelligent automation, but there's a critical gap between getting started quickly and achieving production reliability. The core issue: AI agents are distributed systems in disguise. Every tool call faces state persistence challenges, partial failures, and cascading timeouts. Current frameworks offer limited solutions: restart and lose progress, or build complex recovery systems. 

This creates real problems:

**Wasted resources**: Failed LLM calls burn API credits without delivering value

**Development burden**: Engineers implement state management and retry logic instead of agent features

**Reliability gaps**: Mid-task failures leave incomplete results, limiting use for critical operations

## Core Architecture: Durable Agentic Loop

We solve this by integrating three cutting-edge technologies to create a resilient architecture that separates thinking from acting:

**Technologies**:

* **Temporal's Durable Execution**: Workflows that maintain state across failures with stateless workers that scale infinitely

* **DSPy's Context Engineering**: Structured, type-safe reasoning with declarative signatures—moving beyond brittle prompt engineering

* **MCP Integration**: Seamless tool orchestration with built-in support for weather forecasting, historical data, and agricultural analysis

**Architecture**:

* **Thinking (DSPy)**: The agent reasons through problems using structured modules

* **Acting (Temporal Activities)**: Tool execution is isolated and independently durable

* **Orchestration (Temporal Workflows)**: The overall process is checkpointed and resumable

This separation ensures transparency, traceability, and resilience to transient failures at any layer.

## Deep Dive Articles

- [Building AI Agents with React: Why the Agentic Loop Breaks in Production](https://medium.com/@ryan_53117/building-ai-agents-with-react-why-the-agentic-loop-breaks-in-production-7443a4529909)
- [Building Reliable AI Agents: The Architecture of Durable Intelligence](https://medium.com/@ryan_53117/building-reliable-ai-agents-the-architecture-of-durable-intelligence-f9b43e45646c)

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.10+ with Poetry
- Node.js 20+ (for frontend)

### Installation

```bash
# Clone the repository
git clone https://github.com/retroryan/durable-ai-agent
cd durable-ai-agent

# Set up environment files
cp .env.example .env
cp worker.env .worker.env

# Start all services
./run_docker.sh

# Access the applications
# Frontend (Chat UI): http://localhost:3000
# API Server: http://localhost:8000
# API Documentation: http://localhost:8000/docs
# Temporal UI: http://localhost:8080
```

## Architecture

```
┌──────────────────┐     ┌────────────────────┐     ┌──────────────────┐
│ Temporal         │────▶│ React Agent        │────▶│ DSPy Agent       │
│ Workflows        │     │ Activity           │     │ (Reasoning)      │
└──────────────────┘     └────────────────────┘     └──────────────────┘
                                                              │
                                                              ▼
┌──────────────────┐     ┌────────────────────┐     ┌──────────────────┐
│ Extract Agent    │◀────│ Query Fully        │◀────│ Tool Execution   │
│ Activity         │     │ Answered?          │     │ Activity         │
└──────────────────┘     └────────────────────┘     └──────────────────┘
```

See [Architecture Documentation](docs/ARCHITECTURE.md) for detailed system design.

**Key components:**
- **API Server**: FastAPI REST endpoints
- **Workflows**: Temporal durable execution
- **Agent**: DSPy reasoning loops
- **Tools**: MCP-integrated weather services

## Usage Examples

### Basic Chat Interaction

```bash
# Open the chat UI
open http://localhost:3000

# Example queries:
# "weather: Are conditions good for planting corn in Ames, Iowa?"
# "historical: Show me last week's temperatures in Chicago"
# "agriculture: What's the soil moisture in Nebraska?"
```

### API Usage

```python
# Start a new conversation
POST /chat
{
  "message": "weather: Is it a good day for harvesting wheat?",
  "user_id": "user123"
}

# Check workflow status
GET /workflow/{workflow_id}/status

# Query workflow state
GET /workflow/{workflow_id}/query
```

## MCP Integration

The project includes a complete Model Context Protocol implementation with specialized weather services:

### Available MCP Servers

- **Forecast Server** (port 7778): Weather forecasts up to 7 days
- **Historical Server** (port 7779): Historical weather data with 5-day delay
- **Agricultural Server** (port 7780): Agricultural conditions and soil moisture

### Running MCP Servers

```bash
# Run all servers at once
poetry run poe mcp-all

# Or run individual servers
poetry run poe mcp-forecast
poetry run poe mcp-historical
poetry run poe mcp-agricultural

# Stop all servers
poetry run poe mcp-stop
```

### MCP Tools in the Agent

The system includes MCP-enabled tools that seamlessly integrate with the agentic workflow:

- `WeatherForecastMCPTool`: Weather forecasts via MCP
- `HistoricalWeatherMCPTool`: Historical weather data via MCP
- `AgriculturalWeatherMCPTool`: Agricultural conditions via MCP

## Development

### Local Setup

```bash
# Install dependencies
poetry install

# Start Temporal (requires Temporal CLI)
temporal server start-dev

# Run components in separate terminals
poetry run python scripts/run_worker.py
poetry run python api/main.py
cd frontend && npm install && npm run dev
```

### Running Tests

```bash
# Run all MCP integration tests
poetry run python integration_tests/run_integration_tests.py

# Run individual tests
poetry run python integration_tests/test_stdio_client.py
poetry run python integration_tests/test_http_client.py
poetry run python integration_tests/test_proxy_integration.py
```

## Project Structure

```
durable-ai-agent/
├── workflows/              # Temporal workflows
├── activities/             # Temporal activities with MCP integrations
├── tools/                  # Tool implementations
├── models/                 # Data models
├── shared/                 # Shared utilities
├── worker/                 # Worker process
├── api/                    # FastAPI server
├── mcp_proxy/             # Unified MCP proxy server
├── mcp_servers/           # MCP server implementations
├── frontend/              # React UI
├── integration_tests/     # Integration test suites
└── docker-compose.yml     # Service orchestration
```

## Use Cases

### Perfect For

- **Complex Reasoning Tasks**: Multi-step workflows requiring tool orchestration
- **Mission-Critical Agents**: Where automatic recovery is essential
- **Long-Running Operations**: Processes that may take hours or days
- **Cost-Sensitive Workflows**: Expensive LLM operations requiring guaranteed execution

### Example Applications

- **Agricultural Analysis**: Weather forecasting combined with soil conditions
- **Financial Analysis**: Multi-source data synthesis with reliability guarantees
- **Research Automation**: Literature review and analysis workflows
- **Customer Support**: Complex multi-step resolution processes

## Documentation

- [Agentic Loop Sample Run](Agentic%20Loop%20Sample%20Run.md) - Example of the full reasoning process
- [Agriculture Query Samples](Agriculture%20Query%20Samples.md) - Sample queries and responses
- [MCP Proxy Server Routing](MCP%20Proxy%20Server%20Routing.md) - Proxy routing details
- [DSPy Overview](DSPy%20Overview.md) - DSPy integration details

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## Roadmap

### Current Features
- DSPy-based agentic reasoning loop
- Temporal workflow orchestration
- MCP tool integration
- Weather and agriculture tools
- React chat interface

### Upcoming Features
- Query classification for tool set selection
- Multi-agent coordination
- Enhanced observability dashboard
- Additional tool integrations

## License

This project is licensed under the [MIT License](LICENSE).

## Acknowledgments

- [Temporal](https://temporal.io/) for durable execution infrastructure
- [DSPy](https://dspy-docs.vercel.app/) for structured prompting framework
- [MCP](https://modelcontextprotocol.io/) for standardized tool communication
- [FastMCP](https://github.com/jlowin/fastmcp) for elegant MCP server implementation

---

**Build production-ready AI agents that think intelligently and execute reliably.**