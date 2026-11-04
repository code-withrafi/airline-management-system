# app/ml/no_show/train.py
"""
Train and evaluate the no-show prediction model.

Run:
    python -m app.ml.no_show.train
"""

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split

from app.ml.features import NO_SHOW_FEATURE_ORDER


DATA_FILE = Path("data/no_show_training.csv")
MODEL_DIR = Path("app/ml/models")
MODEL_FILE = MODEL_DIR / "no_show_v1.pkl"


def main() -> None:
    if not DATA_FILE.exists():
        raise SystemExit(
            f"Training data not found at {DATA_FILE}.\n"
            f"Run: python -m app.ml.no_show.generate_data"
        )

    print(f"Loading training data from {DATA_FILE}...")
    df = pd.read_csv(DATA_FILE)

    X = df[NO_SHOW_FEATURE_ORDER].values
    y = df["no_show"].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print(f"  Train size: {len(X_train)}")
    print(f"  Test size:  {len(X_test)}")
    print(f"  Positive class rate (train): {y_train.mean():.2%}")

    # Class-weight balancing: since ~20% of samples are no-shows,
    # XGBoost will naturally bias toward predicting "show" unless we
    # scale the positive class weight. This trades precision for
    # recall on the no-show class, which is what we want for an
    # overbooking advisor.
    scale_pos_weight = float((y_train == 0).sum() / (y_train == 1).sum())
    print(f"  scale_pos_weight: {scale_pos_weight:.3f}")

    model = xgb.XGBClassifier(
        n_estimators=400,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.9,
        colsample_bytree=0.9,
        scale_pos_weight=scale_pos_weight,
        eval_metric="logloss",
        random_state=42,
    )

    print("\nTraining XGBoost model...")
    model.fit(X_train, y_train)

    # ---------- Evaluation ----------
    print("\nEvaluating on held-out test set:")
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]

    acc = accuracy_score(y_test, y_pred)
    auc = roc_auc_score(y_test, y_proba)
    cm = confusion_matrix(y_test, y_pred)
    report = classification_report(y_test, y_pred, digits=3)

    print(f"  Accuracy: {acc:.4f}")
    print(f"  ROC-AUC:  {auc:.4f}")
    print(f"\nConfusion Matrix:")
    print(f"    TN={cm[0,0]:>6}  FP={cm[0,1]:>6}")
    print(f"    FN={cm[1,0]:>6}  TP={cm[1,1]:>6}")
    print(f"\nClassification Report:")
    print(report)

    # ---------- Feature Importance ----------
    importances = model.feature_importances_
    ranking = sorted(
        zip(NO_SHOW_FEATURE_ORDER, importances),
        key=lambda x: x[1],
        reverse=True,
    )
    print("Feature importance (XGBoost gain):")
    for name, imp in ranking:
        print(f"  {name:<26} {imp:.4f}")

    # ---------- Save ----------
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_FILE)
    print(f"\n✓ Saved model to {MODEL_FILE}")


if __name__ == "__main__":
    main()