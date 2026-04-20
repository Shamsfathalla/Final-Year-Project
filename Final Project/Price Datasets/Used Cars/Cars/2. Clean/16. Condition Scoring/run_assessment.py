"""
Batch Car Condition Assessment  (parallel)
==========================================
Reads Final_Used_Cars_Egypt.csv, processes every car's images through the
4-stage pipeline using a multiprocessing pool, and writes a new CSV with
Condition + Score columns.
"""

import os
import logging
import multiprocessing as mp
from pathlib import Path
from functools import partial

import pandas as pd

# ── Config ─────────────────────────────────────────────────────────────
WORKERS = 1            # number of parallel worker processes – tune to your GPU/RAM
BASE_DIR = Path(__file__).resolve().parent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [%(process)d]  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ── Per-worker globals (initialised once per process) ──────────────────
_pipe = None
_calc = None


def _worker_init(base_dir: str):
    """Each pool worker loads its own copy of the pipeline models."""
    global _pipe, _calc
    os.chdir(base_dir)

    from pipeline import CarAssessmentPipeline
    from scoring import calculate_final_score

    _pipe = CarAssessmentPipeline(base_dir)
    _pipe.load_all_models()
    _calc = calculate_final_score
    logger.info("Worker ready.")


def _parse_image_paths(raw: str, base_dir: Path) -> list[str]:
    """Split the semicolon-separated Image Paths cell into absolute paths."""
    if pd.isna(raw) or not raw.strip():
        return []
    paths = [p.strip() for p in raw.split(";") if p.strip()]
    return [
        str(base_dir / p) if not os.path.isabs(p) else p
        for p in paths
    ]


def _process_car(args: tuple) -> tuple[str, float | None]:
    """Process one car (called inside a worker process)."""
    idx, total, raw_paths = args
    img_paths = _parse_image_paths(raw_paths, BASE_DIR)

    if not img_paths:
        logger.info("[%d/%d] No images – skipped.", idx, total)
        return ("N/A", None)

    existing = [p for p in img_paths if os.path.isfile(p)]
    if not existing:
        logger.info("[%d/%d] No valid image files – skipped.", idx, total)
        return ("N/A", None)

    try:
        pipeline_results = _pipe.process_images(existing)
        score_results = _calc(pipeline_results)
        grade = score_results["grade"]
        final_score = score_results["final_score"]
        logger.info(
            "[%d/%d] %s (%.1f/10)  |  %d imgs",
            idx, total, grade, final_score, len(existing),
        )
        return (grade, final_score)
    except Exception as e:
        logger.error("[%d/%d] Pipeline error: %s", idx, total, e)
        return ("Error", None)


def main():
    csv_in = BASE_DIR / "Final_Used_Cars_Egypt.csv"
    csv_out = BASE_DIR / "Final_Used_Cars_Egypt_Assessed.csv"

    logger.info("Reading %s …", csv_in.name)
    df = pd.read_csv(csv_in)
    total = len(df)
    logger.info("Loaded %d rows.  Spawning %d workers …", total, WORKERS)

    # Build argument list: (1-based index, total, raw_path_string)
    tasks = [
        (i + 1, total, row.get("Image Paths", ""))
        for i, row in df.iterrows()
    ]

    with mp.Pool(processes=WORKERS, initializer=_worker_init,
                 initargs=(str(BASE_DIR),)) as pool:
        results = pool.map(_process_car, tasks, chunksize=16)

    conditions, scores = zip(*results) if results else ([], [])
    df["Condition"] = list(conditions)
    df["Condition_Score"] = list(scores)
    df.to_csv(csv_out, index=False)
    logger.info("Saved → %s", csv_out.name)


if __name__ == "__main__":
    mp.freeze_support()          # needed on Windows
    main()
