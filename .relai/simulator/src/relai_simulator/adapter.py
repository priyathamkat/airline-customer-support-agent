from __future__ import annotations

from collections.abc import Sequence

from agents import Runner
from openai.types.responses import ResponseTextDeltaEvent

from airline_support.agent import create_airline_agent
from airline_support.models import select_model
from relai_simulator.adapter_contract import AgentAdapter
from relai_simulator.adapter_contract import AgentTurnResult


class ProjectAgentAdapter:
    def __init__(self) -> None:
        self.agent = create_airline_agent()
        self.agent_or_tools = self.agent
        self._conversation: list[dict[str, str]] = []

    async def run_turn(self, user_input: object) -> AgentTurnResult:
        if not isinstance(user_input, str):
            raise TypeError(
                "The airline support simulator expects FixedTurn.content to be a string."
            )

        self._conversation.append({"role": "user", "content": user_input})
        result = Runner.run_streamed(self.agent, input=self._conversation)

        response_chunks: list[str] = []
        async for event in result.stream_events():
            if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                if event.data.delta:
                    response_chunks.append(event.data.delta)

        assistant_message = "".join(response_chunks)
        if not assistant_message:
            assistant_message = _stringify_final_output(getattr(result, "final_output", None))

        if assistant_message is not None:
            self._conversation.append({"role": "assistant", "content": assistant_message})

        return AgentTurnResult(
            assistant_message=assistant_message,
            metadata={
                "provider": select_model().provider,
                "input_contract": "string",
            },
        )


def build_agent_adapter() -> AgentAdapter:
    return ProjectAgentAdapter()


def _stringify_final_output(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray, str)):
        parts = [part for part in (_stringify_final_output(item) for item in value) if part]
        return "".join(parts) or None
    return str(value)
