from __future__ import annotations

import io
import json
from collections.abc import Iterator

import pytest

from airline_support import main


def input_from(values: list[str]) -> Iterator[str]:
    yield from values


@pytest.fixture(autouse=True)
def api_key(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)


@pytest.mark.asyncio
async def test_terminal_chat_logs_user_and_assistant_messages(monkeypatch, tmp_path):
    monkeypatch.setenv("AIRLINE_SUPPORT_LOG_DIR", str(tmp_path))

    async def fake_stream_agent_response(messages):
        assert messages[-1].content == "What is the baggage policy?"
        yield "Standard tickets include "
        yield "one checked bag."

    monkeypatch.setattr(main, "stream_agent_response", fake_stream_agent_response)
    inputs = input_from(["What is the baggage policy?", "exit"])
    output = io.StringIO()

    log_path = await main.chat(input_func=lambda _prompt: next(inputs), output_stream=output)

    events = [
        json.loads(line)
        for line in tmp_path.joinpath(log_path).read_text(encoding="utf-8").splitlines()
    ]
    messages = [event for event in events if event["type"] == "message"]
    assert [message["role"] for message in messages] == ["user", "assistant"]
    assert messages[0]["content"] == "What is the baggage policy?"
    assert messages[1]["content"] == "Standard tickets include one checked bag."
    assert "Standard tickets include one checked bag." in output.getvalue()
    assert f"Saved conversation log to {log_path}" in output.getvalue()


@pytest.mark.asyncio
async def test_terminal_chat_creates_new_log_each_run(monkeypatch, tmp_path):
    monkeypatch.setenv("AIRLINE_SUPPORT_LOG_DIR", str(tmp_path))

    async def fake_stream_agent_response(_messages):
        yield "Hello."

    monkeypatch.setattr(main, "stream_agent_response", fake_stream_agent_response)

    first_log_path = await main.chat(
        input_func=lambda _prompt: "exit",
        output_stream=io.StringIO(),
    )
    second_log_path = await main.chat(
        input_func=lambda _prompt: "q",
        output_stream=io.StringIO(),
    )

    assert first_log_path != second_log_path
    assert tmp_path.joinpath(first_log_path).exists()
    assert tmp_path.joinpath(second_log_path).exists()


@pytest.mark.asyncio
async def test_terminal_chat_can_use_named_log(monkeypatch, tmp_path):
    monkeypatch.setenv("AIRLINE_SUPPORT_LOG_DIR", str(tmp_path))
    tmp_path.joinpath("off-topic-guardrail.jsonl").write_text("old log", encoding="utf-8")

    async def fake_stream_agent_response(messages):
        assert messages[-1].content == "Can you write a chocolate chip cookie recipe?"
        yield "I can only help with airline support questions."

    monkeypatch.setattr(main, "stream_agent_response", fake_stream_agent_response)
    inputs = input_from(["Can you write a chocolate chip cookie recipe?", "exit"])

    log_path = await main.chat(
        log_name="off-topic-guardrail.jsonl",
        input_func=lambda _prompt: next(inputs),
        output_stream=io.StringIO(),
    )

    assert log_path == str(tmp_path / "off-topic-guardrail.jsonl")
    events = [
        json.loads(line)
        for line in tmp_path.joinpath("off-topic-guardrail.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert events[0]["id"] == "off-topic-guardrail"
    assert events[1]["content"] == "Can you write a chocolate chip cookie recipe?"
    assert events[2]["content"] == "I can only help with airline support questions."


@pytest.mark.asyncio
async def test_terminal_chat_ignores_empty_input(monkeypatch, tmp_path):
    monkeypatch.setenv("AIRLINE_SUPPORT_LOG_DIR", str(tmp_path))
    calls = 0

    async def fake_stream_agent_response(_messages):
        nonlocal calls
        calls += 1
        yield "This should not be called."

    monkeypatch.setattr(main, "stream_agent_response", fake_stream_agent_response)
    inputs = input_from(["", "   ", "quit"])

    log_path = await main.chat(input_func=lambda _prompt: next(inputs), output_stream=io.StringIO())

    events = [
        json.loads(line)
        for line in tmp_path.joinpath(log_path).read_text(encoding="utf-8").splitlines()
    ]
    assert [event["type"] for event in events] == ["session"]
    assert calls == 0
