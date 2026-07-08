"""RELAI learning environment for enforcing an exact response signoff."""

from relai import CodeEvaluator
from relai import EvaluationResult
from relai import FixedInput
from relai import FixedTurn
from relai import RELAIEnvironment


REQUIRED_SUFFIX = "please let me know if you have any questions"
TAGS = ["end-to-end", "responses-end-with-exact-signoff"]


def _get_field(value: object, *names: str) -> object | None:
    if isinstance(value, dict):
        for name in names:
            if name in value:
                return value[name]
        return None
    for name in names:
        if hasattr(value, name):
            return getattr(value, name)
    return None


def _assistant_messages(simulation_result: object) -> list[str]:
    transcript = _get_field(simulation_result, "transcript")
    events = _get_field(transcript, "events") if transcript is not None else None
    if events is None:
        events = _get_field(simulation_result, "events")

    messages: list[str] = []
    if isinstance(events, list):
        for event in events:
            event_type = _get_field(event, "type", "event_type", "kind")
            if event_type not in {"agent_message", "assistant_message"}:
                continue
            content = _get_field(event, "content", "message", "text", "assistant_message")
            if content is not None:
                messages.append(str(content))

    if messages:
        return messages

    final_output = _get_field(simulation_result, "final_output", "assistant_message")
    if final_output is None:
        return []
    return [str(final_output)]


def _describe_suffix_failure(message: str) -> str:
    stripped = message.rstrip()
    if REQUIRED_SUFFIX in stripped and not stripped.endswith(REQUIRED_SUFFIX):
        return "extra text after the required closing phrase"
    return "missing the exact required closing phrase at the end"


def evaluate_exact_signoff(simulation_result: object) -> EvaluationResult:
    assistant_messages = _assistant_messages(simulation_result)
    if not assistant_messages:
        return EvaluationResult(
            score=0.0,
            feedback=(
                "No assistant reply was captured, so the required closing suffix "
                f"could not be verified. Expected every reply to end with "
                f"'{REQUIRED_SUFFIX}'."
            ),
        )

    failed_turns: list[str] = []
    passing_turns = 0

    for turn_index, message in enumerate(assistant_messages, start=1):
        if message.rstrip().endswith(REQUIRED_SUFFIX):
            passing_turns += 1
            continue
        tail = message.rstrip()[-120:] or message
        failed_turns.append(
            f"turn {turn_index} { _describe_suffix_failure(message) }; "
            f"expected suffix '{REQUIRED_SUFFIX}', observed ending '{tail}'"
        )

    if not failed_turns:
        return EvaluationResult(
            score=1.0,
            feedback=(
                f"All {len(assistant_messages)} assistant replies ended with the exact "
                f"required suffix '{REQUIRED_SUFFIX}'."
            ),
        )

    score = passing_turns / len(assistant_messages)
    return EvaluationResult(
        score=score,
        feedback=(
            f"{passing_turns} of {len(assistant_messages)} assistant replies used the exact "
            f"required suffix. {'; '.join(failed_turns)}"
        ),
    )


environment = RELAIEnvironment(
    schema_version="relai.learning_environment.v1",
    id="response-signoff",
    name="Required Reply Signoff",
    description="Checks that every airline-support reply ends with the required closing phrase.",
    tags=TAGS,
    input=FixedInput(
        turns=[
            FixedTurn(content="What is the baggage policy for basic economy?"),
            FixedTurn(content="Can you look up booking SKY123?"),
        ]
    ),
    mocks={},
    evaluators=[
        CodeEvaluator(
            id="exact-response-signoff",
            description="Checks that every assistant reply ends with the exact required closing phrase.",
            evaluate=evaluate_exact_signoff,
        )
    ],
)
