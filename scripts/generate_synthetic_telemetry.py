from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from src.schema import ColumnNames, ResourceIDs, Weakness, WEAKNESS_MAP

SEED = 42
DAYS_WINDOW = 60
SECONDS_PER_DAY = 86400


def random_timestamp(start: datetime, days: int) -> datetime:
    """Return a random timestamp within the specified window."""
    offset = timedelta(days=random.uniform(0, days), seconds=random.randint(0, SECONDS_PER_DAY))
    return start + offset


def build_event(learner_id: str, start: datetime) -> dict[str, Any]:
    """Generate a single telemetry event."""
    resource_id = random.choice([r.value for r in ResourceIDs])

    clarity_score = random.randint(1, 5)
    context_score = random.randint(1, 5)
    constraints_score = random.randint(1, 5)
    evaluation_score = round((clarity_score + context_score + constraints_score) / 3, 2)

    scores = {
        Weakness.CLARITY.value: clarity_score,
        Weakness.CONTEXT.value: context_score,
        Weakness.CONSTRAINTS.value: constraints_score,
    }
    primary_weakness = min(scores, key=scores.get)  # type: ignore[arg-type]
    recommended_resource_id = WEAKNESS_MAP[primary_weakness]
    timestamp = random_timestamp(start, DAYS_WINDOW).replace(tzinfo=timezone.utc)

    return {
        ColumnNames.TIMESTAMP_UTC.value: timestamp.isoformat(),
        ColumnNames.LEARNER_ID.value: learner_id,
        ColumnNames.LEARNER_ROLE.value: "learner",
        ColumnNames.RESOURCE_ID.value: resource_id,
        ColumnNames.USER_PROMPT_CHARACTER_COUNT.value: random.randint(50, 1500),
        ColumnNames.CLARITY_SCORE.value: clarity_score,
        ColumnNames.CONTEXT_SCORE.value: context_score,
        ColumnNames.CONSTRAINTS_SCORE.value: constraints_score,
        ColumnNames.EVALUATION_SCORE.value: evaluation_score,
        ColumnNames.PRIMARY_WEAKNESS.value: primary_weakness,
        ColumnNames.RECOMMENDED_RESOURCE_ID.value: recommended_resource_id,
    }


def generate_events(num_learners: int = 50) -> pd.DataFrame:
    """Generate synthetic telemetry events for the specified number of learners."""
    random.seed(SEED)
    start = datetime.now(timezone.utc) - timedelta(days=DAYS_WINDOW)
    learners = [f"L-{i:03d}" for i in range(1, num_learners + 1)]

    rows: list[dict[str, Any]] = []
    for learner_id in learners:
        for _ in range(random.randint(6, 20)):
            rows.append(build_event(learner_id, start))

    df = pd.DataFrame(rows)
    df.sort_values(ColumnNames.TIMESTAMP_UTC.value, inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df


def main() -> None:
    """Generate synthetic telemetry data and save to CSV."""
    output_path = Path(__file__).resolve().parent.parent / "data" / "aire_telemetry_synthetic.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df = generate_events()
    df.to_csv(output_path, index=False)
    print(f"Generated {len(df)} telemetry rows at {output_path}")


if __name__ == "__main__":
    main()
