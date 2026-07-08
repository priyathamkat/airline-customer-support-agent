import importlib
import re

from relai import AgentTarget
from relai import CodeEvaluator
from relai import EvaluationResult
from relai import FixedInput
from relai import FixedTurn
from relai import RELAIBenchmark
from relai import RELAIEnvironment
from relai import StoredBenchmarkCsv


BENCHMARK_ID = "airline-support-suite"
BENCHMARK_NAME = "airline-support-suite"
DATASET_REF_ID = "7b644c8b-ef0c-4991-8d3a-d58d8824d579"
REQUIRED_COLUMNS = ["sample_id", "input", "expected_behavior", "rubric"]
SCOPE_TAGS = ["end-to-end"]

BOOKING_CODE_PATTERN = re.compile(r"\b[A-Z]{3}\d{3}\b")
SEAT_PATTERN = re.compile(r"\b\d{1,2}[A-F]\b")
MONEY_PATTERN = re.compile(r"(?i)(?:\$\s*\d+(?:\.\d+)?|\b\d+(?:\.\d+)?\s*(?:usd|dollars?)\b)")

ROW_NAMES = {
    "refund-amount-boundary": "No Invented Refund Amount",
    "booking-lookup-sky123": "Booking Lookup Uses Live Details",
    "seat-change-sky123": "Seat Change Confirms Update",
    "unknown-booking-code": "Unknown Booking Stays Unknown",
}


def _get_field(value, *names):
    if isinstance(value, dict):
        for name in names:
            if name in value:
                return value[name]
        return None
    for name in names:
        if hasattr(value, name):
            return getattr(value, name)
    return None


def _assistant_messages(simulation_result):
    transcript = _get_field(simulation_result, "transcript")
    events = _get_field(transcript, "events") if transcript is not None else None
    if events is None:
        events = _get_field(simulation_result, "events")

    messages = []
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


def _last_assistant_message(simulation_result):
    messages = _assistant_messages(simulation_result)
    if not messages:
        return None
    return messages[-1]


def _normalize_text(value):
    return " ".join(str(value).strip().lower().split())


def _extract_booking_code(text):
    match = BOOKING_CODE_PATTERN.search(str(text).upper())
    if match is None:
        return None
    return match.group(0)


def _extract_requested_seat(text):
    matches = SEAT_PATTERN.findall(str(text).upper())
    if not matches:
        return None
    return matches[-1]


def _load_live_booking(confirmation_code):
    try:
        module = importlib.import_module("airline_support.agent")
    except Exception:
        return None

    bookings = getattr(module, "BOOKINGS", None)
    if not isinstance(bookings, dict):
        return None

    booking = bookings.get(confirmation_code)
    if not isinstance(booking, dict):
        return None
    return {str(key): str(value) for key, value in booking.items()}


def _score_from_checks(passed_checks, total_checks):
    if total_checks <= 0:
        return 0.0
    return passed_checks / total_checks


def _missing_response_feedback(expected_behavior):
    return EvaluationResult(
        score=0.0,
        feedback=(
            "No assistant reply was captured. Expected behavior: "
            f"{expected_behavior}"
        ),
    )


def _evaluate_refund_amount_boundary(simulation_result, row_fields):
    response = _last_assistant_message(simulation_result)
    if response is None:
        return _missing_response_feedback(row_fields["expected_behavior"])

    normalized = _normalize_text(response)
    failures = []
    passed_checks = 0

    if MONEY_PATTERN.search(response) is None and "guaranteed refund" not in normalized:
        passed_checks += 1
    else:
        failures.append(
            "wrong content: the reply gave a concrete refund amount or guarantee, "
            f"but it should have stayed non-committal. Observed reply: {response!r}"
        )

    if ("depend" in normalized or "eligib" in normalized) and (
        "fare" in normalized or "booking" in normalized or "ticket" in normalized
    ):
        passed_checks += 1
    else:
        failures.append(
            "missing required explanation: the reply should say refund eligibility or amount "
            "depends on fare rules and booking details."
        )

    if (
        "confirmation code" in normalized
        or "booking code" in normalized
        or "review your booking" in normalized
        or "look up your booking" in normalized
        or "check your booking" in normalized
    ):
        passed_checks += 1
    else:
        failures.append(
            "missing next step: the reply should offer to review the booking with a confirmation code."
        )

    score = _score_from_checks(passed_checks, 3)
    if score == 1.0:
        return EvaluationResult(
            score=1.0,
            feedback=(
                "The reply avoided a refund amount, explained that eligibility depends on fare or booking details, "
                "and offered a booking-review next step."
            ),
        )
    return EvaluationResult(
        score=score,
        feedback="; ".join(failures),
    )


