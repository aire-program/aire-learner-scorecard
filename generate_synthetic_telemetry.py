from __future__ import annotations

import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd


def random_timestamp(start: datetime, days: int) -> datetime:
    """Return a timestamp within the window starting at `start` and spanning `days`."""
    return start + timedelta(days=random.uniform(0, days), seconds=random.randint(0, 86400))


def build_event(learner_id: str, start: datetime) -> dict[str, object]:
    session_id = f"S-{uuid.uuid4().hex[:8]}"
    prompt_id = f"P-{random.randint(100, 999)}"
    module = random.choice(
        [
            "Orientation",
            "Data Ethics",
            "Prompt Engineering",
            "Retrieval Augmented Generation",
            "Evaluation",
        ]
    )
    interaction_type = random.choice(["submission", "rubric_scored", "ai_hint", "reflection"])
    rubric_dimension = random.choice(["Clarity", "Accuracy", "Depth", "Tone"])
    rubric_score = random.randint(1, 5)
    recommendation_tag = random.choice(
        ["examples_needed", "revise_prompt", "ground_with_context", "add_sources", "good_progress"]
    )
    ai_feedback = random.choice(
        [
            "Add a concrete example to support your claim.",
            "Ground the answer in the provided context docs.",
            "Clarify the intended audience before responding.",
            "Good iteration—tighten the rubric alignment.",
            "Strengthen citations and list your sources.",
        ]
    )
    input_tokens = random.randint(150, 450)
    output_tokens = random.randint(120, 400)
    latency_ms = random.randint(800, 2500)
    model = random.choice(["gpt-4o", "gpt-4o-mini"])
    timestamp = random_timestamp(start, days=60)
    return {
        "event_id": uuid.uuid4().hex,
        "timestamp": timestamp.isoformat(),
        "learner_id": learner_id,
        "session_id": session_id,
        "module": module,
        "prompt_id": prompt_id,
        "interaction_type": interaction_type,
        "rubric_dimension": rubric_dimension,
        "rubric_score": rubric_score,
        "ai_feedback": ai_feedback,
        "recommendation_tag": recommendation_tag,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "latency_ms": latency_ms,
        "model": model,
    }


def generate_events(num_learners: int = 50) -> pd.DataFrame:
    random.seed(42)
    start = datetime.now() - timedelta(days=60)
    learners = [f"L-{i:03d}" for i in range(1, num_learners + 1)]
    rows: list[dict[str, object]] = []
    for learner_id in learners:
        events_for_learner = random.randint(6, 14)
        for _ in range(events_for_learner):
            rows.append(build_event(learner_id, start))
    frame = pd.DataFrame(rows)
    frame.sort_values("timestamp", inplace=True)
    frame.reset_index(drop=True, inplace=True)
    return frame


def main() -> None:
    output_path = Path(__file__).parent / "data" / "aire_telemetry_synthetic.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df = generate_events()
    df.to_csv(output_path, index=False)
    print(f"Generated {len(df)} telemetry rows at {output_path}")


if __name__ == "__main__":
    main()
