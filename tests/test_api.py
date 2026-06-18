import numpy as np
from fastapi.testclient import TestClient

import app as api_app


class DummyModel:
    def predict(self, X):
        return [0]

    def predict_proba(self, X):
        return np.array([[0.8, 0.2]])


client = TestClient(api_app.app)


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_predict_valid_input(monkeypatch):
    monkeypatch.setattr(api_app, "model", DummyModel())
    monkeypatch.setattr(
        api_app,
        "feature_columns",
        [
            "tenure_months",
            "monthly_charges",
            "total_charges",
            "contract_One year",
            "contract_Two year",
        ],
    )

    payload = {
        "tenure_months": 12,
        "monthly_charges": 75.5,
        "total_charges": 906.0,
        "contract": "Month-to-month",
    }
    response = client.post("/predict", json=payload)

    assert response.status_code == 200
    assert "prediction" in response.json()


def test_predict_rejects_missing_field():
    response = client.post("/predict", json={"tenure_months": 12})

    assert response.status_code == 422


FEATURE_COLS = [
    "tenure_months",
    "monthly_charges",
    "total_charges",
    "contract_One year",
    "contract_Two year",
]

BATCH_PAYLOAD = {
    "inputs": [
        {"tenure_months": 12, "monthly_charges": 75.5, "total_charges": 906.0, "contract": "Month-to-month"},
        {"tenure_months": 24, "monthly_charges": 90.0, "total_charges": 2160.0, "contract": "One year"},
    ]
}


def test_predict_batch_valid(monkeypatch):
    monkeypatch.setattr(api_app, "model", DummyModel())
    monkeypatch.setattr(api_app, "feature_columns", FEATURE_COLS)

    response = client.post("/predict_batch", json=BATCH_PAYLOAD)

    assert response.status_code == 200
    body = response.json()
    assert body["n_inputs"] == 2
    assert len(body["predictions"]) == 2
    assert body["predictions"][0]["label"] in ("churn", "no_churn")
    assert body["predictions"][1]["label"] in ("churn", "no_churn")


def test_predict_batch_too_large(monkeypatch):
    monkeypatch.setattr(api_app, "model", DummyModel())
    monkeypatch.setattr(api_app, "feature_columns", FEATURE_COLS)

    entry = {"tenure_months": 1, "monthly_charges": 50.0, "total_charges": 50.0, "contract": "Month-to-month"}
    payload = {"inputs": [entry] * 101}

    response = client.post("/predict_batch", json=payload)

    assert response.status_code == 413
