from __future__ import annotations

import json
from typing import Any

from agents import Runner

from airline_support.agent import AIRLINE_AGENT

from relai_simulator.adapter_contract import AgentAdapter, AgentTurnResult


def _assistant_message_from_result(result: Any) -> str | None:
    final_output = getattr(result, "final_output", None)
    if final_output is None:
        return None
    if isinstance(final_output, str):
        return final_output
    try:
        return json.dumps(final_output, ensure_ascii=True)
    except TypeError:
        return str(final_output)


class ProjectAgentAdapter:
    def __init__(self) -> None:
        self.agent_or_tools = AIRLINE_AGENT
        self._conversation: list[dict[str, str]] = []

    async def run_turn(self, user_input: Any) -> AgentTurnResult:
        if not isinstance(user_input, str):
            raise TypeError(
                "airline_support simulator turns must be plain strings matching the user message content"
            )

        self._conversation.append({"role": "user", "content": user_input})
        result = await Runner.run(self.agent_or_tools, input=list(self._conversation))
        assistant_message = _assistant_message_from_result(result)
        if assistant_message is not None:
            self._conversation.append({"role": "assistant", "content": assistant_message})

        return AgentTurnResult(
            assistant_message=assistant_message,
            metadata={"history_length": len(self._conversation)},
        )


def build_agent_adapter() -> AgentAdapter:
    return ProjectAgentAdapter()
