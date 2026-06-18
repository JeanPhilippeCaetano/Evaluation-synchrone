import json
import logging
from pathlib import Path
from typing import Literal

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


API_TOKEN = "churn-demo-token"
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
    return {"status": "healthy", "model_loaded": model is not None}


@app.get("/metrics")
def get_metrics():
    return metrics


@app.post("/predict")
def predict(payload: CustomerInput):
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
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/predict_batch")
def predict_batch(payload: BatchInput):
    if len(payload.inputs) > 100:
        logger.warning("Batch rejeté : %d entrées soumises (max 100)", len(payload.inputs))
        raise HTTPException(
            status_code=413,
            detail=f"Batch trop volumineux : {len(payload.inputs)} entrées (max 100)",
        )

    if model is None:
        metrics["n_errors"] += 1
        raise HTTPException(status_code=500, detail="Modèle indisponible")

    predictions = []
    try:
        for i, item in enumerate(payload.inputs):
            df = pd.DataFrame([item.model_dump()])
            df_encoded = pd.get_dummies(df, drop_first=True)
            df_aligned = df_encoded.reindex(columns=feature_columns, fill_value=0)

            prediction = model.predict(df_aligned)[0]
            confidence = model.predict_proba(df_aligned)[0].max()

            predictions.append({
                "prediction": int(prediction),
                "label": "churn" if prediction == 1 else "no_churn",
                "confidence": float(confidence),
            })

        metrics["n_batch_requests"] += 1
        metrics["n_batch_inputs_total"] += len(payload.inputs)
        logger.info("predict_batch: %d entrées traitées", len(payload.inputs))

        return {"predictions": predictions, "n_inputs": len(payload.inputs)}
    except Exception as e:
        metrics["n_errors"] += 1
        logger.error("Erreur pendant predict_batch (entrée %d) : %s", i, e)
        raise HTTPException(status_code=500, detail=f"Erreur à l'entrée {i} : {e}")
