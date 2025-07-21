# Durable Agentic Architecture

This architecture demonstrates how to build production-ready AI agents by integrating three cutting-edge technologies:

1. **Temporal's Durable Execution**: Workflows that maintain state across failures with stateless workers that scale infinitely
2. **DSPy's Context Engineering**: Structured, type-safe reasoning with declarative signatures—moving beyond brittle prompt engineering
3. **MCP Integration**: Seamless tool orchestration with built-in support for weather forecasting, historical data, and agricultural analysis

## Architecture Overview

```mermaid
flowchart TD
    A[API Server] --> C[Agentic AI Workflow<br/><b>Durable & Resumable</b><br/><i>Survives failures/restarts</i>]
    C --> D[React Agent Activity<br/><b>Resilient & Retryable</b><br/><i>Auto-retry on LLM failures</i>]
    D --> E[React Agent<br/><i>DSPy Reasoning</i>]
    E --> F[LLM]
    F --> G[Tool Execution Activity<br/><b>Fault-Tolerant</b><br/><i>Retries & circuit breakers</i>]
    G --> H{Query Fully<br/>Answered?}
    H -->|No| C
    H -->|Yes| I[Extract Agent Activity<br/><b>Guaranteed Execution</b><br/><i>Never loses accumulated state</i>]
    I --> J[Extract Agent<br/><i>DSPy Synthesis</i>]
    J --> K[LLM Summary]
    K --> L[User Response]
```

The architecture separates thinking from acting:
- **Thinking (DSPy)**: The agent reasons through problems using structured modules
- **Acting (Temporal Activities)**: Tool execution is isolated and independently durable
- **Orchestration (Temporal Workflows)**: The overall process is checkpointed and resumable