from relai import FixedInput, FixedTurn, RELAIEnvironment


environment = RELAIEnvironment(
    schema_version="relai.learning_environment.v1",
    id="relai-init-smoke",
    name="RELAI init smoke",
    description="Checks that the generated simulator can run one representative turn.",
    input=FixedInput(
        turns=[
            FixedTurn(
                content=(
                    "Please look up booking SKY123 and tell me the passenger, route, "
                    "departure time, seat, and status."
                )
            ),
        ],
    ),
    mocks={},
    evaluators=[],
)
