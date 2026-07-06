
import re

from relai import CodeEvaluator, EvaluationResult


TOKEN_LIMIT = 100


def _final_reply(simulation_result) -> str | None:
    final_output = getattr(simulation_result, "final_output", None)
    if final_output is None:
        final_output = getattr(simulation_result, "assistant_message", None)

    if isinstance(final_output, dict):
        final_output = final_output.get("assistant_message", final_output.get("final_output"))

    if final_output is None:
        return None

    return str(final_output).strip()


def _token_count(text: str) -> int:
    return len(re.findall(r"\w+|[^\w\s]", text, flags=re.UNICODE))


def evaluate(simulation_result):
    reply = _final_reply(simulation_result)
    if reply is None:
        return EvaluationResult(
            score=0.0,
            feedback="Expected a final agent reply of 100 tokens or fewer, but no final output was produced.",
        )

    token_count = _token_count(reply)
    if token_count <= TOKEN_LIMIT:
        return EvaluationResult(
            score=1.0,
            feedback=f"The final agent reply was within the 100-token limit at {token_count} tokens.",
        )

    return EvaluationResult(
        score=0.0,
        feedback=(
            "Expected a final agent reply of 100 tokens or fewer, "
            f"but observed {token_count} tokens."
        ),
    )


evaluator = CodeEvaluator(
    id="response-token",
    scope="end-to-end",
    description="Checks whether the final agent reply stays within the response length limit.",
    evaluate=evaluate,
)
