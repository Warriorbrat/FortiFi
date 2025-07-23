import joblib
import numpy as np

# Load model and features
model_path = "model/trained_model.pkl"
model, feature_names = joblib.load(model_path)

def predict_single(input_dict):
    try:
        values = [float(input_dict.get(feat, 0)) for feat in feature_names]
        values_array = np.array(values).reshape(1, -1)
        prediction = model.predict(values_array)[0]
        return prediction
    except Exception as e:
        return f"Prediction Error: {str(e)}"
