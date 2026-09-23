"""
Agent framework providing LLM-calling foundation for ABM agents.

- ConversationMemory: rolling buffer of past decisions for multi-turn context.
- BaseLLMAgent: wraps AsyncOpenAI, supports memory injection, structured JSON
  output, tool calling, and deterministic fallback on failure.
- ToolRegistry: simple function-calling registry for LLM agents.
"""

import json
import os
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from openai import AsyncOpenAI


# ---------------------------------------------------------------------------
# Response parsing helpers
# ---------------------------------------------------------------------------


def extract_json_object(text: str) -> dict:
    """Extract a JSON object from an LLM response.

    LLM providers (notably DeepSeek) may wrap the requested JSON in prose
    and/or Markdown code fences (```` ```json ... ``` ````).  ``model_validate_json``
    then fails because the whole string is not valid JSON.  This locates the
    first ``{`` and the matching last ``}`` and parses that slice.
    """
    if not text or not text.strip():
        raise ValueError("LLM returned empty content")

    stripped = text.strip()

    # Strip Markdown code fences if present.
    fence = "```"
    if stripped.startswith(fence):
        first_nl = stripped.find("\n")
        stripped = stripped[first_nl + 1:] if first_nl != -1 else ""
    if stripped.rstrip().endswith(fence):
        stripped = stripped.rstrip()
        stripped = stripped[:stripped.rfind(fence)].rstrip()

    start = stripped.find("{")
    end = stripped.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError(f"No JSON object in response: {text[:200]!r}")

    return json.loads(stripped[start:end + 1])


# ---------------------------------------------------------------------------
# LLM provider configuration
# ---------------------------------------------------------------------------


def get_llm_model() -> str:
    """Active LLM model name for the configured provider.

    DeepSeek (deepseek-chat) is used when DEEPSEEK_API_KEY is set; otherwise
    the OpenAI model name is used.
    """
    if os.environ.get("DEEPSEEK_API_KEY"):
        return os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")
    return os.environ.get("OPENAI_MODEL", "gpt-4.1-mini")


def create_llm_client() -> AsyncOpenAI:
    """Build an AsyncOpenAI client for the active LLM provider.

    Prefers DeepSeek (reachable from the current network, unlike the blocked
    api.openai.com) when DEEPSEEK_API_KEY is set; otherwise falls back to OpenAI.
    """
    deepseek_key = os.environ.get("DEEPSEEK_API_KEY")
    if deepseek_key:
        return AsyncOpenAI(
            api_key=deepseek_key,
            base_url=os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        )
    return AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY", "sk-placeholder"))


# ---------------------------------------------------------------------------
# Conversation Memory
# ---------------------------------------------------------------------------


@dataclass
class ConversationMemory:
    """Rolling buffer of past agent decisions for multi-turn context.

    Stores up to `max_turns` entries.  Each entry is a dict with:
      - tick: simulation tick
      - decision: the validated Pydantic model or dict
      - outcome: optional result/feedback from the environment
    """

    max_turns: int = 6
    history: List[Dict[str, Any]] = field(default_factory=list)

    def record(self, tick: int, decision: Any, outcome: Optional[str] = None) -> None:
        """Append a decision record, trimming if over capacity."""
        self.history.append({
            "tick": tick,
            "decision": decision,
            "outcome": outcome,
        })
        if len(self.history) > self.max_turns:
            self.history = self.history[-self.max_turns:]

    def format_for_prompt(self) -> str:
        """Render recent history as a prompt snippet."""
        if not self.history:
            return "(No prior decisions recorded.)"

        lines = ["=== Your Recent Decisions ==="]
        for i, entry in enumerate(self.history, 1):
            d = entry["decision"]
            if hasattr(d, "model_dump"):
                payload = json.dumps(d.model_dump(), ensure_ascii=False)
            else:
                payload = str(d)
            lines.append(f"  [{i}] tick {entry['tick']}: {payload}")
            if entry.get("outcome"):
                lines.append(f"       outcome: {entry['outcome']}")
        return "\n".join(lines)

    def last_decision(self) -> Optional[Dict[str, Any]]:
        """Return the most recent decision, or None."""
        return self.history[-1] if self.history else None

    def __len__(self) -> int:
        return len(self.history)


# ---------------------------------------------------------------------------
# Tool Registry (function calling)
# ---------------------------------------------------------------------------


