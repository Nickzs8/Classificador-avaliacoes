from pathlib import Path
import pandas as pd
from repository import ReviewRepository

CSV_PATH = Path("data/reviews.csv")
UNLABELED_RATIO = 0.10
SEED = 42


def load_csv(file_path: Path | str) -> pd.DataFrame:
    """Loads reviews CSV and parses date column into datetime format."""
    df = pd.read_csv(file_path)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df


def build_documents(df: pd.DataFrame) -> list[dict]:
    """
    Transforms DataFrame rows into MongoDB BSON documents.
    Randomly assigns 10% of documents to have label=None (unlabeled for batch prediction).
    """
    unlabeled_indices = set(df.sample(frac=UNLABELED_RATIO, random_state=SEED).index)

    documents = []
    for row in df.itertuples():
        doc = {
            "text": row.text,
            "product": None if pd.isna(row.product) else row.product,
            "date": None if pd.isna(row.date) else row.date.to_pydatetime(),
            "rating": int(row.rating),
            "label": None if row.Index in unlabeled_indices else row.label,
            "true_label": row.label,
            "prediction": None,
            "origin": "batch",
        }
        documents.append(doc)
    return documents


def main():
    df = load_csv(CSV_PATH)
    print(f"CSV loaded: {len(df)} rows")

    documents = build_documents(df)

    with ReviewRepository() as repo:
        repo.clear()
        inserted_count = repo.insert_many(documents)
        repo.create_indexes()

        print(f"Inserted: {inserted_count} documents")
        print("Documents by label:", repo.count_by_label())


if __name__ == "__main__":
    main()
