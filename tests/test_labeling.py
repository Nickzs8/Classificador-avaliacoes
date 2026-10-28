"""Unit tests for data sanitization, cleaning, and labeling rules."""

import pandas as pd
import pytest
from src.prepare_data import clean_data, create_label, label_data


@pytest.mark.parametrize(
    "rating, expected",
    [(5, "positive"), (4, "positive"), (2, "negative"), (1, "negative"), (3, None)],
)
def test_create_label(rating, expected):
    """Verifies that ratings 4-5 map to 'positive', 1-2 to 'negative', and 3 to None."""
    assert create_label(rating) == expected


def test_labeling_discards_rating_3():
    """Asserts that neutral ratings (rating 3) are filtered out from the dataset."""
    df = pd.DataFrame({"text": list("abcde"), "rating": [1, 2, 3, 4, 5]})
    result = label_data(df)

    assert len(result) == 4
    assert 3 not in result["rating"].values
    assert dict(zip(result["rating"], result["label"])) == {
        1: "negative",
        2: "negative",
        4: "positive",
        5: "positive",
    }


def test_labeling_does_not_mutate_original_dataframe():
    """Ensures labeling returns a new DataFrame copy without mutating the original input."""
    df = pd.DataFrame({"text": ["a"], "rating": [5]})
    label_data(df)
    assert "label" not in df.columns


def test_clean_removes_nulls_short_texts_and_duplicates():
    """Verifies that cleaning trims whitespace, drops nulls/short texts, and deduplicates."""
    df = pd.DataFrame(
        {
            "text": [
                "  produto excelente, recomendo  ",  # kept (trimmed)
                None,                                 # null text dropped
                "ok",                                 # too short (< 10 chars) dropped
                "produto excelente, recomendo",       # duplicate dropped
                "entrega atrasada demais",            # null rating dropped
                "entrega atrasada demais",            # kept
            ],
            "rating": [5, 5, 5, 5, None, 1],
        }
    )

    result = clean_data(df)

    assert sorted(result["text"]) == [
        "entrega atrasada demais",
        "produto excelente, recomendo",
    ]
