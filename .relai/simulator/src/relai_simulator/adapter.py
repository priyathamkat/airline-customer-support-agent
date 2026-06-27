from __future__ import annotations

from airline_support.agent import AIRLINE_AGENT, stream_agent_response
from airline_support.sessions import ChatMessage, utc_now
from relai_simulator.adapter_contract import AgentAdapter, AgentTurnResult


def _coerce_user_message(user_input: object) -> str:
    if not isinstance(user_input, str):
        raise TypeError(
            "The airline support simulator expects FixedTurn.content to be a string user message."
        )
    if not user_input.strip():
        raise ValueError("The airline support simulator requires a non-empty user message.")
    return user_input


class ProjectAgentAdapter:
    agent_or_tools: object | None = AIRLINE_AGENT

    def __init__(self) -> None:
        self._messages: list[ChatMessage] = []

    async def run_turn(self, user_input: object) -> AgentTurnResult:
        user_message = _coerce_user_message(user_input)
        self._messages.append(
            ChatMessage(
                role="user",
                content=user_message,
                created_at=utc_now(),
            )
        )

        chunks: list[str] = []
        async for delta in stream_agent_response(self._messages):
            chunks.append(delta)
        assistant_message = "".join(chunks).strip()

        self._messages.append(
            ChatMessage(
                role="assistant",
                content=assistant_message,
                created_at=utc_now(),
            )
        )
        return AgentTurnResult(
            assistant_message=assistant_message,
            metadata={"message_count": len(self._messages)},
        )


def build_agent_adapter() -> AgentAdapter:
    return ProjectAgentAdapter()
