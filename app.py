from pathlib import Path

import pandas as pd
import streamlit as st
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


st.set_page_config(page_title="Sydney House Price Predictor", page_icon="🏠")

DATA_PATH = Path(__file__).with_name("Sydney_Sold_Property_Dataset (1).xlsx")


@st.cache_resource
def train_deployment_model():
    """Train the selected model using the same steps as the notebook."""
    data = pd.read_excel(DATA_PATH, sheet_name="Sold Properties")
    data.columns = data.columns.str.strip()
    data = data.rename(columns={
        "Sold Price (AUD) - TARGET": "Sold Price (AUD)",
        "Sold Price (AUD) - Target": "Sold Price (AUD)",
    })

    # Create the two features used in the final model.
    data["Sold Date"] = pd.to_datetime(data["Sold Date"], errors="coerce")
    data["Sold Month"] = data["Sold Date"].dt.month
    data["Total Rooms"] = (
        data["Bedrooms"].fillna(0) + data["Bathrooms"].fillna(0)
    )

    # These columns are identifiers, source details or highly incomplete fields.
    drop_columns = [
        "ID",
        "Property ID",
        "Address",
        "Listing Source URL",
        "Results Page URL",
        "Sold Date",
        "Postcode",
        "Year Built",
        "Land Size (m²)",
        "Building Size (m²)",
    ]

    target = "Sold Price (AUD)"
    features = data.drop(columns=[target] + drop_columns, errors="ignore")
    prices = data[target]

    categorical_columns = features.select_dtypes(
        include=["object", "category", "bool"]
    ).columns.tolist()
    numerical_columns = features.select_dtypes(include=["number"]).columns.tolist()

    numerical_pipeline = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])

    categorical_pipeline = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore", drop="first")),
    ])

    preprocessor = ColumnTransformer(transformers=[
        ("num", numerical_pipeline, numerical_columns),
        ("cat", categorical_pipeline, categorical_columns),
    ])

    model = Pipeline(steps=[
        ("preprocessor", preprocessor),
        ("model", RandomForestRegressor(
            n_estimators=300,
            max_depth=5,
            min_samples_leaf=2,
            random_state=42,
        )),
    ])

    # Fit once when the cloud application starts.
    model.fit(features, prices)

    category_values = {
        column: sorted(features[column].dropna().astype(str).unique().tolist())
        for column in categorical_columns
    }
    numeric_defaults = {
        column: float(pd.to_numeric(features[column], errors="coerce").median())
        for column in numerical_columns
    }

    return model, features.columns.tolist(), category_values, numeric_defaults


model, feature_columns, category_values, numeric_defaults = train_deployment_model()


def prepare_features(data):
    """Create the same features used when the model was trained."""
    prepared = data.copy()

    if "Sold Month" not in prepared.columns and "Sold Date" in prepared.columns:
        sold_dates = pd.to_datetime(prepared["Sold Date"], errors="coerce")
        prepared["Sold Month"] = sold_dates.dt.month

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

        bedrooms = st.number_input("Bedrooms", 0.0, 10.0, 3.0, 1.0)
        bathrooms = st.number_input("Bathrooms", 0.0, 10.0, 2.0, 1.0)
        car_spaces = st.number_input("Car spaces", 0.0, 10.0, 1.0, 1.0)
        has_parking = st.selectbox("Has parking", ["Yes", "No"])
        has_pool = st.selectbox("Has pool", ["No", "Yes"])
        distance = st.number_input(
            "Approximate distance to Sydney CBD (km)",
            min_value=0.0,
            max_value=100.0,
            value=float(numeric_defaults["Approx. Distance to Sydney CBD (km)"]),
            step=1.0,
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
            "This is a model estimate based on a small dataset. It should not be "
            "treated as a professional property valuation."
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
            results.insert(
                0,
                "Predicted Sale Price (AUD)",
                model.predict(uploaded_features),
            )

            st.success(f"Predictions created for {len(results)} properties.")
            st.dataframe(results, use_container_width=True)
            st.download_button(
                "Download predictions",
                results.to_csv(index=False).encode("utf-8"),
                file_name="property_price_predictions.csv",
                mime="text/csv",
            )
        except Exception as error:
            st.error(f"The predictions could not be created. {error}")

st.divider()
st.caption("Model: Random Forest | Mean cross-validation RMSE: $620,717")
