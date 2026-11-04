# app/ml/fare/train.py
"""
Train the fare multiplier prediction model.

Run:
    python -m app.ml.fare.train
"""

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

from app.ml.fare.features import FARE_FEATURE_ORDER


DATA_FILE = Path("data/fare_training.csv")
MODEL_DIR = Path("app/ml/models")
MODEL_FILE = MODEL_DIR / "fare_v1.pkl"


def main() -> None:
    if not DATA_FILE.exists():
        raise SystemExit(
            f"Training data not found at {DATA_FILE}.\n"
            f"Run: python -m app.ml.fare.generate_data"
        )

    print(f"Loading training data from {DATA_FILE}...")
    df = pd.read_csv(DATA_FILE)

    X = df[FARE_FEATURE_ORDER].values
    y = df["multiplier"].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    print(f"  Train size: {len(X_train)}")
    print(f"  Test size:  {len(X_test)}")

    model = xgb.XGBRegressor(
        n_estimators=300,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.9,
        colsample_bytree=0.9,
        random_state=42,
    )

    print("\nTraining XGBoost regressor...")
    model.fit(X_train, y_train)

    # ---------- Evaluation ----------
    print("\nEvaluating on held-out test set:")
    y_pred = model.predict(X_test)

    mae = mean_absolute_error(y_test, y_pred)
    rmse = mean_squared_error(y_test, y_pred, squared=False)
    r2 = r2_score(y_test, y_pred)

    print(f"  MAE:   {mae:.4f}")
    print(f"  RMSE:  {rmse:.4f}")
    print(f"  R²:    {r2:.4f}")

    # Feature importance
    importances = model.feature_importances_
    ranking = sorted(
        zip(FARE_FEATURE_ORDER, importances),
        key=lambda x: x[1],
        reverse=True,
    )
    print("\nFeature importance:")
    for name, imp in ranking:
        print(f"  {name:<26} {imp:.4f}")

    # Save
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_FILE)
    print(f"\n✓ Saved model to {MODEL_FILE}")


if __name__ == "__main__":
    main()