def _evaluate_booking_lookup(simulation_result, row_fields):
    response = _last_assistant_message(simulation_result)
    if response is None:
        return _missing_response_feedback(row_fields["expected_behavior"])

    input_text = row_fields["input"]
    confirmation_code = _extract_booking_code(input_text) or "SKY123"
    booking = _load_live_booking(confirmation_code)
    normalized = _normalize_text(response)
    failures = []
    passed_checks = 0

    if booking is None:
        return EvaluationResult(
            score=0.0,
            feedback=(
                f"Benchmark setup could not load live booking details for {confirmation_code}, "
                "so the lookup response could not be checked safely."
            ),
        )

    expected_fragments = {
        "passenger": booking["passenger"],
        "route": booking["route"],
        "departure": booking["departure"],
        "seat": booking["seat"],
        "status": booking["status"],
    }
    missing_labels = [
        label
        for label, value in expected_fragments.items()
        if _normalize_text(value) not in normalized
    ]
    if not missing_labels:
        passed_checks += 1
    else:
        failures.append(
            "missing required booking details: expected "
            f"{expected_fragments!r}, but the reply omitted {', '.join(missing_labels)}. "
            f"Observed reply: {response!r}"
        )

    if "no booking" not in normalized and "not found" not in normalized:
        passed_checks += 1
    else:
        failures.append(
            f"wrong content: the reply treated valid confirmation code {confirmation_code} as missing."
        )

    asks_for_code = "confirmation code" in normalized and any(
        phrase in normalized
        for phrase in (
            "need",
            "provide",
            "share",
            "what is",
            "please send",
            "can you provide",
        )
    )
    if not asks_for_code:
        passed_checks += 1
    else:
        failures.append(
            f"wrong content: the reply asked for an extra confirmation code even though {confirmation_code} was already provided."
        )

    score = _score_from_checks(passed_checks, 3)
    if score == 1.0:
        return EvaluationResult(
            score=1.0,
            feedback=(
                f"The reply used confirmation code {confirmation_code} and reported the live booking details "
                f"for {booking['passenger']} without asking for redundant information."
            ),
        )
    return EvaluationResult(score=score, feedback="; ".join(failures))


def _evaluate_seat_change(simulation_result, row_fields):
    response = _last_assistant_message(simulation_result)
    if response is None:
        return _missing_response_feedback(row_fields["expected_behavior"])

    input_text = row_fields["input"]
    confirmation_code = _extract_booking_code(input_text) or "SKY123"
    requested_seat = _extract_requested_seat(input_text) or "14C"
    normalized = _normalize_text(response)
    failures = []
    passed_checks = 0

    if requested_seat.lower() in normalized:
        passed_checks += 1
    else:
        failures.append(
            f"missing required text: the reply should confirm seat {requested_seat}, but that seat was not mentioned. "
            f"Observed reply: {response!r}"
        )

    if confirmation_code.lower() in normalized:
        passed_checks += 1
    else:
        failures.append(
            f"missing required text: the reply should confirm the update for booking {confirmation_code}."
        )

    if any(term in normalized for term in ("updated", "changed", "confirm", "moved", "switched")):
        passed_checks += 1
    else:
        failures.append(
            "missing update confirmation: the reply should clearly say the seat was changed or updated."
        )

    asks_for_code = "confirmation code" in normalized and any(
        phrase in normalized
        for phrase in ("need", "provide", "share", "what is", "valid confirmation code")
    )
    if not asks_for_code:
        passed_checks += 1
    else:
        failures.append(
            f"wrong content: the reply asked for or rejected the confirmation code even though {confirmation_code} was already supplied."
        )

    score = _score_from_checks(passed_checks, 4)
    if score == 1.0:
        return EvaluationResult(
            score=1.0,
            feedback=(
                f"The reply accepted confirmation code {confirmation_code}, confirmed seat {requested_seat}, "
                "and clearly stated that the update was completed."
            ),
        )
    return EvaluationResult(score=score, feedback="; ".join(failures))


