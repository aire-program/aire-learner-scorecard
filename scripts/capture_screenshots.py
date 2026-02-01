from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd
from playwright.sync_api import sync_playwright

DATA_PATH = Path("data/aire_telemetry_synthetic.csv")
OUTPUT_DIR = Path("docs/screesnhots")  # following user-requested path
BASE_URL = "http://127.0.0.1:8501"
VIEWPORT = {"width": 1440, "height": 900}
RENDER_PAUSE_MS = 800  # give charts time to re-render after selection


def iter_learners(path: Path) -> Iterable[str]:
    df = pd.read_csv(path)
    return sorted(df["learner_id"].unique())


def main() -> None:
    learners = list(iter_learners(DATA_PATH))
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport=VIEWPORT)

        page.goto(BASE_URL, wait_until="networkidle")
        page.wait_for_timeout(RENDER_PAUSE_MS)

        for learner_id in learners:
            # select learner
            combobox = page.get_by_role("combobox", name="Select Learner ID")
            combobox.click()
            page.keyboard.type(learner_id)
            option = page.locator("[role='option']", has_text=learner_id).first
            option.wait_for(timeout=10000)
            option.click()

            # let the charts update
            page.wait_for_timeout(RENDER_PAUSE_MS)

            # capture full-height screenshot
            shot_path = OUTPUT_DIR / f"scorecard-{learner_id}.png"
            page.screenshot(path=str(shot_path), full_page=True)

        browser.close()


if __name__ == "__main__":
    main()
