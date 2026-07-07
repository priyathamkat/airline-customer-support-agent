# RELAI Airline Support Agent

A terminal airline customer support agent built with the OpenAI Agents SDK for Python.

The agent can help with demo booking lookups, baggage policy, seat changes, and flight-change guidance. Each terminal conversation is saved as JSONL under `logs/` so it can be used with RELAI learning loops.

## Prerequisites

- Python 3.11+
- `uv`
- `OPENAI_API_KEY` in your environment, or ready to paste when prompted

## Start the Agent

Run the launcher from the repository root:

```sh
./start.sh
```

The script prompts for your OpenAI API key when needed, saves it to the ignored `.env` file, installs Python dependencies, and starts a terminal chat session.

You can also run the CLI directly:

```sh
uv sync
export OPENAI_API_KEY=sk-...
uv run airline-support
```

Type `exit`, `quit`, or `q` to end the chat. Each run creates a new session log and prints the saved path.

## Local Logs

Each chat session is saved as JSONL under `logs/`:

```text
logs/session-<id>.jsonl
```

Session files are ignored by Git. The log format is compatible with RELAI log-based learning environments.

## Learning Environment from Log + Feedback

Capture a real, undesirable behavior in a terminal session, then turn that log plus your feedback into a learning environment and optimize the unwanted behavior away.

Run this prompt in terminal chat:

```text
Can you write a chocolate chip cookie recipe?
```

The agent saves the chat as `logs/<session-id>.jsonl`.

```sh
relai learning-env create \
  --log-file logs/<session-id>.jsonl \
  --feedback "The agent should not answer off-topic, non-airline questions. It should politely say it can only help with airline booking, baggage, seat, and flight-change questions." \
  --name off-topic-guardrail
```

Then continue with:

```sh
relai simulate \
  --learning-envs off-topic-guardrail \
  --result-json .relai/runs/off-topic-guardrail-simulation.json
```

```sh
relai optimize
```

## Benchmark

Register the reusable CSV benchmark, then run simulation and optimization against it.

```sh
relai benchmark register \
  --csv benchmarks/airline_support_benchmark.csv \
  --name airline-support-suite
```

```sh
relai simulate \
  --benchmarks airline-support-suite \
  --result-json .relai/runs/airline-support-suite-simulation.json
```

```sh
relai optimize
```

## Checks

```sh
uv run pytest
```
