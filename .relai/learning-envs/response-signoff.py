"""RELAI learning environment generated from a sandboxed log/feedback pass."""

from relai import (
    CodeEvaluator,
    EvaluationResult,
    FixedInput,
    FixedTurn,
    RELAIEnvironment,
)


REQUIRED_SIGNOFF = "please let me know if you have any questions"
TAGS = ["end-to-end", "reply-ends-with-required-signoff"]


def mock_change_seat(*args, **kwargs):
    """Mock for airline_support.agent:change_seat: Seat changes mutate the shared in-memory demo BOOKINGS state, so mock them when a scenario does not need the mutation itself."""
    return None


def check_required_signoff(simulation_result):
    final_output = getattr(simulation_result, "final_output", None)
    if final_output is None:
        return EvaluationResult(
            score=0.0,
            feedback=(
                "Expected a final agent reply ending exactly with "
                f"'{REQUIRED_SIGNOFF}', but no final output was produced."
            ),
        )

    reply = str(final_output).strip()
    if reply.endswith(REQUIRED_SIGNOFF):
        return EvaluationResult(
            score=1.0,
            feedback="The final agent reply ends with the required closing phrase.",
        )

    if REQUIRED_SIGNOFF in reply:
        trailing_text = reply[reply.rfind(REQUIRED_SIGNOFF) + len(REQUIRED_SIGNOFF) :]
        return EvaluationResult(
            score=0.0,
            feedback=(
                "The final agent reply included the required closing phrase but did not end "
                f"with it exactly. Expected suffix: '{REQUIRED_SIGNOFF}'. "
                f"Observed trailing text after that phrase: {trailing_text!r}."
            ),
        )

    return EvaluationResult(
        score=0.0,
        feedback=(
            f"Expected the final agent reply to end exactly with '{REQUIRED_SIGNOFF}', "
            f"but observed final reply: {reply!r}."
        ),
    )


environment = RELAIEnvironment(
    schema_version="relai.learning_environment.v1",
    id="response-signoff",
    name="Required Response Signoff",
    description="Tests that a routine airline-support reply ends with the required closing phrase.",
    tags=TAGS,
    input=FixedInput(
        turns=[
            FixedTurn(content="What is the baggage policy for a standard ticket?"),
        ]
    ),
    mocks={
        "airline_support.agent:change_seat": mock_change_seat,
    },
    evaluators=[
        CodeEvaluator(
            id="required-signoff",
            description="Checks that the final reply ends exactly with the required closing phrase.",
            evaluate=check_required_signoff,
        ),
    ],
)
