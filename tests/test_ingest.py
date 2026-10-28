"""Unit tests for MongoDB data ingestion and document schema preparation."""

from datetime import datetime
import pandas as pd
from src.ingest import build_documents, load_csv


def create_sample_dataframe(n: int = 100) -> pd.DataFrame:
    """Generates a synthetic DataFrame simulating cleaned CSV review data."""
    return pd.DataFrame(
        {
            "text": [f"sample text {i}" for i in range(n)],
            "rating": [5 if i % 2 == 0 else 1 for i in range(n)],
            "product": [f"product {i % 3}" for i in range(n)],
            "date": pd.date_range("2018-01-01", periods=n, freq="D"),
            "label": ["positive" if i % 2 == 0 else "negative" for i in range(n)],
        }
    )


def test_approximately_ten_percent_of_documents_have_null_label():
    """Verifies that approximately 10% of ingested documents have label set to None."""
    documents = build_documents(create_sample_dataframe(100))
    unlabeled = [d for d in documents if d["label"] is None]
    assert len(unlabeled) == 10


def test_ground_truth_label_is_always_populated():
    """Asserts that true_label is always populated with 'positive' or 'negative'."""
    for doc in build_documents(create_sample_dataframe()):
        assert doc["true_label"] in ("positive", "negative")


def test_training_label_matches_ground_truth_when_present():
    """Ensures that when label is present, it is identical to true_label."""
    for doc in build_documents(create_sample_dataframe()):
        assert doc["label"] in (None, doc["true_label"])


def test_date_is_converted_to_python_datetime():
    """Verifies that pandas timestamps are converted to native Python datetime objects."""
    documents = build_documents(create_sample_dataframe())
    assert all(type(d["date"]) is datetime for d in documents)


def test_missing_values_are_converted_to_none():
    """Ensures NaN / NaT values are safely cast to Python None for BSON serialization."""
    df = create_sample_dataframe()
    df.loc[0, "date"] = pd.NaT
    df.loc[0, "product"] = None

    doc = build_documents(df)[0]

    assert doc["date"] is None
    assert doc["product"] is None


def test_initial_document_schema_fields():
    """Validates the exact set of keys in the initial BSON document before prediction."""
    doc = build_documents(create_sample_dataframe())[0]

    assert doc["prediction"] is None
    assert isinstance(doc["rating"], int)
    assert set(doc) == {
        "text", "product", "date", "rating", "label", "true_label", "prediction", "origin",
    }


def test_unlabeled_sampling_is_deterministic_and_reproducible():
    """Asserts that the random sampling seed produces identical unlabeling across runs."""
    run_a = [d["label"] is None for d in build_documents(create_sample_dataframe())]
    run_b = [d["label"] is None for d in build_documents(create_sample_dataframe())]
    assert run_a == run_b


def test_load_csv_parses_dates_and_handles_invalid_entries(tmp_path):
    """Verifies CSV parsing correctly parses valid datetimes and converts invalid entries to NaT."""
    file_path = tmp_path / "reviews.csv"
    file_path.write_text(
        "text,rating,product,date,label\n"
        "great product,5,A,2018-03-12 14:05:00,positive\n"
        "terrible quality,1,B,invalid-date,negative\n",
        encoding="utf-8",
    )

    df = load_csv(file_path)

    assert pd.api.types.is_datetime64_any_dtype(df["date"])
    assert pd.isna(df.loc[1, "date"])
