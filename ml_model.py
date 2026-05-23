import pandas as pd
import numpy as np
import os
import joblib
from xgboost import XGBRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.neighbors import KNeighborsRegressor

def train_hybrid_model(csv_path="dataset.csv", model_path="hybrid_model.pkl"):
    """
    Trains XGBoost, Random Forest, and KNN Regressors to predict the continuous class labels.
    Uses label = 0, 50, 100
    """
    if not os.path.exists(csv_path):
        return False, "Dataset not found. Please collect data sequentially first."
        
    df = pd.read_csv(csv_path)
    
    # Check if necessary columns exist
    required_cols = ['temp', 'oil_weight', 'density', 'r', 'g', 'b', 'label']
    if not all(col in df.columns for col in required_cols):
        return False, "Dataset missing required columns."
        
    # Check if dataset has any data
    if len(df) == 0:
        return False, "Dataset is empty."
        
    # Drop NAs safely
    df = df.dropna()
    
    X = df[['temp', 'oil_weight', 'density', 'r', 'g', 'b']]
    y = df['label'] # Expected to be 0, 50, 100
    
    # Regressors fit the continuous interpolation safely for ensemble weighting
    xgb_model = XGBRegressor(n_estimators=100, learning_rate=0.1, random_state=42)
    rf_model = RandomForestRegressor(n_estimators=100, random_state=42)
    knn_model = KNeighborsRegressor(n_neighbors=min(5, len(df)))
    
    try:
        xgb_model.fit(X, y)
        rf_model.fit(X, y)
        knn_model.fit(X, y)
    except Exception as e:
        return False, f"Error training models: {str(e)}"
        
    # Combine into a dictionary block
    hybrid_model = {
        'xgb': xgb_model,
        'rf': rf_model,
        'knn': knn_model
    }
    
    joblib.dump(hybrid_model, model_path)
    return True, "Hybrid model (XGB, RF, KNN) trained successfully!"

def predict_adulteration(features, model_path="hybrid_model.pkl"):
    """
    features input format: [temp, oil_weight, density, r, g, b]
    Returns hybrid prediction: 0.5 * XGB + 0.3 * RF + 0.2 * KNN
    """
    if not os.path.exists(model_path):
        return None, "Model not found. Train the model first on the Training page."
        
    try:
        hybrid_model = joblib.load(model_path)
        
        # Format as DataFrame to avoid X-feature warning in scikit-learn
        X_df = pd.DataFrame([features], columns=['temp', 'oil_weight', 'density', 'r', 'g', 'b'])
        
        pred_xgb = hybrid_model['xgb'].predict(X_df)[0]
        pred_rf = hybrid_model['rf'].predict(X_df)[0]
        pred_knn = hybrid_model['knn'].predict(X_df)[0]
        
        # User requested formula weights
        final_prediction = (0.5 * pred_xgb) + (0.3 * pred_rf) + (0.2 * pred_knn)
        
        # Bounded limits logic output
        final_prediction = max(0.0, min(100.0, final_prediction))
        
        return round(final_prediction, 2), None
        
    except Exception as e:
        return None, f"Prediction error: {str(e)}"
