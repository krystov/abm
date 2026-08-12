"""Tests for agent_framework: ConversationMemory, Tool, ToolRegistry, BaseLLMAgent."""

import asyncio

from agents.agent_framework import BaseLLMAgent, ConversationMemory, Tool, ToolRegistry


class TestConversationMemory:
    def test_empty_memory(self):
        cm = ConversationMemory()
        assert len(cm) == 0
        assert cm.last_decision() is None
        assert "No prior decisions" in cm.format_for_prompt()

    def test_record_and_retrieve(self):
        cm = ConversationMemory(max_turns=6)
        cm.record(0, {"will_adopt": True}, "LLM decision")
        assert len(cm) == 1
        last = cm.last_decision()
        assert last["tick"] == 0
        assert last["decision"] == {"will_adopt": True}
        assert last["outcome"] == "LLM decision"

    def test_format_for_prompt_contains_decisions(self):
        cm = ConversationMemory(max_turns=3)
        cm.record(0, {"action": "adopt"})
        cm.record(1, {"action": "skip"})
        prompt = cm.format_for_prompt()
        assert "Your Recent Decisions" in prompt
        assert "adopt" in prompt
        assert "skip" in prompt

    def test_trimming_at_max_turns(self):
        cm = ConversationMemory(max_turns=3)
        for i in range(5):
            cm.record(i, {"tick": i})
        assert len(cm) == 3
        ticks = [d["tick"] for d in cm.history]
        assert ticks == [2, 3, 4]

    def test_last_decision_returns_most_recent(self):
        cm = ConversationMemory(max_turns=3)
        cm.record(0, {"first": True})
        cm.record(1, {"second": True})
        assert cm.last_decision()["decision"] == {"second": True}


class TestTool:
    def test_to_openai_spec(self):
        t = Tool(
            name="get_weather",
            description="Get current temperature",
            parameters={
                "type": "object",
                "properties": {"city": {"type": "string"}},
                "required": ["city"],
            },
            fn=lambda city: {"temp": 20},
        )
        spec = t.to_openai_spec()
        assert spec["type"] == "function"
        assert spec["function"]["name"] == "get_weather"
        assert "city" in spec["function"]["parameters"]["properties"]

    def test_tool_callable(self):
        t = Tool(
            name="double",
            description="Double a number",
            parameters={"type": "object", "properties": {}, "required": []},
            fn=lambda x: x * 2,
        )
        assert t.fn(21) == 42


class TestToolRegistry:
    def test_register_and_get_specs(self):
        reg = ToolRegistry()
        t = Tool(
            name="status",
            description="Get status",
            parameters={"type": "object", "properties": {}, "required": []},
            fn=lambda: {"ok": True},
        )
        reg.register(t)
        assert len(reg) == 1
        specs = reg.get_specs()
        assert len(specs) == 1
        assert specs[0]["function"]["name"] == "status"

    def test_invoke_sync_function(self):
        import asyncio
        reg = ToolRegistry()
        t = Tool(
            name="greet",
            description="Greet someone",
            parameters={"type": "object", "properties": {}, "required": []},
            fn=lambda name="world": {"greeting": f"hello {name}"},
        )
        reg.register(t)
        result = asyncio.run(reg.invoke("greet", {"name": "claude"}))
        assert '"hello claude"' in result

    def test_invoke_unknown_tool(self):
        import asyncio
        reg = ToolRegistry()
        result = asyncio.run(reg.invoke("nonexistent", {}))
        assert "Unknown tool" in result

    def test_invoke_tool_that_raises(self):
        import asyncio
        reg = ToolRegistry()
        def _explode():
            raise ValueError("boom")
        t = Tool(
            name="explode",
            description="Always fails",
            parameters={"type": "object", "properties": {}, "required": []},
            fn=_explode,
        )
        reg.register(t)
        result = asyncio.run(reg.invoke("explode", {}))
        assert "boom" in result

    def test_multiple_tools(self):
        reg = ToolRegistry()
        reg.register(Tool("a", "first", {"type": "object", "properties": {}}, fn=lambda: 1))
        reg.register(Tool("b", "second", {"type": "object", "properties": {}}, fn=lambda: 2))
        assert len(reg) == 2
        names = [s["function"]["name"] for s in reg.get_specs()]
        assert "a" in names and "b" in names


class TestBaseLLMAgent:
    def test_creation_with_defaults(self):
        agent = BaseLLMAgent(agent_id=1)
        assert agent.agent_id == 1
        assert agent.llm_model == "gpt-4.1-mini"
        assert len(agent.memory) == 0

    def test_record_decision(self):
        agent = BaseLLMAgent(agent_id=1)
        agent.record_decision(0, {"action": "test"}, "ok")
        assert len(agent.memory) == 1

    def test_format_memory_context(self):
        agent = BaseLLMAgent(agent_id=1)
        agent.record_decision(0, {"x": 1})
        ctx = agent.format_memory_context()
        assert "1" in ctx

    def test_get_client_lazy_init(self):
        agent = BaseLLMAgent(agent_id=1)
        assert agent._llm_client is None
        client = agent._get_client()
        assert client is not None
        assert agent._llm_client is client
