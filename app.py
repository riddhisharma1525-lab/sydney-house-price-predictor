from pathlib import Path

import pandas as pd
import streamlit as st

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


# Set the browser tab title and icon.
st.set_page_config(
    page_title="Sydney House Price Predictor",
    page_icon="🏠"
)

# The Excel dataset must remain in the same folder as app.py.
DATA_PATH = Path(__file__).with_name(
    "Sydney_Sold_Property_Dataset (1).xlsx"
)


@st.cache_resource
def train_deployment_model():
    """
    Read the collected dataset and train the final Random Forest pipeline.

    Streamlit caches the returned objects, so training is only repeated
    when the application code or data changes.
    """

    # Read the collected property records.
    data = pd.read_excel(
        DATA_PATH,
        sheet_name="Sold Properties"
    )

    # Remove extra spaces from column headings.
    data.columns = data.columns.str.strip()

    # Accept either target-column heading used in the Excel file.
    data = data.rename(columns={
        "Sold Price (AUD) - TARGET": "Sold Price (AUD)",
        "Sold Price (AUD) - Target": "Sold Price (AUD)",
    })

    # Convert the sale date before creating Sold Month.
    data["Sold Date"] = pd.to_datetime(
        data["Sold Date"],
        errors="coerce"
    )

    # Create the same engineered features used in the notebook.
    data["Sold Month"] = data["Sold Date"].dt.month

    data["Total Rooms"] = (
        data["Bedrooms"].fillna(0)
        + data["Bathrooms"].fillna(0)
    )

    # Remove identifiers, source information and unused features.
    # Postcode is removed because it is a nominal location label.
    # The highly incomplete size and year fields are also excluded.
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

    # Create the model inputs and target.
    features = data.drop(
        columns=[target] + drop_columns,
        errors="ignore"
    )

    prices = data[target]

    # Separate categorical and numerical inputs.
    categorical_columns = features.select_dtypes(
        include=["object", "category", "bool"]
    ).columns.tolist()

    numerical_columns = features.select_dtypes(
        include=["number"]
    ).columns.tolist()

    # Fill missing numerical values and standardise the columns.
    numerical_pipeline = Pipeline(steps=[
        (
            "imputer",
            SimpleImputer(strategy="median")
        ),
        (
            "scaler",
            StandardScaler()
        ),
    ])

    # Fill missing categories and convert categories into dummy columns.
    # drop="first" removes one reference category.
    categorical_pipeline = Pipeline(steps=[
        (
            "imputer",
            SimpleImputer(strategy="most_frequent")
        ),
        (
            "onehot",
            OneHotEncoder(
                handle_unknown="ignore",
                drop="first"
            )
        ),
    ])

    # Apply the correct preprocessing to each feature type.
    preprocessor = ColumnTransformer(transformers=[
        (
            "num",
            numerical_pipeline,
            numerical_columns
        ),
        (
            "cat",
            categorical_pipeline,
            categorical_columns
        ),
    ])

    # Use the same Random Forest settings selected in the notebook.
    model = Pipeline(steps=[
        (
            "preprocessor",
            preprocessor
        ),
        (
            "model",
            RandomForestRegressor(
                n_estimators=300,
                max_depth=5,
                min_samples_leaf=2,
                random_state=42
            )
        ),
    ])

    # Train the complete pipeline using all collected properties.
    model.fit(features, prices)

    # Store category values for the drop-down menus.
    category_values = {
        column: sorted(
            features[column]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )
        for column in categorical_columns
    }

    # Store median values for the numerical input defaults.
    numeric_defaults = {
        column: float(
            pd.to_numeric(
                features[column],
                errors="coerce"
            ).median()
        )
        for column in numerical_columns
    }

    return (
        model,
        features.columns.tolist(),
        category_values,
        numeric_defaults
    )


# Train and cache the final deployment pipeline.
(
    model,
    feature_columns,
    category_values,
    numeric_defaults
) = train_deployment_model()


def prepare_features(data):
    """
    Prepare manually entered or uploaded property information.

    The returned DataFrame has the same columns and order used during
    model training.
    """

    prepared = data.copy()

    # Calculate Sold Month when a Sold Date is supplied instead.
    if (
        "Sold Month" not in prepared.columns
        and "Sold Date" in prepared.columns
    ):
        sold_dates = pd.to_datetime(
            prepared["Sold Date"],
            errors="coerce"
        )

        prepared["Sold Month"] = sold_dates.dt.month

    # Calculate Total Rooms when it is not already supplied.
    if "Total Rooms" not in prepared.columns:
        required_room_columns = {
            "Bedrooms",
            "Bathrooms"
        }

        if required_room_columns.issubset(prepared.columns):
            prepared["Total Rooms"] = (
                pd.to_numeric(
                    prepared["Bedrooms"],
                    errors="coerce"
                ).fillna(0)
                + pd.to_numeric(
                    prepared["Bathrooms"],
                    errors="coerce"
                ).fillna(0)
            )

    # Check whether any model inputs are missing.
    missing_columns = [
        column
        for column in feature_columns
        if column not in prepared.columns
    ]

    if missing_columns:
        raise ValueError(
            "Missing columns: "
            + ", ".join(missing_columns)
        )

    # Return the inputs in the same order used during training.
    return prepared[feature_columns]


