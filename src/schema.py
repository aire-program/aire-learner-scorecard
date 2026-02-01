from __future__ import annotations

from enum import Enum


class ColumnNames(str, Enum):
    """Column names for telemetry data."""

    TIMESTAMP_UTC = "timestamp_utc"
    LEARNER_ID = "learner_id"
    RESOURCE_ID = "resource_id"
    EVALUATION_SCORE = "evaluation_score"
    CLARITY_SCORE = "clarity_score"
    CONTEXT_SCORE = "context_score"
    CONSTRAINTS_SCORE = "constraints_score"
    PRIMARY_WEAKNESS = "primary_weakness"
    RECOMMENDED_RESOURCE_ID = "recommended_resource_id"
    USER_PROMPT_CHARACTER_COUNT = "user_prompt_character_count"
    LEARNER_ROLE = "learner_role"


class ResourceIDs(str, Enum):
    """Available resource identifiers."""

    MICRO_TUTOR_01 = "micro-tutor-01"
    MICRO_TUTOR_02 = "micro-tutor-02"
    MICRO_TUTOR_03 = "micro-tutor-03"
    MICRO_TUTOR_04 = "micro-tutor-04"
    MICRO_TUTOR_05 = "micro-tutor-05"


class Weakness(str, Enum):
    """Weakness categories."""

    CLARITY = "Clarity"
    CONTEXT = "Context"
    CONSTRAINTS = "Constraints"


WEAKNESS_MAP: dict[str, str] = {
    Weakness.CLARITY.value: "tutorial-clarity-basics",
    Weakness.CONTEXT.value: "tutorial-grounding-techniques",
    Weakness.CONSTRAINTS.value: "tutorial-prompt-constraints",
}

REQUIRED_COLUMNS: list[str] = [
    ColumnNames.TIMESTAMP_UTC.value,
    ColumnNames.LEARNER_ID.value,
    ColumnNames.RESOURCE_ID.value,
    ColumnNames.EVALUATION_SCORE.value,
    ColumnNames.CLARITY_SCORE.value,
    ColumnNames.CONTEXT_SCORE.value,
    ColumnNames.CONSTRAINTS_SCORE.value,
    ColumnNames.PRIMARY_WEAKNESS.value,
    ColumnNames.RECOMMENDED_RESOURCE_ID.value,
    ColumnNames.USER_PROMPT_CHARACTER_COUNT.value,
]
