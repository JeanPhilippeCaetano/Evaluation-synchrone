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
    response = client.post(
        "/predict",
        json=payload,
        headers={"X-API-Key": "churn-demo-token"}
    )

    assert response.status_code == 200
    assert "prediction" in response.json()


def test_predict_rejects_missing_field():
    response = client.post(
        "/predict",
        json={"tenure_months": 12},
        headers={"X-API-Key": "churn-demo-token"}
    )

    assert response.status_code == 422