# Add the application title and introduction.
st.title("Sydney House Price Predictor")

st.write(
    "This application gives an estimated sale price using the "
    "Random Forest model developed from the collected Mosman, "
    "Parramatta and Penrith data."
)

# Create separate pages for manual entry and CSV upload.
manual_tab, upload_tab = st.tabs([
    "Enter one property",
    "Upload CSV"
])


# Manual property-entry page.
with manual_tab:

    with st.form("property_form"):

        suburb = st.selectbox(
            "Suburb",
            category_values["Suburb"]
        )

        property_type = st.selectbox(
            "Property type",
            category_values["Property Type"]
        )

        state = st.selectbox(
            "State",
            category_values["State"]
        )

        bedrooms = st.number_input(
            "Bedrooms",
            min_value=0.0,
            max_value=10.0,
            value=3.0,
            step=1.0
        )

        bathrooms = st.number_input(
            "Bathrooms",
            min_value=0.0,
            max_value=10.0,
            value=2.0,
            step=1.0
        )

        car_spaces = st.number_input(
            "Car spaces",
            min_value=0.0,
            max_value=10.0,
            value=1.0,
            step=1.0
        )

        has_parking = st.selectbox(
            "Has parking",
            ["Yes", "No"]
        )

        has_pool = st.selectbox(
            "Has pool",
            ["No", "Yes"]
        )

        distance = st.number_input(
            "Approximate distance to Sydney CBD (km)",
            min_value=0.0,
            max_value=100.0,
            value=float(
                numeric_defaults[
                    "Approx. Distance to Sydney CBD (km)"
                ]
            ),
            step=1.0
        )

        sold_month = st.slider(
            "Sold month",
            min_value=1,
            max_value=12,
            value=9
        )

        submitted = st.form_submit_button(
            "Predict sale price"
        )

    # Create a prediction after the form is submitted.
    if submitted:

        property_data = pd.DataFrame([{
            "Suburb": suburb,
            "State": state,
            "Property Type": property_type,
            "Bedrooms": bedrooms,
            "Bathrooms": bathrooms,
            "Has Parking": (
                1 if has_parking == "Yes" else 0
            ),
            "Car Spaces": car_spaces,
            "Approx. Distance to Sydney CBD (km)": distance,
            "Has Pool": (
                1 if has_pool == "Yes" else 0
            ),
            "Sold Month": sold_month,
            "Total Rooms": bedrooms + bathrooms,
        }])

        prediction = model.predict(
            prepare_features(property_data)
        )[0]

        st.metric(
            "Estimated sale price",
            f"${prediction:,.0f}"
        )

        st.caption(
            "This is a model estimate based on a small dataset. "
            "It should not be treated as a professional property "
            "valuation."
        )


# CSV-upload page.
with upload_tab:

    st.write(
        "Upload a CSV file containing the model input columns "
        "shown below."
    )

    st.code(", ".join(feature_columns))

    uploaded_file = st.file_uploader(
        "Choose a CSV file",
        type="csv"
    )

    if uploaded_file is not None:

        try:
            # Read and prepare the uploaded property information.
            uploaded_data = pd.read_csv(uploaded_file)

            uploaded_features = prepare_features(
                uploaded_data
            )

            # Keep the original columns in the downloaded result.
            results = uploaded_data.copy()

            # Place the predicted price at the start of the table.
            results.insert(
                0,
                "Predicted Sale Price (AUD)",
                model.predict(uploaded_features)
            )

            st.success(
                f"Predictions created for "
                f"{len(results)} properties."
            )

            st.dataframe(
                results,
                use_container_width=True
            )

            st.download_button(
                "Download predictions",
                results.to_csv(
                    index=False
                ).encode("utf-8"),
                file_name="property_price_predictions.csv",
                mime="text/csv"
            )

        except Exception as error:
            st.error(
                "The predictions could not be created. "
                + str(error)
            )


# Show the selected model and its cross-validation result.
st.divider()

st.caption(
    "Model: Random Forest | "
    "Mean cross-validation RMSE: $620,717"
)
