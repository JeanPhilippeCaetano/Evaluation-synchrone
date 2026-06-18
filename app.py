import json
import logging
import os
from pathlib import Path
from typing import Literal

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException, Security, Depends
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field


API_TOKEN = os.getenv("API_TOKEN", "churn-demo-token")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)

def verify_token(api_key: str = Security(api_key_header)):
    if api_key != API_TOKEN:
        raise HTTPException(status_code=401, detail="Token invalide")
    return api_key

MODEL_PATH = Path("artifacts/model.pkl")
FEATURE_COLUMNS_PATH = Path("artifacts/feature_columns.json")

metrics = {
    "n_predictions": 0,
    "n_errors": 0,
    "n_batch_requests": 0,
    "n_batch_inputs_total": 0,
}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("churn-api")

model = None
feature_columns = []

try:
    model = joblib.load(MODEL_PATH)
    with open(FEATURE_COLUMNS_PATH, "r", encoding="utf-8") as f:
        feature_columns = json.load(f)
except Exception as e:
    logger.error("Erreur au chargement des artefacts : %s", e)


class CustomerInput(BaseModel):
    tenure_months: int = Field(..., ge=0, le=120)
    monthly_charges: float = Field(..., ge=0)
    total_charges: float = Field(..., ge=0)
    contract: Literal["Month-to-month", "One year", "Two year"]


class BatchInput(BaseModel):
    inputs: list[CustomerInput]


app = FastAPI(title="Churn Prediction API", version="1.0")


@app.get("/")
def root():
    return {"status": "ok"}


@app.get("/health")
def health():
    if model is None:
        raise HTTPException(status_code=503, detail="Modèle indisponible")
    return {"status": "healthy", "model_loaded": True}


@app.get("/metrics")
def get_metrics(api_key: str = Depends(verify_token)):
    return metrics


@app.post("/predict")
def predict(payload: CustomerInput, api_key: str = Depends(verify_token)):
    if model is None:
        metrics["n_errors"] += 1
        raise HTTPException(status_code=500, detail="Modèle indisponible")

    try:
        df = pd.DataFrame([payload.model_dump()])
        df_encoded = pd.get_dummies(df, drop_first=True)
        df_aligned = df_encoded.reindex(columns=feature_columns, fill_value=0)

        prediction = model.predict(df_aligned)[0]
        confidence = model.predict_proba(df_aligned)[0].max()

        metrics["n_predictions"] += 1
        logger.info("prediction=%s", prediction)

        return {
            "prediction": int(prediction),
            "label": "churn" if prediction == 1 else "no_churn",
            "confidence": float(confidence),
        }
    except Exception as e:
        metrics["n_errors"] += 1
        logger.error("Erreur pendant la prédiction : %s", e)
        raise HTTPException(status_code=500, detail="Une erreur interne est survenue pendant la prédiction.")


@app.post("/predict_batch")
def predict_batch(payload: BatchInput, _: str = Depends(verify_token)):
    if len(payload.inputs) > 100:
        logger.warning("Batch rejeté : taille %d dépasse le maximum autorisé (100)", len(payload.inputs))
        raise HTTPException(status_code=413, detail="Trop d'entrées (max 100)")

    if model is None:
        metrics["n_errors"] += 1
        raise HTTPException(status_code=503, detail="Modèle indisponible")

    try:
        results = []
        for item in payload.inputs:
            df = pd.DataFrame([item.model_dump()])
            df_encoded = pd.get_dummies(df, drop_first=True)
            df_aligned = df_encoded.reindex(columns=feature_columns, fill_value=0)
            prediction = model.predict(df_aligned)[0]
            confidence = model.predict_proba(df_aligned)[0].max()
            results.append({
                "prediction": int(prediction),
                "label": "churn" if prediction == 1 else "no_churn",
                "confidence": float(confidence),
            })
            metrics["n_predictions"] += 1

        metrics["n_batch_requests"] += 1
        metrics["n_batch_inputs_total"] += len(payload.inputs)
        logger.info("batch prediction: n=%d", len(payload.inputs))

        return {"n_inputs": len(payload.inputs), "predictions": results}
    except Exception as e:
        metrics["n_errors"] += 1
        logger.error("Erreur pendant la prédiction batch : %s", e)
        raise HTTPException(status_code=500, detail="Une erreur interne est survenue pendant la prédiction.")
