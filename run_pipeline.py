"""
Machine Learning Pipeline Orchestration Script (V1 Batch).

Executes in sequence the initialization, training, and inference stages of the project:
1. src/prepare_data.py - Data cleaning, business rules, and sentiment labeling from raw CSV.
2. src/ingest.py       - BSON ingestion and index provisioning in MongoDB (requires active Docker container).
3. src/train.py        - TF-IDF + Logistic Regression training and .joblib artifact export.
4. src/predict.py      - Batch inference on pending unlabeled reviews and accuracy evaluation.
"""

import subprocess
import sys
import time
from pathlib import Path


def verify_mongodb_active() -> bool:
    """Verifies that the MongoDB container is running via Docker Compose before database stages."""
    print(f"\n{'='*70}")
    print("[INFO] Checking MongoDB container status via Docker Compose...")
    print(f"{'='*70}")

    try:
        res = subprocess.run(
            ["docker", "compose", "ps", "--status", "running", "-q"],
            capture_output=True,
            text=True,
            check=False,
        )

        if res.returncode == 0 and res.stdout.strip():
            print("[OK] MongoDB container is active and running.")
            return True

        print("[ERROR] MongoDB container is not running.")
        print("Start the database before running the pipeline using:")
        print("       docker compose up -d")
        return False

    except FileNotFoundError:
        print("\n[ERROR] Command 'docker' was not found in system PATH.")
        print("Please ensure Docker is installed and accessible.")
        return False
    except Exception as e:
        print(f"\n[ERROR] Unexpected error while verifying Docker: {e}")
        return False


STAGES = [
    {
        "name": "1/4: Data Preparation",
        "script": "src/prepare_data.py",
        "description": "Reads data/raw/B2W-Reviews01.csv, cleans, labels, and generates data/reviews.csv",
        "requires_docker": False,
    },
    {
        "name": "2/4: MongoDB Ingestion",
        "script": "src/ingest.py",
        "description": "Loads data/reviews.csv, converts into BSON, and inserts into MongoDB collection",
        "requires_docker": True,
    },
    {
        "name": "3/4: Model Training",
        "script": "src/train.py",
        "description": "Trains classifier (TF-IDF + LogisticRegression) and saves .joblib model",
        "requires_docker": True,
    },
    {
        "name": "4/4: Batch Prediction & Evaluation",
        "script": "src/predict.py",
        "description": "Classifies pending unlabeled reviews in MongoDB and evaluates accuracy against ground truth",
        "requires_docker": True,
    },
]

# Backward compatibility alias
ETAPAS = STAGES


def execute_stage(stage: dict) -> bool:
    script_path = Path(stage["script"])
    if not script_path.exists():
        print(f"\n[ERROR] Script not found: {script_path}")
        return False

    if stage.get("requires_docker"):
        if not verify_mongodb_active():
            print(f"\n[ERROR] Failed to validate MongoDB for stage '{stage['name']}'.")
            return False

    print(f"\n{'='*70}")
    print(f"[STAGE {stage['name']}]")
    print(f"Description: {stage['description']}")
    print(f"Command:     {sys.executable} {stage['script']}")
    print(f"{'='*70}\n")

    start_time = time.time()
    result = subprocess.run([sys.executable, str(script_path)])
    duration = time.time() - start_time

    if result.returncode != 0:
        print(f"\n[ERROR] Stage '{stage['name']}' failed with exit code {result.returncode}.")
        if stage.get("requires_docker"):
            print("[TIP] If this is a database connection error, check:")
            print("      docker compose ps")
            print("      docker compose logs mongo")
        return False

    print(f"\n[OK] Completed in {duration:.2f}s")
    return True


def main():
    print("=" * 70)
    print("INITIALIZING MACHINE LEARNING PIPELINE")
    print("=" * 70)

    raw_csv = Path("data/raw/B2W-Reviews01.csv")
    reviews_csv = Path("data/reviews.csv")
    if not raw_csv.exists() and not reviews_csv.exists():
        print("\n[WARNING] No dataset found in 'data/raw/' or 'data/'.")
        print("Please ensure 'data/raw/B2W-Reviews01.csv' or 'data/reviews.csv' is present.")
        sys.exit(1)

    total_start = time.time()

    for stage in STAGES:
        success = execute_stage(stage)
        if not success:
            print("\n[ERROR] Pipeline aborted due to failure in previous stage.")
            sys.exit(1)

    total_elapsed = time.time() - total_start
    print("\n" + "=" * 70)
    print(f"[SUCCESS] Pipeline executed successfully in {total_elapsed:.2f}s.")
    print("=" * 70)


if __name__ == "__main__":
    main()
