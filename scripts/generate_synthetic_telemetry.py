from __future__ import annotations

import random
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd


def random_timestamp(start: datetime, days: int) -> datetime:
    """Return a timestamp within the window starting at `start` and spanning `days`."""
    return start + timedelta(days=random.uniform(0, days), seconds=random.randint(0, 86400))


def build_event(learner_id: str, start: datetime) -> dict[str, object]:
    # AIRE Standard Schema Fields
    resource_id = random.choice(
        [
            "micro-tutor-01",  # Orientation
            "micro-tutor-02",  # Data Ethics
            "micro-tutor-03",  # Prompt Engineering
            "micro-tutor-04",  # RAG
            "micro-tutor-05",  # Evaluation
        ]
    )
    
    # Generate scores (1-5 scale)
    clarity_score = random.randint(1, 5)
    context_score = random.randint(1, 5)
    constraints_score = random.randint(1, 5)
    
    # Calculate evaluation score (average)
    evaluation_score = round((clarity_score + context_score + constraints_score) / 3, 2)
    
    # Determine primary weakness based on lowest score
    scores = {
        "Clarity": clarity_score,
        "Context": context_score,
        "Constraints": constraints_score
    }
    primary_weakness = min(scores, key=scores.get)
    
    # Map weakness to recommended resource
    weakness_map = {
        "Clarity": "tutorial-clarity-basics",
        "Context": "tutorial-grounding-techniques",
        "Constraints": "tutorial-prompt-constraints"
    }
    recommended_resource_id = weakness_map[primary_weakness]
    
    # Other fields
    user_prompt_character_count = random.randint(50, 1500)
    timestamp = random_timestamp(start, days=60).replace(tzinfo=timezone.utc)
    
    return {
        "timestamp_utc": timestamp.isoformat(),
        "learner_id": learner_id,
        "learner_role": "learner",  # Static for this dataset
        "resource_id": resource_id,
        "user_prompt_character_count": user_prompt_character_count,
        "clarity_score": clarity_score,
        "context_score": context_score,
        "constraints_score": constraints_score,
        "evaluation_score": evaluation_score,
        "primary_weakness": primary_weakness,
        "recommended_resource_id": recommended_resource_id,
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
    frame.sort_values("timestamp_utc", inplace=True)
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
