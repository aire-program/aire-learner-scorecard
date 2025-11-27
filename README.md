# AIRE Learner Scorecard

Personalized learner analytics dashboard for the AIRE Program, providing individual-level insights, rubric-based prompt feedback trends, and AI-generated learning recommendations. Public release with synthetic data and reproducible Streamlit code.

## Personalized Learner Analytics (Public Version)

This public build centers learner-facing insights by surfacing rubric trends, engagement patterns, and AI coaching tips designed to improve prompt quality and grounding. It mirrors the AIRE Impact Dashboard priorities—clarity, accuracy, depth, and ethical use—so learners see how their work aligns to program outcomes. All shared artifacts use synthetic telemetry to keep data private while preserving realistic patterns for reproducibility.

## Setup & Usage

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Generate Synthetic Data**:
    ```bash
    python3 scripts/generate_synthetic_telemetry.py
    ```
    This will create `data/aire_telemetry_synthetic.csv`.

3.  **Run the Dashboard**:
    ```bash
    streamlit run app.py
    ```

## Data Schema

The dashboard consumes `data/aire_telemetry_synthetic.csv` which adheres to the AIRE standard schema, including:
- `timestamp_utc`
- `learner_id`
- `resource_id`
- `evaluation_score` (1-5)
- `primary_weakness`
- `recommended_resource_id`