@dataclass
class Tool:
    """A callable tool that an LLM agent can invoke."""
    name: str
    description: str
    parameters: dict  # JSON Schema for the tool's parameters
    fn: Callable

    def to_openai_spec(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


class ToolRegistry:
    """Registry of tools available to LLM agents."""

    def __init__(self):
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def get_specs(self) -> List[dict]:
        return [t.to_openai_spec() for t in self._tools.values()]

    async def invoke(self, name: str, arguments: dict) -> str:
        tool = self._tools.get(name)
        if tool is None:
            return json.dumps({"error": f"Unknown tool: {name}"})
        try:
            result = tool.fn(**arguments)
            return json.dumps(result, ensure_ascii=False, default=str)
        except Exception as exc:
            return json.dumps({"error": str(exc)})

    def __len__(self) -> int:
        return len(self._tools)


# ---------------------------------------------------------------------------
# Base LLM Agent
# ---------------------------------------------------------------------------


@dataclass
class BaseLLMAgent:
    """Shared foundation for LLM-augmented ABM agents.

    Provides:
      - lazy init of AsyncOpenAI client
      - conversation memory (past decisions)
      - structured JSON output via response_format
      - optional tool calling
      - deterministic fallback on failure

    Subclasses override:
      - _build_llm_prompt(...) -> str
      - _fallback(...) -> Pydantic decision model
      - apply_decision(decision) -> None
    """

    agent_id: int = 0
    llm_model: str = "gpt-4.1-mini"
    system_prompt: str = "You are a rational economic agent. Respond with JSON only."
    temperature: float = 0.3

    _llm_client: Optional[AsyncOpenAI] = field(default=None, repr=False, compare=False)
    memory: ConversationMemory = field(default_factory=ConversationMemory)
    tools: Optional[ToolRegistry] = None

    # ------------------------------------------------------------------
    # LLM client (lazy init)
    # ------------------------------------------------------------------

    def _get_client(self) -> AsyncOpenAI:
        if self._llm_client is None:
            self._llm_client = create_llm_client()
        return self._llm_client

    # ------------------------------------------------------------------
    # Core LLM call with memory + optional tools
    # ------------------------------------------------------------------

    async def ask_llm(
        self,
        user_prompt: str,
        schema_class: type,
        tick: int = 0,
        include_memory: bool = True,
        use_tools: bool = False,
        max_tool_rounds: int = 3,
    ) -> Any:
        """Send a prompt to the LLM and parse the response into `schema_class`.

        On any error returns the deterministic fallback.
        """
        if include_memory and len(self.memory) > 0:
            full_prompt = self.memory.format_for_prompt() + "\n\n" + user_prompt
        else:
            full_prompt = user_prompt

        messages: List[dict] = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": full_prompt},
        ]

        try:
            client = self._get_client()

            if use_tools and self.tools and len(self.tools) > 0:
                return await self._ask_with_tools(
                    client, messages, schema_class, max_tool_rounds
                )

            response = await client.chat.completions.create(
                model=self.llm_model,
                temperature=self.temperature,
                messages=messages,
                response_format={"type": "json_object"},
            )
            raw = response.choices[0].message.content
            return schema_class.model_validate(extract_json_object(raw))

        except Exception:
            return self._fallback(user_prompt, tick)

    async def _ask_with_tools(
        self,
        client: AsyncOpenAI,
        messages: List[dict],
        schema_class: type,
        max_rounds: int,
    ) -> Any:
        """Multi-step tool-calling loop."""
        for _ in range(max_rounds):
            response = await client.chat.completions.create(
                model=self.llm_model,
                temperature=self.temperature,
                messages=messages,
                tools=self.tools.get_specs(),
                tool_choice="auto",
            )

            msg = response.choices[0].message

            if msg.tool_calls:
                messages.append(msg.model_dump())
                for tc in msg.tool_calls:
                    args = json.loads(tc.function.arguments)
                    result = await self.tools.invoke(tc.function.name, args)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": result,
                    })
            elif msg.content:
                try:
                    return schema_class.model_validate(extract_json_object(msg.content))
                except Exception:
                    messages.append({
                        "role": "user",
                        "content": "Output must be valid JSON matching the required schema. Try again.",
                    })
                    continue

        raise RuntimeError("Tool-calling loop exceeded max rounds without valid output")

    # ------------------------------------------------------------------
    # Memory helpers
    # ------------------------------------------------------------------

    def record_decision(self, tick: int, decision: Any, outcome: Optional[str] = None) -> None:
        """Store a decision in conversation memory."""
        self.memory.record(tick, decision, outcome)

    def format_memory_context(self) -> str:
        """Get formatted memory for prompt injection."""
        return self.memory.format_for_prompt()

    # ------------------------------------------------------------------
    # Override points for subclasses
    # ------------------------------------------------------------------

    def _fallback(self, prompt: str, tick: int) -> Any:
        """Deterministic fallback when LLM is unavailable. Override in subclass."""
        raise NotImplementedError("Subclasses must implement _fallback()")
