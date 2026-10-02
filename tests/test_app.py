import pandas as pd
import app


def test_prepare_features_creates_total_rooms():
    data = pd.DataFrame([{
        "Suburb": "Mosman",
        "State": "NSW",
        "Property Type": "House",
        "Bedrooms": 3,
        "Bathrooms": 2,
        "Has Parking": 1,
        "Car Spaces": 1,
        "Approx. Distance to Sydney CBD (km)": 8,
        "Has Pool": 0,
        "Sold Month": 9
    }])

    prepared = app.prepare_features(data)

    assert "Total Rooms" in prepared.columns
    assert prepared.iloc[0]["Total Rooms"] == 5


def test_prepare_features_creates_sold_month():
    data = pd.DataFrame([{
        "Suburb": "Mosman",
        "State": "NSW",
        "Property Type": "House",
        "Bedrooms": 3,
        "Bathrooms": 2,
        "Has Parking": 1,
        "Car Spaces": 1,
        "Approx. Distance to Sydney CBD (km)": 8,
        "Has Pool": 0,
        "Sold Date": "2026-09-15"
    }])

    prepared = app.prepare_features(data)

    assert "Sold Month" in prepared.columns
    assert prepared.iloc[0]["Sold Month"] == 9


def test_prepare_features_missing_columns():
    data = pd.DataFrame([{
        "Bedrooms": 3,
        "Bathrooms": 2
    }])

    try:
        app.prepare_features(data)
        assert False
    except ValueError as error:
        assert "Missing columns" in str(error)


def test_model_prediction():
    data = pd.DataFrame([{
        "Suburb": app.category_values["Suburb"][0],
        "State": app.category_values["State"][0],
        "Property Type": app.category_values["Property Type"][0],
        "Bedrooms": 3,
        "Bathrooms": 2,
        "Has Parking": 1,
        "Car Spaces": 1,
        "Approx. Distance to Sydney CBD (km)": 10,
        "Has Pool": 0,
        "Sold Month": 9,
        "Total Rooms": 5
    }])

    prepared = app.prepare_features(data)
    prediction = app.model.predict(prepared)[0]

    assert prediction > 0