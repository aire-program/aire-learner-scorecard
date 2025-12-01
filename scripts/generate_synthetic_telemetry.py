from __future__ import annotations

import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

# Add project root to path to allow importing src
sys.path.append(str(Path(__file__).parent.parent))

from src.schema import ColumnNames, ResourceIDs, Weakness, WEAKNESS_MAP


def random_timestamp(start: datetime, days: int) -> datetime:
    """Return a timestamp within the window starting at `start` and spanning `days`."""
    return start + timedelta(days=random.uniform(0, days), seconds=random.randint(0, 86400))


def build_event(learner_id: str, start: datetime) -> dict[str, object]:
    # AIRE Standard Schema Fields
    resource_id = random.choice([r.value for r in ResourceIDs])
    
    # Generate scores (1-5 scale)
    clarity_score = random.randint(1, 5)
    context_score = random.randint(1, 5)
    constraints_score = random.randint(1, 5)
    
    # Calculate evaluation score (average)
    evaluation_score = round((clarity_score + context_score + constraints_score) / 3, 2)
    
    # Determine primary weakness based on lowest score
    scores = {
        Weakness.CLARITY.value: clarity_score,
        Weakness.CONTEXT.value: context_score,
        Weakness.CONSTRAINTS.value: constraints_score
    }
    primary_weakness = min(scores, key=scores.get)
    
    # Map weakness to recommended resource
    recommended_resource_id = WEAKNESS_MAP[primary_weakness]
    
    # Other fields
    user_prompt_character_count = random.randint(50, 1500)
    timestamp = random_timestamp(start, days=60).replace(tzinfo=timezone.utc)
    
    return {
        ColumnNames.TIMESTAMP_UTC.value: timestamp.isoformat(),
        ColumnNames.LEARNER_ID.value: learner_id,
        ColumnNames.LEARNER_ROLE.value: "learner",  # Static for this dataset
        ColumnNames.RESOURCE_ID.value: resource_id,
        ColumnNames.USER_PROMPT_CHARACTER_COUNT.value: user_prompt_character_count,
        ColumnNames.CLARITY_SCORE.value: clarity_score,
        ColumnNames.CONTEXT_SCORE.value: context_score,
        ColumnNames.CONSTRAINTS_SCORE.value: constraints_score,
        ColumnNames.EVALUATION_SCORE.value: evaluation_score,
        ColumnNames.PRIMARY_WEAKNESS.value: primary_weakness,
        ColumnNames.RECOMMENDED_RESOURCE_ID.value: recommended_resource_id,
    }


def generate_events(num_learners: int = 50) -> pd.DataFrame:
    random.seed(42)
    start = datetime.now(timezone.utc) - timedelta(days=60)
    learners = [f"L-{i:03d}" for i in range(1, num_learners + 1)]
    rows: list[dict[str, object]] = []
    for learner_id in learners:
        events_for_learner = random.randint(6, 20)
        for _ in range(events_for_learner):
            rows.append(build_event(learner_id, start))
    frame = pd.DataFrame(rows)
    frame.sort_values(ColumnNames.TIMESTAMP_UTC.value, inplace=True)
    frame.reset_index(drop=True, inplace=True)
    return frame


def main() -> None:
    # Output to ../data/ relative to this script
    output_path = Path(__file__).parent.parent / "data" / "aire_telemetry_synthetic.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df = generate_events()
    df.to_csv(output_path, index=False)
    print(f"Generated {len(df)} telemetry rows at {output_path}")


if __name__ == "__main__":
    main()
