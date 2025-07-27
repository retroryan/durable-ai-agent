# Durable AI Agent

Production-ready AI agents with automatic checkpointing, seamless recovery, and intelligent tool orchestration.

## Overview

The durable-ai-agent represents a fundamental evolution in building reliable AI agents. By combining DSPy's context engineering, Temporal's durable execution, and modern MCP integration, it demonstrates how to build production-ready agentic AI applications that go beyond traditional prompt engineering to deliver agents that reason systematically, execute tools autonomously, and maintain state through failures while ensuring every decision is traceable and every action is durable.

**Key Technologies**:

* **Temporal's Durable Execution**: Workflows that maintain state across failures with stateless workers that scale infinitely

* **DSPy's Context Engineering**: Structured, type-safe reasoning with declarative signatures—moving beyond brittle prompt engineering

* **MCP Integration**: Seamless tool orchestration with built-in support for weather forecasting, historical data, and agricultural analysis

## Deep Dive Articles

- [Building AI Agents with React: Why the Agentic Loop Breaks in Production](https://medium.com/@ryan_53117/building-ai-agents-with-react-why-the-agentic-loop-breaks-in-production-7443a4529909)
- [Building Reliable AI Agents: The Architecture of Durable Intelligence](https://medium.com/@ryan_53117/building-reliable-ai-agents-the-architecture-of-durable-intelligence-f9b43e45646c)

## Quick Start

### Prerequisites

- Docker and Docker Compose

### Installation

```bash
# Set up environment files
cp .env.example .env

# Start all services
./run_docker.sh
```

### Access the Applications

```bash
# Open the chat UI
open http://localhost:3000
```

**Example queries:**
- `"What are the soil moisture levels at my tree farm in Olympia, Washington?"`
- `"Compare current weather and agricultural conditions between Napa Valley and Sonoma County for grape growing. Which location has better conditions right now?"`
- `"What's the weather like in New York and should I bring an umbrella?"`
- `"Check current conditions in Des Moines, Iowa for corn, soybeans, and wheat - which crop has the best growing conditions right now?"`
- `"Compare weather patterns in Napa Valley for the first week of February, March, and April 2024. Which month had the best conditions for vineyard work?"`

**Service URLs:**
- API Server: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Temporal UI: http://localhost:8080


## Architecture

```
┌──────────────────┐     ┌────────────────────┐     ┌──────────────────┐
│ Temporal         │────▶│ React Agent        │────▶│ DSPy Agent       │
│ Workflows        │     │ Activity           │     │ (Reasoning)      │
└──────────────────┘     └────────────────────┘     └──────────────────┘
                                  ▲                           │
                                  │ no                        ▼
┌──────────────────┐     ┌────────────────────┐     ┌──────────────────┐
│ Extract Agent    │◀────│ Query Fully        │◀────│ Tool Execution   │
│ Activity         │ Yes │ Answered?          │     │ Activity         │
└──────────────────┘     └────────────────────┘     └──────────────────┘
```

See [Architecture Documentation](docs/ARCHITECTURE.md) for detailed system design.

**Key components:**
- **API Server**: FastAPI REST endpoints
- **Workflows**: Temporal durable execution
- **Agent**: DSPy reasoning loops
- **Tools**: MCP-integrated weather services

For development setup, running locally, and testing, see the [Development Guide](docs/DEVELOPMENT_GUIDE.md).

For a deep dive into the DSPy agent loop architecture, see the [DSPy Overview](docs/DSPY_OVERVIEW.md).


## MCP Integration

The project includes a complete Model Context Protocol implementation with specialized weather services:

- **Forecast Server**: Weather forecasts up to 7 days
- **Historical Server**: Historical weather data with 5-day delay
- **Agricultural Server**: Agricultural conditions and soil moisture

The system includes MCP-enabled tools that seamlessly integrate with the agentic workflow:

- `WeatherForecastTool`: Weather forecasts via MCP
- `HistoricalWeatherTool`: Historical weather data via MCP
- `AgriculturalWeatherTool`: Agricultural conditions via MCP


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
├── mcp_servers/           # MCP server implementations
├── frontend/              # React UI
├── integration_tests/     # Integration test suites
└── docker-compose.yml     # Service orchestration
```

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.



---

**Build production-ready AI agents that think intelligently and execute reliably.**

## License

This project is licensed under the [MIT License](LICENSE).

## Acknowledgments

- [Temporal](https://temporal.io/) for durable execution infrastructure
- [DSPy](https://dspy-docs.vercel.app/) for structured prompting framework
- [MCP](https://modelcontextprotocol.io/) for standardized tool communication
- [FastMCP](https://github.com/jlowin/fastmcp) for elegant MCP server implementation