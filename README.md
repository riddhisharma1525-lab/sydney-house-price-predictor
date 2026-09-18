# Sydney House Price Predictor

This project develops and evaluates machine learning models for predicting sold property prices in Sydney.

The dataset contains 102 sold properties from Mosman, Parramatta and Penrith. Three regression models were compared using five-fold cross-validation:

- Linear Regression
- Random Forest
- Gradient Boosting

Random Forest was selected for deployment because it achieved the lowest mean validation RMSE and the highest mean validation R².

## Application Features

The Streamlit application allows users to:

- enter the details of one property;
- receive an estimated sale price;
- upload several properties in a CSV file;
- download the generated predictions.

## Project Files

- `app.py` – Streamlit application.
- `syd_house_price_model.joblib` – trained Random Forest pipeline.
- `syd_house_price.ipynb` – complete analysis for Parts 3, 4 and 5.
- `Sydney_Sold_Property_Dataset.xlsx` – collected housing dataset.
- `sample_property_upload.csv` – example CSV upload format.
- `requirements.txt` – required Python packages.
- `screenshots/` – screenshots of the working application.

## Run the Application Locally

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate