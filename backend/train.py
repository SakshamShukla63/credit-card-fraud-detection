"""Train a fraud-detection model on the Kaggle credit-card dataset.

Produces:
  backend/models/model.pkl            - fitted XGBoost classifier
  backend/models/scaler.pkl           - fitted StandardScaler on Amount/Time
  backend/models/feature_names.json  - ordered feature names
  backend/models/metadata.json       - metrics + feature importance

The narrative engine (app/narrative.py) maps raw feature deltas onto plain
English risk triggers, so the model itself stays a black box and the UI
never leaks ML jargon.
"""
import json
import os
import pickle
import warnings

import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    precision_recall_curve,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

warnings.filterwarnings("ignore")

DATA = os.path.join(os.path.dirname(__file__), "data", "creditcard.csv")
MODELS = os.path.join(os.path.dirname(__file__), "models")
os.makedirs(MODELS, exist_ok=True)

# ---------------------------------------------------------------------------
# 1. Load
# ---------------------------------------------------------------------------
print("Loading data ...")
df = pd.read_csv(DATA)
print(f"  rows={len(df):,}  fraud={int(df['Class'].sum()):,}  "
      f"rate={df['Class'].mean()*100:.3f}%")

X = df.drop(columns=["Class"])
y = df["Class"].astype(int)

# ---------------------------------------------------------------------------
# 2. Scale Amount + Time (the only two non-PCA columns). PCA features are
#    already unit-variance and zero-mean, so we leave them untouched.
# ---------------------------------------------------------------------------
scaler = StandardScaler()
scaled = X.copy()
scaled[["Amount", "Time"]] = scaler.fit_transform(X[["Amount", "Time"]])

X_train, X_test, y_train, y_test = train_test_split(
    scaled, y, test_size=0.20, stratify=y, random_state=42
)

# ---------------------------------------------------------------------------
# 3. Train XGBoost with class weighting (handles imbalance without SMOTE).
# ---------------------------------------------------------------------------
neg, pos = (y_train == 0).sum(), (y_train == 1).sum()
scale_pos_weight = neg / pos
print(f"  scale_pos_weight={scale_pos_weight:.1f}")

model = XGBClassifier(
    n_estimators=400,
    max_depth=5,
    learning_rate=0.05,
    subsample=0.85,
    colsample_bytree=0.85,
    scale_pos_weight=scale_pos_weight,
    eval_metric="aucpr",
    random_state=42,
    tree_method="hist",
    n_jobs=-1,
)
model.fit(X_train, y_train)

# ---------------------------------------------------------------------------
# 4. Evaluate
# ---------------------------------------------------------------------------
y_prob = model.predict_proba(X_test)[:, 1]
y_pred = (y_prob >= 0.5).astype(int)
cm = confusion_matrix(y_test, y_pred)
auc = roc_auc_score(y_test, y_prob)
ap = average_precision_score(y_test, y_prob)
precision, recall, _ = precision_recall_curve(y_test, y_prob)
# threshold that maximises F1 on the test set
f1 = 2 * precision * recall / (precision + recall + 1e-12)
best_thresh = float(_[int(np.argmax(f1))])
print(f"  AUC={auc:.4f}  AP={ap:.4f}  best-threshold={best_thresh:.3f}")
print(f"  TN={cm[0,0]}  FP={cm[0,1]}  FN={cm[1,0]}  TP={cm[1,1]}")

# ---------------------------------------------------------------------------
# 5. Feature importance -> narrative mapping keys
# ---------------------------------------------------------------------------
feature_names = list(X.columns)
booster = model.get_booster()
imp = booster.get_score(importance_type="gain")
importance = {f: float(imp.get(f, 0.0)) for f in feature_names}
total = sum(importance.values()) or 1.0
norm_imp = {f: v / total for f, v in importance.items()}

# Save artifacts
with open(os.path.join(MODELS, "model.pkl"), "wb") as fh:
    pickle.dump(model, fh)
with open(os.path.join(MODELS, "scaler.pkl"), "wb") as fh:
    pickle.dump(scaler, fh)
with open(os.path.join(MODELS, "feature_names.json"), "w") as fh:
    json.dump(feature_names, fh)
with open(os.path.join(MODELS, "metadata.json"), "w") as fh:
    json.dump(
        {
            "n_samples": int(len(df)),
            "n_fraud": int(df["Class"].sum()),
            "fraud_rate": float(df["Class"].mean()),
            "auc": float(auc),
            "avg_precision": float(ap),
            "best_threshold": best_thresh,
            "feature_importance": norm_imp,
        },
        fh,
        indent=2,
    )
print("Saved artifacts to", MODELS)