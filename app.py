import joblib
from pathlib import Path

import pandas as pd
import streamlit as st


st.set_page_config(page_title="Sydney House Price Predictor", page_icon="🏠")

MODEL_PATH = Path(__file__).with_name("syd_house_price_model.joblib")
bundle = joblib.load(MODEL_PATH)
model = bundle["model"]
feature_columns = bundle["feature_columns"]
category_values = bundle["category_values"]
numeric_defaults = bundle["numeric_defaults"]


def prepare_features(data):
    """Create the same features used when the model was trained."""
    prepared = data.copy()

    # Sold Month can be supplied directly or calculated from Sold Date.
    if "Sold Month" not in prepared.columns and "Sold Date" in prepared.columns:
        sold_dates = pd.to_datetime(prepared["Sold Date"], errors="coerce")
        prepared["Sold Month"] = sold_dates.dt.month

    # Total Rooms is calculated from the two room-count columns.
    if "Total Rooms" not in prepared.columns:
        if {"Bedrooms", "Bathrooms"}.issubset(prepared.columns):
            prepared["Total Rooms"] = (
                pd.to_numeric(prepared["Bedrooms"], errors="coerce").fillna(0)
                + pd.to_numeric(prepared["Bathrooms"], errors="coerce").fillna(0)
            )

    missing = [column for column in feature_columns if column not in prepared.columns]
    if missing:
        raise ValueError("Missing columns: " + ", ".join(missing))

    return prepared[feature_columns]


st.title("Sydney House Price Predictor")
st.write(
    "This application gives an estimated sale price using the Random Forest model "
    "developed from the collected Mosman, Parramatta and Penrith data."
)

manual_tab, upload_tab = st.tabs(["Enter one property", "Upload CSV"])

with manual_tab:
    with st.form("property_form"):
        suburb = st.selectbox("Suburb", category_values["Suburb"])
        property_type = st.selectbox("Property type", category_values["Property Type"])
        state = st.selectbox("State", category_values["State"])

        bedrooms = st.number_input("Bedrooms", min_value=0.0, max_value=10.0, value=3.0, step=1.0)
        bathrooms = st.number_input("Bathrooms", min_value=0.0, max_value=10.0, value=2.0, step=1.0)
        car_spaces = st.number_input("Car spaces", min_value=0.0, max_value=10.0, value=1.0, step=1.0)
        has_parking = st.selectbox("Has parking", ["Yes", "No"])
        has_pool = st.selectbox("Has pool", ["No", "Yes"])
        distance = st.number_input(
            "Approximate distance to Sydney CBD (km)",
            min_value=0.0,
            max_value=100.0,
            value=float(numeric_defaults["Approx. Distance to Sydney CBD (km)"]),
            step=1.0
        )
        sold_month = st.slider("Sold month", 1, 12, 9)
        submitted = st.form_submit_button("Predict sale price")

    if submitted:
        property_data = pd.DataFrame([{
            "Suburb": suburb,
            "State": state,
            "Property Type": property_type,
            "Bedrooms": bedrooms,
            "Bathrooms": bathrooms,
            "Has Parking": 1 if has_parking == "Yes" else 0,
            "Car Spaces": car_spaces,
            "Approx. Distance to Sydney CBD (km)": distance,
            "Has Pool": 1 if has_pool == "Yes" else 0,
            "Sold Month": sold_month,
            "Total Rooms": bedrooms + bathrooms,
        }])

        prediction = model.predict(prepare_features(property_data))[0]
        st.metric("Estimated sale price", f"${prediction:,.0f}")
        st.caption(
            "This is a model estimate based on a small dataset. It should not be treated "
            "as a professional property valuation."
        )

with upload_tab:
    st.write("Upload a CSV file containing the model input columns shown below.")
    st.code(", ".join(feature_columns))
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

    if uploaded_file is not None:
        try:
            uploaded_data = pd.read_csv(uploaded_file)
            uploaded_features = prepare_features(uploaded_data)
            results = uploaded_data.copy()
            results["Predicted Sale Price (AUD)"] = model.predict(uploaded_features)

            st.success(f"Predictions created for {len(results)} properties.")
            st.dataframe(results, use_container_width=True)
            st.download_button(
                "Download predictions",
                results.to_csv(index=False).encode("utf-8"),
                file_name="property_price_predictions.csv",
                mime="text/csv"
            )
        except Exception as error:
            st.error(f"The predictions could not be created. {error}")

st.divider()
st.caption(
    f"Model: {bundle['model_name']} | Mean cross-validation RMSE: "
    f"${bundle['validation_rmse']:,.0f}"
)
