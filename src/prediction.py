import joblib
import pandas as pd


# Load models

productivity_model = joblib.load("../models/productivity_model.pkl")
energy_model = joblib.load("../models/energy_model.pkl")


def predict_productivity(data):

    df = pd.DataFrame([data])

    prediction = productivity_model.predict(df)

    return prediction[0]


def predict_energy(data):

    df = pd.DataFrame([data])

    prediction = energy_model.predict(df)

    return prediction[0]