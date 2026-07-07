from __future__ import annotations

import asyncio
from collections.abc import Callable
import sys
from typing import TextIO

from dotenv import load_dotenv

from airline_support.agent import stream_agent_response
from airline_support.sessions import append_message, create_session, read_messages, session_path


EXIT_COMMANDS = {"exit", "quit", "q"}


async def chat(
    input_func: Callable[[str], str] = input,
    output_stream: TextIO | None = None,
) -> str:
    load_dotenv()
    output = output_stream or sys.stdout
    session = create_session()
    log_path = session_path(session.id)

    print("SkyServe Airline Support", file=output)
    print(f"Session: {session.id}", file=output)
    print(f"Log: {log_path}", file=output)
    print("Type exit, quit, or q to end the chat.", file=output)

    while True:
        try:
            user_text = input_func("\nYou: ")
        except EOFError:
            print(file=output)
            break

        user_text = user_text.strip()
        if not user_text:
            continue
        if user_text.lower() in EXIT_COMMANDS:
            break

        append_message(session.id, "user", user_text)
        messages = read_messages(session.id)
        chunks: list[str] = []

        print("\nAgent: ", end="", file=output, flush=True)
        async for delta in stream_agent_response(messages):
            chunks.append(delta)
            print(delta, end="", file=output, flush=True)
        print(file=output)

        assistant_text = "".join(chunks).strip()
        if assistant_text:
            append_message(session.id, "assistant", assistant_text)

    print(f"\nSaved conversation log to {log_path}", file=output)
    return str(log_path)


def run() -> None:
    asyncio.run(chat())


def main() -> None:
    run()


if __name__ == "__main__":
    main()
