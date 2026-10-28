"""Streamlit Web Interface for Customer Review Sentiment Analysis.

Connects to the FastAPI backend service via HTTP using httpx.
"""

import os
import sys
from pathlib import Path

# Ensure the 'src' directory is in sys.path when launched directly via streamlit
SRC_DIR = Path(__file__).resolve().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import httpx
import streamlit as st

try:
    from config import API_PORT
except ImportError:
    API_PORT = int(os.getenv("API_PORT", "8000"))

# Base URL for the FastAPI backend service
API_BASE_URL = os.getenv("API_URL", f"http://127.0.0.1:{API_PORT}")


def check_api_health(api_url: str) -> dict | None:
    """Check backend health status via GET /health."""
    try:
        response = httpx.get(f"{api_url}/health", timeout=2.0)
        if response.status_code == 200:
            return response.json()
        return None
    except (httpx.ConnectError, httpx.TimeoutException):
        return None


def send_review(api_url: str, text: str, product: str | None = None) -> tuple[int, dict]:
    """Submit a customer review to the backend API via POST /reviews.

    Returns a tuple with (status_code, response_payload).
    """
    payload = {"text": text.strip()}
    if product and product.strip():
        payload["product"] = product.strip()

    try:
        response = httpx.post(f"{api_url}/reviews", json=payload, timeout=5.0)
        return response.status_code, response.json()
    except httpx.ConnectError:
        return 503, {"error": "Could not connect to the API server. Make sure FastAPI is running."}
    except httpx.TimeoutException:
        return 504, {"error": "The request timed out while waiting for the API response."}
    except Exception as exc:
        return 500, {"error": f"An unexpected error occurred: {str(exc)}"}


def render_header() -> None:
    """Render page title and description."""
    st.set_page_config(
        page_title="Review Sentiment Classifier",
        page_icon="🛍️",
        layout="centered",
    )
    st.title("Review Sentiment Classifier")


def render_result(result: dict) -> None:
    """Render the sentiment classification result and confidence metrics."""
    sentiment = result.get("sentiment", "").lower()
    confidence = float(result.get("confidence", 0.0))
    review_id = result.get("id", "N/A")
    model_name = result.get("model", "N/A")

    st.subheader("Analysis Result")

    # Sentiment Badge
    col_metric, col_badge = st.columns([1, 1])
    with col_metric:
        st.metric(
            label="Confidence Score",
            value=f"{confidence * 100:.1f}%",
        )
    with col_badge:
        if sentiment == "positive":
            st.success("### Sentiment: **Positive**")
        elif sentiment == "negative":
            st.error("### Sentiment: **Negative**")
        else:
            st.info(f"### Sentiment: **{sentiment.capitalize()}**")

    # Visual Confidence Progress Bar
    st.progress(confidence, text=f"Model certainty: {confidence * 100:.1f}%")

    # Low-confidence Warning Alert (< 60%)
    if confidence < 0.60:
        st.warning(
            "**Low Confidence Prediction (< 60%):** "
            "The text might contain mixed opinions, sarcasm, or ambiguous wording."
        )

    # Technical Details Expander
    with st.expander("Technical Metadata"):
        st.write(f"**Database ID:** `{review_id}`")
        st.write(f"**Inference Model:** `{model_name}`")
        st.json(result)


def main() -> None:
    """Main Streamlit application entrypoint."""
    render_header()
    st.divider()

    # Review Submission Form
    with st.form("review_submission_form", clear_on_submit=False):
        st.markdown("#### Submit a Customer Review")

        review_text = st.text_area(
            label="Review Content",
            placeholder="Type or paste the customer review here (e.g., 'Excelente produto, entrega super rápida!')...",
            height=120,
            help="Review must contain between 3 and 2000 characters.",
        )

        product_name = st.text_input(
            label="Product Name (Optional)",
            placeholder="e.g., Wireless Bluetooth Headphones",
            help="Optional field to identify which product this review belongs to.",
        )

        char_count = len(review_text.strip())
        st.caption(f"Character count: {char_count} / 2000")

        submit_button = st.form_submit_button(
            label="Analyze Sentiment",
            use_container_width=True,
        )

    # Process Form Submission
    if submit_button:
        if char_count < 3:
            st.error("The review must be at least 3 characters long.")
        elif char_count > 2000:
            st.error("The review text exceeds the maximum limit of 2000 characters.")
        else:
            with st.spinner("Classifying sentiment..."):
                status_code, response_data = send_review(
                    api_url=API_BASE_URL,
                    text=review_text,
                    product=product_name if product_name else None,
                )

            if status_code == 201:
                render_result(response_data)
            elif status_code == 422:
                detail = response_data.get("detail", "Validation error.")
                st.error(f"Validation Error: {detail}")
            elif status_code == 503:
                detail = response_data.get("detail", response_data.get("error", "Service unavailable."))
                st.error(f"Backend Unavailable: {detail}")
            else:
                detail = response_data.get("detail", response_data.get("error", "Unknown error."))
                st.error(f"Error {status_code}: {detail}")


if __name__ == "__main__":
    main()
