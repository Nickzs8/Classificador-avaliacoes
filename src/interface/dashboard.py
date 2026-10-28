import sys
from pathlib import Path

# Ensure the 'src' directory is in sys.path when launched directly via streamlit
SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import streamlit as st
from analytics import load_analytics

st.set_page_config(page_title="Review Sentiment Analytics", layout="wide")
st.title("Customer Review Sentiment Analytics")


@st.cache_data(ttl=60)
def fetch_analytics():
    return load_analytics()


analytics = fetch_analytics()

# Header KPIs
col1, col2, col3 = st.columns(3)
col1.metric("Total Reviews", analytics["total"])

acc = analytics["accuracy_rate"]
if not acc.empty:
    col2.metric("Accuracy Rate (Pending Data)", f"{acc.loc[0, 'accuracy_rate']}%")
    col3.metric("Evaluated Predictions", int(acc.loc[0, "total"]))

# Analytics tables and charts
st.subheader("Top Products with Most Negative Reviews")
st.dataframe(analytics["negative_by_product"], hide_index=True)

st.subheader("Monthly Sentiment Evolution")
if not analytics["monthly_evolution"].empty:
    st.bar_chart(analytics["monthly_evolution"])

st.subheader("Average Confidence by Predicted Class")
st.dataframe(analytics["average_confidence"], hide_index=True)

st.subheader("Recent Submitted Reviews")
if not analytics["recent"].empty:
    st.dataframe(analytics["recent"], hide_index=True, use_container_width=True)