def _evaluate_unknown_booking(simulation_result, row_fields):
    response = _last_assistant_message(simulation_result)
    if response is None:
        return _missing_response_feedback(row_fields["expected_behavior"])

    input_text = row_fields["input"]
    confirmation_code = _extract_booking_code(input_text) or "ZZZ999"
    normalized = _normalize_text(response)
    failures = []
    passed_checks = 0

    if any(
        phrase in normalized
        for phrase in (
            "no booking was found",
            "no booking found",
            "not found",
            "couldn't find",
            "cannot find",
            "no record",
        )
    ):
        passed_checks += 1
    else:
        failures.append(
            f"wrong content: the reply should clearly report that booking {confirmation_code} was not found. "
            f"Observed reply: {response!r}"
        )

    fabricated_details = [
        detail
        for detail in (
            "maya chen",
            "noah patel",
            "jfk to sfo",
            "lax to sea",
            "12a",
            "18c",
            "confirmed",
        )
        if detail in normalized
    ]
    if not fabricated_details:
        passed_checks += 1
    else:
        failures.append(
            "wrong content: the reply invented booking-specific details for an unknown confirmation code. "
            f"Observed fabricated details: {', '.join(fabricated_details)}."
        )

    score = _score_from_checks(passed_checks, 2)
    if score == 1.0:
        return EvaluationResult(
            score=1.0,
            feedback=(
                f"The reply correctly reported that booking {confirmation_code} was not found and did not fabricate passenger or itinerary details."
            ),
        )
    return EvaluationResult(score=score, feedback="; ".join(failures))


def _evaluate_row(simulation_result, row_fields):
    sample_id = row_fields["sample_id"]
    if sample_id == "refund-amount-boundary":
        return _evaluate_refund_amount_boundary(simulation_result, row_fields)
    if sample_id == "booking-lookup-sky123":
        return _evaluate_booking_lookup(simulation_result, row_fields)
    if sample_id == "seat-change-sky123":
        return _evaluate_seat_change(simulation_result, row_fields)
    if sample_id == "unknown-booking-code":
        return _evaluate_unknown_booking(simulation_result, row_fields)
    return EvaluationResult(
        score=0.0,
        feedback=f"Unsupported benchmark row {sample_id!r}.",
    )


def _build_row_evaluator(row_fields):
    sample_id = row_fields["sample_id"]

    def evaluate(simulation_result):
        return _evaluate_row(simulation_result, row_fields)

    return CodeEvaluator(
        id=f"{sample_id}-behavior",
        description=row_fields["rubric"],
        evaluate=evaluate,
    )


def build_environment(row_fields, sample_index):
    sample_id = row_fields["sample_id"]
    return RELAIEnvironment(
        schema_version="relai.learning_environment.v1",
        id=sample_id,
        name=ROW_NAMES.get(sample_id, sample_id.replace("-", " ").title()),
        description=row_fields["expected_behavior"],
        tags=list(SCOPE_TAGS),
        target=AgentTarget(),
        input=FixedInput(turns=[FixedTurn(content=row_fields["input"])]),
        mocks={},
        evaluators=[_build_row_evaluator(row_fields)],
    )


benchmark = RELAIBenchmark(
    schema_version="relai.benchmark.v1",
    id=BENCHMARK_ID,
    name=BENCHMARK_NAME,
    description="Regression suite for airline support refund, booking lookup, seat-change, and not-found behaviors.",
    dataset_ref=StoredBenchmarkCsv(id=DATASET_REF_ID),
    required_columns=REQUIRED_COLUMNS,
    build_environment=build_environment,
)
