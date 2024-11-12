
import streamlit as st
import pandas as pd
import numpy as np
import tensorflow as tf
# Add other necessary imports from your notebook

st.title("Predictive Maintenance Dashboard")
st.sidebar.title("Controls")

# Load trained model
model = tf.keras.models.load_model('/content/LSTM_model.h5')

# Upload data file or load sample data
uploaded_file = st.file_uploader("Upload Sensor Data", type=["csv", "xlsx"])
if uploaded_file is not None:
    data = pd.read_csv(uploaded_file)  # Or use read_excel for .xlsx

def preprocess_data(data):
    # Add preprocessing steps from your notebook
    return processed_data

if uploaded_file is not None:
    preprocessed_data = preprocess_data(data)
    predictions = model.predict(preprocessed_data)
    st.write(predictions)

import matplotlib.pyplot as plt

if uploaded_file is not None:
    fig, ax = plt.subplots()
    ax.plot(predictions, label="Predictions")
    ax.plot(data['True Label'], label="Actual")
    ax.legend()
    st.pyplot(fig)

