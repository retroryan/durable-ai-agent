"""LLM Factory for multi-provider support using DSPy's unified interface."""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import dspy
from dotenv import load_dotenv
from pydantic import BaseModel, Field


class TokenUsage(BaseModel):
    """Token usage statistics for a single LLM call."""

    input: int = Field(default=0, description="Number of input/prompt tokens")
    output: int = Field(default=0, description="Number of output/completion tokens")
    total: int = Field(default=0, description="Total tokens used (input + output)")


class Message(BaseModel):
    """A single message in the conversation."""

    role: str = Field(
        description="Role of the message sender (user, assistant, system)"
    )
    content: str = Field(description="Content of the message")


class LLMHistoryEntry(BaseModel):
    """Structured representation of a single LLM interaction."""

    timestamp: Optional[str] = Field(
        default=None, description="Timestamp of the interaction"
    )
    model: Optional[str] = Field(
        default=None, description="Model used for the interaction"
    )
    uuid: Optional[str] = Field(
        default=None, description="Unique identifier (first 8 chars)"
    )
    conversation: List[Message] = Field(
        default_factory=list, description="List of messages in the conversation"
    )
    tokens: TokenUsage = Field(
        default_factory=TokenUsage, description="Token usage statistics"
    )
    cost: Optional[float] = Field(
        default=None, description="Cost of the API call if available"
    )


class LLMHistory(BaseModel):
    """Collection of LLM history entries with aggregated statistics."""

    entries: List[LLMHistoryEntry] = Field(
        default_factory=list, description="List of history entries"
    )
    total_tokens: TokenUsage = Field(
        default_factory=TokenUsage, description="Aggregated token usage"
    )
    total_cost: float = Field(default=0.0, description="Total cost across all entries")

    def calculate_totals(self) -> None:
        """Calculate total token usage and cost across all entries."""
        self.total_tokens = TokenUsage(input=0, output=0, total=0)
        self.total_cost = 0.0

        for entry in self.entries:
            self.total_tokens.input += entry.tokens.input
            self.total_tokens.output += entry.tokens.output
            self.total_tokens.total += entry.tokens.total
            if entry.cost is not None:
                self.total_cost += entry.cost


class LLMConfig(BaseModel):
    """Configuration for setting up the LLM."""

    provider: str = Field(
        default_factory=lambda: os.getenv("DSPY_PROVIDER", "ollama"),
        description="LLM provider",
    )
    temperature: float = Field(
        default_factory=lambda: float(os.getenv("LLM_TEMPERATURE", "0.7")),
        description="LLM temperature",
    )
    max_tokens: int = Field(
        default_factory=lambda: int(os.getenv("LLM_MAX_TOKENS", "1024")),
        description="LLM max tokens",
    )
    debug: bool = Field(
        default_factory=lambda: os.getenv("DSPY_DEBUG", "false").lower() == "true",
        description="DSPy debug mode",
    )

    ollama_model: str = Field(
        default_factory=lambda: os.getenv("OLLAMA_MODEL", "gemma3:27b")
    )
    ollama_base_url: str = Field(
        default_factory=lambda: os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    )
    claude_model: str = Field(
        default_factory=lambda: os.getenv("CLAUDE_MODEL", "claude-3-opus-20240229")
    )
    openai_model: str = Field(
        default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
    )
    gemini_model: str = Field(
        default_factory=lambda: os.getenv("GEMINI_MODEL", "gemini-1.5-pro-latest")
    )

    llm_model: Optional[str] = Field(
        default_factory=lambda: os.getenv("LLM_MODEL"),
        description="Generic model for other providers",
    )

    @classmethod
    def from_env(cls) -> "LLMConfig":
        """Loads configuration from environment variables, sourcing a .env file first."""
        env_file = Path(__file__).parent.parent / ".env"
        if env_file.exists():
            load_dotenv(env_file)
        return cls()


def setup_llm(config: LLMConfig) -> dspy.LM:
    """
    Factory function to configure DSPy LLM based on a configuration object.

    Args:
        config: The LLMConfig object with all necessary settings.

    Returns:
        Configured dspy.LM instance
    """
    provider = config.provider

    print(f"🤖 Setting up {provider} LLM")

    # Set up DSPy logging if DSPY_DEBUG is enabled
    if config.debug:
        logging.getLogger("dspy").setLevel(logging.DEBUG)
        print(f"   🔍 DSPy debug logging: ENABLED")
        print(f"   💡 Use dspy.inspect_history() to see prompts/responses")

    # Configure based on provider
    if provider == "ollama":
        model = config.ollama_model
        base_url = config.ollama_base_url
        print(f"   Model: {model}")
        print(f"   Base URL: {base_url}")
        llm = dspy.LM(
            model=f"ollama/{model}",
            api_base=base_url,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
        )
    elif provider == "claude":
        model = config.claude_model
        print(f"   Model: {model}")
        llm = dspy.LM(
            model=f"anthropic/{model}",
            temperature=config.temperature,
            max_tokens=config.max_tokens,
        )
    elif provider == "openai":
        model = config.openai_model
        print(f"   Model: {model}")
        llm = dspy.LM(
            model=f"openai/{model}",
            temperature=config.temperature,
            max_tokens=config.max_tokens,
        )
    elif provider == "gemini":
        model = config.gemini_model
        print(f"   Model: {model}")
        llm = dspy.LM(
            model=f"gemini/{model}",
            temperature=config.temperature,
            max_tokens=config.max_tokens,
        )
    else:
        # Generic provider support using full model string
        model = config.llm_model or f"{provider}/default-model"
        print(f"   Model: {model}")
        llm = dspy.LM(
            model=model, temperature=config.temperature, max_tokens=config.max_tokens
        )

    # Test connection
    try:
        llm("Hello", max_tokens=100)
        print(f"   ✅ {provider} connection successful")
    except Exception as e:
        print(f"   ❌ {provider} connection failed: {e}")
        if provider == "claude":
            print(
                "   💡 Make sure ANTHROPIC_API_KEY is set in your environment or cloud.env"
            )
        elif provider == "openai":
            print(
                "   💡 Make sure OPENAI_API_KEY is set in your environment or cloud.env"
            )
        elif provider == "gemini":
            print(
                "   💡 Make sure GOOGLE_API_KEY is set in your environment or cloud.env"
            )
        raise

    # Configure DSPy
    dspy.settings.configure(lm=llm)

    return llm


