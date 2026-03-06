"""Prediction page UI: single and batch predictions using the model ensemble."""

import pandas as pd
import streamlit as st
from ml.predict import predict_single


def _get_input(train_stats: dict) -> tuple[str, str, str, dict]:
    """Render sidebar inputs and return user selections."""
    st.sidebar.header("Input Selection")

    input_data: dict = {}
    publisher_input = st.sidebar.selectbox("Select Publisher", train_stats["publishers"])
    genre_input = st.sidebar.selectbox("Select Genre", train_stats["genres"])
    platform_input = st.sidebar.selectbox("Select Platform", train_stats["platforms"])
    years = list(range(1970, 2031))
    year_input = st.sidebar.selectbox("Select Release Year", years, index=years.index(2024))
    input_data["Year"] = year_input

    meta_input = st.sidebar.number_input(
        "Select Metacritic Score",
        min_value=0.0,
        max_value=10.0,
        value=train_stats["meta_score_mean"],
        format="%.1f",
    )
    input_data["meta_score"] = meta_input

    user_input = st.sidebar.number_input(
        "Select User Score",
        min_value=0.0,
        max_value=10.0,
        value=train_stats["user_review_mean"],
        format="%.1f",
    )
    input_data["user_review"] = user_input

    return publisher_input, genre_input, platform_input, input_data


def prediction_page() -> None:
    """Render the prediction page."""
    from prediction import (
        load_feature_means,
        load_models,
        load_numerical_transformer,
        load_target_encoder,
    )

    st.title("Video Game Sales Prediction")
    st.caption(
        "Estimate global sales of a video game using our model ensemble"
    )

    try:
        models, meta_learner, version = load_models()
        train_stats = load_feature_means()
        scaler = load_numerical_transformer()
        encoder = load_target_encoder()
    except Exception as e:
        st.error(f"Error loading model: {e}")
        return

    version_label = f"v{version} — {'Stacking Ensemble' if version == 3 else 'Simple Average'}"
    st.info(f"Model: {version_label}")

    # User inputs
    publisher_input, genre_input, platform_input, input_data = _get_input(train_stats)

    if st.sidebar.button("Predict"):
        with st.spinner("Computing prediction..."):
            try:
                pred, uncertainty = predict_single(
                    models,
                    meta_learner,
                    scaler,
                    encoder,
                    train_stats,
                    genre_input,
                    platform_input,
                    publisher_input,
                    input_data["Year"],
                    input_data["meta_score"],
                    input_data["user_review"],
                    version=version,
                )

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Predicted Sales", f"{pred:.4f} M")
                with col2:
                    st.metric("Genre", genre_input)
                with col3:
                    st.metric("Platform", platform_input)

                if uncertainty > 0:
                    st.caption(f"Model uncertainty (inter-model std): {uncertainty:.4f} M")

                export_df = pd.DataFrame(
                    {
                        "Publisher": [publisher_input],
                        "Genre": [genre_input],
                        "Platform": [platform_input],
                        "Year": [input_data["Year"]],
                        "meta_score": [input_data["meta_score"]],
                        "user_review": [input_data["user_review"]],
                        "Predicted_Sales_M": [round(pred, 4)],
                        "Uncertainty_M": [round(uncertainty, 4)],
                    }
                )
                st.download_button(
                    "Download Prediction (CSV)",
                    export_df.to_csv(index=False),
                    file_name="prediction.csv",
                    mime="text/csv",
                )
            except Exception as e:
                st.error(f"Error during prediction: {e}")
    else:
        st.info(
            "Enter the required information in the sidebar "
            "and click 'Predict' to estimate global sales."
        )

    # --- Batch prediction ---
    st.markdown("---")
    st.subheader("Batch Prediction")
    st.write(
        "Upload a CSV file with the following columns: "
        "`Publisher`, `Genre`, `Platform`, `Year`, `meta_score`, `user_review`"
    )
    batch_file = st.file_uploader("CSV File", type="csv", key="batch")

    if batch_file is not None and st.button("Predict Batch"):
        with st.spinner("Running predictions..."):
            try:
                batch_df = pd.read_csv(batch_file)
                required = ["Publisher", "Genre", "Platform", "Year", "meta_score", "user_review"]
                missing = [c for c in required if c not in batch_df.columns]
                if missing:
                    st.error(f"Missing columns: {', '.join(missing)}")
                else:
                    results = []
                    uncertainties = []
                    for _, row in batch_df.iterrows():
                        pred, unc = predict_single(
                            models,
                            meta_learner,
                            scaler,
                            encoder,
                            train_stats,
                            row["Genre"],
                            row["Platform"],
                            row["Publisher"],
                            int(row["Year"]),
                            float(row["meta_score"]),
                            float(row["user_review"]),
                            version=version,
                        )
                        results.append(round(pred, 4))
                        uncertainties.append(round(unc, 4))

                    batch_df["Predicted_Sales_M"] = results
                    batch_df["Uncertainty_M"] = uncertainties
                    st.dataframe(batch_df, use_container_width=True, hide_index=True)
                    st.download_button(
                        "Download Results (CSV)",
                        batch_df.to_csv(index=False),
                        file_name="batch_predictions.csv",
                        mime="text/csv",
                    )
            except Exception as e:
                st.error(f"Error during batch prediction: {e}")

    st.markdown("---")
    st.markdown(
        "<p style='text-align: center; color: #94A3B8;'>"
        "This model is in beta and may make errors. "
        "Consider verifying important information.</p>",
        unsafe_allow_html=True,
    )
