from pathlib import Path

import pandas as pd

RAW_DATA_PATH = Path("data/raw/B2W-Reviews01.csv")
OUTPUT_DATA_PATH = Path("data/reviews.csv")
SAMPLE_SIZE = 20_000
MIN_CHARS = 10
SEED = 42

COLUMNS = {
    "overall_rating": "rating",
    "review_text": "text",
    "product_name": "product",
    "submission_date": "date",
}


def load_raw_data(file_path: Path | str) -> pd.DataFrame:
    """Reads the raw CSV dataset and selects renamed domain columns."""
    df = pd.read_csv(file_path, sep=",", low_memory=False)
    df = df.rename(columns=COLUMNS)
    return df[["text", "rating", "product", "date"]]


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Drops null entries, trims whitespace, removes short texts, and eliminates duplicates."""
    df = df.dropna(subset=["text", "rating"]).copy()
    df["text"] = df["text"].str.strip()
    df = df[df["text"].str.len() >= MIN_CHARS]
    return df.drop_duplicates(subset="text")


def create_label(rating: int | float) -> str | None:
    """Maps rating to binary sentiment: 4/5 -> 'positive', 1/2 -> 'negative', 3 -> None."""
    if rating >= 4:
        return "positive"
    if rating <= 2:
        return "negative"
    return None


def label_data(df: pd.DataFrame) -> pd.DataFrame:
    """Applies sentiment labeling and discards neutral ratings (rating 3)."""
    df = df.copy()
    df["label"] = df["rating"].apply(create_label)
    return df.dropna(subset=["label"])


def sample_data(df: pd.DataFrame, n: int = SAMPLE_SIZE) -> pd.DataFrame:
    """Reproducibly draws a sample of n rows if the dataset exceeds n."""
    if len(df) > n:
        return df.sample(n, random_state=SEED)
    return df


def prepare_data(df: pd.DataFrame) -> pd.DataFrame:
    """Runs the complete preparation pipeline: clean -> label -> sample."""
    return sample_data(label_data(clean_data(df)))


def main():
    df = prepare_data(load_raw_data(RAW_DATA_PATH))
    df.to_csv(OUTPUT_DATA_PATH, index=False)
    print(f"Saved to {OUTPUT_DATA_PATH}: {len(df)} rows")
    print(df["label"].value_counts(normalize=True).round(3))


if __name__ == "__main__":
    main()