def extract_messages(
    history_entries: List[Dict[str, Any]], n: Optional[int] = None
) -> LLMHistory:
    """
    Extract DSPy history entries as structured Pydantic models.

    Args:
        history_entries: List from GLOBAL_HISTORY or lm.history
        n: Number of recent entries (None for all)

    Returns:
        LLMHistory object with structured message data and aggregated statistics
    """
    if not history_entries:
        return LLMHistory()

    # Get entries to process
    entries = history_entries[-n:] if n else history_entries
    history_entries_list = []

    for entry in entries:
        # Create conversation messages
        conversation = []

        # Input messages
        messages = entry.get("messages") or [
            {"role": "user", "content": entry.get("prompt", "")}
        ]

        for msg in messages:
            content = msg.get("content", "")

            # Handle different content types
            if isinstance(content, str):
                message_text = content
            elif isinstance(content, list):
                # Extract text from complex content (images, audio, etc.)
                text_parts = []
                for item in content:
                    if item.get("type") == "text":
                        text_parts.append(item.get("text", ""))
                message_text = " ".join(text_parts)
            else:
                message_text = str(content)

            conversation.append(
                Message(role=msg.get("role", "user"), content=message_text)
            )

        # Response/output
        outputs = entry.get("outputs", [])
        if outputs:
            # Handle different output formats
            if isinstance(outputs[0], dict):
                response_text = outputs[0].get("text", "")
            else:
                response_text = str(outputs[0])

            conversation.append(Message(role="assistant", content=response_text))

        # Token usage - handle different formats
        usage = entry.get("usage", {})
        if isinstance(usage, dict):
            tokens = TokenUsage(
                input=usage.get("prompt_tokens", 0),
                output=usage.get("completion_tokens", 0),
                total=usage.get("total_tokens", 0),
            )
        else:
            # Handle case where usage might be an integer or other type
            tokens = TokenUsage(
                input=0,
                output=0,
                total=int(usage) if isinstance(usage, (int, float)) else 0,
            )

        # Create history entry
        history_entry = LLMHistoryEntry(
            timestamp=entry.get("timestamp"),
            model=entry.get("model"),
            uuid=entry.get("uuid")[:8] if entry.get("uuid") else None,
            conversation=conversation,
            tokens=tokens,
            cost=entry.get("cost"),
        )

        history_entries_list.append(history_entry)

    # Create LLMHistory object and calculate totals
    history = LLMHistory(entries=history_entries_list)
    history.calculate_totals()

    return history


def save_dspy_history(
    tool_set_name: str,
    agent_type: str,
    index: int,
    n_entries: Optional[int] = 1,
    output_dir: str = "prompts_out",
    history: Optional[LLMHistory] = None,
) -> str:
    """
    Extract and save the last N DSPy history entries to a JSON file.

    Args:
        tool_set_name: Name of the tool set being used
        agent_type: Type of agent ("react" or "extract")
        index: Index/iteration number
        n_entries: Number of recent entries to extract (default: 1 for last entry only)
        output_dir: Directory to save the JSON files
        history: Optional pre-extracted LLMHistory object. If not provided, will extract from GLOBAL_HISTORY

    Returns:
        Path to the saved JSON file
    """
    # Create output directory if it doesn't exist
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    # Extract history if not provided
    if history is None:
        from dspy.clients.base_lm import GLOBAL_HISTORY

        history = extract_messages(GLOBAL_HISTORY, n=n_entries)

    if not history or not history.entries:
        return None

    # Create filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{tool_set_name}_{agent_type}_{index}_{timestamp}.json"
    file_path = output_path / filename

    # Convert Pydantic model to dict and save
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(history.model_dump(), f, indent=2, ensure_ascii=False)

    return str(file_path)


def get_full_history() -> LLMHistory:
    """
    Get the full DSPy history from the current session.

    Returns:
        LLMHistory object with all entries and aggregated statistics
    """
    from dspy.clients.base_lm import GLOBAL_HISTORY

    return extract_messages(GLOBAL_HISTORY)
