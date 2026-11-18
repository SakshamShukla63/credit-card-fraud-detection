import json
import pickle
import random
from pathlib import Path
from typing import Optional

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .narrative import get_narrative

BACKEND_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BACKEND_DIR / "data" / "creditcard.csv"
MODELS_DIR = BACKEND_DIR / "models"


class Transaction(BaseModel):
    Time: float = Field(default=0, ge=0)
    Amount: float = Field(default=0, ge=0)
    features: Optional[dict[str, float]] = None


app = FastAPI(title="Radar Fraud Detection API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

model = None
scaler = None
feature_names = None
metadata = None
dataset = None


def load_resources():
    global model, scaler, feature_names, metadata, dataset

    required = ["model.pkl", "scaler.pkl", "feature_names.json", "metadata.json"]
    if not all((MODELS_DIR / name).exists() for name in required):
        raise RuntimeError(
            "Model artifacts are missing. Run: python backend/train.py"
        )

    with (MODELS_DIR / "model.pkl").open("rb") as file:
        model = pickle.load(file)
    with (MODELS_DIR / "scaler.pkl").open("rb") as file:
        scaler = pickle.load(file)
    with (MODELS_DIR / "feature_names.json").open("r", encoding="utf-8") as file:
        feature_names = json.load(file)
    with (MODELS_DIR / "metadata.json").open("r", encoding="utf-8") as file:
        metadata = json.load(file)
    dataset = pd.read_csv(DATA_PATH)


@app.on_event("startup")
def startup():
    try:
        load_resources()
    except Exception as exc:
        raise RuntimeError(str(exc)) from exc


@app.get("/api/health")
def health():
    return {"status": "ok", "modelReady": model is not None}


@app.get("/api/metadata")
def get_metadata():
    if metadata is None:
        raise HTTPException(status_code=503, detail="Model is not loaded")
    return metadata


@app.get("/api/sample")
def get_sample():
    if dataset is None:
        raise HTTPException(status_code=503, detail="Dataset is not loaded")

    row = dataset.iloc[random.randint(0, len(dataset) - 1)]
    features = {
        name: float(row[name])
        for name in feature_names
        if name not in ("Time", "Amount")
    }
    return {
        "Time": float(row["Time"]),
        "Amount": float(row["Amount"]),
        "features": features,
        "actualClass": int(row["Class"]),
    }


@app.post("/api/predict")
def predict(transaction: Transaction):
    if model is None or scaler is None or feature_names is None:
        raise HTTPException(status_code=503, detail="Model is not loaded")

    values = {name: 0.0 for name in feature_names}
    values["Time"] = transaction.Time
    values["Amount"] = transaction.Amount
    for name, value in (transaction.features or {}).items():
        if name in values:
            values[name] = float(value)

    frame = pd.DataFrame([[values[name] for name in feature_names]], columns=feature_names)
    frame[["Amount", "Time"]] = scaler.transform(frame[["Amount", "Time"]])
    probability = float(model.predict_proba(frame)[:, 1][0])
    threshold = float(metadata["best_threshold"]) if metadata else 0.5
    prediction = int(probability >= threshold)
    narrative = get_narrative(values, probability)

    return {
        "probability": probability,
        "score": round(probability * 100, 2),
        "prediction": prediction,
        "threshold": threshold,
        **narrative,
    }
