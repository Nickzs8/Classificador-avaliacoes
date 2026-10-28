import pandas as pd

from repository import ReviewRepository

pd.set_option("display.width", 120)
pd.set_option("display.max_columns", None)


def pivot_monthly_evolution(df: pd.DataFrame) -> pd.DataFrame:
    """Transforms monthly aggregated records into a pivoted DataFrame with months as index."""
    if df.empty:
        return df

    return (
        df.pivot(index="month", columns="sentiment", values="total")
        .fillna(0)
        .astype(int)
    )


def format_recent_reviews(docs: list[dict]) -> pd.DataFrame:
    """Converts a list of BSON review documents into a human-readable display DataFrame."""
    rows = []
    for d in docs:
        pred = d.get("prediction") or {}
        date_val = d.get("date")
        date_str = date_val.strftime("%Y-%m-%d %H:%M") if hasattr(date_val, "strftime") else "N/A"

        sentiment_val = pred.get("sentiment") or d.get("label") or "Pending"
        conf_val = pred.get("confidence")
        conf_str = f"{float(conf_val) * 100:.1f}%" if conf_val is not None else "N/A"

        rows.append(
            {
                "Date": date_str,
                "Product": d.get("product") or "Not specified",
                "Text": d.get("text", ""),
                "Sentiment": sentiment_val,
                "Confidence": conf_str,
                "Origin": d.get("origin", "batch"),
            }
        )
    return pd.DataFrame(rows)


def load_analytics() -> dict:
    """Executes analytical aggregations in MongoDB and returns structured DataFrames."""
    with ReviewRepository() as repo:
        return {
            "total": repo.count(),
            "with_date": repo.count({"date": {"$ne": None}}),
            "negative_by_product": pd.DataFrame(repo.negative_reviews_by_product()),
            "monthly_evolution": pivot_monthly_evolution(pd.DataFrame(repo.monthly_evolution())),
            "average_confidence": pd.DataFrame(repo.average_confidence_by_class()),
            "accuracy_rate": pd.DataFrame(repo.accuracy_rate()),
            "recent": format_recent_reviews(repo.list_recent(limit=10)),
        }


def display_table(title: str, df: pd.DataFrame, index: bool = False):
    """Prints formatted table to terminal stdout."""
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)
    if df.empty:
        print("(no data)")
    else:
        print(df.to_string(index=index))


def verify_totals(analytics: dict):
    """Verifies that monthly evolution aggregates match total documents containing dates."""
    evolution = analytics["monthly_evolution"]
    total_sum = int(evolution.sum().sum()) if not evolution.empty else 0
    print("\n" + "=" * 60)
    print("TOTALS AUDIT")
    print("=" * 60)
    print(f"Monthly sum: {total_sum} | Documents with date: {analytics['with_date']}")


def main():
    analytics = load_analytics()
    print(f"Total documents: {analytics['total']}")

    display_table("TOP PRODUCTS WITH MOST NEGATIVE REVIEWS", analytics["negative_by_product"])
    display_table("MONTHLY SENTIMENT EVOLUTION", analytics["monthly_evolution"], index=True)
    display_table("AVERAGE CONFIDENCE BY PREDICTED CLASS", analytics["average_confidence"])
    display_table("MODEL ACCURACY RATE", analytics["accuracy_rate"])
    verify_totals(analytics)


if __name__ == "__main__":
    main()
